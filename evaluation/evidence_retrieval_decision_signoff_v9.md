# EVAL-DECISION SIGN-OFF

decision: Whether exact revision `c661db66a7b33ae8b6c8507c473e288ec391dcec` may proceed to an isolated candidate deployment for CREST lexical passage retrieval under this contract: rank relevant collection context with meaningful exact lexical/concept support; return no chunks for absent external subjects; treat fully functional collection-scoped questions as valid; permit fuzzy signals to augment ranking but not establish subject identity without another exact named anchor; leave context-rich absent-fact answerability to the evidence brief and ungraded here.

eval: frozen `evaluation/evidence_retrieval_set_v5.json` through `evaluation/evidence_retrieval_set_v9.json`; prior sign-offs v5-v8 inspected as adversarial-class context but not trusted as execution evidence; focused tests; exact-offset checks; two-run determinism; and the fresh precommitted probes below at the exact revision.

verdict: **REJECTED**

## Fresh probe precommit

Pass rules were fixed before execution. Answerable probes require both `meridian-coordination` and `meridian-observation` within top four, exclude `meridian-lisbon-distractor` from the top two, and require exact offsets. No-support probes require `[]`. Contextual absent-fact probes are recorded but ungraded. Every probe must be identical across two executions. Any graded failure rejects the deployment gate.

### Answerable probes

| ID | Class | Exact question |
| --- | --- | --- |
| a01 | targeted | Project Meridian's Vienna exercise: which organization convened it, and what two May 1987 dates are given for its start? |
| a02 | targeted | For the Austrian Meridian pilot, identify the organizing body and reconcile the scheduled opening with the observer's corrected opening. |
| a03 | targeted | Who arranged the Vienna field demonstration for Meridian, and did the source notes place day one on 14 or 16 May 1987? |
| a04 | targeted | Was Harbor Institute or Eastbridge Laboratory responsible for convening the Vienna trial, and which two start dates appear? |
| a05 | targeted | Name the group behind Project Meridian's Austrian event and compare the preliminary date to the date reported by observers. |
| a06 | targeted | In the Vienna coordination and observation accounts, who hosted the pilot and when was it supposed to begin versus when it began? |
| a07 | targeted | Extract the Meridian exercise organizer and the conflicting May opening dates from the Vienna material. |
| a08 | targeted | Which institute put on Project Meridian's Austrian demonstration, and what pair of calendar days marks its debut? |
| a09 | targeted | Vienna Meridian field test — convening organization; scheduled first day; corrected first day. |
| a10 | targeted | Did Harbor Institute organize the Austrian pilot while Eastbridge led field operations, and what dates do the two notes assign to the launch? |
| a11 | targeted | Fourteen or sixteen May 1987: who coordinated the Project Meridian event in Vienna? |
| a12 | targeted | Compare the Vienna field note with the observer correction: identify the convener and both recorded beginnings. |
| a13 | targeted | What body staged Meridian's Vienna gathering, and how do the schedule and correction differ on its opening day? |
| a14 | targeted-lowercase | project meridian in vienna: who organized the pilot and which two dates do the accounts give for its opening? |
| f01 | function-only | Which organization arranged the demonstration, and what two dates were scheduled and observed for its beginning? |
| f02 | function-only | Name the host of the pilot and give the preliminary and corrected opening days. |
| f03 | function-only | Who coordinated the event, and when did the exercise start according to the schedule and the correction? |
| f04 | function-only | What body convened the trial, and which two days were reported for its debut? |
| f05 | function-only | Identify the organizer and reconcile the scheduled beginning with the observed beginning. |
| f06 | function-only | Which committee put the field test together, and what dates compete for day one? |
| f07 | function-only | What institution served as convener, and when was the gathering planned to open versus reported open? |
| f08 | function-only | Which group organized the pilot and what calendar dates did the preliminary schedule and correction state? |
| f09 | function-only | Who hosted the demonstration, and did it launch on the scheduled day or the corrected day? |
| f10 | function-only | Which agency managed the convening role, and what two opening days are recorded for the exercise? |
| m01 | benign-misspelling | For Project Meridain in Vienna, who convened the pilot and what two start dates appear? |
| m02 | benign-misspelling | For Meridian's Veinna demonstration, name the organizer and compare 14 with 16 May 1987. |
| m03 | benign-misspelling | Was Habor Institute the Meridian Vienna trial convener, and which opening days do the notes report? |
| m04 | benign-misspelling | Did Eastbrdge Laboratory or Harbor Institute organize the Vienna pilot, and when did it start? |
| m05 | benign-misspelling | Who arranged the Austrian demonstrtion for Project Meridian, and which May dates mark its opening? |
| m06 | benign-misspelling | Compare the schedulled day with the observor correction for Meridian's Vienna exercise; identify the host. |
| m07 | benign-misspelling | Which labratory led field operations while Harbor Institute convened the Vienna event, and what two dates are recorded? |
| m08 | benign-misspelling | Name the organzier of Project Meridian's Vienna pilot and reconcile its planned and corrected beginnings. |
| d01 | discourse-lead | Actually, for Project Meridian in Vienna, who convened the demonstration and what two dates are reported? |
| d02 | discourse-lead | One more thing: which organization hosted the Meridian Vienna trial, and when was it scheduled versus observed? |
| d03 | discourse-lead | By the way, who organized Project Meridian's Austrian pilot and which May days mark its opening? |
| d04 | discourse-lead | Okay, identify the Vienna exercise convener and reconcile 14 May with 16 May 1987. |
| d05 | discourse-lead | Returning to Meridian, what body arranged the Vienna field test and what two start dates do the notes give? |
| d06 | lowercase | who put the project meridian demonstration in vienna together, and did it start on 14 or 16 may 1987? |
| d07 | uppercase | WHO ORGANIZED PROJECT MERIDIAN'S VIENNA PILOT, AND WHAT TWO OPENING DATES APPEAR? |
| d08 | polite-lead | Please also identify the organization behind the Austrian Meridian event and compare its scheduled and corrected first days. |

### No-support probes

