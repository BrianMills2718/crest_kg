# CREST evidence-retrieval decision sign-off v12

## Evaluation identity and pre-execution probe contract

- Decision: ship or reject passage retrieval for the current small synthetic
  research-collection boundary.
- Exact code revision under evaluation:
  `f56456ab93510753f964b1a4b7a7881301cb6ffb`.
- Verifier: fresh independent `eval-decision-signoff` agent. This contract was
  frozen before importing or executing `crest_app.retrieval`, before running any
  frozen fixture, and without opening v5-v12 fixture contents or any prior
  sign-off artifact.
- Scope: deterministic passage admission, ranking, source identity, and exact
  offsets. This contract does not require arbitrary natural-language semantic
  parsing or answer classification by the ranker. In particular, a question
  about an absent detail should still retrieve a passage when its collection
  subject is present; a question whose asserted external subject is absent
  should retrieve nothing even if it also contains a real location or generic
  retrieval words.

### Fresh synthetic collections

The primary collection uses five one-passage documents. Each `body_text` is
exactly two leading newlines, the displayed passage, then one space and one
newline. Consequently the predeclared exact spans are:

| document id | title | passage | exact span |
| --- | --- | --- | --- |
| `fresh-alder` | Alder Archive Note | `The Alder Institute coordinated Project Saffron in Cordoba. The field rehearsal opened on 22 September. Copper gauges recorded rainfall.` | `[2, 138)` |
| `fresh-morrow` | Morrow Laboratory File | `The Morrow Laboratory managed Project Thistle in Bergen. The pilot began on 4 November. Silver instruments measured pressure.` | `[2, 127)` |
| `fresh-vesper` | Vesper Committee Record | `The Vesper Committee convened Project Lantern in Dakar. The demonstration started on 7 April. Glass equipment tracked wind.` | `[2, 125)` |
| `fresh-juniper` | Juniper Agency Brief | `The Juniper Agency staged Project Kestrel in Kyoto. The exercise commenced on 18 June. Ceramic instruments logged humidity.` | `[2, 125)` |
| `fresh-rowan` | Rowan Team Note | `The Rowan Team supervised Project Harbor in Cordoba. The trial started on 3 March. Bronze equipment logged soil temperature.` | `[2, 126)` |

The isolated ordering collection has documents `order-02` then `order-01` in
input order. Both use title `Twin Committee Register` and body text consisting
of two newlines, `The committee organized the demonstration.`, one space, and
one newline. Both exact spans are `[2, 44)`. This deliberately makes their
scores equal so the documented `document_id` tie-break must return `order-01`
before `order-02`, independently of input order.

### Fresh cases and predeclared grading

Unless stated otherwise, `top_k=1`; the required result is exactly the listed
document-id vector. Any additional document, wrong order, wrong span, source
slice mismatch, or nondeterministic serialization fails its case.

