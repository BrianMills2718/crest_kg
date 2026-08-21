# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS llm-client-wheel
COPY --from=llm_client . /src/llm_client
RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir /wheels /src/llm_client

FROM python:3.12-slim

ARG SOURCE_REVISION=unknown
ARG LLM_CLIENT_REVISION=unknown
LABEL org.opencontainers.image.title="CREST Research Workbench" \
      org.opencontainers.image.source="https://github.com/BrianMills2718/crest_kg" \
      org.opencontainers.image.revision="${SOURCE_REVISION}" \
      crest.llm-client.revision="${LLM_CLIENT_REVISION}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CREST_DATA_DIR=/data/workbench \
    LLM_CLIENT_DATA_ROOT=/data/llm-client \
    LLM_CLIENT_DB_PATH=/data/llm-client/llm_observability.db \
    LLM_CLIENT_PROJECT=crest_kg \
    CREST_ROOT_PATH=/crest \
    SOURCE_REVISION=${SOURCE_REVISION}

WORKDIR /app
COPY requirements.txt /app/requirements.txt
COPY --from=llm-client-wheel /wheels /wheels
RUN apt-get update \
    && apt-get install --yes --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir -r requirements.txt /wheels/*.whl \
    && rm -rf /wheels

COPY crest_app /app/crest_app

COPY crest_pipeline.py /app/crest_pipeline.py
COPY prompts /app/prompts
COPY web /app/web
COPY cia_documents/disinformation_complete_20250517_002848.json /app/cia_documents/disinformation_complete_20250517_002848.json
COPY cia_kg_output/validated_5_documents_relationship_binding_v2.json /app/cia_kg_output/validated_5_documents_relationship_binding_v2.json

# Bake the sentence-embedding model into the image. Ranking calls the embedding
# model on every query, so a runtime download would make the first query depend
# on the network and on HuggingFace being reachable. Imported through
# crest_app.semantic_index so the model name has exactly one definition and
# cannot drift from the application. This must run after every source COPY,
# because importing crest_app loads the whole package.
ENV HF_HOME=/opt/hf-cache
RUN python -c "from crest_app.semantic_index import _model; _model()" \
    && chmod -R a+rX /opt/hf-cache
# Fail loudly if the bake above ever stops working, instead of silently
# reaching for the network mid-query.
ENV HF_HUB_OFFLINE=1

RUN useradd --create-home --uid 10001 crest \
    && mkdir -p /data/workbench /data/llm-client \
    && chown -R crest:crest /data
USER crest

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=2).read()" || exit 1

CMD ["uvicorn", "crest_app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