| ID | Class | Exact question |
| --- | --- | --- |
| e01 | external-subject | Which institution organized the Europa Clipper mission? |
| e02 | external-subject | What agency coordinated the Dakar Rally opening? |
| e03 | external-subject | Which committee supervised the Edinburgh Festival launch? |
| e04 | external-subject | Who hosted the Osaka Expo pilot event? |
| e05 | external-subject | What laboratory directed the Cassini imaging program? |
| e06 | external-subject | Which body convened the Geneva Peace Conference? |
| e07 | external-subject | What team managed the Artemis lunar rehearsal? |
| e08 | external-subject | Who observed and corrected the Monaco Grand Prix schedule? |
| e09 | external-subject | Which institute arranged the Salzburg music gathering? |
| e10 | external-subject | What organization led the Normandy landing exercise? |
| e11 | external-subject | Which agency scheduled the first Ariane rocket test? |
| e12 | external-subject | Who organized the Glastonbury festival demonstration? |
| e13 | external-subject | What committee managed the Pulitzer Prize ceremony? |
| e14 | external-subject | Which institution hosted the Aspen economic forum? |
| e15 | external-subject | Who led the Gemini rendezvous trial and when did it begin? |
| e16 | external-subject | Which body arranged the Melbourne Commonwealth Games opening? |
| e17 | external-subject | What agency corrected the Julian calendar? |
| e18 | external-subject | Which laboratory supplied instruments for the Juno polar mission? |
| e19 | external-subject | Who reviewed press clippings for the Sundance Film Festival? |
| e20 | external-subject | Which office renewed travel forms for the Nairobi aid program? |
| l01 | lowercase-external | which institute reviewed press clippings for the sundance campaign? |
| l02 | lowercase-external | did osiris staff operate from the field site? |
| l03 | lowercase-external | which atlas archive office renewed the travel forms? |
| l04 | lowercase-external | did the helix program replace storage cabinets in the regional archive? |
| l05 | lowercase-external | who managed the portuguese media campaign for orion? |
| l06 | lowercase-external | when did kepler communications staff meet in lisbon? |
| l07 | lowercase-external | what instruments are listed in the zephyr field note? |
| l08 | lowercase-external | did the aurora observer correction mention the field site? |
| l09 | lowercase-external | which polaris scheduling note discussed press clippings? |
| l10 | lowercase-external | did the apollo regional archive office record the program? |
| l11 | lowercase-external | what project costs accompanied genesis storage cabinets? |
| l12 | lowercase-external | were nomad travel forms tied to funding totals? |
| l13 | lowercase-external | who led voyager operations at the field site? |
| l14 | lowercase-external | did titan instruments reach the field site? |
| l15 | lowercase-external | which cassini communications staff received convening support? |
| l16 | lowercase-external | did odyssey begin on 14 may 1987 according to the scheduling note? |
| z01 | fuzzy-subject | Harbour Institute mission? |
| z02 | fuzzy-subject | When did the Meridiane Project begin? |
| z03 | fuzzy-subject | Who led the Eastbrudge Laboratory trial? |
| z04 | fuzzy-subject | What happened at Lisborn? |
| z05 | fuzzy-subject-with-generic-anchor | Which Reginal archive program used the travel forms? |
| z06 | fuzzy-subject-with-generic-anchor | Did Arbour Institute author the field note? |
| z07 | fuzzy-subject-with-generic-anchor | Which Medial campaign produced the press clippings? |
| z08 | fuzzy-subject-with-generic-anchor | Did Preview communications staff write the brief? |
| z09 | fuzzy-subject-with-generic-anchor | Were Supple instruments listed in the field note? |
| z10 | fuzzy-subject-with-generic-anchor | Did Meridion appear in the scheduling note? |
| z11 | fuzzy-subject-with-generic-anchor | Was Eastbride named at the field site? |
| z12 | fuzzy-subject-with-generic-anchor | Did Arbor staff review the press clippings? |
| s01 | unrelated-singleton | Zeugma? |
| s02 | unrelated-singleton | Pulsar? |
| s03 | unrelated-singleton | Kombucha? |
| s04 | unrelated-singleton | Moraine? |
| s05 | unrelated-singleton | Isotope? |
| s06 | unrelated-singleton | Chiaroscuro? |
| s07 | unrelated-singleton | Banyan? |
| s08 | unrelated-singleton | Semaphore? |
| u01 | unrelated-multiword | How do coral reefs bleach? |
| u02 | unrelated-multiword | What causes lunar libration? |
| u03 | unrelated-multiword | Explain protein folding in cells. |
| u04 | unrelated-multiword | Who painted The Night Watch? |
| u05 | unrelated-multiword | Calculate the area of a hexagon. |
| u06 | unrelated-multiword | Why do cicadas emerge periodically? |
| u07 | unrelated-multiword | Translate morning star into Finnish. |
| u08 | unrelated-multiword | Describe the formation of desert dunes. |

### Contextual absent-fact probes — ungraded

| ID | Class | Exact question |
| --- | --- | --- |
| c01 | contextual-absent-fact | Which insurance policy covered Project Meridian's Vienna pilot? |
| c02 | contextual-absent-fact | What vehicle registration carried Eastbridge instruments to the field site? |
| c03 | contextual-absent-fact | What badge color did Harbor Institute conveners wear during the demonstration? |
| c04 | contextual-absent-fact | Which lunch menu was served before the Vienna exercise began? |
| c05 | contextual-absent-fact | What radio serial number was assigned to the Meridian organizing committee? |
| c06 | contextual-absent-fact | Which hotel housed the observer team during the Vienna pilot? |
| c07 | contextual-absent-fact | How many people attended Project Meridian's field demonstration? |
| c08 | contextual-absent-fact | What weather was recorded at the Vienna field site on 16 May 1987? |

## Sign-off gates

gate 1 validity: **PASS** — Exact commit `c661db66a7b33ae8b6c8507c473e288ec391dcec` was clean before this artifact. Python 3.12.3 and required imports responded; `pip check` found no broken requirements. Frozen v5-v9 passed twice identically with exact offsets; focused tests reported `7 passed, 12 deselected`. All 112 fresh probes repeated identically and every returned source slice was exact.