| id | class | query | required ids |
| --- | --- | --- | --- |
| `P01` | answerable paraphrase | Which institute coordinated the Saffron rehearsal? | `[fresh-alder]` |
| `P02` | answerable paraphrase | When did the Thistle pilot commence? | `[fresh-morrow]` |
| `P03` | answerable paraphrase | What equipment did Lantern use to track wind? | `[fresh-vesper]` |
| `P04` | answerable paraphrase | When was the Harbor trial opened? | `[fresh-rowan]` |
| `O01` | arbitrary OOV discourse/verb | Could you zorbishly recount who coordinated Project Saffron? | `[fresh-alder]` |
| `O02` | arbitrary OOV modifier/verb | Inexplicably, did Alder florp the Saffron demonstration? | `[fresh-alder]` |
| `O03` | arbitrary OOV discourse/modifier | Please quazzle how the Morrow Laboratory inscrutably began Thistle. | `[fresh-morrow]` |
| `F01` | possessive form | What date did Vesper's Lantern demonstration start? | `[fresh-vesper]` |
| `F02` | Project form | When did Project Thistle open? | `[fresh-morrow]` |
| `F03` | source-head form | What does the Alder archive note report about rainfall? | `[fresh-alder]` |
| `F04` | event-head form | Which date did the Lantern demonstration start? | `[fresh-vesper]` |
| `F05` | auxiliary form | Did Juniper stage the Kestrel exercise? | `[fresh-juniper]` |
| `F06` | who form | Who convened Project Lantern? | `[fresh-vesper]` |
| `F07` | leading-copula form | Was Morrow responsible for Thistle's pilot? | `[fresh-morrow]` |
| `F08` | leading-copula form | Is Rowan the team that supervised Harbor? | `[fresh-rowan]` |
| `R01` | `for`, postposed subject | When did the rehearsal for Saffron begin? | `[fresh-alder]` |
| `R02` | `for`, fronted subject | For Thistle, when did the pilot begin? | `[fresh-morrow]` |
| `R03` | identity `associated with` | Which equipment was associated with Lantern? | `[fresh-vesper]` |
| `R04` | identity `connected with`, fronted | Connected with Kestrel, which agency staged the exercise? | `[fresh-juniper]` |
| `R05` | `under` plus Project form, fronted | Under Project Kestrel, when did the exercise commence? | `[fresh-juniper]` |
| `R06` | `under`, postposed second exact subject | Who coordinated Project Saffron under Alder? | `[fresh-alder]` |
| `R07` | plain `with` is not an identity relation | For Project Saffron, what happened with titanium badges? | `[fresh-alder]` |
| `R08` | `under` scopes an absent requested detail, not a subject | For Project Saffron, what was recorded under insurance policy Nimbus? | `[fresh-alder]` |
| `R09` | `under`, postposed exact subject | When did the Saffron rehearsal begin under Alder? | `[fresh-alder]` |
| `T01` | named transposition with exact anchor | Who coordinated Project Saffron for Aldre? | `[fresh-alder]` |
| `T02` | named transposition with exact anchor | When did Project Thitsle begin in Bergen? | `[fresh-morrow]` |
| `T03` | named transposition with exact anchor | Who convened Project Lantner in Dakar? | `[fresh-vesper]` |
| `T04` | typo safety control without exact anchor | When did Project Thitsle begin? | `[]` |
| `N01` | absent external Project subject | When did Project Nimbus begin? | `[]` |
| `N02` | absent external `for` subject | Who organized the rehearsal for Talon? | `[]` |
| `N03` | absent external identity subject | Was the equipment associated with Onyx? | `[]` |
| `N04` | absent external `under`, fronted | Under Marigold, when did the pilot begin? | `[]` |
| `N05` | absent external `under`, postposed | When did the rehearsal begin under Marigold? | `[]` |
| `N06` | absent Project subject plus real location | For Project Nimbus in Cordoba, what equipment was supplied? | `[]` |
| `N07` | absent Project subject plus real source anchor | What did the Alder archive report for Project Nimbus? | `[]` |
| `C01` | present subject, absent context-rich details | For Project Saffron in Cordoba, what insurance carrier, badge color, and catering vendor were recorded? | `[fresh-alder]` |
| `C02` | present possessive subject, absent details | In Bergen, what was Thistle's insurance policy number and lunch menu? | `[fresh-morrow]` |
| `C03` | present possessive/event subject, absent details | Which unlisted locksmith and radio frequency accompanied Lantern's Dakar demonstration? | `[fresh-vesper]` |
| `D01` | deterministic equal-score ordering (`top_k=2`) | Which committee organized the demonstration? | `[order-01, order-02]` |

The fresh suite therefore has 39 cases: 4 answerable paraphrases, 3 OOV
variants, 8 structural-form probes, 9 relation-scoping probes, 4 typo probes,
7 absent-subject negatives, 3 context-rich absent-detail positives, and 1
equal-score ordering probe. Every returned chunk must additionally satisfy both
the exact predeclared span for its document and
`body_text[start_char:end_char] == text`. The entire fresh result object will be
serialized with sorted JSON keys and executed twice; the two byte streams must
be identical.

