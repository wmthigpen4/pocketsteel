#!/usr/bin/env python3
"""Run local-only answer eval against v2 Chroma with reranked retrieval."""

from __future__ import annotations

import argparse
import json
import sys
import threading
from collections import Counter
from pathlib import Path
from typing import Any
from wsgiref.simple_server import WSGIServer, make_server

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from steel_guitar_rag.api import create_app
from steel_guitar_rag.access_control import DEV_ACCESS_ROLE_ENVIRON
from steel_guitar_rag.answer_usage import InMemoryAnswerRateLimiter
from steel_guitar_rag.chroma_search import ChromaSearchIndex, SearchResponse
from scripts.run_answer_eval import DEFAULT_QUESTION_BANK, REPORT_GROUPS, render_report, result_to_json, run_eval
from scripts.run_retrieval_ab_eval import RerankConfig, rerank_sources


DEFAULT_V2_CHROMA_PATH = Path("corpus-v2/vector-stores/chroma")
DEFAULT_V2_COLLECTION = "steel_guitar_unified_v2"
DEFAULT_OUTPUT = Path("corpus-v2/reports/answer-eval-v2-rerank.md")
DEFAULT_JSON_OUTPUT = Path("corpus-v2/reports/answer-eval-v2-rerank.json")
DEFAULT_V1_BASELINE_JSON = Path("/tmp/answer-eval-results.json")


class RerankedSearchIndex:
    def __init__(self, base: ChromaSearchIndex, config: RerankConfig) -> None:
        self.base = base
        self.config = config

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        source_system: str | None = None,
        forum_name: str | None = None,
    ) -> SearchResponse:
        candidate_limit = max(limit, self.config.candidate_k)
        response = self.base.search(
            query,
            limit=candidate_limit,
            source_system=source_system,
            forum_name=forum_name,
        )
        return SearchResponse(
            results=rerank_sources(response.results, limit=limit, config=self.config),
            warnings=response.warnings,
        )


def local_eval_auth_app(app: Any) -> Any:
    def wrapped(environ: dict[str, Any], start_response: Any) -> Any:
        environ.setdefault(DEV_ACCESS_ROLE_ENVIRON, "beta_user")
        return app(environ, start_response)

    return wrapped


