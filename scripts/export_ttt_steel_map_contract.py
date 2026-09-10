#!/usr/bin/env python3
"""Generate or verify the versioned deterministic contract consumed by TTT."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from steel_guitar_rag.ttt_steel_map_contract import THEORY_SOURCE_REVISION, build_ttt_steel_map_contract, canonical_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("contracts/steel-map-e9-contract-v1.json"))
    parser.add_argument("--source-revision", default=THEORY_SOURCE_REVISION)
    parser.add_argument("--check", action="store_true", help="fail instead of updating a stale snapshot")
    args = parser.parse_args()
    payload = build_ttt_steel_map_contract(args.source_revision)
    rendered = canonical_json(payload) + "\n"
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"{args.output} is stale; rerun this script without --check.")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
