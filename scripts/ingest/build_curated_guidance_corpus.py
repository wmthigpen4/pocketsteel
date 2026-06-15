#!/usr/bin/env python3
"""Build a private-review curated guidance JSONL export from markdown summaries.

This is intentionally separate from SGF/forum corpus ingestion. It reads local
markdown guidance summaries, writes ignored private JSONL/report artifacts, and
does not embed content or touch Chroma.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


DEFAULT_SOURCE_CANDIDATES = (
    Path.home() / "Documents/vtt-test/guidance-cleaned",
    Path.home() / "Document/vtt-test/guidance-cleaned",
)
DEFAULT_OUTPUT = Path("corpus-private/curated-guidance/normalized/curated-guidance-documents.jsonl")
DEFAULT_PRIVATE_INVENTORY = Path("corpus-private/reports/curated-guidance-inventory-full.md")

STEEL_TERMS = {
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
    "knee",
    "dobro",
    "lap steel",
}
TOPIC_KEYWORDS = {
    "bar control": ("bar control", "bar", "intonation", "vibrato", "slant"),
    "blocking": ("blocking", "block", "palm", "pick blocking"),
    "chords": ("chord", "harmony", "interval", "triad", "dominant", "minor", "major"),
    "copedent": ("copedent", "pedal setup", "pedal", "lever", "changer"),
    "fills": ("fill", "fills", "solo", "lick", "phrase", "turnaround"),
    "grips": ("grip", "strings 3", "strings 4", "strings 5", "string group"),
    "practice": ("practice", "exercise", "routine", "drill"),
    "right hand": ("right hand", "picks", "pick", "attack"),
    "scales": ("scale", "diatonic", "major scale", "minor scale"),
    "tone": ("tone", "amp", "settings", "volume pedal", "pickups"),
}
TECHNIQUE_KEYWORDS = {
    "bar slants": ("slant", "slants"),
    "blocking": ("blocking", "palm block", "pick block"),
    "chimes": ("chime", "harmonic", "harmonics"),
    "grips": ("grip", "grips"),
    "hammer-ons": ("hammer-on", "hammer on", "pull-off", "pull off"),
    "pedal movement": ("pedal", "a+b", "b+c", "a pedal", "b pedal", "c pedal"),
    "right hand": ("right hand", "pick attack", "fingerpick"),
    "volume pedal": ("volume pedal", "swell"),
}
KEY_RE = re.compile(r"\b(?:key\s+of\s+)?([A-G](?:#|b)?)(?:\s+(?:major|minor))?\b")
FRET_RE = re.compile(r"\b(?:fret|frets|at)\s+(\d{1,2})(?:st|nd|rd|th)?\b|\b(\d{1,2})(?:st|nd|rd|th)\s+fret\b", re.I)
STRING_RE = re.compile(r"\bstrings?\s+((?:\d{1,2}\s*(?:,|and|-)?\s*)+)\b", re.I)
PEDAL_LEVER_PATTERNS = {
    "A": re.compile(r"\b(?:a\s+pedal|p1|pedal\s+a|a\+b|a\+f)\b", re.I),
    "B": re.compile(r"\b(?:b\s+pedal|p2|pedal\s+b|a\+b|b\+c)\b", re.I),
    "C": re.compile(r"\b(?:c\s+pedal|p3|pedal\s+c|b\+c)\b", re.I),
    "E-lower": re.compile(r"\b(?:e[-\s]?lower|lower(?:ing)?\s+the\s+e'?s|e\s+lever)\b", re.I),
    "F": re.compile(r"\b(?:f\s+lever|e[-\s]?raise|raises?\s+the\s+e'?s|a\+f)\b", re.I),
    "vertical/Bb": re.compile(r"\b(?:vertical|bb\s+lever|b\s+to\s+bb|b\s+to\s+a#)\b", re.I),
}


@dataclass(frozen=True)
class BuildResult:
    source_root: Path
    output_path: Path
    inventory_path: Path
    files_found: int
    files_processed: int
    files_skipped: int
    quality_counts: Counter[str]
    instrument_counts: Counter[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build curated-guidance private-review JSONL from markdown files.")
    parser.add_argument("--source", help="Guidance markdown root. Defaults to ~/Documents/vtt-test/guidance-cleaned.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Ignored private JSONL output path.")
    parser.add_argument(
        "--inventory-report",
        default=str(DEFAULT_PRIVATE_INVENTORY),
        help="Ignored private full inventory report path.",
    )
    return parser.parse_args()


def resolve_source_root(source_arg: str | None = None) -> Path:
    if source_arg:
        source = Path(source_arg).expanduser()
        if not source.exists():
            raise SystemExit(f"Guidance source path does not exist: {source}")
        if not source.is_dir():
            raise SystemExit(f"Guidance source path is not a directory: {source}")
        return source

    for candidate in DEFAULT_SOURCE_CANDIDATES:
        if candidate.exists() and candidate.is_dir():
            return candidate
    checked = ", ".join(path.as_posix() for path in DEFAULT_SOURCE_CANDIDATES)
    raise SystemExit(f"Guidance source path not found. Checked: {checked}")


def markdown_files(source_root: Path) -> list[Path]:
    return sorted(path for path in source_root.rglob("*.md") if path.is_file())


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_markdown(text: str) -> str:
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.splitlines()]
    return re.sub(r"\n{4,}", "\n\n\n", "\n".join(lines)).strip()


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    body = text[text.find("\n", end + 4) + 1 :]
    metadata: dict[str, Any] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if value.startswith("[") and value.endswith("]"):
            metadata[key] = [part.strip().strip('"').strip("'") for part in value[1:-1].split(",") if part.strip()]
        else:
            metadata[key] = value
    return metadata, body


def slug_to_title(text: str) -> str:
    text = re.sub(r"^[0-9a-f]{8,}-", "", text)
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text.title() if text else "Untitled"


def extract_title(path: Path, source_root: Path, metadata: dict[str, Any], body: str) -> str:
    title = str(metadata.get("title") or "").strip()
    if title:
        return title
    for line in body.splitlines():
        match = re.match(r"^\s*#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    if path.name == "guidance_draft.md" and path.parent != source_root:
        return slug_to_title(path.parent.name)
    return slug_to_title(path.stem)


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w#+'-]+\b", text))


def metadata_list(metadata: dict[str, Any], *keys: str) -> list[str]:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [part.strip() for part in re.split(r",|;", value) if part.strip()]
    return []


def keyword_tags(text: str, mapping: dict[str, tuple[str, ...]]) -> list[str]:
    lowered = text.lower()
    tags = [tag for tag, needles in mapping.items() if any(needle in lowered for needle in needles)]
    return sorted(set(tags))


def infer_topics(metadata: dict[str, Any], text: str) -> list[str]:
    return sorted(set(metadata_list(metadata, "topics", "topic", "tags") + keyword_tags(text, TOPIC_KEYWORDS)))


def infer_technique_tags(metadata: dict[str, Any], text: str) -> list[str]:
    return sorted(set(metadata_list(metadata, "technique_tags", "techniques") + keyword_tags(text, TECHNIQUE_KEYWORDS)))


def infer_instrument(text: str) -> str:
    lowered = text.lower()
    if re.search(r"\be9(?:th)?\b", lowered):
        return "E9"
    if re.search(r"\bc6(?:th)?\b", lowered):
        return "C6"
    if "dobro" in lowered or "lap steel" in lowered or "non-pedal" in lowered:
        return "non_pedal"
    if any(term in lowered for term in ("pedal steel", "steel guitar", "steel")):
        return "general"
    return "unknown"


def extract_strings(text: str) -> list[int]:
    found: set[int] = set()
    for match in STRING_RE.finditer(text):
        token = match.group(1)
        for number in re.findall(r"\d{1,2}", token):
            value = int(number)
            if 1 <= value <= 12:
                found.add(value)
    return sorted(found)


def extract_frets(text: str) -> list[int]:
    found: set[int] = set()
    for match in FRET_RE.finditer(text):
        for group in match.groups():
            if group:
                value = int(group)
                if 0 <= value <= 36:
                    found.add(value)
    return sorted(found)


def extract_keys(text: str) -> list[str]:
    found: set[str] = set()
    false_positives = {"A", "I"}
    for match in KEY_RE.finditer(text):
        key = match.group(1)
        if key in false_positives and match.group(0).lower() not in {"key of a", "a major", "a minor"}:
            continue
        found.add(key)
    return sorted(found)


def extract_pedals_levers(text: str) -> list[str]:
    return sorted(label for label, pattern in PEDAL_LEVER_PATTERNS.items() if pattern.search(text))


def infer_difficulty(metadata: dict[str, Any], text: str) -> str:
    explicit = str(metadata.get("difficulty") or "").lower().strip()
    if explicit in {"beginner", "intermediate", "advanced"}:
        return explicit
    lowered = text.lower()
    if any(term in lowered for term in ("advanced", "complex", "outside", "substitution")):
        return "advanced"
    if any(term in lowered for term in ("intermediate", "connect", "harmonized", "turnaround")):
        return "intermediate"
    if any(term in lowered for term in ("beginner", "basic", "intro", "start", "simple")):
        return "beginner"
    return "unknown"


def quality_flags_for_row(row: dict[str, Any], body: str) -> list[str]:
    flags: list[str] = []
    lowered = body.lower()
    if "the player should" in lowered:
        flags.append("contains_player_should_phrase")
    if re.search(r"\b(?:webvtt|\d{1,2}:\d{2}(?::\d{2})?[,.]\d{3}\s+-->|^speaker\s*\d*:)", body, re.I | re.M):
        flags.append("possible_transcript_residue")
    if re.search(r"\b(?:i'm going to show|i want you to|my students|in this lesson i|let me show you)\b", lowered):
        flags.append("first_person_instructor_phrasing")
    if not row["title"] or row["title"] == "Untitled":
        flags.append("missing_title")
    if not row["topics"]:
        flags.append("missing_topic_tags")
    if row["word_count"] < 100:
        flags.append("body_under_100_words")
    if row["word_count"] > 2500:
        flags.append("body_over_reasonable_chunk_size")
    if row["visibility"] != "private_review" or row["needs_review"] is not True:
        flags.append("unclear_rights_visibility")
    if not any(term in lowered for term in STEEL_TERMS):
        flags.append("no_steel_specific_terms")
    return sorted(set(flags))


def build_row(path: Path, source_root: Path) -> dict[str, Any]:
    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    source_sha256 = sha256_text(raw_text)
    normalized = normalize_markdown(raw_text)
    metadata, body = split_frontmatter(normalized)
    body = normalize_markdown(body)
    text_for_inference = f"{path.as_posix()}\n{body}"
    row: dict[str, Any] = {
        "content_layer": "curated_guidance",
        "visibility": "private_review",
        "source_path": path.relative_to(source_root).as_posix(),
        "source_filename": path.name,
        "source_sha256": source_sha256,
        "title": extract_title(path, source_root, metadata, body),
        "body": body,
        "word_count": word_count(body),
        "topics": infer_topics(metadata, text_for_inference),
        "technique_tags": infer_technique_tags(metadata, text_for_inference),
        "instrument": infer_instrument(text_for_inference),
        "strings": extract_strings(text_for_inference),
        "pedals_levers": extract_pedals_levers(text_for_inference),
        "frets": extract_frets(text_for_inference),
        "keys": extract_keys(text_for_inference),
        "difficulty": infer_difficulty(metadata, text_for_inference),
        "needs_review": True,
        "quality_flags": [],
    }
    row["quality_flags"] = quality_flags_for_row(row, body)
    return row


def write_jsonl(rows: Iterable[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def render_private_inventory(rows: list[dict[str, Any]], source_root: Path) -> str:
    quality_counts = Counter(flag for row in rows for flag in row["quality_flags"])
    instrument_counts = Counter(str(row["instrument"]) for row in rows)
    lines = [
        "# Curated Guidance Full Inventory",
        "",
        "Private/local inventory for curated guidance markdown summaries. Do not commit generated corpus-private reports.",
        "",
        f"- Source root: `{source_root.as_posix()}`",
        f"- Markdown files processed: {len(rows)}",
        "",
        "## Instrument Counts",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in sorted(instrument_counts.items()))
    lines.extend(["", "## Quality Flag Counts", ""])
    if quality_counts:
        lines.extend(f"- `{key}`: {value}" for key, value in sorted(quality_counts.items()))
    else:
        lines.append("- None")
    lines.extend(["", "## Files", ""])
    for row in rows:
        flags = ", ".join(row["quality_flags"]) if row["quality_flags"] else "none"
        lines.append(f"- `{row['source_path']}` | title: `{row['title']}` | words: {row['word_count']} | flags: {flags}")
    return "\n".join(lines) + "\n"


def build_corpus(source_root: Path, output_path: Path, inventory_path: Path) -> BuildResult:
    files = markdown_files(source_root)
    rows = [build_row(path, source_root) for path in files]
    write_jsonl(rows, output_path)
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text(render_private_inventory(rows, source_root), encoding="utf-8")
    return BuildResult(
        source_root=source_root,
        output_path=output_path,
        inventory_path=inventory_path,
        files_found=len(files),
        files_processed=len(rows),
        files_skipped=len(files) - len(rows),
        quality_counts=Counter(flag for row in rows for flag in row["quality_flags"]),
        instrument_counts=Counter(str(row["instrument"]) for row in rows),
    )


def main() -> int:
    args = parse_args()
    source_root = resolve_source_root(args.source)
    result = build_corpus(source_root, Path(args.output), Path(args.inventory_report))
    print(f"Found {result.files_found} markdown file(s).")
    print(f"Processed {result.files_processed} curated guidance row(s).")
    print(f"Skipped {result.files_skipped} file(s).")
    print(f"Wrote JSONL: {result.output_path}")
    print(f"Wrote private inventory: {result.inventory_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