## Execution evidence

All commands ran from
`/home/brian/code/crest_kg/worktrees/codex-crest-evidence-synthesis-week` with
HEAD still at `f56456ab93510753f964b1a4b7a7881301cb6ffb`. The only working-tree
change during execution was this untracked sign-off record; product code and
fixtures remained identical to HEAD.

### Fresh contract, two runs

The contract above was materialized as the transient runner
`/tmp/crest_fresh_signoff_v12.py` (SHA-256
`f51f4550ac5792a61b705825deb75dd58fc49fafdf6d6e5b8f4e3189ef06e6bc`).
It constructed the displayed documents directly, called `rank_evidence`,
compared exact ID vectors, checked every returned chunk against the predeclared
span/text/title and its source slice, and emitted sorted-key JSON. Exact command:

```bash
set +e
PYTHONPATH=. .venv/bin/python /tmp/crest_fresh_signoff_v12.py > /tmp/crest_fresh_signoff_v12_run1.json
run1_status=$?
PYTHONPATH=. .venv/bin/python /tmp/crest_fresh_signoff_v12.py > /tmp/crest_fresh_signoff_v12_run2.json
run2_status=$?
cmp -s /tmp/crest_fresh_signoff_v12_run1.json /tmp/crest_fresh_signoff_v12_run2.json
cmp_status=$?
```

Observed: `run1_status=1`, `run2_status=1`, and `cmp_status=0`. Both JSON files
had identical SHA-256
`035c52274e08329eb4aeeb934c4580a2d92a1d95f3d8fd592047b8c972deb5f6`.
Each run passed **38/39** cases. Category counts were P 4/4, O 3/3, F 8/8,
R 9/9, T 3/4, N 7/7, C 3/3, and D 1/1.

The sole failure was predeclared case `T03`:

```text
query:        Who convened Project Lantner in Dakar?
expected:     [fresh-vesper]
actual:       []
```

The failure is mechanistic. `_structural_subject_surfaces` correctly extracted
`lantner`, and the exact anchor `Dakar` was present, but `_best_fuzzy("lantner",
("lantern",))` returned `0.8571428571428571`, below the fixed admission threshold
of `0.86`. Thus an anchored, same-length benign name permutation suppressed the
otherwise relevant passage. This is passage admission, not a demand that the
ranker classify whether the requested answer exists.

All **31/31 returned-chunk offset checks** passed. Observed exact spans were
`fresh-alder [2,138)`, `fresh-morrow [2,127)`, `fresh-vesper [2,125)`,
`fresh-juniper [2,125)`, `fresh-rowan [2,126)`, and both ordering documents
`[2,44)`. Every source slice, chunk text, title, and declared span matched.
`D01` returned `[order-01, order-02]` even though input order was reversed, and
the complete fresh outputs were byte-identical across runs.

### Frozen v5-v12, two runs each

Exact command:

```bash
set +e
for version in 5 6 7 8 9 10 11 12; do
  fixture="evaluation/evidence_retrieval_set_v${version}.json"
  out1="/tmp/crest_frozen_v${version}_run1.json"
  out2="/tmp/crest_frozen_v${version}_run2.json"
  PYTHONPATH=. .venv/bin/python evaluation/run_evidence_retrieval_eval.py --fixture "$fixture" > "$out1"
  status1=$?
  PYTHONPATH=. .venv/bin/python evaluation/run_evidence_retrieval_eval.py --fixture "$fixture" > "$out2"
  status2=$?
  cmp -s "$out1" "$out2"
  cmp_status=$?
done
```

