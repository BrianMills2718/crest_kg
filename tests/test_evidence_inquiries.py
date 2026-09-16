from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from crest_app.briefing import generate_evidence_brief, validate_provider_brief
from crest_app.main import create_app
from crest_app.models import (
    BriefFinding,
    CollectionCreate,
    EvidenceBrief,
    EvidenceInquiry,
    EvidenceInquiryRequest,
    GraphJob,
    ProviderEvidenceBrief,
)
from crest_app.retrieval import RetrievalDocument, rank_evidence
from crest_app.services import EvidenceInquiryRunner, WorkbenchStore


def _evidence():
    return rank_evidence(
        "Who organized the Vienna exercise and what date conflict exists?",
        [
            RetrievalDocument(
                document_id="meridian-one",
                connector_id="user-uploads",
                title="Coordination note",
                body_text=(
                    "The Harbor Institute organized the Vienna exercise on "
                    "14 May 1987."
                ),
            ),
            RetrievalDocument(
                document_id="meridian-two",
                connector_id="user-uploads",
                title="Observer correction",
                body_text=(
                    "The Vienna exercise began on 16 May 1987, not 14 May. "
                    "Harbor Institute convened the group."
                ),
            ),
        ],
        limit=4,
    )


def _completed_brief(evidence) -> EvidenceBrief:
    return EvidenceBrief(
        answer_status="partial",
        synthesis="Harbor Institute organized the exercise, while the date is disputed.",
        synthesis_citation_ids=[item.id for item in evidence],
        findings=[
            BriefFinding(
                statement="The sources give different May start dates.",
                classification="contradiction",
                citation_ids=[item.id for item in evidence],
            )
        ],
        unresolved_questions=["Which date governed the final operational record?"],
        model="test-model",
        trace_id="crest_kg/inquiries/test",
        observed_cost_usd=0.001,
    )


def test_brief_validation_rejects_unknown_citations_and_handles_no_evidence() -> None:
    evidence = _evidence()
    invalid = ProviderEvidenceBrief(
        answer_status="answered",
        synthesis="A plausible but invalid answer.",
        synthesis_citation_ids=["evidence-00000000000000000000"],
        findings=[
            BriefFinding(
                statement="Unsupported.",
                classification="support",
                citation_ids=["evidence-00000000000000000000"],
            )
        ],
    )
    with pytest.raises(ValueError, match="unknown chunks"):
        validate_provider_brief(invalid, evidence)

    empty = generate_evidence_brief(
        question="What radio frequency was used?",
        collection_title="Project Meridian",
        evidence=[],
        trace_id="crest_kg/inquiries/empty",
        max_budget_usd=0.06,
        max_output_tokens=1_800,
    )
    assert empty.answer_status == "insufficient"
    assert empty.observed_cost_usd == 0
    assert empty.model == "deterministic-no-evidence"


def test_brief_declares_reasoning_effort_for_current_llm_contract(monkeypatch) -> None:
    captured = {}
    evidence = _evidence()

    def call_llm_structured(_model, _messages, **kwargs):
        captured.update(kwargs)
        return (
            ProviderEvidenceBrief(
                answer_status="answered",
                synthesis="The Institute organized the exercise.",
                synthesis_citation_ids=[evidence[0].id],
                findings=[
                    BriefFinding(
                        statement="The Institute organized the exercise.",
                        classification="support",
                        citation_ids=[evidence[0].id],
                    )
                ],
            ),
            SimpleNamespace(cost=0.001),
        )

    monkeypatch.setitem(
        sys.modules,
        "llm_client",
        SimpleNamespace(
            call_llm_structured=call_llm_structured,
            get_model=lambda *_args, **_kwargs: "openrouter/openai/gpt-5.6-luna",
            render_prompt=lambda *_args, **_kwargs: [{"role": "user", "content": "test"}],
        ),
    )
    generated = generate_evidence_brief(
        question="Who organized the exercise?",
        collection_title="Project Meridian",
        evidence=evidence,
        trace_id="crest_kg/inquiries/reasoning-contract",
        max_budget_usd=0.03,
        max_output_tokens=800,
    )

    assert generated.answer_status == "answered"
    assert captured["reasoning_effort"] == "medium"


