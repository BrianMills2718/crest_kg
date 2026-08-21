# CREST seven-day evidence-synthesis increment

Status: completed and deployed 2026-08-21
Owner: Brian Mills (product) / repository automation (implementation)
Planned window: 2026-08-20 through 2026-08-27; completed early
Stage: private single-operator internal product
Canonical surface: <https://brian-mac-mini.tail9c321e.ts.net/crest/>

## Outcome

A researcher can ask a natural-language question over one persistent collection,
inspect the exact passages CREST ranked, generate a persistent evidence brief
whose findings cite those passages, see support, contradiction, and uncertainty
without silent synthesis, and hand the cited sources into the existing focused
graph builder. Refresh or service restart must not strand the question, brief,
or graph.

The canonical observation is **Project Meridian**. The operator creates that
collection and adds four short field documents: one names the organizing body
and a preliminary launch date, one records a different observed launch date and
distinguishes convening from operational leadership, one is a same-project
Lisbon distractor, and one contains unrelated budget administration. The
operator asks:

> Which group organized the Austrian field demonstration, and what date
> disagreement exists?

The workbench must rank exact Vienna passages from the first two documents,
exclude the Lisbon distractor from the selected evidence, produce a traced brief
that identifies the organizing body while preserving the role ambiguity and
the 14/16 May contradiction, expose exact source passages, select the cited
documents for a collection-guarded graph build, and recover both completed
artifacts after refresh.

Passing proves this exact question-to-evidence-to-graph workflow at the named
revision and deployment. It does not prove semantic recall across arbitrary
corpora, factual correctness beyond supplied sources, citation entailment,
production orchestration, or public multi-user readiness.

## Completion readout

All five slices below are complete on runtime revision
`d884f493a73bc289bcbbc72399294aa77cdd4ce4`, independently signed off by
artifact commit `677a441e13ccc4c4be0a6c5305a55b9ce23e4bd8`, and deployed at the canonical
surface.

- Retrieval: deterministic exact-offset passage chunks, stable scoring details,
  collection isolation, and operator-only preview.
- Inquiry: atomic persistent lifecycle, ranked evidence snapshots,
  citation-validation failure, shared serial provider execution, trace/cost
  receipts, and restart recovery.
- Brief: support, contradiction, uncertainty, unresolved questions, exact
  citations, and an explicit insufficient-evidence path.
- Handoff: at most three cited collection members may enter the existing graph
  builder, with inquiry provenance retained on the graph request.
- Browser: Ask collection, evidence preview, bounded brief authorization,
  passage/source inspection, Recent activity, cited-source handoff, graph
  exploration, and refresh/restart recovery.
- Operations: isolated candidate, authentic provider traces, external-anonymous
  privacy denials, exact image promotion, unchanged Funnel route, stopped
  rollback container, and canonical restart/reopen proof.

The authoritative runtime receipt is
[`deployments/2026-08-21-mac-mini-crest-evidence-synthesis.md`](deployments/2026-08-21-mac-mini-crest-evidence-synthesis.md).

## Current-to-target delta

CREST already owns durable sources, collections, lexical document search,
one-to-three-document graph extraction, evidence inspection, job recovery, and
private-source authorization. This increment extends those seams rather than
creating a second catalog, model client, job store, or graph pipeline.

```text
collection documents
  -> deterministic chunks + hybrid lexical/fuzzy ranking
  -> persisted inquiry with bounded evidence snapshot
  -> one structured llm_client evidence-brief call
  -> deterministic citation/reference validation
  -> cited-source handoff to existing GraphBuildRequest
  -> existing graph job, evidence inspector, and export
```

## Boundaries and rules