def load_baseline(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list of answer eval rows.")
    return [row for row in data if isinstance(row, dict)]


def failure_counter(rows: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        for failure in row.get("failures") or []:
            if isinstance(failure, dict):
                counts[str(failure.get("reason") or "")] += 1
    return counts


def group_counter(rows: list[dict[str, Any]]) -> Counter[str]:
    return Counter(str(row.get("group") or "") for row in rows)


def source_count(rows: list[dict[str, Any]]) -> int:
    return sum(int(row.get("source_count") or 0) for row in rows)


def no_source_count(rows: list[dict[str, Any]]) -> int:
    return sum(1 for row in rows if int(row.get("source_count") or 0) == 0)


def top_failures(rows: list[dict[str, Any]], *, limit: int = 20) -> list[dict[str, Any]]:
    failures = [row for row in rows if row.get("group") != "pass"]
    group_rank = {group: index for index, group in enumerate(REPORT_GROUPS)}
    return sorted(
        failures,
        key=lambda row: (
            group_rank.get(str(row.get("group") or ""), 99),
            -len(row.get("failures") or []),
            str(row.get("id") or ""),
        ),
    )[:limit]


def rows_for_category(rows: list[dict[str, Any]], category: str, *, limit: int = 5) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("category") == category][:limit]


def comparison_markdown(v2_rows: list[dict[str, Any]], v1_rows: list[dict[str, Any]], *, baseline_path: Path | None) -> str:
    lines = ["", "## V1 Baseline Comparison", ""]
    if not v1_rows:
        lines.append(f"No v1 baseline JSON was found at `{baseline_path}`.")
        return "\n".join(lines)

    v1_groups = group_counter(v1_rows)
    v2_groups = group_counter(v2_rows)
    lines.extend(
        [
            f"Baseline JSON: `{baseline_path}`",
            "",
            "| Group | v1 | v2 rerank |",
            "| --- | ---: | ---: |",
        ]
    )
    for group in REPORT_GROUPS:
        lines.append(f"| {group} | {v1_groups[group]} | {v2_groups[group]} |")
    lines.extend(
        [
            "",
            "| Metric | v1 | v2 rerank |",
            "| --- | ---: | ---: |",
            f"| Total rows | {len(v1_rows)} | {len(v2_rows)} |",
            f"| Total source cards | {source_count(v1_rows)} | {source_count(v2_rows)} |",
            f"| No-source rows | {no_source_count(v1_rows)} | {no_source_count(v2_rows)} |",
            "",
            "## Failure Reason Comparison",
            "",
            "| Reason | v1 | v2 rerank |",
            "| --- | ---: | ---: |",
        ]
    )
    v1_failures = failure_counter(v1_rows)
    v2_failures = failure_counter(v2_rows)
    for reason, _ in (v1_failures + v2_failures).most_common(30):
        if reason:
            lines.append(f"| {reason} | {v1_failures[reason]} | {v2_failures[reason]} |")

    lines.extend(["", "## Worst 20 V2 Failures", ""])
    for row in top_failures(v2_rows):
        reasons = "; ".join(str(failure.get("reason") or "") for failure in row.get("failures") or [])
        lines.append(f"- `{row.get('id')}` {row.get('question')} ({row.get('group')}; sources: {row.get('source_count')}; reasons: {reasons})")

    sample_categories = [
        ("Player Bio Samples", "entity_player_biography"),
        ("Copedent/Fretboard Samples", "e9_fretboard_copedent"),
        ("Gear/Tone Samples", "gear_effects_tone"),
        ("Maintenance/Troubleshooting Samples", "maintenance_parts_safety"),
    ]
    for title, category in sample_categories:
        lines.extend(["", f"## {title}", ""])
        for row in rows_for_category(v2_rows, category):
            reasons = "; ".join(str(failure.get("reason") or "") for failure in row.get("failures") or []) or "pass"
            lines.append(
                f"- `{row.get('id')}` {row.get('question')} "
                f"(group: {row.get('group')}, sources: {row.get('source_count')}, first source: {row.get('first_source_forum')} / {row.get('first_source_title')}, reasons: {reasons})"
            )
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0, help="Local loopback port. 0 chooses a free ephemeral port.")
    parser.add_argument("--v2-chroma-path", type=Path, default=DEFAULT_V2_CHROMA_PATH)
    parser.add_argument("--v2-collection", default=DEFAULT_V2_COLLECTION)
    parser.add_argument("--question-bank", type=Path, default=DEFAULT_QUESTION_BANK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--v1-baseline-json", type=Path, default=DEFAULT_V1_BASELINE_JSON)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--candidate-k", type=int, default=20)
    parser.add_argument("--min-excerpt-chars", type=int, default=80)
    parser.add_argument("--dedupe-thread", action="store_true", default=True)
    parser.add_argument("--question-only-penalty", type=float, default=0.12)
    parser.add_argument("--mention-only-penalty", type=float, default=0.20)
    parser.add_argument("--answer-advice-boost", type=float, default=0.04)
    parser.add_argument("--quality-boost", type=float, default=0.04)
    parser.add_argument("--quality-threshold", type=float, default=0.70)
    parser.add_argument("--noise-penalty", type=float, default=0.06)
    parser.add_argument("--noise-threshold", type=float, default=0.60)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.candidate_k <= 0:
        raise SystemExit("--candidate-k must be greater than zero")
    if args.min_excerpt_chars < 0:
        raise SystemExit("--min-excerpt-chars must be zero or greater")

    rerank_config = RerankConfig(
        candidate_k=args.candidate_k,
        min_excerpt_chars=args.min_excerpt_chars,
        dedupe_thread=args.dedupe_thread,
        question_only_penalty=args.question_only_penalty,
        mention_only_penalty=args.mention_only_penalty,
        answer_advice_boost=args.answer_advice_boost,
        quality_boost=args.quality_boost,
        quality_threshold=args.quality_threshold,
        noise_penalty=args.noise_penalty,
        noise_threshold=args.noise_threshold,
    )
    search_index = RerankedSearchIndex(
        ChromaSearchIndex.from_chroma(
            chroma_path=args.v2_chroma_path,
            collection_name=args.v2_collection,
        ),
        rerank_config,
    )
    app = local_eval_auth_app(
        create_app(
            search_index,
            answer_auth_mode="local_dev",
            auth_provider="scaffold",
            answer_rate_limiter=InMemoryAnswerRateLimiter(enabled=False),
        )
    )
    server: WSGIServer = make_server(args.host, args.port, app)
    host, port = server.server_address[:2]
    base_url = f"http://{host}:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        from scripts.run_answer_eval import load_question_bank

        questions = load_question_bank(args.question_bank)
        if args.limit is not None:
            questions = questions[: max(0, args.limit)]
        results = run_eval(base_url, questions)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    result_rows = [result_to_json(result) for result in results]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = render_report(results, base_url=base_url, question_bank=args.question_bank)
    report += comparison_markdown(result_rows, load_baseline(args.v1_baseline_json), baseline_path=args.v1_baseline_json)
    args.output.write_text(report, encoding="utf-8")
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result_rows, indent=2), encoding="utf-8")

    group_counts = Counter(result.group for result in results)
    print(f"Evaluated {len(results)} questions against local-only v2 reranked retrieval at {base_url}")
    for group in REPORT_GROUPS:
        print(f"{group}: {group_counts[group]}")
    print(f"Markdown report: {args.output}")
    print(f"JSON results: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
