#!/usr/bin/env python3
"""Preflight private source-inbox chunks before any embedding run."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Iterable


DEFAULT_INPUT = Path("corpus-private/chunks/source-inbox-chunks.jsonl")
DEFAULT_VECTOR_PATH = Path("corpus-private/vector-stores/chroma")
DEFAULT_COLLECTION = "steel_guitar_private_sources_v1"
DEFAULT_REPORT = Path("corpus-private/reports/private-source-embed-preflight.md")
EXPECTED_COLLECTION = "steel_guitar_private_sources_v1"

REQUIRED_FIELDS = {
    "chunk_id",
    "source_id",
    "source_system",
    "visibility",
    "source_path",
    "title",
    "text",
    "provenance_status",
    "embedding_allowed",
    "redistribution_allowed",
    "answer_quote_allowed",
}

KNOWN_NON_PRIVATE_VECTOR_PARTS = (
    ("data", "rag", "chroma"),
    ("rag-data",),
    ("corpus-v2",),
    ("corpus-unified",),
    ("sgf-output",),
)


@dataclass
class PreflightResult:
    ok: bool
    chunk_count: int
    failures: list[str]
    warnings: list[str]
    source_system_counts: Counter[str]
    visibility_counts: Counter[str]
    source_id_counts: Counter[str]
    length_stats: dict[str, int | float]
    vector_path: str
    collection: str


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            value["_line_number"] = line_number
            yield value


def truthy_embedding(value: Any) -> bool:
    return value is True or (isinstance(value, str) and value.lower() == "true")


def path_parts(path: Path) -> tuple[str, ...]:
    return tuple(part for part in path.as_posix().split("/") if part and part != ".")


def contains_sequence(parts: tuple[str, ...], sequence: tuple[str, ...]) -> bool:
    if len(sequence) > len(parts):
        return False
    for index in range(0, len(parts) - len(sequence) + 1):
        if parts[index : index + len(sequence)] == sequence:
            return True
    return False


def vector_path_is_private(vector_path: Path) -> bool:
    parts = path_parts(vector_path)
    if "corpus-private" not in parts:
        return False
    return not any(contains_sequence(parts, sequence) for sequence in KNOWN_NON_PRIVATE_VECTOR_PARTS)


def length_stats(lengths: list[int]) -> dict[str, int | float]:
    if not lengths:
        return {"min": 0, "max": 0, "avg": 0, "tiny_lt_threshold": 0}
    return {
        "min": min(lengths),
        "max": max(lengths),
        "avg": round(mean(lengths), 2),
        "tiny_lt_threshold": 0,
    }


def validate_chunks(
    input_path: Path,
    *,
    vector_path: Path = DEFAULT_VECTOR_PATH,
    collection: str = DEFAULT_COLLECTION,
    tiny_threshold: int = 80,
) -> PreflightResult:
    failures: list[str] = []
    warnings: list[str] = []

    if not input_path.exists():
        failures.append(f"Input file does not exist: {input_path}")
        return PreflightResult(
            ok=False,
            chunk_count=0,
            failures=failures,
            warnings=warnings,
            source_system_counts=Counter(),
            visibility_counts=Counter(),
            source_id_counts=Counter(),
            length_stats={"min": 0, "max": 0, "avg": 0, "tiny_lt_threshold": 0},
            vector_path=vector_path.as_posix(),
            collection=collection,
        )

    chunks = list(read_jsonl(input_path))
    if not chunks:
        failures.append("Chunk count is 0.")

    if collection != EXPECTED_COLLECTION:
        failures.append(f"Collection must be {EXPECTED_COLLECTION!r}, got {collection!r}.")

    if not vector_path_is_private(vector_path):
        failures.append(
            "Planned vector path must live under corpus-private/ and be separate from SGF v1/v2 paths."
        )

    seen_chunk_ids: set[str] = set()
    source_system_counts: Counter[str] = Counter()
    visibility_counts: Counter[str] = Counter()
    source_id_counts: Counter[str] = Counter()
    lengths: list[int] = []
    tiny_count = 0

    for index, chunk in enumerate(chunks, start=1):
        label = f"row {chunk.get('_line_number', index)}"
        missing = sorted(field for field in REQUIRED_FIELDS if chunk.get(field) in (None, ""))
        if missing:
            failures.append(f"{label}: missing required fields: {', '.join(missing)}")

        chunk_id = str(chunk.get("chunk_id") or "")
        if chunk_id in seen_chunk_ids:
            failures.append(f"{label}: duplicate chunk_id {chunk_id!r}")
        if chunk_id:
            seen_chunk_ids.add(chunk_id)

        source_system = str(chunk.get("source_system") or "")
        visibility = str(chunk.get("visibility") or "")
        source_id = str(chunk.get("source_id") or "")
        source_path = str(chunk.get("source_path") or "")
        file_type = str(chunk.get("file_type") or Path(source_path).suffix.lower().lstrip("."))
        text = str(chunk.get("text") or "")

        source_system_counts[source_system] += 1
        visibility_counts[visibility] += 1
        source_id_counts[source_id] += 1

        if visibility not in {"private", "public", "review"}:
            failures.append(f"{label}: invalid visibility {visibility!r}")
        if visibility in {"public", "review"} and chunk.get("provenance_status") != "reviewed":
            failures.append(f"{label}: public/review visibility requires reviewed provenance.")

        if not truthy_embedding(chunk.get("embedding_allowed")):
            failures.append(f"{label}: embedding_allowed is false or not explicitly true.")

        if not text.strip():
            failures.append(f"{label}: empty text.")
        else:
            length = len(text)
            lengths.append(length)
            if length < tiny_threshold:
                tiny_count += 1
                failures.append(f"{label}: tiny chunk under threshold ({length} < {tiny_threshold}).")

        if file_type in {"pdf", "docx"} or source_path.lower().endswith((".pdf", ".docx")):
            failures.append(f"{label}: unsupported PDF/DOCX text appears in private chunks.")

        if source_system == "curated_source_candidate":
            failures.append(f"{label}: curated-source candidate should use source registry, not embeddings.")

        if visibility == "private" and chunk.get("redistribution_allowed") is True:
            warnings.append(f"{label}: private chunk has redistribution_allowed=true; verify this is intentional.")

    stats = length_stats(lengths)
    stats["tiny_lt_threshold"] = tiny_count

    return PreflightResult(
        ok=not failures,
        chunk_count=len(chunks),
        failures=failures,
        warnings=warnings,
        source_system_counts=source_system_counts,
        visibility_counts=visibility_counts,
        source_id_counts=source_id_counts,
        length_stats=stats,
        vector_path=vector_path.as_posix(),
        collection=collection,
    )


def render_counter(counter: Counter[str]) -> list[str]:
    if not counter:
        return ["- None"]
    return [f"- `{key}`: {value}" for key, value in sorted(counter.items())]


def render_report(result: PreflightResult, input_path: Path, tiny_threshold: int) -> str:
    failures = [f"- {failure}" for failure in result.failures] if result.failures else ["- None"]
    warnings = [f"- {warning}" for warning in result.warnings] if result.warnings else ["- None"]
    lines = [
        "# Private Source Embed Preflight",
        "",
        "This report validates private source-inbox chunks before embeddings. It does not run embeddings or write Chroma.",
        "",
        f"- Input chunks: `{input_path.as_posix()}`",
        f"- Planned vector path: `{result.vector_path}`",
        f"- Planned collection: `{result.collection}`",
        f"- Status: `{'pass' if result.ok else 'fail'}`",
        f"- Chunk count: `{result.chunk_count}`",
        f"- Tiny threshold: `{tiny_threshold}` characters",
        "",
        "## Source System Counts",
        "",
        *render_counter(result.source_system_counts),
        "",
        "## Visibility Counts",
        "",
        *render_counter(result.visibility_counts),
        "",
        "## Source ID Counts",
        "",
        *render_counter(result.source_id_counts),
        "",
        "## Chunk Length Stats",
        "",
        f"- Min: `{result.length_stats['min']}`",
        f"- Max: `{result.length_stats['max']}`",
        f"- Avg: `{result.length_stats['avg']}`",
        f"- Tiny under threshold: `{result.length_stats['tiny_lt_threshold']}`",
        "",
        "## Failures",
        "",
        *failures,
        "",
        "## Warnings",
        "",
        *warnings,
        "",
    ]
    return "\n".join(lines)


def write_report(path: Path, result: PreflightResult, input_path: Path, tiny_threshold: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report(result, input_path, tiny_threshold), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--vector-path", type=Path, default=DEFAULT_VECTOR_PATH)
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--tiny-threshold", type=int, default=80)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    result = validate_chunks(
        args.input,
        vector_path=args.vector_path,
        collection=args.collection,
        tiny_threshold=args.tiny_threshold,
    )
    write_report(args.report, result, args.input, args.tiny_threshold)
    print(f"Preflight status: {'pass' if result.ok else 'fail'}")
    print(f"Chunks checked: {result.chunk_count}")
    print(f"Failures: {len(result.failures)}")
    print(f"Warnings: {len(result.warnings)}")
    print(f"Report: {args.report}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
