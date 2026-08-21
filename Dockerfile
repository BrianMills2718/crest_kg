FROM nginx:1.27-alpine

ARG SOURCE_REVISION=unknown
LABEL org.opencontainers.image.title="CREST Knowledge Graph Viewer" \
      org.opencontainers.image.source="https://github.com/BrianMills2718/crest_kg" \
      org.opencontainers.image.revision="${SOURCE_REVISION}"

COPY web/index.html web/styles.css web/app.js /usr/share/nginx/html/
COPY cia_kg_output/validated_5_documents_relationship_binding_v2.json /usr/share/nginx/html/data/graph.json
COPY web/nginx.conf /etc/nginx/conf.d/default.conf

RUN printf '{"source_revision":"%s"}\n' "$SOURCE_REVISION" > /usr/share/nginx/html/data/build.json

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O - http://127.0.0.1:8080/health >/dev/null || exit 1
