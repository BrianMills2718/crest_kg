# Mac mini deployment — semantic retrieval and answerability gate

- **Date:** 2026-08-21
- **Host:** Mac mini (Tailscale), container `crest-kg`, published on `127.0.0.1:8798`
- **Public path:** `/crest` behind Tailscale, currently exposed via **Funnel** (public internet), not tailnet-only
- **Image:** `crest-kg:442f27f`
- **Source revision:** `442f27f9a5dd4c2f8b08bb61616b86cee8a52ded`
- **Data:** named volume `crest-kg-data` mounted at `/data` (preserved across the swap)

## What changed in this revision

Evidence retrieval no longer scores passages with hand-written lexical heuristics.
Ranking is a static sentence embedding (`minishlab/potion-base-8M`, baked into the
image) and abstention is a separate LLM answerability gate through the shared
`llm_client`. Held-out fixture error fell from 58.6% to 17.2%; on the real CREST
corpus probe, abstention rose from 10% to 85% and ranking recall from 80% to 85%.

## Deployment defects found and fixed during verification

1. **No operator token.** The previous container ran without `CREST_OPERATOR_TOKEN`
   and without `CREST_TRUST_TAILSCALE_HEADERS`, so every operator action returned
   403. The hosted app was a read-only document browser. A token now lives at
   `~/.crest_operator_token` on the host (`chmod 600`) and is passed to the container.
2. **Answerability cache path was read-only.** `CREST_ANSWERABILITY_CACHE` defaults
   beside the evaluation fixtures, which is correct in a checkout but not writable in
   the image, so every evidence preview raised
   `PermissionError: /app/evaluation` and returned HTTP 500. The container now sets
   `CREST_ANSWERABILITY_CACHE=/data/workbench/answerability_cache`, and the Dockerfile
   sets the same default so a rebuild keeps the fix.

## Verification (this deployment, through the running container)

- `GET /crest/health` → `{"status":"ok","source_revision":"442f27f…"}` (over Tailscale)
- `POST /crest/api/search` `disinformation` → 40 matches
- Unauthenticated `GET /api/collections` → **403**
- Authenticated collection create → **201**; membership update → **200** (8 documents)
- Answerable question — *"What did the KGB manual reveal about dezinformatsiya?"* →
  **200**, one passage kept: *DISINFORMATION: OR, WHY THE CIA CANNOT VERIFY AN
  ARMS-CONTROL AGREEMENT*, chars 12533–13381
- Unanswerable question — *"What was the hotel address of the Vienna team and which
  airline did they fly?"* → **200**, **abstained** (zero passages)

## Known limits

- `/crest` is on Tailscale **Funnel**, i.e. reachable from the public internet. Write
  actions are token-gated; document search and reading are not.
- The `user-uploads` connector reports `unavailable` — document upload is disabled on
  this server, so the hosted instance searches the 40 bundled documents only.
- The `cia-reading-room-live` connector is unavailable; cia.gov returns 403 to this
  host. Bundled documents were downloaded before the block and are unaffected.
- `score_components` in the evidence payload still carries the retired lexical fields
  (`bm25`, `fuzzy`, `phrase`), which now report zero.

---

## Update — revision `9402fb6`: the hosted page was broken and I shipped the broken URL

The verification above was API-only. I never loaded the page. Brian did, and it
rendered as unstyled broken markup with no working controls.

**Cause.** Every asset and API call in `index.html` is written relative
(`./app.js`, `./styles.css`, `./api/search`). A browser resolves those against
the current directory. At `/crest` — no trailing slash — that directory is the
site root, so the page requested `/app.js` (**404, no JavaScript at all**) and
`/styles.css`, which exists on this host but belongs to a *different* app
proxied at `/`. The page therefore loaded someone else's stylesheet and none of
its own code. At `/crest/` the same page works. I handed over the URL without
the slash.

**Fix.** `index.html` is now served with a `<base href="{root_path}/">` derived
from the app's mount point, so relative resolution is pinned regardless of the
trailing slash. Covered by
`tests/test_crest_web.py::test_page_assets_resolve_under_a_mount_prefix_without_a_trailing_slash`,
which mounts the app under a prefix and asserts the tag. Full suite: 52 passed.

**Second defect, self-inflicted.** The first redeploy of this fix dropped
`SOURCE_REVISION`, because the env carry-forward filter only preserved
`CREST_*`, `LLM_CLIENT_*`, `OPENROUTER_*`, and `HF_*`. `/health` reported
`source_revision: unknown` — the deployment could not identify itself. Rebuilt
with `--build-arg SOURCE_REVISION=<sha>` and redeployed.

