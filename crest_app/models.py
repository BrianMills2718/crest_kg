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


class SearchRequest(ApiModel):
    query: str = Field(min_length=1, max_length=200)
    connector_id: Literal["bundled-crest"] = "bundled-crest"
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
    title: str
    source_url: str | None
    metadata: dict[str, str]
    body_preview: str
    body_chars: int
    body_sha256: str


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


class GraphList(ApiModel):
    graphs: list[GraphSummary]
