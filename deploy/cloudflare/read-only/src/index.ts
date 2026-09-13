import { Container, getContainer } from "@cloudflare/containers";

export class CrestReviewContainer extends Container<Env> {
  defaultPort = 8080;
  requiredPorts = [8080];
  sleepAfter = "15m";
  enableInternet = false;
  envVars = {
    CREST_ROOT_PATH: "/crest",
    CREST_BUILD_ENABLED: "0",
    CREST_BRIEF_ENABLED: "0",
    CREST_UPLOAD_ENABLED: "0",
  };

  override async fetch(request: Request): Promise<Response> {
    await this.startAndWaitForPorts({
      ports: this.defaultPort,
      cancellationOptions: {
        instanceGetTimeoutMS: 180_000,
        portReadyTimeoutMS: 180_000,
        waitInterval: 500,
      },
    });
    return this.containerFetch(request, this.defaultPort);
  }

  override onError(error: unknown) {
    console.error("CREST review container failed", error);
    throw error;
  }
}

function containerRequest(request: Request): Request {
  const incoming = new URL(request.url);
  const forwardedUrl = new URL(request.url);
  forwardedUrl.pathname = incoming.pathname.slice("/crest".length) || "/";
  const headers = new Headers(request.headers);
  headers.set("X-Forwarded-Host", incoming.host);
  headers.set("X-Forwarded-Prefix", "/crest");
  headers.set("X-Forwarded-Proto", "https");
  return new Request(forwardedUrl, {
    method: request.method,
    headers,
    body: request.body,
    redirect: "manual",
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const incoming = new URL(request.url);
    if (incoming.pathname !== "/crest" && !incoming.pathname.startsWith("/crest/")) {
      return new Response("Not found\n", { status: 404 });
    }
    return getContainer(env.CREST_REVIEW_CONTAINER, "public-review-v2").fetch(
      containerRequest(request),
    );
  },
  async scheduled(
    _controller: ScheduledController,
    env: Env,
    ctx: ExecutionContext,
  ): Promise<void> {
    ctx.waitUntil(
      getContainer(env.CREST_REVIEW_CONTAINER, "public-review-v2")
        .fetch(new Request("https://brianmills.dev/health"))
        .then((response) => {
          if (!response.ok) {
            throw new Error(`CREST keepalive returned ${response.status}`);
          }
        }),
    );
  },
};
