# CREST seven-day daily research workbench increment

Status: active implementation plan  
Owner: Brian Mills (product) / repository automation (implementation)  
Window: 2026-08-20 through 2026-08-27  
Stage: internal product  
Canonical surface: <https://brian-mac-mini.tail9c321e.ts.net/crest/>

## Outcome

A researcher can organize private and bundled documents into a durable research
collection, add several sources in one batch without losing successful items
when another fails, search and build a graph within that collection, and recover
the build and graph after a browser refresh or service restart.

The stable observation is **Project Aster**: create that collection, batch-add
two readable sources and one unsupported file, observe two successes and one
explicit failure, search only Project Aster, select up to three members, run one
real traced graph build, refresh the page, reopen the completed job and graph,
inspect exact evidence, and export the validated artifact.

Passing this observation proves that the named daily workflow executed on the
named revision and deployment. It does not prove corpus recall, extraction
quality beyond the observed sources, production-scale orchestration, or public
multi-user readiness.

## Boundaries and invariants

| Boundary | Owns | Invariants and failure behavior |
| --- | --- | --- |
| Acquisition | Bounded local decoding/OCR and a typed extraction result | No external OCR; unsupported, unreadable, or oversized input fails explicitly; a batch reports each item independently. |
| Source catalog | Search, source identity, and raw-document resolution | Collection scope can only narrow eligible sources; connector failure remains visible; no source is relabeled as live. |
| Collection store | Private collection metadata and ordered document membership | Collections never own or copy source bytes; deleting a collection preserves sources and graphs; deleting an upload removes its memberships; existing sources begin Unfiled. |
| Job/graph store | Persistent state, recovery, access classification, and graph artifacts | Interrupted queued/running work becomes an explicit failed job after restart; restricted artifacts fail closed; history is operator-only. |
| Workbench API | Authorization, server ceilings, typed transitions, and API parity | Private data is checked before it crosses the seam; collection builds may use only collection members; no partial action silently succeeds. |
| Browser workbench | Repeated research flow and visible recovery | Business rules stay behind the API; initial, loading, partial success, empty, failed, running, completed, and recovered states are visible. |

Collection state transition:

```text
absent --create--> active --replace membership / batch add--> active --delete--> absent
                              |                                  |
                     upload deleted                       sources retained
                              v
                    dangling membership removed
```

Build recovery transition:

```text
queued -> running -> completed -> reopen graph after refresh
             |            |
             +-> failed <--+ service restart marks interrupted work explicitly
```

## Typed contracts

- `ResearchCollection`: stable ID, title, description, ordered unique document
  IDs, and created/updated timestamps.
- `CollectionCreate` and `CollectionUpdate`: strict mutation inputs; unknown
  fields rejected.
- `SearchRequest.collection_id`: optional private scope; when present, only
  members can be returned.
- `GraphBuildRequest.collection_id`: optional provenance/scope guard; every
  selected document must be a current member.
- `BatchUploadReceipt`: ordered successes plus per-file typed failures and the
  optional collection that received successful documents.
- `GraphJobList`: newest-first persisted job history using the existing
  `GraphJob` transition contract.

The repository-local acquisition and source-connector contracts are the
canonical seam for this increment. Extraction into a shared package is deferred
until a real second repository consumes the contract; the trigger is an actual
consumer integration, not anticipated reuse.

## Risk-ordered slices

### Slice 1 — Durable collection vertical

- Advances: organizes multiple sources into a repeatable research context.
- Vertical scope: create/list/update/delete collection, scope search, guard a
  collection graph build, and select the active collection in the existing UI.
- De-risks: persistence, privacy, deletion, and membership ownership.
- Success: focused API test covers create, membership, scoped positive/negative
  search, out-of-collection build rejection, upload deletion reconciliation,
  collection deletion source retention, and anonymous denial.
- Done when: the API and rendered UI can drive the same collection workflow.

### Slice 2 — Partial-success batch acquisition

- Advances: makes source ingestion efficient enough for daily work.
- Vertical scope: upload several files, persist every valid extraction, attach
  successes to the active collection, and display every outcome.
- De-risks: mixed failure semantics and duplicate handling.
- Success: two valid fixtures and one unsupported fixture yield two durable
  receipts and one explicit failure; an invalid collection rejects before
  ingestion.
- Done when: an operator can select multiple files once and understand the
  complete result without inspecting logs.

### Slice 3 — Job and graph recovery

- Advances: makes completed and failed work discoverable after reload.
- Vertical scope: newest-first job API, visible recent activity, running/failed
  state, and reopen action for completed graphs.
- De-risks: durable state that exists but is stranded in storage.
- Success: persisted jobs survive app recreation; interrupted work is listed as
  failed; a completed graph reopens from the history surface after refresh.
- Done when: no remembered job ID or prior tab state is required.

### Slice 4 — Acquisition/connector contract adoption

- Advances: gives future projects one truthful extension seam.
- Vertical scope: strict typed acquisition result, explicit source-connector
  protocol, adoption by the current upload and CIA connector paths, contract
  documentation, and focused positive/failure fixtures.
- De-risks: adding another bespoke extraction or connector path.
- Success: current consumers use the declared seam and incompatible results fail
  validation.
- Done when: a new connector can implement the documented contract without
  changing the workbench API; no cross-project adoption claim is made.

### Slice 5 — Canonical integration and promotion

- Advances: turns the increment into observed, recoverable hosted capability.
- Vertical scope: focused suite, fresh browser context, one real traced model
  build, privacy checks, candidate container, canonical promotion, rollback,
  and immutable deployment receipt.
- De-risks: UI/API drift, stale assets, access regression, route damage, and
  unobserved model behavior.
- Success: Project Aster passes through the canonical URL at one representative
  desktop viewport with no severe console errors or failed critical requests;
  anonymous negative checks pass; all pre-existing Funnel routes remain.
- Done when: the exact pushed revision/image/trace and rollback are recorded.

## Preservation contract

The existing `/crest/` entry point, bundled search, live-connector status/probe,
source inspection, one-to-three source selection, budget ceiling, traced graph
build, graph visualization, evidence inspector, graph picker, and JSON export
are preserved. Collection controls extend the existing research panel; recent
activity extends the existing graph picker rather than creating a competing
application.

The development viewport is 1440×1000. Responsive behavior below 760 px is
preserved but is not a new layout target for this internal-product increment.

## Explicit non-goals and promotion triggers

- No claim of repaired CIA live acquisition while the official endpoint denies
  access.
- No semantic/vector search, automatic entity resolution across graphs, or
  corpus-scale recall claim.
- No handwriting or non-English OCR, annotation, collaboration, multi-user
  tenancy, production queue, or arbitrary connector marketplace.
- No shared package extraction until a second maintained repository adopts the
  seam and supplies a consumer integration check.
- No “finished product” claim beyond this private single-operator internal
  product boundary.

## Progress and stop rules

Each slice leaves a pushed coherent checkpoint and updates this plan when an
observed result changes a downstream contract. Switch tactics when two
consecutive increments do not improve the Project Aster workflow. Stop only for
a materially different product scope, new publication/authority boundary, or
provider spend beyond the existing bounded real canary.
