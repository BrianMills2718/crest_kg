# CREST Knowledge Graph

This repository preserves experiments over CIA CREST and UFO Reading Room
material. `crest_pipeline.py` is the canonical extraction path. The older
numbered scripts are retained as historical code; their downloaded inputs,
progress snapshots, and generated visualizations remain in the local archive
but are excluded from Git because they are reproducible or redundant artifacts.

The initial Git history intentionally tracks the canonical prompt and tests,
the exact five-document source corpus, and the validated graph. This keeps the
grounded result independently checkable without committing the full 108 MB
working archive.

## What the canonical path guarantees

- The corpus file is explicit, and document selection is sorted by stable
  CREST/FOIA identifiers.
- Model responses are validated as strict Pydantic structures by the shared
  `llm_client` structured-output boundary.
- Every entity and relationship must cite a bounded numbered source-line range;
  the pipeline materializes the exact original quote and character offsets.
- V2 relationships retain exact source, predicate, and target spans;
  whole-token endpoint binding and lexical predicate checks reject pronouns,
  clipped endpoints, punctuation predicates, and unsupported direction words.
- Provider responses use a compact portable schema, then pass item-level strict
  conversion with every dropped candidate recorded in a rejection ledger.
- Entity identity includes semantic type, so a location and organization with
  the same name cannot be silently collapsed.
- A graph cannot be written with duplicate IDs, dangling relationships, unknown
  provenance documents, or ungrounded assertions.
- Existing output is never overwritten unless `--force` is explicit.

## Inspect the deterministic five-document selection

This command is offline and does not call a model:

```bash
python crest_pipeline.py inspect-corpus \
  --corpus cia_documents/disinformation_complete_20250517_002848.json \
  --limit 5
```

The manifest reports each source ID, URL, full-text SHA-256, total character
count, and the exact analyzed character and line window.

## Run an extraction

Extraction uses the workspace's shared `llm_client`, its `graph_building` model
route, structured output, traces, and cost ledger. A positive total dollar
ceiling is mandatory:

```bash
python crest_pipeline.py extract \
  --corpus cia_documents/disinformation_complete_20250517_002848.json \
  --limit 5 \
  --max-chars 15000 \
  --max-budget-usd 1.00 \
  --output cia_kg_output/validated_5_documents.json
```

The command keeps all five calls under one root budget scope and writes only
after every document has passed structured and evidence validation. The default
15,000-character source window is recorded in the output rather than hidden.
Use `--refine-relationships` for the precision-first relationship-only stage.
Interrupted successful calls can be reused with `--resume-trace-id` and
`--resume-relationship-trace-id`; their selected-attempt receipts and costs are
embedded in the graph. `--prior-observed-cost-usd` and
`--unattributed-cost-reserve-usd` keep earlier failed or interrupted work inside
one aggregate authorization rather than resetting the budget on resume.

Validate an artifact independently:

```bash
python crest_pipeline.py validate \
  --graph cia_kg_output/validated_5_documents.json
```

## Hosted evidence viewer

The audited relationship-binding v2 checkpoint has a read-only browser surface
at <https://brian-mac-mini.tail9c321e.ts.net/crest/>. It defaults to the five
entities connected by the three accepted relationships, exposes all 82
extracted entities separately, and lets every accepted edge step down to its
exact source quote and grounding spans.

The viewer deliberately retains the evaluation boundary: it is an exploratory
five-document checkpoint with unknown corpus recall, not a complete CREST map.
Its container and Mac mini promotion/rollback contract are documented in
[`docs/MAC_MINI_DEPLOYMENT.md`](docs/MAC_MINI_DEPLOYMENT.md).

## Verified vertical

The canonical path was exercised against the explicit five-document selection
on 2026-08-20:

- artifact: `cia_kg_output/validated_5_documents.json`
- root trace: `crest_kg/extraction/20260820-line-grounded-five-document`
- resolved model: `openrouter/minimax/minimax-m3`
- observed successful-run cost: `$0.03924106`
- result: 5 documents, 91 entities, and 79 relationships
- integrity: 0 duplicate IDs, 0 dangling relationships, and 0 ungrounded
  relationships

An independent replay also matched all five source hashes and all 177 entity
and relationship evidence spans back to the original corpus text.

## Semantic relationship audit

Structural grounding did not imply semantic relationship quality. An
agent-adjudicated census of all 79 emitted relationships found 44 (55.7%) that
were both fully supported by their cited quote and faithful in endpoints,
predicate, direction, and types. Thirteen were unsupported, 19 partially
supported, and one indeterminate. The artifact therefore fails the frozen 90%
scale-unchanged gate even though all integrity checks above still pass.

Run the deterministic audit:

```bash
python crest_relationship_eval.py
```

See [`evaluation/README.md`](evaluation/README.md) for the decision rule,
case-set provenance, exact readout, limitations, and the cross-project reuse
boundary. This is transparently agent-adjudicated and output-conditioned; it
does not claim human review or corpus relationship recall.

## Relationship-binding v2 development checkpoint

The v2 path was authentically exercised and then rebuilt provider-free from
strict selected-attempt receipts:

- artifact: `cia_kg_output/validated_5_documents_relationship_binding_v2.json`
- primary trace: `crest_kg/extraction/20260820-relationship-binding-v2i`
- relationship trace: `crest_kg/extraction/20260820-relationship-binding-v2k`
- primary model: `gemini/gemini-2.5-flash-lite`
- relationship model: `gemini/gemini-2.5-flash`
- result: 5 documents, 82 entities, 3 relationships, and 72 explicit candidate
  rejections
- known observed spend across the full interrupted effort: `$0.05298666`
- conservative interrupted-call reserve: `$0.01307078`
- accounted total under the `$0.10` authorization: `$0.06605744`

The candidate-visible, agent-authored census in
`evaluation/relationship_quality_set_v2.json` labels all three emitted edges as
fully supported and faithful. Its deterministic scorer mechanically satisfies
the frozen 90%/zero-unsupported threshold and all four corruption controls.
Independent decision sign-off nevertheless rejected calling this a semantic
gate pass: the guard was iterated on these same five documents, only two
documents emitted any edge, there is no held-out same-class set or yield
safeguard, and corpus recall remains unmeasured. The permitted claim is only
that the fixed artifact's three edges were independently source-replayed and
then adjudicated 3/3 supported. See
`evaluation/eval_decision_signoff_v2.md` for the full verdict.

Reproduce the exact v2 readout:

```bash
python crest_relationship_eval.py \
  --graph cia_kg_output/validated_5_documents_relationship_binding_v2.json \
  --quality-set evaluation/relationship_quality_set_v2.json \
  --fail-on-threshold
```

## Focused verification

```bash
python -m pytest -q tests/test_crest_pipeline.py tests/test_crest_relationship_eval.py
```

The focused suite covers deterministic selection, rejection of dangling
relationships, exact line-to-character evidence grounding, typed identity, five-document graph
integrity, serialization round-tripping, overwrite refusal, frozen semantic
audit binding, complete adjudication coverage, and corruption detection.
