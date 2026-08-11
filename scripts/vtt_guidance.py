#!/usr/bin/env python3
"""Build, review, index, inspect, or purge isolated VTT guidance artifacts.

Raw sources are read-only. Every output stays beneath the ignored
``corpus-private/vtt-guidance-v2`` root unless an explicit test path is used.
No hosted model or embedding endpoint is supported.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from steel_guitar_rag.vtt_guidance import (
    BUILD_VERSION,
    DEFAULT_APPROVED_CARDS,
    DEFAULT_INDEX,
    DEFAULT_ROOT,
    SCHEMA_VERSION,
    VttGuidanceError,
    build_fts_index,
    canonical_json,
    card_renderable_text,
    evaluate_index,
    privacy_findings,
    sha256_file,
    stable_id,
    validate_card,
    validate_technical_anchors,
    write_jsonl,
)


SOURCE_ROOT = Path.home() / "Documents/vtt-test"
RECORDS_PATH = SOURCE_ROOT / "guidance-cleaned/full-draft/records.jsonl"
SUMMARY_ROOT = SOURCE_ROOT / "guidance-cleaned/summary-draft"
DEFAULT_MANIFEST = DEFAULT_ROOT / "manifest/structured-62.jsonl"
DEFAULT_CANDIDATES = DEFAULT_ROOT / "candidates/cards.jsonl"
DEFAULT_REVIEW_QUEUE = DEFAULT_ROOT / "review/review-queue.jsonl"
DEFAULT_DECISIONS_TEMPLATE = DEFAULT_ROOT / "review/decisions-template.jsonl"
DEFAULT_GENERATION_REPORT = DEFAULT_ROOT / "reports/generation-report.json"
DEFAULT_CORPUS_AUDIT_REPORT = DEFAULT_ROOT / "reports/corpus-audit.json"
DEFAULT_APPROVAL_REPORT = DEFAULT_ROOT / "reports/approval-report.json"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
GENERATION_MODEL = os.environ.get("VTT_GUIDANCE_GENERATION_MODEL", "qwen3.5:27b")
PRIVACY_MODEL = os.environ.get("VTT_GUIDANCE_PRIVACY_MODEL", "gemma4:12b")
EXPECTED_MANIFEST_COUNT = 62
PURGE_CONFIRMATION = "DELETE-VTT-GUIDANCE-V2"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare-manifest", help="Create the exact 62-record private manifest.")
    prepare.add_argument("--records", type=Path, default=RECORDS_PATH)
    prepare.add_argument("--summary-root", type=Path, default=SUMMARY_ROOT)
    prepare.add_argument("--output", type=Path, default=DEFAULT_MANIFEST)

    generate = sub.add_parser("generate", help="Generate local-model candidate cards and privacy reviews.")
    generate.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    generate.add_argument("--output", type=Path, default=DEFAULT_CANDIDATES)
    generate.add_argument("--review-queue", type=Path, default=DEFAULT_REVIEW_QUEUE)
    generate.add_argument("--decisions-template", type=Path, default=DEFAULT_DECISIONS_TEMPLATE)
    generate.add_argument("--report", type=Path, default=DEFAULT_GENERATION_REPORT)
    generate.add_argument("--checkpoint-root", type=Path, default=DEFAULT_ROOT / "candidates/by-source")
    generate.add_argument("--limit", type=int)
    generate.add_argument("--regenerate", action="store_true")

    audit = sub.add_parser(
        "audit-corpus",
        help="Run metadata-only integrity, privacy, overlap, and eligibility gates.",
    )
    audit.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    audit.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    audit.add_argument("--checkpoint-root", type=Path, default=DEFAULT_ROOT / "candidates/by-source")
    audit.add_argument("--report", type=Path, default=DEFAULT_CORPUS_AUDIT_REPORT)

    approve = sub.add_parser("apply-review", help="Apply a complete human card-decision ledger.")
    approve.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    approve.add_argument("--decisions", type=Path, required=True)
    approve.add_argument("--output", type=Path, default=DEFAULT_APPROVED_CARDS)
    approve.add_argument("--report", type=Path, default=DEFAULT_APPROVAL_REPORT)

    index = sub.add_parser("build-index", help="Build the dedicated approved-card FTS5 index.")
    index.add_argument("--cards", type=Path, default=DEFAULT_APPROVED_CARDS)
    index.add_argument("--output", type=Path, default=DEFAULT_INDEX)

    evaluate = sub.add_parser("evaluate", help="Run the isolated FTS retrieval acceptance gates.")
    evaluate.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    evaluate.add_argument("--probes", type=Path, default=DEFAULT_ROOT / "review/retrieval-probes.jsonl")
    evaluate.add_argument("--report", type=Path, default=DEFAULT_ROOT / "reports/retrieval-eval.json")

    status = sub.add_parser("status", help="Show metadata-only artifact status.")
    status.add_argument("--root", type=Path, default=DEFAULT_ROOT)

    purge = sub.add_parser("purge", help="Dry-run or explicitly delete the isolated derived artifact root.")
    purge.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    purge.add_argument("--confirm", default="")

    return parser.parse_args(argv)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise VttGuidanceError(f"{path.name}:{line_number} must contain an object")
            rows.append(value)
    return rows


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _summary_index(summary_root: Path) -> dict[str, list[Path]]:
    by_key: dict[str, list[Path]] = defaultdict(list)
    for path in summary_root.rglob("*.md"):
        if path.name.lower().startswith("readme") or "superseded" in path.name.lower():
            continue
        for key in {_slug(path.parent.name), _slug(path.stem)}:
            by_key[key].append(path)
    return by_key


def prepare_manifest(records_path: Path, summary_root: Path, output_path: Path) -> dict[str, object]:
    if not records_path.is_file() or not summary_root.is_dir():
        raise VttGuidanceError("vtt-test records or summary root is missing")
    records = read_jsonl(records_path)
    summaries = _summary_index(summary_root)
    manifest: list[dict[str, object]] = []
    for record in records:
        if record.get("candidate_status") != "candidate_after_human_review":
            continue
        if record.get("corpus_class") != "structured_lesson":
            continue
        if record.get("privacy_action") != "converted" or record.get("licensing_action") != "low_risk":
            continue
        if sum(int(value) for value in (record.get("guidance_risk_counts") or {}).values()) != 0:
            continue
        source_path = Path(str(record.get("source_path") or ""))
        guidance_path = Path(str((record.get("outputs") or {}).get("guidance_draft") or ""))
        if not source_path.is_file() or not guidance_path.is_file():
            continue
        keys = {
            _slug(str(record.get("source_title") or "")),
            _slug(source_path.stem).removesuffix("-clean"),
        }
        found: list[Path] = []
        for key in keys:
            found.extend(summaries.get(key, []))
        found = list(dict.fromkeys(found))
        if len(found) != 1:
            continue
        source_relpath = str(record.get("source_relpath") or "")
        source_id = stable_id("vtt-source-v2", source_relpath)[:24]
        manifest.append(
            {
                "schema_version": "vtt_guidance_manifest_v2",
                "source_id": source_id,
                "source_path": source_path.as_posix(),
                "source_relpath": source_relpath,
                "source_sha256": sha256_file(source_path),
                "guidance_path": guidance_path.as_posix(),
                "guidance_sha256": sha256_file(guidance_path),
                "overview_path": found[0].as_posix(),
                "overview_sha256": sha256_file(found[0]),
                "corpus_class": record["corpus_class"],
                "privacy_action": record["privacy_action"],
                "licensing_action": record["licensing_action"],
                "candidate_status": record["candidate_status"],
                "approved_for_generation": True,
                "allowed_for_embedding": False,
                "answer_quote_allowed": False,
            }
        )
    manifest.sort(key=lambda row: str(row["source_id"]))
    if len(manifest) != EXPECTED_MANIFEST_COUNT:
        raise VttGuidanceError(
            f"manifest must contain exactly {EXPECTED_MANIFEST_COUNT} records; found {len(manifest)}"
        )
    if len({str(row["source_id"]) for row in manifest}) != len(manifest):
        raise VttGuidanceError("manifest contains duplicate source IDs")
    write_jsonl(output_path, manifest)
    return {
        "manifest_count": len(manifest),
        "manifest_sha256": sha256_file(output_path),
        "output": output_path.as_posix(),
    }


def _ollama_models() -> dict[str, str]:
    request = urllib.request.Request(f"{OLLAMA_URL}/api/tags", headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise VttGuidanceError("local Ollama is unavailable") from exc
    return {
        str(model.get("name") or ""): str(model.get("digest") or "")
        for model in payload.get("models") or []
    }


def _local_json(
    model: str,
    system: str,
    user: str,
    *,
    json_schema: Mapping[str, object] | None = None,
    timeout: int = 600,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "format": json_schema or "json",
        "stream": False,
        "think": False,
        "options": {"temperature": 0, "seed": 17, "num_predict": 2_048},
    }
    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise VttGuidanceError(f"local model {model} failed") from exc
    content = str((body.get("message") or {}).get("content") or "")
    try:
        value = json.loads(content)
    except json.JSONDecodeError as exc:
        raise VttGuidanceError(f"local model {model} returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise VttGuidanceError(f"local model {model} returned a non-object")
    return value


GENERATION_SYSTEM = """You transform privacy-cleaned steel-guitar lesson guidance into compact, reusable teaching cards.
Never include people, brands, lesson titles, course/platform references, URLs, locations, personal stories, requester framing, or direct quotations.
Paraphrase. Preserve concrete strings, frets, pedals, levers, grips, harmonic functions, setup, procedure, mistakes, and transfer only when supported.
Do not invent notes, pitches, positions, or copedent behavior. Use instrument E9, C6, non_pedal, general, or unknown.
Return JSON only with: instrument and cards. cards must contain 2-4 objects with card_type, concept, setup, procedure, common_mistakes, transfer, and technical_anchors.
card_type must be overview, concept, setup, procedure, common_mistake, or transfer.
technical_anchors must contain arrays: strings, frets, pedals, levers, grips, keys, chord_functions, techniques.
Use named technical anchors only when the same term appears in the detailed guidance; otherwise leave that anchor array empty.
Include exactly one overview card, then select the most useful source-specific details. Keep every sentence instructional, attribution-free, and at most 22 words.
Use no more than two setup items, three procedure steps, one common mistake, and one transfer item per card."""

GENERATION_JSON_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["instrument", "cards"],
    "properties": {
        "instrument": {
            "type": "string",
            "enum": ["E9", "C6", "non_pedal", "general", "unknown"],
        },
        "cards": {
            "type": "array",
            "minItems": 2,
            "maxItems": 4,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "card_type",
                    "concept",
                    "setup",
                    "procedure",
                    "common_mistakes",
                    "transfer",
                    "technical_anchors",
                ],
                "properties": {
                    "card_type": {
                        "type": "string",
                        "enum": [
                            "overview",
                            "concept",
                            "setup",
                            "procedure",
                            "common_mistake",
                            "transfer",
                        ],
                    },
                    "concept": {"type": "string"},
                    "setup": {"type": "array", "maxItems": 2, "items": {"type": "string"}},
                    "procedure": {"type": "array", "maxItems": 3, "items": {"type": "string"}},
                    "common_mistakes": {
                        "type": "array",
                        "maxItems": 1,
                        "items": {"type": "string"},
                    },
                    "transfer": {"type": "array", "maxItems": 1, "items": {"type": "string"}},
                    "technical_anchors": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "strings",
                            "frets",
                            "pedals",
                            "levers",
                            "grips",
                            "keys",
                            "chord_functions",
                            "techniques",
                        ],
                        "properties": {
                            field: {
                                "type": "array",
                                "maxItems": 12,
                                "items": {"type": "string"},
                            }
                            for field in (
                                "strings",
                                "frets",
                                "pedals",
                                "levers",
                                "grips",
                                "keys",
                                "chord_functions",
                                "techniques",
                            )
                        },
                    },
                },
            },
        },
    },
}

PRIVACY_SYSTEM = """You are a strict privacy and transformation reviewer for private steel-guitar teaching cards.
Reject any person, brand, title, platform, membership/request framing, location, contact data, personal anecdote, transcript voice, direct quotation, or invented technical claim.
Return JSON only: {"approved": boolean, "findings": [short machine-readable labels]}.
Do not repeat private text in findings."""


def _bounded_source(text: str, *, limit: int = 45_000) -> str:
    value = text.strip()
    if len(value) <= limit:
        return value
    return value[:22_000] + "\n\n[private source middle omitted for model context bound]\n\n" + value[-22_000:]


def _normalize_anchor_map(value: object) -> dict[str, list[object]]:
    source = value if isinstance(value, dict) else {}
    result: dict[str, list[object]] = {}
    for field in (
        "strings",
        "frets",
        "pedals",
        "levers",
        "grips",
        "keys",
        "chord_functions",
        "techniques",
    ):
        raw = source.get(field) or []
        result[field] = list(raw)[:16] if isinstance(raw, list) else []
    return result


def _clean_string_list(value: object, *, limit: int = 8) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned = [" ".join(str(item).split()) for item in value]
    return [item for item in cleaned if item][:limit]


def _make_cards(
    manifest: Mapping[str, object],
    generated: Mapping[str, object],
    *,
    generation_digest: str,
    privacy_digest: str,
) -> list[dict[str, object]]:
    source_id = str(manifest["source_id"])
    source_sha256 = str(manifest["guidance_sha256"])
    instrument = str(generated.get("instrument") or "unknown")
    raw_cards = generated.get("cards")
    if not isinstance(raw_cards, list) or not raw_cards:
        raise VttGuidanceError("generation returned no cards")
    overview_indexes = [index for index, card in enumerate(raw_cards) if isinstance(card, dict) and card.get("card_type") == "overview"]
    if len(overview_indexes) != 1:
        raise VttGuidanceError("generation must return exactly one overview card")
    parent_id = stable_id(source_id, "overview", 0)[:24]
    cards: list[dict[str, object]] = []
    for ordinal, raw in enumerate(raw_cards[:4]):
        if not isinstance(raw, dict):
            continue
        card_type = str(raw.get("card_type") or "")
        card_id = parent_id if card_type == "overview" else stable_id(source_id, card_type, ordinal)[:24]
        card: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "card_id": card_id,
            "source_id": source_id,
            "parent_overview_id": parent_id,
            "card_type": card_type,
            "instrument": instrument,
            "concept": " ".join(str(raw.get("concept") or "").split()),
            "setup": _clean_string_list(raw.get("setup")),
            "procedure": _clean_string_list(raw.get("procedure")),
            "common_mistakes": _clean_string_list(raw.get("common_mistakes")),
            "transfer": _clean_string_list(raw.get("transfer")),
            "technical_anchors": _normalize_anchor_map(raw.get("technical_anchors")),
            "source_sha256": source_sha256,
            "corpus_class": manifest["corpus_class"],
            "privacy_action": manifest["privacy_action"],
            "licensing_action": manifest["licensing_action"],
            "allowed_for_embedding": False,
            "answer_quote_allowed": False,
            "generation_model": GENERATION_MODEL,
            "generation_model_digest": generation_digest,
            "generator_version": BUILD_VERSION,
            "privacy_review_model": PRIVACY_MODEL,
            "privacy_review_model_digest": privacy_digest,
            "privacy_review_status": "pending",
            "music_validation_status": "pending",
            "review_status": "pending_human_review",
            "human_approved": False,
        }
        cards.append(card)
    return cards


def _anchor_support_findings(card: Mapping[str, object], source: str) -> list[str]:
    lowered = source.lower()
    anchors = card.get("technical_anchors")
    if not isinstance(anchors, dict):
        return ["technical_anchors_not_object"]
    findings: list[str] = []
    for field in ("pedals", "levers", "grips", "keys"):
        for value in anchors.get(field) or []:
            normalized = str(value).strip().lower()
            variants = {normalized, normalized.replace("+", " and "), normalized.replace("-", " ")}
            if normalized and not any(variant in lowered for variant in variants):
                findings.append(f"unsupported_{field[:-1]}")
    return sorted(set(findings))


def _privacy_review(card: Mapping[str, object]) -> dict[str, object]:
    public_candidate = {
        key: card.get(key)
        for key in (
            "card_type",
            "instrument",
            "concept",
            "setup",
            "procedure",
            "common_mistakes",
            "transfer",
            "technical_anchors",
        )
    }
    result = _local_json(PRIVACY_MODEL, PRIVACY_SYSTEM, canonical_json(public_candidate))
    raw_findings = result.get("findings")
    findings: list[Any] = raw_findings if isinstance(raw_findings, list) else []
    return {
        "approved": result.get("approved") is True,
        "findings": [str(value)[:80] for value in findings[:20]],
    }


def generate_cards(
    manifest_path: Path,
    output_path: Path,
    review_queue_path: Path,
    decisions_template_path: Path,
    report_path: Path,
    checkpoint_root: Path,
    *,
    limit: int | None = None,
    regenerate: bool = False,
) -> dict[str, object]:
    models = _ollama_models()
    missing = [model for model in (GENERATION_MODEL, PRIVACY_MODEL) if model not in models]
    if missing:
        raise VttGuidanceError(f"required local model is missing: {', '.join(missing)}")
    manifest = read_jsonl(manifest_path)
    if len(manifest) != EXPECTED_MANIFEST_COUNT:
        raise VttGuidanceError("generation requires the exact 62-record manifest")
    selected = manifest[: max(0, limit)] if limit is not None else manifest
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    all_cards: list[dict[str, object]] = []
    source_status: Counter[str] = Counter()
    for item in selected:
        source_id = str(item["source_id"])
        checkpoint = checkpoint_root / f"{source_id}.json"
        source_path = Path(str(item["guidance_path"]))
        source_text = source_path.read_text(encoding="utf-8", errors="ignore")
        if sha256_file(source_path) != item.get("guidance_sha256"):
            raise VttGuidanceError("privacy-cleaned guidance hash changed")
        cards: list[dict[str, object]] = []
        if checkpoint.is_file() and not regenerate:
            payload = json.loads(checkpoint.read_text(encoding="utf-8"))
            if payload.get("guidance_sha256") == item.get("guidance_sha256"):
                raw_cards = payload.get("cards")
                if isinstance(raw_cards, list):
                    cards = [card for card in raw_cards if isinstance(card, dict)]
                current_digests = all(
                    card.get("generation_model_digest") == models[GENERATION_MODEL]
                    and card.get("privacy_review_model_digest") == models[PRIVACY_MODEL]
                    and card.get("generator_version") == BUILD_VERSION
                    for card in cards
                )
                if cards and current_digests:
                    source_status["resumed_and_revalidated"] += 1
                else:
                    cards = []
        if not cards:
            overview = Path(str(item["overview_path"])).read_text(encoding="utf-8", errors="ignore")
            user = (
                "Existing compact overview (use for topic orientation, not wording):\n"
                + _bounded_source(overview, limit=12_000)
                + "\n\nPrivacy-cleaned detailed guidance:\n"
                + _bounded_source(source_text)
            )
            generated = _local_json(
                GENERATION_MODEL,
                GENERATION_SYSTEM,
                user,
                json_schema=GENERATION_JSON_SCHEMA,
            )
            cards = _make_cards(
                item,
                generated,
                generation_digest=models[GENERATION_MODEL],
                privacy_digest=models[PRIVACY_MODEL],
            )
            source_status["generated"] += 1
        for card in cards:
            card["review_status"] = "pending_human_review"
            card["human_approved"] = False
            local_findings = validate_card(card, source_text=source_text)
            local_findings.extend(_anchor_support_findings(card, source_text))
            local_findings.extend(validate_technical_anchors(card.get("technical_anchors"), instrument=str(card["instrument"])))
            review = _privacy_review(card)
            raw_model_findings = review["findings"]
            model_findings = (
                [str(value) for value in raw_model_findings]
                if isinstance(raw_model_findings, list)
                else []
            )
            all_findings = sorted(set(local_findings + model_findings))
            card["privacy_review_status"] = "passed" if review["approved"] and not privacy_findings(card_renderable_text(card)) else "failed"
            card["music_validation_status"] = "passed" if not validate_technical_anchors(card.get("technical_anchors"), instrument=str(card["instrument"])) else "failed"
            card["automated_findings"] = all_findings
            if all_findings or card["privacy_review_status"] != "passed" or card["music_validation_status"] != "passed":
                card["review_status"] = "blocked_automated_review"
        checkpoint.write_text(
            json.dumps(
                {"source_id": source_id, "guidance_sha256": item["guidance_sha256"], "cards": cards},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        all_cards.extend(cards)
    all_cards.sort(key=lambda card: str(card.get("card_id") or ""))
    write_jsonl(output_path, all_cards)
    review_rows = [
        {
            "card_id": card["card_id"],
            "source_id": card["source_id"],
            "card_type": card["card_type"],
            "instrument": card["instrument"],
            "concept": card["concept"],
            "setup": card["setup"],
            "procedure": card["procedure"],
            "common_mistakes": card["common_mistakes"],
            "transfer": card["transfer"],
            "technical_anchors": card["technical_anchors"],
            "automated_findings": card.get("automated_findings") or [],
            "review_status": card["review_status"],
        }
        for card in all_cards
    ]
    write_jsonl(review_queue_path, review_rows)
    write_jsonl(
        decisions_template_path,
        (
            {"card_id": card["card_id"], "decision": "pending", "reviewer": ""}
            for card in all_cards
        ),
    )
    report = {
        "schema_version": "vtt_guidance_generation_report_v2",
        "manifest_count": len(manifest),
        "processed_source_count": len(selected),
        "partial_generation": len(selected) != len(manifest),
        "card_count": len(all_cards),
        "source_status": dict(source_status),
        "blocked_card_count": sum(card["review_status"] == "blocked_automated_review" for card in all_cards),
        "pending_human_review_count": sum(card["review_status"] == "pending_human_review" for card in all_cards),
        "generation_model": GENERATION_MODEL,
        "generation_model_digest": models[GENERATION_MODEL],
        "privacy_model": PRIVACY_MODEL,
        "privacy_model_digest": models[PRIVACY_MODEL],
        "hosted_calls": 0,
        "embeddings_created": 0,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def audit_corpus(
    manifest_path: Path,
    candidates_path: Path,
    checkpoint_root: Path,
    report_path: Path,
) -> dict[str, object]:
    """Audit generated candidates without returning private text or source metadata."""

    manifest = read_jsonl(manifest_path)
    candidates = read_jsonl(candidates_path)
    manifest_by_id = {str(item.get("source_id") or ""): item for item in manifest}
    manifest_ids = set(manifest_by_id)
    source_text_by_id: dict[str, str] = {}
    source_hash_mismatch_count = 0
    missing_source_file_count = 0
    manifest_policy_mismatch_count = 0
    for source_id, item in manifest_by_id.items():
        if (
            not source_id
            or item.get("approved_for_generation") is not True
            or item.get("candidate_status") != "candidate_after_human_review"
            or item.get("corpus_class") != "structured_lesson"
            or item.get("privacy_action") != "converted"
            or item.get("licensing_action") != "low_risk"
            or item.get("answer_quote_allowed") is not False
            or item.get("allowed_for_embedding") is not False
        ):
            manifest_policy_mismatch_count += 1
        for path_field, hash_field in (
            ("source_path", "source_sha256"),
            ("overview_path", "overview_sha256"),
            ("guidance_path", "guidance_sha256"),
        ):
            path = Path(str(item.get(path_field) or ""))
            if not path.is_file():
                missing_source_file_count += 1
                continue
            if sha256_file(path) != item.get(hash_field):
                source_hash_mismatch_count += 1
        guidance_path = Path(str(item.get("guidance_path") or ""))
        if guidance_path.is_file():
            source_text_by_id[source_id] = guidance_path.read_text(
                encoding="utf-8", errors="ignore"
            )

    card_ids = [str(card.get("card_id") or "") for card in candidates]
    card_sources = [str(card.get("source_id") or "") for card in candidates]
    overview_counts: Counter[str] = Counter(
        str(card.get("source_id") or "")
        for card in candidates
        if card.get("card_type") == "overview"
    )
    validation_findings: Counter[str] = Counter()
    source_reference_mismatch_count = 0
    for card in candidates:
        source_id = str(card.get("source_id") or "")
        manifest_item = manifest_by_id.get(source_id)
        source_text = source_text_by_id.get(source_id)
        for finding in validate_card(card, source_text=source_text):
            validation_findings[finding] += 1
        if (
            manifest_item is None
            or card.get("source_sha256") != manifest_item.get("guidance_sha256")
        ):
            source_reference_mismatch_count += 1

    checkpoint_files = sorted(checkpoint_root.glob("*.json")) if checkpoint_root.is_dir() else []
    checkpoint_cards: list[dict[str, object]] = []
    checkpoint_integrity_mismatch_count = 0
    for checkpoint in checkpoint_files:
        payload = json.loads(checkpoint.read_text(encoding="utf-8"))
        source_id = str(payload.get("source_id") or "")
        manifest_item = manifest_by_id.get(source_id)
        raw_cards = payload.get("cards")
        if (
            manifest_item is None
            or payload.get("guidance_sha256") != manifest_item.get("guidance_sha256")
            or not isinstance(raw_cards, list)
        ):
            checkpoint_integrity_mismatch_count += 1
            continue
        checkpoint_cards.extend(card for card in raw_cards if isinstance(card, dict))
    candidate_digest = canonical_json(sorted(candidates, key=lambda card: str(card.get("card_id") or "")))
    checkpoint_digest = canonical_json(
        sorted(checkpoint_cards, key=lambda card: str(card.get("card_id") or ""))
    )
    if candidate_digest != checkpoint_digest:
        checkpoint_integrity_mismatch_count += 1

    status_counts = Counter(str(card.get("review_status") or "") for card in candidates)
    instrument_counts = Counter(str(card.get("instrument") or "") for card in candidates)
    card_type_counts = Counter(str(card.get("card_type") or "") for card in candidates)
    privacy_status_counts = Counter(
        str(card.get("privacy_review_status") or "") for card in candidates
    )
    music_status_counts = Counter(
        str(card.get("music_validation_status") or "") for card in candidates
    )
    recorded_automated_findings: Counter[str] = Counter(
        str(finding)
        for card in candidates
        for finding in (card.get("automated_findings") or [])
    )
    pending_runtime_count = sum(
        card.get("review_status") == "pending_human_review"
        and card.get("instrument") in {"E9", "general"}
        for card in candidates
    )
    pending_offline_instrument_count = sum(
        card.get("review_status") == "pending_human_review"
        and card.get("instrument") not in {"E9", "general"}
        for card in candidates
    )
    blocked_consistency_mismatch_count = sum(
        (card.get("review_status") == "blocked_automated_review")
        != bool(
            card.get("automated_findings")
            or card.get("privacy_review_status") != "passed"
            or card.get("music_validation_status") != "passed"
        )
        for card in candidates
    )
    generator_version_mismatch_count = sum(
        card.get("generator_version") != BUILD_VERSION for card in candidates
    )
    quote_or_embedding_enabled_count = sum(
        card.get("answer_quote_allowed") is not False
        or card.get("allowed_for_embedding") is not False
        for card in candidates
    )
    manifest_shape_valid = (
        len(manifest) == EXPECTED_MANIFEST_COUNT
        and len(manifest_ids) == EXPECTED_MANIFEST_COUNT
        and "" not in manifest_ids
    )
    card_shape_valid = (
        len(set(card_ids)) == len(card_ids)
        and all(card_ids)
        and set(card_sources) == manifest_ids
        and set(overview_counts) == manifest_ids
        and all(count == 1 for count in overview_counts.values())
    )
    private_or_overlap_count = sum(
        count
        for finding, count in validation_findings.items()
        if finding in {
            "presenter_or_brand",
            "member_or_request",
            "contact_or_url",
            "platform_or_course",
            "private_path_or_filename",
            "source_ten_word_overlap",
        }
    )
    candidate_gate_passed = all(
        (
            manifest_shape_valid,
            card_shape_valid,
            len(checkpoint_files) == EXPECTED_MANIFEST_COUNT,
            missing_source_file_count == 0,
            source_hash_mismatch_count == 0,
            source_reference_mismatch_count == 0,
            manifest_policy_mismatch_count == 0,
            checkpoint_integrity_mismatch_count == 0,
            blocked_consistency_mismatch_count == 0,
            generator_version_mismatch_count == 0,
            quote_or_embedding_enabled_count == 0,
            private_or_overlap_count == 0,
            status_counts.get("approved", 0) == 0,
        )
    )
    report: dict[str, object] = {
        "schema_version": "vtt_guidance_corpus_audit_v2",
        "candidate_gate_passed": candidate_gate_passed,
        "runtime_gate_passed": False,
        "manifest_count": len(manifest),
        "manifest_policy_mismatch_count": manifest_policy_mismatch_count,
        "candidate_card_count": len(candidates),
        "candidate_source_count": len(set(card_sources)),
        "checkpoint_count": len(checkpoint_files),
        "pending_runtime_review_count": pending_runtime_count,
        "pending_offline_instrument_count": pending_offline_instrument_count,
        "review_status_counts": dict(sorted(status_counts.items())),
        "instrument_counts": dict(sorted(instrument_counts.items())),
        "card_type_counts": dict(sorted(card_type_counts.items())),
        "independent_validation_finding_counts": dict(sorted(validation_findings.items())),
        "recorded_automated_finding_counts": dict(sorted(recorded_automated_findings.items())),
        "privacy_review_status_counts": dict(sorted(privacy_status_counts.items())),
        "music_validation_status_counts": dict(sorted(music_status_counts.items())),
        "private_or_ten_word_overlap_count": private_or_overlap_count,
        "missing_source_file_count": missing_source_file_count,
        "source_hash_mismatch_count": source_hash_mismatch_count,
        "source_reference_mismatch_count": source_reference_mismatch_count,
        "checkpoint_integrity_mismatch_count": checkpoint_integrity_mismatch_count,
        "blocked_consistency_mismatch_count": blocked_consistency_mismatch_count,
        "generator_version_mismatch_count": generator_version_mismatch_count,
        "quote_or_embedding_enabled_count": quote_or_embedding_enabled_count,
        "generation_model_digest_count": len(
            {str(card.get("generation_model_digest") or "") for card in candidates}
        ),
        "privacy_model_digest_count": len(
            {str(card.get("privacy_review_model_digest") or "") for card in candidates}
        ),
        "approved_card_count": status_counts.get("approved", 0),
        "index_created": False,
        "embeddings_created": 0,
        "hosted_calls": 0,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def apply_review(candidates_path: Path, decisions_path: Path, output_path: Path, report_path: Path) -> dict[str, object]:
    candidates = read_jsonl(candidates_path)
    decisions = read_jsonl(decisions_path)
    candidate_ids = [str(card.get("card_id") or "") for card in candidates]
    if len(set(candidate_ids)) != len(candidate_ids) or any(not value for value in candidate_ids):
        raise VttGuidanceError("candidate cards must have unique non-empty card IDs")
    candidate_sources = {str(card.get("source_id") or "") for card in candidates}
    if len(candidate_sources) != EXPECTED_MANIFEST_COUNT or "" in candidate_sources:
        raise VttGuidanceError("human review requires candidates from all 62 manifest sources")
    overview_counts: Counter[str] = Counter(
        str(card["source_id"]) for card in candidates if card.get("card_type") == "overview"
    )
    if set(overview_counts) != candidate_sources or any(count != 1 for count in overview_counts.values()):
        raise VttGuidanceError("every candidate source requires exactly one overview card")
    by_id = {str(row.get("card_id") or ""): row for row in decisions}
    if len(decisions) != len(by_id) or set(by_id) != set(candidate_ids):
        raise VttGuidanceError("human decision ledger must contain every candidate card exactly once")
    approved: list[dict[str, object]] = []
    counts: Counter[str] = Counter()
    for candidate in candidates:
        card = dict(candidate)
        decision = by_id[str(card["card_id"])]
        value = str(decision.get("decision") or "").strip().lower()
        reviewer = str(decision.get("reviewer") or "").strip()
        if value not in {"approve", "reject"} or not reviewer:
            raise VttGuidanceError("every human decision must be approve/reject with a reviewer")
        counts[value] += 1
        if value == "reject":
            continue
        if card.get("review_status") == "blocked_automated_review":
            raise VttGuidanceError("automated-blocked cards cannot be human-approved without regeneration")
        card["review_status"] = "approved"
        card["human_approved"] = True
        card["human_reviewer"] = reviewer
        findings = validate_card(card, require_human_approval=True)
        if findings:
            raise VttGuidanceError(f"approved card failed final gate: {card['card_id']} {findings}")
        approved.append(card)
    if not approved:
        raise VttGuidanceError("human review approved no cards")
    write_jsonl(output_path, approved)
    report = {
        "schema_version": "vtt_guidance_approval_report_v2",
        "candidate_count": len(candidates),
        "approved_count": len(approved),
        "rejected_count": counts["reject"],
        "approved_source_count": len({str(card["source_id"]) for card in approved}),
        "approved_cards_sha256": sha256_file(output_path),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def status(root: Path) -> dict[str, object]:
    files = [path for path in root.rglob("*") if path.is_file()] if root.is_dir() else []
    manifest_path = root / "manifest/structured-62.jsonl"
    candidates_path = root / "candidates/cards.jsonl"
    approved_path = root / "approved/cards.jsonl"
    manifest = read_jsonl(manifest_path) if manifest_path.is_file() else []
    candidates = read_jsonl(candidates_path) if candidates_path.is_file() else []
    approved = read_jsonl(approved_path) if approved_path.is_file() else []
    return {
        "root_exists": root.is_dir(),
        "file_count": len(files),
        "manifest_exists": manifest_path.is_file(),
        "manifest_count": len(manifest),
        "candidates_exist": candidates_path.is_file(),
        "candidate_card_count": len(candidates),
        "candidate_source_count": len({str(card.get("source_id") or "") for card in candidates}),
        "candidate_pending_count": sum(
            card.get("review_status") == "pending_human_review" for card in candidates
        ),
        "candidate_blocked_count": sum(
            card.get("review_status") == "blocked_automated_review" for card in candidates
        ),
        "approved_cards_exist": approved_path.is_file(),
        "approved_card_count": len(approved),
        "index_exists": (root / "index/vtt-guidance-v2.sqlite").is_file(),
    }


def purge(root: Path, confirmation: str, *, expected_root: Path | None = None) -> dict[str, object]:
    repo_root = Path(__file__).resolve().parents[1]
    expected = (expected_root or (repo_root / DEFAULT_ROOT)).resolve()
    resolved = root.resolve()
    if resolved != expected:
        raise VttGuidanceError(f"purge root must resolve exactly to {expected}")
    if root.is_symlink() or any(path.is_symlink() for path in root.rglob("*")):
        raise VttGuidanceError("purge refuses symlinks")
    files = sorted(path for path in root.rglob("*") if path.is_file()) if root.is_dir() else []
    if confirmation != PURGE_CONFIRMATION:
        return {
            "dry_run": True,
            "root": resolved.as_posix(),
            "file_count": len(files),
            "confirmation_required": PURGE_CONFIRMATION,
        }
    if root.is_dir():
        shutil.rmtree(root)
    return {"dry_run": False, "root": resolved.as_posix(), "removed_file_count": len(files)}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "prepare-manifest":
            result = prepare_manifest(args.records, args.summary_root, args.output)
        elif args.command == "generate":
            result = generate_cards(
                args.manifest,
                args.output,
                args.review_queue,
                args.decisions_template,
                args.report,
                args.checkpoint_root,
                limit=args.limit,
                regenerate=args.regenerate,
            )
        elif args.command == "audit-corpus":
            result = audit_corpus(
                args.manifest,
                args.candidates,
                args.checkpoint_root,
                args.report,
            )
            if result["candidate_gate_passed"] is not True:
                raise VttGuidanceError("VTT guidance candidate corpus audit failed")
        elif args.command == "apply-review":
            result = apply_review(args.candidates, args.decisions, args.output, args.report)
        elif args.command == "build-index":
            result = build_fts_index(args.cards, args.output)
        elif args.command == "evaluate":
            result = evaluate_index(args.index, args.probes, args.report)
            if result["gate_passed"] is not True:
                raise VttGuidanceError("VTT guidance retrieval acceptance gates failed")
        elif args.command == "status":
            result = status(args.root)
        elif args.command == "purge":
            result = purge(args.root, args.confirm)
        else:  # pragma: no cover
            raise VttGuidanceError("unknown command")
    except (VttGuidanceError, OSError, json.JSONDecodeError) as exc:
        print(f"VTT guidance command failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
