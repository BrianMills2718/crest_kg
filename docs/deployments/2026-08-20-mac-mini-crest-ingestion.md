# CREST private ingestion and OCR deployment — 2026-08-20

## Promoted artifact

- Canonical URL: `https://brian-mac-mini.tail9c321e.ts.net/crest/`
- Git repository: `BrianMills2718/crest_kg`
- Git revision: `cffa32fd89a3cf481fbef73def0ae4d88961f3f9`
- Git state at promotion: revision was the pushed `main` head
- Shared `llm_client` revision:
  `16b9eb19ae6402c23271ee8384c0508dce0f5acd`
- Image tag: `crest-kg:cffa32f`
- Image ID:
  `sha256:41a3757110a52f233f1da5ef08ae8a6dd4199749c4273d0368241eae5396c49a`
- Live container ID:
  `7eea80467f601d60fbeca9ae592cf70772dddd6c488e6e2283b6d9784c038f2b`
- Host binding: `127.0.0.1:8798 -> 8080/tcp`
- Persistent volume: `crest-kg-data -> /data`
- Existing Funnel route: `/crest -> http://127.0.0.1:8798`
- OCR runtime: Tesseract `5.5.0`

No Tailscale route was added, removed, or changed during promotion.

## User-visible increment

The workbench now accepts operator-only PDF, image, and UTF-8 text uploads.
It uses native PDF text where available, falls back to local OCR for sparse PDF
pages, and uses local OCR for PNG, JPEG, and TIFF images. Originals, extracted
text, source hashes, and extraction metadata persist in the existing workbench
volume. Uploaded sources participate in the same search, inspection, selection,
and graph-building flow as bundled CREST records.

Uploaded sources are private. Anonymous requests cannot list or open them, and
graphs built from uploads inherit operator-only access. Graph access records are
written before graph artifacts; missing access metadata fails closed after a
one-time migration explicitly classifies pre-feature generated graphs as
bundled/public.

The CIA Reading Room live connector now has a typed implementation and an
operator probe, but remains visibly unavailable because the official search
endpoint returns HTTP 403 from both development and deployment hosts. The UI
does not pretend that redirected landing pages are acquired source documents.

## Authentic ingestion and graph evidence

An isolated candidate received a generated 1,800 × 600 PNG containing a short
field memorandum. Local OCR produced the following receipt:

- document: `upload-248f339674b752fc589d`
- extraction: `image-ocr`, 1 page, 188 characters
- source SHA-256:
  `248f339674b752fc589d337eca2ab13aa396ec79e74a84bafbe0198419b5d05d`
- body SHA-256:
  `e347b4f609ce94c7dd0a5019a75d811c03a7c610f96af9b7a04cb4e038d6e15e`
- observed text included `Petrov delivered the Silver Key dossier on 9 May
  1978.`
- private search ranked the upload first for `Silver Key dossier`
- a second text upload round-tripped byte-for-byte with matching source hash

The candidate then completed a real UI-driven extraction through the shared
LLM client:

- trace: `crest_kg/workbench/c4605a1d367b405db0114f8151596ebd`
- model: `openrouter/minimax/minimax-m3`
- observed cost: `$0.00128688`
- result: 1 document, 8 entities, 1 accepted relationship, 3 explicit
  rejections

After promotion, the same first-visit browser workflow was exercised at the
canonical URL without an operator token; Tailscale identity supplied operator
authorization. The UI uploaded and selected the scan, ran the real graph build,
opened the result, selected the `delivered` relationship, and displayed the
exact supporting source quote and grounded endpoint spans:

- graph: `9599a773ce754017bec5ec90f0110419`
- trace: `crest_kg/workbench/9599a773ce754017bec5ec90f0110419`
- model: `openrouter/minimax/minimax-m3`
- observed cost: `$0.000719865`
- result: 1 document, 7 entities, 1 accepted relationship, 1 explicit
  rejection
- relationship: Elena Petrov `delivered` the Silver Key dossier
- evidence: uploaded document lines 3–3
- browser: zero severe console entries and zero failed network requests at
  1440 × 1000

## Boundary verification

- `GET /crest/health` reports healthy service `crest-workbench` at the exact
  promoted Git revision.
- Tailnet capability requests report upload and graph building enabled and
  authorized, with one private upload in the live volume.
- An external capability request reports both
  `document_upload_authorized=false` and `graph_build_authorized=false`, and
  omits the private upload count.
- The external graph list omits graph
  `9599a773ce754017bec5ec90f0110419`.
- An external direct request for that graph returns HTTP 403 with
  `Private graph access requires an authorized operator`.
- An unauthenticated upload to the isolated container returns HTTP 403.
- The CIA connector probe returns a typed unavailable result with official
  search HTTP status 403.
- The original Funnel routing table was observed after promotion with the same
  routes and `/crest` target.

## Rollback

The immediate pre-ingestion service is retained as stopped container
`crest-kg-rollback-c6c4cbc-pre-ingestion` using image `crest-kg:c6c4cbc`. Its
source data remains in the shared `crest-kg-data` volume, which the new version
only extends with explicit access records and private-ingestion directories.

To roll back the application, stop and rename the current `crest-kg`, rename
`crest-kg-rollback-c6c4cbc-pre-ingestion` to `crest-kg`, start it, and recheck
the unchanged `/crest` Funnel route. Do not reset the shared Funnel router.