gate 2 representativeness: **FAIL** — The fresh precommit spans 40 answerable probes (14 targeted, 10 function-only, 8 benign misspellings, 8 discourse/case variants), 64 no-support controls (20 capitalized external subjects, 16 lowercase external subjects sharing corpus vocabulary, 12 named collisions, 8 unrelated singletons, 8 unrelated multiword), and 8 contextual absent-fact questions ungraded. It exposes stable classes absent from frozen v5-v9: discourse/case false abstention, function-only false abstention/redirection, lowercase external-subject false admission, and a name-normalization collision.

gate 3 diagnosis: **PASS** — `_named_query_terms` mistakes capitalized discourse or all-caps words (`Actually`, `One`, `Okay`, `Returning`, `Extract`, `Fourteen`, `APPEAR`) for mandatory subject targets. Intended function questions acquire incidental target stems (`accord`, `plann`, `state`, `record`, `convener`), suppressing or redirecting relevant evidence. Conversely, lowercase absent names create no named-target requirement, so exact generic words (`field site`, `press clippings`, `travel forms`, dates) admit Meridian passages. `Meridiane` stems to exact `meridian`, collapsing identity without another exact named anchor.

gate 4 generalization: **FAIL** — Fresh execution passed 28/40 answerable and 47/64 no-support probes. Answerable: targeted 12/14, function-only 6/10, benign misspellings 7/8, discourse/case 3/8. No-support: capitalized external 20/20, lowercase external 0/16, named collisions 11/12, unrelated singleton 8/8, unrelated multiword 8/8. All 29 graded failures are deterministic with exact offsets.

gate 5 decision: **FAIL** — The isolated deployment gate is justified and explicitly rejects on any graded failure. Twenty-nine stable failures remain; the eight contextual absent-fact probes are ungraded and do not affect the verdict.

rejections / required fixes: Do not deploy this revision under the stated contract. Separate subject identity from surface capitalization, exempt discourse and answer-function vocabulary from mandatory identity, require an explicit subject anchor for lowercase external names, and prevent stemming distinct proper names into identity. Freeze these 29 failures and obtain another independent sign-off after repair.

## Execution evidence

Fresh precommit SHA-256: `a877c3ff54071e72dd394983f2124a5bf50d5ff26a58567bc614d41a3684a1b6` over the ordered compact JSON `{id,class,question}` array. Counts: 40 answerable, 64 no-support, 8 contextual ungraded; 112 unique IDs and questions. The hash was recorded before `rank_evidence` execution.

```text
$ git rev-parse HEAD
c661db66a7b33ae8b6c8507c473e288ec391dcec
$ .venv/bin/python --version
Python 3.12.3
$ .venv/bin/python -m pip check
No broken requirements found.
$ .venv/bin/python -m pytest -q tests/test_evidence_retrieval.py tests/test_evidence_inquiries.py tests/test_crest_app.py -k 'evidence or inquiry'
7 passed, 12 deselected, 1 warning in 0.95s
```

Execution hashes:

```text
b0dcee424fa22714f4f285570dada0b70c74df3dab073cceece7af462e521466  evaluation/evidence_retrieval_set_v5.json
4b8d4ef44adc3cf4d9b5539b54ee09901396489abd29efbc1c3473f561394e38  evaluation/evidence_retrieval_set_v6.json
cdf24b289a8303a24c76ab43e9cb326616ae4d7fb0957b53133fd86fbd28a92c  evaluation/evidence_retrieval_set_v7.json
589866bc1f131599d662d224ae2b0d126980a99c7c603ea746291df798a51ae9  evaluation/evidence_retrieval_set_v8.json
79a02f933741381886981d3a3a83379c0f6cfbff44e0ff4c8f206245f1f2758e  evaluation/evidence_retrieval_set_v9.json
b1887128251afd6a29afdc5264231d86e8743426f0388b307a39e9c609bac7e6  evaluation/run_evidence_retrieval_eval.py
b835011c8689a9d8717d8abb72ed0416b1da4c7c257ec74aa8d2634e0161467a  crest_app/retrieval.py
7afb0331e069ba11de0096d8269c71f53d9db895091b7a235b7fd9ce8ff9ddcb  tests/test_evidence_retrieval.py
```

### Frozen v5-v9 results

Each JSONL record is the first run; `deterministic:true` means the immediate second complete fixture value was identical. Passing chunks are not expanded.

```jsonl
{"fixture":"v5","passed":true,"deterministic":true,"all_offsets_exact":true,"cases":[{"id":"quick-check-set-up-dates","ranked_document_ids":["meridian-coordination","meridian-observation","meridian-lisbon-distractor"],"passed":true,"offsets_exact":true},{"id":"pin-down-convening-dates","ranked_document_ids":["meridian-observation","meridian-coordination"],"passed":true,"offsets_exact":true},{"id":"got-demonstration-together","ranked_document_ids":["meridian-observation","meridian-coordination"],"passed":true,"offsets_exact":true},{"id":"outfit-staged-trial","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"passed":true,"offsets_exact":true},{"id":"organization-convened-memo-days","ranked_document_ids":["meridian-observation","meridian-coordination"],"passed":true,"offsets_exact":true},{"id":"brought-field-test-together","ranked_document_ids":["meridian-coordination","meridian-observation","meridian-lisbon-distractor"],"passed":true,"offsets_exact":true},{"id":"no-support-radio-frequency","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-quantum-telemetry","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-airline","ranked_document_ids":[],"passed":true,"offsets_exact":true}]}
{"fixture":"v6","passed":true,"deterministic":true,"all_offsets_exact":true,"cases":[{"id":"put-together-timetable-debut","ranked_document_ids":["meridian-coordination","meridian-observation","meridian-lisbon-distractor"],"passed":true,"offsets_exact":true},{"id":"host-timings-debut","ranked_document_ids":["meridian-coordination","meridian-observation","meridian-lisbon-distractor"],"passed":true,"offsets_exact":true},{"id":"no-support-projectile","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-projective","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-projectile-question","ranked_document_ids":[],"passed":true,"offsets_exact":true}]}
{"fixture":"v7","passed":true,"deterministic":true,"all_offsets_exact":true,"cases":[{"id":"programming-program","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"reginald-regional","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"supple-supplied","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"preview-review","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"arbor-harbor","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"medial-media","ranked_document_ids":[],"passed":true,"offsets_exact":true}]}
{"fixture":"v8","passed":true,"deterministic":true,"all_offsets_exact":true,"cases":[{"id":"paperwork-organizer-beginnings","ranked_document_ids":["meridian-coordination","meridian-observation","meridian-lisbon-distractor"],"passed":true,"offsets_exact":true},{"id":"no-support-mars-institution","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-paris-convener","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-olympic-committee","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-genome-laboratory","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-debate-host","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-chess-observer","ranked_document_ids":[],"passed":true,"offsets_exact":true}]}
{"fixture":"v9","passed":true,"deterministic":true,"all_offsets_exact":true,"cases":[{"id":"functional-organizer-corrected-beginning","ranked_document_ids":["meridian-observation","meridian-coordination"],"passed":true,"offsets_exact":true},{"id":"functional-committee-days-mark-debut","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"passed":true,"offsets_exact":true},{"id":"functional-host-scheduled-corrected","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"passed":true,"offsets_exact":true},{"id":"no-support-arbor-mission","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-meridion-program","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-eastbridle-laboratory","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-reginal-program","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-supple-demonstration","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-preview-event","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-medial-program","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-eastbride-mission","ranked_document_ids":[],"passed":true,"offsets_exact":true},{"id":"no-support-kepler-instruments","ranked_document_ids":[],"passed":true,"offsets_exact":true}]}
```

