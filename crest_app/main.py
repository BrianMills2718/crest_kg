"""FastAPI entry point for the CREST research workbench."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from .models import (
    Capabilities,
    ConnectorStatus,
    DocumentDetail,
    GraphBuildRequest,
    GraphJob,
    GraphList,
    SearchRequest,
    SearchResponse,
)
from .services import CorpusCatalog, GraphJobRunner, WorkbenchStore, request_is_operator


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
    resolved_catalog = catalog or CorpusCatalog()
    resolved_store = store or WorkbenchStore(
        data_dir
        or Path(os.getenv("CREST_DATA_DIR", "/tmp/crest-workbench-data"))
    )
    runner = GraphJobRunner(resolved_store, resolved_catalog.corpus_path)
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
                    id="cia-reading-room-live",
                    label="CIA Reading Room live",
                    state="unavailable",
                    detail=(
                        "The CIA search and document routes currently redirect automated "
                        "requests back to the Reading Room landing page."
                    ),
                ),
            ],
            graph_build_enabled=os.getenv("CREST_BUILD_ENABLED", "0") == "1",
            graph_build_authorized=operator_status(authorization, tailscale_login),
            max_documents_per_build=3,
            max_build_budget_usd=float(
                os.getenv("CREST_MAX_BUILD_BUDGET_USD", "0.25")
            ),
        )

    @app.post("/api/search", response_model=SearchResponse)
    def search(payload: SearchRequest) -> SearchResponse:
        return resolved_catalog.search(payload.query, limit=payload.limit)

    @app.get("/api/documents/{document_id}", response_model=DocumentDetail)
    def document(document_id: str) -> DocumentDetail:
        try:
            return resolved_catalog.detail(document_id)
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
            if document_id not in resolved_catalog.by_id
        ]
        if unknown_ids:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown document IDs: {', '.join(unknown_ids)}",
            )
        return app.state.runner.submit(payload)

    @app.get("/api/jobs/{job_id}", response_model=GraphJob)
    def get_job(job_id: str) -> GraphJob:
        try:
            return resolved_store.get_job(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc

    @app.get("/api/graphs", response_model=GraphList)
    def list_graphs() -> GraphList:
        return GraphList(graphs=resolved_store.list_graphs())

    @app.get("/api/graphs/{graph_id}")
    def get_graph(graph_id: str) -> JSONResponse:
        try:
            graph = resolved_store.get_graph(graph_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Graph not found") from exc
        return JSONResponse(graph.model_dump(mode="json", by_alias=True))

    @app.get("/api/graphs/{graph_id}/export.json")
    def export_graph(graph_id: str) -> Response:
        try:
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
