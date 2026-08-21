# CREST research workbench

## Product outcome

CREST is an evidence-first document-to-knowledge-graph workbench. A researcher
can search tracked CIA Reading Room material, privately add PDFs, scans, and
text files, inspect and select sources, run a budget-bounded LLM extraction,
explore the resulting graph, and export its provenance-preserving artifact.

The public product entry point is the workbench at `/crest/`. A fixed graph or
evaluation artifact is supporting evidence, not the product front door.

## Primary workflow

1. Upload a private source or search an available connector with ordinary keywords.
2. Observe native extraction, OCR, duplicate, unsupported, or failed state.
3. Inspect result metadata and source text before selecting documents.
4. Select one to three documents and explicitly authorize a dollar ceiling.
5. Start one traced graph-build job through the same API used by the UI.
6. Observe queued, running, failed, or completed state without silent fallback.
7. Explore entities, relationships, exact source quotes, and grounding spans.
8. Download the validated `crest-kg-v2` JSON artifact.

The stable acquisition example is uploading a short field memorandum, finding
it by title or body text, selecting it, building its graph, and opening an
extracted assertion's exact source evidence.

## Current source contract

- `bundled-crest`: searchable and available. It contains the 40 tracked CIA
  Reading Room records in
  `cia_documents/disinformation_complete_20250517_002848.json`.
- `user-uploads`: operator-only and persistent when enabled. PDF pages use
  embedded text when present and local Tesseract OCR otherwise; PNG, JPEG, and
  TIFF use OCR; UTF-8 text, Markdown, RST, CSV, and TSV use direct text. The
  original bytes and validated extracted text share one content-addressed ID.
- `cia-reading-room-live`: implemented against the official current
  `/search/results` response and Reading Room HTML contract, but visibly
  unavailable unless both search and document acquisition succeed. As of
  2026-08-20, official search returns HTTP 403 from the workstation and Mac
  mini, and direct document routes redirect to the landing page.

Additional corpora and a repaired live connector should implement the same
typed search/document boundary rather than introduce another extraction path.

## Execution and trust boundary

Bundled search, bundled document inspection, public graph exploration, and
public JSON export are read-only. Uploads, private-source search and inspection,
original downloads, deletion, live connector calls, and graphs built from any
private/live source require a Tailscale identity or operator token. A missing
graph-access sidecar fails closed; the deployment performs one explicit
backfill of pre-feature bundled graphs.

Graph building can spend provider funds and therefore also requires all of the
following:

- server-side build enablement;
- a request budget no greater than the configured server ceiling; and
- an operator identity supplied by a trusted Tailscale header or an operator
  token.

The server uses the repository's canonical `crest_pipeline.py` and the shared
`llm_client`; it does not maintain a second extractor. Jobs and generated graph
artifacts are persisted as atomic JSON files. The first implementation is a
single-operator development service, so builds run serially. Workbench calls
allow one `llm_client` structured-validation retry inside the same request
budget; source-grounding validation is never relaxed to rescue a bad response.

## Product stage and explicit non-goals

This is an active development product, not a finished corpus-scale platform.
It does not claim live CIA coverage, layout-preserving OCR, handwriting
recognition, non-English OCR packs, corpus recall, multi-user collaboration, or
production-scale job orchestration. The
fixed five-document relationship-binding graph remains an explicitly labeled
example checkpoint.

## Acceptance boundary for this vertical

- A fresh visitor immediately sees an acquisition/search workbench rather than a fixed
  artifact viewer.
- An authorized operator can upload text, a text PDF, and a scanned image;
  inspect extraction method and source hashes; search the result; select it;
  download the original; and delete it.
- Private source text and private-source graphs are unavailable without an
  operator identity.
- Searching `disinformation` returns real tracked CREST documents with source
  identity, metadata, and text snippets.
- Selection and build controls are functional and have matching public API
  actions.
- Unauthorized build attempts fail visibly without calling a model.
- One authorized search-to-graph run completes through `llm_client`, records a
  trace and observed cost, renders in the workbench, and exports as validated
  JSON.
- The Mac mini deployment preserves every non-CREST Funnel route and exposes
  the exact pushed source revision.
