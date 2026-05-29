#!/usr/bin/env python3
"""Compare read-only retrieval quality between v1 and v2 Chroma indexes."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import textwrap
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pocketsteel.chroma_search import ChromaSearchIndex
from scripts.run_answer_eval import load_question_bank


DEFAULT_V1_CHROMA_PATH = Path("/Users/cory/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma")
DEFAULT_V1_COLLECTION = "steel_guitar_unified"
DEFAULT_V2_CHROMA_PATH = Path("corpus-v2/vector-stores/chroma")
DEFAULT_V2_COLLECTION = "steel_guitar_unified_v2"
DEFAULT_QUESTION_BANK = Path("tests/fixtures/user_question_bank.json")
DEFAULT_OUTPUT = Path("docs/retrieval-ab-eval-report.md")
DEFAULT_JSON_OUTPUT = Path("/tmp/retrieval-ab-eval-results.json")

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.I)
EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", re.I)
TOP_LEAK_PATTERN = re.compile(r"(^|\s)Top(\s|$)", re.I)
SIGNATURE_PATTERN = re.compile(
    r"(?im)(^_{4,}$|^\s*(thanks|regards|sincerely|cheers|best),?\s*$|^\s*sent from my\b|^\s*signature\b)"
)

V1_METADATA_FIELDS = [
    "source_system",
    "forum_name",
    "thread_title",
    "thread_url",
    "chunk_id",
    "source_kind",
    "forum_id",
    "thread_id",
    "legacy_thread_uid",
    "thread_category",
    "chunk_index",
]
V2_METADATA_FIELDS = [
    "source_system",
    "forum_name",
    "thread_title",
    "thread_url",
    "chunk_id",
    "thread_id",
    "chunk_role",
    "quality_score",
    "noise_score",
    "source_metadata_complete",
    "post_uids",
]
METADATA_FIELDS = V1_METADATA_FIELDS
POST_IDENTITY_FIELDS = ["post_uid", "thread_id", "chunk_id"]
QUESTION_START_PATTERN = re.compile(r"^(does|do|did|what|where|how|why|who|which|can|should|is|are)\b", re.I)
USEFUL_SHORT_FRAGMENT_PATTERN = re.compile(
    r"\b(use|raise|lower|pedal|lever|string|fret|check|adjust|tune|because|avoid|compare|recommend|clean|oil|buy|practice)\b",
    re.I,
)


@dataclass(frozen=True)
class SideConfig:
    name: str
    chroma_path: Path
    collection: str


@dataclass(frozen=True)
class RerankConfig:
    candidate_k: int
    min_excerpt_chars: int = 0
    dedupe_thread: bool = False
    question_only_penalty: float = 0.0
    mention_only_penalty: float = 0.0
    answer_advice_boost: float = 0.0
    quality_boost: float = 0.0
    quality_threshold: float = 0.70
    noise_penalty: float = 0.0
    noise_threshold: float = 0.60

    @property
    def enabled(self) -> bool:
        return any(
            [
                self.min_excerpt_chars > 0,
                self.dedupe_thread,
                self.question_only_penalty > 0,
                self.mention_only_penalty > 0,
                self.answer_advice_boost > 0,
                self.quality_boost > 0,
                self.noise_penalty > 0,
            ]
        )


def compact(text: str, width: int = 220) -> str:
    return textwrap.shorten(re.sub(r"\s+", " ", text or "").strip(), width=width, placeholder=" ...")


def numeric_score(value: Any) -> float | None:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if score != score:
        return None
    return score


def score_summary(scores: list[float]) -> dict[str, Any]:
    if not scores:
        return {"count": 0, "min": None, "max": None, "mean": None, "median": None}
    return {
        "count": len(scores),
        "min": round(min(scores), 6),
        "max": round(max(scores), 6),
        "mean": round(statistics.fmean(scores), 6),
        "median": round(statistics.median(scores), 6),
    }


def source_identity(source: dict[str, Any]) -> str:
    for key in ("thread_url", "post_uid", "chunk_id"):
        value = str(source.get(key) or "").strip()
        if value:
            return f"{key}:{value}"
    return ""


def duplicate_source_rate(sources: list[dict[str, Any]]) -> float:
    identities = [identity for source in sources if (identity := source_identity(source))]
    if not identities:
        return 0.0
    return round((len(identities) - len(set(identities))) / len(identities), 6)


def field_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def has_v2_metadata(source: dict[str, Any]) -> bool:
    return any(field_present(source.get(field)) for field in ("chunk_role", "quality_score", "noise_score", "source_metadata_complete", "post_uids"))


def leakage_flags(excerpt: str) -> list[str]:
    flags: list[str] = []
    if TOP_LEAK_PATTERN.search(excerpt):
        flags.append("top")
    if EMAIL_PATTERN.search(excerpt):
        flags.append("email")
    if URL_PATTERN.search(excerpt):
        flags.append("raw_link")
    if SIGNATURE_PATTERN.search(excerpt):
        flags.append("signature")
    return flags


def required_field_rate(source: dict[str, Any], fields: list[str]) -> float:
    if not fields:
        return 1.0
    present = sum(1 for field in fields if field_present(source.get(field)))
    return round(present / len(fields), 6)


def metadata_fields_for_source(source: dict[str, Any]) -> list[str]:
    return V2_METADATA_FIELDS if has_v2_metadata(source) else V1_METADATA_FIELDS


def is_question_only_source(source: dict[str, Any]) -> bool:
    role = str(source.get("chunk_role") or "").strip().lower()
    excerpt = str(source.get("excerpt") or "").strip()
    return role == "question" or excerpt.endswith("?") or bool(QUESTION_START_PATTERN.search(excerpt))


def is_mention_only_fragment(source: dict[str, Any], *, min_chars: int = 80) -> bool:
    excerpt = re.sub(r"\s+", " ", str(source.get("excerpt") or "")).strip()
    if len(excerpt) >= min_chars:
        return False
    if USEFUL_SHORT_FRAGMENT_PATTERN.search(excerpt):
        return False
    words = re.findall(r"[A-Za-z0-9+#'-]+", excerpt)
    return len(words) <= 10


def rerank_score(source: dict[str, Any], config: RerankConfig) -> float:
    score = numeric_score(source.get("score")) or 0.0
    role = str(source.get("chunk_role") or "").strip().lower()
    quality = numeric_score(source.get("quality_score"))
    noise = numeric_score(source.get("noise_score"))

    if role == "answer_advice":
        score += config.answer_advice_boost
    elif role in {"question", "unknown", "event", "memorial"}:
        score -= config.question_only_penalty / 2

    if quality is not None and quality >= config.quality_threshold:
        score += config.quality_boost
    if noise is not None and noise >= config.noise_threshold:
        score -= config.noise_penalty
    if is_question_only_source(source):
        score -= config.question_only_penalty
    if is_mention_only_fragment(source, min_chars=max(config.min_excerpt_chars, 80)):
        score -= config.mention_only_penalty
    return round(score, 6)


def select_with_thread_dedupe(sources: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen_threads: set[str] = set()
    deferred: list[dict[str, Any]] = []
    for source in sources:
        thread_url = str(source.get("thread_url") or "").strip()
        if thread_url and thread_url in seen_threads:
            deferred.append(source)
            continue
        selected.append(source)
        if thread_url:
            seen_threads.add(thread_url)
        if len(selected) >= limit:
            return selected
    for source in deferred:
        selected.append(source)
        if len(selected) >= limit:
            break
    return selected


def rerank_sources(sources: list[dict[str, Any]], *, limit: int, config: RerankConfig) -> list[dict[str, Any]]:
    if not config.enabled:
        return sources[:limit]

    ranked = []
    for index, source in enumerate(sources):
        source = dict(source)
        source["rerank_score"] = rerank_score(source, config)
        source["rerank_flags"] = []
        if config.min_excerpt_chars and len(str(source.get("excerpt") or "").strip()) < config.min_excerpt_chars:
            source["rerank_flags"].append("short_excerpt")
        if is_question_only_source(source):
            source["rerank_flags"].append("question_only")
        if is_mention_only_fragment(source, min_chars=max(config.min_excerpt_chars, 80)):
            source["rerank_flags"].append("mention_only")
        ranked.append((source["rerank_score"], -index, source))

    ordered = [source for _, _, source in sorted(ranked, reverse=True)]
    if config.min_excerpt_chars:
        long_enough = [source for source in ordered if "short_excerpt" not in source["rerank_flags"]]
        short = [source for source in ordered if "short_excerpt" in source["rerank_flags"]]
        ordered = long_enough + short
    if config.dedupe_thread:
        return select_with_thread_dedupe(ordered, limit)
    return ordered[:limit]


def analyze_sources(sources: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [score for source in sources if (score := numeric_score(source.get("score"))) is not None]
    url_count = sum(1 for source in sources if str(source.get("thread_url") or "").strip())
    forums = sorted({str(source.get("forum_name") or "").strip() for source in sources if str(source.get("forum_name") or "").strip()})
    source_systems = sorted(
        {str(source.get("source_system") or "").strip() for source in sources if str(source.get("source_system") or "").strip()}
    )
    leakage_counts: Counter[str] = Counter()
    leaking_source_count = 0
    metadata_rates: list[float] = []
    post_identity_rates: list[float] = []

    for source in sources:
        flags = leakage_flags(str(source.get("excerpt") or ""))
        if flags:
            leaking_source_count += 1
            leakage_counts.update(flags)
        metadata_rates.append(required_field_rate(source, metadata_fields_for_source(source)))
        post_identity_rates.append(required_field_rate(source, POST_IDENTITY_FIELDS))

    source_count = len(sources)
    return {
        "source_count": source_count,
        "source_url_count": url_count,
        "source_url_rate": round(url_count / source_count, 6) if source_count else 0.0,
        "forums": forums,
        "source_systems": source_systems,
        "duplicate_source_rate": duplicate_source_rate(sources),
        "excerpt_leakage_source_count": leaking_source_count,
        "excerpt_leakage_rate": round(leaking_source_count / source_count, 6) if source_count else 0.0,
        "excerpt_leakage_counts": dict(sorted(leakage_counts.items())),
        "metadata_completeness_rate": round(statistics.fmean(metadata_rates), 6) if metadata_rates else 0.0,
        "post_identity_completeness_rate": round(statistics.fmean(post_identity_rates), 6) if post_identity_rates else 0.0,
        "score_distribution": score_summary(scores),
    }


def summarize_side(question_results: list[dict[str, Any]]) -> dict[str, Any]:
    sources = [source for result in question_results for source in result["sources"]]
    summary = analyze_sources(sources)
    summary["question_count"] = len(question_results)
    summary["retrieval_warning_count"] = sum(len(result["warnings"]) for result in question_results)
    summary["zero_source_questions"] = sum(1 for result in question_results if not result["sources"])
    summary["category_counts"] = dict(sorted(Counter(result["category"] for result in question_results).items()))
    return summary


def run_side(config: SideConfig, questions: list[dict[str, str]], top_k: int, rerank_config: RerankConfig) -> dict[str, Any]:
    index = ChromaSearchIndex.from_chroma(chroma_path=config.chroma_path, collection_name=config.collection)
    results: list[dict[str, Any]] = []
    candidate_k = max(top_k, rerank_config.candidate_k)
    for row in questions:
        response = index.search(row["question"], limit=candidate_k)
        candidate_sources = list(response.results)
        sources = rerank_sources(candidate_sources, limit=top_k, config=rerank_config)
        results.append(
            {
                "id": row["id"],
                "category": row["category"],
                "question": row["question"],
                "expected_intent": row.get("expected_intent", ""),
                "expected_contract": row.get("expected_contract", ""),
                "sources": sources,
                "candidate_source_count": len(candidate_sources),
                "warnings": response.warnings,
                "metrics": analyze_sources(sources),
            }
        )
    return {
        "name": config.name,
        "chroma_path": str(config.chroma_path),
        "collection": config.collection,
        "summary": summarize_side(results),
        "results": results,
    }


def load_answer_eval(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain the JSON list written by scripts/run_answer_eval.py")
    by_id: dict[str, dict[str, Any]] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        question_id = str(item.get("id") or "").strip()
        if not question_id:
            continue
        group = str(item.get("group") or "")
        by_id[question_id] = {
            "group": group,
            "passed": group == "pass",
            "failure_count": len(item.get("failures") or []),
            "source_count": item.get("source_count"),
        }
    return by_id


def attach_answer_eval(report: dict[str, Any], side_name: str, answer_eval: dict[str, dict[str, Any]]) -> None:
    if not answer_eval or side_name not in report["sides"]:
        return
    passed = 0
    failed = 0
    for result in report["sides"][side_name]["results"]:
        answer_result = answer_eval.get(result["id"])
        result["answer_eval"] = answer_result
        if not answer_result:
            continue
        if answer_result["passed"]:
            passed += 1
        else:
            failed += 1
    report["sides"][side_name]["summary"]["answer_eval"] = {
        "provided": True,
        "pass_count": passed,
        "fail_count": failed,
    }


def pair_results(report: dict[str, Any], questions: list[dict[str, str]]) -> list[dict[str, Any]]:
    v1_results = {row["id"]: row for row in report["sides"].get("v1", {}).get("results", [])}
    v2_results = {row["id"]: row for row in report["sides"].get("v2", {}).get("results", [])}
    pairs: list[dict[str, Any]] = []
    for row in questions:
        v1 = v1_results.get(row["id"])
        v2 = v2_results.get(row["id"])
        pairs.append(
            {
                "id": row["id"],
                "category": row["category"],
                "question": row["question"],
                "v1": v1["metrics"] if v1 else None,
                "v2": v2["metrics"] if v2 else None,
                "answer_eval": {
                    "v1": v1.get("answer_eval") if v1 else None,
                    "v2": v2.get("answer_eval") if v2 else None,
                },
            }
        )
    return pairs


def render_summary_block(summary: dict[str, Any]) -> list[str]:
    scores = summary["score_distribution"]
    lines = [
        f"- Questions: {summary['question_count']}",
        f"- Sources: {summary['source_count']}",
        f"- Zero-source questions: {summary['zero_source_questions']}",
        f"- Source URL rate: {summary['source_url_rate']:.2%}",
        f"- Duplicate source rate: {summary['duplicate_source_rate']:.2%}",
        f"- Excerpt leakage rate: {summary['excerpt_leakage_rate']:.2%}",
        f"- Metadata completeness: {summary['metadata_completeness_rate']:.2%}",
        f"- Post identity completeness: {summary['post_identity_completeness_rate']:.2%}",
        f"- Score count/min/median/max: {scores['count']} / {scores['min']} / {scores['median']} / {scores['max']}",
    ]
    if summary.get("answer_eval", {}).get("provided"):
        answer_eval = summary["answer_eval"]
        lines.append(f"- Answer eval pass/fail: {answer_eval['pass_count']} / {answer_eval['fail_count']}")
    if summary["forums"]:
        lines.append(f"- Forum coverage: {', '.join(summary['forums'])}")
    if summary["source_systems"]:
        lines.append(f"- Source-system coverage: {', '.join(summary['source_systems'])}")
    if summary["excerpt_leakage_counts"]:
        leakage = ", ".join(f"{key}: {value}" for key, value in summary["excerpt_leakage_counts"].items())
        lines.append(f"- Leakage counts: {leakage}")
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Retrieval A/B Eval Report",
        "",
        f"Generated: {report['generated_at']}",
        f"Question bank: `{report['question_bank']}`",
        f"Top K: {report['top_k']}",
        f"Candidate K: {report['rerank_config']['candidate_k']}",
        "",
        "## Safety Notes",
        "",
        "- This harness reads existing Chroma collections only when a side is explicitly enabled.",
        "- It does not scrape, rebuild embeddings, reset Chroma, switch app config, or call answer generation.",
        "- v2 retrieval requires both `--run-v2` and `--confirm-v2-ready`.",
        f"- Rerank enabled: `{report['rerank_config']['enabled']}`.",
        "",
        "## Side Summaries",
        "",
    ]
    for side_name in ("v1", "v2"):
        side = report["sides"].get(side_name)
        if not side:
            lines.extend([f"### {side_name}", "", "Not run.", ""])
            continue
        lines.extend(
            [
                f"### {side_name}",
                "",
                f"- Chroma path: `{side['chroma_path']}`",
                f"- Collection: `{side['collection']}`",
            ]
        )
        lines.extend(render_summary_block(side["summary"]))
        lines.append("")

    lines.extend(["## Paired Question Metrics", ""])
    if not report["paired_results"]:
        lines.append("No paired rows were generated.")
    else:
        lines.append("| ID | Category | v1 sources | v2 sources | v1 leaks | v2 leaks | v1 answer | v2 answer |")
        lines.append("| --- | --- | ---: | ---: | ---: | ---: | --- | --- |")
        for pair in report["paired_results"]:
            v1 = pair["v1"] or {}
            v2 = pair["v2"] or {}
            answer = pair.get("answer_eval") or {}
            v1_answer = answer.get("v1", {}).get("group") if answer.get("v1") else ""
            v2_answer = answer.get("v2", {}).get("group") if answer.get("v2") else ""
            lines.append(
                "| {id} | {category} | {v1_sources} | {v2_sources} | {v1_leaks} | {v2_leaks} | {v1_answer} | {v2_answer} |".format(
                    id=pair["id"],
                    category=pair["category"],
                    v1_sources=v1.get("source_count", ""),
                    v2_sources=v2.get("source_count", ""),
                    v1_leaks=v1.get("excerpt_leakage_source_count", ""),
                    v2_leaks=v2.get("excerpt_leakage_source_count", ""),
                    v1_answer=v1_answer,
                    v2_answer=v2_answer,
                )
            )

    lines.extend(["", "## Review Samples", ""])
    for side_name in ("v1", "v2"):
        side = report["sides"].get(side_name)
        if not side:
            continue
        lines.extend([f"### {side_name}", ""])
        for result in side["results"][:10]:
            first_source = result["sources"][0] if result["sources"] else {}
            lines.extend(
                [
                    f"- `{result['id']}` {result['question']}",
                    f"  - Sources: {len(result['sources'])}; warnings: {len(result['warnings'])}",
                    f"  - First source: {first_source.get('forum_name', '')} / {first_source.get('thread_title', '')} / {first_source.get('thread_url', '')}",
                    f"  - Excerpt: {compact(str(first_source.get('excerpt') or ''))}",
                ]
            )
    lines.append("")
    return "\n".join(lines)


def build_report(args: argparse.Namespace, questions: list[dict[str, str]]) -> dict[str, Any]:
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
    report: dict[str, Any] = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "question_bank": str(args.question_bank),
        "top_k": args.top_k,
        "rerank_config": {**asdict(rerank_config), "enabled": rerank_config.enabled},
        "sides": {},
        "paired_results": [],
    }
    if args.run_v1:
        report["sides"]["v1"] = run_side(SideConfig("v1", args.v1_chroma_path, args.v1_collection), questions, args.top_k, rerank_config)
    if args.run_v2:
        report["sides"]["v2"] = run_side(SideConfig("v2", args.v2_chroma_path, args.v2_collection), questions, args.top_k, rerank_config)

    attach_answer_eval(report, "v1", load_answer_eval(args.v1_answer_eval_json))
    attach_answer_eval(report, "v2", load_answer_eval(args.v2_answer_eval_json))
    report["paired_results"] = pair_results(report, questions)
    return report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1-chroma-path", type=Path, default=DEFAULT_V1_CHROMA_PATH)
    parser.add_argument("--v1-collection", default=DEFAULT_V1_COLLECTION)
    parser.add_argument("--v2-chroma-path", type=Path, default=DEFAULT_V2_CHROMA_PATH)
    parser.add_argument("--v2-collection", default=DEFAULT_V2_COLLECTION)
    parser.add_argument("--question-bank", type=Path, default=DEFAULT_QUESTION_BANK)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--candidate-k", type=int, default=5, help="Read-only candidate count to retrieve before optional rerank/dedupe.")
    parser.add_argument("--min-excerpt-chars", type=int, default=0, help="Prefer sources with at least this many excerpt characters.")
    parser.add_argument("--dedupe-thread", action="store_true", help="Prefer one source per thread URL after reranking.")
    parser.add_argument("--question-only-penalty", type=float, default=0.0)
    parser.add_argument("--mention-only-penalty", type=float, default=0.0)
    parser.add_argument("--answer-advice-boost", type=float, default=0.0)
    parser.add_argument("--quality-boost", type=float, default=0.0)
    parser.add_argument("--quality-threshold", type=float, default=0.70)
    parser.add_argument("--noise-penalty", type=float, default=0.0)
    parser.add_argument("--noise-threshold", type=float, default=0.60)
    parser.add_argument("--limit", type=int, default=None, help="Optional question limit for smoke runs.")
    parser.add_argument("--run-v1", action="store_true", help="Run read-only retrieval against the v1 Chroma collection.")
    parser.add_argument("--run-v2", action="store_true", help="Run read-only retrieval against the v2 Chroma collection.")
    parser.add_argument(
        "--confirm-v2-ready",
        action="store_true",
        help="Required with --run-v2 so v2 is not opened while embeddings are still running.",
    )
    parser.add_argument("--v1-answer-eval-json", type=Path, default=None)
    parser.add_argument("--v2-answer-eval-json", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and print the planned run without opening Chroma.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.top_k <= 0:
        parser.error("--top-k must be greater than zero")
    if args.candidate_k <= 0:
        parser.error("--candidate-k must be greater than zero")
    if args.min_excerpt_chars < 0:
        parser.error("--min-excerpt-chars must be zero or greater")
    if args.run_v2 and not args.confirm_v2_ready:
        parser.error("--run-v2 requires --confirm-v2-ready after v2 embedding completes")

    questions = load_question_bank(args.question_bank)
    if args.limit is not None:
        questions = questions[: max(0, args.limit)]

    if args.dry_run:
        sides = []
        if args.run_v1:
            sides.append("v1")
        if args.run_v2:
            sides.append("v2")
        print("Retrieval A/B eval dry run")
        print(f"Question bank: {args.question_bank}")
        print(f"Questions: {len(questions)}")
        print(f"Top K: {args.top_k}")
        print(f"Requested sides: {', '.join(sides) if sides else 'none'}")
        print(f"Markdown output: {args.output}")
        print(f"JSON output: {args.json_output}")
        print("Dry run did not open Chroma.")
        return 0

    if not args.run_v1 and not args.run_v2:
        parser.error("choose at least one retrieval side with --run-v1 and/or --run-v2, or use --dry-run")

    report = build_report(args, questions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(report), encoding="utf-8")
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Evaluated {len(questions)} questions")
    print(f"Sides: {', '.join(report['sides'])}")
    print(f"Markdown report: {args.output}")
    print(f"JSON report: {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
