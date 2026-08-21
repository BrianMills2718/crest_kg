from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from crest_pipeline import (
    DocumentExtraction,
    EntityCandidate,
    EntityKind,
    EvidenceCandidate,
    ProviderDocumentExtraction,
    ProviderEntityCandidate,
    ProviderEvidenceCandidate,
    ProviderRelationshipCandidate,
    RelationshipCandidate,
    build_graph,
    load_corpus,
    partition_extraction_grounding,
    recover_extraction_from_trace,
    validate_extraction_grounding,
    validate_graph_file,
    validate_provider_extraction,
    write_graph,
)


def _write_corpus(path: Path, count: int = 5) -> Path:
    records = []
    for number in reversed(range(1, count + 1)):
        records.append(
            {
                "url": f"https://www.cia.gov/readingroom/document/doc-{number}",
                "title": f"Document {number}",
                "metadata": {
                    "Document Number (FOIA) /ESDN (CREST)": f"DOC-{number}"
                },
                "body_text": (
                    f"Analyst {number} described the Archive as an organization in Document {number}."
                ),
            }
        )
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


def _extraction(number: int) -> DocumentExtraction:
    return DocumentExtraction(
        entities=[
            EntityCandidate(
                local_id="analyst",
                name=f"Analyst {number}",
                type=EntityKind.PERSON,
                evidence=EvidenceCandidate(line_start=1, line_count=1),
            ),
            EntityCandidate(
                local_id="archive",
                name="Archive",
                type=EntityKind.ORGANIZATION,
                evidence=EvidenceCandidate(line_start=1, line_count=1),
            ),
        ],
        relationships=[
            RelationshipCandidate(
                source_entity_id="analyst",
                target_entity_id="archive",
                type="described",
                source_mention=f"Analyst {number}",
                relation_phrase="described",
                target_mention="Archive",
                support_reasoning="The analyst is the named subject describing the Archive.",
                evidence=EvidenceCandidate(line_start=1, line_count=1),
            )
        ],
    )


def test_load_corpus_selects_explicit_file_and_sorts_document_ids(tmp_path: Path) -> None:
    corpus = _write_corpus(tmp_path / "corpus.json", count=6)

    documents = load_corpus(corpus, limit=5, max_chars=10_000)

    assert [item.manifest.document_id for item in documents] == [
        "doc-1",
        "doc-2",
        "doc-3",
        "doc-4",
        "doc-5",
    ]
    assert all(item.manifest.corpus_path == corpus.as_posix() for item in documents)


def test_document_extraction_rejects_dangling_relationships() -> None:
    with pytest.raises(ValidationError, match="target is undeclared"):
        DocumentExtraction(
            entities=[
                EntityCandidate(
                    local_id="known",
                    name="Known",
                    type=EntityKind.CONCEPT,
                    evidence=EvidenceCandidate(line_start=1, line_count=1),
                )
            ],
            relationships=[
                RelationshipCandidate(
                    source_entity_id="known",
                    target_entity_id="missing",
                    type="mentions",
                    source_mention="Known",
                    relation_phrase="mentions",
                    target_mention="missing",
                    support_reasoning="The named source mentions the named target.",
                    evidence=EvidenceCandidate(line_start=1, line_count=1),
                )
            ],
        )


def test_evidence_line_count_is_enforced_in_the_provider_schema() -> None:
    schema = ProviderEvidenceCandidate.model_json_schema()

    assert schema["properties"]["line_count"]["maximum"] == 5
    with pytest.raises(ValidationError, match="less than or equal to 5"):
        EvidenceCandidate(line_start=1, line_count=6)


def test_provider_conversion_rejects_invalid_items_without_losing_valid_ones() -> None:
    response = ProviderDocumentExtraction(
        entities=[
            ProviderEntityCandidate(
                local_id="bad id",
                name="Bad",
                type=EntityKind.PERSON,
                evidence=ProviderEvidenceCandidate(line_start=1, line_count=1),
            ),
            ProviderEntityCandidate(
                local_id="archive",
                name="Archive",
                type=EntityKind.ORGANIZATION,
                evidence=ProviderEvidenceCandidate(line_start=1, line_count=1),
            ),
        ],
        relationships=[
            ProviderRelationshipCandidate(
                source_entity_id="bad id",
                target_entity_id="archive",
                type="described",
                source_mention="Bad",
                relation_phrase="described",
                target_mention="Archive",
                support_reasoning="The named source described the named target.",
                evidence=ProviderEvidenceCandidate(line_start=1, line_count=1),
            )
        ],
    )

    extraction, rejections = validate_provider_extraction("doc-1", response)

    assert [entity.local_id for entity in extraction.entities] == ["archive"]
    assert extraction.relationships == []
    assert [rejection.item_kind for rejection in rejections] == [
        "entity",
        "relationship",
    ]
    assert "strict entity validation failed" in rejections[0].reason
    assert "undeclared after strict entity validation" in rejections[1].reason


