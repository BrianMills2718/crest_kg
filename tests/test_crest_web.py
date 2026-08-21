from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
GRAPH_PATH = ROOT / "cia_kg_output" / "validated_5_documents_relationship_binding_v2.json"
WEB_ROOT = ROOT / "web"


def test_hosted_viewer_uses_the_canonical_audited_graph() -> None:
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
    connected_ids = {
        endpoint
        for relationship in graph["relationships"]
        for endpoint in (relationship["source"], relationship["target"])
    }

    assert graph["schema_version"] == "crest-kg-v2"
    assert len(graph["documents"]) == 5
    assert len(graph["entities"]) == 82
    assert len(graph["relationships"]) == 3
    assert len(graph["rejections"]) == 72
    assert len(connected_ids) == 5
    assert all(relationship["groundings"] for relationship in graph["relationships"])


def test_hosted_viewer_exposes_evidence_and_limitations() -> None:
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    javascript = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    assert "Exploratory checkpoint" in html
    assert "corpus recall is unknown" in html
    assert "Trace a claim back to its source" in html
    assert 'href="./data/graph.json"' in html
    assert 'role="img"' in html
    assert 'aria-live="polite"' in html
    assert "relationship.groundings" in javascript
    assert "source_mention" in javascript
    assert "relation_phrase" in javascript
    assert "target_mention" in javascript
    assert "No accepted relationships in this checkpoint" in javascript


def test_hosted_viewer_is_self_contained_and_fails_visible() -> None:
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    javascript = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
    css = (WEB_ROOT / "styles.css").read_text(encoding="utf-8")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    nginx = (WEB_ROOT / "nginx.conf").read_text(encoding="utf-8")

    assert "cdnjs" not in html + javascript + css
    assert "Graph request failed" in javascript
    assert "has a missing endpoint" in javascript
    assert "has no exact grounding" in javascript
    assert "validated_5_documents_relationship_binding_v2.json" in dockerfile
    assert "127.0.0.1:8080/health" in dockerfile
    assert '"service":"crest-kg-viewer"' in nginx
    assert "try_files $uri $uri/ =404;" in nginx
