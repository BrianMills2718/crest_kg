# Cloudflare public edge

This Worker publishes <https://brianmills.dev/crest/> while the full CREST
workbench runs on Brian's personal VPS. It strips the public `/crest` prefix and
proxies to `CREST_BACKEND_ORIGIN`, currently
`https://crest-api.brianmills.dev` through the `personal-vps` Cloudflare tunnel.

The edge holds no application data or secrets. Anonymous search, source review,
the bundled graph, and export remain public. Uploads, private sources, evidence
briefs, and graph builds retain the application's existing bearer-token check;
the browser stores an entered operator token only in session storage.

The former Cloudflare Container was read-only and ephemeral. Migration `v2`
deletes its Durable Object class after the VPS deployment becomes the public
backend.

```bash
npm install
npm test
npm run check
npm run deploy
```

Wrangler reads Cloudflare credentials from the environment. Never print or
commit them. If the backend hostname moves, update only `CREST_BACKEND_ORIGIN`
in `wrangler.jsonc`.

Verify the root, health, capabilities, bundled search, operator-token unlock,
and one authenticated write journey through the public hostname after deploy.
