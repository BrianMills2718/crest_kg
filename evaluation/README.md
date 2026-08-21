# CREST evaluation evidence

This directory contains two deliberately bounded evaluation lines: the
deterministic passage-retrieval regression/sign-off used by the evidence
workbench, and the semantic quality census for the canonical five-document
CREST graph. Both use agent-authored evidence and state that limitation; neither
is described as human-labeled or independent expert review.

## Deterministic evidence-retrieval gate

`evidence_retrieval_set_v1.json` was the original three-case preregistered
Project Meridian fixture. It was useful for plumbing but too small to support a
ship decision. Independent execution repeatedly rejected revisions v1-v4 when
fresh cases exposed contextual absent-subject false positives and the design
incorrectly made retrieval decide whether every requested detail was answered.

The resulting contract separates the concerns:

- retrieval admits exact subject context and ranks exact source slices;
- a genuinely different or absent structural subject must not borrow shared
  predicate/detail words;
- answerability, contradiction, and uncertainty belong to the downstream
  citation-valid brief rather than the lexical ranker.

Every independently observed retrieval or chunk-boundary failure was frozen
before its repair. Fixtures v5-v16 therefore form a cumulative, agent-authored
repair regression set rather than a blind or human gold set. Their sign-off
artifacts are retained, including rejected candidates, so later readers can see
why each contract was added rather than treating the final green run as the only
history.

The decision-bearing record is
`evidence_retrieval_decision_signoff_v17.md`. A fresh verifier froze 8 new
retrieval cases and 4 new chunking/source-byte cases before inspecting the
candidate. On exact runtime revision
`d884f493a73bc289bcbbc72399294aa77cdd4ce4`:

- all 12 frozen fixtures v5-v16, totaling 99 cases, passed twice with valid
  exact offsets and byte-identical aggregate output;
- all 12 fresh verifier cases passed twice with byte-identical output;
- the complete repository suite passed 51 tests;
- JavaScript syntax and Python dependency checks passed.

The v17 verdict is **PASS — SIGNED-OFF** only for deterministic passage
admission, ranking, chunking, and exact offsets in small synthetic collections.
It does not establish arbitrary question parsing, real-corpus recall,
answer-status correctness, semantic entailment, or production-scale behavior.

Run one frozen fixture deterministically:

```bash
python evaluation/run_evidence_retrieval_eval.py \
  --fixture evaluation/evidence_retrieval_set_v16.json
```

## Relationship-quality decision and claim

The bounded decision is whether the current extraction can be scaled unchanged
to more CREST documents.

The falsifiable claim is:

> At least 90% of emitted directed relationships are fully supported by their
> exact cited quote, use the right endpoints, predicate and direction, and give
> both endpoints plausible types; no emitted relationship is unsupported.

The unit of review is one emitted relationship. The population is a census of
all 79 relationships in
`cia_kg_output/validated_5_documents.json`, not a sample. The reviewer inspected
the exact evidence quote embedded in the graph and separately judged:

- source support;
- endpoint fidelity;
- predicate fidelity;
- direction fidelity; and
- endpoint type fidelity.

The candidate output was visible to the reviewer, so this set can estimate the
precision and fidelity of the frozen emitted population but cannot establish
corpus recall. A source-first expected-relationship inventory would be required
for that different claim.

## Relationship-quality artifacts

- `relationship_quality_set_v1.json` — frozen judgments, rationales, graph
  digest, assertion fingerprints, and the precommitted decision rule.
- `relationship_quality_report_v1.json` — deterministic aggregate readout.
- `relationship_quality_set_v2.json` and `relationship_quality_report_v2.json`
  — exploratory v2 emitted-population census and readout.
- `eval_decision_signoff_v2.md` — independent execution-based decision review;
  it rejects treating the descriptive v2 census as a semantic gate pass.
- `../crest_relationship_eval.py` — strict loader, binding checks, scorer, and
  negative controls.

Run the exact offline evaluation:

```bash
python crest_relationship_eval.py \
  --out evaluation/relationship_quality_report_v1.json \
  --force
```

