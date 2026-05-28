#!/usr/bin/env python3
"""Build sample-safe corpus-v2 retrieval chunks from Phase 3B records."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.phase3_clean_classify_chunks import as_list, compact_space, word_count


ANSWER_ROLE = "answer_advice"
QUESTION_ROLE = "question"
EXCLUDED_ANSWER_ROLES = {"contact_block", "gear_signature", "link_only", "sale_wanted", "joke_chatter"}
SEPARATE_ROLES = {"event", "memorial", "opinion", "unknown"}
DEFAULT_TARGET_WORDS = 180
DEFAULT_MAX_WORDS = 240
DEFAULT_MIN_WORDS = 8


def stable_hash(*parts: object, length: int = 10) -> str:
    payload = "\u241f".join("" if part is None else str(part) for part in parts)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:length]


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            value = json.loads(stripped)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            yield value


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def source_url(record: Mapping[str, Any]) -> str:
    return str(record.get("source_url") or record.get("thread_url") or "")


def text_for_chunk(record: Mapping[str, Any]) -> str:
    return compact_space(str(record.get("answer_text") or record.get("clean_text") or record.get("chunk_text") or ""))


def role_for(record: Mapping[str, Any]) -> str:
    return str(record.get("chunk_role") or record.get("post_role") or "unknown")


def source_metadata_complete(records: list[Mapping[str, Any]]) -> bool:
    return all(bool(record.get("source_metadata_complete", True)) for record in records)


def merged_post_uids(records: list[Mapping[str, Any]]) -> list[Any]:
    seen: set[str] = set()
    merged: list[Any] = []
    for record in records:
        for post_uid in as_list(record.get("post_uids") or record.get("post_uid")):
            key = str(post_uid)
            if key not in seen:
                seen.add(key)
                merged.append(post_uid)
    return merged


def merged_cleanup_flags(records: list[Mapping[str, Any]], extra: Iterable[str] = ()) -> list[str]:
    flags: set[str] = set(extra)
    for record in records:
        flags.update(str(flag) for flag in as_list(record.get("cleanup_flags")))
    return sorted(flags)


def record_risk_flags(record: Mapping[str, Any]) -> set[str]:
    flags: set[str] = set()
    cleanup_flags = set(str(flag) for flag in as_list(record.get("cleanup_flags")))
    detected_roles = set(str(role) for role in as_list(record.get("detected_roles")))
    role = role_for(record)
    if "quote_marker_detected" in cleanup_flags:
        flags.add("quote_heavy_flagged")
    mixed_roles = mixed_topic_roles(record)
    if role == ANSWER_ROLE and mixed_roles:
        flags.add("mixed_topic_flagged")
        flags.add("mixed_topic_quarantined")
    return flags


def mixed_topic_roles(record: Mapping[str, Any]) -> set[str]:
    detected_roles = set(str(role) for role in as_list(record.get("detected_roles")))
    cleaned_artifact_roles = {"contact_block", "gear_signature"}
    return detected_roles - {role_for(record), "answer_advice", "question"} - cleaned_artifact_roles


def post_role_summary(records: list[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter(role_for(record) for record in records)
    return dict(sorted(counts.items()))


def average_field(records: list[Mapping[str, Any]], field: str) -> float:
    values = []
    for record in records:
        try:
            values.append(float(record.get(field) or 0))
        except (TypeError, ValueError):
            values.append(0.0)
    return round(sum(values) / max(len(values), 1), 3)


def chunk_id_for(thread_id: str, chunk_role: str, chunk_index: int, text: str, records: list[Mapping[str, Any]]) -> str:
    source_ids = ",".join(str(record.get("chunk_id") or record.get("post_uid") or "") for record in records)
    digest = stable_hash(thread_id, chunk_role, chunk_index, source_ids, text)
    safe_thread = re.sub(r"[^A-Za-z0-9_.-]+", "-", thread_id or "unknown").strip("-") or "unknown"
    return f"v2:{safe_thread}:{chunk_role}:{chunk_index:04d}:{digest}"


def make_chunk(
    records: list[Mapping[str, Any]],
    text: str,
    *,
    chunk_role: str,
    chunk_index: int,
    extra_flags: Iterable[str] = (),
) -> dict[str, Any]:
    first = records[0]
    thread_id = str(first.get("thread_id") or "")
    cleanup_flags = merged_cleanup_flags(records, extra_flags)
    noise_score = average_field(records, "noise_score")
    quality = average_field(records, "quality_score")
    if "tiny_low_value_flagged" in cleanup_flags:
        quality = min(quality, 0.35)
    if "mixed_topic_flagged" in cleanup_flags:
        noise_score = max(noise_score, 0.65)
        quality = min(quality, 0.35)
    return {
        "chunk_id": chunk_id_for(thread_id, chunk_role, chunk_index, text, records),
        "source_system": first.get("source_system") or "",
        "forum_name": first.get("forum_name") or "",
        "thread_id": thread_id,
        "thread_title": first.get("thread_title") or "",
        "source_url": source_url(first),
        "post_uids": merged_post_uids(records),
        "chunk_text": compact_space(text),
        "chunk_role": chunk_role,
        "post_role_summary": post_role_summary(records),
        "quality_score": quality,
        "noise_score": noise_score,
        "cleanup_flags": cleanup_flags,
        "source_metadata_complete": source_metadata_complete(records),
    }


def split_text(text: str, max_words: int) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text]
    parts: list[str] = []
    current: list[str] = []
    for word in words:
        if current and len(current) + 1 > max_words:
            parts.append(" ".join(current))
            current = []
        current.append(word)
    if current:
        parts.append(" ".join(current))
    return parts


def should_skip_record(record: Mapping[str, Any], min_words: int) -> tuple[bool, str]:
    role = role_for(record)
    text = text_for_chunk(record)
    words = word_count(text)
    if role == ANSWER_ROLE and mixed_topic_roles(record):
        return True, "mixed_topic_quarantined"
    if role in EXCLUDED_ANSWER_ROLES:
        return True, f"excluded_role:{role}"
    if words < min_words and role not in {QUESTION_ROLE, ANSWER_ROLE}:
        return True, "tiny_low_value"
    return False, ""


def append_record_chunks(
    chunks: list[dict[str, Any]],
    record: Mapping[str, Any],
    *,
    chunk_index: int,
    max_words: int,
    min_words: int,
    extra_flags: Iterable[str] = (),
) -> int:
    text = text_for_chunk(record)
    role = role_for(record)
    flags = set(extra_flags) | record_risk_flags(record)
    if word_count(text) < min_words:
        flags.add("tiny_low_value_flagged")
    parts = split_text(text, max_words)
    if len(parts) > 1:
        flags.add("oversized_split")
    for part in parts:
        chunks.append(make_chunk([record], part, chunk_role=role, chunk_index=chunk_index, extra_flags=flags))
        chunk_index += 1
    return chunk_index


def build_thread_chunks(
    records: list[Mapping[str, Any]],
    *,
    target_words: int = DEFAULT_TARGET_WORDS,
    max_words: int = DEFAULT_MAX_WORDS,
    min_words: int = DEFAULT_MIN_WORDS,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    chunk_index = 1
    pending_question: Mapping[str, Any] | None = None
    answer_group: list[Mapping[str, Any]] = []
    answer_words = 0

    def flush_answers(extra_flags: Iterable[str] = ()) -> None:
        nonlocal answer_group, answer_words, chunk_index
        if not answer_group:
            return
        text = "\n\n".join(text_for_chunk(record) for record in answer_group)
        flags = set(extra_flags)
        role_counts = {role_for(record) for record in answer_group}
        if len(role_counts) > 1:
            flags.add("mixed_topic_flagged")
        for record in answer_group:
            flags.update(record_risk_flags(record))
        for part in split_text(text, max_words):
            part_flags = set(flags)
            if part != text:
                part_flags.add("oversized_split")
            chunks.append(
                make_chunk(answer_group, part, chunk_role=ANSWER_ROLE, chunk_index=chunk_index, extra_flags=part_flags)
            )
            chunk_index += 1
        answer_group = []
        answer_words = 0

    for record in records:
        role = role_for(record)
        text = text_for_chunk(record)
        skip, reason = should_skip_record(record, min_words)
        if skip:
            if pending_question is not None and role != ANSWER_ROLE:
                chunk_index = append_record_chunks(
                    chunks,
                    pending_question,
                    chunk_index=chunk_index,
                    max_words=max_words,
                    min_words=min_words,
                    extra_flags=["question_unpaired"],
                )
                pending_question = None
            continue

        if role == QUESTION_ROLE:
            flush_answers()
            if pending_question is not None:
                chunk_index = append_record_chunks(
                    chunks,
                    pending_question,
                    chunk_index=chunk_index,
                    max_words=max_words,
                    min_words=min_words,
                    extra_flags=["question_unpaired"],
                )
            pending_question = record
            continue

        if role == ANSWER_ROLE:
            if pending_question is not None:
                question_text = text_for_chunk(pending_question)
                combined = f"Question:\n{question_text}\n\nAnswer:\n{text}"
                if word_count(combined) <= max_words:
                    chunks.append(
                        make_chunk(
                            [pending_question, record],
                            combined,
                            chunk_role=ANSWER_ROLE,
                            chunk_index=chunk_index,
                            extra_flags=["question_paired"],
                        )
                    )
                    chunk_index += 1
                    pending_question = None
                    continue
                chunk_index = append_record_chunks(
                    chunks,
                    pending_question,
                    chunk_index=chunk_index,
                    max_words=max_words,
                    min_words=min_words,
                    extra_flags=["question_unpaired"],
                )
                pending_question = None

            record_words = word_count(text)
            if answer_group and answer_words + record_words > target_words:
                flush_answers()
            answer_group.append(record)
            answer_words += record_words
            continue

        flush_answers()
        if pending_question is not None:
            chunk_index = append_record_chunks(
                chunks,
                pending_question,
                chunk_index=chunk_index,
                max_words=max_words,
                min_words=min_words,
                extra_flags=["question_unpaired"],
            )
            pending_question = None
        chunk_index = append_record_chunks(
            chunks,
            record,
            chunk_index=chunk_index,
            max_words=max_words,
            min_words=min_words,
            extra_flags=["separate_role"],
        )

    flush_answers()
    if pending_question is not None:
        chunk_index = append_record_chunks(
            chunks,
            pending_question,
            chunk_index=chunk_index,
            max_words=max_words,
            min_words=min_words,
            extra_flags=["question_unpaired"],
        )
    return chunks


def group_by_thread(records: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record.get("thread_id") or "")].append(record)
    return dict(grouped)


def build_chunks(
    records: Iterable[Mapping[str, Any]],
    *,
    target_words: int = DEFAULT_TARGET_WORDS,
    max_words: int = DEFAULT_MAX_WORDS,
    min_words: int = DEFAULT_MIN_WORDS,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for thread_id, thread_records in sorted(group_by_thread(records).items()):
        chunks.extend(
            build_thread_chunks(
                thread_records,
                target_words=target_words,
                max_words=max_words,
                min_words=min_words,
            )
        )
    return chunks


def summarize(chunks: list[Mapping[str, Any]]) -> dict[str, Any]:
    role_counts = Counter(str(chunk.get("chunk_role") or "unknown") for chunk in chunks)
    flag_counts: Counter[str] = Counter()
    for chunk in chunks:
        flag_counts.update(str(flag) for flag in as_list(chunk.get("cleanup_flags")))
    return {
        "chunks": len(chunks),
        "role_counts": dict(sorted(role_counts.items())),
        "cleanup_flag_counts": dict(sorted(flag_counts.items())),
        "avg_noise_score": round(sum(float(chunk.get("noise_score") or 0) for chunk in chunks) / max(len(chunks), 1), 3),
        "avg_quality_score": round(sum(float(chunk.get("quality_score") or 0) for chunk in chunks) / max(len(chunks), 1), 3),
    }


def update_summary_counts(summary: dict[str, Any], chunk: Mapping[str, Any]) -> None:
    summary["chunks"] += 1
    summary["role_counts"][str(chunk.get("chunk_role") or "unknown")] += 1
    summary["cleanup_flag_counts"].update(str(flag) for flag in as_list(chunk.get("cleanup_flags")))
    summary["noise_score_total"] += float(chunk.get("noise_score") or 0)
    summary["quality_score_total"] += float(chunk.get("quality_score") or 0)


def finalize_summary(summary: Mapping[str, Any]) -> dict[str, Any]:
    chunks = int(summary["chunks"])
    return {
        "chunks": chunks,
        "role_counts": dict(sorted(summary["role_counts"].items())),
        "cleanup_flag_counts": dict(sorted(summary["cleanup_flag_counts"].items())),
        "avg_noise_score": round(float(summary["noise_score_total"]) / max(chunks, 1), 3),
        "avg_quality_score": round(float(summary["quality_score_total"]) / max(chunks, 1), 3),
    }


def build_chunks_file(
    input_path: Path,
    output_path: Path,
    *,
    target_words: int = DEFAULT_TARGET_WORDS,
    max_words: int = DEFAULT_MAX_WORDS,
    min_words: int = DEFAULT_MIN_WORDS,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "chunks": 0,
        "role_counts": Counter(),
        "cleanup_flag_counts": Counter(),
        "noise_score_total": 0.0,
        "quality_score_total": 0.0,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)

    current_thread_id: str | None = None
    thread_records: list[Mapping[str, Any]] = []

    def flush_thread(handle: Any) -> None:
        nonlocal thread_records
        if not thread_records:
            return
        chunks = build_thread_chunks(
            thread_records,
            target_words=target_words,
            max_words=max_words,
            min_words=min_words,
        )
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False, sort_keys=True) + "\n")
            update_summary_counts(summary, chunk)
        thread_records = []

    with output_path.open("w", encoding="utf-8") as handle:
        for record in iter_jsonl(input_path):
            thread_id = str(record.get("thread_id") or "")
            if current_thread_id is not None and thread_id != current_thread_id:
                flush_thread(handle)
            current_thread_id = thread_id
            thread_records.append(record)
        flush_thread(handle)

    return finalize_summary(summary)


def markdown_report(summary: Mapping[str, Any], input_path: Path, output_path: Path) -> str:
    lines = [
        "# Phase 3C Chunker V2 Sample Report",
        "",
        f"- Input: `{input_path}`",
        f"- Output: `{output_path}`",
        f"- Chunks: `{summary['chunks']}`",
        f"- Average noise score: `{summary['avg_noise_score']}`",
        f"- Average quality score: `{summary['avg_quality_score']}`",
        "",
        "## Role Counts",
        "| role | count |",
        "| --- | ---: |",
    ]
    for role, count in dict(summary["role_counts"]).items():
        lines.append(f"| `{role}` | {count} |")
    lines.extend(["", "## Cleanup Flag Counts", "| flag | count |", "| --- | ---: |"])
    for flag, count in dict(summary["cleanup_flag_counts"]).items():
        lines.append(f"| `{flag}` | {count} |")
    lines.append("")
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Phase 3B cleaned/classified JSONL input.")
    parser.add_argument("--output", required=True, type=Path, help="Sample chunk-v2 JSONL output.")
    parser.add_argument("--report", type=Path, help="Optional Markdown sample report.")
    parser.add_argument("--target-words", type=int, default=DEFAULT_TARGET_WORDS)
    parser.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS)
    parser.add_argument("--min-words", type=int, default=DEFAULT_MIN_WORDS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.target_words < 1 or args.max_words < 1 or args.min_words < 1:
        raise SystemExit("word limits must be positive")
    if args.target_words > args.max_words:
        raise SystemExit("--target-words must be less than or equal to --max-words")
    summary = build_chunks_file(
        args.input,
        args.output,
        target_words=args.target_words,
        max_words=args.max_words,
        min_words=args.min_words,
    )
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(markdown_report(summary, args.input, args.output), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
