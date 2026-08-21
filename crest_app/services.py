"""Search, persistence, authorization, and graph-build services."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from crest_pipeline import (
    GraphArtifact,
    RawDocument,
    derive_document_id,
    load_document_records,
    run_extraction,
)

from .acquisition import ExtractedUpload
from .briefing import generate_evidence_brief
from .connectors import SourceConnector
from .models import (
    CollectionCreate,
    CollectionUpdate,
    ConnectorProbe,
    ConnectorStatus,
    DocumentDetail,
    DocumentSummary,
    EvidenceBrief,
    EvidenceChunk,
    EvidenceInquiry,
    EvidenceInquiryRequest,
    GraphAccessRecord,
    GraphBuildRequest,
    GraphJob,
    GraphSummary,
    ResearchCollection,
    SearchResponse,
    UploadedDocumentReceipt,
    UploadedDocumentRecord,
)
from .retrieval import RetrievalDocument, rank_evidence


ROOT = Path(__file__).parents[1]
DEFAULT_CORPUS = ROOT / "cia_documents" / "disinformation_complete_20250517_002848.json"
DEFAULT_EXAMPLE_GRAPH = (
    ROOT / "cia_kg_output" / "validated_5_documents_relationship_binding_v2.json"
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temporary = handle.name
        os.replace(temporary, path)
    finally:
        if temporary and Path(temporary).exists():
            Path(temporary).unlink()


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = handle.name
        os.replace(temporary, path)
    finally:
        if temporary and Path(temporary).exists():
            Path(temporary).unlink()


class ConnectorUnavailable(RuntimeError):
    """A source connector cannot complete its public acquisition contract."""


class CiaReadingRoomConnector:
    """Best-effort adapter for the CIA's current official search surface."""

    search_endpoint = "https://www.cia.gov/search/results"

    def __init__(self, *, timeout_seconds: float = 8.0) -> None:
        self.timeout_seconds = timeout_seconds
        self._result_urls: dict[str, str] = {}
        self._documents: dict[str, RawDocument] = {}
        self.last_status = ConnectorStatus(
            id="cia-reading-room-live",
            label="CIA Reading Room live",
            state="unavailable",
            detail=(
                "Official search currently returns access denied and direct Reading Room "
                "document routes redirect to the landing page."
            ),
        )

    @staticmethod
    def _plain_html(value: str) -> str:
        from html import unescape

        return " ".join(unescape(re.sub(r"<[^>]+>", " ", value)).split())

    def _get(self, url: str) -> tuple[int, bytes, str]:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
                "Referer": "https://www.cia.gov/search/",
                "User-Agent": (
                    "CREST-Research-Workbench/0.2 "
                    "(+https://github.com/BrianMills2718/crest_kg)"
                ),
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return response.status, response.read(), response.geturl()
        except urllib.error.HTTPError as exc:
            raise ConnectorUnavailable(
                f"CIA official endpoint returned HTTP {exc.code}."
            ) from exc
        except urllib.error.URLError as exc:
            raise ConnectorUnavailable(f"CIA official endpoint failed: {exc.reason}") from exc

    def search(self, query: str, *, limit: int) -> SearchResponse:
        parameters = urllib.parse.urlencode(
            {
                "query": query,
                "sitelimit": "www.cia.gov/readingroom",
                "limit": min(limit, 50),
            }
        )
        status, body, _ = self._get(f"{self.search_endpoint}?{parameters}")
        try:
            payload = json.loads(body)
            web = payload["web"]
            raw_results = web["results"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ConnectorUnavailable(
                "CIA official search returned an unsupported response."
            ) from exc

        results: list[DocumentSummary] = []
        for rank, item in enumerate(raw_results[:limit]):
            url = str(item.get("url") or "").strip()
            if "/readingroom/document/" not in url:
                continue
            document_id = url.rstrip("/").rsplit("/", 1)[-1]
            title = self._plain_html(str(item.get("title") or document_id))
            snippet = self._plain_html(str(item.get("snippet") or ""))
            self._result_urls[document_id] = url
            results.append(
                DocumentSummary(
                    document_id=document_id,
                    connector_id="cia-reading-room-live",
                    title=title,
                    source_url=url,
                    document_type="CIA Reading Room",
                    collection=None,
                    publication_date=None,
                    page_count=None,
                    snippet=snippet,
                    score=float(limit - rank),
                )
            )
        self.last_status = ConnectorStatus(
            id="cia-reading-room-live",
            label="CIA Reading Room live",
            state="available",
            detail="Official CIA search and document acquisition are responding.",
        )
        return SearchResponse(
            query=query,
            connector_id="cia-reading-room-live",
            total_matches=int(web.get("total") or len(results)),
            results=results,
        )

    def _fetch_document(self, document_id: str) -> RawDocument:
        if document_id in self._documents:
            return self._documents[document_id]
        url = self._result_urls.get(document_id)
        if not url:
            raise KeyError(document_id)
        _, body, final_url = self._get(url)
        if final_url.rstrip("/") == "https://www.cia.gov/readingroom":
            raise ConnectorUnavailable(
                "CIA document acquisition redirected to the Reading Room landing page."
            )
        try:
            from bs4 import BeautifulSoup
        except ImportError as exc:  # pragma: no cover - packaging guard
            raise ConnectorUnavailable("The CIA HTML parser is unavailable.") from exc
        soup = BeautifulSoup(body, "html.parser")
        heading = soup.select_one("h1.documentFirstHeading") or soup.find("h1")
        body_node = soup.select_one(".field-name-body .field-item")
        text = body_node.get_text("\n", strip=True) if body_node else ""
        if not text.strip():
            raise ConnectorUnavailable(
                "CIA document page did not expose readable source text."
            )
        metadata: dict[str, str] = {
            "Document Number": document_id,
            "Connector": "cia-reading-room-live",
        }
        for field in soup.select(".field-label-inline"):
            label = field.select_one(".field-label")
            value = field.select_one(".field-item")
            if label and value:
                metadata[label.get_text(" ", strip=True).rstrip(":")] = value.get_text(
                    " ", strip=True
                )
        document = RawDocument(
            url=url,
            title=heading.get_text(" ", strip=True) if heading else document_id,
            metadata=metadata,
            body_text=text,
        )
        self._documents[document_id] = document
        return document

    def detail(self, document_id: str) -> DocumentDetail:
        document = self._fetch_document(document_id)
        return _document_detail(document_id, document, "cia-reading-room-live")

    def raw_document(self, document_id: str) -> RawDocument:
        return self._fetch_document(document_id)

    def contains(self, document_id: str) -> bool:
        return document_id in self._result_urls or document_id in self._documents

    def probe(self) -> ConnectorProbe:
        checked_at = utc_now()
        search_status: int | None = None
        document_status: int | None = None
        try:
            response = self.search("disinformation", limit=1)
            search_status = 200
            if not response.results:
                raise ConnectorUnavailable("CIA official search returned no Reading Room result.")
            self._fetch_document(response.results[0].document_id)
            document_status = 200
        except ConnectorUnavailable as exc:
            match = re.search(r"HTTP (\d{3})", str(exc))
            if match and search_status is None:
                search_status = int(match.group(1))
            self.last_status = ConnectorStatus(
                id="cia-reading-room-live",
                label="CIA Reading Room live",
                state="unavailable",
                detail=str(exc),
            )
        return ConnectorProbe(
            connector=self.last_status,
            checked_at=checked_at,
            search_endpoint=self.search_endpoint,
            search_http_status=search_status,
            document_http_status=document_status,
        )


def _document_detail(
    document_id: str, document: RawDocument, connector_id: str
) -> DocumentDetail:
    return DocumentDetail(
        document_id=document_id,
        connector_id=connector_id,
        title=document.title,
        source_url=document.url,
        metadata=document.metadata,
        body_preview=document.body_text[:8_000],
        body_chars=len(document.body_text),
        body_sha256=hashlib.sha256(document.body_text.encode("utf-8")).hexdigest(),
    )


class CorpusCatalog:
    """Unified searchable view of bundled, uploaded, and live source records."""

    def __init__(
        self,
        corpus_path: Path = DEFAULT_CORPUS,
        *,
        store: WorkbenchStore | None = None,
        cia_connector: SourceConnector | None = None,
    ) -> None:
        self.corpus_path = corpus_path
        self.store = store
        self.cia_connector = cia_connector or CiaReadingRoomConnector()
        payload = json.loads(corpus_path.read_text(encoding="utf-8"))
        raw_items = payload["documents"] if isinstance(payload, dict) else payload
        self.documents = [RawDocument.model_validate(item) for item in raw_items]
        self._bundled_by_id: dict[str, RawDocument] = {}
        for document in self.documents:
            document_id = derive_document_id(document)
            if document_id in self._bundled_by_id:
                raise ValueError(f"duplicate source document ID: {document_id}")
            self._bundled_by_id[document_id] = document

    @property
    def count(self) -> int:
        return len(self.documents)

    @property
    def upload_count(self) -> int:
        return len(self.store.list_uploaded_documents()) if self.store else 0

    @property
    def by_id(self) -> dict[str, RawDocument]:
        documents = dict(self._bundled_by_id)
        if self.store:
            documents.update(
                {
                    record.document_id: self._uploaded_raw_document(record)
                    for record in self.store.list_uploaded_documents()
                }
            )
        return documents

    @staticmethod
    def _uploaded_raw_document(record: UploadedDocumentRecord) -> RawDocument:
        return RawDocument(
            title=record.title,
            metadata={
                "Document Number": record.document_id,
                "Connector": "user-uploads",
                "Original Filename": record.original_filename,
                "Media Type": record.media_type,
                "Extraction Method": record.extraction_method,
                "Document Page Count": str(record.page_count),
                "Uploaded At": record.uploaded_at.isoformat(),
            },
            body_text=record.body_text,
        )

    def connector_for(self, document_id: str) -> str:
        if document_id in self._bundled_by_id:
            return "bundled-crest"
        if self.store:
            try:
                self.store.get_uploaded_document(document_id)
                return "user-uploads"
            except KeyError:
                pass
        if self.cia_connector.contains(document_id):
            return "cia-reading-room-live"
        raise KeyError(document_id)

    def contains(self, document_id: str) -> bool:
        try:
            self.connector_for(document_id)
            return True
        except KeyError:
            return False

    def search(
        self,
        query: str,
        *,
        limit: int,
        connector_id: str = "all",
        include_uploads: bool = False,
        document_ids: set[str] | None = None,
    ) -> SearchResponse:
        if connector_id == "cia-reading-room-live" and document_ids is None:
            return self.cia_connector.search(query, limit=limit)
        documents: dict[str, tuple[RawDocument, str]] = {}
        if connector_id in {"all", "bundled-crest"}:
            documents.update(
                {
                    document_id: (document, "bundled-crest")
                    for document_id, document in self._bundled_by_id.items()
                }
            )
        if include_uploads and connector_id in {"all", "user-uploads"} and self.store:
            documents.update(
                {
                    record.document_id: (
                        self._uploaded_raw_document(record),
                        "user-uploads",
                    )
                    for record in self.store.list_uploaded_documents()
                }
            )
        if document_ids is not None:
            documents = {
                document_id: value
                for document_id, value in documents.items()
                if document_id in document_ids
            }
        normalized_query = " ".join(query.casefold().split())
        terms = tuple(dict.fromkeys(re.findall(r"[a-z0-9]+", normalized_query)))
        scored: list[tuple[float, str, RawDocument, str, str]] = []
        for document_id, (document, source_connector) in documents.items():
            title = document.title.casefold()
            metadata = " ".join(document.metadata.values()).casefold()
            body = document.body_text.casefold()
            score = 0.0
            if normalized_query in title:
                score += 30
            if normalized_query in metadata:
                score += 12
            if normalized_query in body:
                score += 8
            for term in terms:
                score += title.count(term) * 8
                score += metadata.count(term) * 3
                score += min(body.count(term), 20)
            if score <= 0:
                continue
            first_positions = [body.find(term) for term in terms if body.find(term) >= 0]
            match_at = min(first_positions) if first_positions else 0
            start = max(0, match_at - 130)
            end = min(len(document.body_text), match_at + 330)
            snippet = " ".join(document.body_text[start:end].split())
            if start:
                snippet = f"…{snippet}"
            if end < len(document.body_text):
                snippet = f"{snippet}…"
            scored.append((score, document_id, document, snippet, source_connector))
        scored.sort(key=lambda item: (-item[0], item[1]))
        results = [
            DocumentSummary(
                document_id=document_id,
                connector_id=source_connector,
                title=document.title,
                source_url=document.url,
                document_type=document.metadata.get("Document Type"),
                collection=document.metadata.get("Collection"),
                publication_date=document.metadata.get("Publication Date"),
                page_count=document.metadata.get("Document Page Count"),
                snippet=snippet,
                score=score,
            )
            for score, document_id, document, snippet, source_connector in scored[:limit]
        ]
        return SearchResponse(
            query=query,
            connector_id=connector_id,
            total_matches=len(scored),
            results=results,
        )

    def detail(self, document_id: str) -> DocumentDetail:
        connector_id = self.connector_for(document_id)
        if connector_id == "cia-reading-room-live":
            return self.cia_connector.detail(document_id)
        document = self.by_id[document_id]
        return _document_detail(document_id, document, connector_id)

    def load_selected(self, document_ids: list[str], *, max_chars: int):
        documents: list[RawDocument] = []
        for document_id in document_ids:
            connector_id = self.connector_for(document_id)
            if connector_id == "cia-reading-room-live":
                documents.append(self.cia_connector.raw_document(document_id))
            else:
                documents.append(self.by_id[document_id])
        return load_document_records(
            documents,
            document_ids=document_ids,
            max_chars=max_chars,
            corpus_label="crest-workbench-catalog",
        )

    def rank_collection_evidence(
        self,
        question: str,
        *,
        document_ids: list[str],
        limit: int,
        max_chars_per_document: int,
    ):
        """Rank exact chunks from the durable members of one collection."""

        documents: list[RetrievalDocument] = []
        for document_id in document_ids:
            connector_id = self.connector_for(document_id)
            if connector_id == "cia-reading-room-live":
                raw = self.cia_connector.raw_document(document_id)
            else:
                raw = self.by_id[document_id]
            documents.append(
                RetrievalDocument(
                    document_id=document_id,
                    connector_id=connector_id,
                    title=raw.title,
                    body_text=raw.body_text,
                )
            )
        return rank_evidence(
            question,
            documents,
            limit=limit,
            max_chars_per_document=max_chars_per_document,
        )


class WorkbenchStore:
    """Atomic JSON persistence for collections, sources, jobs, and graph artifacts."""

    example_id = "example-fixed-v2"

    def __init__(self, data_dir: Path, example_graph: Path = DEFAULT_EXAMPLE_GRAPH) -> None:
        self.data_dir = data_dir
        self.jobs_dir = data_dir / "jobs"
        self.graphs_dir = data_dir / "graphs"
        self.graph_access_dir = data_dir / "graph-access"
        self.collections_dir = data_dir / "collections"
        self.inquiries_dir = data_dir / "inquiries"
        self.upload_records_dir = data_dir / "uploads" / "records"
        self.upload_files_dir = data_dir / "uploads" / "files"
        self.example_graph_path = example_graph
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.graphs_dir.mkdir(parents=True, exist_ok=True)
        self.graph_access_dir.mkdir(parents=True, exist_ok=True)
        self.collections_dir.mkdir(parents=True, exist_ok=True)
        self.inquiries_dir.mkdir(parents=True, exist_ok=True)
        self.upload_records_dir.mkdir(parents=True, exist_ok=True)
        self.upload_files_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize_graph_access()
        self._mark_interrupted_jobs_failed()
        self._mark_interrupted_inquiries_failed()

    def _initialize_graph_access(self) -> None:
        """Explicitly classify pre-feature graphs once, then fail closed forever."""

        marker = self.graph_access_dir / ".migration-v1-complete"
        if marker.is_file():
            return
        for path in self.graphs_dir.glob("*.json"):
            access_path = self.graph_access_dir / path.name
            if access_path.is_file():
                continue
            access = GraphAccessRecord(
                graph_id=path.stem,
                restricted=False,
                connector_ids=["bundled-crest"],
                recorded_at=utc_now(),
            )
            _atomic_json(access_path, access.model_dump(mode="json"))
        _atomic_bytes(marker, b"graph-access-v1\n")

    def _mark_interrupted_jobs_failed(self) -> None:
        for path in self.jobs_dir.glob("*.json"):
            job = GraphJob.model_validate_json(path.read_text(encoding="utf-8"))
            if job.state in {"queued", "running"}:
                job.state = "failed"
                job.error = "Service restarted before this build completed."
                job.progress_detail = "Build interrupted by service restart"
                job.updated_at = utc_now()
                self.save_job(job)

    def _mark_interrupted_inquiries_failed(self) -> None:
        for path in self.inquiries_dir.glob("*.json"):
            inquiry = EvidenceInquiry.model_validate_json(
                path.read_text(encoding="utf-8")
            )
            if inquiry.state in {"queued", "running"}:
                inquiry.state = "failed"
                inquiry.error = "Service restarted before this evidence brief completed."
                inquiry.progress_detail = "Evidence brief interrupted by service restart"
                inquiry.updated_at = utc_now()
                self.save_inquiry(inquiry)

    def save_job(self, job: GraphJob) -> None:
        with self._lock:
            _atomic_json(
                self.jobs_dir / f"{job.id}.json",
                job.model_dump(mode="json"),
            )

    def get_job(self, job_id: str) -> GraphJob:
        path = self.jobs_dir / f"{job_id}.json"
        if not path.is_file():
            raise KeyError(job_id)
        return GraphJob.model_validate_json(path.read_text(encoding="utf-8"))

    def list_jobs(self) -> list[GraphJob]:
        jobs = [
            GraphJob.model_validate_json(path.read_text(encoding="utf-8"))
            for path in self.jobs_dir.glob("*.json")
        ]
        return sorted(jobs, key=lambda item: item.updated_at, reverse=True)

    def save_inquiry(self, inquiry: EvidenceInquiry) -> None:
        with self._lock:
            _atomic_json(
                self.inquiries_dir / f"{inquiry.id}.json",
                inquiry.model_dump(mode="json"),
            )

    def get_inquiry(self, inquiry_id: str) -> EvidenceInquiry:
        if not re.fullmatch(r"inquiry-[0-9a-f]{32}", inquiry_id):
            raise KeyError(inquiry_id)
        path = self.inquiries_dir / f"{inquiry_id}.json"
        if not path.is_file():
            raise KeyError(inquiry_id)
        return EvidenceInquiry.model_validate_json(path.read_text(encoding="utf-8"))

    def list_inquiries(self) -> list[EvidenceInquiry]:
        inquiries = [
            EvidenceInquiry.model_validate_json(path.read_text(encoding="utf-8"))
            for path in self.inquiries_dir.glob("*.json")
        ]
        return sorted(inquiries, key=lambda item: item.updated_at, reverse=True)

    def create_collection(self, payload: CollectionCreate) -> ResearchCollection:
        now = utc_now()
        collection = ResearchCollection(
            id=f"collection-{secrets.token_hex(8)}",
            title=payload.title,
            description=payload.description,
            document_ids=[],
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            _atomic_json(
                self.collections_dir / f"{collection.id}.json",
                collection.model_dump(mode="json"),
            )
        return collection

    def get_collection(self, collection_id: str) -> ResearchCollection:
        if not re.fullmatch(r"collection-[0-9a-f]{16}", collection_id):
            raise KeyError(collection_id)
        path = self.collections_dir / f"{collection_id}.json"
        if not path.is_file():
            raise KeyError(collection_id)
        return ResearchCollection.model_validate_json(path.read_text(encoding="utf-8"))

    def list_collections(self) -> list[ResearchCollection]:
        collections = [
            ResearchCollection.model_validate_json(path.read_text(encoding="utf-8"))
            for path in self.collections_dir.glob("*.json")
        ]
        return sorted(collections, key=lambda item: item.updated_at, reverse=True)

    def _save_collection(self, collection: ResearchCollection) -> ResearchCollection:
        with self._lock:
            _atomic_json(
                self.collections_dir / f"{collection.id}.json",
                collection.model_dump(mode="json"),
            )
        return collection

    def update_collection(
        self, collection_id: str, payload: CollectionUpdate
    ) -> ResearchCollection:
        collection = self.get_collection(collection_id)
        changes = payload.model_dump(exclude_none=True)
        if not changes:
            return collection
        return self._save_collection(
            collection.model_copy(update={**changes, "updated_at": utc_now()})
        )

    def replace_collection_documents(
        self, collection_id: str, document_ids: list[str]
    ) -> ResearchCollection:
        collection = self.get_collection(collection_id)
        if collection.document_ids == document_ids:
            return collection
        return self._save_collection(
            collection.model_copy(
                update={"document_ids": document_ids, "updated_at": utc_now()}
            )
        )

    def add_collection_documents(
        self, collection_id: str, document_ids: list[str]
    ) -> ResearchCollection:
        collection = self.get_collection(collection_id)
        combined = list(dict.fromkeys([*collection.document_ids, *document_ids]))
        return self.replace_collection_documents(collection_id, combined)

    def delete_collection(self, collection_id: str) -> ResearchCollection:
        with self._lock:
            collection = self.get_collection(collection_id)
            (self.collections_dir / f"{collection_id}.json").unlink()
        return collection

    def remove_document_from_collections(self, document_id: str) -> None:
        with self._lock:
            for collection in self.list_collections():
                if document_id not in collection.document_ids:
                    continue
                self.replace_collection_documents(
                    collection.id,
                    [item for item in collection.document_ids if item != document_id],
                )

    @staticmethod
    def _upload_receipt(
        record: UploadedDocumentRecord, *, duplicate: bool = False
    ) -> UploadedDocumentReceipt:
        return UploadedDocumentReceipt(
            document_id=record.document_id,
            title=record.title,
            original_filename=record.original_filename,
            media_type=record.media_type,
            source_sha256=record.source_sha256,
            body_sha256=record.body_sha256,
            body_chars=len(record.body_text),
            extraction_method=record.extraction_method,
            page_count=record.page_count,
            uploaded_at=record.uploaded_at,
            duplicate=duplicate,
        )

    def save_uploaded_document(
        self, record: UploadedDocumentRecord, source_bytes: bytes
    ) -> UploadedDocumentReceipt:
        record_path = self.upload_records_dir / f"{record.document_id}.json"
        source_path = self.upload_files_dir / f"{record.document_id}.source"
        with self._lock:
            if record_path.is_file():
                existing = self.get_uploaded_document(record.document_id)
                if existing.source_sha256 != record.source_sha256:
                    raise ValueError(
                        f"upload ID collision for {record.document_id}; source was not changed"
                    )
                return self._upload_receipt(existing, duplicate=True)
            _atomic_bytes(source_path, source_bytes)
            _atomic_json(record_path, record.model_dump(mode="json"))
        return self._upload_receipt(record)

    def get_uploaded_document(self, document_id: str) -> UploadedDocumentRecord:
        if not re.fullmatch(r"upload-[0-9a-f]{20}", document_id):
            raise KeyError(document_id)
        path = self.upload_records_dir / f"{document_id}.json"
        if not path.is_file():
            raise KeyError(document_id)
        return UploadedDocumentRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def list_uploaded_documents(self) -> list[UploadedDocumentRecord]:
        records = [
            UploadedDocumentRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in self.upload_records_dir.glob("*.json")
        ]
        return sorted(records, key=lambda item: item.uploaded_at, reverse=True)

    def uploaded_source_path(self, document_id: str) -> Path:
        self.get_uploaded_document(document_id)
        path = self.upload_files_dir / f"{document_id}.source"
        if not path.is_file():
            raise RuntimeError(f"uploaded source bytes are missing for {document_id}")
        return path

    def delete_uploaded_document(self, document_id: str) -> UploadedDocumentRecord:
        with self._lock:
            record = self.get_uploaded_document(document_id)
            self.remove_document_from_collections(document_id)
            record_path = self.upload_records_dir / f"{document_id}.json"
            source_path = self.upload_files_dir / f"{document_id}.source"
            record_path.unlink()
            if source_path.exists():
                source_path.unlink()
            return record

    def save_graph(
        self,
        graph_id: str,
        graph: GraphArtifact,
        *,
        connector_ids: list[str],
    ) -> None:
        with self._lock:
            access = GraphAccessRecord(
                graph_id=graph_id,
                restricted=any(item != "bundled-crest" for item in connector_ids),
                connector_ids=sorted(set(connector_ids)),
                recorded_at=utc_now(),
            )
            _atomic_json(
                self.graph_access_dir / f"{graph_id}.json",
                access.model_dump(mode="json"),
            )
            _atomic_json(
                self.graphs_dir / f"{graph_id}.json",
                graph.model_dump(mode="json", by_alias=True),
            )

    def get_graph(self, graph_id: str) -> GraphArtifact:
        path = (
            self.example_graph_path
            if graph_id == self.example_id
            else self.graphs_dir / f"{graph_id}.json"
        )
        if not path.is_file():
            raise KeyError(graph_id)
        return GraphArtifact.model_validate_json(path.read_text(encoding="utf-8"))

    def graph_access(self, graph_id: str) -> GraphAccessRecord:
        if graph_id == self.example_id:
            return GraphAccessRecord(
                graph_id=graph_id,
                restricted=False,
                connector_ids=["bundled-crest"],
                recorded_at=utc_now(),
            )
        path = self.graph_access_dir / f"{graph_id}.json"
        if not path.is_file():
            return GraphAccessRecord(
                graph_id=graph_id,
                restricted=True,
                connector_ids=["unknown"],
                recorded_at=utc_now(),
            )
        return GraphAccessRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def graph_is_restricted(self, graph_id: str) -> bool:
        return self.graph_access(graph_id).restricted

    def list_graphs(self, *, include_restricted: bool = False) -> list[GraphSummary]:
        paths = [(self.example_id, self.example_graph_path, "example")]
        paths.extend(
            (path.stem, path, "generated")
            for path in sorted(
                self.graphs_dir.glob("*.json"),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
        )
        summaries: list[GraphSummary] = []
        for graph_id, path, kind in paths:
            access = self.graph_access(graph_id)
            if access.restricted and not include_restricted:
                continue
            graph = GraphArtifact.model_validate_json(path.read_text(encoding="utf-8"))
            summaries.append(
                GraphSummary(
                    id=graph_id,
                    label=(
                        "Five-document evidence checkpoint"
                        if kind == "example"
                        else f"Generated graph · {len(graph.documents)} document(s)"
                    ),
                    generated_at=graph.generated_at,
                    documents=len(graph.documents),
                    entities=len(graph.entities),
                    relationships=len(graph.relationships),
                    observed_cost_usd=graph.observed_cost_usd,
                    trace_id=graph.trace_id,
                    kind=kind,
                    restricted=access.restricted,
                )
            )
        return summaries


def persist_extracted_upload(
    store: WorkbenchStore, extracted: ExtractedUpload, source_bytes: bytes
) -> UploadedDocumentReceipt:
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    document_id = f"upload-{source_sha256[:20]}"
    record = UploadedDocumentRecord(
        document_id=document_id,
        title=extracted.title,
        original_filename=extracted.filename,
        media_type=extracted.media_type,
        source_sha256=source_sha256,
        body_sha256=hashlib.sha256(extracted.body_text.encode("utf-8")).hexdigest(),
        body_text=extracted.body_text,
        extraction_method=extracted.extraction_method,
        page_count=extracted.page_count,
        uploaded_at=utc_now(),
    )
    return store.save_uploaded_document(record, source_bytes)


class ProviderExecutionLane:
    """One serialized worker shared by every provider-spending CREST job."""

    def __init__(self) -> None:
        self.executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="crest-provider",
        )

    def submit(self, function, *args) -> None:
        self.executor.submit(function, *args)


class GraphJobRunner:
    """Single-lane executor that keeps provider-spending jobs serialized."""

    def __init__(
        self,
        store: WorkbenchStore,
        catalog: CorpusCatalog,
        lane: ProviderExecutionLane | None = None,
    ) -> None:
        self.store = store
        self.catalog = catalog
        self.lane = lane or ProviderExecutionLane()

    def submit(self, request: GraphBuildRequest) -> GraphJob:
        now = utc_now()
        job_id = uuid4().hex
        job = GraphJob(
            id=job_id,
            state="queued",
            request=request,
            created_at=now,
            updated_at=now,
            progress_detail="Waiting for the extraction lane",
        )
        self.store.save_job(job)
        self.lane.submit(self._run, job_id)
        return job

    def _run(self, job_id: str) -> None:
        job = self.store.get_job(job_id)
        try:
            job.state = "running"
            job.updated_at = utc_now()
            job.trace_id = f"crest_kg/workbench/{job.id}"
            job.progress_detail = "Extracting grounded entities and relationships"
            self.store.save_job(job)
            connector_ids = [
                self.catalog.connector_for(document_id)
                for document_id in job.request.document_ids
            ]
            documents = self.catalog.load_selected(
                job.request.document_ids,
                max_chars=job.request.max_chars_per_document,
            )
            graph = run_extraction(
                documents,
                model_override=None,
                model_justification_override=None,
                trace_id=job.trace_id,
                max_budget_usd=job.request.max_budget_usd,
                max_output_tokens=3_500,
                refine_relationships=job.request.refine_relationships,
                relationship_max_output_tokens=2_000,
                structured_retries=1,
            )
            graph_id = job.id
            self.store.save_graph(
                graph_id,
                graph,
                connector_ids=connector_ids,
            )
            job.state = "completed"
            job.graph_id = graph_id
            job.progress_detail = (
                f"Completed with {len(graph.entities)} entities and "
                f"{len(graph.relationships)} relationships"
            )
            job.updated_at = utc_now()
            self.store.save_job(job)
        except Exception as exc:
            job.state = "failed"
            job.error = f"{type(exc).__name__}: {exc}"
            job.progress_detail = "Graph build failed"
            job.updated_at = utc_now()
            self.store.save_job(job)


class EvidenceInquiryRunner:
    """Persist evidence before one citation-validated synthesis call."""

    def __init__(
        self,
        store: WorkbenchStore,
        lane: ProviderExecutionLane,
    ) -> None:
        self.store = store
        self.lane = lane

    def submit(
        self,
        request: EvidenceInquiryRequest,
        *,
        collection: ResearchCollection,
        evidence: list[EvidenceChunk],
    ) -> EvidenceInquiry:
        now = utc_now()
        inquiry = EvidenceInquiry(
            id=f"inquiry-{uuid4().hex}",
            state="queued",
            request=request,
            collection_title=collection.title,
            evidence=evidence,
            created_at=now,
            updated_at=now,
            progress_detail=(
                "Waiting for the provider lane"
                if evidence
                else "Completing without a model because no evidence matched"
            ),
        )
        self.store.save_inquiry(inquiry)
        self.lane.submit(self._run, inquiry.id)
        return inquiry

    def _run(self, inquiry_id: str) -> None:
        inquiry = self.store.get_inquiry(inquiry_id)
        try:
            inquiry.state = "running"
            inquiry.updated_at = utc_now()
            inquiry.trace_id = f"crest_kg/inquiries/{inquiry.id}"
            inquiry.progress_detail = "Synthesizing a citation-valid evidence brief"
            self.store.save_inquiry(inquiry)
            brief: EvidenceBrief = generate_evidence_brief(
                question=inquiry.request.question,
                collection_title=inquiry.collection_title,
                evidence=inquiry.evidence,
                trace_id=inquiry.trace_id,
                max_budget_usd=inquiry.request.max_budget_usd,
                max_output_tokens=inquiry.request.max_output_tokens,
                structured_retries=1,
            )
            inquiry.brief = brief
            inquiry.state = "completed"
            inquiry.progress_detail = (
                f"Completed {brief.answer_status} brief with "
                f"{len(brief.findings)} finding(s)"
            )
            inquiry.updated_at = utc_now()
            self.store.save_inquiry(inquiry)
        except Exception as exc:
            inquiry.state = "failed"
            inquiry.error = f"{type(exc).__name__}: {exc}"
            inquiry.progress_detail = "Evidence brief failed; ranked evidence was retained"
            inquiry.updated_at = utc_now()
            self.store.save_inquiry(inquiry)


def request_is_operator(
    *, supplied_token: str | None, tailscale_login: str | None
) -> bool:
    expected_token = os.getenv("CREST_OPERATOR_TOKEN", "")
    if expected_token and supplied_token:
        candidate = supplied_token.removeprefix("Bearer ").strip()
        if secrets.compare_digest(candidate, expected_token):
            return True
    trust_tailscale = os.getenv("CREST_TRUST_TAILSCALE_HEADERS", "0") == "1"
    return bool(trust_tailscale and tailscale_login and tailscale_login.strip())
