#!/usr/bin/env python3
"""Apply a bounded, independently measured beat-grid offset to a pilot track."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--track-id", required=True)
    parser.add_argument("--offset-seconds", type=float, required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    if not -2 <= args.offset_seconds <= 2:
        raise SystemExit("offset must be between -2 and 2 seconds")

    proof = json.loads(args.proof.read_text(encoding="utf-8"))
    matches = [item for item in proof["tracks"] if item["track"]["id"] == args.track_id]
    if len(matches) != 1:
        raise SystemExit(f"expected one track named {args.track_id!r}")
    rhythm = matches[0]["track"].setdefault("rhythm", {})
    rhythm["gridOffsetSeconds"] = round(args.offset_seconds, 3)
    rhythm["gridOffsetSource"] = args.source

    temporary = args.proof.with_suffix(f"{args.proof.suffix}.tmp")
    temporary.write_text(f"{json.dumps(proof, indent=2)}\n", encoding="utf-8")
    temporary.replace(args.proof)


if __name__ == "__main__":
    main()