| fixture | run 1 | run 2 | byte compare | cases passed |
| --- | ---: | ---: | ---: | ---: |
| v5 | 0 | 0 | 0 | 9/9 |
| v6 | 0 | 0 | 0 | 5/5 |
| v7 | 0 | 0 | 0 | 6/6 |
| v8 | 0 | 0 | 0 | 7/7 |
| v9 | 0 | 0 | 0 | 12/12 |
| v10 | 0 | 0 | 0 | 29/29 |
| v11 | 0 | 0 | 0 | 13/13 |
| v12 | 0 | 0 | 0 | 2/2 |

Frozen total: **83/83** passed on each run. Every per-version `cmp` returned 0.

### Repository checks and mechanism inspection

Exact commands and outcomes:

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
# 50 passed, 1 Starlette/httpx deprecation warning in 4.12s

node --check web/app.js
# exit 0, no stdout/stderr

git diff --find-renames --find-copies \
  19e4c34..f56456ab93510753f964b1a4b7a7881301cb6ffb -- \
  crest_app/retrieval.py tests/test_evidence_retrieval.py \
  evaluation/run_evidence_retrieval_eval.py \
  evaluation/evidence_retrieval_set_v12.json
```

The production delta is a generic grammar change, not instance memorization:
it adds `under` to subject boundaries and admits `under` through the same
structural relation path as `for`. No fixture entity or sentence literal occurs
in production code. The new frozen fixture adds one answerable and one absent
external-subject `under` case; the test only registers v12. The mechanism
generalized beyond that sentence: all six materially different fresh `under`
placements/scopes (`R05`, `R06`, `R08`, `R09`, `N04`, `N05`) passed, and all
81 pre-v12 frozen cases remained green. The targeted `under` repair therefore
generalizes, but it does not cure the independently exposed anchored-name
admission boundary.

## Gate assessment and decision

**EVAL-DECISION SIGN-OFF**

- decision: ship CREST passage retrieval for the small synthetic research
  collection boundary
- eval: exact code revision
  `f56456ab93510753f964b1a4b7a7881301cb6ffb`; frozen v5-v12 plus the
  pre-execution fresh contract above
- verdict: **REJECTED**
- gate 1 validity: **PASS** — authentic local retrieval imports and execution
  worked; positive controls returned correct passages; frozen v5-v12 passed
  83/83 twice; 50 repository tests and JavaScript syntax passed. No dependency,
  fixture, index, or service was unavailable.
- gate 2 representativeness: **PASS** — the fresh corpus is independent of the
  frozen entity set and covers answerable paraphrases, absent external
  subjects, arbitrary OOV language, all requested structural forms, multiple
  relation words and placements, anchored typos, absent requested details,
  equal-score ordering, and exact offsets without requiring answer
  classification or unrestricted semantic parsing.
- gate 3 diagnosis: **PASS** — the failure is class-level and executable:
  structurally admitted, exactly anchored name variants are still rejected when
  their similarity falls narrowly below the global `0.86` gate. `T03` is the
  held-out witness; its measured score is `0.8571428571428571`.
- gate 4 generalization: **PASS** for the targeted `under` repair — v12 passed
  2/2, six fresh varied `under` probes passed, and frozen v5-v11 stayed 81/81.
  The code delta is a generic relation-grammar change rather than an
  entity/query special case.
- gate 5 decision: **FAIL** — ship cannot fire on a predeclared representative
  contract with a genuine failed case, even though the targeted `under` repair
  itself generalized and all frozen fixtures passed.

Limits: this sign-off establishes deterministic local behavior only for the
small synthetic passage-retrieval boundary. It does not establish real-world
recall, arbitrary question understanding, answer generation/classification, or
production service behavior.

**Ship recommendation: do not ship revision
`f56456ab93510753f964b1a4b7a7881301cb6ffb` as the accepted retrieval
boundary.** Repair the exact-anchor-assisted named-variant admission mechanism
at the class level, freeze the failure before repair, preserve the current
`under` behavior, and require another fresh independent sign-off.