| Boundary | Owns | Required behavior |
| --- | --- | --- |
| Evidence retrieval | Deterministic chunking, score components, ranking, diversity, and exact offsets | Search only current collection members; retain exact text and stable chunk IDs; empty or weak evidence remains visible; never call a model. |
| Inquiry store | Question, collection snapshot, evidence snapshot, state, trace, cost, validated brief, and error | Atomic JSON; newest-first history; queued/running becomes explicit failed after restart; source/collection deletion does not rewrite historical evidence. |
| Brief generation | One structured model response over the retained evidence snapshot | Use shared `llm_client`; one root trace and request ceiling; no invisible fallback; late failure preserves ranked evidence. |
| Brief validation | Citation identity and state transition | Every cited chunk must exist in the inquiry snapshot; every finding has at least one citation; source IDs are system-derived; malformed or unknown citations fail the job. Semantic entailment is not claimed. |
| Provider execution | Serial ordering of brief and graph jobs | Evidence briefs and graph builds share one single-worker lane so two browser actions cannot spend concurrently. |
| Graph handoff | Inquiry provenance and cited-source eligibility | A handoff may select at most three unique cited documents; all must remain in the named collection; graph build retains optional inquiry ID provenance. |
| Browser workbench | Question entry, ranked evidence, brief states, history/reopen, exact passage inspection, and graph handoff | Initial, retrieving, queued, running, insufficient, failed, completed, and recovered states are legible using normal controls. |
| Authorization | Private inquiry and evidence boundary | Every inquiry route is operator-only; no private question, passage, brief, trace, or inquiry-derived graph crosses an anonymous response. |

Collection edits affect future inquiries only. A completed inquiry is a retained
research record containing a bounded evidence snapshot, so deleting an upload
or collection does not silently erase or mutate that historical brief. A new
inquiry always reads the current collection membership and source bodies.

## Typed contracts

- `EvidenceInquiryRequest`: collection ID, normalized question, evidence limit,
  per-document scan ceiling, output-token ceiling, and dollar ceiling.
- `EvidenceChunk`: stable content-derived ID, document/source identity, title,
  zero-based character offsets, exact text, rank, total score, and named score
  components.
- `BriefFinding`: one source-grounded statement, classification
  (`support | contradiction | uncertainty`), and one or more retained chunk IDs.
- `EvidenceBrief`: answer status (`answered | partial | insufficient`), concise
  synthesis, findings, unresolved questions, model, trace, and observed cost.
- `EvidenceInquiry`: stable ID and lifecycle
  (`queued | running | completed | failed`), request, collection title snapshot,
  ranked evidence, optional brief, timestamps, trace, error, and progress.
- `GraphBuildRequest.inquiry_id`: optional provenance/eligibility guard; when
  present, selected documents must be cited by the completed inquiry and belong
  to its collection.

All API models reject unknown fields. Inquiry IDs and evidence IDs are assigned
by the service, not accepted from model output.

## Retrieval evaluation lineage and decision

The agent-authored fixture at
`evaluation/evidence_retrieval_set_v1.json` was the initial deterministic
pre-registration. It is not a human gold set and is not evidence of real-world
representativeness. Independent fresh execution rejected the first four
decision attempts: those runs exposed contextual absent-subject admissions and
showed that retrieval had been incorrectly asked to decide whether a requested
detail was answered.

Claim: the implemented ranker can retrieve the decisive Project Meridian
passages despite light paraphrase, keep a same-project/location distractor below
the decisive evidence, preserve exact offsets, and return no evidence for a
query with no lexical/fuzzy support.

Decision: continue to the model-backed vertical only if the frozen ranker meets
the fixture contract without case-specific source IDs or phrases in production
code; otherwise revise the general scoring/chunking contract before any paid
call.

Case taxonomy and split:

- calibration: exact-term multi-document retrieval and exact offset recovery;
- holdout: paraphrased role/date question, same-project distractor pressure,
  and a genuinely absent-subject negative control;
- corruption control: a brief that cites an unknown chunk ID must fail
  validation even when its prose is plausible.

Primary gate: every expected decisive document appears in the configured top
four for each answerable case. Secondary gates: the named distractor is absent
from the top two where specified; chunk text equals its document character
slice; a genuinely absent structural subject returns zero chunks. Exact-subject
context remains retrievable even when extra requested details are absent;
answerability belongs to the brief. Results are reported per case because the
set is small. No aggregate percentage is used to imply corpus quality.

