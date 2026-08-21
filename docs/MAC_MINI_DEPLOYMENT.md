# CREST Mac mini deployment

This document owns the operational contract for the hosted CREST research
workbench.

## Service contract

- Public entry: `https://brian-mac-mini.tail9c321e.ts.net/crest/`
- Publication: Tailscale Funnel path `/crest` on the existing port 443 router
- Container: `crest-kg`
- Container port: `8080`, bound to host loopback port `8798`
- Health response: `GET /health` returns service `crest-workbench`
- Read data: the tracked 40-document archive and immutable audited v2 example
  graph copied into the image at build time
- Persistence: named Docker volume `crest-kg-data` mounted at `/data` for jobs,
  generated graphs, graph-access records, private source originals/extracted
  text, and `llm_client` traces
- Build authorization: `CREST_BUILD_ENABLED=1`, the server budget ceiling, and
  either a Tailscale identity header or operator token
- Evidence-brief authorization: `CREST_BRIEF_ENABLED=1`,
  `CREST_MAX_BRIEF_BUDGET_USD`, and the same operator boundary; deterministic
  evidence preview and every inquiry read remain private
- Upload authorization: `CREST_UPLOAD_ENABLED=1`, byte/page/extracted-text
  ceilings, and the same operator boundary; the image contains local Tesseract
  OCR and never sends source files to an OCR service
- Secrets: `/Users/b/.secrets/api_keys.env` and the CREST operator environment
  are passed with Docker `--env-file`; neither is copied into the image
- Existing bare-root and `/api`, `/learning`, `/process-tracing`, and other
  Funnel routes are separate services and must not be replaced.

The default graph intentionally remains a fixed development checkpoint. Hosting
does not promote its three supported edges into a corpus-recall or
generalization claim.

The image depends on Brian's shared `llm_client`. BuildKit receives its exact
checkout as a named, read-only build context; it is built into a wheel without
copying Git credentials:

```bash
docker build \
  --build-context llm_client=/Users/b/code/active/llm_client \
  --build-arg SOURCE_REVISION=<crest-full-revision> \
  --build-arg LLM_CLIENT_REVISION=<llm-client-full-revision> \
  -t crest-kg:<crest-short-revision> .
```

## Promotion procedure

1. Push the intended source revision to a recoverable Git ref.
2. Transfer a hash-bound archive or pull that exact revision on the Mac mini.
3. Build `crest-kg:<short-revision>` with `SOURCE_REVISION=<full-revision>`.
4. Start `crest-kg-candidate` on an isolated host loopback port with its own
   candidate volume. Verify `/health`, `/`, bundled search, private text and
   scanned-image upload, OCR receipt, private search/detail/original download,
   unauthorized upload/private-read rejection, example graph rendering,
   export, unauthorized-build rejection, frozen evidence-retrieval gates, one
   authorized traced evidence brief, its cited-source graph handoff, and one
   authorized traced private document build before changing Funnel.
5. Retain the currently verified container or image as a named rollback.
6. Promote only `crest-kg`, bound to `127.0.0.1:8798`.
7. Append the `/crest` Funnel path; never reset the shared Funnel router.
8. Verify the canonical public URL, browser console, failed requests, upload,
   OCR, private/bundled search, document selection, build authorization, job
   completion, graph counts, source evidence, private export, and external
   denial of private-source and spend-bearing actions. For an evidence-synthesis
   promotion, also verify ranked passage preview, brief citations and
   contradiction/uncertainty labels, inquiry recovery, graph provenance, and
   anonymous denial of every inquiry route.
9. Record the exact deployed revision and evidence under `docs/deployments/`.

## Rollback

Restore the prior `crest-kg` container or image on host loopback port `8798`,
then recheck `/health` and the public `/crest/` route. If this first deployment
must be removed, remove only the `/crest` Funnel path and `crest-kg` container;
do not run `tailscale funnel reset`.