def test_grounding_rejects_lines_outside_supplied_document(tmp_path: Path) -> None:
    corpus = _write_corpus(tmp_path / "corpus.json", count=1)
    document = load_corpus(corpus, limit=1, max_chars=10_000)[0]
    extraction = DocumentExtraction(
        entities=[
            EntityCandidate(
                local_id="archive",
                name="Archive",
                type=EntityKind.ORGANIZATION,
                evidence=EvidenceCandidate(line_start=2, line_count=1),
            )
        ],
        relationships=[],
    )

    with pytest.raises(ValueError, match="exceeds"):
        validate_extraction_grounding(document, extraction)


def test_grounding_rejects_relationship_fragment_not_in_quote(tmp_path: Path) -> None:
    corpus = _write_corpus(tmp_path / "corpus.json", count=1)
    document = load_corpus(corpus, limit=1, max_chars=10_000)[0]
    extraction = _extraction(1)
    extraction.relationships[0].relation_phrase = "wrote about"

    with pytest.raises(ValueError, match="relation_phrase is not an exact substring"):
        validate_extraction_grounding(document, extraction)


def test_grounding_rejects_predicate_direction_missing_from_exact_phrase(
    tmp_path: Path,
) -> None:
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(
        json.dumps(
            [
                {
                    "title": "Direction",
                    "metadata": {"Document Number": "DIRECTION"},
                    "body_text": "Central Committee and KGB preparations continued.",
                }
            ]
        ),
        encoding="utf-8",
    )
    document = load_corpus(corpus_path, limit=1, max_chars=10_000)[0]
    extraction = DocumentExtraction(
        entities=[
            EntityCandidate(
                local_id="committee",
                name="Central Committee",
                type=EntityKind.ORGANIZATION,
                evidence=EvidenceCandidate(line_start=1, line_count=1),
            ),
            EntityCandidate(
                local_id="kgb",
                name="KGB",
                type=EntityKind.ORGANIZATION,
                evidence=EvidenceCandidate(line_start=1, line_count=1),
            ),
        ],
        relationships=[
            RelationshipCandidate(
                source_entity_id="committee",
                target_entity_id="kgb",
                type="prepared_for",
                source_mention="Central Committee",
                relation_phrase="Central Committee and KGB preparations",
                target_mention="KGB",
                support_reasoning="The phrase mentions joint preparations, not preparation for KGB.",
                evidence=EvidenceCandidate(line_start=1, line_count=1),
            )
        ],
    )

    with pytest.raises(ValueError, match="not lexically supported"):
        validate_extraction_grounding(document, extraction)


