#!/usr/bin/env python3
"""Deterministic, provenance-preserving CREST knowledge-graph pipeline.

This is the canonical extraction path for the CREST research workbench.  It
keeps corpus selection deterministic, validates model output with Pydantic,
grounds every assertion in an exact source quote, and refuses to write graphs
that violate referential integrity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

PIPELINE_VERSION: Literal["crest-kg-v2"] = "crest-kg-v2"
PROMPT_PATH = Path(__file__).with_name("prompts") / "crest_extraction.yaml"
RELATIONSHIP_PROMPT_PATH = (
    Path(__file__).with_name("prompts") / "crest_relationship_refinement.yaml"
)
PROMPT_REF = "crest_kg.crest_extraction@4"
RELATIONSHIP_PROMPT_REF = "crest_kg.crest_relationship_refinement@1"
RECOVERABLE_PROMPT_REFS = frozenset(
    {
        "crest_kg.crest_extraction@2",
        PROMPT_REF,
    }
)
MAX_EVIDENCE_LINES = 5
MAX_ENTITIES_PER_DOCUMENT = 20
MAX_RELATIONSHIPS_PER_DOCUMENT = 8
MAX_RELATIONSHIP_CANDIDATES_PER_DOCUMENT = 30
DOCUMENT_NUMBER_KEYS = (
    "Document Number (FOIA) /ESDN (CREST)",
    "Document Number",
    "CREST Number",
)


class StrictModel(BaseModel):
    """Base model for boundaries that must reject unexpected fields."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class EntityKind(str, Enum):
    """Entity classes supported by the bounded CREST extraction contract."""

    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    EVENT = "event"
    CONCEPT = "concept"
    TIME = "time"
    WORK = "work"
    OTHER = "other"


class RawDocument(BaseModel):
    """Validated source record loaded from a CREST corpus export."""

    model_config = ConfigDict(extra="ignore")

    url: str | None = Field(default=None, description="Public source URL for the CREST record.")
    title: str = Field(min_length=1, description="Document title from the source record.")
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Source metadata normalized to string values.",
    )
    body_text: str = Field(min_length=1, description="OCR or transcription text to analyze.")

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must contain non-whitespace text")
        return value

    @field_validator("body_text")
    @classmethod
    def preserve_source_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("body_text must contain non-whitespace text")
        return value

    @field_validator("metadata", mode="before")
    @classmethod
    def normalize_metadata(cls, value: Any) -> dict[str, str]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError("metadata must be an object")
        return {
            str(key).strip(): str(item).strip()
            for key, item in value.items()
            if str(key).strip() and item is not None
        }


class SourceDocument(StrictModel):
    """Stable manifest entry for the exact source slice shown to the model."""

    document_id: str = Field(min_length=1, description="Stable CREST or FOIA document identifier.")
    title: str = Field(min_length=1, description="Source document title.")
    source_url: str | None = Field(default=None, description="Public source URL, when available.")
    corpus_path: str = Field(min_length=1, description="Corpus path supplied to the pipeline.")
    body_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="SHA-256 digest of the complete source body text.",
    )
    total_chars: int = Field(ge=1, description="Character count of the complete source body.")
    analyzed_start: int = Field(ge=0, description="Inclusive source offset shown to the model.")
    analyzed_end: int = Field(gt=0, description="Exclusive source offset shown to the model.")
    analyzed_lines: int = Field(
        ge=1,
        description="Count of numbered source lines shown to the model.",
    )

    @model_validator(mode="after")
    def validate_window(self) -> Self:
        if self.analyzed_start >= self.analyzed_end:
            raise ValueError("analyzed_start must be before analyzed_end")
        if self.analyzed_end > self.total_chars:
            raise ValueError("analyzed window exceeds source text")
        return self


@dataclass(frozen=True)
class SourceLine:
    """One numbered source line and its exact character offsets."""

    number: int
    start_char: int
    end_char: int


@dataclass(frozen=True)
class LoadedDocument:
    """In-memory source document paired with its portable manifest."""

    manifest: SourceDocument
    metadata: dict[str, str]
    analysis_text: str
    source_lines: tuple[SourceLine, ...]


class EvidenceCandidate(StrictModel):
    """Bounded source-line citation emitted by the extractor."""

    line_start: int = Field(
        ge=1,
        description="First cited L-number from the supplied document, inclusive.",
    )
    line_count: int = Field(
        ge=1,
        le=MAX_EVIDENCE_LINES,
        description="Number of consecutive cited lines, from one through five.",
    )

    @property
    def line_end(self) -> int:
        """Return the inclusive final line derived from the bounded count."""

        return self.line_start + self.line_count - 1


class EntityCandidate(StrictModel):
    """Document-local entity proposed by the model."""

    local_id: str = Field(
        min_length=1,
        pattern=r"^[A-Za-z0-9_.:-]+$",
        description="Document-local identifier referenced by relationships.",
    )
    name: str = Field(min_length=1, description="Entity name exactly as supported by the document.")
    entity_type: EntityKind = Field(alias="type", description="Semantic class of the entity.")
    attributes: dict[str, str] = Field(
        default_factory=dict,
        description="Only attributes explicitly supported by the evidence quote.",
    )
    evidence: EvidenceCandidate = Field(description="Bounded source lines supporting this entity.")

    @field_validator("local_id", "name")
    @classmethod
    def strip_entity_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must contain non-whitespace text")
        return value


class RelationshipCandidate(StrictModel):
    """Document-local directed assertion proposed by the model."""

    source_entity_id: str = Field(
        min_length=1,
        description="local_id of the relationship source entity.",
    )
    target_entity_id: str = Field(
        min_length=1,
        description="local_id of the relationship target entity.",
    )
    relationship_type: str = Field(
        alias="type",
        min_length=1,
        description="Short directed predicate supported by the evidence quote.",
    )
    source_mention: str = Field(
        min_length=1,
        description="Exact source-entity surface text copied from the cited quote.",
    )
    relation_phrase: str = Field(
        min_length=1,
        description="Exact predicate-supporting surface text copied from the cited quote.",
    )
    target_mention: str = Field(
        min_length=1,
        description="Exact target-entity surface text copied from the cited quote.",
    )
    support_reasoning: str = Field(
        min_length=1,
        description="Concise explanation of how the exact mentions support this directed edge.",
    )
    attributes: dict[str, str] = Field(
        default_factory=dict,
        description="Only relationship attributes explicitly supported by the quote.",
    )
    evidence: EvidenceCandidate = Field(description="Bounded source lines supporting the relationship.")

    @field_validator(
        "source_entity_id",
        "target_entity_id",
        "relationship_type",
        "source_mention",
        "relation_phrase",
        "target_mention",
        "support_reasoning",
    )
    @classmethod
    def strip_relationship_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must contain non-whitespace text")
        return value


class ProviderEvidenceCandidate(StrictModel):
    """Compact provider-facing evidence schema with the critical direct bound."""

    line_start: int = Field(ge=1)
    line_count: int = Field(ge=1, le=MAX_EVIDENCE_LINES)


class ProviderEntityCandidate(StrictModel):
    """Compact provider-facing entity shape; strict semantics are applied locally."""

    local_id: str
    name: str
    entity_type: EntityKind = Field(alias="type")
    evidence: ProviderEvidenceCandidate


class ProviderRelationshipCandidate(StrictModel):
    """Compact provider-facing relationship shape; strict semantics are applied locally."""

    source_entity_id: str
    target_entity_id: str
    relationship_type: str = Field(alias="type")
    source_mention: str
    relation_phrase: str
    target_mention: str
    support_reasoning: str
    evidence: ProviderEvidenceCandidate


class ProviderDocumentExtraction(StrictModel):
    """Portable structured-response envelope intentionally small enough for Gemini."""

    entities: list[ProviderEntityCandidate]
    relationships: list[ProviderRelationshipCandidate]


class ProviderRelationshipExtraction(StrictModel):
    """Compact second-stage envelope over an already declared entity set."""

    relationships: list[ProviderRelationshipCandidate]


