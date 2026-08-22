from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parents[1]
WEB_ROOT = ROOT / "web"


def test_workbench_leads_with_the_search_to_graph_workflow() -> None:
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    assert "CREST research workbench" in html
    assert "Search your source library" in html
    assert "Add document" in html
    assert "Turn documents into searchable evidence" in html
    assert "Research collection" in html
    assert "Ask this collection" in html
    assert "Preview ranked evidence" in html
    assert "support, contradiction, and uncertainty" in html
    assert "Use cited sources for a focused graph" not in html
    assert "Recent activity" in html
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
        'api("uploads/batch"',
        "api(`uploads/",
        'api("collections"',
        'api("evidence/preview"',
        'api("inquiries"',
        "api(`inquiries/",
        "api(`collections/",
        'api("connectors/cia-reading-room-live/probe"',
        "api(`documents/",
        'api("graphs"',
        'api("jobs"',
        "api(`jobs/",
        "api(`graphs/",
    ):
        assert route in javascript
    assert "Search failed:" in javascript
    assert "Build failed:" in javascript
    assert "Graph request failed:" in javascript
    assert "Upload failed:" in javascript
    assert "Evidence preview failed:" in javascript
    assert "Brief request rejected:" in javascript
    assert "Use cited sources for a focused graph" in javascript
    assert "inquiry_id: state.inquiryId" in javascript
    assert 'localStorage.setItem("crestActiveCollection"' in javascript
    assert 'localStorage.getItem("crestActiveCollection"' in javascript
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
    assert '[hidden] { display: none !important; }' in css
    assert "crest_app.main:app" in dockerfile
    assert "LLM_CLIENT_DATA_ROOT=/data/llm-client" in dockerfile
    assert "COPY --from=llm_client" in dockerfile
    assert "127.0.0.1:8080/health" in dockerfile


def test_page_assets_resolve_under_a_mount_prefix_without_a_trailing_slash() -> None:
    """The served page must not depend on the URL's trailing slash.

    Every asset and API call in index.html is written relative. Without a
    <base>, requesting the app at ``/crest`` makes the browser resolve
    ``./app.js`` against the site root, so the page loads no JavaScript and
    whatever unrelated stylesheet the parent host serves at ``/styles.css``.
    It renders as broken unstyled markup, while ``/crest/`` works -- a
    one-character difference that is easy to hand someone by accident.
    """

    from fastapi.testclient import TestClient

    from crest_app.main import create_app

    for root_path, expected in (("", '<base href="/" />'), ("/crest", '<base href="/crest/" />')):
        response = TestClient(create_app(), root_path=root_path).get("/")
        assert response.status_code == 200
        assert expected in response.text, f"missing base for root_path={root_path!r}"
