# EVAL-DECISION SIGN-OFF

decision: Whether exact code revision `3f5510c268408648af89e4b514dc220d6a23f2fd` may proceed to isolated deployment under the narrow CREST passage-ranking contract.

eval: Frozen `evaluation/evidence_retrieval_set_v5.json` through `evaluation/evidence_retrieval_set_v10.json`, two-run determinism and exact offsets, focused and full tests, and a fresh precommitted 52-probe same-class suite. Context-rich absent-fact probes are explicitly ungraded because the evidence brief owns answered/partial/insufficient classification.

verdict: **REJECTED**

## Gates

gate 1 validity: **PASS** — The checkout was clean at the exact revision before execution. Python 3.12.3, all required imports, and dependencies were available. Frozen v5-v10 passed twice identically (68/68 cases), all returned offsets were exact, the focused suite passed 7 tests, and the full suite passed 50 tests.

gate 2 representativeness: **FAIL** — The frozen set passes completely, but unseen same-class probes pass only 8/18 answerable and 23/26 no-support cases. The fresh set covers targeted, function-only, discourse, case, benign-typo, lowercase/capitalized external-subject, fuzzy-collision, unrelated, and contextual absent-fact classes. Its 13 stable graded failures show that v5-v10 do not yet represent ordinary lexical variation within the advertised classes.

gate 3 diagnosis: **PASS** — The failures share three mechanisms. First, every out-of-lexicon content term is treated as a mandatory subject, so ordinary modifiers, verbs, and discourse leads (`within`, `ran`, `using`, `contrast`, `handled`, `claimed`, `explain`, `incidentally`, `follow-up`, `circle back`, `separately`, `contain`) suppress relevant passages. Second, the requested-detail exemption consumes an external subject before a known corpus anchor, so Borealis/Triton/Horizon are waived when Vienna/Austria follows. Third, one-pass suffix stemming is not morphologically stable: `document` becomes `docu`, while `documented` becomes `document`, causing the mixed-case answerable probe to acquire an unmatched target.

gate 4 generalization: **FAIL** — Frozen v5-v10 and all 50 repository tests pass, but the precommitted held-out suite has 13/44 graded failures: 10 false abstentions and 3 false admissions. All 52 probe outputs repeated identically and every returned source slice was exact. The repair fits the frozen failures but does not generalize to unseen surface forms in the same classes.

gate 5 decision: **FAIL** — This empirical gate is justified: subject admission is a central user-visible boundary, the proposed deployment depends on it, and executing deterministic probes is cheaper than deploying an invalid candidate. The explicit decision rule rejects on any graded failure; deployment must not proceed from this revision.

rejections / required fixes: Do not deploy `3f5510c`. Replace the open-ended “all non-function terms are subjects” rule with structural subject/request-slot handling; prevent requested-detail parsing from waiving an external named subject merely because a known collection anchor follows; and make morphological normalization idempotent across inflections. Freeze the 13 failures and obtain another independent sign-off after repair.

## Execution evidence

The ordered compact fresh-probe JSON was frozen and hashed before the first `rank_evidence` call: `fcaf101fadb61e5b64c47623b811202d5dfdbf0150a1c11e5924065cc498637a`. It contains 52 unique questions (18 answerable, 26 no-support, 8 contextual ungraded) and has no exact duplicates in frozen v5-v10. Pass rules were fixed first: answerable probes require both decisive documents in the top four and no Lisbon distractor in the top two; no-support probes require `[]`; contextual probes are ungraded; all outputs must repeat twice with exact offsets; any graded failure rejects. An initial invocation omitted `PYTHONPATH` and exited at module import before any retrieval execution; the successful run used the unchanged precommit hash.

| Class | Passed | Total | Failing IDs |
| --- | ---: | ---: | --- |
| answerable targeted | 0 | 4 | a01-a04 |
| answerable function-only | 3 | 4 | f01 |
| answerable discourse | 0 | 4 | d01-d04 |
| answerable case | 1 | 2 | c01 |
| answerable benign typo | 4 | 4 | — |
| no-support lowercase external | 6 | 8 | n01, n08 |
| no-support capitalized external | 5 | 6 | n09 |
| no-support fuzzy collision | 6 | 6 | — |
| no-support unrelated | 6 | 6 | — |
| contextual absent fact | ungraded | 8 | returned 0-3 passages; recorded only |

Exact graded failures:

| ID | Expected | Exact question | Actual document IDs |
| --- | --- | --- | --- |
| a01 | coordination + observation | Within Project Meridian's Austrian files, which body ran the Vienna exercise, and do the opening records say 14 or 16 May 1987? | `[]` |
| a02 | coordination + observation | Using the Austrian Project Meridian accounts, name the organizer and contrast the planned opening with the observer correction. | `[]` |
| a03 | coordination + observation | Did Harbor Institute convene the Meridian field test while Eastbridge handled operations, and were 14 and 16 May 1987 both claimed as opening dates? | `[]` |
| a04 | coordination + observation | From the Vienna records on Project Meridian, identify the convening body and explain the two-day discrepancy in its start. | `[]` |
| f01 | coordination + observation | Which body put the exercise together, and what preliminary and corrected start days do the notes contain? | `[]` |
| d01 | coordination + observation | Incidentally, for Meridian at Vienna, who hosted the pilot and which opening dates conflict? | `[]` |
| d02 | coordination + observation | As a follow-up, who convened Project Meridian in Vienna and what days are disputed? | `[]` |
| d03 | coordination + observation | To circle back, identify the Meridian Vienna organizer and its two reported May opening dates. | `[]` |
| d04 | coordination + observation | Separately, which institution hosted the Austrian pilot, and what opening dates differ? | `[]` |
| c01 | coordination + observation | pRoJeCt mErIdIaN in vIeNnA: who arranged the trial and what two May start days are documented? | `[]` |
| n01 | no evidence | which institute convened the borealis vienna pilot and when did it open? | coordination, observation, Lisbon distractor |
| n08 | no evidence | which organization hosted triton's austrian trial? | coordination, observation, Lisbon distractor |
| n09 | no evidence | Which institute organized Project Horizon's Vienna exercise? | coordination, observation, Lisbon distractor |