class DocumentExtraction(StrictModel):
    """Validated structured model output for one source document."""

    entities: list[EntityCandidate] = Field(
        max_length=MAX_ENTITIES_PER_DOCUMENT,
        description="Entities supported by exact quotes in this document. Use an empty list when none qualify."
    )
    relationships: list[RelationshipCandidate] = Field(
        max_length=MAX_RELATIONSHIP_CANDIDATES_PER_DOCUMENT,
        description="Directed relationships whose endpoints are declared entities. Use an empty list when none qualify."
    )

    @model_validator(mode="after")
    def validate_local_graph(self) -> Self:
        entity_ids = [entity.local_id for entity in self.entities]
        if len(entity_ids) != len(set(entity_ids)):
            raise ValueError("entity local_id values must be unique within a document")

        known_ids = set(entity_ids)
        seen_relationships: set[tuple[str, str, str, int, int]] = set()
        for relationship in self.relationships:
            if relationship.source_entity_id not in known_ids:
                raise ValueError(
                    f"relationship source is undeclared: {relationship.source_entity_id}"
                )
            if relationship.target_entity_id not in known_ids:
                raise ValueError(
                    f"relationship target is undeclared: {relationship.target_entity_id}"
                )
            key = (
                relationship.source_entity_id,
                relationship.target_entity_id,
                normalize_text(relationship.relationship_type),
                relationship.evidence.line_start,
                relationship.evidence.line_end,
            )
            if key in seen_relationships:
                raise ValueError("duplicate relationship assertion within a document")
            seen_relationships.add(key)
        return self


class Provenance(StrictModel):
    """Verifiable source location for one entity or relationship assertion."""

    document_id: str = Field(min_length=1, description="Source document identifier.")
    source_url: str | None = Field(default=None, description="Public source URL, when available.")
    corpus_path: str = Field(min_length=1, description="Corpus artifact containing the source record.")
    body_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Digest binding the quote offsets to exact source text.",
    )
    quote: str = Field(min_length=1, description="Exact supporting source quote.")
    line_start: int = Field(ge=1, description="First cited source line, inclusive.")
    line_end: int = Field(ge=1, description="Last cited source line, inclusive.")
    start_char: int = Field(ge=0, description="Inclusive quote offset in the complete body text.")
    end_char: int = Field(gt=0, description="Exclusive quote offset in the complete body text.")

    @model_validator(mode="after")
    def validate_offsets(self) -> Self:
        if self.end_char - self.start_char != len(self.quote):
            raise ValueError("quote length does not match source offsets")
        if self.line_end < self.line_start:
            raise ValueError("line_end must be greater than or equal to line_start")
        return self


class ExtractionRejection(StrictModel):
    """Visible record of one model candidate rejected at the source boundary."""

    document_id: str = Field(min_length=1, description="Source document identifier.")
    item_kind: Literal["entity", "relationship"] = Field(
        description="Candidate collection that contained the rejected item."
    )
    item_index: int = Field(ge=0, description="Zero-based index in the model response.")
    candidate_ref: str = Field(
        min_length=1,
        description="Compact local identifier for the rejected candidate.",
    )
    reason: str = Field(
        min_length=1,
        description="Deterministic boundary failure that caused rejection.",
    )


def validate_provider_extraction(
    document_id: str,
    response: ProviderDocumentExtraction,
) -> tuple[DocumentExtraction, list[ExtractionRejection]]:
    """Convert a compact provider response into strict candidates item by item."""

    entities: list[EntityCandidate] = []
    known_entity_ids: set[str] = set()
    rejections: list[ExtractionRejection] = []
    for index, provider_entity in enumerate(response.entities):
        candidate_ref = provider_entity.local_id.strip() or f"entity:{index}"
        if index >= MAX_ENTITIES_PER_DOCUMENT:
            rejections.append(
                ExtractionRejection(
                    document_id=document_id,
                    item_kind="entity",
                    item_index=index,
                    candidate_ref=candidate_ref,
                    reason=(
                        "candidate exceeds per-document entity limit of "
                        f"{MAX_ENTITIES_PER_DOCUMENT}"
                    ),
                )
            )
            continue
        try:
            entity = EntityCandidate.model_validate(
                provider_entity.model_dump(by_alias=True)
            )
        except ValidationError as exc:
            rejections.append(
                ExtractionRejection(
                    document_id=document_id,
                    item_kind="entity",
                    item_index=index,
                    candidate_ref=candidate_ref,
                    reason=f"strict entity validation failed: {exc}",
                )
            )
            continue
        if entity.local_id in known_entity_ids:
            rejections.append(
                ExtractionRejection(
                    document_id=document_id,
                    item_kind="entity",
                    item_index=index,
                    candidate_ref=candidate_ref,
                    reason="duplicate entity local_id within the document",
                )
            )
            continue
        entities.append(entity)
        known_entity_ids.add(entity.local_id)

    relationships: list[RelationshipCandidate] = []
    seen_relationships: set[tuple[str, str, str, int, int]] = set()
    for index, provider_relationship in enumerate(response.relationships):
        candidate_ref = (
            f"{provider_relationship.source_entity_id}:"
            f"{safe_predicate(provider_relationship.relationship_type)}:"
            f"{provider_relationship.target_entity_id}"
        )
        if index >= MAX_RELATIONSHIP_CANDIDATES_PER_DOCUMENT:
            rejections.append(
                ExtractionRejection(
                    document_id=document_id,
                    item_kind="relationship",
                    item_index=index,
                    candidate_ref=candidate_ref,
                    reason=(
                        "candidate exceeds per-document relationship limit of "
                        f"{MAX_RELATIONSHIP_CANDIDATES_PER_DOCUMENT}"
                    ),
                )
            )
            continue
        try:
            relationship = RelationshipCandidate.model_validate(
                provider_relationship.model_dump(by_alias=True)
            )
        except ValidationError as exc:
            rejections.append(
                ExtractionRejection(
                    document_id=document_id,
                    item_kind="relationship",
                    item_index=index,
                    candidate_ref=candidate_ref,
                    reason=f"strict relationship validation failed: {exc}",
                )
            )
            continue
        missing_endpoints = sorted(
            {
                relationship.source_entity_id,
                relationship.target_entity_id,
            }
            - known_entity_ids
        )
        if missing_endpoints:
            rejections.append(
                ExtractionRejection(
                    document_id=document_id,
                    item_kind="relationship",
                    item_index=index,
                    candidate_ref=candidate_ref,
                    reason=(
                        "relationship endpoint is undeclared after strict entity "
                        f"validation: {missing_endpoints}"
                    ),
                )
            )
            continue
        key = (
            relationship.source_entity_id,
            relationship.target_entity_id,
            normalize_text(relationship.relationship_type),
            relationship.evidence.line_start,
            relationship.evidence.line_end,
        )
        if key in seen_relationships:
            rejections.append(
                ExtractionRejection(
                    document_id=document_id,
                    item_kind="relationship",
                    item_index=index,
                    candidate_ref=candidate_ref,
                    reason="duplicate relationship assertion within the document",
                )
            )
            continue
        seen_relationships.add(key)
        relationships.append(relationship)

    return DocumentExtraction(
        entities=entities,
        relationships=relationships,
    ), rejections


def validate_provider_relationship_extraction(
    document_id: str,
    response: ProviderRelationshipExtraction,
    entities: list[EntityCandidate],
) -> tuple[DocumentExtraction, list[ExtractionRejection]]:
    """Apply the same item-level strict conversion to a relationship-only response."""

    provider_entities = [
        ProviderEntityCandidate(
            local_id=entity.local_id,
            name=entity.name,
            type=entity.entity_type,
            evidence=ProviderEvidenceCandidate(
                line_start=entity.evidence.line_start,
                line_count=entity.evidence.line_count,
            ),
        )
        for entity in entities
    ]
    extraction, rejections = validate_provider_extraction(
        document_id,
        ProviderDocumentExtraction(
            entities=provider_entities,
            relationships=response.relationships,
        ),
    )
    return DocumentExtraction(
        entities=entities,
        relationships=extraction.relationships,
    ), rejections


class RecoveredExtractionReceipt(StrictModel):
    """Trace-bound proof that one prior successful extraction was reused."""

    stage: Literal["primary", "relationship_refinement"] = Field(
        default="primary",
        description="Pipeline stage whose successful response was reused.",
    )
    document_id: str = Field(min_length=1, description="Recovered source document identifier.")
    trace_id: str = Field(min_length=1, description="Exact successful document trace.")
    call_id: int = Field(ge=1, description="Terminal llm_client call-row identity.")
    logical_call_id: str = Field(
        min_length=1,
        description="Structured-call identity joining the selected attempt lifecycle.",
    )
    selected_attempt_ordinal: int = Field(
        ge=0,
        description="Zero-based selected structured-output attempt.",
    )
    schema_hash: str = Field(
        min_length=1,
        description="Provider-facing response-schema hash retained by llm_client.",
    )
    raw_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Digest of the selected raw provider content.",
    )
    selected_attempt_receipt_digest: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Integrity digest over the selected-attempt runtime evidence.",
    )
    response_sha256: str = Field(
        pattern=r"^[0-9a-f]{64}$",
        description="Digest of the normalized terminal response that was revalidated.",
    )
    model: str = Field(min_length=1, description="Resolved model that produced the response.")
    prompt_ref: str = Field(
        min_length=1,
        description="Prompt version retained by the recovered terminal row.",
    )
    observed_cost_usd: float = Field(
        ge=0,
        description="Successful call cost reported in the recovered terminal row.",
    )


