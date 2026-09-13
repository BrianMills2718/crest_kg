# Cloudflare read-only workbench

This Worker and Container publish the read-only CREST workbench at
<https://brianmills.dev/crest/>. Cloudflare is the canonical public host; the
Mac Mini is not part of the request path.

The repository-root Dockerfile requires `llm_client` as a named build context.
Export the pinned shared-client revision into a clean temporary directory so
linked worktrees, caches, and local environments are not copied into Docker:

```bash
export LLM_CLIENT_REPO=/absolute/path/to/llm_client
export LLM_CLIENT_CONTEXT="$(mktemp -d)"
git -C "$LLM_CLIENT_REPO" archive 54bb657c316b37b13369c251fc8e60c6cecad995 \
  | tar -x -C "$LLM_CLIENT_CONTEXT"
docker build \
  --build-context llm_client="$LLM_CLIENT_CONTEXT" \
  --build-arg SOURCE_REVISION=5f586075d551265999a5ca00245e70d2ae7d1c88 \
  --build-arg LLM_CLIENT_REVISION=54bb657c316b37b13369c251fc8e60c6cecad995 \
  -t crest-review:5f58607 .
```

Set `DOCKER_BIN` to the Docker CLI path when it is not already on `PATH`, run
`npx wrangler containers push crest-review:5f58607 --path-to-docker
"$DOCKER_BIN"`, and remove only the exact temporary context created above.
Then run `npm install`, `npm run check`, and `npm run deploy` here. Update both
source pins and the image tag whenever either repository changes.

The public recovery intentionally disables graph building, evidence briefs,
and uploads. It serves the tracked 40-document archive and audited example
graph without secrets or a persistent volume. A five-minute scheduled health
request keeps the single basic instance warm; the Worker permits a three-minute
cold start if the instance is stopped.
