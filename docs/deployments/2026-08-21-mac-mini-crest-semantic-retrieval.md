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
