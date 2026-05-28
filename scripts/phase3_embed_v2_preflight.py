#!/usr/bin/env python3
"""Preflight corpus-v2 chunks before any embedding or Chroma creation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.phase3_clean_classify_chunks import as_list, word_count


V1_CHUNKS_PATH = Path("/Users/cory/Documents/sgf-scrape-test/corpus-unified/chunks.jsonl")
V1_CHROMA_PATH = Path("/Users/cory/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma")
V1_UNIFIED_ROOT = Path("/Users/cory/Documents/sgf-scrape-test/corpus-unified")

REQUIRED_CHUNK_FIELDS = (
    "chunk_id",
    "source_system",
    "forum_name",
    "thread_id",
    "thread_title",
    "chunk_text",
    "chunk_role",
    "quality_score",
    "noise_score",
    "cleanup_flags",
    "source_metadata_complete",
)

CONTACT_LEAK_RE = re.compile(
    r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b|"
    r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}|"
    r"\b(?:e-?mail\s+me|call\s+me|contact\s+me|send\s+me\s+(?:an?\s+)?(?:email|pm))\b",
    re.IGNORECASE,
)
URL_RE = re.compile(r"https?://\S+|www\.\S+|\bclick here\b", re.IGNORECASE)
SIGNATURE_SEPARATOR_RE = re.compile(r"(?:-{5,}|_{5,}|={5,})")
GEAR_RE = re.compile(
    r"\b(?:D-?10|SD-?10|S-?10|U-?12|Zum(?:Steel)?|Emmons|Sho-?Bud|Mullen|MSA|Carter|GFI|Sierra|"
    r"Williams|Franklin|Derby|Fessenden|MCI|BMI|Excel|Peavey|Nashville\s*(?:400|112|1000)|Session\s*400|"
    r"Webb|Evans|Telonics|Goodrich|Hilton|Sarno|Black Box|Steel King|Profex|NV\s*112|pickup|volume pedal)\b",
    re.IGNORECASE,
)
SIGNATURE_ANCHOR_RE = re.compile(
    r"\b[A-Z][A-Za-z.'~-]+(?:\s+[A-Z][A-Za-z.'~-]+){1,3}\s+"
    r"(?=(?:D-?10|SD-?10|S-?10|U-?12|Zum(?:Steel)?|Emmons|Sho-?Bud|Mullen|MSA|Carter|GFI|Sierra|"
    r"Williams|Franklin|Derby|Fessenden|MCI|BMI|Excel|Rittenberry|Peavey|Nashville|Session|Webb|"
    r"Evans|Telonics|Goodrich|Hilton|Steel King)\b)"
)
AUTHOR_DATE_RE = re.compile(
    r"\b[A-Z][A-Za-z.'~-]+(?:\s+[A-Z][A-Za-z.'~-]+){0,3}\s*/\s+"
    r"\d{1,2}\s+[A-Z][a-z]+\s+\d{4}\s+\d{1,2}:\d{2}\s+(?:am|pm)\b"
)


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


def resolved(path: Path) -> Path:
    return path.expanduser().resolve()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def source_url(record: Mapping[str, Any]) -> str:
    return str(record.get("source_url") or record.get("thread_url") or "")


def has_source_metadata(record: Mapping[str, Any]) -> bool:
    if record.get("source_metadata_complete") is False:
        return False
    required_present = all(field in record for field in REQUIRED_CHUNK_FIELDS)
    required_present = required_present and all(
        bool(record.get(field))
        for field in ("chunk_id", "source_system", "forum_name", "thread_id", "thread_title", "chunk_text", "chunk_role")
    )
    return required_present and bool(source_url(record))


def has_post_identity(record: Mapping[str, Any]) -> bool:
    return bool(record.get("post_uid") or as_list(record.get("post_uids")))


def numeric_field(record: Mapping[str, Any], field: str) -> float:
    try:
        return float(record.get(field) or 0)
    except (TypeError, ValueError):
        return 0.0


def percentile(values: list[int], fraction: float) -> int:
    if not values:
        return 0
    index = min(len(values) - 1, max(0, round((len(values) - 1) * fraction)))
    return values[index]


def chunk_length_distribution(chunks: list[Mapping[str, Any]]) -> dict[str, float | int]:
    lengths = sorted(word_count(str(chunk.get("chunk_text") or "")) for chunk in chunks)
    if not lengths:
        return {"min": 0, "p50": 0, "p95": 0, "max": 0, "avg": 0.0}
    return {
        "min": lengths[0],
        "p50": percentile(lengths, 0.50),
        "p95": percentile(lengths, 0.95),
        "max": lengths[-1],
        "avg": round(sum(lengths) / len(lengths), 1),
    }


def noise_buckets(chunks: list[Mapping[str, Any]]) -> dict[str, int]:
    buckets = Counter()
    for chunk in chunks:
        noise = numeric_field(chunk, "noise_score")
        if noise <= 0.20:
            buckets["0.00-0.20"] += 1
        elif noise <= 0.40:
            buckets["0.21-0.40"] += 1
        elif noise <= 0.60:
            buckets["0.41-0.60"] += 1
        elif noise <= 0.80:
            buckets["0.61-0.80"] += 1
        else:
            buckets["0.81-1.00"] += 1
    return dict(sorted(buckets.items()))


def looks_link_only(text: str) -> bool:
    words = word_count(text)
    urls = len(URL_RE.findall(text))
    return bool(urls and (words <= 25 or urls / max(words, 1) > 0.08))


def looks_signature_like(text: str) -> bool:
    words = text.split()
    tail = " ".join(words[-60:])
    separator = SIGNATURE_SEPARATOR_RE.search(tail)
    if separator:
        after_separator = tail[separator.end() :]
        if word_count(after_separator) <= 80 and len(GEAR_RE.findall(after_separator)) >= 1:
            return True
    for match in SIGNATURE_ANCHOR_RE.finditer(tail):
        next_author = AUTHOR_DATE_RE.search(tail, match.end())
        end = next_author.start() if next_author else len(tail)
        candidate = tail[match.start() : end]
        list_like = candidate.count(",") >= 2 or bool(re.search(r"\b(?:my rig|gear|equipment)\s*:", candidate, re.I))
        sentence_count = len(re.findall(r"[.!?]", candidate))
        if list_like and sentence_count <= 2 and len(GEAR_RE.findall(candidate)) >= 3 and not re.search(
            r"\b(?:check|try|because|adjust|replace|use|recommend|problem|issue|sounds?)\b",
            candidate,
            re.IGNORECASE,
        ):
            return True
    return False


def leakage_counts(chunks: list[Mapping[str, Any]]) -> dict[str, int]:
    contact = signature = link_only = 0
    for chunk in chunks:
        text = str(chunk.get("chunk_text") or "")
        role = str(chunk.get("chunk_role") or "")
        if CONTACT_LEAK_RE.search(text):
            contact += 1
        if looks_signature_like(text) or role == "gear_signature":
            signature += 1
        if role == "link_only" or looks_link_only(text):
            link_only += 1
    return {
        "contact": contact,
        "signature": signature,
        "link_only": link_only,
        "total": contact + signature + link_only,
    }


def top_cleanup_flags(chunks: list[Mapping[str, Any]], limit: int = 15) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for chunk in chunks:
        counts.update(str(flag) for flag in as_list(chunk.get("cleanup_flags")))
    return dict(counts.most_common(limit))


def path_checks(chunk_input: Path, target_chroma_path: Path, planned_output_path: Path | None) -> list[str]:
    failures: list[str] = []
    chunk_input_resolved = resolved(chunk_input)
    target_resolved = resolved(target_chroma_path)
    output_resolved = resolved(planned_output_path) if planned_output_path else None
    v1_chunks = resolved(V1_CHUNKS_PATH)
    v1_chroma = resolved(V1_CHROMA_PATH)
    v1_root = resolved(V1_UNIFIED_ROOT)

    if target_resolved == v1_chroma or is_relative_to(target_resolved, v1_chroma):
        failures.append("target Chroma path points at or inside v1 Chroma")
    if is_relative_to(target_resolved, v1_root):
        failures.append("target Chroma path appears to be under the v1 corpus-unified tree")
    if output_resolved and output_resolved == v1_chunks:
        failures.append("planned chunk output path would overwrite corpus-unified/chunks.jsonl")
    if output_resolved and is_relative_to(output_resolved, v1_root):
        failures.append("planned output path appears to be under the v1 corpus-unified tree")
    if chunk_input_resolved == v1_chunks:
        failures.append("chunk input is the production v1 chunks.jsonl, not a corpus-v2 candidate")
    return failures


def evaluate_preflight(
    *,
    chunk_input: Path,
    clean_input: Path | None = None,
    target_chroma_path: Path,
    planned_output_path: Path | None = None,
    metadata_threshold: float = 0.99,
    post_identity_threshold: float = 0.99,
    max_leakage_rate: float = 0.005,
    max_mixed_topic_rate: float = 0.05,
    max_avg_noise_score: float = 0.60,
) -> dict[str, Any]:
    chunks = list(iter_jsonl(chunk_input))
    clean_records = list(iter_jsonl(clean_input)) if clean_input else []
    total_chunks = len(chunks)
    role_counts = Counter(str(chunk.get("chunk_role") or "unknown") for chunk in chunks)
    flag_counts = top_cleanup_flags(chunks)
    leak_counts = leakage_counts(chunks)
    metadata_complete = sum(1 for chunk in chunks if has_source_metadata(chunk))
    post_identity_complete = sum(1 for chunk in chunks if has_post_identity(chunk))
    mixed_topic_quarantined = sum(
        1 for chunk in chunks if "mixed_topic_quarantined" in as_list(chunk.get("cleanup_flags"))
    )
    avg_quality = round(sum(numeric_field(chunk, "quality_score") for chunk in chunks) / max(total_chunks, 1), 3)
    avg_noise = round(sum(numeric_field(chunk, "noise_score") for chunk in chunks) / max(total_chunks, 1), 3)

    metadata_rate = metadata_complete / max(total_chunks, 1)
    post_identity_rate = post_identity_complete / max(total_chunks, 1)
    leakage_rate = leak_counts["total"] / max(total_chunks, 1)
    mixed_topic_rate = mixed_topic_quarantined / max(total_chunks, 1)

    failures = path_checks(chunk_input, target_chroma_path, planned_output_path)
    if total_chunks == 0:
        failures.append("chunk input contains zero chunks")
    if metadata_rate < metadata_threshold:
        failures.append(
            f"metadata completeness {metadata_rate:.3f} is below threshold {metadata_threshold:.3f}"
        )
    if post_identity_rate < post_identity_threshold:
        failures.append(
            f"post identity completeness {post_identity_rate:.3f} is below threshold {post_identity_threshold:.3f}"
        )
    if leakage_rate > max_leakage_rate:
        failures.append(f"leakage rate {leakage_rate:.3f} exceeds threshold {max_leakage_rate:.3f}")
    if mixed_topic_rate > max_mixed_topic_rate:
        failures.append(
            f"mixed-topic quarantine rate {mixed_topic_rate:.3f} exceeds threshold {max_mixed_topic_rate:.3f}"
        )
    if avg_noise > max_avg_noise_score:
        failures.append(f"average noise_score {avg_noise:.3f} exceeds threshold {max_avg_noise_score:.3f}")

    return {
        "passed": not failures,
        "failures": failures,
        "inputs": {
            "clean_input": str(clean_input) if clean_input else "",
            "chunk_input": str(chunk_input),
            "target_chroma_path": str(target_chroma_path),
            "planned_output_path": str(planned_output_path) if planned_output_path else "",
        },
        "total_records": len(clean_records) if clean_input else total_chunks,
        "total_chunks": total_chunks,
        "role_distribution": dict(sorted(role_counts.items())),
        "average_quality_score": avg_quality,
        "average_noise_score": avg_noise,
        "noise_buckets": noise_buckets(chunks),
        "source_metadata_complete": metadata_complete,
        "source_metadata_completeness_rate": round(metadata_rate, 3),
        "post_identity_complete": post_identity_complete,
        "post_identity_completeness_rate": round(post_identity_rate, 3),
        "leakage_counts": leak_counts,
        "leakage_rate": round(leakage_rate, 3),
        "question_only_chunk_count": role_counts.get("question", 0),
        "answer_advice_chunk_count": role_counts.get("answer_advice", 0),
        "mixed_topic_quarantined_count": mixed_topic_quarantined,
        "mixed_topic_quarantined_rate": round(mixed_topic_rate, 3),
        "chunk_length_distribution": chunk_length_distribution(chunks),
        "top_cleanup_flags": flag_counts,
        "path_safety": {"safe_outside_v1_paths": not path_checks(chunk_input, target_chroma_path, planned_output_path)},
        "embedding_commands_executed": False,
    }


def markdown_table(mapping: Mapping[str, Any], key_label: str, value_label: str) -> list[str]:
    lines = [f"| {key_label} | {value_label} |", "| --- | ---: |"]
    for key, value in mapping.items():
        lines.append(f"| `{key}` | {value} |")
    return lines


def markdown_report(result: Mapping[str, Any]) -> str:
    status = "PASS" if result["passed"] else "FAIL"
    lines = [
        "# Phase 3D Embed V2 Preflight Report",
        "",
        f"Status: `{status}`",
        "",
        "This report is preflight-only. It does not run embeddings and does not create or modify Chroma stores.",
        "",
        "## Inputs",
        "",
    ]
    for key, value in dict(result["inputs"]).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Total records: `{result['total_records']}`",
            f"- Total chunks: `{result['total_chunks']}`",
            f"- Average quality score: `{result['average_quality_score']}`",
            f"- Average noise score: `{result['average_noise_score']}`",
            f"- Source metadata completeness: `{result['source_metadata_complete']}/{result['total_chunks']}` "
            f"(`{result['source_metadata_completeness_rate']}`)",
            f"- Post identity completeness: `{result['post_identity_complete']}/{result['total_chunks']}` "
            f"(`{result['post_identity_completeness_rate']}`)",
            f"- Contact/signature/link-only leakage: `{result['leakage_counts']['total']}` "
            f"(`{result['leakage_rate']}`)",
            f"- Question-only chunks: `{result['question_only_chunk_count']}`",
            f"- Answer/advice chunks: `{result['answer_advice_chunk_count']}`",
            f"- Mixed-topic quarantined chunks: `{result['mixed_topic_quarantined_count']}` "
            f"(`{result['mixed_topic_quarantined_rate']}`)",
            f"- Safe outside v1 paths: `{result['path_safety']['safe_outside_v1_paths']}`",
            f"- Embedding commands executed: `{result['embedding_commands_executed']}`",
            "",
            "## Failures",
            "",
        ]
    )
    if result["failures"]:
        lines.extend(f"- {failure}" for failure in result["failures"])
    else:
        lines.append("- None")
    lines.extend(["", "## Role Distribution"])
    lines.extend(markdown_table(dict(result["role_distribution"]), "role", "count"))
    lines.extend(["", "## Noise Buckets"])
    lines.extend(markdown_table(dict(result["noise_buckets"]), "noise bucket", "count"))
    lines.extend(["", "## Chunk Length Distribution", ""])
    for key, value in dict(result["chunk_length_distribution"]).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Top Cleanup Flags"])
    lines.extend(markdown_table(dict(result["top_cleanup_flags"]), "flag", "count"))
    lines.extend(["", "## Current V1 Chroma Statement", ""])
    lines.append(
        "No embeddings were run, no v2 Chroma store was created, and the current v1 Chroma store was not modified."
    )
    lines.append("")
    return "\n".join(lines)


def bounded_rate(value: str) -> float:
    parsed = float(value)
    if parsed < 0 or parsed > 1:
        raise argparse.ArgumentTypeError("rate thresholds must be between 0 and 1")
    return parsed


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunk-input", required=True, type=Path, help="Candidate chunk-v2 JSONL to inspect.")
    parser.add_argument("--clean-input", type=Path, help="Optional cleaned/classified JSONL for total record count.")
    parser.add_argument("--target-chroma-path", required=True, type=Path, help="Planned v2 Chroma output path.")
    parser.add_argument("--planned-output-path", type=Path, help="Planned chunk-v2 output path.")
    parser.add_argument("--report", type=Path, help="Optional Markdown report path.")
    parser.add_argument("--json-report", type=Path, help="Optional JSON report path.")
    parser.add_argument("--metadata-threshold", type=bounded_rate, default=0.99)
    parser.add_argument("--post-identity-threshold", type=bounded_rate, default=0.99)
    parser.add_argument("--max-leakage-rate", type=bounded_rate, default=0.005)
    parser.add_argument("--max-mixed-topic-rate", type=bounded_rate, default=0.05)
    parser.add_argument("--max-avg-noise-score", type=bounded_rate, default=0.60)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    result = evaluate_preflight(
        chunk_input=args.chunk_input,
        clean_input=args.clean_input,
        target_chroma_path=args.target_chroma_path,
        planned_output_path=args.planned_output_path,
        metadata_threshold=args.metadata_threshold,
        post_identity_threshold=args.post_identity_threshold,
        max_leakage_rate=args.max_leakage_rate,
        max_mixed_topic_rate=args.max_mixed_topic_rate,
        max_avg_noise_score=args.max_avg_noise_score,
    )
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(markdown_report(result), encoding="utf-8")
    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
