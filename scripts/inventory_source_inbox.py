#!/usr/bin/env python3
"""Create a metadata-only inventory of source-inbox candidates.

This script is intentionally read-only with respect to source files. It records
file metadata and light text counts, but it does not ingest, normalize, chunk, or
embed any source content.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUPPORTED_EXTENSIONS = {
    ".txt": "txt",
    ".md": "md",
    ".pdf": "pdf",
    ".vtt": "vtt",
    ".srt": "srt",
    ".docx": "docx",
}

TEXT_FILE_TYPES = {"txt", "md", "vtt", "srt"}

FOLDER_MAPPING = {
    "private-lessons": {
        "source_system": "private_lesson_transcript",
        "visibility": "private",
        "recommendation": (
            "Review permission, privacy, and provenance before any ingestion; "
            "keep private unless explicitly approved."
        ),
    },
    "public-reference": {
        "source_system": "public_reference",
        "visibility": "public",
        "recommendation": "Review license and provenance before ingestion.",
    },
    "manuals": {
        "source_system": "steel_manual",
        "visibility": "review",
        "recommendation": "Review manual rights and provenance before ingestion.",
    },
    "pdfs": {
        "source_system": "pdf_reference",
        "visibility": "review",
        "recommendation": "PDF metadata only for now; extract text only after review.",
    },
    "transcripts": {
        "source_system": "transcript",
        "visibility": "review",
        "recommendation": "Review transcript source, permission, and rights before ingestion.",
    },
    "rules": {
        "source_system": "personal_rules_note",
        "visibility": "private",
        "recommendation": (
            "Consider rules-layer conversion; do not embed personal rules notes by default."
        ),
    },
    "curated-sources": {
        "source_system": "curated_source_candidate",
        "visibility": "review",
        "recommendation": (
            "Consider curated source registry entry; do not embed as RAG text by default."
        ),
    },
    "pending-review": {
        "source_system": "pending_review",
        "visibility": "review",
        "recommendation": "Human review required before routing or ingestion.",
    },
}

ROOT_DEFAULT = {
    "source_system": "pending_review",
    "visibility": "review",
    "recommendation": "Review manually before ingestion.",
}


@dataclass
class InventoryRow:
    path: str
    filename: str
    extension: str
    file_type: str
    file_size_bytes: int
    modified_time: str
    likely_source_category: str
    source_system_suggestion: str
    visibility_suggestion: str
    ingestion_recommendation: str
    approximate_line_count: int | None = None
    approximate_character_count: int | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory source-inbox files without ingesting source content."
    )
    parser.add_argument(
        "--source",
        default="source-inbox",
        help="Source inbox directory to scan. Default: source-inbox",
    )
    parser.add_argument(
        "--output",
        default="source-inbox/inventory.json",
        help="JSON inventory output path. Default: source-inbox/inventory.json",
    )
    parser.add_argument(
        "--markdown",
        default="docs/source-inbox-inventory.md",
        help="Markdown summary output path. Default: docs/source-inbox-inventory.md",
    )
    return parser.parse_args()


def utc_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def detect_file_type(path: Path) -> str:
    return SUPPORTED_EXTENSIONS.get(path.suffix.lower(), "unknown")


def classify_folder(path: Path, source_root: Path) -> dict[str, str]:
    relative = path.relative_to(source_root)
    top_folder = relative.parts[0] if len(relative.parts) > 1 else "source-inbox-root"
    mapping = FOLDER_MAPPING.get(top_folder, ROOT_DEFAULT)
    return {
        "likely_source_category": top_folder,
        "source_system_suggestion": mapping["source_system"],
        "visibility_suggestion": mapping["visibility"],
        "ingestion_recommendation": mapping["recommendation"],
    }


def count_text_file(path: Path) -> tuple[int, int]:
    line_count = 0
    character_count = 0
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line_count += 1
            character_count += len(line)
    return line_count, character_count


def resolved(path: Path) -> Path:
    return path.expanduser().resolve()


def should_skip_file(
    path: Path, output_path: Path, markdown_path: Path
) -> tuple[bool, str | None]:
    if path.name.startswith("."):
        return True, "hidden_or_placeholder"

    path_resolved = resolved(path)
    generated_paths = {resolved(output_path), resolved(markdown_path)}
    if path_resolved in generated_paths:
        return True, "generated_inventory_output"

    if path.name == ".DS_Store":
        return True, "system_file"

    return False, None


def build_inventory(source_root: Path, output_path: Path, markdown_path: Path) -> dict[str, Any]:
    files: list[InventoryRow] = []
    skipped_reasons: Counter[str] = Counter()

    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue

        skip, reason = should_skip_file(path, output_path, markdown_path)
        if skip:
            skipped_reasons[reason or "skipped"] += 1
            continue

        stat = path.stat()
        file_type = detect_file_type(path)
        folder_classification = classify_folder(path, source_root)

        line_count: int | None = None
        character_count: int | None = None
        if file_type in TEXT_FILE_TYPES:
            line_count, character_count = count_text_file(path)

        files.append(
            InventoryRow(
                path=path.as_posix(),
                filename=path.name,
                extension=path.suffix.lower().lstrip("."),
                file_type=file_type,
                file_size_bytes=stat.st_size,
                modified_time=utc_timestamp(stat.st_mtime),
                approximate_line_count=line_count,
                approximate_character_count=character_count,
                **folder_classification,
            )
        )

    counts_by_file_type = Counter(row.file_type for row in files)
    counts_by_source_system = Counter(row.source_system_suggestion for row in files)
    counts_by_visibility = Counter(row.visibility_suggestion for row in files)
    counts_by_category = Counter(row.likely_source_category for row in files)

    return {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "source_root": source_root.as_posix(),
        "total_files": len(files),
        "skipped_files": sum(skipped_reasons.values()),
        "skipped_reasons": dict(sorted(skipped_reasons.items())),
        "counts_by_file_type": dict(sorted(counts_by_file_type.items())),
        "counts_by_source_system": dict(sorted(counts_by_source_system.items())),
        "counts_by_visibility": dict(sorted(counts_by_visibility.items())),
        "counts_by_category": dict(sorted(counts_by_category.items())),
        "files": [asdict(row) for row in files],
    }


def markdown_escape(value: object) -> str:
    text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def render_counter(counter: dict[str, int]) -> list[str]:
    if not counter:
        return ["- None"]
    return [f"- `{key}`: {value}" for key, value in sorted(counter.items())]


def render_markdown(inventory: dict[str, Any]) -> str:
    lines = [
        "# Source Inbox Inventory",
        "",
        "This report is metadata-only. It does not ingest, normalize, chunk, or embed source files.",
        "",
        f"- Generated: `{inventory['generated_at']}`",
        f"- Source root: `{inventory['source_root']}`",
        f"- Candidate files: `{inventory['total_files']}`",
        f"- Skipped hidden/generated files: `{inventory['skipped_files']}`",
        "",
        "## Counts By File Type",
        "",
        *render_counter(inventory["counts_by_file_type"]),
        "",
        "## Counts By Source System Suggestion",
        "",
        *render_counter(inventory["counts_by_source_system"]),
        "",
        "## Counts By Visibility Suggestion",
        "",
        *render_counter(inventory["counts_by_visibility"]),
        "",
        "## Counts By Folder Category",
        "",
        *render_counter(inventory["counts_by_category"]),
        "",
        "## Candidate Files",
        "",
    ]

    files = inventory["files"]
    if not files:
        lines.append("No candidate files were found.")
        lines.append("")
        return "\n".join(lines)

    lines.extend(
        [
            "| Path | Type | Size | Lines | Characters | Source System | Visibility | Recommendation |",
            "| --- | --- | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for row in files:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_escape(row["path"]),
                    markdown_escape(row["file_type"]),
                    markdown_escape(row["file_size_bytes"]),
                    markdown_escape(row.get("approximate_line_count") or ""),
                    markdown_escape(row.get("approximate_character_count") or ""),
                    markdown_escape(row["source_system_suggestion"]),
                    markdown_escape(row["visibility_suggestion"]),
                    markdown_escape(row["ingestion_recommendation"]),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def write_outputs(inventory: dict[str, Any], output_path: Path, markdown_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(inventory), encoding="utf-8")


def main() -> int:
    args = parse_args()
    source_root = Path(args.source)
    output_path = Path(args.output)
    markdown_path = Path(args.markdown)

    if not source_root.exists():
        raise SystemExit(f"Source directory does not exist: {source_root}")
    if not source_root.is_dir():
        raise SystemExit(f"Source path is not a directory: {source_root}")

    inventory = build_inventory(source_root, output_path, markdown_path)
    write_outputs(inventory, output_path, markdown_path)

    print(f"Inventoried {inventory['total_files']} candidate file(s).")
    print(f"Skipped {inventory['skipped_files']} hidden/generated file(s).")
    print(f"Wrote JSON: {output_path}")
    print(f"Wrote Markdown: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