## Verification — browser, not curl

- `https://brian-mac-mini.tail9c321e.ts.net/crest` (no trailing slash) loads with
  **zero console errors**; previously `app.js` 404'd at 158ms
- `<base href="/crest/" />` present in the served HTML at the bare URL
- Page renders the full workbench: sources panel, search returning 40 matches for
  `disinformation`, evidence graph with labelled nodes, inspector
- `/health` reports `source_revision: 9402fb6a439c2741395143c704eb41e306273533`

## Open UI issues observed while looking (not fixed)

- The graph canvas is roughly three times the height of the drawn graph, so the
  default view is mostly empty and the nodes sit in the lower third. `Fit graph`
  corrects it manually; it should be the initial state.
- The header reports `82 ENTITIES` while five nodes are visible, because
  `Connected only` is on by default. The headline number does not describe what
  is on screen.
- `72 REJECTED CANDIDATES` is given equal prominence to `3 RELATIONSHIPS`. A 96%
  rejection rate is the most visually prominent fact about the graph.
- Every left-panel action — `Add document`, `New collection`, `Ask this
  collection` — is disabled without an operator token, so an unauthenticated
  visitor sees a mostly dead panel with no explanation of how to authenticate
  beyond one line of small grey text.

---

## Update — usability pass, and the deployment's real gap

The owner's verdict on the working page was that he had no idea how to use it
and the interface was incredibly busy. A cold-start comprehension audit found
20 interactive controls on the first screen, 7 of them disabled, and 13
separate instruction texts — but the reason the journey was unreadable was
structural, not density.

**The stage numbers contradicted their own order.** Panels read 01 Sources, 02
Search, 03 Explore, 04 Evidence, with the select-and-build dock numbered 05.
Building is what creates the graph Explore and Evidence display, so 05 had to
happen before 03 and 04. Step 01 — the one the numbering told a newcomer to
start on — had all four of its controls disabled on this deployment. The
sequence now reads 01 Search, 02 select and build, 03 Explore, 04 Evidence,
with Sources demoted to a collapsed status panel below Search.

**The primary action was switched off.** `CREST_BUILD_ENABLED` was unset, so
`Build knowledge graph` could never enable: the hosted instance could search
and read but not do the one thing it exists for, and the landing page's own
orientation line promised it. `CREST_BUILD_ENABLED`, `CREST_BRIEF_ENABLED`, and
`CREST_UPLOAD_ENABLED` are now `1`. All three remain operator-token gated and
keep the server budget ceilings ($0.25 build, $0.15 brief), so only an
authenticated operator can spend.

Other changes: the identity and primary journey moved out of the `?` dialog
onto the page; rejected candidates moved from the headline metrics to the
provenance line; the graph frames its own content instead of a fixed viewBox;
the workbench fits the window rather than clipping under the sticky dock; build
options collapse behind `Options`; and the operator-token field, now one click
deeper, has a visible route in from the build status.

## Verification — browser, at 1440x900 and 900x800

- Landing view renders with zero console errors; whole workbench fits the
  window at desktop width with no clipping
- Search returns 40 matches; ticking a result updates the dock to `1 document
  selected` and names it
- Clicking a graph node populates the Inspector with the entity, its type, the
  grounded reference count, and an exact source quote with document ID and line
  numbers (`Document 05259030 · lines 54–54`)
- Unauthenticated: `Build knowledge graph` stays disabled and the status offers
  `Enter operator token to build`, which opens Options and focuses the field
- A deliberately wrong token leaves the button disabled
- With the correct token, `GET /api/capabilities` returns
  `graph_build_authorized: true`

**Not verified:** no graph build was executed. Running one spends against the
OpenRouter key, which is the owner's call, so the build path is proven up to
authorization and not beyond.

## Still open

- `/crest` remains on Tailscale **Funnel** (public internet). Turning Funnel off
  is not scoped to this app — the root host also serves 16 other paths — so it
  needs its own decision rather than a side effect of this work.
- `CREST_TRUST_TAILSCALE_HEADERS` stays off deliberately. It would let the
  proxy's identity header authorize an operator, which is unsafe while the same
  container answers on a public Funnel route.
- The operator token lives in `sessionStorage`, so it is re-entered per browser
  session.
- Below 1121px the dock stacks to two rows and the graph scrolls under it.
