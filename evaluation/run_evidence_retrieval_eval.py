#!/usr/bin/env python3
"""Run CREST evidence-retrieval regression fixtures.

By default this runs every frozen fixture, not just the newest one. Each
fixture was frozen to pin one failure class; running only the latest lets a
later rule silently undo an earlier guarantee. That happened on 2026-08-20:
sets v2/v3/v4 pinned abstention on absent-answer questions, passed when frozen
at 530 lines of retrieval.py, and were broken by `fa18dbc` without any
sign-off noticing, because each sign-off ran only its own fixture.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from crest_app.retrieval import evaluate_retrieval_fixture  # noqa: E402

FIXTURE_DIR = ROOT / "evaluation"
FIXTURE_GLOB = "evidence_retrieval_set_v*.json"


def _version(path: Path) -> int:
    match = re.search(r"_v(\d+)\.json$", path.name)
    if match is None:
        raise ValueError(f"fixture name carries no version: {path.name}")
    return int(match.group(1))


def all_fixtures() -> list[Path]:
    paths = sorted(FIXTURE_DIR.glob(FIXTURE_GLOB), key=_version)
    if not paths:
        raise FileNotFoundError(f"no fixtures matched {FIXTURE_DIR / FIXTURE_GLOB}")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fixture",
        type=Path,
        action="append",
        help="Run only this fixture. Repeatable. Defaults to every frozen fixture.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Replay cached answerability verdicts only; fail on a cache miss instead of calling a model.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the full per-fixture result objects instead of the summary table.",
    )
    args = parser.parse_args()

    fixtures = args.fixture if args.fixture else all_fixtures()
    results = {
        path.name: evaluate_retrieval_fixture(path, allow_calls=not args.offline)
        for path in fixtures
    }

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for name, result in results.items():
            failed = [c["case_id"] for c in result["cases"] if not c["passed"]]
            status = "PASS" if result["passed"] else f"FAIL ({len(failed)})"
            print(f"{name:<40} {status}")
            for case_id in failed:
                print(f"    failing case: {case_id}")

    regressed = [name for name, result in results.items() if not result["passed"]]
    if regressed:
        print(
            f"\n{len(regressed)} of {len(results)} frozen fixtures failing: "
            + ", ".join(regressed),
            file=sys.stderr,
        )
    return 0 if not regressed else 1


if __name__ == "__main__":
    raise SystemExit(main())
