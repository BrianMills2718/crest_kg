"""Decide whether retrieved passages actually answer a question.

Ranking finds the passages most *about* a question. Abstention is a different
question -- can these passages supply the specific fact being asked for? -- and
the two are not correlated. On the sixteen frozen CREST fixtures, unanswerable
questions ("which airline flew the team to Vienna", "what was the hotel
address") share every topical anchor with answerable ones and out-score them on
cosine similarity roughly half the time.

Seventeen freeze-fix cycles on 2026-08-20 tried to settle this with surface
rules and ended up regressing sixteen abstention cases that had previously
passed. Determining whether a corpus can supply the *kind of thing* a question
asks for is a semantic judgment, so this module asks a model, through the
shared ``llm_client``, and caches the verdict.

The cache is keyed by model, question and exact passage text, so a frozen
regression fixture costs its judgments once and replays offline forever after.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Iterable, Sequence

from pydantic import BaseModel, Field

CACHE_DIR = Path(
    os.environ.get("CREST_ANSWERABILITY_CACHE", Path(__file__).parents[1] / "evaluation" / "answerability_cache")
)
JUDGE_TASK = os.environ.get("CREST_ANSWERABILITY_TASK", "fast_cheap_mid")
JUDGE_REASONING_EFFORT = os.environ.get("CREST_ANSWERABILITY_REASONING", "high")

_SYSTEM = (
    "You decide which supplied source passages actually state the specific "
    "information a question asks for.\n\n"
    "SUPPORTING means the passage states the requested fact. Judge meaning, not "
    "wording:\n"
    "- Paraphrase, synonyms and different parts of speech still support. "
    "'the outfit that staged the trial' is answered by 'the Institute acted as "
    "the organizing body'.\n"
    "- Ordinary world knowledge still supports. A question about Austria is "
    "answered by a passage about Vienna.\n"
    "- A passage may supply only part of a multi-part question and still "
    "support it.\n\n"
    "NOT SUPPORTING, no matter how similar the topic:\n"
    "- The passages are about the same subject but never state the attribute "
    "asked for. If the question asks for an airline, a fuel, an address, a "
    "serial number, a call sign or a count, and no passage states one, nothing "
    "supports it.\n"
    "- The question names a DIFFERENT entity. Treat a proper name that differs "
    "from the one in the passages as a different thing, not as a typo to be "
    "corrected: 'Eastbridle Laboratory' is not 'Eastbridge Laboratory', and the "
    "'Meridiane Project' is not 'Project Meridian'. Never answer about the "
    "entity you think was meant. Only the passages themselves can establish "
    "that two names are the same thing.\n\n"
    "Return the ids of supporting passages only, and an empty list when the "
    "requested fact is absent. Abstaining is the correct answer more often than "
    "not; a passage that merely shares a topic is not evidence."
)


class AnswerabilityVerdict(BaseModel):
    """Which of the supplied passages actually state the requested fact."""

    supporting_ids: list[str] = Field(
        default_factory=list,
        description="Ids of passages that state the requested fact. Empty when absent.",
    )
    # Deliberately unconstrained. A max_length here is not something a provider
    # can enforce at decode time, so it only produces validation retries; the
    # length is trimmed client-side after the call instead.
    reason: str = Field(
        default="",
        description="One sentence naming the requested fact and whether a passage states it.",
    )


class AnswerabilityUnavailable(RuntimeError):
    """Raised when a verdict is needed, is not cached, and cannot be obtained."""


def _fingerprint(model: str, question: str, passages: Sequence[tuple[str, str]]) -> str:
    payload = json.dumps(
        {
            "model": model,
            "reasoning_effort": JUDGE_REASONING_EFFORT,
            "question": question,
            "passages": list(passages),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:40]


def _cache_path(fingerprint: str) -> Path:
    return CACHE_DIR / f"{fingerprint}.json"


def judge_supporting(
    question: str,
    passages: Iterable[tuple[str, str]],
    *,
    trace_id: str = "crest_kg.answerability",
    allow_calls: bool = True,
) -> AnswerabilityVerdict:
    """Return the passages that state the fact ``question`` asks for.

    ``passages`` is an iterable of ``(passage_id, exact_text)``. A cached
    verdict is returned without a model call. With ``allow_calls=False`` a cache
    miss raises rather than silently degrading to a permissive answer -- an
    abstention gate that fails open is not a gate.
    """

    items = list(passages)
    if not items:
        return AnswerabilityVerdict(supporting_ids=[], reason="No candidate passages.")

    from llm_client import call_llm_structured, get_model

    model = get_model(JUDGE_TASK, use_performance=False)
    fingerprint = _fingerprint(model, question, items)
    cached = _cache_path(fingerprint)
    if cached.is_file():
        return AnswerabilityVerdict.model_validate_json(cached.read_text(encoding="utf-8"))
    if not allow_calls:
        raise AnswerabilityUnavailable(
            f"No cached answerability verdict for {fingerprint} and calls are disabled."
        )

    rendered = "\n\n".join(f"[{pid}]\n{text}" for pid, text in items)
    messages = [
        {"role": "system", "content": _SYSTEM},
        {
            "role": "user",
            "content": f"Question:\n{question}\n\nPassages:\n{rendered}",
        },
    ]
    verdict, _result = call_llm_structured(
        model,
        messages,
        response_model=AnswerabilityVerdict,
        task="crest_kg.answerability",
        trace_id=trace_id,
        # Explicit, because llm_client forbids provider reasoning defaults. This
        # is a bounded presence/absence judgment over a few short passages, not
        # an analysis task, so it does not need a high reasoning budget.
        reasoning_effort=JUDGE_REASONING_EFFORT,
        model_policy="enforce_allowlist",
        model_justification=(
            "Resolved through llm_client get_model('judging', use_performance=False) "
            "for one structured passage-answerability verdict."
        ),
    )
    known = {pid for pid, _ in items}
    verdict = AnswerabilityVerdict(
        supporting_ids=[pid for pid in verdict.supporting_ids if pid in known],
        reason=verdict.reason[:300],
    )
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached.write_text(verdict.model_dump_json(indent=2), encoding="utf-8")
    return verdict
