# Mac mini CREST viewer deployment receipt

- Observed at: `2026-08-21T02:14:02Z`
- Public URL: <https://brian-mac-mini.tail9c321e.ts.net/crest/>
- Capability: `crest-kg-evidence-viewer`
- Profile: static `service` with read-only browser UI
- Source revision: `a3439e523962511f41b90f7bf30771ba2b8deb2b`
- Image ID: `sha256:2b3a14bdd986135a039c2098e844bed9fe1206d09b42ead57ba2c5749cb68207`
- Container ID: `e170175b27a048acbffe036b63a56eadf38945c60e7694a80c4c8484287ee624`
- Target: `Bs-Mac-mini.local`, macOS `26.5.2`, Docker `29.3.1`,
  Tailscale `1.102.2`, Chrome `151.0.7922.170`
- Route: Funnel `/crest` to `127.0.0.1:8798`; the pre-existing `/`
  and all sibling routes remained configured.

## Verification

| Criterion | Executed scenario | Result | Durable artifact or receipt | Limitation |
| --- | --- | --- | --- | --- |
| Exact deployment | Read public `data/build.json` and inspect the canonical container | PASS: both identify the source revision and image above | Docker image/container metadata on the target | Invalidated by source, image, container, Docker, Funnel, or target-host changes |
| API/data contract | Public `/`, `/health`, and `data/graph.json` | PASS: HTTP 200; graph contains 5 documents, 82 entities, 3 accepted relationships, and 72 rejections | Graph SHA-256 `1abae3739b7a32f01d83814ac9b68a755403b7cba2e00355084f5f15f4fe5837` | Fixed five-document artifact; corpus recall remains unknown |
| Invalid path | Public `definitely-missing` | PASS: HTTP 404 | Canonical container access log at `2026-08-21T02:14:04Z` | This is a static service, not a typed application API |
| Missing dependency | Build the exact source archive without the canonical graph JSON | PASS: image build failed at the required `COPY` | `$HOME/runtime/crest-kg/candidates/61b7e1a3/missing-graph-build.log`, SHA-256 `2886e366aa024c5c47a6127e4cab6d9cd8277bedf4cbbe71f51b9f44ac5e4556` | Negative control used the immediately preceding revision; the graph-copy dependency is unchanged in the deployed revision |
| Browser composition | In deployed Chrome, load the public URL, select a relationship, inspect its exact quote and grounded spans, switch to all entities, and search for `CIA` | PASS: `CIA` returned 1 of 82 entities; no console exceptions, failed requests, or HTTP errors | Target-host browser run and canonical container access log | Technical execution only; stakeholder comprehension has not been claimed |
| Responsive rendering | Capture and inspect 1440×1000 and 390×844 public renders | PASS: hierarchy remains legible with no observed clipping or horizontal overflow | `$HOME/runtime/crest-kg/candidates/a3439e52/live-desktop-cdp.png` and `live-mobile.png` | Chrome only; no browser-matrix claim |
| Service lifecycle | Inspect health after promotion | PASS: container is `healthy` with `unless-stopped` restart policy | Docker state and `/health` receipt | No persistence or telemetry beyond container logs |

The capability evidence reaches `deployment_verified` for this bounded static
service in report-only mode. Project Meta's independent certification observer
is not yet available, so this receipt is not represented as a hard enforcement
verdict.

## Rollback

The stopped `crest-kg-rollback-61b7e1a3` container and its image remain on the
Mac mini. To roll back, stop and rename the current `crest-kg`, rename that
rollback container to `crest-kg`, start it, and recheck `/health` plus the public
route. The Funnel mapping does not need to change.

## Non-claims

This deployment proves that the audited five-document checkpoint is publicly
served and usable through its bounded evidence-inspection flow. It does not
establish corpus recall, extraction generalization, production SLOs, stakeholder
comprehension, or a finished full-corpus CREST product.