def test_grounding_rejects_punctuation_only_relation_phrase(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(
        json.dumps(
            [
                {
                    "title": "List",
                    "metadata": {"Document Number": "LIST"},
                    "body_text": "FBI, J. Edgar Hoover",
                }
            ]
        ),
        encoding="utf-8",
    )
    document = load_corpus(corpus_path, limit=1, max_chars=10_000)[0]
    extraction = DocumentExtraction(
        entities=[
            EntityCandidate(
                local_id="fbi",
                name="FBI",
                type=EntityKind.ORGANIZATION,
                evidence=EvidenceCandidate(line_start=1, line_count=1),
            ),
            EntityCandidate(
                local_id="hoover",
                name="J. Edgar Hoover",
                type=EntityKind.PERSON,
                evidence=EvidenceCandidate(line_start=1, line_count=1),
            ),
        ],
        relationships=[
            RelationshipCandidate(
                source_entity_id="fbi",
                target_entity_id="hoover",
                type="is_related_to",
                source_mention="FBI",
                relation_phrase=",",
                target_mention="J. Edgar Hoover",
                support_reasoning="The names only occur in a list.",
                evidence=EvidenceCandidate(line_start=1, line_count=1),
            )
        ],
    )

    with pytest.raises(ValueError, match="not lexically supported"):
        validate_extraction_grounding(document, extraction)


def test_partition_records_rejected_relationship_without_silent_fallback(
    tmp_path: Path,
) -> None:
    corpus = _write_corpus(tmp_path / "corpus.json", count=1)
    document = load_corpus(corpus, limit=1, max_chars=10_000)[0]
    extraction = _extraction(1)
    extraction.relationships[0].relation_phrase = "wrote about"

    grounded, rejections = partition_extraction_grounding(document, extraction)

    assert grounded.entities == extraction.entities
    assert grounded.relationships == []
    assert len(rejections) == 1
    assert rejections[0].item_kind == "relationship"
    assert "relation_phrase is not an exact substring" in rejections[0].reason

    graph = build_graph(
        [document],
        [grounded],
        model="test-model",
        trace_id="crest_kg/test/rejection-ledger",
        max_budget_usd=1.0,
        observed_cost_usd=0.0,
        rejections=rejections,
    )
    assert graph.relationships == []
    assert graph.rejections == rejections


def test_grounding_rejects_pronominal_endpoint_mentions(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(
        json.dumps(
            [
                {
                    "title": "Pronoun",
                    "metadata": {"Document Number": "PRONOUN"},
                    "body_text": "Analyst 1 said it described the Archive.",
                }
            ]
        ),
        encoding="utf-8",
    )
    document = load_corpus(corpus_path, limit=1, max_chars=10_000)[0]
    extraction = _extraction(1)
    extraction.relationships[0].source_mention = "it"

    with pytest.raises(ValueError, match="may not be a pronoun"):
        validate_extraction_grounding(document, extraction)


def test_grounding_rejects_first_person_endpoint_mention(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(
        json.dumps(
            [
                {
                    "title": "First person",
                    "metadata": {"Document Number": "FIRST-PERSON"},
                    "body_text": "I described the Archive.",
                }
            ]
        ),
        encoding="utf-8",
    )
    document = load_corpus(corpus_path, limit=1, max_chars=10_000)[0]
    extraction = _extraction(1)
    extraction.relationships[0].source_mention = "I"

    with pytest.raises(ValueError, match="may not be a pronoun"):
        validate_extraction_grounding(document, extraction)


def test_grounding_materializes_exact_source_whitespace(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(
        json.dumps(
            [
                {
                    "title": "Wrapped",
                    "metadata": {"Document Number": "WRAPPED"},
                    "body_text": "Central Committee directed the\nKGB Institute.",
                }
            ]
        ),
        encoding="utf-8",
    )
    document = load_corpus(corpus_path, limit=1, max_chars=10_000)[0]
    extraction = DocumentExtraction(
        entities=[
            EntityCandidate(
                local_id="committee",
                name="Central Committee",
                type=EntityKind.ORGANIZATION,
                evidence=EvidenceCandidate(line_start=1, line_count=1),
            ),
            EntityCandidate(
                local_id="institute",
                name="KGB Institute",
                type=EntityKind.ORGANIZATION,
                evidence=EvidenceCandidate(line_start=2, line_count=1),
            ),
        ],
        relationships=[
            RelationshipCandidate(
                source_entity_id="committee",
                target_entity_id="institute",
                type="directed",
                source_mention="Central Committee",
                relation_phrase="directed the KGB",
                target_mention="KGB Institute",
                support_reasoning="The committee is the named subject directing the institute.",
                evidence=EvidenceCandidate(line_start=1, line_count=2),
            )
        ],
    )

    grounded, rejections = partition_extraction_grounding(document, extraction)

    assert rejections == []
    assert grounded.relationships[0].relation_phrase == "directed the\nKGB"


def test_grounding_accepts_explicit_acronym_binding(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(
        json.dumps(
            [
                {
                    "title": "Acronym",
                    "metadata": {"Document Number": "ACRONYM"},
                    "body_text": "The Central Intelligence Agency briefed Congress.",
                }
            ]
        ),
        encoding="utf-8",
    )
    document = load_corpus(corpus_path, limit=1, max_chars=10_000)[0]
    extraction = DocumentExtraction(
        entities=[
            EntityCandidate(
                local_id="cia",
                name="CIA",
                type=EntityKind.ORGANIZATION,
                evidence=EvidenceCandidate(line_start=1, line_count=1),
            ),
            EntityCandidate(
                local_id="congress",
                name="Congress",
                type=EntityKind.ORGANIZATION,
                evidence=EvidenceCandidate(line_start=1, line_count=1),
            ),
        ],
        relationships=[
            RelationshipCandidate(
                source_entity_id="cia",
                target_entity_id="congress",
                type="briefed",
                source_mention="Central Intelligence Agency",
                relation_phrase="briefed",
                target_mention="Congress",
                support_reasoning="The agency is the named subject briefing Congress.",
                evidence=EvidenceCandidate(line_start=1, line_count=1),
            )
        ],
    )

    validate_extraction_grounding(document, extraction)
    graph = build_graph(
        [document],
        [extraction],
        model="test-model",
        trace_id="crest_kg/test/acronym",
        max_budget_usd=1.0,
        observed_cost_usd=0.0,
    )
    assert graph.relationships[0].groundings[0].source_mention == (
        "Central Intelligence Agency"
    )


def test_grounding_rejects_mention_that_names_a_different_entity(tmp_path: Path) -> None:
    corpus = _write_corpus(tmp_path / "corpus.json", count=1)
    document = load_corpus(corpus, limit=1, max_chars=10_000)[0]
    extraction = _extraction(1)
    extraction.entities[0].name = "Researcher 1"

    with pytest.raises(ValueError, match="source_mention does not identify"):
        validate_extraction_grounding(document, extraction)


def test_relationship_predicates_are_normalized_to_snake_case(tmp_path: Path) -> None:
    corpus = _write_corpus(tmp_path / "corpus.json", count=1)
    documents = load_corpus(corpus, limit=1, max_chars=10_000)
    extraction = _extraction(1)
    extraction.relationships[0].relationship_type = "DESCRIBED-AS"

    graph = build_graph(
        documents,
        [extraction],
        model="test-model",
        trace_id="crest_kg/test/predicate-normalization",
        max_budget_usd=1.0,
        observed_cost_usd=0.0,
    )

    assert graph.relationships[0].relationship_type == "described_as"


def test_five_document_graph_is_grounded_and_integrity_checked(tmp_path: Path) -> None:
    corpus = _write_corpus(tmp_path / "corpus.json")
    documents = load_corpus(corpus, limit=5, max_chars=10_000)
    graph = build_graph(
        documents,
        [_extraction(number) for number in range(1, 6)],
        model="test-model",
        trace_id="crest_kg/test/five-documents",
        max_budget_usd=1.0,
        observed_cost_usd=0.0,
    )

    assert len(graph.documents) == 5
    assert len(graph.entities) == 6
    assert len(graph.relationships) == 5
    assert graph.schema_version == "crest-kg-v2"
    assert all(relationship.evidence for relationship in graph.relationships)
    assert all(relationship.groundings for relationship in graph.relationships)
    assert {
        grounding.source_mention
        for relationship in graph.relationships
        for grounding in relationship.groundings
    } == {f"Analyst {number}" for number in range(1, 6)}
    assert all(
        evidence.quote.startswith("Analyst ")
        for relationship in graph.relationships
        for evidence in relationship.evidence
    )
    assert {item.document_id for rel in graph.relationships for item in rel.evidence} == {
        "doc-1",
        "doc-2",
        "doc-3",
        "doc-4",
        "doc-5",
    }

    output = tmp_path / "validated.json"
    write_graph(graph, output, force=False)
    reloaded = validate_graph_file(output)
    assert reloaded == graph


def test_graph_budget_includes_prior_spend_and_unattributed_reserve(
    tmp_path: Path,
) -> None:
    corpus = _write_corpus(tmp_path / "corpus.json", count=1)
    documents = load_corpus(corpus, limit=1, max_chars=10_000)

    with pytest.raises(ValidationError, match="spend and reserve"):
        build_graph(
            documents,
            [_extraction(1)],
            model="test-model",
            trace_id="crest_kg/test/budget-lineage",
            max_budget_usd=0.10,
            observed_cost_usd=0.03,
            prior_observed_cost_usd=0.05,
            unattributed_cost_reserve_usd=0.03,
        )


def test_recover_extraction_revalidates_trace_and_records_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    corpus = _write_corpus(tmp_path / "corpus.json", count=1)
    document = load_corpus(corpus, limit=1, max_chars=10_000)[0]
    response = _extraction(1).model_dump_json(by_alias=True)
    model = "test-model"
    trace_id = "crest_kg/test/prior/documents/doc-1"
    monkeypatch.setattr(
        "llm_client.lookup_result",
        lambda candidate: {
            "response": response,
            "model": model,
            "cost": 0.004,
            "finish_reason": "stop",
            "prompt_ref": "crest_kg.crest_extraction@2",
        }
        if candidate == trace_id
        else None,
    )
    monkeypatch.setattr(
        "llm_client.diagnose_runtime_selected_attempt_receipt_for_trace",
        lambda candidate: SimpleNamespace(
            call_id=7,
            logical_call_id="llmcall_test",
            trace_id=candidate,
            selected_attempt_ordinal=0,
            schema_hash="schema-hash",
            raw_sha256="a" * 64,
            receipt_digest="b" * 64,
            resolved_model=model,
        ),
    )

    recovered = recover_extraction_from_trace(
        document,
        root_trace_id="crest_kg/test/prior",
        expected_model=model,
    )

    assert recovered is not None
    extraction, receipt, rejections = recovered
    assert extraction == _extraction(1)
    assert rejections == []
    assert receipt.document_id == "doc-1"
    assert receipt.trace_id == trace_id
    assert receipt.call_id == 7
    assert receipt.prompt_ref == "crest_kg.crest_extraction@2"
    assert receipt.observed_cost_usd == 0.004


def test_recover_extraction_returns_none_without_successful_terminal_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    corpus = _write_corpus(tmp_path / "corpus.json", count=1)
    document = load_corpus(corpus, limit=1, max_chars=10_000)[0]
    monkeypatch.setattr("llm_client.lookup_result", lambda _trace_id: None)

    assert (
        recover_extraction_from_trace(
            document,
            root_trace_id="crest_kg/test/interrupted",
            expected_model="test-model",
        )
        is None
    )


def test_typed_identity_does_not_merge_same_name_across_types(tmp_path: Path) -> None:
    corpus_path = tmp_path / "corpus.json"
    corpus_path.write_text(
        json.dumps(
            [
                {
                    "title": "One",
                    "metadata": {"Document Number": "ONE"},
                    "body_text": "The Soviet Union was described as a location.",
                },
                {
                    "title": "Two",
                    "metadata": {"Document Number": "TWO"},
                    "body_text": "The Soviet Union operated as an organization.",
                },
            ]
        ),
        encoding="utf-8",
    )
    documents = load_corpus(corpus_path, limit=2, max_chars=10_000)
    extractions = [
        DocumentExtraction(
            entities=[
                EntityCandidate(
                    local_id="ussr",
                    name="Soviet Union",
                    type=EntityKind.LOCATION,
                    evidence=EvidenceCandidate(line_start=1, line_count=1),
                )
            ],
            relationships=[],
        ),
        DocumentExtraction(
            entities=[
                EntityCandidate(
                    local_id="ussr",
                    name="Soviet Union",
                    type=EntityKind.ORGANIZATION,
                    evidence=EvidenceCandidate(line_start=1, line_count=1),
                )
            ],
            relationships=[],
        ),
    ]

    graph = build_graph(
        documents,
        extractions,
        model="test-model",
        trace_id="crest_kg/test/typed-identity",
        max_budget_usd=1.0,
        observed_cost_usd=0.0,
    )

    assert len(graph.entities) == 2
    assert {entity.entity_type for entity in graph.entities} == {
        EntityKind.LOCATION,
        EntityKind.ORGANIZATION,
    }


def test_write_refuses_silent_overwrite(tmp_path: Path) -> None:
    corpus = _write_corpus(tmp_path / "corpus.json", count=1)
    documents = load_corpus(corpus, limit=1, max_chars=10_000)
    graph = build_graph(
        documents,
        [_extraction(1)],
        model="test-model",
        trace_id="crest_kg/test/overwrite",
        max_budget_usd=1.0,
        observed_cost_usd=0.0,
    )
    output = tmp_path / "graph.json"
    write_graph(graph, output, force=False)

    with pytest.raises(ValueError, match="--force"):
        write_graph(graph, output, force=False)
