# CREST deployment operations

This document owns the operational contract for the hosted CREST research
workbench. Cloudflare is the canonical public host. The Mac Mini procedure is
retained below only as historical guidance for the private, full-featured
runtime; it is not the public availability path.

## Canonical public service

- Public entry: `https://brianmills.dev/crest/`
- Host: Cloudflare Worker `crest-review` and Cloudflare Container application
  `crest-review-crestreviewcontainer`
- Worker version: `2d17f736-3f70-4c0e-b136-01fcb899f601`
- Container application ID: `a03a5128-e488-4b65-89b2-b71f4987a312`
- Image: `crest-review:5f58607`, digest
  `sha256:48e22a7307746c0be5ceb777cd694631f14089db279ede7f2e57b29de114fb33`
- CREST source revision: `5f586075d551265999a5ca00245e70d2ae7d1c88`
- `llm_client` source revision:
  `54bb657c316b37b13369c251fc8e60c6cecad995`
- Deployment configuration: `deploy/cloudflare/read-only/`
- Public capabilities: tracked 40-document archive, semantic search, audited
  example graph, source inspection, and graph export
- Disabled public capabilities: graph building, evidence briefs, and uploads
- Persistence: none; the public recovery does not accept durable writes
- Secrets: none

The basic instance starts slowly. The Worker permits a three-minute cold start
and sends a scheduled health request every five minutes to keep its single
instance available. The Mac Mini is not in the public request path.

## Cloudflare promotion and rollback

Build and push the image using `deploy/cloudflare/read-only/README.md`, run
`npm run check`, then deploy from that directory. Verify `/crest/`,
`/crest/health`, `/crest/api/capabilities`, the bundled graph and export routes,
and the three browser assets. Confirm in a real browser that the tracked archive
and audited example graph render.

Rollback by deploying the prior known-good Worker version or by restoring the
prior image tag in `wrangler.jsonc` and redeploying. Do not alter unrelated
`brianmills.dev` routes, and do not restore the Mac Funnel as the canonical
public host.

## Legacy Mac full-feature service contract

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

## Last full-feature Mac promotion (historical)

As of 2026-08-21, `crest-kg:d884f49` is the healthy canonical container on the
existing `crest-kg-data` volume. Its full source revision is
`d884f493a73bc289bcbbc72399294aa77cdd4ce4`; the stopped rollback container is
`crest-kg-rollback-8263c1e-20260821`. The isolated candidate and candidate
volume are retained stopped. Exact build hashes, authentic Project Meridian
traces and costs, external privacy probes, restart recovery, screenshot hashes,
and route evidence are in
[`deployments/2026-08-21-mac-mini-crest-evidence-synthesis.md`](deployments/2026-08-21-mac-mini-crest-evidence-synthesis.md).

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

## Historical Mac promotion procedure

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

## Historical Mac rollback

Restore the prior `crest-kg` container or image on host loopback port `8798`,
then recheck `/health` and the public `/crest/` route. If this first deployment
must be removed, remove only the `/crest` Funnel path and `crest-kg` container;
do not run `tailscale funnel reset`.
