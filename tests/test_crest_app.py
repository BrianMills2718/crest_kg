from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from crest_app.main import create_app
from crest_app.models import GraphJob
from crest_pipeline import load_selected_documents


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "cia_documents" / "disinformation_complete_20250517_002848.json"


def test_search_document_graph_and_export_read_boundaries(tmp_path: Path) -> None:
    client = TestClient(create_app(data_dir=tmp_path))

    capabilities = client.get("/api/capabilities")
    assert capabilities.status_code == 200
    connectors = capabilities.json()["connectors"]
    assert connectors[0]["id"] == "bundled-crest"
    assert connectors[0]["state"] == "available"
    assert connectors[0]["document_count"] == 40
    assert connectors[1]["id"] == "cia-reading-room-live"
    assert connectors[1]["state"] == "unavailable"

    search = client.post(
        "/api/search",
        json={"query": "disinformation", "connector_id": "bundled-crest", "limit": 10},
    )
    assert search.status_code == 200
    payload = search.json()
    assert payload["total_matches"] >= len(payload["results"]) > 0
    document_id = payload["results"][0]["document_id"]
    assert payload["results"][0]["snippet"]

    document = client.get(f"/api/documents/{document_id}")
    assert document.status_code == 200
    assert document.json()["document_id"] == document_id
    assert document.json()["body_chars"] >= len(document.json()["body_preview"])
    assert len(document.json()["body_sha256"]) == 64

    graphs = client.get("/api/graphs")
    assert graphs.status_code == 200
    assert graphs.json()["graphs"][0]["id"] == "example-fixed-v2"
    graph = client.get("/api/graphs/example-fixed-v2")
    assert graph.status_code == 200
    assert graph.json()["schema_version"] == "crest-kg-v2"
    exported = client.get("/api/graphs/example-fixed-v2/export.json")
    assert exported.status_code == 200
    assert "attachment" in exported.headers["content-disposition"]


def test_graph_build_requires_operator_and_enforces_server_budget(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("CREST_BUILD_ENABLED", "1")
    monkeypatch.setenv("CREST_OPERATOR_TOKEN", "test-operator-token")
    monkeypatch.setenv("CREST_MAX_BUILD_BUDGET_USD", "0.20")
    app = create_app(data_dir=tmp_path)
    client = TestClient(app)
    document_id = client.post(
        "/api/search", json={"query": "disinformation"}
    ).json()["results"][0]["document_id"]
    request = {
        "document_ids": [document_id],
        "max_chars_per_document": 5000,
        "max_budget_usd": 0.10,
        "refine_relationships": False,
    }

    unauthorized = client.post("/api/graphs", json=request)
    assert unauthorized.status_code == 403

    too_expensive = client.post(
        "/api/graphs",
        json={**request, "max_budget_usd": 0.21},
        headers={"Authorization": "Bearer test-operator-token"},
    )
    assert too_expensive.status_code == 422

    submitted: list[str] = []

    class FakeRunner:
        def submit(self, payload):
            submitted.extend(payload.document_ids)
            now = datetime.now(timezone.utc)
            return GraphJob(
                id="job-1",
                state="queued",
                request=payload,
                created_at=now,
                updated_at=now,
                progress_detail="Waiting for the extraction lane",
            )

    app.state.runner = FakeRunner()
    authorized = client.post(
        "/api/graphs",
        json=request,
        headers={"Authorization": "Bearer test-operator-token"},
    )
    assert authorized.status_code == 202
    assert authorized.json()["state"] == "queued"
    assert submitted == [document_id]


def test_explicit_selection_uses_canonical_pipeline_loader() -> None:
    all_documents = load_selected_documents(
        CORPUS,
        document_ids=["05259029", "05798947"],
        max_chars=4_000,
    )

    assert [item.manifest.document_id for item in all_documents] == [
        "05259029",
        "05798947",
    ]
    assert all(item.manifest.analyzed_end <= 4_000 for item in all_documents)