### Fresh ranked results

The exact question text is precommitted above under the same unique ID. These compact records provide every ranked document ID, graded pass/fail value, determinism flag, and offset flag without expanding passing chunks.

```jsonl
{"id":"a01","ranked_document_ids":["meridian-coordination","meridian-observation"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"a02","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"a03","ranked_document_ids":["meridian-observation","meridian-coordination"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"a04","ranked_document_ids":["meridian-observation","meridian-coordination"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"a05","ranked_document_ids":["meridian-coordination","meridian-observation","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"a06","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"a07","ranked_document_ids":[],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"a08","ranked_document_ids":["meridian-coordination","meridian-observation","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"a09","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"a10","ranked_document_ids":["meridian-observation","meridian-coordination"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"a11","ranked_document_ids":[],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"a12","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"a13","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"a14","ranked_document_ids":["meridian-coordination","meridian-observation","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"f01","ranked_document_ids":["meridian-coordination","meridian-observation"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"f02","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"f03","ranked_document_ids":[],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"f04","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"f05","ranked_document_ids":["meridian-observation","meridian-coordination"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"f06","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"f07","ranked_document_ids":["meridian-coordination"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"f08","ranked_document_ids":[],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"f09","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"f10","ranked_document_ids":["meridian-administration"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"m01","ranked_document_ids":["meridian-coordination","meridian-observation","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"m02","ranked_document_ids":[],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"m03","ranked_document_ids":["meridian-coordination","meridian-observation","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"m04","ranked_document_ids":["meridian-observation","meridian-coordination"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"m05","ranked_document_ids":["meridian-coordination","meridian-observation"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"m06","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"m07","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"m08","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"d01","ranked_document_ids":[],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"d02","ranked_document_ids":[],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"d03","ranked_document_ids":["meridian-coordination","meridian-observation"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"d04","ranked_document_ids":[],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"d05","ranked_document_ids":[],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"d06","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"d07","ranked_document_ids":[],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"d08","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e01","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e02","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e03","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e04","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e05","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e06","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e07","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e08","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e09","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e10","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e11","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e12","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e13","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e14","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e15","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e16","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e17","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e18","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e19","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"e20","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"l01","ranked_document_ids":["meridian-lisbon-distractor"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l02","ranked_document_ids":["meridian-observation","meridian-lisbon-distractor","meridian-coordination"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l03","ranked_document_ids":["meridian-administration"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l04","ranked_document_ids":["meridian-administration"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l05","ranked_document_ids":["meridian-lisbon-distractor"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l06","ranked_document_ids":["meridian-lisbon-distractor"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l07","ranked_document_ids":["meridian-coordination","meridian-observation"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l08","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l09","ranked_document_ids":["meridian-lisbon-distractor","meridian-coordination","meridian-observation"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l10","ranked_document_ids":["meridian-administration"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l11","ranked_document_ids":["meridian-administration"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l12","ranked_document_ids":["meridian-administration"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l13","ranked_document_ids":["meridian-observation","meridian-coordination"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l14","ranked_document_ids":["meridian-coordination","meridian-observation"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l15","ranked_document_ids":["meridian-lisbon-distractor","meridian-observation"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"l16","ranked_document_ids":["meridian-coordination","meridian-observation"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"z01","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"z02","ranked_document_ids":["meridian-coordination","meridian-observation","meridian-lisbon-distractor"],"graded":true,"passed":false,"deterministic":true,"offsets_exact":true}
{"id":"z03","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"z04","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"z05","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"z06","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"z07","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"z08","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"z09","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"z10","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"z11","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"z12","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"s01","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"s02","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"s03","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"s04","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"s05","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"s06","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"s07","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"s08","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"u01","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"u02","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"u03","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"u04","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"u05","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"u06","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"u07","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"u08","ranked_document_ids":[],"graded":true,"passed":true,"deterministic":true,"offsets_exact":true}
{"id":"c01","ranked_document_ids":["meridian-coordination","meridian-lisbon-distractor","meridian-observation"],"graded":false,"passed":null,"deterministic":true,"offsets_exact":true}
{"id":"c02","ranked_document_ids":["meridian-coordination","meridian-observation"],"graded":false,"passed":null,"deterministic":true,"offsets_exact":true}
{"id":"c03","ranked_document_ids":["meridian-coordination","meridian-lisbon-distractor","meridian-observation"],"graded":false,"passed":null,"deterministic":true,"offsets_exact":true}
{"id":"c04","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"graded":false,"passed":null,"deterministic":true,"offsets_exact":true}
{"id":"c05","ranked_document_ids":["meridian-coordination","meridian-observation","meridian-lisbon-distractor"],"graded":false,"passed":null,"deterministic":true,"offsets_exact":true}
{"id":"c06","ranked_document_ids":["meridian-lisbon-distractor","meridian-observation","meridian-coordination"],"graded":false,"passed":null,"deterministic":true,"offsets_exact":true}
{"id":"c07","ranked_document_ids":["meridian-coordination","meridian-lisbon-distractor","meridian-observation"],"graded":false,"passed":null,"deterministic":true,"offsets_exact":true}
{"id":"c08","ranked_document_ids":["meridian-observation","meridian-coordination"],"graded":false,"passed":null,"deterministic":true,"offsets_exact":true}
```

