from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from crest_app.acquisition import extract_upload
from crest_app.main import create_app
from crest_app.models import GraphJob
from crest_app.services import CiaReadingRoomConnector, WorkbenchStore
from crest_pipeline import (
    GraphArtifact,
    RawDocument,
    load_document_records,
    load_selected_documents,
)


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
    assert connectors[1]["id"] == "user-uploads"
    assert connectors[1]["state"] == "unavailable"
    assert connectors[2]["id"] == "cia-reading-room-live"
    assert connectors[2]["state"] == "unavailable"

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


def test_uploaded_text_is_private_searchable_and_buildable(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("CREST_UPLOAD_ENABLED", "1")
    monkeypatch.setenv("CREST_BUILD_ENABLED", "1")
    monkeypatch.setenv("CREST_OPERATOR_TOKEN", "test-operator-token")
    app = create_app(data_dir=tmp_path)
    client = TestClient(app)
    auth = {"Authorization": "Bearer test-operator-token"}
    source = (
        b"Project Lantern source memorandum.\n"
        b"Analyst Rowan documented a KGB disinformation channel in Vienna.\n"
    )

    unauthorized = client.post(
        "/api/uploads",
        files={"file": ("lantern.txt", source, "text/plain")},
    )
    assert unauthorized.status_code == 403

    uploaded = client.post(
        "/api/uploads",
        data={"title": "Project Lantern memorandum"},
        files={"file": ("lantern.txt", source, "text/plain")},
        headers=auth,
    )
    assert uploaded.status_code == 201
    receipt = uploaded.json()
    document_id = receipt["document_id"]
    assert document_id.startswith("upload-")
    assert receipt["extraction_method"] == "plain-text"
    assert receipt["body_chars"] == len(source.decode().strip())

    duplicate = client.post(
        "/api/uploads",
        files={"file": ("renamed.txt", source, "text/plain")},
        headers=auth,
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["document_id"] == document_id
    assert duplicate.json()["duplicate"] is True

    public_search = client.post("/api/search", json={"query": "Lantern"})
    assert public_search.status_code == 200
    assert all(item["document_id"] != document_id for item in public_search.json()["results"])

    private_search = client.post(
        "/api/search",
        json={"query": "Lantern", "connector_id": "all"},
        headers=auth,
    )
    assert private_search.status_code == 200
    match = next(
        item for item in private_search.json()["results"] if item["document_id"] == document_id
    )
    assert match["connector_id"] == "user-uploads"

    assert client.get(f"/api/documents/{document_id}").status_code == 403
    detail = client.get(f"/api/documents/{document_id}", headers=auth)
    assert detail.status_code == 200
    assert detail.json()["connector_id"] == "user-uploads"
    assert "KGB disinformation channel" in detail.json()["body_preview"]

    original = client.get(f"/api/uploads/{document_id}/original", headers=auth)
    assert original.status_code == 200
    assert original.content == source

    submitted: list[str] = []

    class FakeRunner:
        def submit(self, payload):
            submitted.extend(payload.document_ids)
            now = datetime.now(timezone.utc)
            return GraphJob(
                id="upload-job",
                state="queued",
                request=payload,
                created_at=now,
                updated_at=now,
                progress_detail="Waiting for the extraction lane",
            )

    app.state.runner = FakeRunner()
    build = client.post(
        "/api/graphs",
        json={"document_ids": [document_id], "max_budget_usd": 0.05},
        headers=auth,
    )
    assert build.status_code == 202
    assert submitted == [document_id]
    loaded = app.state.catalog.load_selected([document_id], max_chars=4_000)
    assert loaded[0].manifest.document_id == document_id
    assert "KGB disinformation channel" in loaded[0].analysis_text

    deleted = client.delete(f"/api/uploads/{document_id}", headers=auth)
    assert deleted.status_code == 200
    assert client.get(f"/api/documents/{document_id}", headers=auth).status_code == 404


def test_upload_rejects_unsupported_and_oversized_inputs(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("CREST_UPLOAD_ENABLED", "1")
    monkeypatch.setenv("CREST_OPERATOR_TOKEN", "test-operator-token")
    monkeypatch.setenv("CREST_MAX_UPLOAD_BYTES", "10")
    client = TestClient(create_app(data_dir=tmp_path))
    auth = {"Authorization": "Bearer test-operator-token"}

    oversized = client.post(
        "/api/uploads",
        files={"file": ("large.txt", b"more than ten bytes", "text/plain")},
        headers=auth,
    )
    assert oversized.status_code == 413

    unsupported = client.post(
        "/api/uploads",
        files={"file": ("archive.zip", b"PK\x03\x04", "application/zip")},
        headers=auth,
    )
    assert unsupported.status_code == 415


def test_pdf_text_and_image_ocr_share_the_upload_contract(monkeypatch) -> None:
    import fitz
    from PIL import Image
    from io import BytesIO

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Project Aster links Rowan to Vienna intelligence reporting.")
    pdf_bytes = pdf.tobytes()
    pdf.close()
    extracted_pdf = extract_upload(
        pdf_bytes,
        filename="aster.pdf",
        supplied_title=None,
        max_pages=5,
        max_extracted_chars=10_000,
        max_image_pixels=10_000_000,
    )
    assert extracted_pdf.extraction_method == "pdf-text"
    assert "Project Aster" in extracted_pdf.body_text

    monkeypatch.setattr(
        "crest_app.acquisition._ocr_image",
        lambda image: "Scanned memorandum identifies Rowan in Vienna.",
    )
    image = Image.new("RGB", (320, 100), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    extracted_image = extract_upload(
        buffer.getvalue(),
        filename="scan.png",
        supplied_title="Scanned field note",
        max_pages=5,
        max_extracted_chars=10_000,
        max_image_pixels=10_000_000,
    )
    assert extracted_image.extraction_method == "image-ocr"
    assert extracted_image.title == "Scanned field note"


def test_record_loader_preserves_explicit_uploaded_selection_order() -> None:
    records = [
        RawDocument(
            title="Second",
            metadata={"Document Number": "upload-second"},
            body_text="Second document source text.",
        ),
        RawDocument(
            title="First",
            metadata={"Document Number": "upload-first"},
            body_text="First document source text.",
        ),
    ]
    loaded = load_document_records(
        records,
        document_ids=["upload-first", "upload-second"],
        max_chars=4_000,
        corpus_label="crest-workbench-catalog",
    )
    assert [item.manifest.document_id for item in loaded] == [
        "upload-first",
        "upload-second",
    ]
    assert all(item.manifest.corpus_path == "crest-workbench-catalog" for item in loaded)


def test_graphs_from_private_sources_are_operator_only(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("CREST_OPERATOR_TOKEN", "test-operator-token")
    store = WorkbenchStore(tmp_path)
    graph = GraphArtifact.model_validate_json(
        (ROOT / "cia_kg_output" / "validated_5_documents_relationship_binding_v2.json").read_text(
            encoding="utf-8"
        )
    )
    store.save_graph(
        "private-graph",
        graph,
        connector_ids=["user-uploads"],
    )
    client = TestClient(create_app(store=store))
    auth = {"Authorization": "Bearer test-operator-token"}

    public_ids = [item["id"] for item in client.get("/api/graphs").json()["graphs"]]
    assert "private-graph" not in public_ids
    assert client.get("/api/graphs/private-graph").status_code == 403
    assert client.get("/api/graphs/private-graph/export.json").status_code == 403

    private_graphs = client.get("/api/graphs", headers=auth).json()["graphs"]
    summary = next(item for item in private_graphs if item["id"] == "private-graph")
    assert summary["restricted"] is True
    assert client.get("/api/graphs/private-graph", headers=auth).status_code == 200
    assert (
        client.get("/api/graphs/private-graph/export.json", headers=auth).status_code
        == 200
    )


def test_cia_connector_activates_only_when_search_and_document_acquisition_work(
    monkeypatch,
) -> None:
    connector = CiaReadingRoomConnector()
    result_url = "https://www.cia.gov/readingroom/document/cia-test-1"
    search_payload = {
        "web": {
            "total": 1,
            "results": [
                {
                    "url": result_url,
                    "title": "<b>Test memorandum</b>",
                    "snippet": "A <em>grounded</em> source result.",
                }
            ],
        }
    }
    document_html = b"""
        <h1 class="documentFirstHeading">Test memorandum</h1>
        <div class="field-label-inline"><div class="field-label">Collection:</div><div class="field-item">CREST</div></div>
        <div class="field-name-body"><div class="field-item">Rowan reported from Vienna.</div></div>
    """

    def fake_get(url: str):
        if url.startswith(connector.search_endpoint):
            import json

            return 200, json.dumps(search_payload).encode(), url
        return 200, document_html, result_url

    monkeypatch.setattr(connector, "_get", fake_get)
    probe = connector.probe()
    assert probe.connector.state == "available"
    assert probe.search_http_status == 200
    assert probe.document_http_status == 200
    detail = connector.detail("cia-test-1")
    assert detail.connector_id == "cia-reading-room-live"
    assert detail.metadata["Collection"] == "CREST"
    assert "Rowan reported" in detail.body_preview
