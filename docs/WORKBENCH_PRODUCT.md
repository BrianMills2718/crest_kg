# CREST research workbench

## Product outcome

CREST is an evidence-first research workbench for CIA Reading Room material. A
researcher can search an available CREST corpus, inspect and select source
documents, run a budget-bounded LLM extraction, explore the resulting knowledge
graph, and export the complete provenance-preserving graph artifact.

The public product entry point is the workbench at `/crest/`. A fixed graph or
evaluation artifact is supporting evidence, not the product front door.

## Primary workflow

1. Search an available source connector with ordinary keywords.
2. Inspect result metadata and source text before selecting documents.
3. Select one to three documents and explicitly authorize a dollar ceiling.
4. Start one traced graph-build job through the same API used by the UI.
5. Observe queued, running, failed, or completed state without silent fallback.
6. Explore entities, relationships, exact source quotes, and grounding spans.
7. Download the validated `crest-kg-v2` JSON artifact.

The stable first-run example is the query `disinformation`, selecting one
document, building its graph, and opening an extracted assertion's evidence.

## Current source contract

- `bundled-crest`: searchable and available. It contains the 40 tracked CIA
  Reading Room records in
  `cia_documents/disinformation_complete_20250517_002848.json`.
- `cia-reading-room-live`: visibly unavailable while the CIA Reading Room
  search and document routes redirect automated requests back to the landing
  page. The application must not label bundled results as live results.

Additional corpora and a repaired live connector should implement the same
typed search/document boundary rather than introduce another extraction path.

## Execution and trust boundary

Search, document inspection, completed graph exploration, and JSON export are
read-only. Graph building can spend provider funds and therefore requires all
of the following:

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

This is an active development vertical, not a finished corpus-scale product.
It does not yet claim live CIA coverage, OCR of newly uploaded PDFs, corpus
recall, multi-user collaboration, or production-scale job orchestration. The
fixed five-document relationship-binding graph remains an explicitly labeled
example checkpoint.

## Acceptance boundary for this vertical

- A fresh visitor immediately sees a search workbench rather than a fixed
  artifact viewer.
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
