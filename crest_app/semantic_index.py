"""Semantic ranking for CREST evidence chunks.

This replaces the hand-written lexical scoring stack that grew to 1,059 lines
across seventeen freeze-fix cycles on 2026-08-20. That stack fought paraphrase
with surface rules -- a hand-rolled stemmer, hardcoded synonym tables,
``difflib`` fuzzy scoring, "benign name variants", structural subject parsing --
and each loosening it made to admit a paraphrase eroded its ability to abstain.

Ranking here is a static sentence embedding (``model2vec``), which needs no
surface rules and no network at query time. Measured on the sixteen frozen
fixtures, embeddings alone place the expected documents in the exact top-k for
93.4% of answerable cases.

Embeddings deliberately do NOT decide abstention. On the same fixtures the
best-document cosine for answerable cases (p10 0.348) sits below that of
unanswerable ones (p90 0.566), because an unanswerable question is usually
still on-topic: "which airline flew the team to Vienna" is topically identical
to the Vienna coordination note that cannot answer it. Abstention is a semantic
judgment and lives in ``crest_app.answerability``.
"""

from __future__ import annotations

import functools
import re

import numpy as np

# Static embeddings: ~30MB, CPU-only, no torch. Downloaded once and cached by
# the HuggingFace hub; a fresh environment needs network for that first load.
EMBEDDING_MODEL = "minishlab/potion-base-8M"


@functools.lru_cache(maxsize=1)
def _model():
    from model2vec import StaticModel

    return StaticModel.from_pretrained(EMBEDDING_MODEL)


def _unit(matrix: np.ndarray) -> np.ndarray:
    return matrix / (np.linalg.norm(matrix, axis=-1, keepdims=True) + 1e-9)


def embed(texts: list[str]) -> np.ndarray:
    """Return L2-normalized embeddings, one row per text."""

    if not texts:
        return np.zeros((0, 256), dtype=np.float32)
    return _unit(np.asarray(_model().encode(texts), dtype=np.float32))


_TOKEN = re.compile(r"[A-Za-z0-9]+")


def lexical_overlap(question: str, text: str) -> float:
    """Fraction of distinct question tokens that appear verbatim in ``text``.

    A small tie-breaker only. It is never an admission gate: making a lexical
    signal decide admission is precisely what failed before.
    """

    q = {t.casefold() for t in _TOKEN.findall(question)}
    if not q:
        return 0.0
    body = {t.casefold() for t in _TOKEN.findall(text)}
    return len(q & body) / len(q)


def rank_texts(question: str, texts: list[str], *, lexical_weight: float = 0.15) -> list[float]:
    """Score each text against the question. Higher is more relevant."""

    if not texts:
        return []
    vectors = embed([question] + texts)
    query, body = vectors[0], vectors[1:]
    cosine = body @ query
    overlap = np.array([lexical_overlap(question, t) for t in texts], dtype=np.float32)
    return list((1.0 - lexical_weight) * cosine + lexical_weight * overlap)