class RelationshipGrounding(StrictModel):
    """Exact endpoint and predicate binding for one relationship observation."""

    evidence: Provenance = Field(description="Exact source quote supporting the edge.")
    source_mention: str = Field(
        min_length=1,
        description="Exact source-entity surface text inside evidence.quote.",
    )
    relation_phrase: str = Field(
        min_length=1,
        description="Exact predicate-supporting surface text inside evidence.quote.",
    )
    target_mention: str = Field(
        min_length=1,
        description="Exact target-entity surface text inside evidence.quote.",
    )
    support_reasoning: str = Field(
        min_length=1,
        description="Concise explanation of the directed semantic mapping.",
    )

    @field_validator(
        "source_mention",
        "relation_phrase",
        "target_mention",
        "support_reasoning",
    )
    @classmethod
    def strip_grounding_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must contain non-whitespace text")
        return value

    @model_validator(mode="after")
    def validate_exact_fragments(self) -> Self:
        _validate_relationship_fragments(
            quote=self.evidence.quote,
            source_mention=self.source_mention,
            relation_phrase=self.relation_phrase,
            target_mention=self.target_mention,
        )
        return self


class GraphEntity(StrictModel):
    """Canonical typed entity with aggregated grounded observations."""

    id: str = Field(min_length=1, description="Deterministic typed identity key.")
    name: str = Field(min_length=1, description="Preferred observed entity name.")
    entity_type: EntityKind = Field(alias="type", description="Semantic class included in identity.")
    attributes: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Distinct observed attribute values without destructive overwrites.",
    )
    evidence: list[Provenance] = Field(
        min_length=1,
        description="Source observations supporting the entity.",
    )


class GraphRelationship(StrictModel):
    """Canonical directed relationship with one or more grounded observations."""

    id: str = Field(min_length=1, description="Deterministic relationship identifier.")
    source: str = Field(min_length=1, description="Canonical source entity ID.")
    target: str = Field(min_length=1, description="Canonical target entity ID.")
    relationship_type: str = Field(alias="type", min_length=1, description="Directed predicate.")
    attributes: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Distinct observed relationship attribute values.",
    )
    evidence: list[Provenance] = Field(
        min_length=1,
        description="Source observations supporting this relationship.",
    )
    groundings: list[RelationshipGrounding] = Field(
        default_factory=list,
        description=(
            "Exact endpoint and predicate bindings for v2 observations; empty only for "
            "legacy v1 artifacts."
        ),
    )


class GraphArtifact(StrictModel):
    """Complete validated and provenance-preserving knowledge-graph artifact."""

    schema_version: Literal["crest-kg-v1", "crest-kg-v2"] = Field(
        description="Graph contract version."
    )
    generated_at: datetime = Field(description="UTC time when the run completed.")
    model: str = Field(min_length=1, description="Resolved model used for extraction.")
    prompt_ref: str | None = Field(
        default=None,
        description="Current extraction prompt contract; absent only on legacy v1 artifacts.",
    )
    relationship_prompt_ref: str | None = Field(
        default=None,
        description="Optional dedicated relationship-refinement prompt contract.",
    )
    relationship_model: str | None = Field(
        default=None,
        description="Resolved model used by the optional relationship-refinement stage.",
    )
    trace_id: str = Field(min_length=1, description="Root llm_client observability trace.")
    max_budget_usd: float = Field(gt=0, description="User-authorized run budget ceiling.")
    observed_cost_usd: float = Field(
        ge=0,
        description="Successful current and recovered extraction cost reported by llm_client.",
    )
    prior_observed_cost_usd: float = Field(
        default=0.0,
        ge=0,
        description="Known earlier spend not represented by a successful recovered extraction.",
    )
    unattributed_cost_reserve_usd: float = Field(
        default=0.0,
        ge=0,
        description="Conservative budget reserve for interrupted calls lacking a terminal cost row.",
    )
    recovered_extractions: list[RecoveredExtractionReceipt] = Field(
        default_factory=list,
        description="Prior successful document calls reused without another provider request.",
    )
    documents: list[SourceDocument] = Field(
        min_length=1,
        description="Exact, deterministic source selection for this run.",
    )
    entities: list[GraphEntity] = Field(description="Canonical grounded entities.")
    relationships: list[GraphRelationship] = Field(description="Canonical grounded relationships.")
    rejections: list[ExtractionRejection] = Field(
        default_factory=list,
        description="Model candidates rejected by deterministic source-boundary checks.",
    )

    @model_validator(mode="after")
    def validate_graph_integrity(self) -> Self:
        if self.schema_version == "crest-kg-v2" and not self.prompt_ref:
            raise ValueError("v2 graph must declare its extraction prompt reference")
        accounted_cost = (
            self.observed_cost_usd
            + self.prior_observed_cost_usd
            + self.unattributed_cost_reserve_usd
        )
        if accounted_cost > self.max_budget_usd + 1e-12:
            raise ValueError("observed spend and reserve exceed the authorized budget")

        document_ids = [document.document_id for document in self.documents]
        if len(document_ids) != len(set(document_ids)):
            raise ValueError("document IDs must be unique")
        known_documents = set(document_ids)

        recovered_stage_documents = [
            (receipt.stage, receipt.document_id)
            for receipt in self.recovered_extractions
        ]
        if len(recovered_stage_documents) != len(set(recovered_stage_documents)):
            raise ValueError("recovered extraction stage/document pairs must be unique")
        for receipt in self.recovered_extractions:
            if receipt.document_id not in known_documents:
                raise ValueError(
                    "recovered extraction references unknown document: "
                    f"{receipt.document_id}"
                )
            expected_receipt_model = (
                self.relationship_model
                if receipt.stage == "relationship_refinement"
                else self.model
            )
            if receipt.model != expected_receipt_model:
                raise ValueError(
                    "recovered extraction model differs from its graph stage model: "
                    f"{receipt.stage}/{receipt.document_id}"
                )
        recovered_cost = sum(
            receipt.observed_cost_usd for receipt in self.recovered_extractions
        )
        if recovered_cost > self.observed_cost_usd + 1e-12:
            raise ValueError("recovered extraction cost exceeds observed graph cost")

        entity_ids = [entity.id for entity in self.entities]
        if len(entity_ids) != len(set(entity_ids)):
            raise ValueError("entity IDs must be unique")
        known_entities = set(entity_ids)
        entities_by_id = {entity.id: entity for entity in self.entities}

        relationship_ids = [relationship.id for relationship in self.relationships]
        if len(relationship_ids) != len(set(relationship_ids)):
            raise ValueError("relationship IDs must be unique")

        for entity in self.entities:
            _validate_provenance_documents(entity.evidence, known_documents)
        for rejection in self.rejections:
            if rejection.document_id not in known_documents:
                raise ValueError(
                    f"rejection references unknown document: {rejection.document_id}"
                )
        for relationship in self.relationships:
            if relationship.source not in known_entities:
                raise ValueError(f"dangling relationship source: {relationship.source}")
            if relationship.target not in known_entities:
                raise ValueError(f"dangling relationship target: {relationship.target}")
            _validate_provenance_documents(relationship.evidence, known_documents)
            if self.schema_version == "crest-kg-v2":
                if not relationship.groundings:
                    raise ValueError(
                        f"v2 relationship has no exact grounding: {relationship.id}"
                    )
                _validate_relationship_groundings(
                    relationship,
                    entities_by_id=entities_by_id,
                    known_documents=known_documents,
                )
        return self


def _validate_provenance_documents(
    evidence: list[Provenance], known_documents: set[str]
) -> None:
    for item in evidence:
        if item.document_id not in known_documents:
            raise ValueError(f"provenance references unknown document: {item.document_id}")


def normalize_text(value: str) -> str:
    """Normalize text for deterministic identity comparisons."""

    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(normalized.split())


_PRONOMINAL_MENTIONS = {
    "i",
    "he",
    "her",
    "hers",
    "him",
    "his",
    "it",
    "its",
    "me",
    "mine",
    "my",
    "our",
    "ours",
    "she",
    "that",
    "their",
    "theirs",
    "them",
    "these",
    "they",
    "this",
    "those",
    "us",
    "we",
    "who",
    "whom",
    "whose",
    "you",
    "your",
    "yours",
}
_INITIALISM_STOP_WORDS = {"a", "an", "and", "for", "of", "the", "to"}
_LEADING_ARTICLES = {"a", "an", "the"}
_PREDICATE_HELPER_WORDS = {
    "a",
    "an",
    "be",
    "been",
    "being",
    "had",
    "has",
    "have",
    "is",
    "of",
    "the",
    "was",
    "were",
}
_DIRECTIONAL_PREDICATE_WORDS = {
    "against",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "on",
    "through",
    "to",
    "toward",
    "with",
}


