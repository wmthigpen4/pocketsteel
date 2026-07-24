#!/usr/bin/env python3
"""Run lightweight Electronics-only RAG evaluations for Steel Guitar RAG."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from rag_answer import answer_question  # noqa: E402
from rag_common import DEFAULT_CHAT_MODEL, DEFAULT_EMBEDDING_MODEL, excerpt  # noqa: E402


DEFAULT_QUESTIONS = PROJECT_ROOT / "eval" / "electronics_gold_questions.jsonl"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "eval" / "results"
MANUAL_SCORE_FIELDS = {
    "retrieval_relevance": None,
    "answer_accuracy": None,
    "electronics_specificity": None,
    "source_grounding": None,
    "practical_usefulness": None,
    "hallucination_risk": None,
    "failure_type": None,
    "reviewer_notes": "",
}
FAILURE_TYPES = (
    "bad_retrieval",
    "weak_chunking",
    "missing_metadata",
    "generic_answer",
    "unsupported_claim",
    "wrong_electronics_logic",
    "citation_problem",
    "good_answer",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            value = json.loads(stripped)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            rows.append(value)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def unique_source_links(rows: list[dict[str, Any]]) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for row in rows:
        metadata = row.get("metadata") or {}
        url = metadata.get("source_url") or metadata.get("thread_url") or ""
        if url and url not in seen:
            links.append(url)
            seen.add(url)
    return links


def serialize_retrieved_chunks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for rank, row in enumerate(rows, 1):
        metadata = row.get("metadata") or {}
        text = row.get("text") or ""
        chunks.append(
            {
                "rank": rank,
                "chunk_id": metadata.get("chunk_id"),
                "distance": row.get("distance"),
                "thread_title": metadata.get("thread_title"),
                "source_url": metadata.get("source_url") or metadata.get("thread_url"),
                "username": metadata.get("username"),
                "post_date": metadata.get("post_date") or metadata.get("post_date_raw"),
                "excerpt": excerpt(text, width=500),
                "text": text,
                "metadata": metadata,
            }
        )
    return chunks


def dated_output_dir(output_root: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return output_root / f"electronics-{stamp}"


def run_eval(args: argparse.Namespace) -> int:
    questions = read_jsonl(Path(args.questions))
    if args.limit is not None:
        questions = questions[: args.limit]

    output_dir = dated_output_dir(Path(args.output_root))
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "results.jsonl"
    summary_path = output_dir / "summary.json"

    embedding_model = args.embedding_model or os.environ.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    chat_model = args.chat_model or os.environ.get("CHAT_MODEL", DEFAULT_CHAT_MODEL)
    run_started_at = datetime.now(timezone.utc).isoformat()
    settings = {
        "corpus": "Steel Guitar Forum - Electronics forum only",
        "questions_path": str(Path(args.questions)),
        "top_k": args.top_k,
        "chroma": args.chroma,
        "collection": args.collection,
        "embedding_model": embedding_model,
        "chat_model": chat_model,
        "forum_name": args.forum_name,
    }

    failures = 0
    with results_path.open("w", encoding="utf-8") as handle:
        for index, item in enumerate(questions, 1):
            question = item["question"]
            print(f"[{index}/{len(questions)}] {question}", flush=True)
            timestamp = datetime.now(timezone.utc).isoformat()
            error = None
            answer = ""
            retrieved_rows: list[dict[str, Any]] = []
            weak_retrieval = None
            try:
                answer, retrieved_rows, weak_retrieval = answer_question(
                    question,
                    top_k=args.top_k,
                    chroma_path=args.chroma,
                    collection_name=args.collection,
                    model=embedding_model,
                    chat_model=chat_model,
                    forum_name=args.forum_name,
                )
            except Exception as exc:  # Preserve the failed eval row for review.
                failures += 1
                error = f"{type(exc).__name__}: {exc}"

            result = {
                "id": item.get("id"),
                "question": question,
                "topic": item.get("topic"),
                "scope": item.get("scope"),
                "expected_evidence": item.get("expected_evidence", []),
                "generated_answer": answer,
                "weak_retrieval": weak_retrieval,
                "retrieved_chunks": serialize_retrieved_chunks(retrieved_rows),
                "source_thread_links": unique_source_links(retrieved_rows),
                "timestamp": timestamp,
                "model_settings": settings,
                "error": error,
                "manual_scores": dict(MANUAL_SCORE_FIELDS),
                "allowed_failure_types": list(FAILURE_TYPES),
            }
            handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")

    summary = {
        "run_started_at": run_started_at,
        "run_finished_at": datetime.now(timezone.utc).isoformat(),
        "question_count": len(questions),
        "failure_count": failures,
        "results_path": str(results_path),
        "settings": settings,
        "manual_score_fields": MANUAL_SCORE_FIELDS,
        "allowed_failure_types": list(FAILURE_TYPES),
    }
    write_json(summary_path, summary)
    print(f"\nWrote results to {results_path}")
    print(f"Wrote summary to {summary_path}")
    if failures:
        print(f"Completed with {failures} question-level errors preserved in results.")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", default=str(DEFAULT_QUESTIONS), help="Electronics eval questions JSONL.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Directory for dated eval runs.")
    parser.add_argument("--top-k", type=int, default=6)
    parser.add_argument("--chroma", default="rag-data/electronics/chroma")
    parser.add_argument("--collection", default="electronics")
    parser.add_argument("--embedding-model", default=None)
    parser.add_argument("--chat-model", default=None)
    parser.add_argument("--forum-name", default="Electronics")
    parser.add_argument("--limit", type=int, default=None, help="Optional question limit for smoke tests.")
    return parser


def main() -> int:
    return run_eval(build_arg_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())

