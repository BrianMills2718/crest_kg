from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parents[1]
WEB_ROOT = ROOT / "web"


def test_workbench_leads_with_the_search_to_graph_workflow() -> None:
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    assert "CREST research workbench" in html
    assert "Search the archive" in html
    assert "Build knowledge graph" in html
    assert "Evidence" in html
    assert "Export JSON" in html
    assert "five-document graph is a labeled example checkpoint" in html
    assert 'role="img"' in html
    assert 'aria-live="polite"' in html


def test_workbench_actions_have_api_counterparts_and_fail_visible() -> None:
    javascript = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    for route in (
        'api("capabilities"',
        'api("search"',
        "api(`documents/",
        'api("graphs"',
        "api(`jobs/",
        "api(`graphs/",
    ):
        assert route in javascript
    assert "Search failed:" in javascript
    assert "Build failed:" in javascript
    assert "Graph request failed:" in javascript
    assert "relationship.groundings" in javascript
    assert "source_mention" in javascript
    assert "relation_phrase" in javascript
    assert "target_mention" in javascript


def test_workbench_is_self_contained_and_declares_dynamic_service() -> None:
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    javascript = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
    css = (WEB_ROOT / "styles.css").read_text(encoding="utf-8")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "cdnjs" not in html + javascript + css
    assert "uvicorn" in dockerfile
    assert "crest_app.main:app" in dockerfile
    assert "LLM_CLIENT_DATA_ROOT=/data/llm-client" in dockerfile
    assert "COPY --from=llm_client" in dockerfile
    assert "127.0.0.1:8080/health" in dockerfile
