"""FastAPI entry point for the CREST research workbench."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response

from .acquisition import (
    AcquisitionError,
    ExtractionUnavailable,
    UnsupportedUpload,
    extract_upload,
)
from .models import (
    Capabilities,
    ConnectorProbe,
    ConnectorStatus,
    DocumentDetail,
    GraphBuildRequest,
    GraphJob,
    GraphList,
    SearchRequest,
    SearchResponse,
    UploadedDocumentList,
    UploadedDocumentReceipt,
)
from .services import (
    ConnectorUnavailable,
    CorpusCatalog,
    GraphJobRunner,
    WorkbenchStore,
    persist_extracted_upload,
    request_is_operator,
)


ROOT = Path(__file__).parents[1]
WEB_ROOT = ROOT / "web"


def create_app(
    *,
    data_dir: Path | None = None,
    catalog: CorpusCatalog | None = None,
    store: WorkbenchStore | None = None,
) -> FastAPI:
    app = FastAPI(
        title="CREST research workbench API",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        root_path=os.getenv("CREST_ROOT_PATH", ""),
    )
    resolved_store = store or WorkbenchStore(
        data_dir
        or Path(os.getenv("CREST_DATA_DIR", "/tmp/crest-workbench-data"))
    )
    resolved_catalog = catalog or CorpusCatalog(store=resolved_store)
    if resolved_catalog.store is None:
        resolved_catalog.store = resolved_store
    runner = GraphJobRunner(resolved_store, resolved_catalog)
    app.state.catalog = resolved_catalog
    app.state.store = resolved_store
    app.state.runner = runner

    def operator_status(
        authorization: str | None, tailscale_login: str | None
    ) -> bool:
        return request_is_operator(
            supplied_token=authorization,
            tailscale_login=tailscale_login,
        )

    def require_operator(
        authorization: str | None, tailscale_login: str | None, *, action: str
    ) -> None:
        if not operator_status(authorization, tailscale_login):
            raise HTTPException(
                status_code=403,
                detail=f"{action} requires an authorized operator",
            )

    def upload_enabled() -> bool:
        return os.getenv("CREST_UPLOAD_ENABLED", "0") == "1"

    def max_upload_bytes() -> int:
        return int(os.getenv("CREST_MAX_UPLOAD_BYTES", str(15 * 1024 * 1024)))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "crest-workbench",
            "source_revision": os.getenv("SOURCE_REVISION", "development"),
        }

    @app.get("/api/capabilities", response_model=Capabilities)
    def capabilities(
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> Capabilities:
        is_operator = operator_status(authorization, tailscale_login)
        uploads_enabled = upload_enabled()
        return Capabilities(
            source_revision=os.getenv("SOURCE_REVISION", "development"),
            connectors=[
                ConnectorStatus(
                    id="bundled-crest",
                    label="Bundled CREST archive",
                    state="available",
                    detail="Tracked CIA Reading Room documents with searchable source text.",
                    document_count=resolved_catalog.count,
                ),
                ConnectorStatus(
                    id="user-uploads",
                    label="Private uploads",
                    state="available" if uploads_enabled else "unavailable",
                    detail=(
                        "Operator-only PDF, image, and text ingestion with local OCR."
                        if uploads_enabled
                        else "Document upload is disabled on this server."
                    ),
                    document_count=(
                        resolved_catalog.upload_count if is_operator else None
                    ),
                ),
                resolved_catalog.cia_connector.last_status,
            ],
            graph_build_enabled=os.getenv("CREST_BUILD_ENABLED", "0") == "1",
            graph_build_authorized=operator_status(authorization, tailscale_login),
            max_documents_per_build=3,
            max_build_budget_usd=float(
                os.getenv("CREST_MAX_BUILD_BUDGET_USD", "0.25")
            ),
            document_upload_enabled=uploads_enabled,
            document_upload_authorized=is_operator,
            max_upload_bytes=max_upload_bytes(),
        )

    @app.post("/api/search", response_model=SearchResponse)
    def search(
        payload: SearchRequest,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> SearchResponse:
        is_operator = operator_status(authorization, tailscale_login)
        if payload.connector_id in {"user-uploads", "cia-reading-room-live"}:
            require_operator(
                authorization,
                tailscale_login,
                action="This source connector",
            )
        try:
            return resolved_catalog.search(
                payload.query,
                limit=payload.limit,
                connector_id=payload.connector_id,
                include_uploads=is_operator,
            )
        except ConnectorUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post(
        "/api/connectors/cia-reading-room-live/probe",
        response_model=ConnectorProbe,
    )
    def probe_cia_connector(
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> ConnectorProbe:
        require_operator(
            authorization,
            tailscale_login,
            action="Connector probing",
        )
        return resolved_catalog.cia_connector.probe()

    @app.post(
        "/api/uploads",
        response_model=UploadedDocumentReceipt,
        status_code=201,
    )
    async def upload_document(
        file: UploadFile = File(...),
        title: str | None = Form(default=None, max_length=200),
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> UploadedDocumentReceipt:
        if not upload_enabled():
            raise HTTPException(status_code=503, detail="Document upload is disabled")
        require_operator(
            authorization,
            tailscale_login,
            action="Document upload",
        )
        ceiling = max_upload_bytes()
        source_bytes = await file.read(ceiling + 1)
        await file.close()
        if not source_bytes:
            raise HTTPException(status_code=422, detail="The uploaded file is empty")
        if len(source_bytes) > ceiling:
            raise HTTPException(
                status_code=413,
                detail=f"Upload exceeds the {ceiling:,}-byte server limit",
            )
        try:
            extracted = extract_upload(
                source_bytes,
                filename=file.filename,
                supplied_title=title,
                max_pages=int(os.getenv("CREST_MAX_UPLOAD_PAGES", "50")),
                max_extracted_chars=int(
                    os.getenv("CREST_MAX_EXTRACTED_CHARS", "1000000")
                ),
                max_image_pixels=int(
                    os.getenv("CREST_MAX_IMAGE_PIXELS", "40000000")
                ),
            )
        except UnsupportedUpload as exc:
            raise HTTPException(status_code=415, detail=str(exc)) from exc
        except ExtractionUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except AcquisitionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return persist_extracted_upload(resolved_store, extracted, source_bytes)

    @app.get("/api/uploads", response_model=UploadedDocumentList)
    def list_uploads(
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> UploadedDocumentList:
        require_operator(
            authorization,
            tailscale_login,
            action="Private upload listing",
        )
        return UploadedDocumentList(
            documents=[
                resolved_store._upload_receipt(record)
                for record in resolved_store.list_uploaded_documents()
            ]
        )

    @app.get("/api/uploads/{document_id}/original")
    def uploaded_original(
        document_id: str,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> FileResponse:
        require_operator(
            authorization,
            tailscale_login,
            action="Private source download",
        )
        try:
            record = resolved_store.get_uploaded_document(document_id)
            path = resolved_store.uploaded_source_path(document_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Upload not found") from exc
        return FileResponse(
            path,
            media_type=record.media_type,
            filename=record.original_filename,
        )

    @app.delete("/api/uploads/{document_id}", response_model=UploadedDocumentReceipt)
    def delete_upload(
        document_id: str,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> UploadedDocumentReceipt:
        require_operator(
            authorization,
            tailscale_login,
            action="Private upload deletion",
        )
        try:
            record = resolved_store.delete_uploaded_document(document_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Upload not found") from exc
        return resolved_store._upload_receipt(record)

    @app.get("/api/documents/{document_id}", response_model=DocumentDetail)
    def document(
        document_id: str,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> DocumentDetail:
        try:
            connector_id = resolved_catalog.connector_for(document_id)
            if connector_id != "bundled-crest":
                require_operator(
                    authorization,
                    tailscale_login,
                    action="Private or live document access",
                )
            return resolved_catalog.detail(document_id)
        except ConnectorUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Document not found") from exc

    @app.post("/api/graphs", response_model=GraphJob, status_code=202)
    def build_graph(
        payload: GraphBuildRequest,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> GraphJob:
        if os.getenv("CREST_BUILD_ENABLED", "0") != "1":
            raise HTTPException(status_code=503, detail="Graph building is disabled")
        if not operator_status(authorization, tailscale_login):
            raise HTTPException(
                status_code=403,
                detail="Graph building requires an authorized operator",
            )
        budget_ceiling = float(os.getenv("CREST_MAX_BUILD_BUDGET_USD", "0.25"))
        if payload.max_budget_usd > budget_ceiling:
            raise HTTPException(
                status_code=422,
                detail=f"Requested budget exceeds the ${budget_ceiling:.2f} server ceiling",
            )
        unknown_ids = [
            document_id
            for document_id in payload.document_ids
            if not resolved_catalog.contains(document_id)
        ]
        if unknown_ids:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown document IDs: {', '.join(unknown_ids)}",
            )
        return app.state.runner.submit(payload)

    @app.get("/api/jobs/{job_id}", response_model=GraphJob)
    def get_job(
        job_id: str,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> GraphJob:
        require_operator(authorization, tailscale_login, action="Job status access")
        try:
            return resolved_store.get_job(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc

    @app.get("/api/graphs", response_model=GraphList)
    def list_graphs(
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> GraphList:
        return GraphList(
            graphs=resolved_store.list_graphs(
                include_restricted=operator_status(authorization, tailscale_login)
            )
        )

    @app.get("/api/graphs/{graph_id}")
    def get_graph(
        graph_id: str,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> JSONResponse:
        try:
            if resolved_store.graph_is_restricted(graph_id):
                require_operator(
                    authorization,
                    tailscale_login,
                    action="Private graph access",
                )
            graph = resolved_store.get_graph(graph_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Graph not found") from exc
        return JSONResponse(graph.model_dump(mode="json", by_alias=True))

    @app.get("/api/graphs/{graph_id}/export.json")
    def export_graph(
        graph_id: str,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> Response:
        try:
            if resolved_store.graph_is_restricted(graph_id):
                require_operator(
                    authorization,
                    tailscale_login,
                    action="Private graph export",
                )
            graph = resolved_store.get_graph(graph_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Graph not found") from exc
        return Response(
            graph.model_dump_json(by_alias=True, indent=2) + "\n",
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="crest-{graph_id}.json"'
            },
        )

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(WEB_ROOT / "index.html")

    @app.get("/styles.css")
    def styles() -> FileResponse:
        return FileResponse(WEB_ROOT / "styles.css", media_type="text/css")

    @app.get("/app.js")
    def javascript() -> FileResponse:
        return FileResponse(WEB_ROOT / "app.js", media_type="text/javascript")

    return app


app = create_app()
