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


def test_landing_headline_does_not_claim_to_be_loading() -> None:
    """The page's largest text must not be a status message it cannot retract.

    ``<h1 data-graph-title>`` ships in the static HTML and is only rewritten
    once app.js runs. When it read "Loading evidence graph…", any viewer whose
    JavaScript failed to load saw a permanent loading claim that no server-side
    state backed -- indistinguishable from a slow response, with nothing to act
    on. The static default has to describe what the panel is for instead.
    """

    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    assert "Loading evidence graph" not in html
    assert "Search documents to build a graph" in html


def test_asset_urls_advance_with_the_build_so_a_deploy_actually_ships() -> None:
    """A changed app.js must reach browsers without a hand-edited version string.

    The CSS and JS URLs carried a hardcoded date token. Shipping a change to
    either file without also remembering to edit that token leaves every
    browser on the cached previous copy, so the deploy silently changes
    nothing -- observed live, where a corrected headline stayed wrong after it
    had been corrected and redeployed. The token is now derived from the
    build, so it advances whenever the assets can have.
    """

    import os

    from fastapi.testclient import TestClient

    from crest_app.main import create_app

    os.environ["SOURCE_REVISION"] = "0123456789abcdef0123456789abcdef01234567"
    try:
        text = TestClient(create_app()).get("/").text
    finally:
        os.environ.pop("SOURCE_REVISION", None)

    assert "__ASSET_VERSION__" not in text, "placeholder was left unstamped"
    for asset in ("styles.css", "app.js"):
        assert f"{asset}?v=0123456789ab" in text, f"{asset} did not carry the build token"


def test_stage_numbers_follow_the_actual_task_order() -> None:
    """Numbered stages must not contradict the order they have to happen in.

    The panels were numbered 01 Sources, 02 Search, 03 Explore, 04 Evidence,
    with the select-and-build dock numbered 05 -- but building is what creates
    the graph that Explore and Evidence display, so 05 had to happen before 03
    and 04. A reader following the numbers was told to start on a panel whose
    every control is disabled, and to build last.
    """

    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    assert '<div class="eyebrow">01 · Search</div>' in html
    assert '<div class="step-number">02</div>' in html
    assert '<div class="eyebrow">03 · Explore</div>' in html
    assert '<div class="eyebrow">04 · Evidence</div>' in html
    assert "01 · Sources" not in html, "a fully disabled panel must not be step one"
    assert '<div class="step-number">05</div>' not in html


def test_identity_and_primary_journey_do_not_require_the_help_dialog() -> None:
    """What this is and what to do must be on the page, not behind "?".

    "CREST" is an unexplained acronym and the product's output was never named
    in the landing view; both lived only in the About dialog.
    """

    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    orientation = html.split('class="orientation"', 1)

    assert len(orientation) == 2, "no orientation line on the page"
    intro = orientation[1][: orientation[1].index("</p>")]
    assert "declassified" in intro and "CIA" in intro, "never says what the corpus is"
    assert "build" in intro.lower(), "never names the primary action"


def test_every_metric_the_script_writes_exists_in_the_document() -> None:
    """A script writing to a removed element takes the whole render down.

    renderGraphHeader() loops over metric names and assigns textContent
    unguarded, so deleting one <strong data-metric> from index.html without
    editing that loop throws "Cannot set properties of null" and the graph
    never draws -- observed live after the rejected-candidates metric was
    removed from the strip. The two lists have to agree.
    """

    import re

    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    present = set(re.findall(r'data-metric="([^"]+)"', html))

    # Every loop whose body writes data-metric, not just the first one found:
    # app.js has an unrelated validation loop with the same shape earlier in
    # the file, and matching only the first one checked the wrong list.
    loops = [
        match
        for match in re.finditer(r'for \(const field of \[([^\]]+)\]\)\s*\{(.*?)\n    \}', script, re.S)
        if "data-metric" in match.group(2)
    ]
    assert loops, "no metric-writing loop found in app.js"

    for match in loops:
        written = set(re.findall(r'"([^"]+)"', match.group(1)))
        missing = written - present
        assert not missing, f"app.js writes metrics absent from the page: {sorted(missing)}"


def test_setup_and_status_are_collapsed_out_of_the_primary_journey() -> None:
    """Configuration must not outweigh the one action a newcomer needs.

    The first screen carried 20 interactive controls, 7 of them disabled. The
    Sources panel sat above Search with eight controls -- every one of them
    disabled on a deployment without an operator token -- so the densest block
    on the page was also the deadest, and it came first.
    """

    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    search_at = html.index('class="panel-section search-section"')
    sources_at = html.index('class="panel-section source-section"')
    assert search_at < sources_at, "search must precede sources in the panel"

    assert '<details class="panel-section source-section">' in html
    assert '<details class="build-settings-wrap">' in html
    for block in ('class="panel-section source-section"', 'class="build-settings-wrap"'):
        opening = html[html.index(block) - 40 : html.index(block)]
        assert " open" not in opening, f"{block} must start collapsed"
