# CREST collections and recovery deployment — 2026-08-20

## Promoted artifact

- Canonical URL: `https://brian-mac-mini.tail9c321e.ts.net/crest/`
- Git repository: `BrianMills2718/crest_kg`
- Git revision: `8263c1e26ae23922e4a21e883efdceeb069a0a17`
- Git state at promotion: revision was the pushed `main` head
- Shared `llm_client` revision:
  `87e5df3c7e3f9217568a9ea2a7a67b4a0bc1d1e3`
- Image tag: `crest-kg:8263c1e`
- Image ID:
  `sha256:deb702583c2ae52e5aa4729d4e74313bd446e8cc33af3a3508afa6a9b3ee6372`
- Live container ID:
  `e38f096f9d1d1341ad0b55b05ce6eb3bc4339d74f8a33494a412bc6a908f3893`
- Host binding: `127.0.0.1:8798 -> 8080/tcp`
- Persistent volume: `crest-kg-data -> /data`
- Existing Funnel route: `/crest -> http://127.0.0.1:8798`
- OCR runtime: Tesseract `5.5.0`

No Tailscale route was added, removed, or changed. The live container reports
healthy and `/crest/health` reports the exact revision above.

The host's credential source uses shell syntax, including directives that are
not accepted by Docker's `--env-file` parser. Promotion therefore did not pass
that source to Docker directly: it copied only the already-approved application
environment keys from the prior live container into the replacement invocation
without printing or persisting their values. This preserved the credential
boundary while keeping an invalid shell-style file out of Docker's parser.

## User-visible increment

The workbench now provides private persistent research collections. An operator
can create a collection, add or remove durable bundled/uploaded source members,
search only that membership, and guard a graph build so it cannot silently use
an out-of-collection document. Deleting an upload repairs every membership;
deleting a collection retains its sources and graphs. The browser remembers the
active collection across refreshes.

Multi-file ingestion accepts up to the configured batch limit and reports each
file independently. A bad sibling no longer discards valid extractions. Recent
activity lists persistent jobs newest-first, exposes completed/failed/running
state, and reopens a completed graph without a remembered job ID. A service
restart marks interrupted work explicitly failed and retains completed history.

`ExtractedUpload` is now a strict Pydantic phase result and `SourceConnector` is
the repository-local search/detail/raw-document/probe protocol used by the CIA
connector path. This is generalized internal infrastructure, not yet a shared
package: extraction waits for a real second maintained consumer.

## Project Aster canonical observation

At the canonical URL, a fresh 1440 × 1000 browser context performed the stable
Project Aster workflow:

1. created collection `collection-6518c3038fdb4f35`;
2. submitted two readable text sources and one unsupported ZIP in one upload;
3. observed two independent successes and one explicit unsupported-format
   failure in the dialog;
4. searched `Orchid Transit` within the collection and observed exactly two
   results;
5. selected both sources and submitted a collection-scoped `$0.10` graph job;
6. opened the resulting graph, refreshed through a service/image replacement,
   observed the active collection restored, and reopened the graph from Recent
   activity;
7. selected an entity, read its exact source quote, and downloaded the validated
   JSON artifact.

Canonical graph evidence:

- graph/job: `b640860308a245afb476f32ddeeef083`
- trace: `crest_kg/workbench/b640860308a245afb476f32ddeeef083`
- model: `openrouter/minimax/minimax-m3`
- observed cost: `$0.00126448`
- result: 2 documents, 12 entities, 5 relationships, 0 rejected candidates
- source IDs: `upload-626b4ae35bad52d25e64` and
  `upload-a6e7df6cf6c19b903e83`
- trace inspection: two JSON-schema calls; both recorded started, received, and
  validated events on attempt zero; neither call recorded an error or retry
- browser: 17 observed API responses, zero failed API responses, zero console
  errors, and zero unexplained request failures
- export: `crest-b640860308a245afb476f32ddeeef083.json`
- screenshot:
  `/Users/b/runtime/crest-kg/deployments/8263c1e/project-aster-canonical-1440x1000.png`
- screenshot SHA-256:
  `af4d94f2a16b242c86b2c7f424e79ded1530053f26a7809b8ed9014c03a3ad49`

The first canonical pass exposed that persistence was correct but the active
collection picker reset to All documents after refresh. Revision `8263c1e`
stores and restores that selection locally. The same paid graph was retained;
the final pass reselected once, refreshed, observed automatic restoration, and
then completed history, evidence, and export checks without another model call.

## Contract and boundary verification

- Final repository suite: 43 passed.
- OpenAPI and API tests cover private collection CRUD, strict unique membership,
  scoped search, out-of-collection build rejection, upload-deletion
  reconciliation, collection-deletion source retention, batch partial success,
  invalid-collection preflight, persistent job listing, and interrupted-job
  recovery.
- An isolated candidate used its own volume, completed an independent two-source
  graph canary, survived a container restart, and was removed after promotion.
  Its container and disposable volume are not recoverable; no live data used
  them.
- Direct anonymous candidate requests returned 403 for collection/job lists,
  private search, private document, private graph, batch upload, and graph build.
- An external retrieval path reported
  `graph_build_authorized=false`,
  `document_upload_authorized=false`, and no private upload count. External
  collection list, job list, and canonical private graph requests returned 403.
- The final canonical browser used normal visible controls and the same API
  routes documented at `/crest/api/docs`.
- The Funnel routing table after promotion retained the bare root, `/api`,
  `/dr-k`, `/brent`, `/godel`, `/claude`, `/category`, `/waltzman`, `/learning`,
  `/generated`, `/second-brain`, `/learning-map`, `/process-tracing`,
  `/twitter-prospector`, `/cybernetic-influence`, and
  `/second-brain-planning` routes unchanged.

## Rollback

The immediate pre-refresh-fix service is retained as stopped container
`crest-kg-rollback-693e0db-pre-recovery` using image `crest-kg:693e0db`. The
pre-collections service is also retained as
`crest-kg-rollback-cffa32f-pre-collections` using `crest-kg:cffa32f`.

To roll back the application, stop and rename the current `crest-kg`, rename the
chosen rollback container to `crest-kg`, start it on the unchanged live volume,
and recheck `/health` and `/crest/`. Do not reset the shared Funnel router.
