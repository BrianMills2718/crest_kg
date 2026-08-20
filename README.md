# CREST Knowledge Graph

This repository preserves experiments over CIA CREST and UFO Reading Room
material. `crest_pipeline.py` is the canonical extraction path. The older
numbered scripts are retained as historical code; their downloaded inputs,
progress snapshots, and generated visualizations remain in the local archive
but are excluded from Git because they are reproducible or redundant artifacts.

The initial Git history intentionally tracks the canonical prompt and tests,
the exact five-document source corpus, and the validated graph. This keeps the
grounded result independently checkable without committing the full 108 MB
working archive.

## What the canonical path guarantees

- The corpus file is explicit, and document selection is sorted by stable
  CREST/FOIA identifiers.
- Model responses are validated as strict Pydantic structures by the shared
  `llm_client` structured-output boundary.
- Every entity and relationship must cite a bounded numbered source-line range;
  the pipeline materializes the exact original quote and character offsets.
- Entity identity includes semantic type, so a location and organization with
  the same name cannot be silently collapsed.
- A graph cannot be written with duplicate IDs, dangling relationships, unknown
  provenance documents, or ungrounded assertions.
- Existing output is never overwritten unless `--force` is explicit.

## Inspect the deterministic five-document selection

This command is offline and does not call a model:

```bash
python crest_pipeline.py inspect-corpus \
  --corpus cia_documents/disinformation_complete_20250517_002848.json \
  --limit 5
```

The manifest reports each source ID, URL, full-text SHA-256, total character
count, and the exact analyzed character and line window.

## Run an extraction

Extraction uses the workspace's shared `llm_client`, its `graph_building` model
route, structured output, traces, and cost ledger. A positive total dollar
ceiling is mandatory:

```bash
python crest_pipeline.py extract \
  --corpus cia_documents/disinformation_complete_20250517_002848.json \
  --limit 5 \
  --max-chars 15000 \
  --max-budget-usd 1.00 \
  --output cia_kg_output/validated_5_documents.json
```

The command keeps all five calls under one root budget scope and writes only
after every document has passed structured and evidence validation. The default
15,000-character source window is recorded in the output rather than hidden.

Validate an artifact independently:

```bash
python crest_pipeline.py validate \
  --graph cia_kg_output/validated_5_documents.json
```

## Verified vertical

The canonical path was exercised against the explicit five-document selection
on 2026-08-20:

- artifact: `cia_kg_output/validated_5_documents.json`
- root trace: `crest_kg/extraction/20260820-line-grounded-five-document`
- resolved model: `openrouter/minimax/minimax-m3`
- observed successful-run cost: `$0.03924106`
- result: 5 documents, 91 entities, and 79 relationships
- integrity: 0 duplicate IDs, 0 dangling relationships, and 0 ungrounded
  relationships

An independent replay also matched all five source hashes and all 177 entity
and relationship evidence spans back to the original corpus text.

## Focused verification

```bash
python -m pytest -q tests/test_crest_pipeline.py
```

The focused suite covers deterministic selection, rejection of dangling
relationships, exact line-to-character evidence grounding, typed identity, five-document graph
integrity, serialization round-tripping, and overwrite refusal.
