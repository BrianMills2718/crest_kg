#!/usr/bin/env python3
"""Measure recall and abstention on the real CREST corpus.

Each probe question was generated from one exact passage, so the document that
passage came from is by construction the one that answers it. Two runs per
probe:

* **recall** -- the whole corpus. The source document must be returned.
* **abstention** -- the corpus with the source document removed. No other
  document states that fact, so the correct result is to return nothing.

Ranking is also scored without the answerability gate, so a miss can be
attributed to the ranker or to the gate rather than to "retrieval".
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from crest_app.retrieval import (  # noqa: E402
    RetrievalDocument,
    rank_evidence,
    select_evidence,
)
from evaluation.build_real_corpus_probe import load_documents  # noqa: E402

PROBE = ROOT / "evaluation" / "real_corpus_probe.json"

# A question that points at its own source ("according to this passage") has no
# stable answer once that source is removed, so it cannot score abstention.
DEGENERATE = ("this passage", "the passage", "the document", "the text", "according to the")


def is_degenerate(question: str) -> bool:
    lowered = question.casefold()
    return any(marker in lowered for marker in DEGENERATE)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=4, help="Evidence limit per query.")
    parser.add_argument("--offline", action="store_true", help="Replay cached verdicts only.")
    args = parser.parse_args()

    payload = json.loads(PROBE.read_text(encoding="utf-8"))
    documents = load_documents()
    everything = [
        RetrievalDocument(
            document_id=identity,
            connector_id="bundled-crest",
            title=item.get("title", ""),
            body_text=item["body_text"],
        )
        for identity, item in sorted(documents.items())
    ]

    rows: list[dict] = []
    for probe in payload["probes"]:
        if is_degenerate(probe["question"]):
            rows.append({**probe, "skipped": "degenerate-self-referential-question"})
            continue
        question, source = probe["question"], probe["source_identity"]
        without_source = [d for d in everything if d.document_id != source]

        ranked = rank_evidence(question, everything, limit=args.limit)
        rank_hit = source in {item.document_id for item in ranked}

        kept = select_evidence(
            question, everything, limit=args.limit, allow_calls=not args.offline,
            trace_id=f"crest_kg.real_probe/{probe['probe_id']}/recall",
        )
        recall_hit = source in {item.document_id for item in kept}

        held_out = select_evidence(
            question, without_source, limit=args.limit, allow_calls=not args.offline,
            trace_id=f"crest_kg.real_probe/{probe['probe_id']}/abstain",
        )
        abstained = not held_out

        rows.append(
            {
                "probe_id": probe["probe_id"],
                "question": question,
                "rank_hit": rank_hit,
                "recall_hit": recall_hit,
                "abstained_when_source_removed": abstained,
                "leaked_documents": [item.document_id for item in held_out],
            }
        )
        print(
            f"  {probe['probe_id']}  rank={'HIT ' if rank_hit else 'miss'}"
            f"  gate={'HIT ' if recall_hit else 'miss'}"
            f"  abstain={'OK  ' if abstained else 'LEAK'}  {question[:60]}"
        )

    scored = [r for r in rows if "skipped" not in r]
    skipped = [r for r in rows if "skipped" in r]
    n = len(scored)
    summary = {
        "scored_probes": n,
        "skipped_degenerate": len(skipped),
        "rank_recall": sum(r["rank_hit"] for r in scored) / n if n else 0.0,
        "recall_after_gate": sum(r["recall_hit"] for r in scored) / n if n else 0.0,
        "abstention_when_answer_absent": (
            sum(r["abstained_when_source_removed"] for r in scored) / n if n else 0.0
        ),
    }
    out = ROOT / "evaluation" / "real_corpus_probe_result.json"
    out.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2) + "\n", encoding="utf-8")

    print(f"\nscored {n} probes ({len(skipped)} skipped as self-referential)")
    print(f"  ranking recall @{args.limit}          {summary['rank_recall']:.1%}")
    print(f"  recall after answerability gate  {summary['recall_after_gate']:.1%}")
    print(f"  abstention when answer absent    {summary['abstention_when_answer_absent']:.1%}")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
