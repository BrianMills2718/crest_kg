"""Typed public contracts for the CREST workbench."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConnectorStatus(ApiModel):
    id: str
    label: str
    state: Literal["available", "unavailable"]
    detail: str
    document_count: int | None = None


class Capabilities(ApiModel):
    service: Literal["crest-workbench"] = "crest-workbench"
    source_revision: str
    connectors: list[ConnectorStatus]
    graph_build_enabled: bool
    graph_build_authorized: bool
    graph_build_requires_operator: bool = True
    max_documents_per_build: int
    max_build_budget_usd: float
    document_upload_enabled: bool
    document_upload_authorized: bool
    max_upload_bytes: int


class SearchRequest(ApiModel):
    query: str = Field(min_length=1, max_length=200)
    connector_id: Literal[
        "all", "bundled-crest", "user-uploads", "cia-reading-room-live"
    ] = "all"
    limit: int = Field(default=20, ge=1, le=50)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("query must contain non-whitespace text")
        return normalized


class DocumentSummary(ApiModel):
    document_id: str
    connector_id: Literal[
        "bundled-crest", "user-uploads", "cia-reading-room-live"
    ]
    title: str
    source_url: str | None
    document_type: str | None
    collection: str | None
    publication_date: str | None
    page_count: str | None
    snippet: str
    score: float


class SearchResponse(ApiModel):
    query: str
    connector_id: str
    total_matches: int
    results: list[DocumentSummary]


class DocumentDetail(ApiModel):
    document_id: str
    connector_id: Literal[
        "bundled-crest", "user-uploads", "cia-reading-room-live"
    ]
    title: str
    source_url: str | None
    metadata: dict[str, str]
    body_preview: str
    body_chars: int
    body_sha256: str


UploadExtractionMethod = Literal[
    "plain-text", "pdf-text", "pdf-ocr", "pdf-mixed", "image-ocr"
]


class UploadedDocumentRecord(ApiModel):
    """Durable private source record persisted in the workbench data volume."""

    document_id: str
    title: str
    original_filename: str
    media_type: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    body_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    body_text: str = Field(min_length=1)
    extraction_method: UploadExtractionMethod
    page_count: int = Field(ge=1)
    uploaded_at: datetime


class UploadedDocumentReceipt(ApiModel):
    document_id: str
    title: str
    original_filename: str
    media_type: str
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    body_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    body_chars: int = Field(ge=1)
    extraction_method: UploadExtractionMethod
    page_count: int = Field(ge=1)
    uploaded_at: datetime
    duplicate: bool = False


class UploadedDocumentList(ApiModel):
    documents: list[UploadedDocumentReceipt]


class ConnectorProbe(ApiModel):
    connector: ConnectorStatus
    checked_at: datetime
    search_endpoint: str
    search_http_status: int | None = None
    document_http_status: int | None = None


class GraphBuildRequest(ApiModel):
    document_ids: list[str] = Field(min_length=1, max_length=3)
    max_chars_per_document: int = Field(default=12_000, ge=1_000, le=20_000)
    max_budget_usd: float = Field(default=0.10, gt=0, le=5.0)
    refine_relationships: bool = False

    @field_validator("document_ids")
    @classmethod
    def unique_document_ids(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("document IDs must be nonblank")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("document IDs must be unique")
        return cleaned


JobState = Literal["queued", "running", "completed", "failed"]


class GraphJob(ApiModel):
    id: str
    state: JobState
    request: GraphBuildRequest
    created_at: datetime
    updated_at: datetime
    graph_id: str | None = None
    trace_id: str | None = None
    error: str | None = None
    progress_detail: str


class GraphSummary(ApiModel):
    id: str
    label: str
    generated_at: datetime
    documents: int
    entities: int
    relationships: int
    observed_cost_usd: float
    trace_id: str
    kind: Literal["example", "generated"]
    restricted: bool = False


class GraphList(ApiModel):
    graphs: list[GraphSummary]


class GraphAccessRecord(ApiModel):
    graph_id: str
    restricted: bool
    connector_ids: list[str]
    recorded_at: datetime
