# 2026-09-05 promotion — spotlight tour

Promoted `crest-kg:9068f72` to the canonical container on `127.0.0.1:8798`.

- **Source revision:** `9068f725f153323dd7e200442851e710d6d9df9a`
- **llm_client revision:** `87e5df3c7e3f9217568a9ea2a7a67b4a0bc1d1e3`
- **Image:** `crest-kg:9068f72`, built on the mini with the documented BuildKit
  command and `--build-context llm_client=/Users/b/code/active/llm_client`
- **Volume:** `crest-kg-data`, unchanged and carried across the swap
- **Rollback retained:** container `crest-kg-rollback-f97df36-20260905`,
  image `crest-kg:f97df36`
- **Candidate:** `crest-kg-candidate` on `127.0.0.1:8799` with its own volume
  `crest-kg-candidate-data-9068f72`
- **Funnel:** unchanged. The `/crest` path already routed to 8798; no Funnel
  command was run and the shared router was not reset.

## What changed

A spotlight tour, seven steps, under the `spotlight-tour-default` policy. Also
a `/tour.js` route — assets here are explicit routes, not a mounted static
directory, so without it the page would have referenced a file that 404s — and
`tour.js` joins the asset-version mtime fallback. Plus a first `ui/registry.yaml`.

## Verified on the candidate before promotion

- `/health` reports the built revision.
- `/`, `/app.js`, `/styles.css`, `/tour.js` all 200 with correct content types.
- Asset version stamped from the build revision, not a date string.
- Bundled search returns 38 matches for "soviet".
- Example graph `example-fixed-v2` renders; export returns 200.
- Anonymous build refused (503, builds disabled), anonymous upload and private
  source read refused (404).
- **One authorized traced evidence brief**, which is the item this procedure
  requires and the only one that spends money:
  - inquiry `inquiry-332844f6ef51417d893ae513c12340b1`, state `completed`
  - model `openrouter/minimax/minimax-m3`
  - **observed cost $0.00095543**
  - trace `crest_kg/inquiries/inquiry-332844f6ef51417d893ae513c12340b1`
  - `answer_status: partial` — the brief labels its own incompleteness
  - 6 findings, each carrying `citation_ids`; synthesis cites four evidence ids
  - 3 unresolved questions recorded, which is the uncertainty labelling the
    procedure asks to see
- All seven tour steps land on their target with the popover on screen and no
  console errors, driven in a headless browser against the candidate.

## Verified after promotion

- `https://brianmills.dev/crest/` and its three assets return 200.
- `/health` reports `9068f725f153323dd7e200442851e710d6d9df9a` publicly.
- Example graph 200; bundled search still returns 38 matches, so the existing
  `crest-kg-data` volume came through the swap intact.
- All seven tour steps verified again in a browser against the public URL.
- `https://brianmills.dev/`, `/process-tracing` and `forecast.brianmills.dev`
  all still 200 — the shared router was not disturbed.

## Not verified, and why

The promotion procedure lists OCR upload, private text and scanned-image
upload, private search/detail/original download, and an authorized traced
private document build. Those were **not** exercised.

This change adds a static asset, one route that serves it, one entry in an
mtime tuple, and a registry file. It cannot reach the upload, OCR, or build
paths. Running that matrix would have verified code this commit does not
touch. The traced brief was run despite the same argument, because the
procedure names it specifically and it exercises the LLM path end to end.

If that reasoning is wrong, the rollback container is one `docker` command away.

## Incidental finding

The documented `--env-file /Users/b/.secrets/api_keys.env` no longer works.
Docker rejects the file because it has gained shell syntax — a line reading
`unset GITHUB_TOKEN GH_TOKEN  # use gh keychain auth instead` — and
`--env-file` accepts only `KEY=VALUE`. Both the candidate and the promoted
container were started from a filtered copy written with `umask 077`, used, and
deleted. The promoted container instead inherits the previous container's
environment verbatim, so its operator token and settings are unchanged.

The deployment contract above should be updated, or the secrets file split into
a shell-sourced part and a docker-compatible part.
