# CREST relationship-binding v2 evaluation decision sign-off

## Decision under review

Treat CREST relationship-binding v2 as passing its emitted-relationship
semantic-precision gate and publish it as a development checkpoint, without
recall or wider-corpus claims.

## Evaluated snapshot

- Source revision: `a68a6f5184edda44f10578d7e7a587f343fd0082`
- Graph SHA-256: `1abae3739b7a32f01d83814ac9b68a755403b7cba2e00355084f5f15f4fe5837`
- Quality-set SHA-256: `31fbc1547cadd73715344ccbb86c29e1d3c40c097e58b9d8feb3597effde767a`
- Reproduced report SHA-256: `c80d9d0ae9cdefb35c5672457df91f6de8111913f3f187fe6029fde57424df46`

## Verdict: REJECTED

The raw code and artifact may be retained as an explicitly exploratory
development checkpoint. The post-fix semantic gate-pass claim is unsigned and
must not be used to justify scaling the extractor unchanged.

### Gate 1 — validity: PASS

`crest_pipeline.py validate` returned `valid crest-kg-v2: 5 documents, 82
entities, 3 relationships`. The evaluator rerun exited zero and reproduced the
saved report byte-for-byte. Source replay confirmed all three body hashes,
offsets, quotes, and exact grounding fragments. The known-good grounding
control passed and the focused suite returned 28 passed.

### Gate 2 — representativeness: FAIL

The census is complete only for the literal three-edge frozen population. It is
candidate-visible and output-conditioned, covers only two of five documents,
and two edges share the same quote and predicate. No held-out same-class cases
exist. Emissions collapsed from the prior 79-edge five-document artifact to
three edges, while the rule has no yield or coverage safeguard, so precision
can improve through abstention.

### Gate 3 — diagnosis: PASS

`evaluation/README.md` identifies class-level failures: clipped endpoint
evidence, predicates stronger than quoted wording, lost third-party
attribution, and type errors. The lexical predicate guard targets one
identified class mechanism.

### Gate 4 — generalization: FAIL

The v2k run emitted six relationships at `2026-08-21T01:15:15Z`; commit
`a68a6f5` added the predicate guard at `01:20:29Z` after that candidate existed.
The v2l and final artifacts replayed the exact v2k relationship-response hashes,
removed three known failing edges, and introduced no unseen outputs; the three
survivors are byte-identical. The three-case adjudication was authored at
`01:22:10Z`. No fresh held-out run, same-class reproduction, or semantic
regression/yield check exists. Passing unit tests authored with the fix do not
satisfy this gate.

### Gate 5 — decision: FAIL

The 90%/zero-unsupported threshold predates v2, but it was originally tied to
the scale-unchanged decision and lacks protection against emission collapse.
Calling the artifact a development checkpoint lowers the action's stakes but
does not repair gates 2 and 4.

## Permitted claim

The frozen three-edge artifact was independently source-replayed and its
candidate-visible, agent-authored census labeled 3/3 emitted relationships as
supported. This is a descriptive fixed-artifact result, not a semantic gate
pass, a recall result, or evidence of wider-corpus generalization.

## Required evidence for a future gate pass

Freeze unseen documents and same-class accept/reject cases before further
changes; add a precommitted yield/coverage safeguard or source-first
denominator; run v2 fresh without tuning on those cases; independently
adjudicate the emitted population blind to candidate/version; and demonstrate
the threshold, zero unsupported edges, same-class reproduction, and no
regression across other failure classes.
