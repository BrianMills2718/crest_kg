# CREST workbench Mac mini deployment — 2026-08-20

## Promoted artifact

- Public URL: `https://brian-mac-mini.tail9c321e.ts.net/crest/`
- Git repository: `BrianMills2718/crest_kg`
- Git revision: `c6c4cbcc82a887f216170cae9daa67a747e81ea7`
- Git state at promotion: revision was the pushed `main` head
- Shared `llm_client` revision:
  `16b9eb19ae6402c23271ee8384c0508dce0f5acd`
- Image tag: `crest-kg:c6c4cbc`
- Image digest:
  `sha256:a9e6b372539664338d16415c0f1b7bad3daee1863a78d07159339d8a251446d3`
- Live container ID:
  `e4e84f06b5475c2983a683680c87192d7110fb722f69c2f9b1d47a4dfba54660`
- Host binding: `127.0.0.1:8798 -> 8080/tcp`
- Persistent volume: `crest-kg-data -> /data`
- Funnel route: existing `/crest -> http://127.0.0.1:8798`; no other
  Tailscale route was changed

## Authentic execution evidence

The isolated Mac candidate used the same image and provider environment later
promoted to production. The canonical `disinformation` example selected CIA
document `05798947`, ran through the workbench API and shared `llm_client`, and
produced a graph that independently passed `crest_pipeline.py validate`:

- trace: `crest_kg/workbench/b585a3cea99b404abc98d79a92bb0224`
- model: `openrouter/minimax/minimax-m3`
- observed cost: `$0.00125106`
- result: 1 document, 10 entities, 1 relationship, 4 explicit rejections
- integrity: 0 duplicate IDs, 0 dangling relationships, 0 ungrounded
  relationships
- accepted assertion: the KGB `planted_rumor_about` the Central Intelligence
  Agency, grounded in document lines 101–104 with exact source, predicate, and
  target spans

The generated graph, job receipt, SQLite observability database, and JSONL
trace records were copied from the candidate volume to `crest-kg-data` before
promotion. A second build through the canonical tailnet URL proved the live
container's spend boundary and provider path:

- trace: `crest_kg/workbench/f610157f16f7412bbcccde41dd98b909`
- observed cost: `$0.00232866`
- result: 1 document, 17 entities, 0 relationships, 8 explicit rejections

An entity-only result is valid and remains visible as such; it was not inflated
with unsupported relationships.

## Boundary verification

- `GET /crest/health`: healthy service `crest-workbench` at the exact Git
  revision above.
- `POST /crest/api/search` for `disinformation`: 40 tracked matches; first
  result `05798947`.
- Browser critical flow on the isolated candidate and canonical public URL:
  30 results rendered, document selection worked, the build action became
  available for the Tailscale-authenticated operator, the generated graph
  opened, its relationship was selected, and exact source evidence appeared.
- Browser console: zero severe entries on both the candidate and canonical URL.
- Public/external capability probe: `graph_build_authorized=false`; graph
  building still requires an operator identity or token.
- Direct request without a trusted identity or token: HTTP 403.
- JSON export: returned a valid `crest-kg-v2` artifact containing the authentic
  trace and accepted relationship.
- Existing Tailscale Funnel routes before and after promotion were preserved;
  only the container behind the existing `/crest` target changed.

## Rollback

- Immediate pre-workbench rollback container:
  `crest-kg-rollback-a3439e52-pre-workbench` using image
  `crest-kg:a3439e52`.
- Fully tested workbench candidate retained stopped as `crest-kg-candidate`
  with its original `crest-kg-candidate-data` volume.
- Earlier rollback containers `crest-kg-rollback-61b7e1a3` and
  `crest-kg-rollback-5825d2f2` were not modified.

To restore the immediate prior viewer, stop and rename the current `crest-kg`,
rename `crest-kg-rollback-a3439e52-pre-workbench` to `crest-kg`, start it, and
recheck the unchanged `/crest` Funnel route. Do not reset the shared Funnel
router.
