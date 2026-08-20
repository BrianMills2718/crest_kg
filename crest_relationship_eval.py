#!/usr/bin/env python3
"""Evaluate a frozen, source-grounded audit of CREST graph relationships.

The quality set is deliberately separate from the extraction artifact.  It is
an output-conditioned census for estimating assertion precision and fidelity;
it is not a source-first recall denominator.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from crest_pipeline import GraphArtifact, GraphRelationship

QUALITY_SET_PATH = Path(__file__).with_name("evaluation") / "relationship_quality_set_v1.json"
GRAPH_PATH = Path(__file__).with_name("cia_kg_output") / "validated_5_documents.json"


class StrictModel(BaseModel):
    """Base model for evaluation artifacts that must reject schema drift."""

    model_config = ConfigDict(extra="forbid")


class SupportLabel(str, Enum):
    """Whether the cited quote semantically supports the asserted edge."""

    SUPPORTED = "supported"
    PARTIAL = "partially_supported"
    UNSUPPORTED = "unsupported"
    INDETERMINATE = "indeterminate"


class FidelityVerdict(str, Enum):
    """A review verdict for one independently inspectable edge dimension."""

    PASS = "pass"
    FAIL = "fail"
    UNCLEAR = "unclear"


class RelationshipAdjudication(StrictModel):
    """One reviewer-authored judgment over an emitted relationship."""

    relationship_id: str = Field(pattern=r"^relationship:[0-9a-f]{12}$")
    assertion_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    support: SupportLabel
    endpoint_fidelity: FidelityVerdict
    predicate_fidelity: FidelityVerdict
    direction_fidelity: FidelityVerdict
    type_fidelity: FidelityVerdict
    rationale: str = Field(min_length=12)
    suggested_relation: str | None = None

    @field_validator("rationale", "suggested_relation")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_judgment_consistency(self) -> Self:
        dimensions = (
            self.endpoint_fidelity,
            self.predicate_fidelity,
            self.direction_fidelity,
            self.type_fidelity,
        )
        if self.support in {SupportLabel.PARTIAL, SupportLabel.UNSUPPORTED} and all(
            verdict is FidelityVerdict.PASS for verdict in dimensions
        ):
            raise ValueError("non-supported cases must expose at least one fidelity defect")
        return self


class DecisionRule(StrictModel):
    """Precommitted threshold for deciding whether the artifact can scale."""

    min_fully_supported_rate: float = Field(ge=0.0, le=1.0)
    max_unsupported_relationships: int = Field(ge=0)
    require_all_corruption_controls: Literal[True] = True


class RelationshipQualitySet(StrictModel):
    """Frozen audit metadata and a census of adjudicated emitted edges."""

    schema_version: Literal["grounded-relationship-audit-v1"]
    quality_set_id: str = Field(min_length=1)
    artifact_path: str = Field(min_length=1)
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selection_mode: Literal["census_of_emitted_relationships"]
    adjudication_method: Literal["agent_review_of_exact_evidence_quote"]
    adjudicator: str = Field(min_length=1)
    adjudicated_at: datetime
    candidate_visible_to_adjudicator: Literal[True]
    output_conditioned: Literal[True]
    corpus_recall_claimed: Literal[False]
    decision_rule: DecisionRule
    cases: tuple[RelationshipAdjudication, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_cases(self) -> Self:
        ids = [case.relationship_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("quality-set relationship IDs must be unique")
        return self


class DocumentQualitySummary(StrictModel):
    """Audit counts for one source document."""

    relationship_count: int = Field(ge=0)
    supported_count: int = Field(ge=0)
    partially_supported_count: int = Field(ge=0)
    unsupported_count: int = Field(ge=0)
    indeterminate_count: int = Field(ge=0)
    fully_supported_count: int = Field(ge=0)
    fully_supported_rate: float = Field(ge=0.0, le=1.0)


class RelationshipQualityReport(StrictModel):
    """Deterministic readout over one frozen relationship-quality set."""

    schema_version: Literal["grounded-relationship-audit-report-v1"]
    quality_set_id: str
    graph_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    relationship_count: int = Field(ge=0)
    support_counts: dict[str, int]
    fully_supported_count: int = Field(ge=0)
    fully_supported_rate: float = Field(ge=0.0, le=1.0)
    dimension_pass_rates: dict[str, float]
    unsupported_relationship_ids: tuple[str, ...]
    partially_supported_relationship_ids: tuple[str, ...]
    indeterminate_relationship_ids: tuple[str, ...]
    by_document: dict[str, DocumentQualitySummary]
    corruption_controls: dict[str, bool]
    decision_rule: DecisionRule
    passed: bool
    licensed_claim: str
    non_claims: tuple[str, ...]


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of exact file bytes."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def relationship_fingerprint(
    graph: GraphArtifact,
    relationship: GraphRelationship,
) -> str:
    """Bind an adjudication to its exact endpoints, types, predicate, and evidence."""

    entities = {entity.id: entity for entity in graph.entities}
    source = entities[relationship.source]
    target = entities[relationship.target]
    payload = {
        "source": {
            "id": source.id,
            "name": source.name,
            "type": source.entity_type.value,
        },
        "predicate": relationship.relationship_type,
        "target": {
            "id": target.id,
            "name": target.name,
            "type": target.entity_type.value,
        },
        "attributes": relationship.attributes,
        "evidence": [item.model_dump(mode="json") for item in relationship.evidence],
    }
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def load_graph(path: Path) -> GraphArtifact:
    """Load a strict CREST graph artifact."""

    return GraphArtifact.model_validate_json(path.read_text(encoding="utf-8"))


def load_quality_set(path: Path) -> RelationshipQualitySet:
    """Load the frozen relationship audit."""

    return RelationshipQualitySet.model_validate_json(path.read_text(encoding="utf-8"))


def _validate_binding(
    graph: GraphArtifact,
    quality_set: RelationshipQualitySet,
    *,
    graph_sha256: str,
) -> dict[str, RelationshipAdjudication]:
    if graph_sha256 != quality_set.artifact_sha256:
        raise ValueError(
            "graph artifact SHA-256 does not match the frozen adjudication: "
            f"expected {quality_set.artifact_sha256}, observed {graph_sha256}"
        )

    relationships = {relationship.id: relationship for relationship in graph.relationships}
    cases = {case.relationship_id: case for case in quality_set.cases}
    missing_labels = sorted(set(relationships) - set(cases))
    unknown_labels = sorted(set(cases) - set(relationships))
    if missing_labels or unknown_labels:
        raise ValueError(
            "quality-set census does not match graph relationships; "
            f"missing_labels={missing_labels}, unknown_labels={unknown_labels}"
        )

    drifted = [
        relationship_id
        for relationship_id, case in cases.items()
        if relationship_fingerprint(graph, relationships[relationship_id])
        != case.assertion_sha256
    ]
    if drifted:
        raise ValueError(f"adjudicated relationship content drifted: {sorted(drifted)}")
    return cases


def _is_fully_supported(case: RelationshipAdjudication) -> bool:
    return case.support is SupportLabel.SUPPORTED and all(
        verdict is FidelityVerdict.PASS
        for verdict in (
            case.endpoint_fidelity,
            case.predicate_fidelity,
            case.direction_fidelity,
            case.type_fidelity,
        )
    )


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _run_corruption_controls(
    graph: GraphArtifact,
    quality_set: RelationshipQualitySet,
    *,
    graph_sha256: str,
) -> dict[str, bool]:
    """Prove that the deterministic binding rejects known-bad mutations."""

    controls: dict[str, bool] = {}

    missing_graph = graph.model_copy(deep=True)
    missing_graph.relationships.pop()
    try:
        _validate_binding(missing_graph, quality_set, graph_sha256=graph_sha256)
    except ValueError as exc:
        controls["missing_relationship"] = "census does not match" in str(exc)
    else:
        controls["missing_relationship"] = False

    mutated_graph = graph.model_copy(deep=True)
    first = mutated_graph.relationships[0]
    first.relationship_type = f"corrupted-{first.relationship_type}"
    try:
        _validate_binding(mutated_graph, quality_set, graph_sha256=graph_sha256)
    except ValueError as exc:
        controls["predicate_mutation"] = "content drifted" in str(exc)
    else:
        controls["predicate_mutation"] = False

    unknown_payload = quality_set.model_dump(mode="json")
    unknown_payload["cases"] = copy.deepcopy(unknown_payload["cases"])
    unknown_payload["cases"][0]["relationship_id"] = "relationship:ffffffffffff"
    unknown_set = RelationshipQualitySet.model_validate(unknown_payload)
    try:
        _validate_binding(graph, unknown_set, graph_sha256=graph_sha256)
    except ValueError as exc:
        controls["unknown_relationship"] = "census does not match" in str(exc)
    else:
        controls["unknown_relationship"] = False

    duplicate_payload = quality_set.model_dump(mode="json")
    duplicate_payload["cases"].append(copy.deepcopy(duplicate_payload["cases"][0]))
    try:
        RelationshipQualitySet.model_validate(duplicate_payload)
    except ValueError as exc:
        controls["duplicate_adjudication"] = "must be unique" in str(exc)
    else:
        controls["duplicate_adjudication"] = False

    return controls


def evaluate_relationship_quality(
    graph: GraphArtifact,
    quality_set: RelationshipQualitySet,
    *,
    graph_sha256: str,
) -> RelationshipQualityReport:
    """Validate the frozen census and compute semantic-fidelity metrics."""

    cases = _validate_binding(graph, quality_set, graph_sha256=graph_sha256)
    support_counts = Counter(case.support.value for case in quality_set.cases)
    fully_supported = [case for case in quality_set.cases if _is_fully_supported(case)]

    dimensions = {
        "endpoint_fidelity": [case.endpoint_fidelity for case in quality_set.cases],
        "predicate_fidelity": [case.predicate_fidelity for case in quality_set.cases],
        "direction_fidelity": [case.direction_fidelity for case in quality_set.cases],
        "type_fidelity": [case.type_fidelity for case in quality_set.cases],
    }
    dimension_pass_rates = {
        name: _rate(
            sum(verdict is FidelityVerdict.PASS for verdict in verdicts),
            len(verdicts),
        )
        for name, verdicts in dimensions.items()
    }

    per_document_cases: dict[str, list[RelationshipAdjudication]] = defaultdict(list)
    for relationship in graph.relationships:
        document_ids = {item.document_id for item in relationship.evidence}
        for document_id in document_ids:
            per_document_cases[document_id].append(cases[relationship.id])

    by_document: dict[str, DocumentQualitySummary] = {}
    for document_id, document_cases in sorted(per_document_cases.items()):
        counts = Counter(case.support.value for case in document_cases)
        document_fully_supported = sum(_is_fully_supported(case) for case in document_cases)
        by_document[document_id] = DocumentQualitySummary(
            relationship_count=len(document_cases),
            supported_count=counts[SupportLabel.SUPPORTED.value],
            partially_supported_count=counts[SupportLabel.PARTIAL.value],
            unsupported_count=counts[SupportLabel.UNSUPPORTED.value],
            indeterminate_count=counts[SupportLabel.INDETERMINATE.value],
            fully_supported_count=document_fully_supported,
            fully_supported_rate=_rate(document_fully_supported, len(document_cases)),
        )

    controls = _run_corruption_controls(
        graph,
        quality_set,
        graph_sha256=graph_sha256,
    )
    fully_supported_rate = _rate(len(fully_supported), len(quality_set.cases))
    unsupported_ids = tuple(
        sorted(
            case.relationship_id
            for case in quality_set.cases
            if case.support is SupportLabel.UNSUPPORTED
        )
    )
    partial_ids = tuple(
        sorted(
            case.relationship_id
            for case in quality_set.cases
            if case.support is SupportLabel.PARTIAL
        )
    )
    indeterminate_ids = tuple(
        sorted(
            case.relationship_id
            for case in quality_set.cases
            if case.support is SupportLabel.INDETERMINATE
        )
    )
    rule = quality_set.decision_rule
    passed = (
        fully_supported_rate >= rule.min_fully_supported_rate
        and len(unsupported_ids) <= rule.max_unsupported_relationships
        and (all(controls.values()) if rule.require_all_corruption_controls else True)
    )
    return RelationshipQualityReport(
        schema_version="grounded-relationship-audit-report-v1",
        quality_set_id=quality_set.quality_set_id,
        graph_sha256=graph_sha256,
        relationship_count=len(quality_set.cases),
        support_counts=dict(sorted(support_counts.items())),
        fully_supported_count=len(fully_supported),
        fully_supported_rate=fully_supported_rate,
        dimension_pass_rates=dimension_pass_rates,
        unsupported_relationship_ids=unsupported_ids,
        partially_supported_relationship_ids=partial_ids,
        indeterminate_relationship_ids=indeterminate_ids,
        by_document=by_document,
        corruption_controls=controls,
        decision_rule=rule,
        passed=passed,
        licensed_claim=(
            "Semantic precision and fidelity of the 79 relationships emitted in the "
            "frozen five-document CREST artifact, as adjudicated from their exact quotes."
        ),
        non_claims=(
            "This output-conditioned census does not measure corpus relationship recall.",
            "Agent adjudication is not human or independent expert review.",
            "The five selected documents do not establish quality on the wider CREST corpus.",
        ),
    )


def evaluate_paths(graph_path: Path, quality_set_path: Path) -> RelationshipQualityReport:
    """Load, bind, and evaluate artifact paths."""

    graph_sha256 = sha256_file(graph_path)
    return evaluate_relationship_quality(
        load_graph(graph_path),
        load_quality_set(quality_set_path),
        graph_sha256=graph_sha256,
    )


def _write_report(path: Path, report: RelationshipQualityReport, *, force: bool) -> None:
    if path.exists() and not force:
        raise ValueError(f"output already exists; pass --force to replace it: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = report.model_dump_json(indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary_path = Path(handle.name)
        handle.write(rendered)
        handle.flush()
    temporary_path.replace(path)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the frozen CREST relationship audit."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, default=GRAPH_PATH)
    parser.add_argument("--quality-set", type=Path, default=QUALITY_SET_PATH)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--fail-on-threshold",
        action="store_true",
        help="Return exit status 1 when the precommitted quality decision fails.",
    )
    args = parser.parse_args(argv)
    try:
        report = evaluate_paths(args.graph, args.quality_set)
        if args.out is not None:
            _write_report(args.out, report, force=args.force)
        print(report.model_dump_json(indent=2))
    except (OSError, ValueError, TypeError) as exc:
        print(f"relationship quality evaluation failed: {exc}", file=sys.stderr)
        return 2
    if args.fail_on_threshold and not report.passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