def _alphanumeric_words(value: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z0-9]+", normalize_text(value)))


def _semantic_key(value: str) -> str:
    return " ".join(_alphanumeric_words(value))


def _initialism(value: str) -> str:
    return "".join(
        word[0]
        for word in _alphanumeric_words(value)
        if word not in _INITIALISM_STOP_WORDS
    )


def _without_leading_articles(words: tuple[str, ...]) -> tuple[str, ...]:
    index = 0
    while index < len(words) and words[index] in _LEADING_ARTICLES:
        index += 1
    return words[index:]


def _is_contiguous_word_sequence(
    candidate: tuple[str, ...],
    value: tuple[str, ...],
) -> bool:
    if not candidate or len(candidate) > len(value):
        return False
    width = len(candidate)
    return any(
        value[index : index + width] == candidate
        for index in range(len(value) - width + 1)
    )


def _word_stem(word: str) -> str:
    for suffix in ("ations", "ation", "ments", "ment", "ingly", "edly", "ing", "ied", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            if suffix == "ied":
                return f"{word[:-3]}y"
            return word[: -len(suffix)]
    return word


def predicate_supported_by_phrase(predicate: str, relation_phrase: str) -> bool:
    """Require lexical predicate support, including explicit directional words."""

    predicate_words = _alphanumeric_words(predicate)
    phrase_words = _alphanumeric_words(relation_phrase)
    if not any(len(word) >= 2 for word in phrase_words):
        return False
    for word in predicate_words:
        if word in _DIRECTIONAL_PREDICATE_WORDS and word not in phrase_words:
            return False
    predicate_stems = {
        _word_stem(word)
        for word in predicate_words
        if word not in _PREDICATE_HELPER_WORDS
        and word not in _DIRECTIONAL_PREDICATE_WORDS
    }
    phrase_stems = {_word_stem(word) for word in phrase_words}
    return bool(predicate_stems & phrase_stems)


def mention_identifies_entity(mention: str, entity_name: str) -> bool:
    """Return whether a non-pronominal surface mention names an entity."""

    mention_key = _semantic_key(mention)
    entity_key = _semantic_key(entity_name)
    if not mention_key or not entity_key or mention_key in _PRONOMINAL_MENTIONS:
        return False
    mention_words = _without_leading_articles(_alphanumeric_words(mention))
    entity_words = _without_leading_articles(_alphanumeric_words(entity_name))
    if _is_contiguous_word_sequence(
        mention_words, entity_words
    ) or _is_contiguous_word_sequence(entity_words, mention_words):
        return True

    compact_mention = mention_key.replace(" ", "")
    compact_entity = entity_key.replace(" ", "")
    mention_initialism = _initialism(mention)
    entity_initialism = _initialism(entity_name)
    return bool(
        len(compact_mention) >= 2
        and len(compact_entity) >= 2
        and (
            compact_mention == entity_initialism
            or compact_entity == mention_initialism
        )
    )


def _require_exact_fragment(quote: str, fragment: str, field_name: str) -> None:
    if fragment not in quote:
        raise ValueError(f"{field_name} is not an exact substring of the cited quote")


def _materialize_exact_fragment(quote: str, fragment: str, field_name: str) -> str:
    """Map whitespace-equivalent model text back to exact source characters."""

    if fragment in quote:
        return fragment
    pattern = "".join(
        r"\s+" if part.isspace() else re.escape(part)
        for part in re.split(r"(\s+)", fragment)
        if part
    )
    match = re.search(pattern, quote)
    if match is None:
        raise ValueError(f"{field_name} is not an exact substring of the cited quote")
    return match.group(0)


def _validate_relationship_fragments(
    *,
    quote: str,
    source_mention: str,
    relation_phrase: str,
    target_mention: str,
) -> None:
    _require_exact_fragment(quote, source_mention, "source_mention")
    _require_exact_fragment(quote, relation_phrase, "relation_phrase")
    _require_exact_fragment(quote, target_mention, "target_mention")
    for field_name, mention in (
        ("source_mention", source_mention),
        ("target_mention", target_mention),
    ):
        if _semantic_key(mention) in _PRONOMINAL_MENTIONS:
            raise ValueError(f"{field_name} may not be a pronoun or demonstrative")


def _provenance_key(item: Provenance) -> tuple[str, int, int, str]:
    return (item.document_id, item.start_char, item.end_char, item.quote)


def _validate_relationship_groundings(
    relationship: GraphRelationship,
    *,
    entities_by_id: dict[str, GraphEntity],
    known_documents: set[str],
) -> None:
    source_entity = entities_by_id[relationship.source]
    target_entity = entities_by_id[relationship.target]
    _validate_provenance_documents(
        [grounding.evidence for grounding in relationship.groundings],
        known_documents,
    )
    evidence_keys = {_provenance_key(item) for item in relationship.evidence}
    grounding_keys = {
        _provenance_key(grounding.evidence) for grounding in relationship.groundings
    }
    if evidence_keys != grounding_keys:
        raise ValueError(
            f"relationship grounding/evidence mismatch: {relationship.id}"
        )
    for grounding in relationship.groundings:
        if not predicate_supported_by_phrase(
            relationship.relationship_type,
            grounding.relation_phrase,
        ):
            raise ValueError(
                f"relationship predicate is not supported by its exact phrase: "
                f"{relationship.id}"
            )
        if not mention_identifies_entity(
            grounding.source_mention,
            source_entity.name,
        ):
            raise ValueError(
                f"source_mention does not identify {source_entity.name!r}: "
                f"{grounding.source_mention!r}"
            )
        if not mention_identifies_entity(
            grounding.target_mention,
            target_entity.name,
        ):
            raise ValueError(
                f"target_mention does not identify {target_entity.name!r}: "
                f"{grounding.target_mention!r}"
            )


def safe_predicate(value: str, *, fallback: str = "related_to") -> str:
    """Return a bounded lowercase snake_case relationship predicate."""

    predicate = re.sub(r"[^a-z0-9]+", "_", normalize_text(value)).strip("_")
    return predicate[:60] or fallback


def safe_token(value: str, *, fallback: str = "item") -> str:
    """Return a portable lowercase token for IDs and trace segments."""

    token = re.sub(r"[^a-z0-9]+", "-", normalize_text(value)).strip("-")
    return token[:60] or fallback


def _body_digest(body_text: str) -> str:
    return hashlib.sha256(body_text.encode("utf-8")).hexdigest()


def build_source_lines(text: str) -> tuple[SourceLine, ...]:
    """Map numbered prompt lines back to exact source character offsets."""

    lines: list[SourceLine] = []
    cursor = 0
    for number, raw_line in enumerate(text.splitlines(keepends=True), start=1):
        content = raw_line.rstrip("\r\n")
        lines.append(
            SourceLine(
                number=number,
                start_char=cursor,
                end_char=cursor + len(content),
            )
        )
        cursor += len(raw_line)
    if not lines:
        lines.append(SourceLine(number=1, start_char=0, end_char=len(text)))
    return tuple(lines)


def render_numbered_source(document: LoadedDocument) -> str:
    """Render the exact analysis window with stable, model-citable line labels."""

    return "\n".join(
        f"L{line.number:04d} | "
        f"{document.analysis_text[line.start_char:line.end_char]}"
        for line in document.source_lines
    )


def derive_document_id(document: RawDocument) -> str:
    """Derive a stable source identifier without depending on list position."""

    for key in DOCUMENT_NUMBER_KEYS:
        value = document.metadata.get(key)
        if value:
            return safe_token(value, fallback="document")
    if document.url:
        tail = document.url.rstrip("/").rsplit("/", 1)[-1]
        if tail:
            return safe_token(tail, fallback="document")
    digest = hashlib.sha256(f"{document.title}\0{document.body_text}".encode()).hexdigest()[:16]
    return f"document-{digest}"


def load_corpus(corpus_path: Path, *, limit: int, max_chars: int) -> list[LoadedDocument]:
    """Load, validate, sort, and select an explicit CREST corpus."""

    if limit <= 0:
        raise ValueError("limit must be positive")
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if not corpus_path.is_file():
        raise ValueError(f"corpus is not a file: {corpus_path}")

    payload = json.loads(corpus_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("documents"), list):
        raw_documents = payload["documents"]
    elif isinstance(payload, list):
        raw_documents = payload
    else:
        raise TypeError("corpus must be a list or an object with a documents list")

    parsed = [RawDocument.model_validate(item) for item in raw_documents]
    if len(parsed) < limit:
        raise ValueError(f"corpus contains {len(parsed)} documents, fewer than limit={limit}")

    corpus_label = corpus_path.as_posix()
    loaded: list[LoadedDocument] = []
    seen_ids: set[str] = set()
    for document in parsed:
        document_id = derive_document_id(document)
        if document_id in seen_ids:
            raise ValueError(f"duplicate source document ID: {document_id}")
        seen_ids.add(document_id)
        analyzed_end = min(len(document.body_text), max_chars)
        analysis_text = document.body_text[:analyzed_end]
        source_lines = build_source_lines(analysis_text)
        manifest = SourceDocument(
            document_id=document_id,
            title=document.title,
            source_url=document.url,
            corpus_path=corpus_label,
            body_sha256=_body_digest(document.body_text),
            total_chars=len(document.body_text),
            analyzed_start=0,
            analyzed_end=analyzed_end,
            analyzed_lines=len(source_lines),
        )
        loaded.append(
            LoadedDocument(
                manifest=manifest,
                metadata=document.metadata,
                analysis_text=analysis_text,
                source_lines=source_lines,
            )
        )

    loaded.sort(key=lambda item: item.manifest.document_id)
    return loaded[:limit]


def load_selected_documents(
    corpus_path: Path,
    *,
    document_ids: list[str],
    max_chars: int,
) -> list[LoadedDocument]:
    """Load an explicit document selection through the canonical source boundary."""

    if not document_ids:
        raise ValueError("at least one document ID is required")
    if len(document_ids) != len(set(document_ids)):
        raise ValueError("document IDs must be unique")
    all_documents = load_corpus(
        corpus_path,
        limit=len(_raw_corpus_items(corpus_path)),
        max_chars=max_chars,
    )
    documents_by_id = {
        document.manifest.document_id: document for document in all_documents
    }
    missing = [document_id for document_id in document_ids if document_id not in documents_by_id]
    if missing:
        raise ValueError(f"unknown document IDs: {', '.join(missing)}")
    return [documents_by_id[document_id] for document_id in document_ids]


def _raw_corpus_items(corpus_path: Path) -> list[Any]:
    """Return raw corpus items for selection without weakening load validation."""

    if not corpus_path.is_file():
        raise ValueError(f"corpus is not a file: {corpus_path}")
    payload = json.loads(corpus_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("documents"), list):
        return payload["documents"]
    if isinstance(payload, list):
        return payload
    raise TypeError("corpus must be a list or an object with a documents list")


def locate_evidence(document: LoadedDocument, evidence: EvidenceCandidate) -> Provenance:
    """Materialize a bounded model line citation as exact original source text."""

    if evidence.line_end > len(document.source_lines):
        raise ValueError(
            f"evidence line L{evidence.line_end:04d} exceeds "
            f"{document.manifest.document_id}'s {len(document.source_lines)} supplied lines"
        )
    first = document.source_lines[evidence.line_start - 1]
    last = document.source_lines[evidence.line_end - 1]
    start = first.start_char
    end = last.end_char
    quote = document.analysis_text[start:end]
    if not quote.strip():
        raise ValueError(
            f"evidence lines L{evidence.line_start:04d}-L{evidence.line_end:04d} "
            f"contain no source text in {document.manifest.document_id}"
        )
    return Provenance(
        document_id=document.manifest.document_id,
        source_url=document.manifest.source_url,
        corpus_path=document.manifest.corpus_path,
        body_sha256=document.manifest.body_sha256,
        quote=quote,
        line_start=evidence.line_start,
        line_end=evidence.line_end,
        start_char=start,
        end_char=end,
    )


def validate_extraction_grounding(
    document: LoadedDocument, extraction: DocumentExtraction
) -> None:
    """Fail immediately when any model citation cannot bind to supplied source lines."""

    entities_by_local_id = {entity.local_id: entity for entity in extraction.entities}
    for entity in extraction.entities:
        locate_evidence(document, entity.evidence)
    for relationship in extraction.relationships:
        _validate_relationship_candidate(
            document,
            relationship,
            entities_by_local_id=entities_by_local_id,
        )


def _validate_relationship_candidate(
    document: LoadedDocument,
    relationship: RelationshipCandidate,
    *,
    entities_by_local_id: dict[str, EntityCandidate],
) -> RelationshipCandidate:
    provenance = locate_evidence(document, relationship.evidence)
    grounded_relationship = relationship.model_copy(
        update={
            "source_mention": _materialize_exact_fragment(
                provenance.quote,
                relationship.source_mention,
                "source_mention",
            ),
            "relation_phrase": _materialize_exact_fragment(
                provenance.quote,
                relationship.relation_phrase,
                "relation_phrase",
            ),
            "target_mention": _materialize_exact_fragment(
                provenance.quote,
                relationship.target_mention,
                "target_mention",
            ),
        }
    )
    _validate_relationship_fragments(
        quote=provenance.quote,
        source_mention=grounded_relationship.source_mention,
        relation_phrase=grounded_relationship.relation_phrase,
        target_mention=grounded_relationship.target_mention,
    )
    if not predicate_supported_by_phrase(
        grounded_relationship.relationship_type,
        grounded_relationship.relation_phrase,
    ):
        raise ValueError(
            "relationship type is not lexically supported by relation_phrase"
        )
    source_entity = entities_by_local_id[grounded_relationship.source_entity_id]
    target_entity = entities_by_local_id[grounded_relationship.target_entity_id]
    if not mention_identifies_entity(
        grounded_relationship.source_mention,
        source_entity.name,
    ):
        raise ValueError(
            f"source_mention does not identify {source_entity.name!r}: "
            f"{grounded_relationship.source_mention!r}"
        )
    if not mention_identifies_entity(
        grounded_relationship.target_mention,
        target_entity.name,
    ):
        raise ValueError(
            f"target_mention does not identify {target_entity.name!r}: "
            f"{grounded_relationship.target_mention!r}"
        )
    return grounded_relationship


def partition_extraction_grounding(
    document: LoadedDocument,
    extraction: DocumentExtraction,
) -> tuple[DocumentExtraction, list[ExtractionRejection]]:
    """Keep grounded candidates and return explicit records for every rejection."""

    accepted_entities: list[EntityCandidate] = []
    accepted_entity_ids: set[str] = set()
    rejections: list[ExtractionRejection] = []
    for index, entity in enumerate(extraction.entities):
        try:
            locate_evidence(document, entity.evidence)
        except ValueError as exc:
            rejections.append(
                ExtractionRejection(
                    document_id=document.manifest.document_id,
                    item_kind="entity",
                    item_index=index,
                    candidate_ref=entity.local_id,
                    reason=str(exc),
                )
            )
        else:
            accepted_entities.append(entity)
            accepted_entity_ids.add(entity.local_id)

    entities_by_local_id = {
        entity.local_id: entity for entity in accepted_entities
    }
    accepted_relationships: list[RelationshipCandidate] = []
    for index, relationship in enumerate(extraction.relationships):
        candidate_ref = (
            f"{relationship.source_entity_id}:"
            f"{safe_predicate(relationship.relationship_type)}:"
            f"{relationship.target_entity_id}"
        )
        missing_endpoints = sorted(
            {
                relationship.source_entity_id,
                relationship.target_entity_id,
            }
            - accepted_entity_ids
        )
        if missing_endpoints:
            rejections.append(
                ExtractionRejection(
                    document_id=document.manifest.document_id,
                    item_kind="relationship",
                    item_index=index,
                    candidate_ref=candidate_ref,
                    reason=(
                        "relationship endpoint failed entity grounding: "
                        f"{missing_endpoints}"
                    ),
                )
            )
            continue
        try:
            grounded_relationship = _validate_relationship_candidate(
                document,
                relationship,
                entities_by_local_id=entities_by_local_id,
            )
        except ValueError as exc:
            rejections.append(
                ExtractionRejection(
                    document_id=document.manifest.document_id,
                    item_kind="relationship",
                    item_index=index,
                    candidate_ref=candidate_ref,
                    reason=str(exc),
                )
            )
        else:
            if len(accepted_relationships) >= MAX_RELATIONSHIPS_PER_DOCUMENT:
                rejections.append(
                    ExtractionRejection(
                        document_id=document.manifest.document_id,
                        item_kind="relationship",
                        item_index=index,
                        candidate_ref=candidate_ref,
                        reason=(
                            "grounded candidate exceeds emitted relationship limit of "
                            f"{MAX_RELATIONSHIPS_PER_DOCUMENT}"
                        ),
                    )
                )
            else:
                accepted_relationships.append(grounded_relationship)

    return (
        DocumentExtraction(
            entities=accepted_entities,
            relationships=accepted_relationships,
        ),
        rejections,
    )


def canonical_entity_id(entity: EntityCandidate) -> str:
    """Build a stable ID that cannot collapse entities across semantic types."""

    identity = f"{entity.entity_type.value}\0{normalize_text(entity.name)}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
    return f"{entity.entity_type.value}:{safe_token(entity.name)}:{digest}"


def _merge_attributes(target: dict[str, list[str]], additions: dict[str, str]) -> None:
    for raw_key, raw_value in additions.items():
        key = raw_key.strip()
        value = raw_value.strip()
        if not key or not value:
            continue
        values = target.setdefault(key, [])
        if value not in values:
            values.append(value)


def _append_provenance(target: list[Provenance], item: Provenance) -> None:
    key = _provenance_key(item)
    existing = {_provenance_key(entry) for entry in target}
    if key not in existing:
        target.append(item)


def _append_grounding(
    target: list[RelationshipGrounding], item: RelationshipGrounding
) -> None:
    key = (
        _provenance_key(item.evidence),
        item.source_mention,
        item.relation_phrase,
        item.target_mention,
        item.support_reasoning,
    )
    existing = {
        (
            _provenance_key(entry.evidence),
            entry.source_mention,
            entry.relation_phrase,
            entry.target_mention,
            entry.support_reasoning,
        )
        for entry in target
    }
    if key not in existing:
        target.append(item)


def build_graph(
    documents: list[LoadedDocument],
    extractions: list[DocumentExtraction],
    *,
    model: str,
    prompt_ref: str = PROMPT_REF,
    relationship_prompt_ref: str | None = None,
    relationship_model: str | None = None,
    trace_id: str,
    max_budget_usd: float,
    observed_cost_usd: float,
    prior_observed_cost_usd: float = 0.0,
    unattributed_cost_reserve_usd: float = 0.0,
    recovered_extractions: list[RecoveredExtractionReceipt] | None = None,
    rejections: list[ExtractionRejection] | None = None,
) -> GraphArtifact:
    """Merge validated per-document extractions into one integrity-checked graph."""

    if len(documents) != len(extractions):
        raise ValueError("each selected document must have exactly one extraction")

    entities_by_id: dict[str, GraphEntity] = {}
    local_id_maps: list[dict[str, str]] = []

    for document, extraction in zip(documents, extractions, strict=True):
        local_map: dict[str, str] = {}
        for entity_candidate in extraction.entities:
            entity_id = canonical_entity_id(entity_candidate)
            local_map[entity_candidate.local_id] = entity_id
            provenance = locate_evidence(document, entity_candidate.evidence)
            entity = entities_by_id.get(entity_id)
            if entity is None:
                entity = GraphEntity(
                    id=entity_id,
                    name=entity_candidate.name,
                    type=entity_candidate.entity_type,
                    attributes={},
                    evidence=[provenance],
                )
                entities_by_id[entity_id] = entity
            else:
                _append_provenance(entity.evidence, provenance)
            _merge_attributes(entity.attributes, entity_candidate.attributes)
        local_id_maps.append(local_map)

    relationships_by_key: dict[tuple[str, str, str], GraphRelationship] = {}
    for document, extraction, local_map in zip(
        documents, extractions, local_id_maps, strict=True
    ):
        for relationship_candidate in extraction.relationships:
            source = local_map[relationship_candidate.source_entity_id]
            target = local_map[relationship_candidate.target_entity_id]
            normalized_type = safe_predicate(relationship_candidate.relationship_type)
            key = (source, target, normalized_type)
            provenance = locate_evidence(document, relationship_candidate.evidence)
            grounding = RelationshipGrounding(
                evidence=provenance,
                source_mention=relationship_candidate.source_mention,
                relation_phrase=relationship_candidate.relation_phrase,
                target_mention=relationship_candidate.target_mention,
                support_reasoning=relationship_candidate.support_reasoning,
            )
            relationship = relationships_by_key.get(key)
            if relationship is None:
                digest = hashlib.sha256("\0".join(key).encode("utf-8")).hexdigest()[:12]
                relationship = GraphRelationship(
                    id=f"relationship:{digest}",
                    source=source,
                    target=target,
                    type=normalized_type,
                    attributes={},
                    evidence=[provenance],
                    groundings=[grounding],
                )
                relationships_by_key[key] = relationship
            else:
                _append_provenance(relationship.evidence, provenance)
                _append_grounding(relationship.groundings, grounding)
            _merge_attributes(relationship.attributes, relationship_candidate.attributes)

    return GraphArtifact(
        schema_version=PIPELINE_VERSION,
        generated_at=datetime.now(timezone.utc),
        model=model,
        prompt_ref=prompt_ref,
        relationship_prompt_ref=relationship_prompt_ref,
        relationship_model=relationship_model,
        trace_id=trace_id,
        max_budget_usd=max_budget_usd,
        observed_cost_usd=observed_cost_usd,
        prior_observed_cost_usd=prior_observed_cost_usd,
        unattributed_cost_reserve_usd=unattributed_cost_reserve_usd,
        recovered_extractions=recovered_extractions or [],
        documents=[document.manifest for document in documents],
        entities=sorted(entities_by_id.values(), key=lambda entity: entity.id),
        relationships=sorted(
            relationships_by_key.values(), key=lambda relationship: relationship.id
        ),
        rejections=rejections or [],
    )


def _recover_trace_payload(
    trace_id: str,
    *,
    expected_model: str,
    allowed_prompt_refs: frozenset[str],
) -> tuple[str, str, float, Any] | None:
    """Join one successful terminal response to its selected-attempt receipt."""

    from llm_client import (
        diagnose_runtime_selected_attempt_receipt_for_trace,
        lookup_result,
    )

    result = lookup_result(trace_id)
    if result is None:
        return None
    response = result.get("response")
    result_model = result.get("model")
    finish_reason = result.get("finish_reason")
    prompt_ref = result.get("prompt_ref")
    cost_value = result.get("cost")
    if not isinstance(response, str) or not response.strip():
        raise ValueError(f"recovered trace has no terminal response: {trace_id}")
    if result_model != expected_model:
        raise ValueError(
            f"recovered trace model mismatch for {trace_id}: "
            f"expected {expected_model}, found {result_model!r}"
        )
    if finish_reason != "stop":
        raise ValueError(f"recovered trace did not finish with stop: {trace_id}")
    if not isinstance(prompt_ref, str) or prompt_ref not in allowed_prompt_refs:
        raise ValueError(f"recovered trace prompt mismatch for {trace_id}: {prompt_ref!r}")
    if (
        isinstance(cost_value, bool)
        or not isinstance(cost_value, (int, float))
        or not math.isfinite(float(cost_value))
        or float(cost_value) < 0
    ):
        raise ValueError(f"recovered trace has invalid cost: {trace_id}")

    receipt = diagnose_runtime_selected_attempt_receipt_for_trace(trace_id)
    if receipt.trace_id != trace_id:
        raise ValueError(f"selected-attempt receipt trace mismatch: {trace_id}")
    if receipt.resolved_model != expected_model:
        raise ValueError(f"selected-attempt receipt model mismatch: {trace_id}")
    return response, prompt_ref, float(cost_value), receipt


def recover_extraction_from_trace(
    document: LoadedDocument,
    *,
    root_trace_id: str,
    expected_model: str,
) -> tuple[
    DocumentExtraction,
    RecoveredExtractionReceipt,
    list[ExtractionRejection],
] | None:
    """Recover and revalidate one exact successful prior document extraction."""

    document_trace_id = (
        f"{root_trace_id}/documents/{safe_token(document.manifest.document_id)}"
    )
    payload = _recover_trace_payload(
        document_trace_id,
        expected_model=expected_model,
        allowed_prompt_refs=RECOVERABLE_PROMPT_REFS,
    )
    if payload is None:
        return None
    response, prompt_ref, cost_value, receipt = payload

    try:
        extraction = DocumentExtraction.model_validate_json(response)
    except ValidationError:
        provider_extraction = ProviderDocumentExtraction.model_validate_json(response)
        extraction, recovery_rejections = validate_provider_extraction(
            document.manifest.document_id,
            provider_extraction,
        )
    else:
        recovery_rejections = []
    recovered = RecoveredExtractionReceipt(
        document_id=document.manifest.document_id,
        trace_id=document_trace_id,
        call_id=receipt.call_id,
        logical_call_id=receipt.logical_call_id,
        selected_attempt_ordinal=receipt.selected_attempt_ordinal,
        schema_hash=receipt.schema_hash,
        raw_sha256=receipt.raw_sha256,
        selected_attempt_receipt_digest=receipt.receipt_digest,
        response_sha256=hashlib.sha256(response.encode("utf-8")).hexdigest(),
        model=expected_model,
        prompt_ref=prompt_ref,
        observed_cost_usd=cost_value,
    )
    return extraction, recovered, recovery_rejections


def recover_relationship_extraction_from_trace(
    document: LoadedDocument,
    *,
    root_trace_id: str,
    expected_model: str,
) -> tuple[ProviderRelationshipExtraction, RecoveredExtractionReceipt] | None:
    """Recover one successful relationship-refinement response and its receipt."""

    document_trace_id = (
        f"{root_trace_id}/relationship-refinement/documents/"
        f"{safe_token(document.manifest.document_id)}"
    )
    payload = _recover_trace_payload(
        document_trace_id,
        expected_model=expected_model,
        allowed_prompt_refs=frozenset({RELATIONSHIP_PROMPT_REF}),
    )
    if payload is None:
        return None
    response, prompt_ref, cost_value, receipt = payload
    extraction = ProviderRelationshipExtraction.model_validate_json(response)
    recovered = RecoveredExtractionReceipt(
        stage="relationship_refinement",
        document_id=document.manifest.document_id,
        trace_id=document_trace_id,
        call_id=receipt.call_id,
        logical_call_id=receipt.logical_call_id,
        selected_attempt_ordinal=receipt.selected_attempt_ordinal,
        schema_hash=receipt.schema_hash,
        raw_sha256=receipt.raw_sha256,
        selected_attempt_receipt_digest=receipt.receipt_digest,
        response_sha256=hashlib.sha256(response.encode("utf-8")).hexdigest(),
        model=expected_model,
        prompt_ref=prompt_ref,
        observed_cost_usd=cost_value,
    )
    return extraction, recovered


def run_extraction(
    documents: list[LoadedDocument],
    *,
    model_override: str | None,
    model_justification_override: str | None,
    relationship_model_override: str | None = None,
    relationship_model_justification_override: str | None = None,
    trace_id: str,
    max_budget_usd: float,
    resume_trace_ids: list[str] | None = None,
    resume_relationship_trace_ids: list[str] | None = None,
    prior_observed_cost_usd: float = 0.0,
    unattributed_cost_reserve_usd: float = 0.0,
    max_output_tokens: int = 3_500,
    refine_relationships: bool = False,
    relationship_max_output_tokens: int = 2_000,
    reasoning_effort: str | None = None,
    structured_retries: int = 0,
) -> GraphArtifact:
    """Execute one fully traced structured extraction per selected document."""

    from llm_client import call_llm_structured, get_model, render_prompt

    model = model_override or get_model("graph_building", use_performance=False)
    if model_override:
        model_justification = (model_justification_override or "").strip()
        if not model_justification:
            raise ValueError("--model requires --model-justification")
    else:
        model_justification = (
            "Resolved through llm_client get_model('graph_building', "
            "use_performance=False) for structured CREST graph extraction."
        )
    relationship_model = relationship_model_override or model
    if relationship_model_override:
        relationship_model_justification = (
            relationship_model_justification_override or ""
        ).strip()
        if not relationship_model_justification:
            raise ValueError(
                "--relationship-model requires --relationship-model-justification"
            )
    else:
        relationship_model_justification = model_justification
    if relationship_model_override and not refine_relationships:
        raise ValueError("--relationship-model requires --refine-relationships")
    if resume_relationship_trace_ids and not refine_relationships:
        raise ValueError(
            "relationship resume traces require --refine-relationships"
        )
    if not math.isfinite(prior_observed_cost_usd) or prior_observed_cost_usd < 0:
        raise ValueError("prior observed cost must be a finite nonnegative value")
    if (
        not math.isfinite(unattributed_cost_reserve_usd)
        or unattributed_cost_reserve_usd < 0
    ):
        raise ValueError("unattributed cost reserve must be a finite nonnegative value")
    if max_output_tokens <= 0:
        raise ValueError("max output tokens must be greater than zero")
    if relationship_max_output_tokens <= 0:
        raise ValueError("relationship max output tokens must be greater than zero")
    if structured_retries < 0:
        raise ValueError("structured retries must be nonnegative")

    resume_roots = list(dict.fromkeys(resume_trace_ids or []))
    if any(not root.strip() for root in resume_roots):
        raise ValueError("resume trace IDs must be nonblank")
    if trace_id in resume_roots:
        raise ValueError("the new trace ID must differ from every resume trace ID")
    relationship_resume_roots = list(
        dict.fromkeys(resume_relationship_trace_ids or [])
    )
    if any(not root.strip() for root in relationship_resume_roots):
        raise ValueError("relationship resume trace IDs must be nonblank")
    if trace_id in relationship_resume_roots:
        raise ValueError(
            "the new trace ID must differ from every relationship resume trace ID"
        )

    recovered_by_document: dict[
        str,
        tuple[
            DocumentExtraction,
            RecoveredExtractionReceipt,
            list[ExtractionRejection],
        ],
    ] = {}
    for document in documents:
        for resume_root in reversed(resume_roots):
            recovered = recover_extraction_from_trace(
                document,
                root_trace_id=resume_root,
                expected_model=model,
            )
            if recovered is not None:
                recovered_by_document[document.manifest.document_id] = recovered
                break

    recovered_relationships_by_document: dict[
        str,
        tuple[ProviderRelationshipExtraction, RecoveredExtractionReceipt],
    ] = {}
    if refine_relationships:
        for document in documents:
            for resume_root in reversed(relationship_resume_roots):
                recovered_relationship = (
                    recover_relationship_extraction_from_trace(
                        document,
                        root_trace_id=resume_root,
                        expected_model=relationship_model,
                    )
                )
                if recovered_relationship is not None:
                    recovered_relationships_by_document[
                        document.manifest.document_id
                    ] = recovered_relationship
                    break

    recovered_receipts = [
        recovered_by_document[document.manifest.document_id][1]
        for document in documents
        if document.manifest.document_id in recovered_by_document
    ]
    recovered_receipts.extend(
        recovered_relationships_by_document[document.manifest.document_id][1]
        for document in documents
        if document.manifest.document_id in recovered_relationships_by_document
    )
    recovered_cost = sum(receipt.observed_cost_usd for receipt in recovered_receipts)
    authorized_new_call_budget = (
        max_budget_usd
        - prior_observed_cost_usd
        - unattributed_cost_reserve_usd
        - recovered_cost
    )
    missing_document_count = len(documents) - len(recovered_by_document)
    missing_relationship_count = (
        len(documents) - len(recovered_relationships_by_document)
        if refine_relationships
        else 0
    )
    if (
        missing_document_count or missing_relationship_count
    ) and authorized_new_call_budget <= 0:
        raise ValueError("no authorized budget remains for new model calls")

    extractions: list[DocumentExtraction] = []
    rejections: list[ExtractionRejection] = []
    observed_cost = recovered_cost

    for document in documents:
        recovered = recovered_by_document.get(document.manifest.document_id)
        if recovered is not None:
            validated = DocumentExtraction.model_validate(
                recovered[0].model_dump(by_alias=True)
            )
            schema_rejections = recovered[2]
            result = None
        else:
            messages = render_prompt(
                PROMPT_PATH,
                document_id=document.manifest.document_id,
                title=document.manifest.title,
                source_url=document.manifest.source_url or "",
                metadata_json=json.dumps(
                    document.metadata, ensure_ascii=False, sort_keys=True
                ),
                numbered_body_text=render_numbered_source(document),
            )
            provider_extraction, result = call_llm_structured(
                model,
                messages,
                response_model=ProviderDocumentExtraction,
                task="crest_kg.entity_relationship_extraction",
                trace_id=(
                    f"{trace_id}/documents/"
                    f"{safe_token(document.manifest.document_id)}"
                ),
                budget_scope_trace_id=trace_id,
                max_budget=authorized_new_call_budget,
                max_tokens=max_output_tokens,
                num_retries=structured_retries,
                reasoning_effort=reasoning_effort,
                model_policy="enforce_allowlist",
                model_justification=model_justification,
                prompt_ref=PROMPT_REF,
            )
            validated, schema_rejections = validate_provider_extraction(
                document.manifest.document_id,
                provider_extraction,
            )
        grounded, document_rejections = partition_extraction_grounding(
            document,
            validated,
        )
        rejections.extend(schema_rejections)
        rejections.extend(document_rejections)
        if result is not None:
            observed_cost += float(result.cost or 0.0)

        if not refine_relationships or not grounded.entities:
            extractions.append(grounded)
            continue

        recovered_relationship = recovered_relationships_by_document.get(
            document.manifest.document_id
        )
        if recovered_relationship is not None:
            provider_relationships = recovered_relationship[0]
            relationship_result = None
        else:
            relationship_messages = render_prompt(
                RELATIONSHIP_PROMPT_PATH,
                document_id=document.manifest.document_id,
                eligible_entities_json=json.dumps(
                    [
                        {
                            "local_id": entity.local_id,
                            "name": entity.name,
                            "type": entity.entity_type.value,
                        }
                        for entity in grounded.entities
                    ],
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                numbered_body_text=render_numbered_source(document),
            )
            provider_relationships, relationship_result = call_llm_structured(
                relationship_model,
                relationship_messages,
                response_model=ProviderRelationshipExtraction,
                task="crest_kg.relationship_refinement",
                trace_id=(
                    f"{trace_id}/relationship-refinement/documents/"
                    f"{safe_token(document.manifest.document_id)}"
                ),
                budget_scope_trace_id=trace_id,
                max_budget=authorized_new_call_budget,
                max_tokens=relationship_max_output_tokens,
                num_retries=structured_retries,
                reasoning_effort=reasoning_effort,
                model_policy="enforce_allowlist",
                model_justification=relationship_model_justification,
                prompt_ref=RELATIONSHIP_PROMPT_REF,
            )
        refined, refinement_schema_rejections = (
            validate_provider_relationship_extraction(
                document.manifest.document_id,
                provider_relationships,
                grounded.entities,
            )
        )
        refined_grounded, refinement_grounding_rejections = (
            partition_extraction_grounding(document, refined)
        )
        extractions.append(refined_grounded)
        rejections.extend(refinement_schema_rejections)
        rejections.extend(refinement_grounding_rejections)
        if relationship_result is not None:
            observed_cost += float(relationship_result.cost or 0.0)

    return build_graph(
        documents,
        extractions,
        model=model,
        relationship_prompt_ref=(
            RELATIONSHIP_PROMPT_REF if refine_relationships else None
        ),
        relationship_model=relationship_model if refine_relationships else None,
        trace_id=trace_id,
        max_budget_usd=max_budget_usd,
        observed_cost_usd=observed_cost,
        prior_observed_cost_usd=prior_observed_cost_usd,
        unattributed_cost_reserve_usd=unattributed_cost_reserve_usd,
        recovered_extractions=recovered_receipts,
        rejections=rejections,
    )


def write_graph(graph: GraphArtifact, output_path: Path, *, force: bool) -> None:
    """Atomically write a graph, refusing silent overwrite."""

    if output_path.exists() and not force:
        raise ValueError(f"output already exists; pass --force to replace it: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialized = graph.model_dump_json(by_alias=True, indent=2) + "\n"
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, output_path)
    except Exception:
        if temp_name:
            Path(temp_name).unlink(missing_ok=True)
        raise


def validate_graph_file(graph_path: Path) -> GraphArtifact:
    """Load and validate a graph artifact against the full contract."""

    return GraphArtifact.model_validate_json(graph_path.read_text(encoding="utf-8"))


def _positive_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def _nonnegative_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0:
        raise argparse.ArgumentTypeError("value must be a finite nonnegative number")
    return parsed


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_corpus_arguments(command: argparse.ArgumentParser) -> None:
        command.add_argument("--corpus", type=Path, required=True)
        command.add_argument("--limit", type=_positive_int, default=5)
        command.add_argument("--max-chars", type=_positive_int, default=15_000)

    inspect_parser = subparsers.add_parser(
        "inspect-corpus", help="Show the exact deterministic source selection without an LLM call."
    )
    add_corpus_arguments(inspect_parser)

    extract_parser = subparsers.add_parser(
        "extract", help="Run traced structured extraction and write a validated graph."
    )
    add_corpus_arguments(extract_parser)
    extract_parser.add_argument("--output", type=Path, required=True)
    extract_parser.add_argument(
        "--max-budget-usd",
        type=_positive_float,
        required=True,
        help="Explicit total dollar ceiling shared by all document calls.",
    )
    extract_parser.add_argument("--model", help="Optional model override; defaults to graph_building.")
    extract_parser.add_argument(
        "--model-justification",
        help="Required rationale when --model overrides the graph_building registry route.",
    )
    extract_parser.add_argument(
        "--relationship-model",
        help="Optional model override for the dedicated relationship-only pass.",
    )
    extract_parser.add_argument(
        "--relationship-model-justification",
        help="Required rationale when --relationship-model is supplied.",
    )
    extract_parser.add_argument("--trace-id", help="Optional root trace ID.")
    extract_parser.add_argument(
        "--resume-trace-id",
        action="append",
        default=[],
        help="Prior root trace to search for reusable successful document calls; repeatable.",
    )
    extract_parser.add_argument(
        "--resume-relationship-trace-id",
        action="append",
        default=[],
        help="Prior root trace to search for reusable relationship-stage calls; repeatable.",
    )
    extract_parser.add_argument(
        "--prior-observed-cost-usd",
        type=_nonnegative_float,
        default=0.0,
        help="Known earlier spend charged against the total authorization.",
    )
    extract_parser.add_argument(
        "--unattributed-cost-reserve-usd",
        type=_nonnegative_float,
        default=0.0,
        help="Conservative reserve for interrupted provider work without a terminal cost row.",
    )
    extract_parser.add_argument(
        "--max-output-tokens",
        type=_positive_int,
        default=3_500,
        help="Per-document structured response token ceiling.",
    )
    extract_parser.add_argument(
        "--refine-relationships",
        action="store_true",
        help="Run a dedicated relationship-only pass over the extracted entity set.",
    )
    extract_parser.add_argument(
        "--relationship-max-output-tokens",
        type=_positive_int,
        default=2_000,
        help="Per-document token ceiling for the optional relationship-only pass.",
    )
    extract_parser.add_argument(
        "--reasoning-effort",
        help="Explicit llm_client reasoning setting when the selected model requires one.",
    )
    extract_parser.add_argument("--force", action="store_true")

    validate_parser = subparsers.add_parser(
        "validate", help="Validate a generated graph and print its integrity counts."
    )
    validate_parser.add_argument("--graph", type=Path, required=True)
    return parser


def _default_trace_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"crest_kg/extraction/{timestamp}"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect-corpus":
            documents = load_corpus(args.corpus, limit=args.limit, max_chars=args.max_chars)
            print(
                json.dumps(
                    [document.manifest.model_dump(mode="json") for document in documents],
                    indent=2,
                )
            )
            return 0

        if args.command == "extract":
            documents = load_corpus(args.corpus, limit=args.limit, max_chars=args.max_chars)
            graph = run_extraction(
                documents,
                model_override=args.model,
                model_justification_override=args.model_justification,
                relationship_model_override=args.relationship_model,
                relationship_model_justification_override=(
                    args.relationship_model_justification
                ),
                trace_id=args.trace_id or _default_trace_id(),
                max_budget_usd=args.max_budget_usd,
                resume_trace_ids=args.resume_trace_id,
                resume_relationship_trace_ids=args.resume_relationship_trace_id,
                prior_observed_cost_usd=args.prior_observed_cost_usd,
                unattributed_cost_reserve_usd=args.unattributed_cost_reserve_usd,
                max_output_tokens=args.max_output_tokens,
                refine_relationships=args.refine_relationships,
                relationship_max_output_tokens=args.relationship_max_output_tokens,
                reasoning_effort=args.reasoning_effort,
            )
            write_graph(graph, args.output, force=args.force)
            print(
                f"wrote {args.output}: {len(graph.documents)} documents, "
                f"{len(graph.entities)} entities, {len(graph.relationships)} relationships, "
                f"observed_cost=${graph.observed_cost_usd:.6f}, "
                f"accounted_total=${graph.observed_cost_usd + graph.prior_observed_cost_usd + graph.unattributed_cost_reserve_usd:.6f}"
            )
            return 0

        graph = validate_graph_file(args.graph)
        print(
            f"valid {graph.schema_version}: {len(graph.documents)} documents, "
            f"{len(graph.entities)} entities, {len(graph.relationships)} relationships; "
            "duplicate_ids=0 dangling_relationships=0 ungrounded_relationships=0"
        )
        return 0
    except (OSError, ValueError, json.JSONDecodeError, ValidationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
