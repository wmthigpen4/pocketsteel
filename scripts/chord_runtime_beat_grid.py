#!/usr/bin/env python3
"""Generate one sealed development-only runtime beat-grid receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from steel_guitar_rag.chord_reader.runtime_beat_grid import (
    DEFAULT_RUNNER_TIMEOUT_SECONDS,
    INPUT_MANIFEST_SCHEMA,
    MAX_RUNNER_TIMEOUT_SECONDS,
    generate_runtime_beat_grid_receipt,
)


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a sealed reference-free beat receipt by reconciling a new "
            "integer target-browser rhythm run to an attested runtime bar-grid v2 parent."
        )
    )
    parser.add_argument(
        "--manifest",
        action="append",
        type=Path,
        required=True,
        help=f"Explicit {INPUT_MANIFEST_SCHEMA} development audio manifest; may be repeated.",
    )
    parser.add_argument("--parent-runtime-manifest", type=Path, required=True)
    parser.add_argument("--parent-runtime-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New .json receipt path.")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_RUNNER_TIMEOUT_SECONDS,
        help=f"Per-track target-browser timeout (maximum {MAX_RUNNER_TIMEOUT_SECONDS:g}).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    receipt = generate_runtime_beat_grid_receipt(
        args.manifest,
        args.parent_runtime_manifest,
        args.parent_runtime_root,
        args.output,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(receipt, ensure_ascii=False, allow_nan=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
