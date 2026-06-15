#!/usr/bin/env python3
"""Validate curated guidance JSONL before any retrieval or embedding work."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


DEFAULT_INPUT = Path("corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl")
DEFAULT_REPORT = Path("corpus-private/reports/curated-guidance-validation.md")
DEFAULT_JSON_REPORT = Path("corpus-private/reports/curated-guidance-validation.json")

REQUIRED_FIELDS = {
    "content_layer",
    "visibility",
    "source_path",
    "source_filename",
    "source_sha256",
    "title",
    "body",
    "word_count",
    "topics",
    "technique_tags",
    "instrument",
    "strings",
    "pedals_levers",
    "frets",
    "keys",
    "difficulty",
    "needs_review",
    "quality_flags",
}
VALID_INSTRUMENTS = {"unknown", "E9", "C6", "non_pedal", "general"}
VALID_DIFFICULTIES = {"unknown", "beginner", "intermediate", "advanced"}
STEEL_TERMS = (
    "e9",
    "c6",
    "steel",
    "pedal",
    "lever",
    "string",
    "fret",
    "bar",
    "grip",
    "pocket",
    "copedent",
    "changer",
    "blocking",
    "volume pedal",
)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    rows: list[dict[str, Any]]
    failures: list[str]
    warnings: list[str]
    flag_counts: Counter[str]
    instrument_counts: Counter[str]
    difficulty_counts: Counter[str]
    word_stats: dict[str, int | float]
    duplicate_hashes: dict[str, list[str]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate curated-guidance private-review JSONL.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Curated guidance JSONL path.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Markdown validation report path.")
    parser.add_argument("--json-report", default=str(DEFAULT_JSON_REPORT), help="JSON validation report path.")
    parser.add_argument("--max-words", type=int, default=2500, help="Reasonable per-row chunk size.")
    return parser.parse_args()


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            row["_line_number"] = line_number
            yield row


def word_stats(values: list[int]) -> dict[str, int | float]:
    if not values:
        return {"min": 0, "max": 0, "avg": 0}
    return {"min": min(values), "max": max(values), "avg": round(mean(values), 2)}


def detect_flags(row: dict[str, Any], max_words: int) -> set[str]:
    flags = set(str(flag) for flag in row.get("quality_flags") or [])
    body = str(row.get("body") or "")
    lowered = body.lower()
    if "the player should" in lowered:
        flags.add("contains_player_should_phrase")
    if re.search(r"\b(?:webvtt|\d{1,2}:\d{2}(?::\d{2})?[,.]\d{3}\s+-->|^speaker\s*\d*:)", body, re.I | re.M):
        flags.add("possible_transcript_residue")
    if re.search(r"\b(?:i'm going to show|i want you to|my students|in this lesson i|let me show you)\b", lowered):
        flags.add("first_person_instructor_phrasing")
    if not str(row.get("title") or "").strip():
        flags.add("missing_title")
    if not row.get("topics"):
        flags.add("missing_topic_tags")
    word_count = int(row.get("word_count") or 0)
    if word_count < 100:
        flags.add("body_under_100_words")
    if word_count > max_words:
        flags.add("body_over_reasonable_chunk_size")
    if row.get("visibility") != "private_review" or row.get("needs_review") is not True:
        flags.add("unclear_rights_visibility")
    if not any(term in lowered for term in STEEL_TERMS):
        flags.add("no_steel_specific_terms")
    return flags


def validate_rows(input_path: Path, *, max_words: int = 2500) -> ValidationResult:
    failures: list[str] = []
    warnings: list[str] = []
    if not input_path.exists():
        return ValidationResult(
            ok=False,
            rows=[],
            failures=[f"Input file does not exist: {input_path}"],
            warnings=[],
            flag_counts=Counter(),
            instrument_counts=Counter(),
            difficulty_counts=Counter(),
            word_stats={"min": 0, "max": 0, "avg": 0},
            duplicate_hashes={},
        )

    rows = list(read_jsonl(input_path))
    hash_paths: dict[str, list[str]] = defaultdict(list)
    flag_counts: Counter[str] = Counter()
    instrument_counts: Counter[str] = Counter()
    difficulty_counts: Counter[str] = Counter()
    words: list[int] = []
    seen_paths: set[str] = set()

    for index, row in enumerate(rows, start=1):
        label = f"row {row.get('_line_number', index)}"
        missing = sorted(field for field in REQUIRED_FIELDS if field not in row)
        if missing:
            failures.append(f"{label}: missing required fields: {', '.join(missing)}")

        if row.get("content_layer") != "curated_guidance":
            failures.append(f"{label}: content_layer must be curated_guidance")
        if row.get("visibility") != "private_review":
            failures.append(f"{label}: visibility must remain private_review")
        if row.get("needs_review") is not True:
            failures.append(f"{label}: needs_review must be true")

        source_path = str(row.get("source_path") or "")
        if not source_path:
            failures.append(f"{label}: missing source_path")
        elif source_path in seen_paths:
            failures.append(f"{label}: duplicate source_path {source_path}")
        seen_paths.add(source_path)

        source_hash = str(row.get("source_sha256") or "")
        if source_hash:
            hash_paths[source_hash].append(source_path)
        else:
            failures.append(f"{label}: missing source_sha256")

        instrument = str(row.get("instrument") or "")
        difficulty = str(row.get("difficulty") or "")
        instrument_counts[instrument] += 1
        difficulty_counts[difficulty] += 1
        if instrument not in VALID_INSTRUMENTS:
            failures.append(f"{label}: invalid instrument {instrument!r}")
        if difficulty not in VALID_DIFFICULTIES:
            failures.append(f"{label}: invalid difficulty {difficulty!r}")

        word_count = int(row.get("word_count") or 0)
        words.append(word_count)
        detected = detect_flags(row, max_words)
        flag_counts.update(detected)
        for flag in sorted(detected):
            warnings.append(f"{label}: {flag} ({source_path})")

    duplicate_hashes = {hash_value: paths for hash_value, paths in hash_paths.items() if len(paths) > 1}
    for hash_value, paths in duplicate_hashes.items():
        flag_counts["possible_duplicate_files_by_hash"] += len(paths)
        warnings.append(f"duplicate hash {hash_value[:12]}: {len(paths)} files")

    return ValidationResult(
        ok=not failures,
        rows=rows,
        failures=failures,
        warnings=warnings,
        flag_counts=flag_counts,
        instrument_counts=instrument_counts,
        difficulty_counts=difficulty_counts,
        word_stats=word_stats(words),
        duplicate_hashes=duplicate_hashes,
    )


def render_counter(counter: Counter[str]) -> list[str]:
    if not counter:
        return ["- None"]
    return [f"- `{key}`: {value}" for key, value in sorted(counter.items())]


def redacted_examples(rows: list[dict[str, Any]], limit: int = 3) -> list[str]:
    examples: list[str] = []
    for row in rows[:limit]:
        public_row = {
            "content_layer": row.get("content_layer"),
            "visibility": row.get("visibility"),
            "source_path": row.get("source_path"),
            "source_filename": row.get("source_filename"),
            "source_sha256": f"{str(row.get('source_sha256', ''))[:12]}...",
            "title": row.get("title"),
            "body": "<private_review body omitted from handoff/report preview>",
            "word_count": row.get("word_count"),
            "topics": row.get("topics"),
            "technique_tags": row.get("technique_tags"),
            "instrument": row.get("instrument"),
            "strings": row.get("strings"),
            "pedals_levers": row.get("pedals_levers"),
            "frets": row.get("frets"),
            "keys": row.get("keys"),
            "difficulty": row.get("difficulty"),
            "needs_review": row.get("needs_review"),
            "quality_flags": row.get("quality_flags"),
        }
        examples.append("```json\n" + json.dumps(public_row, indent=2, ensure_ascii=False) + "\n```")
    return examples


def render_report(result: ValidationResult, input_path: Path) -> str:
    lines = [
        "# Curated Guidance Validation Report",
        "",
        "Private/local validation report. Generated body previews are redacted to avoid committing private teaching text.",
        "",
        f"- Input: `{input_path.as_posix()}`",
        f"- Rows: {len(result.rows)}",
        f"- OK: {result.ok}",
        "",
        "## Word Count Stats",
        "",
        f"- min: {result.word_stats['min']}",
        f"- max: {result.word_stats['max']}",
        f"- avg: {result.word_stats['avg']}",
        "",
        "## Instrument Counts",
        "",
    ]
    lines.extend(render_counter(result.instrument_counts))
    lines.extend(["", "## Difficulty Counts", ""])
    lines.extend(render_counter(result.difficulty_counts))
    lines.extend(["", "## Quality Flag Counts", ""])
    lines.extend(render_counter(result.flag_counts))
    lines.extend(["", "## Failures", ""])
    lines.extend(f"- {failure}" for failure in result.failures[:200]) if result.failures else lines.append("- None")
    if len(result.failures) > 200:
        lines.append(f"- ... {len(result.failures) - 200} more")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in result.warnings[:200]) if result.warnings else lines.append("- None")
    if len(result.warnings) > 200:
        lines.append(f"- ... {len(result.warnings) - 200} more")
    lines.extend(["", "## Redacted Example Rows", ""])
    lines.extend(redacted_examples(result.rows))
    return "\n".join(lines) + "\n"


def write_json_report(result: ValidationResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "ok": result.ok,
        "row_count": len(result.rows),
        "failures": result.failures,
        "warnings": result.warnings,
        "flag_counts": dict(result.flag_counts),
        "instrument_counts": dict(result.instrument_counts),
        "difficulty_counts": dict(result.difficulty_counts),
        "word_stats": result.word_stats,
        "duplicate_hashes": result.duplicate_hashes,
    }
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    result = validate_rows(input_path, max_words=args.max_words)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(result, input_path), encoding="utf-8")
    write_json_report(result, Path(args.json_report))
    print(f"Validated {len(result.rows)} curated guidance row(s).")
    print(f"Failures: {len(result.failures)}")
    print(f"Warnings: {len(result.warnings)}")
    print(f"Wrote validation report: {report_path}")
    print(f"Wrote validation JSON: {args.json_report}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
