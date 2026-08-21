"""Search, persistence, authorization, and graph-build services."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from crest_pipeline import (
    GraphArtifact,
    RawDocument,
    derive_document_id,
    load_selected_documents,
    run_extraction,
)

from .models import (
    DocumentDetail,
    DocumentSummary,
    GraphBuildRequest,
    GraphJob,
    GraphSummary,
    SearchResponse,
)


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


class CorpusCatalog:
    """Searchable, immutable view of one tracked CREST corpus."""

    def __init__(self, corpus_path: Path = DEFAULT_CORPUS) -> None:
        self.corpus_path = corpus_path
        payload = json.loads(corpus_path.read_text(encoding="utf-8"))
        raw_items = payload["documents"] if isinstance(payload, dict) else payload
        self.documents = [RawDocument.model_validate(item) for item in raw_items]
        self.by_id: dict[str, RawDocument] = {}
        for document in self.documents:
            document_id = derive_document_id(document)
            if document_id in self.by_id:
                raise ValueError(f"duplicate source document ID: {document_id}")
            self.by_id[document_id] = document

    @property
    def count(self) -> int:
        return len(self.documents)

    def search(self, query: str, *, limit: int) -> SearchResponse:
        normalized_query = " ".join(query.casefold().split())
        terms = tuple(dict.fromkeys(re.findall(r"[a-z0-9]+", normalized_query)))
        scored: list[tuple[float, str, RawDocument, str]] = []
        for document_id, document in self.by_id.items():
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
            scored.append((score, document_id, document, snippet))
        scored.sort(key=lambda item: (-item[0], item[1]))
        results = [
            DocumentSummary(
                document_id=document_id,
                title=document.title,
                source_url=document.url,
                document_type=document.metadata.get("Document Type"),
                collection=document.metadata.get("Collection"),
                publication_date=document.metadata.get("Publication Date"),
                page_count=document.metadata.get("Document Page Count"),
                snippet=snippet,
                score=score,
            )
            for score, document_id, document, snippet in scored[:limit]
        ]
        return SearchResponse(
            query=query,
            connector_id="bundled-crest",
            total_matches=len(scored),
            results=results,
        )

    def detail(self, document_id: str) -> DocumentDetail:
        document = self.by_id.get(document_id)
        if document is None:
            raise KeyError(document_id)
        return DocumentDetail(
            document_id=document_id,
            title=document.title,
            source_url=document.url,
            metadata=document.metadata,
            body_preview=document.body_text[:8_000],
            body_chars=len(document.body_text),
            body_sha256=hashlib.sha256(document.body_text.encode("utf-8")).hexdigest(),
        )


class WorkbenchStore:
    """Atomic JSON persistence for jobs and graph artifacts."""

    example_id = "example-fixed-v2"

    def __init__(self, data_dir: Path, example_graph: Path = DEFAULT_EXAMPLE_GRAPH) -> None:
        self.data_dir = data_dir
        self.jobs_dir = data_dir / "jobs"
        self.graphs_dir = data_dir / "graphs"
        self.example_graph_path = example_graph
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.graphs_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._mark_interrupted_jobs_failed()

    def _mark_interrupted_jobs_failed(self) -> None:
        for path in self.jobs_dir.glob("*.json"):
            job = GraphJob.model_validate_json(path.read_text(encoding="utf-8"))
            if job.state in {"queued", "running"}:
                job.state = "failed"
                job.error = "Service restarted before this build completed."
                job.progress_detail = "Build interrupted by service restart"
                job.updated_at = utc_now()
                self.save_job(job)

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

    def save_graph(self, graph_id: str, graph: GraphArtifact) -> None:
        with self._lock:
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

    def list_graphs(self) -> list[GraphSummary]:
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
                )
            )
        return summaries


class GraphJobRunner:
    """Single-lane executor that keeps provider-spending jobs serialized."""

    def __init__(self, store: WorkbenchStore, corpus_path: Path = DEFAULT_CORPUS) -> None:
        self.store = store
        self.corpus_path = corpus_path
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="crest-build")

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
        self.executor.submit(self._run, job_id)
        return job

    def _run(self, job_id: str) -> None:
        job = self.store.get_job(job_id)
        try:
            job.state = "running"
            job.updated_at = utc_now()
            job.trace_id = f"crest_kg/workbench/{job.id}"
            job.progress_detail = "Extracting grounded entities and relationships"
            self.store.save_job(job)
            documents = load_selected_documents(
                self.corpus_path,
                document_ids=job.request.document_ids,
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
            self.store.save_graph(graph_id, graph)
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