Add `--fail-on-threshold` when using the result as a gate. A failed quality
threshold then returns status 1; malformed inputs or broken binding return
status 2.

## Result

The frozen artifact fails the precommitted scale-unchanged gate:

| Measure | Result |
| --- | ---: |
| Relationships reviewed | 79 |
| Fully supported and faithful | 44 (55.7%) |
| Supported, including type defects | 46 |
| Partially supported | 19 |
| Unsupported | 13 |
| Indeterminate | 1 |
| Endpoint fidelity pass | 57 (72.2%) |
| Predicate fidelity pass | 50 (63.3%) |
| Direction fidelity pass | 65 (82.3%) |
| Type fidelity pass | 76 (96.2%) |
| Corruption controls detected | 4 of 4 |

The largest recurring failure families are clipped citations that do not bind
both endpoints, predicates stronger than the quoted wording, binary edges that
lose a third participant (for example, who was alleged to have caused an
event), and a few report/program type errors. The worst source document is
`cia-rdp70-00058r000300020010-5`, where only 6 of 17 edges are fully faithful;
its OCR and column ordering make short evidence windows especially ambiguous.

This does not invalidate the artifact's already-verified structural properties:
the graph remains schema-valid, referentially closed, source-hash-bound, and
exactly quoted. It shows that structural grounding is necessary but not enough
for semantic edge correctness.

## V2 exploratory readout

`../cia_kg_output/validated_5_documents_relationship_binding_v2.json` is the
precision-first development checkpoint. Its complete agent-authored census is
`relationship_quality_set_v2.json`, with deterministic output in
`relationship_quality_report_v2.json`.

The deterministic scorer mechanically satisfies its emitted-population rule:
3 of 3 relationships are labeled fully supported and faithful, zero are
unsupported, and all four corruption controls fire. This is only a descriptive
fixed-artifact census. Independent sign-off in
`eval_decision_signoff_v2.md` rejects the semantic gate-pass claim because
predicate guards were revised after inspecting failures on this same
five-document population, only two documents emit any relationship, there is
no held-out same-class test, no yield safeguard, and no source-first recall
denominator.

Reproduce it with:

```bash
python ../crest_relationship_eval.py \
  --graph ../cia_kg_output/validated_5_documents_relationship_binding_v2.json \
  --quality-set relationship_quality_set_v2.json \
  --fail-on-threshold
```

## Cross-project reuse

The reusable architecture already has clear owners:

1. Consumer repositories own their source corpus, adapter, frozen labels or
   retrieval fixtures, and decision readout. CREST keeps its subject parsing,
   ranking, and Project Meridian cases local. The reusable pattern is to freeze
   exact failures before repair, retain rejected sign-offs, and require fresh
   decision cases; it should become shared code only when a second maintained
   consumer needs the same typed contract.
2. `onto_canon6` owns domain-neutral knowledge-graph assertion and extraction
   quality semantics. Its existing benchmark models already separate source
   support, structural validity, canonical fidelity, and accepted alternatives.
   If a second graph project needs this exact census contract, the typed
   `RelationshipQualitySet` and deterministic scorer should move there rather
   than be copied.
3. `prompt_eval` owns prompt/model variant experiments over frozen case sets and
   can compare candidate extractor runs once a source-first case set exists.
4. `trace_eval` owns stage and cascade diagnosis for multi-stage pipelines; it
   should not be used for this single-output semantic census.
5. `llm_client` remains the execution, trace, cost, and observability layer.

That gives cross-project reuse without creating another evaluation platform.
The portable seam proven here is a typed, hash-bound adjudication record plus a
deterministic scorer and mandatory corruptions. The project-specific graph
adapter and labels remain local.

## Limitations

- The adjudicator was an agent and saw the candidate graph; the set is not
  blind or human-authored.
- Semantic labels are reasoned judgments. The corruption controls prove the
  mechanical binding and census checks, not the correctness of those judgments.
- The set cannot measure omitted relationships or generalize beyond these five
  documents.
- A later promotion, model-selection, or high-stakes publication decision
  should obtain an independent adjudication pass over a frozen subset or the
  full census.
