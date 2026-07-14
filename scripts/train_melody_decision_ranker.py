#!/usr/bin/env python3
"""Train the private reviewed-decision ranker without exposing source text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pocketsteel.melody_ranker import train_pairwise_ranker


DEFAULT_INPUT = Path("corpus-private/melody-decisions/reviewed-decisions.jsonl")
DEFAULT_OUTPUT = Path("corpus-private/melody-decisions/models/melody-decision-ranker-v1.json")


def load_records(path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"Line {line_number} is not a decision record.")
        records.append(value)
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--epochs", type=int, default=20)
    args = parser.parse_args()
    model = train_pairwise_ranker(load_records(args.input), epochs=args.epochs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(model.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {model.example_count} reviewed decisions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
