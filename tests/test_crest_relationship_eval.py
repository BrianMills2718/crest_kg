from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from crest_relationship_eval import (
    GRAPH_PATH,
    QUALITY_SET_PATH,
    RelationshipQualitySet,
    evaluate_paths,
    evaluate_relationship_quality,
    load_graph,
    load_quality_set,
    sha256_file,
)

V2_GRAPH_PATH = (
    Path(__file__).parents[1]
    / "cia_kg_output"
    / "validated_5_documents_relationship_binding_v2.json"
)
V2_QUALITY_SET_PATH = (
    Path(__file__).parents[1] / "evaluation" / "relationship_quality_set_v2.json"
)


def test_frozen_quality_set_is_complete_and_honest() -> None:
    graph = load_graph(GRAPH_PATH)
    quality_set = load_quality_set(QUALITY_SET_PATH)

    assert len(quality_set.cases) == len(graph.relationships) == 79
    assert len({case.relationship_id for case in quality_set.cases}) == 79
    assert quality_set.output_conditioned is True
    assert quality_set.corpus_recall_claimed is False
    assert quality_set.artifact_sha256 == sha256_file(GRAPH_PATH)


def test_frozen_quality_report_runs_controls_and_exposes_failed_gate() -> None:
    report = evaluate_paths(GRAPH_PATH, QUALITY_SET_PATH)

    assert report.relationship_count == 79
    assert sum(report.support_counts.values()) == 79
    assert report.fully_supported_count < 79
    assert report.unsupported_relationship_ids
    assert report.corruption_controls and all(report.corruption_controls.values())
    assert report.passed is False
    assert any("does not measure corpus relationship recall" in item for item in report.non_claims)


def test_v2_agent_census_mechanically_meets_fixed_artifact_threshold() -> None:
    graph = load_graph(V2_GRAPH_PATH)
    quality_set = load_quality_set(V2_QUALITY_SET_PATH)
    report = evaluate_paths(V2_GRAPH_PATH, V2_QUALITY_SET_PATH)

    assert len(graph.relationships) == len(quality_set.cases) == 3
    assert report.fully_supported_count == 3
    assert report.fully_supported_rate == 1.0
    assert report.unsupported_relationship_ids == ()
    assert report.corruption_controls and all(report.corruption_controls.values())
    assert report.passed is True
    assert any(
        "does not measure corpus relationship recall" in item
        for item in report.non_claims
    )


def test_relationship_mutation_is_rejected_even_with_original_file_digest() -> None:
    graph = load_graph(GRAPH_PATH)
    quality_set = load_quality_set(QUALITY_SET_PATH)
    graph.relationships[0].relationship_type = "corrupted-predicate"

    with pytest.raises(ValueError, match="content drifted"):
        evaluate_relationship_quality(
            graph,
            quality_set,
            graph_sha256=quality_set.artifact_sha256,
        )


def test_duplicate_adjudication_is_rejected() -> None:
    payload = load_quality_set(QUALITY_SET_PATH).model_dump(mode="json")
    payload["cases"].append(copy.deepcopy(payload["cases"][0]))

    with pytest.raises(ValidationError, match="must be unique"):
        RelationshipQualitySet.model_validate(payload)


def test_graph_digest_drift_is_rejected(tmp_path: Path) -> None:
    graph_path = tmp_path / "graph.json"
    graph_path.write_bytes(GRAPH_PATH.read_bytes() + b"\n")

    with pytest.raises(ValueError, match="SHA-256 does not match"):
        evaluate_paths(graph_path, QUALITY_SET_PATH)


def test_cli_can_enforce_failed_quality_threshold() -> None:
    completed = subprocess.run(
        [sys.executable, "crest_relationship_eval.py", "--fail-on-threshold"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert json.loads(completed.stdout)["passed"] is False
    assert completed.stderr == ""
