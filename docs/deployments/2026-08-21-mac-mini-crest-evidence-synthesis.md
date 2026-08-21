# CREST evidence-synthesis deployment receipt

Observed at `2026-08-21T09:39:12Z`.

## Promoted artifact

- Canonical URL: <https://brian-mac-mini.tail9c321e.ts.net/crest/>
- Runtime source revision:
  `d884f493a73bc289bcbbc72399294aa77cdd4ce4`
- Independent sign-off artifact revision:
  `677a441e13ccc4c4be0a6c5305a55b9ce23e4bd8`
- Image: `crest-kg:d884f49`
- Image ID:
  `sha256:393a4ca847733b15a52d99c592c5eafe90943d30ddbfefa1d3d29dbed360b692`
- Source archive SHA-256:
  `5b7f04c7f62c42fec23a31fae1ab0228aabeca23fce1c700272c443f1300a6c7`
- Embedded `llm_client` revision:
  `87e5df3c7e3f9217568a9ea2a7a67b4a0bc1d1e3`
- Container: `crest-kg`, bound to `127.0.0.1:8798`, using the existing
  `crest-kg-data` volume.
- Public and loopback health both returned `crest-workbench`, status `ok`, and
  the full runtime revision above before and after restart.

The image was built from the hash-checked source archive, tested first as
`crest-kg-candidate` on `127.0.0.1:8799` with the isolated
`crest-kg-candidate-data-d884f49` volume, and then promoted without changing
the shared Funnel configuration.

## Deterministic gate

The fresh execution-based decision record is
[`evidence_retrieval_decision_signoff_v17.md`](../../evaluation/evidence_retrieval_decision_signoff_v17.md).
It signed off the exact runtime revision for deterministic passage retrieval
over small synthetic collections only:

- frozen fixtures v5-v16: 12 fixtures and 99 cases passed twice with
  byte-identical aggregate output and valid exact offsets;
- fresh verifier cases: 8 retrieval and 4 chunking cases passed twice with
  byte-identical output;
- repository suite: 51 passed with one Starlette/httpx deprecation warning;
- `node --check web/app.js`: passed;
- `python -m pip check`: passed.

This gate does not claim arbitrary-language parsing, corpus recall, answer
classification, semantic entailment, production scale, or live-CIA coverage.

## Candidate observation

The operator created the four-source Project Meridian collection and asked:

> Which group organized the Austrian field demonstration, and what date
> disagreement exists?

The browser ranked exact Vienna passages, generated a persistent partial brief,
selected the two cited sources, built a focused graph, refreshed, reopened both
artifacts from Recent activity, restarted the candidate container, and reopened
both again.

- Brief trace:
  `crest_kg/inquiries/inquiry-b55d747d75ab4124b74ec3014a11adf3`
- Brief execution: one completed `call_llm_structured` call through
  `openrouter/minimax/minimax-m3`, 1,301 tokens, `$0.00083028`, zero LLM errors.
- Graph trace:
  `crest_kg/workbench/eaf854aee93a429590a98c80e4346888`
- Graph execution: two completed structured extraction calls, 2,897 tokens,
  `$0.00149532`, zero LLM errors.
- Result: Harbor Institute identified as organizer/convenor; 14 versus 16 May
  1987 preserved as a contradiction; Eastbridge's operational role retained as
  unresolved; 10 entities and 4 relationships rendered from two cited sources.
- Browser recovery: 16 observed API responses, zero failed API responses, zero
  console errors, and zero runtime exceptions.
- Candidate screenshots before and after restart had the same SHA-256:
  `544f377552bd839722ab0e43c6d0ea46d42bf26a6ce5e107e2b384cac60a285e`.

## Canonical observation

The same question-to-evidence-to-graph workflow was executed through Chrome at
the public `/crest/` URL after promotion.

- Collection: Project Meridian, four sources.
- Brief trace:
  `crest_kg/inquiries/inquiry-0561881efd2b4568be13de078f5fc036`
- Brief execution: one completed structured call through
  `openrouter/minimax/minimax-m3`, 1,420 tokens, `$0.00097308`, zero LLM errors.
- Graph trace:
  `crest_kg/workbench/371e28c2898d44d8a3d39592283c268d`
- Graph execution: two completed structured extraction calls, 3,045 tokens,
  `$0.00171583`, zero LLM errors.
- Result: four citation-valid findings, explicit support and contradiction,
  unresolved 14/16 May and Harbor/Eastbridge role questions, two cited source
  documents, 12 entities, and 4 relationships.
- Browser recovery: 20 observed API responses, zero failed API responses, zero
  console errors, and zero runtime exceptions.
- The live container was restarted and the same inquiry and graph reopened from
  persisted history while public health continued to report the exact runtime
  revision.
- Canonical screenshot SHA-256 before restart:
  `5364dc601d4fb891ab7e45fcb67629c504d408d1aafb4beabcff2b291b0aac42`.
- Canonical screenshot SHA-256 after restart:
  `4c8369cb75785807823c44b565938f9371398d2253ab3999b85726b596f4e7bf`.

The four screenshots are retained on the Mac mini under
`/Users/b/runtime/crest-kg/receipts/2026-08-21-evidence-synthesis/`.

## Authorization and routing

- Direct candidate requests without an operator token returned 403 for evidence
  preview, inquiry create/list/read, private graph read, and upload.
- A tailnet request to the canonical URL was correctly authorized by its trusted
  Tailscale identity. A separate public-resolver/IP probe, which bypassed
  tailnet identity injection, returned 403 for evidence preview, inquiry
  create/list/read, private graph read, and upload.
- External capabilities remained readable but reported graph, brief, and upload
  actions as enabled and unauthorized.
- The temporary tailnet-authenticated privacy-probe upload was deleted and a
  follow-up upload listing confirmed no probe document remained.
- `tailscale funnel status` still mapped only `/crest` to
  `http://127.0.0.1:8798`; the root and `/crest/` both returned HTTP 200, and no
  sibling Funnel route was changed.

## Rollback and retained state

- Prior live container: `crest-kg-rollback-8263c1e-20260821`, stopped.
- Prior image: `crest-kg:8263c1e`.
- Prior image ID:
  `sha256:deb702583c2ae52e5aa4729d4e74313bd446e8cc33af3a3508afa6a9b3ee6372`.
- The rollback container and promoted container point to the same durable live
  volume, but only the promoted container is running.
- The tested candidate container and its isolated volume are retained stopped;
  they are not on the canonical route.

Rollback is to stop and remove or rename the promoted `crest-kg`, rename the
retained rollback container to `crest-kg`, start it on loopback port 8798, and
recheck `/health` and `/crest/`. Funnel must not be reset.
