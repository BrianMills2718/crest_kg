#!/usr/bin/env python3
"""Build a retrieval probe from the real CREST documents in ``cia_documents/``.

The sixteen frozen fixtures are 13 synthetic documents of about 210 characters
each, authored in one night by the lexical loop this ranker replaced. The real
corpus is 40 OCR'd government memoranda with a median length of 6,931
characters -- roughly 33x longer, far noisier, and multi-chunk per document.
Numbers measured on the fixtures do not automatically transfer, so this probe
measures the same two properties on the real text.

Ground truth is structural rather than hand-labelled. A question is generated
from one exact passage, so the document that passage came from is by
construction the one that answers it:

* **recall** -- ask the question against the whole corpus. The source document
  must come back, and the gate must not abstain.
* **abstention** -- ask the same question against the corpus with the source
  document removed. Nothing else states that fact, so the gate must abstain.

The abstention half is the strict one, and it is the property the overnight
lexical loop regressed.
"""

from __future__ import annotations

import argparse
import glob
import json
import random
import re
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from pydantic import BaseModel, Field  # noqa: E402

OUT = ROOT / "evaluation" / "real_corpus_probe.json"
# Fixed so the probe is reproducible; ground truth does not depend on it.
SEED = 20260821


class ProbeQuestion(BaseModel):
    """A question answerable only from the supplied passage."""

    question: str = Field(
        description=(
            "A specific factual question answered by this passage and by nothing "
            "else. Name the entities involved rather than saying 'the document'."
        )
    )
    answer: str = Field(description="The answer, quoted or closely paraphrased from the passage.")


def load_documents() -> dict[str, dict]:
    documents: dict[str, dict] = {}
    for path in sorted(glob.glob(str(ROOT / "cia_documents" / "*.json"))):
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        for item in payload if isinstance(payload, list) else [payload]:
            if not isinstance(item, dict) or not item.get("body_text"):
                continue
            identity = item.get("url") or item.get("title")
            if identity:
                documents[identity] = item
    return documents


def pick_passage(body: str, *, rng: random.Random, window: int = 700) -> str | None:
    """Pick a clean, information-dense window of the OCR'd body.

    These scans carry single newlines and no blank-line paragraph breaks, so
    splitting on paragraphs finds a usable passage in only 3 of 40 documents.
    Normalize the whitespace and take a sentence-aligned window instead, past
    the release-stamp header every CREST scan begins with.
    """

    text = " ".join(body.split())
    text = re.sub(
        r"(Approved For Release|Sanitized Copy Approved for Release)[^A-Z]{0,80}"
        r"CIA-RDP[\w-]+",
        " ",
        text,
    )
    text = " ".join(text.split())
    if len(text) < window + 400:
        return None

    # Start past the header, and align to a sentence boundary so the passage
    # does not open mid-clause.
    lowest, highest = 300, len(text) - window - 100
    if highest <= lowest:
        return None
    start = rng.randint(lowest, highest)
    boundary = text.find(". ", start)
    if boundary != -1 and boundary - start < 300:
        start = boundary + 2
    passage = text[start : start + window]
    tail = passage.rfind(". ")
    if tail > window // 2:
        passage = passage[: tail + 1]

    # Reject windows that are mostly OCR noise rather than prose.
    letters = sum(character.isalpha() or character.isspace() for character in passage)
    if len(passage) < 320 or letters / len(passage) < 0.85:
        return None
    return passage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=25, help="How many probe questions to build.")
    args = parser.parse_args()

    from llm_client import call_llm_structured, get_model

    documents = load_documents()
    rng = random.Random(SEED)
    identities = sorted(documents)
    rng.shuffle(identities)

    model = get_model("fast_cheap_mid", use_performance=False)
    probes: list[dict] = []
    for identity in identities:
        if len(probes) >= args.count:
            break
        passage = pick_passage(documents[identity]["body_text"], rng=rng)
        if passage is None:
            continue
        generated, _ = call_llm_structured(
            model,
            [
                {
                    "role": "system",
                    "content": (
                        "Write one specific factual question that this passage "
                        "answers and that could not be answered without it. Name "
                        "the people, organisations, dates or documents involved. "
                        "Never refer to 'the passage', 'the document' or 'the text'."
                    ),
                },
                {"role": "user", "content": passage},
            ],
            response_model=ProbeQuestion,
            task="crest_kg.real_corpus_probe",
            trace_id=f"crest_kg.probe/{len(probes)}",
            reasoning_effort="none",
            model_policy="enforce_allowlist",
            model_justification=(
                "Resolved through llm_client get_model('fast_cheap_mid') to author "
                "one probe question from one exact CREST passage."
            ),
        )
        probes.append(
            {
                "probe_id": f"probe-{len(probes):03d}",
                "source_identity": identity,
                "source_title": documents[identity].get("title", ""),
                "passage": passage,
                "question": generated.question,
                "expected_answer": generated.answer,
            }
        )
        print(f"  {probes[-1]['probe_id']}: {generated.question[:96]}")

    OUT.write_text(
        json.dumps(
            {
                "schema_version": "crest-real-corpus-probe/v1",
                "seed": SEED,
                "generator_model": model,
                "document_count": len(documents),
                "probes": probes,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {len(probes)} probes over {len(documents)} real documents -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
