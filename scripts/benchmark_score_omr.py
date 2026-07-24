#!/usr/bin/env python3
"""Score a founder-reviewed printed-score OMR manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from steel_guitar_rag.score_omr_benchmark import benchmark_score_omr


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Private JSON manifest containing reference and candidate drafts.")
    parser.add_argument("--output", type=Path, help="Optional metrics JSON destination.")
    args = parser.parse_args()
    payload: Any = json.loads(args.manifest.read_text(encoding="utf-8"))
    cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(cases, list):
        parser.error("Manifest must be a list or an object with a cases list.")
    result = benchmark_score_omr(cases)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
