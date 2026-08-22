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
