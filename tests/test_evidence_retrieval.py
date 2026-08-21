from __future__ import annotations

from pathlib import Path

from crest_app.models import BriefFinding, ProviderEvidenceBrief
from crest_app.retrieval import (
    RetrievalDocument,
    evaluate_retrieval_fixture,
    rank_evidence,
)


ROOT = Path(__file__).parents[1]


def test_frozen_evidence_retrieval_fixtures_pass() -> None:
    expected_splits = {
        "v5": {"regression", "negative"},
        "v6": {"regression", "negative"},
        "v7": {"negative"},
        "v8": {"regression", "negative"},
        "v9": {"regression", "negative"},
        "v10": {"regression", "negative"},
        "v11": {"regression", "negative"},
        "v12": {"regression", "negative"},
    }
    for version, splits in expected_splits.items():
        result = evaluate_retrieval_fixture(
            ROOT / "evaluation" / f"evidence_retrieval_set_{version}.json"
        )
        assert result["passed"], result
        assert {item["split"] for item in result["cases"]} == splits


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