def test_inquiry_runner_persists_completion_failure_and_restart(
    tmp_path: Path, monkeypatch
) -> None:
    store = WorkbenchStore(tmp_path)
    collection = store.create_collection(CollectionCreate(title="Project Meridian"))
    evidence = _evidence()

    class ImmediateLane:
        def submit(self, function, *args):
            function(*args)

    monkeypatch.setattr(
        "crest_app.services.generate_evidence_brief",
        lambda **kwargs: _completed_brief(kwargs["evidence"]),
    )
    runner = EvidenceInquiryRunner(store, ImmediateLane())
    submitted = runner.submit(
        EvidenceInquiryRequest(
            collection_id=collection.id,
            question="Who organized the Vienna exercise and what date conflict exists?",
        ),
        collection=collection,
        evidence=evidence,
    )
    completed = store.get_inquiry(submitted.id)
    assert completed.state == "completed"
    assert completed.brief and completed.brief.findings

    interrupted = completed.model_copy(
        update={
            "id": "inquiry-" + "a" * 32,
            "state": "running",
            "brief": None,
            "error": None,
        }
    )
    store.save_inquiry(interrupted)
    restarted = WorkbenchStore(tmp_path)
    recovered = restarted.get_inquiry(interrupted.id)
    assert recovered.state == "failed"
    assert "restart" in recovered.error.lower()
    assert recovered.evidence == evidence

    def fail_brief(**_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr("crest_app.services.generate_evidence_brief", fail_brief)
    failed = EvidenceInquiryRunner(restarted, ImmediateLane()).submit(
        EvidenceInquiryRequest(
            collection_id=collection.id,
            question="Who organized the Vienna exercise?",
        ),
        collection=collection,
        evidence=evidence,
    )
    failed = restarted.get_inquiry(failed.id)
    assert failed.state == "failed"
    assert failed.evidence == evidence
    assert "provider unavailable" in failed.error


def test_private_inquiry_api_history_and_cited_graph_handoff(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("CREST_UPLOAD_ENABLED", "1")
    monkeypatch.setenv("CREST_BUILD_ENABLED", "1")
    monkeypatch.setenv("CREST_BRIEF_ENABLED", "1")
    monkeypatch.setenv("CREST_OPERATOR_TOKEN", "test-operator-token")
    monkeypatch.setenv("CREST_MAX_BRIEF_BUDGET_USD", "0.10")
    app = create_app(data_dir=tmp_path)
    assert app.state.runner.lane is app.state.inquiry_runner.lane
    client = TestClient(app)
    auth = {"Authorization": "Bearer test-operator-token"}
    collection = client.post(
        "/api/collections",
        json={"title": "Project Meridian"},
        headers=auth,
    ).json()
    document_ids = []
    for index, body in enumerate(
        [
            b"The Harbor Institute organized the Vienna exercise on 14 May 1987.",
            b"The Vienna exercise began on 16 May 1987, not 14 May.",
        ]
    ):
        receipt = client.post(
            "/api/uploads",
            files={"file": (f"meridian-{index}.txt", body, "text/plain")},
            headers=auth,
        )
        document_ids.append(receipt.json()["document_id"])
    client.put(
        f"/api/collections/{collection['id']}/documents",
        json={"document_ids": document_ids},
        headers=auth,
    )

    captured: list[EvidenceInquiry] = []

    class FakeInquiryRunner:
        def submit(self, payload, *, collection, evidence):
            now = datetime.now(timezone.utc)
            inquiry = EvidenceInquiry(
                id="inquiry-" + "b" * 32,
                state="queued",
                request=payload,
                collection_title=collection.title,
                evidence=evidence,
                created_at=now,
                updated_at=now,
                progress_detail="Waiting for the provider lane",
            )
            app.state.store.save_inquiry(inquiry)
            captured.append(inquiry)
            return inquiry

    app.state.inquiry_runner = FakeInquiryRunner()
    request = {
        "collection_id": collection["id"],
        "question": "Who organized the Vienna exercise and what date conflict exists?",
        "max_budget_usd": 0.06,
    }
    assert client.post("/api/inquiries", json=request).status_code == 403
    too_expensive = client.post(
        "/api/inquiries",
        json={**request, "max_budget_usd": 0.11},
        headers=auth,
    )
    assert too_expensive.status_code == 422
    submitted = client.post("/api/inquiries", json=request, headers=auth)
    assert submitted.status_code == 202
    assert len(captured[0].evidence) == 2
    assert client.get("/api/inquiries").status_code == 403
    assert client.get("/api/inquiries", headers=auth).json()["inquiries"][0][
        "id"
    ] == captured[0].id

    completed = captured[0].model_copy(
        update={
            "state": "completed",
            "brief": _completed_brief([captured[0].evidence[0]]),
            "trace_id": "crest_kg/inquiries/test",
        }
    )
    app.state.store.save_inquiry(completed)
    submitted_graph_ids: list[str] = []

    class FakeGraphRunner:
        def submit(self, payload):
            submitted_graph_ids.extend(payload.document_ids)
            now = datetime.now(timezone.utc)
            return GraphJob(
                id="graph-job",
                state="queued",
                request=payload,
                created_at=now,
                updated_at=now,
                progress_detail="Waiting",
            )

    app.state.runner = FakeGraphRunner()
    base_graph = {
        "collection_id": collection["id"],
        "inquiry_id": completed.id,
        "max_budget_usd": 0.05,
    }
    uncited = client.post(
        "/api/graphs",
        json={**base_graph, "document_ids": [document_ids[1]]},
        headers=auth,
    )
    assert uncited.status_code == 422
    assert "not cited" in uncited.json()["detail"]
    cited = client.post(
        "/api/graphs",
        json={
            **base_graph,
            "document_ids": [completed.evidence[0].document_id],
        },
        headers=auth,
    )
    assert cited.status_code == 202
    assert submitted_graph_ids == [completed.evidence[0].document_id]
