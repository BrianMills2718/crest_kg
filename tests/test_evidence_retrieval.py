from __future__ import annotations

import json
import re
from pathlib import Path

from crest_app.models import BriefFinding, ProviderEvidenceBrief
from crest_app.retrieval import (
    RetrievalDocument,
    chunk_document,
    evaluate_retrieval_fixture,
    rank_evidence,
)


ROOT = Path(__file__).parents[1]


def test_frozen_evidence_retrieval_fixtures_do_not_regress() -> None:
    """Every frozen fixture is checked, and only recorded failures are tolerated.

    Asserting a blanket ``passed`` here would be false: nineteen of the 136
    frozen cases are known to fail. Asserting nothing would repeat the mistake
    that let sixteen abstention cases regress unnoticed on 2026-08-20, when the
    harness only ever ran the newest fixture. So this is a ratchet against the
    measured baseline in ``evaluation/known_failing_cases.json``: a case outside
    that list must never start failing, and the list must only shrink.

    Verdicts replay from cache, so the suite makes no model calls.
    """

    baseline = json.loads(
        (ROOT / "evaluation" / "known_failing_cases.json").read_text(encoding="utf-8")
    )
    allowed = {name: set(cases) for name, cases in baseline["failing"].items()}

    fixtures = sorted(
        (ROOT / "evaluation").glob("evidence_retrieval_set_v*.json"),
        key=lambda path: int(re.search(r"_v(\d+)\.json$", path.name).group(1)),
    )
    assert fixtures, "no frozen fixtures found"

    new_failures: dict[str, list[str]] = {}
    fixed: dict[str, list[str]] = {}
    for fixture in fixtures:
        result = evaluate_retrieval_fixture(fixture, allow_calls=False)
        failing = {item["case_id"] for item in result["cases"] if not item["passed"]}
        tolerated = allowed.get(fixture.name, set())
        if failing - tolerated:
            new_failures[fixture.name] = sorted(failing - tolerated)
        if tolerated - failing:
            fixed[fixture.name] = sorted(tolerated - failing)

    assert not new_failures, (
        "cases outside the recorded baseline are now failing: "
        f"{new_failures}. Fix them, or justify and re-record the baseline."
    )
    assert not fixed, (
        "these cases now pass and must be removed from "
        f"evaluation/known_failing_cases.json: {fixed}"
    )


def test_evidence_chunks_preserve_exact_offsets_and_stable_ids() -> None:
    document = RetrievalDocument(
        document_id="doc-one",
        connector_id="bundled-crest",
        title="Vienna field note",
        body_text=(
            "The Harbor Institute organized the Vienna exercise. "
            "Observers recorded the start date as 16 May 1987."
        ),
    )
    first = rank_evidence("Who organized the Vienna exercise?", [document])
    second = rank_evidence("Who organized the Vienna exercise?", [document])
    assert first
    assert [item.id for item in first] == [item.id for item in second]
    assert all(
        document.body_text[item.start_char : item.end_char] == item.text
        for item in first
    )


def test_chunking_prefers_strongest_exact_boundaries() -> None:
    paragraph = (
        "Project Telltale ledger states the Bronze Wren Office coordinated the "
        "harbor rehearsal on 4 April 1996. Evidence remains archived in bay seven."
    )
    document = RetrievalDocument(
        document_id="doc-telltale",
        connector_id="bundled-crest",
        title="Project Telltale repeated ledger",
        body_text="\n\n".join([paragraph] * 3),
    )
    chunks = chunk_document(
        document,
        max_chunk_chars=200,
        overlap_chars=0,
    )
    assert [(item.start_char, item.end_char) for item in chunks] == [
        (0, 143),
        (145, 288),
        (290, 433),
    ]
    assert all(
        document.body_text[item.start_char : item.end_char] == item.text
        for item in chunks
    )

    sentence_body = "A" * 120 + ". " + "B" * 50 + " " + "C" * 80
    sentence_document = RetrievalDocument(
        document_id="doc-sentence-boundary",
        connector_id="bundled-crest",
        title="Sentence boundary probe",
        body_text=sentence_body,
    )
    sentence_chunks = chunk_document(
        sentence_document,
        max_chunk_chars=200,
        overlap_chars=0,
    )
    assert (sentence_chunks[0].start_char, sentence_chunks[0].end_char) == (
        0,
        121,
    )
    assert sentence_chunks[0].text.endswith(".")
    assert all(
        sentence_body[item.start_char : item.end_char] == item.text
        for item in sentence_chunks
    )


def test_provider_brief_contract_rejects_duplicate_citations() -> None:
    finding = {
        "statement": "The documents disagree.",
        "classification": "contradiction",
        "citation_ids": ["evidence-00000000000000000000"] * 2,
    }
    try:
        BriefFinding.model_validate(finding)
    except ValueError as exc:
        assert "unique" in str(exc)
    else:  # pragma: no cover - protects a contract regression
        raise AssertionError("duplicate citations were accepted")

    insufficient = ProviderEvidenceBrief(
        answer_status="insufficient",
        synthesis="The retained evidence does not answer the question.",
        synthesis_citation_ids=[],
        findings=[],
        unresolved_questions=["What additional source records the answer?"],
    )
    assert insufficient.answer_status == "insufficient"
