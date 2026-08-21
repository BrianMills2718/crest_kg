#!/usr/bin/env python3
"""Run the frozen CREST evidence-retrieval regression fixture."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from crest_app.retrieval import evaluate_retrieval_fixture  # noqa: E402


def main() -> int:
    result = evaluate_retrieval_fixture(
        ROOT / "evaluation" / "evidence_retrieval_set_v1.json"
    )
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
