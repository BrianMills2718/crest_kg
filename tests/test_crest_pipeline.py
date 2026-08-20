from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from crest_pipeline import (
    DocumentExtraction,
    EntityCandidate,
    EntityKind,
    EvidenceCandidate,
    RelationshipCandidate,
    build_graph,
    load_corpus,
    validate_extraction_grounding,
    validate_graph_file,
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
                evidence=EvidenceCandidate(line_start=1, line_end=1),
            ),
            EntityCandidate(
                local_id="archive",
                name="Archive",
                type=EntityKind.ORGANIZATION,
                evidence=EvidenceCandidate(line_start=1, line_end=1),
            ),
        ],
        relationships=[
            RelationshipCandidate(
                source_entity_id="analyst",
                target_entity_id="archive",
                type="described",
                evidence=EvidenceCandidate(line_start=1, line_end=1),
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
                    evidence=EvidenceCandidate(line_start=1, line_end=1),
                )
            ],
            relationships=[
                RelationshipCandidate(
                    source_entity_id="known",
                    target_entity_id="missing",
                    type="mentions",
                    evidence=EvidenceCandidate(line_start=1, line_end=1),
                )
            ],
        )


def test_grounding_rejects_lines_outside_supplied_document(tmp_path: Path) -> None:
    corpus = _write_corpus(tmp_path / "corpus.json", count=1)
    document = load_corpus(corpus, limit=1, max_chars=10_000)[0]
    extraction = DocumentExtraction(
        entities=[
            EntityCandidate(
                local_id="archive",
                name="Archive",
                type=EntityKind.ORGANIZATION,
                evidence=EvidenceCandidate(line_start=2, line_end=2),
            )
        ],
        relationships=[],
    )

    with pytest.raises(ValueError, match="exceeds"):
        validate_extraction_grounding(document, extraction)


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
    assert all(relationship.evidence for relationship in graph.relationships)
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
                    evidence=EvidenceCandidate(line_start=1, line_end=1),
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
                    evidence=EvidenceCandidate(line_start=1, line_end=1),
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