Every fresh failure was frozen before its repair. Fixtures v5-v16 now contain
12 cumulative repair sets and 99 cases. The independent v17 verifier added 8
fresh retrieval and 4 fresh chunk-boundary cases, then ran both frozen and fresh
suites twice. All cases passed with byte-identical output, exact offsets, 51
repository tests, valid JavaScript syntax, and a consistent Python environment.
The signed scope is deterministic passage retrieval over small synthetic
collections only; see
[`../evaluation/evidence_retrieval_decision_signoff_v17.md`](../evaluation/evidence_retrieval_decision_signoff_v17.md).

## External-call budget

- Evidence brief: one structured call, serial depth one, at most one
  `llm_client` structured-validation retry inside the same request ceiling.
- Focused graph: the existing one call per selected document, up to three
  documents, with relationship refinement off for the canonical observation.
- Shared concurrency: one provider worker across both job types.
- Context bound: at most six retained evidence chunks and the configured
  per-chunk character ceiling; the exact rendered prompt size is measured before
  the live canary.
- Canonical ceilings: `$0.06` for the evidence brief and `$0.10` for the graph;
  actual model, timing, tokens, cost, attempts, and validation events are read
  from the shared trace store.
- Retry/fallback: no model fallback; one structured retry may repair schema
  failure; terminal failure retains evidence and records the exact error.
- Checkpoints: inquiry JSON exists before the call; completed evidence is not
  recomputed on refresh; graph job remains independently recoverable.

## Risk-ordered slices

### Slice 1 — Question-to-ranked-evidence vertical

Implement typed chunks and deterministic hybrid ranking behind an operator-only
collection inquiry preview. Run the frozen retrieval fixture, positive/negative
controls, exact-offset check, and privacy denial. This is the first missing
boundary and must pass before a model call.

### Slice 2 — Persistent citation-valid brief

Persist inquiry lifecycle and evidence before submitting one structured
`llm_client` call. Validate citation identities, retain partial evidence on
failure, list/reopen history, and mark interrupted work failed after restart.
Use the existing shared client and add no second prompt/call unless an observed
failure proves one necessary.

### Slice 3 — Focused graph provenance handoff

Let the operator select up to three unique cited sources into the existing graph
builder. Carry `inquiry_id` through the request and reject a source that is not
cited, not in the inquiry collection, or no longer in current membership.

### Slice 4 — Browser workflow and recovery

Add one integrated research-question panel, evidence cards, support/
contradiction/uncertainty findings, exact-passage inspection, recent inquiries,
and the graph handoff. Reuse the current collection picker, graph build dock,
job history, graph explorer, and export.

### Slice 5 — Canonical integration and promotion

Run focused and full tests, retrieval evaluation sign-off, exact prompt/schema
preflight, one paid evidence-brief canary, one focused graph build, private-route
negative checks, a fresh canonical browser journey, candidate restart, exact
image promotion, route preservation, rollback retention, and immutable receipt.

## Compatibility, failure, and non-goals

Existing document search, collections, uploads, graph requests without
`inquiry_id`, job history, graph artifacts, URLs, and JSON export remain valid.
No backfill is required; the inquiry store begins empty alongside existing data.

No vector database, hosted embedding service, cross-collection global index,
automatic corpus-wide entity resolution, live CIA repair, annotation workflow,
collaboration, multi-user tenancy, production queue, semantic-entailment claim,
or generalized shared package is in scope. Extraction remains repository-local
until a real second maintained consumer exists.

## Course and stop rules

The stable Project Meridian browser journey owns the critical path. After one
non-visible increment, return to that journey unless a newly observed direct
blocker prevents it. Reversible implementation and fixture-authoring choices are
delegated. Stop only for materially different product scope, new external or
publication authority, or provider spend beyond the bounded canonical canary.
