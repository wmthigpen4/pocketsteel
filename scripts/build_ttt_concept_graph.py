#!/usr/bin/env python3
"""Compile the private, deterministic TTT timestamped concept graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from steel_guitar_rag.ttt_concept_graph import (
    TttConceptGraphError,
    canonical_json_bytes,
    compile_concept_graph,
    graph_report,
)


PACKAGE = ROOT / "partner_companions" / "travis_practice_guide"
DEFAULT_TRANSCRIPTS = Path.home() / "Documents" / "vtt-test" / "Sections"
DEFAULT_TAXONOMY = PACKAGE / "content" / "concept-taxonomy.json"
DEFAULT_CATALOG = PACKAGE / "content" / "lesson-catalog.json"
DEFAULT_OUTPUT = ROOT / "corpus-private" / "ttt-concept-graph" / "graph.json"
DEFAULT_REPORT = ROOT / "corpus-private" / "ttt-concept-graph" / "report.json"
DEFAULT_REVIEW_QUEUE = ROOT / "corpus-private" / "ttt-concept-graph" / "review-queue.json"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TttConceptGraphError(f"Expected an object in {path}")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcripts", type=Path, default=DEFAULT_TRANSCRIPTS)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--review-queue", type=Path, default=DEFAULT_REVIEW_QUEUE)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    graph = compile_concept_graph(
        args.transcripts,
        _load(args.taxonomy),
        _load(args.catalog),
        limit=args.limit,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.review_queue.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(graph))
    args.report.write_bytes(canonical_json_bytes(graph_report(graph)))
    args.review_queue.write_bytes(
        canonical_json_bytes(
            {
                "schemaVersion": "ttt_concept_review_queue_v1",
                "graphSha256": graph["graphSha256"],
                "autoPublishAllowed": False,
                "items": graph["reviewQueue"],
            }
        )
    )
    print(json.dumps(graph_report(graph), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
