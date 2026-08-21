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
    max_batch_files: int


class SearchRequest(ApiModel):
    query: str = Field(min_length=1, max_length=200)
    connector_id: Literal[
        "all", "bundled-crest", "user-uploads", "cia-reading-room-live"
    ] = "all"
    limit: int = Field(default=20, ge=1, le=50)
    collection_id: str | None = Field(
        default=None, pattern=r"^collection-[0-9a-f]{16}$"
    )

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


class BatchUploadFailure(ApiModel):
    filename: str
    status_code: int = Field(ge=400, le=599)
    detail: str


class BatchUploadReceipt(ApiModel):
    collection_id: str | None
    successes: list[UploadedDocumentReceipt]
    failures: list[BatchUploadFailure]


class CollectionCreate(ApiModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("title must contain non-whitespace text")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        return " ".join(value.split())


class CollectionUpdate(ApiModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("title")
    @classmethod
    def normalize_optional_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("title must contain non-whitespace text")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_optional_description(cls, value: str | None) -> str | None:
        return " ".join(value.split()) if value is not None else None


class CollectionDocumentsRequest(ApiModel):
    document_ids: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("document_ids")
    @classmethod
    def unique_document_ids(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("document IDs must be nonblank")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("document IDs must be unique")
        return cleaned


class ResearchCollection(ApiModel):
    id: str = Field(pattern=r"^collection-[0-9a-f]{16}$")
    title: str
    description: str
    document_ids: list[str]
    created_at: datetime
    updated_at: datetime


class CollectionList(ApiModel):
    collections: list[ResearchCollection]


class ConnectorProbe(ApiModel):
    connector: ConnectorStatus
    checked_at: datetime
    search_endpoint: str
    search_http_status: int | None = None
    document_http_status: int | None = None


class GraphBuildRequest(ApiModel):
    document_ids: list[str] = Field(min_length=1, max_length=3)
    collection_id: str | None = Field(
        default=None, pattern=r"^collection-[0-9a-f]{16}$"
    )
    inquiry_id: str | None = Field(
        default=None, pattern=r"^inquiry-[0-9a-f]{32}$"
    )
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


class GraphJobList(ApiModel):
    jobs: list[GraphJob]


class EvidenceQueryRequest(ApiModel):
    collection_id: str = Field(pattern=r"^collection-[0-9a-f]{16}$")
    question: str = Field(min_length=3, max_length=500)
    evidence_limit: int = Field(default=6, ge=2, le=10)
    max_chars_per_document: int = Field(default=50_000, ge=1_000, le=100_000)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 3:
            raise ValueError("question must contain meaningful text")
        return normalized


class EvidenceInquiryRequest(EvidenceQueryRequest):
    max_budget_usd: float = Field(default=0.06, gt=0, le=1.0)
    max_output_tokens: int = Field(default=1_800, ge=500, le=3_000)


class EvidenceScore(ApiModel):
    bm25: float = Field(ge=0)
    coverage: float = Field(ge=0, le=1)
    fuzzy: float = Field(ge=0, le=1)
    phrase: float = Field(ge=0)
    title: float = Field(ge=0)


class EvidenceChunk(ApiModel):
    id: str = Field(pattern=r"^evidence-[0-9a-f]{20}$")
    document_id: str
    connector_id: Literal[
        "bundled-crest", "user-uploads", "cia-reading-room-live"
    ]
    title: str
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    text: str = Field(min_length=1)
    rank: int = Field(ge=1)
    score: float = Field(gt=0)
    score_components: EvidenceScore
    matched_terms: list[str]

    @field_validator("matched_terms")
    @classmethod
    def unique_matched_terms(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))


class EvidencePreview(ApiModel):
    collection_id: str = Field(pattern=r"^collection-[0-9a-f]{16}$")
    question: str
    evidence: list[EvidenceChunk]


FindingClassification = Literal["support", "contradiction", "uncertainty"]
AnswerStatus = Literal["answered", "partial", "insufficient"]


class BriefFinding(ApiModel):
    statement: str = Field(min_length=1, max_length=1_000)
    classification: FindingClassification
    citation_ids: list[str] = Field(min_length=1, max_length=6)

    @field_validator("citation_ids")
    @classmethod
    def unique_citations(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("citation IDs must be nonblank")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("citation IDs must be unique within a finding")
        return cleaned


class ProviderEvidenceBrief(ApiModel):
    answer_status: AnswerStatus
    synthesis: str = Field(min_length=1, max_length=2_000)
    synthesis_citation_ids: list[str] = Field(default_factory=list, max_length=6)
    findings: list[BriefFinding] = Field(default_factory=list, max_length=8)
    unresolved_questions: list[str] = Field(default_factory=list, max_length=6)

    @field_validator("synthesis_citation_ids")
    @classmethod
    def unique_synthesis_citations(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value]
        if any(not item for item in cleaned):
            raise ValueError("synthesis citation IDs must be nonblank")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("synthesis citation IDs must be unique")
        return cleaned


class EvidenceBrief(ProviderEvidenceBrief):
    model: str
    trace_id: str
    observed_cost_usd: float = Field(ge=0)


InquiryState = Literal["queued", "running", "completed", "failed"]


class EvidenceInquiry(ApiModel):
    id: str = Field(pattern=r"^inquiry-[0-9a-f]{32}$")
    state: InquiryState
    request: EvidenceInquiryRequest
    collection_title: str
    evidence: list[EvidenceChunk]
    created_at: datetime
    updated_at: datetime
    trace_id: str | None = None
    brief: EvidenceBrief | None = None
    error: str | None = None
    progress_detail: str


class EvidenceInquiryList(ApiModel):
    inquiries: list[EvidenceInquiry]


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
