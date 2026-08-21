# CREST research workbench

## Product outcome

CREST is an evidence-first document-to-knowledge-graph workbench. A researcher
can search tracked CIA Reading Room material, privately add PDFs, scans, and
text files in partial-success batches, organize sources into persistent research
collections, inspect and select sources, run a collection-scoped budget-bounded
evidence brief over exact ranked passages, hand cited sources into the existing
LLM graph extraction, recover prior inquiries and jobs after refresh or restart,
explore the resulting graph, and export its provenance-preserving artifact.

The public product entry point is the workbench at `/crest/`. A fixed graph or
evaluation artifact is supporting evidence, not the product front door.

## Primary workflow

1. Create or choose a private research collection, or work across all documents.
2. Batch-add private sources or search an available connector with ordinary keywords.
3. Observe native extraction, OCR, duplicate, unsupported, or failed state for every file.
4. Add tracked sources to the collection and search only its current membership.
5. Ask a natural-language question and preview exact ranked collection passages without a model call.
6. Authorize one brief ceiling; inspect support, contradiction, uncertainty, citations, unresolved questions, trace, and cost.
7. Hand at most three cited sources into the existing collection-guarded graph builder and authorize its separate ceiling.
8. Observe queued, running, failed, interrupted, or completed state without silent fallback.
9. Refresh or restart and reopen the persisted inquiry, job, and completed graph from recent activity.
10. Explore entities, relationships, exact source quotes, and grounding spans.
11. Download the validated `crest-kg-v2` JSON artifact.

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
  Batch ingestion applies the byte/page/pixel/text ceilings independently and
  reports every success and failure without rolling back valid siblings.
- `cia-reading-room-live`: implemented against the official current
  `/search/results` response and Reading Room HTML contract, but visibly
  unavailable unless both search and document acquisition succeed. As of
  2026-08-20, official search returns HTTP 403 from the workstation and Mac
  mini, and direct document routes redirect to the landing page.

Additional corpora and a repaired live connector should implement the same
`SourceConnector` search/document/probe boundary rather than introduce another
extraction path. Local files cross the strict `ExtractedUpload` contract before
persistence. These seams remain repository-local until a real second maintained
project adopts them.

## Collection and recovery contract

Collections are operator-private metadata records containing an ordered,
duplicate-free list of durable bundled or uploaded document IDs. They do not own
or copy source bytes. Deleting an upload removes it from every collection;
deleting a collection preserves its sources and completed graphs. Existing
sources remain available under All documents without a migration.

Collection-scoped searches can only return current members. A graph request that
names a collection is rejected if any selected document is not a member. Live
connector results are not durable members because their document cache does not
survive restart; retain that material as an uploaded source first.

Jobs are persisted newest-first and private. A service restart changes queued or
running records to explicit failed state; it never pretends an interrupted model
call completed. Completed job records link back to their persisted graph.

Evidence inquiries are likewise operator-private persistent records. Retrieval
chunks current collection members deterministically, retains exact character
offsets and score components, and calls no model. A brief may cite only its
retained chunk IDs; malformed or unknown citations fail the inquiry while its
evidence remains inspectable. Completed briefs label support, contradiction,
and uncertainty without claiming semantic entailment. A focused graph handoff
may select only cited documents that remain in the inquiry's collection.

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

Evidence-brief generation has the parallel `CREST_BRIEF_ENABLED` and
`CREST_MAX_BRIEF_BUDGET_USD` gates. Briefs and graph builds share one serial
provider lane, preventing concurrent browser actions from spending in parallel.

The server uses the repository's canonical `crest_pipeline.py` and the shared
`llm_client`; it does not maintain a second extractor. Jobs and generated graph
artifacts are persisted as atomic JSON files. The first implementation is a
single-operator development service, so builds run serially. Workbench calls
allow one `llm_client` structured-validation retry inside the same request
budget; source-grounding validation is never relaxed to rescue a bad response.

## Product stage and explicit non-goals

This is a private single-operator internal product, not a finished corpus-scale platform.
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
- An authorized operator can create Project Aster, ingest two valid sources and
  one unsupported file in a single batch, retain both successes, and understand
  the failed item without inspecting logs.
- Collection-only search cannot return non-members, collection graph builds
  reject non-members, upload deletion repairs memberships, and collection
  deletion preserves sources and graphs.
- Recent activity survives refresh; service-interrupted work is shown as failed,
  and completed jobs reopen their persisted graph.
- Private source text and private-source graphs are unavailable without an
  operator identity.
- Searching `disinformation` returns real tracked CREST documents with source
  identity, metadata, and text snippets.
- Selection and build controls are functional and have matching public API
  actions.
- Project Meridian's regression paraphrases rank the Vienna coordination and
  observer passages ahead of the Lisbon distractor, while contextual
  absent-subject controls return no evidence.
- An authorized operator can preview passages without model spend, persist a
  citation-valid brief that preserves the 14/16 May contradiction and role
  ambiguity, reopen it after refresh, and hand only cited documents to a graph.
- Anonymous inquiry preview, history, detail, and creation requests fail closed.
- Unauthorized build attempts fail visibly without calling a model.
- One authorized search-to-graph run completes through `llm_client`, records a
  trace and observed cost, renders in the workbench, and exports as validated
  JSON.
- The Mac mini deployment preserves every non-CREST Funnel route and exposes
  the exact pushed source revision.