### Failure chunk details

Only graded failures are expanded. Each record includes the exact question and every returned `EvidenceChunk` field plus a recomputed `offset_exact` flag. `chunks:[]` is the complete output for abstention failures.

```jsonl
{"id":"a07","class":"targeted","question":"Extract the Meridian exercise organizer and the conflicting May opening dates from the Vienna material.","ranked_document_ids":[],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[]}
{"id":"a11","class":"targeted","question":"Fourteen or sixteen May 1987: who coordinated the Project Meridian event in Vienna?","ranked_document_ids":[],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[]}
{"id":"f03","class":"function-only","question":"Who coordinated the event, and when did the exercise start according to the schedule and the correction?","ranked_document_ids":[],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[]}
{"id":"f07","class":"function-only","question":"What institution served as convener, and when was the gathering planned to open versus reported open?","ranked_document_ids":["meridian-coordination"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-4956460d5a45d9e6c5c3","document_id":"meridian-coordination","connector_id":"bundled-crest","title":"Project Meridian Vienna coordination note","start_char":0,"end_char":254,"text":"Project Meridian field note. The Harbor Institute acted as the organizing body for the Vienna pilot. Its conveners scheduled the first field exercise for 14 May 1987. Eastbridge Laboratory supplied instruments but did not direct the organizing committee.","rank":1,"score":6.55683977,"score_components":{"bm25":2.856839773934239,"coverage":0.8,"fuzzy":0.0,"phrase":0.0,"title":0.5},"matched_terms":["institution","convener","gather","open"],"offset_exact":true}]}
{"id":"f08","class":"function-only","question":"Which group organized the pilot and what calendar dates did the preliminary schedule and correction state?","ranked_document_ids":[],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[]}
{"id":"f10","class":"function-only","question":"Which agency managed the convening role, and what two opening days are recorded for the exercise?","ranked_document_ids":["meridian-administration"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-e5b52cafa44e2567543d","document_id":"meridian-administration","connector_id":"bundled-crest","title":"Regional archive administration","start_char":0,"end_char":168,"text":"The archive office renewed storage cabinets and travel forms for regional programs. No project costs, funding totals, or procurement budgets were recorded in this note.","rank":1,"score":2.84043985,"score_components":{"bm25":1.5071065211653059,"coverage":0.3333333333333333,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["record","exercis"],"offset_exact":true}]}
{"id":"m02","class":"benign-misspelling","question":"For Meridian's Veinna demonstration, name the organizer and compare 14 with 16 May 1987.","ranked_document_ids":[],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[]}
{"id":"d01","class":"discourse-lead","question":"Actually, for Project Meridian in Vienna, who convened the demonstration and what two dates are reported?","ranked_document_ids":[],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[]}
{"id":"d02","class":"discourse-lead","question":"One more thing: which organization hosted the Meridian Vienna trial, and when was it scheduled versus observed?","ranked_document_ids":[],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[]}
{"id":"d04","class":"discourse-lead","question":"Okay, identify the Vienna exercise convener and reconcile 14 May with 16 May 1987.","ranked_document_ids":[],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[]}
{"id":"d05","class":"discourse-lead","question":"Returning to Meridian, what body arranged the Vienna field test and what two start dates do the notes give?","ranked_document_ids":[],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[]}
{"id":"d07","class":"uppercase","question":"WHO ORGANIZED PROJECT MERIDIAN'S VIENNA PILOT, AND WHAT TWO OPENING DATES APPEAR?","ranked_document_ids":[],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[]}
{"id":"l01","class":"lowercase-external","question":"which institute reviewed press clippings for the sundance campaign?","ranked_document_ids":["meridian-lisbon-distractor"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-676c9047965194370acf","document_id":"meridian-lisbon-distractor","connector_id":"bundled-crest","title":"Project Meridian Lisbon communications brief","start_char":0,"end_char":210,"text":"Project Meridian communications staff met in Lisbon during June 1987. The Harbor Institute reviewed press clippings for the Portuguese media campaign. This brief does not concern the Vienna field demonstration.","rank":1,"score":8.63878178,"score_components":{"bm25":5.305448450827204,"coverage":0.8333333333333334,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["institut","review","pres","clipping","campaign"],"offset_exact":true}]}
{"id":"l02","class":"lowercase-external","question":"did osiris staff operate from the field site?","ranked_document_ids":["meridian-observation","meridian-lisbon-distractor","meridian-coordination"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-dcb521a91bb47c381917","document_id":"meridian-observation","connector_id":"bundled-crest","title":"Vienna demonstration observer correction","start_char":0,"end_char":252,"text":"Observer correction for Project Meridian. The Vienna demonstration began on 16 May 1987, not 14 May as stated in the preliminary scheduling note. Harbor Institute provided convening support, while Eastbridge Laboratory led operations at the field site.","rank":1,"score":4.49628208,"score_components":{"bm25":2.096282082202704,"coverage":0.6,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["operat","field","site"],"offset_exact":true},{"id":"evidence-676c9047965194370acf","document_id":"meridian-lisbon-distractor","connector_id":"bundled-crest","title":"Project Meridian Lisbon communications brief","start_char":0,"end_char":210,"text":"Project Meridian communications staff met in Lisbon during June 1987. The Harbor Institute reviewed press clippings for the Portuguese media campaign. This brief does not concern the Vienna field demonstration.","rank":2,"score":3.20074051,"score_components":{"bm25":1.6007405067833615,"coverage":0.4,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["staff","field"],"offset_exact":true},{"id":"evidence-4956460d5a45d9e6c5c3","document_id":"meridian-coordination","connector_id":"bundled-crest","title":"Project Meridian Vienna coordination note","start_char":0,"end_char":254,"text":"Project Meridian field note. The Harbor Institute acted as the organizing body for the Vienna pilot. Its conveners scheduled the first field exercise for 14 May 1987. Eastbridge Laboratory supplied instruments but did not direct the organizing committee.","rank":3,"score":2.72635973,"score_components":{"bm25":1.1263597255944624,"coverage":0.4,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["operat","field"],"offset_exact":true}]}
{"id":"l03","class":"lowercase-external","question":"which atlas archive office renewed the travel forms?","ranked_document_ids":["meridian-administration"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-e5b52cafa44e2567543d","document_id":"meridian-administration","connector_id":"bundled-crest","title":"Regional archive administration","start_char":0,"end_char":168,"text":"The archive office renewed storage cabinets and travel forms for regional programs. No project costs, funding totals, or procurement budgets were recorded in this note.","rank":1,"score":10.58610484,"score_components":{"bm25":6.752771503971693,"coverage":0.8333333333333334,"fuzzy":0.0,"phrase":0.0,"title":0.5},"matched_terms":["archiv","offic","renew","travel","form"],"offset_exact":true}]}
{"id":"l04","class":"lowercase-external","question":"did the helix program replace storage cabinets in the regional archive?","ranked_document_ids":["meridian-administration"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-e5b52cafa44e2567543d","document_id":"meridian-administration","connector_id":"bundled-crest","title":"Regional archive administration","start_char":0,"end_char":168,"text":"The archive office renewed storage cabinets and travel forms for regional programs. No project costs, funding totals, or procurement budgets were recorded in this note.","rank":1,"score":9.41591228,"score_components":{"bm25":5.558769423548322,"coverage":0.7142857142857143,"fuzzy":0.0,"phrase":0.0,"title":1.0},"matched_terms":["program","storag","cabinet","regional","archiv"],"offset_exact":true}]}
{"id":"l05","class":"lowercase-external","question":"who managed the portuguese media campaign for orion?","ranked_document_ids":["meridian-lisbon-distractor"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-676c9047965194370acf","document_id":"meridian-lisbon-distractor","connector_id":"bundled-crest","title":"Project Meridian Lisbon communications brief","start_char":0,"end_char":210,"text":"Project Meridian communications staff met in Lisbon during June 1987. The Harbor Institute reviewed press clippings for the Portuguese media campaign. This brief does not concern the Vienna field demonstration.","rank":1,"score":6.10470794,"score_components":{"bm25":3.704707944043842,"coverage":0.6,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["portugues","media","campaign"],"offset_exact":true}]}
{"id":"l06","class":"lowercase-external","question":"when did kepler communications staff meet in lisbon?","ranked_document_ids":["meridian-lisbon-distractor"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-676c9047965194370acf","document_id":"meridian-lisbon-distractor","connector_id":"bundled-crest","title":"Project Meridian Lisbon communications brief","start_char":0,"end_char":210,"text":"Project Meridian communications staff met in Lisbon during June 1987. The Harbor Institute reviewed press clippings for the Portuguese media campaign. This brief does not concern the Vienna field demonstration.","rank":1,"score":6.70470794,"score_components":{"bm25":3.704707944043842,"coverage":0.5,"fuzzy":0.0,"phrase":0.0,"title":1.0},"matched_terms":["communication","staff","lisbon"],"offset_exact":true}]}
{"id":"l07","class":"lowercase-external","question":"what instruments are listed in the zephyr field note?","ranked_document_ids":["meridian-coordination","meridian-observation"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-4956460d5a45d9e6c5c3","document_id":"meridian-coordination","connector_id":"bundled-crest","title":"Project Meridian Vienna coordination note","start_char":0,"end_char":254,"text":"Project Meridian field note. The Harbor Institute acted as the organizing body for the Vienna pilot. Its conveners scheduled the first field exercise for 14 May 1987. Eastbridge Laboratory supplied instruments but did not direct the organizing committee.","rank":1,"score":4.84596149,"score_components":{"bm25":1.9459614889473913,"coverage":0.6,"fuzzy":0.0,"phrase":0.0,"title":0.5},"matched_terms":["instrument","field","note"],"offset_exact":true},{"id":"evidence-dcb521a91bb47c381917","document_id":"meridian-observation","connector_id":"bundled-crest","title":"Vienna demonstration observer correction","start_char":0,"end_char":252,"text":"Observer correction for Project Meridian. The Vienna demonstration began on 16 May 1987, not 14 May as stated in the preliminary scheduling note. Harbor Institute provided convening support, while Eastbridge Laboratory led operations at the field site.","rank":2,"score":2.26349541,"score_components":{"bm25":0.6634954090870641,"coverage":0.4,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["field","note"],"offset_exact":true}]}
{"id":"l08","class":"lowercase-external","question":"did the aurora observer correction mention the field site?","ranked_document_ids":["meridian-observation","meridian-coordination","meridian-lisbon-distractor"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-dcb521a91bb47c381917","document_id":"meridian-observation","connector_id":"bundled-crest","title":"Vienna demonstration observer correction","start_char":0,"end_char":252,"text":"Observer correction for Project Meridian. The Vienna demonstration began on 16 May 1987, not 14 May as stated in the preliminary scheduling note. Harbor Institute provided convening support, while Eastbridge Laboratory led operations at the field site.","rank":1,"score":6.77733838,"score_components":{"bm25":3.110671710893363,"coverage":0.6666666666666666,"fuzzy":0.0,"phrase":0.0,"title":1.0},"matched_terms":["observer","correction","field","site"],"offset_exact":true},{"id":"evidence-4956460d5a45d9e6c5c3","document_id":"meridian-coordination","connector_id":"bundled-crest","title":"Project Meridian Vienna coordination note","start_char":0,"end_char":254,"text":"Project Meridian field note. The Harbor Institute acted as the organizing body for the Vienna pilot. Its conveners scheduled the first field exercise for 14 May 1987. Eastbridge Laboratory supplied instruments but did not direct the organizing committee.","rank":2,"score":2.44724987,"score_components":{"bm25":1.113916538016323,"coverage":0.3333333333333333,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["observer","field"],"offset_exact":true},{"id":"evidence-676c9047965194370acf","document_id":"meridian-lisbon-distractor","connector_id":"bundled-crest","title":"Project Meridian Lisbon communications brief","start_char":0,"end_char":210,"text":"Project Meridian communications staff met in Lisbon during June 1987. The Harbor Institute reviewed press clippings for the Portuguese media campaign. This brief does not concern the Vienna field demonstration.","rank":3,"score":2.06500905,"score_components":{"bm25":0.7316757175374949,"coverage":0.3333333333333333,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["observer","field"],"offset_exact":true}]}
{"id":"l09","class":"lowercase-external","question":"which polaris scheduling note discussed press clippings?","ranked_document_ids":["meridian-lisbon-distractor","meridian-coordination","meridian-observation"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-676c9047965194370acf","document_id":"meridian-lisbon-distractor","connector_id":"bundled-crest","title":"Project Meridian Lisbon communications brief","start_char":0,"end_char":210,"text":"Project Meridian communications staff met in Lisbon during June 1987. The Harbor Institute reviewed press clippings for the Portuguese media campaign. This brief does not concern the Vienna field demonstration.","rank":1,"score":3.80313863,"score_components":{"bm25":2.4698052960292283,"coverage":0.3333333333333333,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["pres","clipping"],"offset_exact":true},{"id":"evidence-4956460d5a45d9e6c5c3","document_id":"meridian-coordination","connector_id":"bundled-crest","title":"Project Meridian Vienna coordination note","start_char":0,"end_char":254,"text":"Project Meridian field note. The Harbor Institute acted as the organizing body for the Vienna pilot. Its conveners scheduled the first field exercise for 14 May 1987. Eastbridge Laboratory supplied instruments but did not direct the organizing committee.","rank":2,"score":3.08657779,"score_components":{"bm25":1.2532444611822613,"coverage":0.3333333333333333,"fuzzy":0.0,"phrase":0.0,"title":0.5},"matched_terms":["schedul","note"],"offset_exact":true},{"id":"evidence-dcb521a91bb47c381917","document_id":"meridian-observation","connector_id":"bundled-crest","title":"Vienna demonstration observer correction","start_char":0,"end_char":252,"text":"Observer correction for Project Meridian. The Vienna demonstration began on 16 May 1987, not 14 May as stated in the preliminary scheduling note. Harbor Institute provided convening support, while Eastbridge Laboratory led operations at the field site.","rank":3,"score":2.71306513,"score_components":{"bm25":1.3797318008178954,"coverage":0.3333333333333333,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["schedul","note"],"offset_exact":true}]}
{"id":"l10","class":"lowercase-external","question":"did the apollo regional archive office record the program?","ranked_document_ids":["meridian-administration"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-e5b52cafa44e2567543d","document_id":"meridian-administration","connector_id":"bundled-crest","title":"Regional archive administration","start_char":0,"end_char":168,"text":"The archive office renewed storage cabinets and travel forms for regional programs. No project costs, funding totals, or procurement budgets were recorded in this note.","rank":1,"score":9.89210276,"score_components":{"bm25":5.558769423548322,"coverage":0.8333333333333334,"fuzzy":0.0,"phrase":0.0,"title":1.0},"matched_terms":["regional","archiv","offic","record","program"],"offset_exact":true}]}
{"id":"l11","class":"lowercase-external","question":"what project costs accompanied genesis storage cabinets?","ranked_document_ids":["meridian-administration"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-e5b52cafa44e2567543d","document_id":"meridian-administration","connector_id":"bundled-crest","title":"Regional archive administration","start_char":0,"end_char":168,"text":"The archive office renewed storage cabinets and travel forms for regional programs. No project costs, funding totals, or procurement budgets were recorded in this note.","rank":1,"score":7.53032854,"score_components":{"bm25":4.863661877698995,"coverage":0.6666666666666666,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["project","cost","storag","cabinet"],"offset_exact":true}]}
{"id":"l12","class":"lowercase-external","question":"were nomad travel forms tied to funding totals?","ranked_document_ids":["meridian-administration"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-e5b52cafa44e2567543d","document_id":"meridian-administration","connector_id":"bundled-crest","title":"Regional archive administration","start_char":0,"end_char":168,"text":"The archive office renewed storage cabinets and travel forms for regional programs. No project costs, funding totals, or procurement budgets were recorded in this note.","rank":1,"score":8.72433062,"score_components":{"bm25":6.057663958122366,"coverage":0.6666666666666666,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["travel","form","fund","total"],"offset_exact":true}]}
{"id":"l13","class":"lowercase-external","question":"who led voyager operations at the field site?","ranked_document_ids":["meridian-observation","meridian-coordination"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-dcb521a91bb47c381917","document_id":"meridian-observation","connector_id":"bundled-crest","title":"Vienna demonstration observer correction","start_char":0,"end_char":252,"text":"Observer correction for Project Meridian. The Vienna demonstration began on 16 May 1987, not 14 May as stated in the preliminary scheduling note. Harbor Institute provided convening support, while Eastbridge Laboratory led operations at the field site.","rank":1,"score":6.41611183,"score_components":{"bm25":3.2161118346301065,"coverage":0.8,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["led","operation","field","site"],"offset_exact":true},{"id":"evidence-4956460d5a45d9e6c5c3","document_id":"meridian-coordination","connector_id":"bundled-crest","title":"Project Meridian Vienna coordination note","start_char":0,"end_char":254,"text":"Project Meridian field note. The Harbor Institute acted as the organizing body for the Vienna pilot. Its conveners scheduled the first field exercise for 14 May 1987. Eastbridge Laboratory supplied instruments but did not direct the organizing committee.","rank":2,"score":2.72635973,"score_components":{"bm25":1.1263597255944624,"coverage":0.4,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["led","field"],"offset_exact":true}]}
{"id":"l14","class":"lowercase-external","question":"did titan instruments reach the field site?","ranked_document_ids":["meridian-coordination","meridian-observation"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-4956460d5a45d9e6c5c3","document_id":"meridian-coordination","connector_id":"bundled-crest","title":"Project Meridian Vienna coordination note","start_char":0,"end_char":254,"text":"Project Meridian field note. The Harbor Institute acted as the organizing body for the Vienna pilot. Its conveners scheduled the first field exercise for 14 May 1987. Eastbridge Laboratory supplied instruments but did not direct the organizing committee.","rank":1,"score":3.20898025,"score_components":{"bm25":1.608980253569693,"coverage":0.4,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["instrument","field"],"offset_exact":true},{"id":"evidence-dcb521a91bb47c381917","document_id":"meridian-observation","connector_id":"bundled-crest","title":"Vienna demonstration observer correction","start_char":0,"end_char":252,"text":"Observer correction for Project Meridian. The Vienna demonstration began on 16 May 1987, not 14 May as stated in the preliminary scheduling note. Harbor Institute provided convening support, while Eastbridge Laboratory led operations at the field site.","rank":2,"score":3.05157746,"score_components":{"bm25":1.4515774569709343,"coverage":0.4,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["field","site"],"offset_exact":true}]}
{"id":"l15","class":"lowercase-external","question":"which cassini communications staff received convening support?","ranked_document_ids":["meridian-lisbon-distractor","meridian-observation"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-676c9047965194370acf","document_id":"meridian-lisbon-distractor","connector_id":"bundled-crest","title":"Project Meridian Lisbon communications brief","start_char":0,"end_char":210,"text":"Project Meridian communications staff met in Lisbon during June 1987. The Harbor Institute reviewed press clippings for the Portuguese media campaign. This brief does not concern the Vienna field demonstration.","rank":1,"score":4.30313863,"score_components":{"bm25":2.4698052960292283,"coverage":0.3333333333333333,"fuzzy":0.0,"phrase":0.0,"title":0.5},"matched_terms":["communication","staff"],"offset_exact":true},{"id":"evidence-dcb521a91bb47c381917","document_id":"meridian-observation","connector_id":"bundled-crest","title":"Vienna demonstration observer correction","start_char":0,"end_char":252,"text":"Observer correction for Project Meridian. The Vienna demonstration began on 16 May 1987, not 14 May as stated in the preliminary scheduling note. Harbor Institute provided convening support, while Eastbridge Laboratory led operations at the field site.","rank":2,"score":3.09786771,"score_components":{"bm25":1.7645343776591722,"coverage":0.3333333333333333,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["conven","support"],"offset_exact":true}]}
{"id":"l16","class":"lowercase-external","question":"did odyssey begin on 14 may 1987 according to the scheduling note?","ranked_document_ids":["meridian-coordination","meridian-observation"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-4956460d5a45d9e6c5c3","document_id":"meridian-coordination","connector_id":"bundled-crest","title":"Project Meridian Vienna coordination note","start_char":0,"end_char":254,"text":"Project Meridian field note. The Harbor Institute acted as the organizing body for the Vienna pilot. Its conveners scheduled the first field exercise for 14 May 1987. Eastbridge Laboratory supplied instruments but did not direct the organizing committee.","rank":1,"score":6.25711905,"score_components":{"bm25":2.8999761972499174,"coverage":0.7142857142857143,"fuzzy":0.0,"phrase":0.0,"title":0.5},"matched_terms":["begin","14","may","1987","note"],"offset_exact":true},{"id":"evidence-dcb521a91bb47c381917","document_id":"meridian-observation","connector_id":"bundled-crest","title":"Vienna demonstration observer correction","start_char":0,"end_char":252,"text":"Observer correction for Project Meridian. The Vienna demonstration began on 16 May 1987, not 14 May as stated in the preliminary scheduling note. Harbor Institute provided convening support, while Eastbridge Laboratory led operations at the field site.","rank":2,"score":6.11958855,"score_components":{"bm25":3.2624456959584136,"coverage":0.7142857142857143,"fuzzy":0.0,"phrase":0.0,"title":0.0},"matched_terms":["begin","14","may","1987","note"],"offset_exact":true}]}
{"id":"z02","class":"fuzzy-subject","question":"When did the Meridiane Project begin?","ranked_document_ids":["meridian-coordination","meridian-observation","meridian-lisbon-distractor"],"passed":false,"deterministic":true,"offsets_exact":true,"chunks":[{"id":"evidence-4956460d5a45d9e6c5c3","document_id":"meridian-coordination","connector_id":"bundled-crest","title":"Project Meridian Vienna coordination note","start_char":0,"end_char":254,"text":"Project Meridian field note. The Harbor Institute acted as the organizing body for the Vienna pilot. Its conveners scheduled the first field exercise for 14 May 1987. Eastbridge Laboratory supplied instruments but did not direct the organizing committee.","rank":1,"score":6.41389317,"score_components":{"bm25":1.4138931682248876,"coverage":1.0,"fuzzy":0.0,"phrase":0.0,"title":1.0},"matched_terms":["meridian","project","begin"],"offset_exact":true},{"id":"evidence-dcb521a91bb47c381917","document_id":"meridian-observation","connector_id":"bundled-crest","title":"Vienna demonstration observer correction","start_char":0,"end_char":252,"text":"Observer correction for Project Meridian. The Vienna demonstration began on 16 May 1987, not 14 May as stated in the preliminary scheduling note. Harbor Institute provided convening support, while Eastbridge Laboratory led operations at the field site.","rank":2,"score":6.01748636,"score_components":{"bm25":1.5174863622237618,"coverage":1.0,"fuzzy":0.0,"phrase":0.0,"title":0.5},"matched_terms":["meridian","project","begin"],"offset_exact":true},{"id":"evidence-676c9047965194370acf","document_id":"meridian-lisbon-distractor","connector_id":"bundled-crest","title":"Project Meridian Lisbon communications brief","start_char":0,"end_char":210,"text":"Project Meridian communications staff met in Lisbon during June 1987. The Harbor Institute reviewed press clippings for the Portuguese media campaign. This brief does not concern the Vienna field demonstration.","rank":3,"score":4.17991353,"score_components":{"bm25":0.513246860558672,"coverage":0.6666666666666666,"fuzzy":0.0,"phrase":0.0,"title":1.0},"matched_terms":["meridian","project"],"offset_exact":true}]}
```

### Summary

```json
{
  "answerable_passed": 28,
  "answerable_total": 40,
  "no_support_passed": 47,
  "no_support_total": 64,
  "graded_failures": 29,
  "contextual_absent_fact_ungraded_total": 8,
  "all_offsets_exact": true,
  "all_repeats_identical": true,
  "all_graded_passed": false
}
```