Fresh manifest (the other 39 probes, in precommit order):

```text
f02 Who served in the convening role, and did the demonstration open on fourteen or sixteen May 1987?
f03 Name the event host and compare the scheduling note's first day with the observer correction.
f04 What organization arranged the field trial; when was its opening planned and when was it observed?
c02 PROJECT MERIDIAN VIENNA EXERCISE — ORGANIZER AND THE TWO MAY 1987 START DATES?
t01 For Project Meridian's Vinenna exercise, who organized it and what start days conflict?
t02 Project Meridian in Vienan: name the convener and compare 14 with 16 May 1987.
t03 Which body convened Project Meridain at Vienna, and which two dates are in dispute?
t04 Did Harobr Institute convene Project Meridian's Vienna pilot, and what opening dates do the accounts give?
n02 did icarus operations begin at the field site on 16 may 1987?
n03 who organized the phoenix project demonstration in vienna?
n04 when did selene communications staff meet in lisbon during june 1987?
n05 did argonaut laboratory supply instruments to the vienna field exercise?
n06 which archive note recorded perseus project costs and funding totals?
n07 did prometheus observers correct the 14 may scheduling note?
n10 Did Northstar Laboratory lead operations at the field site?
n11 When did Project Daedalus open in Austria?
n12 Who reviewed Portuguese press clippings for Project Solstice?
n13 Which body convened the Helios pilot on 16 May 1987?
n14 Did Redwood Institute supply the Meridian instruments?
z01 When did Project Meridiano begin?
z02 What happened during the Vienan exercise?
z03 Did Harobr Institute organize the pilot?
z04 Who led Eastbridg Laboratory operations?
z05 Was Lisboon the communications meeting site?
z06 Did Arhive office renew the travel forms?
u01 How are quasars powered?
u02 Describe photosynthesis in kelp.
u03 What causes tectonic subduction?
u04 Who composed the Brandenburg Concertos?
u05 Compute the volume of a cone.
u06 Axolotl?
g01 Which caterer served Project Meridian's Vienna exercise?
g02 What aircraft tail number carried Eastbridge Laboratory instruments to Vienna?
g03 How many trucks delivered Harbor Institute equipment to the field site?
g04 What hotel room housed Project Meridian observers in Vienna?
g05 Which badge emblem did Harbor Institute conveners display?
g06 What wind speed did the Vienna observer note record on 16 May 1987?
g07 Which translator assisted Eastbridge Laboratory during Project Meridian?
g08 What was the vehicle mileage for the Harbor Institute field trip?
```

Commands and outputs:

```text
$ git rev-parse HEAD
3f5510c268408648af89e4b514dc220d6a23f2fd
$ .venv/bin/python --version
Python 3.12.3
$ .venv/bin/python -m pip check
No broken requirements found.
$ PYTHONPATH=. .venv/bin/python /tmp/crest_signoff_v10_run.py
v5-v10: 68/68 passed twice; deterministic=true; exact offsets=true
fresh: deterministic=true; exact offsets=true; answerable=8/18; no-support=23/26; contextual=8 ungraded
$ .venv/bin/python -m pytest -q tests/test_evidence_retrieval.py tests/test_evidence_inquiries.py tests/test_crest_app.py -k 'evidence or inquiry'
7 passed, 12 deselected, 1 warning in 0.93s
$ .venv/bin/python -m pytest -q
50 passed, 1 warning in 5.63s
$ node --check web/app.js
exit 0
```

Input hashes:

```text
b0dcee424fa22714f4f285570dada0b70c74df3dab073cceece7af462e521466  evaluation/evidence_retrieval_set_v5.json
4b8d4ef44adc3cf4d9b5539b54ee09901396489abd29efbc1c3473f561394e38  evaluation/evidence_retrieval_set_v6.json
cdf24b289a8303a24c76ab43e9cb326616ae4d7fb0957b53133fd86fbd28a92c  evaluation/evidence_retrieval_set_v7.json
589866bc1f131599d662d224ae2b0d126980a99c7c603ea746291df798a51ae9  evaluation/evidence_retrieval_set_v8.json
79a02f933741381886981d3a3a83379c0f6cfbff44e0ff4c8f206245f1f2758e  evaluation/evidence_retrieval_set_v9.json
009df48185fccd1752177131a99d2fe655edf6d052cdc2bcab876b2d08188364  evaluation/evidence_retrieval_set_v10.json
8a0fc5f26acbb66e57d4b1fc6e41868f9a38e89f6a20c4fd31f3a12c6dcaf311  evaluation/run_evidence_retrieval_eval.py
6eb33c44f6c26acfdc3478701d43a1b6370eeaab27b5a20340e90b45d94450c3  crest_app/retrieval.py
3e610f659d7845353106605fcba6fa6ade1d8dcb5ed15268c4419f293ad9a9a2  tests/test_evidence_retrieval.py
```

Limitations: This is a narrow deterministic synthetic passage-ranking sign-off, not a human-quality retrieval evaluation. It does not grade answerability for contextual absent facts and does not verify the UI, live LLM brief, graph generation, or deployment runtime. Those boundaries cannot compensate for this failed prerequisite.
