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
  generated graphs, and `llm_client` traces
- Build authorization: `CREST_BUILD_ENABLED=1`, the server budget ceiling, and
  either a Tailscale identity header or operator token
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
   candidate volume. Verify `/health`, `/`, search, document inspection,
   example graph rendering, export, unauthorized-build rejection, and one
   authorized traced build before changing Funnel.
5. Retain the currently verified container or image as a named rollback.
6. Promote only `crest-kg`, bound to `127.0.0.1:8798`.
7. Append the `/crest` Funnel path; never reset the shared Funnel router.
8. Verify the canonical public URL, browser console, failed requests, source
   search, document selection, build authorization, job completion, graph
   counts, relationship selection, source evidence, and JSON export.
9. Record the exact deployed revision and evidence under `docs/deployments/`.

## Rollback

Restore the prior `crest-kg` container or image on host loopback port `8798`,
then recheck `/health` and the public `/crest/` route. If this first deployment
must be removed, remove only the `/crest` Funnel path and `crest-kg` container;
do not run `tailscale funnel reset`.
