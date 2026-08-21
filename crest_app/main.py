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
    BatchUploadFailure,
    BatchUploadReceipt,
    Capabilities,
    CollectionCreate,
    CollectionDocumentsRequest,
    CollectionList,
    CollectionUpdate,
    ConnectorProbe,
    ConnectorStatus,
    DocumentDetail,
    EvidencePreview,
    EvidenceInquiry,
    EvidenceInquiryList,
    EvidenceInquiryRequest,
    EvidenceQueryRequest,
    GraphBuildRequest,
    GraphJob,
    GraphJobList,
    GraphList,
    ResearchCollection,
    SearchRequest,
    SearchResponse,
    UploadedDocumentList,
    UploadedDocumentReceipt,
)
from .services import (
    ConnectorUnavailable,
    CorpusCatalog,
    EvidenceInquiryRunner,
    GraphJobRunner,
    ProviderExecutionLane,
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
        version="0.2.0",
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
    provider_lane = ProviderExecutionLane()
    runner = GraphJobRunner(resolved_store, resolved_catalog, provider_lane)
    inquiry_runner = EvidenceInquiryRunner(resolved_store, provider_lane)
    app.state.catalog = resolved_catalog
    app.state.store = resolved_store
    app.state.runner = runner
    app.state.inquiry_runner = inquiry_runner
    app.state.provider_lane = provider_lane

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

    def max_batch_files() -> int:
        return int(os.getenv("CREST_MAX_BATCH_FILES", "10"))

    def require_collection(collection_id: str) -> ResearchCollection:
        try:
            return resolved_store.get_collection(collection_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Collection not found") from exc

    def require_inquiry(inquiry_id: str) -> EvidenceInquiry:
        try:
            return resolved_store.get_inquiry(inquiry_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Inquiry not found") from exc

    async def ingest_upload(
        file: UploadFile, *, title: str | None = None
    ) -> UploadedDocumentReceipt:
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
            evidence_brief_enabled=os.getenv("CREST_BRIEF_ENABLED", "0") == "1",
            evidence_brief_authorized=is_operator,
            max_evidence_budget_usd=float(
                os.getenv("CREST_MAX_BRIEF_BUDGET_USD", "0.15")
            ),
            document_upload_enabled=uploads_enabled,
            document_upload_authorized=is_operator,
            max_upload_bytes=max_upload_bytes(),
            max_batch_files=max_batch_files(),
        )

    @app.post("/api/search", response_model=SearchResponse)
    def search(
        payload: SearchRequest,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> SearchResponse:
        is_operator = operator_status(authorization, tailscale_login)
        collection = None
        if payload.collection_id:
            require_operator(
                authorization,
                tailscale_login,
                action="Collection search",
            )
            collection = require_collection(payload.collection_id)
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
                document_ids=(set(collection.document_ids) if collection else None),
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

    @app.post("/api/evidence/preview", response_model=EvidencePreview)
    def preview_evidence(
        payload: EvidenceQueryRequest,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> EvidencePreview:
        require_operator(
            authorization,
            tailscale_login,
            action="Collection evidence retrieval",
        )
        collection = require_collection(payload.collection_id)
        return EvidencePreview(
            collection_id=collection.id,
            question=payload.question,
            evidence=resolved_catalog.rank_collection_evidence(
                payload.question,
                document_ids=collection.document_ids,
                limit=payload.evidence_limit,
                max_chars_per_document=payload.max_chars_per_document,
            ),
        )

    @app.post("/api/inquiries", response_model=EvidenceInquiry, status_code=202)
    def create_inquiry(
        payload: EvidenceInquiryRequest,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> EvidenceInquiry:
        if os.getenv("CREST_BRIEF_ENABLED", "0") != "1":
            raise HTTPException(status_code=503, detail="Evidence briefs are disabled")
        require_operator(
            authorization,
            tailscale_login,
            action="Evidence brief generation",
        )
        budget_ceiling = float(os.getenv("CREST_MAX_BRIEF_BUDGET_USD", "0.15"))
        if payload.max_budget_usd > budget_ceiling:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Requested evidence budget exceeds the "
                    f"${budget_ceiling:.2f} server ceiling"
                ),
            )
        collection = require_collection(payload.collection_id)
        evidence = resolved_catalog.rank_collection_evidence(
            payload.question,
            document_ids=collection.document_ids,
            limit=payload.evidence_limit,
            max_chars_per_document=payload.max_chars_per_document,
        )
        return app.state.inquiry_runner.submit(
            payload,
            collection=collection,
            evidence=evidence,
        )

    @app.get("/api/inquiries", response_model=EvidenceInquiryList)
    def list_inquiries(
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> EvidenceInquiryList:
        require_operator(
            authorization,
            tailscale_login,
            action="Inquiry history access",
        )
        return EvidenceInquiryList(inquiries=resolved_store.list_inquiries())

    @app.get("/api/inquiries/{inquiry_id}", response_model=EvidenceInquiry)
    def get_inquiry(
        inquiry_id: str,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> EvidenceInquiry:
        require_operator(
            authorization,
            tailscale_login,
            action="Inquiry access",
        )
        return require_inquiry(inquiry_id)

    @app.post(
        "/api/collections",
        response_model=ResearchCollection,
        status_code=201,
    )
    def create_collection(
        payload: CollectionCreate,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> ResearchCollection:
        require_operator(authorization, tailscale_login, action="Collection creation")
        return resolved_store.create_collection(payload)

    @app.get("/api/collections", response_model=CollectionList)
    def list_collections(
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> CollectionList:
        require_operator(authorization, tailscale_login, action="Collection listing")
        return CollectionList(collections=resolved_store.list_collections())

    @app.get("/api/collections/{collection_id}", response_model=ResearchCollection)
    def get_collection(
        collection_id: str,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> ResearchCollection:
        require_operator(authorization, tailscale_login, action="Collection access")
        return require_collection(collection_id)

    @app.patch("/api/collections/{collection_id}", response_model=ResearchCollection)
    def update_collection(
        collection_id: str,
        payload: CollectionUpdate,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> ResearchCollection:
        require_operator(authorization, tailscale_login, action="Collection update")
        require_collection(collection_id)
        return resolved_store.update_collection(collection_id, payload)

    @app.put(
        "/api/collections/{collection_id}/documents",
        response_model=ResearchCollection,
    )
    def replace_collection_documents(
        collection_id: str,
        payload: CollectionDocumentsRequest,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> ResearchCollection:
        require_operator(authorization, tailscale_login, action="Collection membership update")
        require_collection(collection_id)
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
        live_ids = [
            document_id
            for document_id in payload.document_ids
            if resolved_catalog.connector_for(document_id) == "cia-reading-room-live"
        ]
        if live_ids:
            raise HTTPException(
                status_code=422,
                detail="Live connector results are not durable collection members; upload a retained source instead",
            )
        return resolved_store.replace_collection_documents(
            collection_id, payload.document_ids
        )

    @app.delete("/api/collections/{collection_id}", response_model=ResearchCollection)
    def delete_collection(
        collection_id: str,
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> ResearchCollection:
        require_operator(authorization, tailscale_login, action="Collection deletion")
        require_collection(collection_id)
        return resolved_store.delete_collection(collection_id)

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
        return await ingest_upload(file, title=title)

    @app.post("/api/uploads/batch", response_model=BatchUploadReceipt)
    async def upload_document_batch(
        files: list[UploadFile] = File(...),
        collection_id: str | None = Form(default=None),
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> BatchUploadReceipt:
        if not upload_enabled():
            raise HTTPException(status_code=503, detail="Document upload is disabled")
        require_operator(authorization, tailscale_login, action="Batch document upload")
        if not files:
            raise HTTPException(status_code=422, detail="Choose at least one source file")
        if len(files) > max_batch_files():
            raise HTTPException(
                status_code=413,
                detail=f"Batch exceeds the {max_batch_files()}-file server limit",
            )
        if collection_id:
            require_collection(collection_id)
        successes: list[UploadedDocumentReceipt] = []
        failures: list[BatchUploadFailure] = []
        for file in files:
            filename = file.filename or "upload"
            try:
                successes.append(await ingest_upload(file))
            except HTTPException as exc:
                failures.append(
                    BatchUploadFailure(
                        filename=filename,
                        status_code=exc.status_code,
                        detail=str(exc.detail),
                    )
                )
        if collection_id and successes:
            resolved_store.add_collection_documents(
                collection_id,
                [item.document_id for item in successes],
            )
        return BatchUploadReceipt(
            collection_id=collection_id,
            successes=successes,
            failures=failures,
        )

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
        if payload.inquiry_id:
            inquiry = require_inquiry(payload.inquiry_id)
            if inquiry.state != "completed" or inquiry.brief is None:
                raise HTTPException(
                    status_code=422,
                    detail="Focused graph handoff requires a completed evidence inquiry",
                )
            if payload.collection_id != inquiry.request.collection_id:
                raise HTTPException(
                    status_code=422,
                    detail="Focused graph handoff must use the inquiry collection",
                )
            cited_ids = set(inquiry.brief.synthesis_citation_ids)
            cited_ids.update(
                citation_id
                for finding in inquiry.brief.findings
                for citation_id in finding.citation_ids
            )
            cited_documents = {
                item.document_id for item in inquiry.evidence if item.id in cited_ids
            }
            uncited_documents = [
                document_id
                for document_id in payload.document_ids
                if document_id not in cited_documents
            ]
            if uncited_documents:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Documents are not cited by the selected inquiry: "
                        + ", ".join(uncited_documents)
                    ),
                )
        if payload.collection_id:
            collection = require_collection(payload.collection_id)
            outside_collection = [
                document_id
                for document_id in payload.document_ids
                if document_id not in collection.document_ids
            ]
            if outside_collection:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Documents are outside the selected collection: "
                        + ", ".join(outside_collection)
                    ),
                )
        return app.state.runner.submit(payload)

    @app.get("/api/jobs", response_model=GraphJobList)
    def list_jobs(
        authorization: str | None = Header(default=None),
        tailscale_login: str | None = Header(default=None, alias="Tailscale-User-Login"),
    ) -> GraphJobList:
        require_operator(authorization, tailscale_login, action="Job history access")
        return GraphJobList(jobs=resolved_store.list_jobs())

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
