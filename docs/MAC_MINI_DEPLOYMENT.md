# CREST Mac mini deployment

This document owns the current operational contract for the hosted CREST
relationship-binding v2 viewer.

## Service contract

- Public entry: `https://brian-mac-mini.tail9c321e.ts.net/crest/`
- Publication: Tailscale Funnel path `/crest` on the existing port 443 router
- Container: `crest-kg`
- Container port: `8080`, bound to host loopback port `8798`
- Health response: `GET /health` returns service `crest-kg-viewer`
- Data: the immutable audited v2 graph copied into the image at build time
- Persistence: none; this is a read-only static viewer
- Existing bare-root and `/api`, `/learning`, `/process-tracing`, and other
  Funnel routes are separate services and must not be replaced.

The viewer intentionally presents a fixed development checkpoint. Hosting does
not promote its three supported edges into a corpus-recall or generalization
claim.

## Promotion procedure

1. Push the intended source revision to a recoverable Git ref.
2. Transfer a hash-bound archive or pull that exact revision on the Mac mini.
3. Build `crest-kg:<short-revision>` with `SOURCE_REVISION=<full-revision>`.
4. Start `crest-kg-candidate` on an isolated host loopback port and verify
   `/health`, `/`, `data/graph.json`, and the rendered relationship/evidence
   flow before changing Funnel.
5. Retain the currently verified container or image as a named rollback.
6. Promote only `crest-kg`, bound to `127.0.0.1:8798`.
7. Append the `/crest` Funnel path; never reset the shared Funnel router.
8. Verify the canonical public URL, browser console, failed requests, graph
   counts, relationship selection, entity search, and source evidence.
9. Record the exact deployed revision and evidence under `docs/deployments/`.

## Rollback

Restore the prior `crest-kg` container or image on host loopback port `8798`,
then recheck `/health` and the public `/crest/` route. If this first deployment
must be removed, remove only the `/crest` Funnel path and `crest-kg` container;
do not run `tailscale funnel reset`.
