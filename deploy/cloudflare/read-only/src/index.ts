/** Public edge for the full CREST workbench on Brian's personal VPS. */

interface Env {
  CREST_BACKEND_ORIGIN: string;
}

const FALLBACK_STATUSES = new Set([502, 503, 504, 521, 522, 523, 524, 530]);

function unavailablePage(detail: string): Response {
  return new Response(
    `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CREST — temporarily unavailable</title></head><body><main><h1>CREST is temporarily unavailable</h1><p>The research server is not answering right now. Saved work is on durable storage and will return with the server.</p><p>${detail}</p></main></body></html>`,
    {
      status: 503,
      headers: {
        "content-type": "text/html; charset=utf-8",
        "cache-control": "no-store",
        "retry-after": "120",
      },
    },
  );
}

export function backendPath(pathname: string): string | null {
  if (pathname === "/crest") return "/";
  if (pathname.startsWith("/crest/")) return pathname.slice("/crest".length);
  return null;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const incoming = new URL(request.url);
    const pathname = backendPath(incoming.pathname);
    if (pathname === null) {
      return new Response("Not found\n", { status: 404 });
    }

    if (!env.CREST_BACKEND_ORIGIN) {
      return unavailablePage("CREST_BACKEND_ORIGIN is not configured.");
    }

    const target = new URL(pathname + incoming.search, env.CREST_BACKEND_ORIGIN);
    const headers = new Headers(request.headers);
    headers.set("x-forwarded-host", incoming.host);
    headers.set("x-forwarded-prefix", "/crest");
    headers.set("x-forwarded-proto", "https");
    headers.delete("host");

    let response: Response;
    try {
      response = await fetch(
        new Request(target, {
          method: request.method,
          headers,
          body:
            request.method === "GET" || request.method === "HEAD"
              ? undefined
              : request.body,
          redirect: "manual",
        }),
      );
    } catch (error) {
      console.error("CREST backend unreachable", error);
      return unavailablePage("The backend connection failed.");
    }

    if (
      FALLBACK_STATUSES.has(response.status) &&
      request.method === "GET" &&
      (request.headers.get("accept") || "").includes("text/html")
    ) {
      return unavailablePage(`Backend returned HTTP ${response.status}.`);
    }

    const outgoing = new Headers(response.headers);
    outgoing.delete("content-encoding");
    outgoing.delete("content-length");
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: outgoing,
    });
  },
};
