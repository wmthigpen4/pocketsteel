#!/usr/bin/env python3
"""Clean and classify sample Phase 3 SGF chunks for corpus-v2 planning."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping


ROLES = {
    "question",
    "answer_advice",
    "opinion",
    "gear_signature",
    "sale_wanted",
    "event",
    "memorial",
    "link_only",
    "joke_chatter",
    "contact_block",
    "unknown",
}

SOURCE_METADATA_FIELDS = ("source_system", "forum_name", "thread_id", "thread_title", "thread_url")

EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}")
CONTACT_RE = re.compile(
    r"\b(?:e-?mail\s+me|pm\s+me|private\s+message|call\s+me|contact\s+me|send\s+me\s+(?:an?\s+)?(?:email|pm))\b",
    re.IGNORECASE,
)
SHARE_RE = re.compile(r"(?:[?&](?:sp|usp)=sharing\b|\b(?:sp|usp)=sharing\b|drive\.google\.com)", re.IGNORECASE)
URL_RE = re.compile(r"https?://\S+|www\.\S+|\bclick here\b", re.IGNORECASE)
RAW_URL_RE = re.compile(r"https?://\S+|www\.\S+|\bclick here\b", re.IGNORECASE)
TOP_TOKEN_RE = re.compile(r"(?<![A-Za-z])Top(?![A-Za-z])")
NAV_LINE_RE = re.compile(
    r"^(?:Top|Back to top|You do not have the required permissions to view the files attached to this post\.)$",
    re.IGNORECASE,
)
EDIT_LINE_RE = re.compile(r"^Last edited by .+? in total\.$", re.IGNORECASE)
QUOTE_RE = re.compile(r"\b[A-Z][\w .'-]{0,80}\s+wrote:|\bquote:\b|<small>|</small>", re.IGNORECASE)
SIGNATURE_SEPARATOR_RE = re.compile(r"^\s*(?:-{5,}|_{5,}|={5,}|--)\s*$")
INLINE_SIGNATURE_SEPARATOR_RE = re.compile(r"(?<![_=])-{5,}(?![_=])")
GEAR_RE = re.compile(
    r"\b(?:D-?10|SD-?10|S-?10|U-?12|Zum(?:Steel)?|Emmons|Sho-?Bud|Mullen|MSA|Carter|GFI|Sierra|"
    r"Williams|Franklin|Derby|Fessenden|MCI|BMI|Excel|Rittenberry|Quilter|Peavey|Nashville\s*(?:400|112|1000)|Session\s*400|"
    r"Webb|Evans|Telonics|Goodrich|Hilton|Sarno|Black Box|Steel King|Profex|NV\s*112|L710|BL-?710|"
    r"E9|C6|copedent|amp|cab(?:inet)?|pickup|volume pedal)\b",
    re.IGNORECASE,
)
AUTHOR_DATE_RE = re.compile(
    r"\b[A-Z][A-Za-z.'~-]+(?:\s+[A-Z][A-Za-z.'~-]+){0,3}\s*/\s+"
    r"\d{1,2}\s+[A-Z][a-z]+\s+\d{4}\s+\d{1,2}:\d{2}\s+(?:am|pm)\b"
)
INLINE_GEAR_SIGNATURE_START_RE = re.compile(
    r"\b[A-Z][A-Za-z.'~-]+(?:\s+[A-Z][A-Za-z.'~-]+){1,3}\s+"
    r"(?=(?:D-?10|SD-?10|S-?10|U-?12|Zum(?:Steel)?|Emmons|Sho-?Bud|Mullen|MSA|Carter|GFI|Sierra|"
    r"Williams|Franklin|Derby|Fessenden|MCI|BMI|Excel|Rittenberry|Peavey|Nashville|Session|Webb|"
    r"Evans|Telonics|Goodrich|Hilton|Steel King)\b)"
)
QUESTION_RE = re.compile(
    r"\?|"
    r"\b(?:does anyone|has anyone|can anyone|could someone|what|why|how|where|which|who|is there|are there|"
    r"anybody know|looking for|need help|can somebody|could somebody)\b",
    re.IGNORECASE,
)
ANSWER_RE = re.compile(
    r"\b(?:you should|i recommend|i would|try|use|adjust|check|replace|lower|raise|tune|because|"
    r"the problem|the issue|works well|best way|be sure|make sure|in my experience|i use|i've used|"
    r"sounds? good|settings?|ohm|pot|pickup|changer|pedal|lever|fret|string|amp|speaker|cabinet|reverb|delay|"
    r"compressor|volume pedal|tone|hum|buzz|ground|lubricat|tri-flow|wd-?40)\b",
    re.IGNORECASE,
)
ADVICE_RE = re.compile(
    r"\b(?:you should|i recommend|i would|try|use|adjust|check|replace|lower|raise|tune|because|"
    r"the problem|the issue|works well|sounds? good|best way|be sure|make sure|in my experience|i use|i've used)\b",
    re.IGNORECASE,
)
OPINION_RE = re.compile(r"\b(?:i think|i believe|in my opinion|imo|imho|prefer|favorite|best|better|worse)\b", re.IGNORECASE)
SALE_RE = re.compile(
    r"\b(?:for sale|wanted|wtb|wtt|sold|bump|pm sent|price|shipping|paypal|obo|trade|classified|"
    r"lowered price|still available|buyer)\b|\$\s?\d",
    re.IGNORECASE,
)
CHATTER_RE = re.compile(
    r"\b(?:thanks|thank you|lol|haha|amen|congrats|welcome|me too|same here|good luck|delete this|"
    r"wrong section|test post)\b",
    re.IGNORECASE,
)
EVENT_RE = re.compile(
    r"\b(?:show|jam|jamboree|convention|seminar|festival|concert|gig|club|meeting|schedule|calendar|"
    r"workshop|steel show|tsga|isgc)\b",
    re.IGNORECASE,
)
EVENT_STRONG_RE = re.compile(
    r"\b(?:jamboree|convention|seminar|festival|concert|meeting|schedule|calendar|workshop|steel show|tsga|isgc)\b",
    re.IGNORECASE,
)
MEMORIAL_RE = re.compile(
    r"\b(?:rip|r\.i\.p\.|rest in peace|passed away|sad to hear|condolences|memorial|obituary|funeral|"
    r"prayers|will be missed)\b",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9+'_.-]*")


def compact_space(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def as_list(value: Any) -> list[Any]:
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        return [item for item in value if item not in (None, "")]
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return [item for item in parsed if item not in (None, "")]
        return [part.strip() for part in stripped.split(",") if part.strip()]
    return [value]


def source_metadata_complete(row: Mapping[str, Any]) -> tuple[bool, list[str]]:
    missing = [field for field in SOURCE_METADATA_FIELDS if not row.get(field)]
    return not missing, missing


def stable_legacy_thread_id(row: Mapping[str, Any]) -> str:
    if row.get("source_system") != "sgf_ubb_legacy":
        return ""
    for field in ("legacy_thread_uid", "thread_url", "source_url"):
        value = str(row.get(field) or "").strip()
        if not value:
            continue
        match = re.search(r"(?:^|[:/])(Forum\d+/HTML/\d+)\.html\b", value, flags=re.IGNORECASE)
        if match:
            return f"ubb:{match.group(1).lower()}"
        if field == "legacy_thread_uid":
            safe_value = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-").lower()
            if safe_value:
                return f"ubb:{safe_value}"
    seed = "|".join(
        str(row.get(field) or "")
        for field in ("forum_name", "thread_title", "chunk_id", "large_sample_source_line")
    )
    if seed.strip("|"):
        return f"ubb:derived:{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"
    return ""


def normalize_source_metadata(row: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    if not normalized.get("thread_id"):
        legacy_thread_id = stable_legacy_thread_id(normalized)
        if legacy_thread_id:
            normalized["thread_id"] = legacy_thread_id
            flags = as_list(normalized.get("metadata_normalization_flags"))
            if "legacy_thread_id_derived" not in flags:
                flags.append("legacy_thread_id_derived")
            normalized["metadata_normalization_flags"] = flags
    return normalized


def normalize_post_identity(row: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    if not normalized.get("post_uid") and not as_list(normalized.get("post_uids")):
        chunk_id = str(normalized.get("chunk_id") or "").strip()
        if chunk_id:
            normalized["post_uids"] = [f"source_chunk:{chunk_id}"]
            flags = as_list(normalized.get("metadata_normalization_flags"))
            if "post_identity_derived_from_chunk_id" not in flags:
                flags.append("post_identity_derived_from_chunk_id")
            normalized["metadata_normalization_flags"] = flags
    return normalized


def post_identity_complete(row: Mapping[str, Any]) -> bool:
    return bool(row.get("post_uid") or as_list(row.get("post_uids")))


def strip_contact_text(text: str, flags: set[str]) -> str:
    if EMAIL_RE.search(text) or PHONE_RE.search(text) or CONTACT_RE.search(text):
        flags.add("contact_block_removed")
    text = EMAIL_RE.sub("[contact removed]", text)
    text = PHONE_RE.sub("[contact removed]", text)
    text = CONTACT_RE.sub("[contact removed]", text)
    return text


def strip_share_fragments(text: str, flags: set[str]) -> str:
    if SHARE_RE.search(text):
        flags.add("share_fragment_removed")
    text = re.sub(r"([?&])(?:sp|usp)=sharing\b&?", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:sp|usp)=sharing\b", "", text, flags=re.IGNORECASE)
    return text


def strip_raw_links(text: str, flags: set[str]) -> str:
    if RAW_URL_RE.search(text):
        flags.add("raw_link_removed")
        text = RAW_URL_RE.sub("[link removed]", text)
    return text


def remove_navigation_lines(text: str, flags: set[str]) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if NAV_LINE_RE.match(stripped) or EDIT_LINE_RE.match(stripped):
            flags.add("navigation_removed")
            continue
        lines.append(line)
    text = "\n".join(lines)
    if TOP_TOKEN_RE.search(text):
        flags.add("top_removed")
        text = TOP_TOKEN_RE.sub(" ", text)
    return text


def sentence_parts(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", compact_space(text)) if part.strip()]


def remove_repeated_sentences(text: str, flags: set[str]) -> str:
    seen: set[str] = set()
    kept: list[str] = []
    for part in sentence_parts(text):
        key = re.sub(r"\W+", " ", part).strip().lower()
        if len(key) > 20 and (key in seen or any(key in previous for previous in seen)):
            flags.add("duplicate_sentence_removed")
            continue
        seen.add(key)
        kept.append(part)
    return " ".join(kept) if kept else text


def remove_repeated_thread_title(text: str, thread_title: str, flags: set[str]) -> str:
    title = compact_space(thread_title)
    if len(title) < 12:
        return text
    pattern = re.compile(rf"(?im)^\s*{re.escape(title)}\s*$")
    text, count = pattern.subn("", text)
    if count:
        flags.add("thread_title_removed")
    return text


def strip_quote_markers(text: str, flags: set[str]) -> str:
    quote_markers = len(QUOTE_RE.findall(text))
    if quote_markers:
        flags.add("quote_marker_detected")
    return text


def split_signature(text: str, flags: set[str]) -> tuple[str, str]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if SIGNATURE_SEPARATOR_RE.match(line):
            body = "\n".join(lines[:index])
            signature = "\n".join(lines[index + 1 :])
            if signature.strip():
                flags.add("signature_removed")
                return body, signature

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if len(paragraphs) > 1:
        tail = paragraphs[-1]
        gear_hits = len(GEAR_RE.findall(tail))
        if gear_hits >= 3 and word_count(tail) <= 80:
            flags.add("gear_signature_removed")
            return "\n\n".join(paragraphs[:-1]), tail

    return text, ""


def split_inline_gear_signature(text: str, signature_text: str, flags: set[str]) -> tuple[str, str]:
    """Remove short rig-list tails that were flattened onto an answer line."""
    inline_match = re.search(r"\b[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+)?\s[-/]\s.+$", text)
    if inline_match:
        tail = inline_match.group(0).strip()
        if word_count(tail) <= 80 and len(GEAR_RE.findall(tail)) >= 3:
            body = compact_space(text[: inline_match.start()])
            if word_count(body) >= 5:
                flags.add("inline_gear_signature_removed")
                merged_signature = compact_space(f"{signature_text}\n{tail}" if signature_text else tail)
                return body, merged_signature

    words = text.split()
    if len(words) < 14:
        return text, signature_text

    for tail_word_count in (24, 32, 44, 60):
        if len(words) <= tail_word_count:
            continue
        tail = " ".join(words[-tail_word_count:])
        gear_hits = len(GEAR_RE.findall(tail))
        if gear_hits < 3:
            continue
        has_signature_shape = bool(
            re.search(r"(?:\s[-/]\s|\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s*[-/]\s)", tail)
            or re.search(r"\b(?:D-?10|SD-?10|S-?10|U-?12)\b", tail, re.IGNORECASE)
        )
        if not has_signature_shape:
            continue
        body = " ".join(words[:-tail_word_count])
        if word_count(body) < 5:
            continue
        flags.add("inline_gear_signature_removed")
        merged_signature = compact_space(f"{signature_text}\n{tail}" if signature_text else tail)
        return compact_space(body), merged_signature

    return text, signature_text


def strip_inline_signature_spans(text: str, signature_text: str, flags: set[str]) -> tuple[str, str]:
    pieces: list[str] = []
    signatures: list[str] = [signature_text] if signature_text else []
    cursor = 0
    removed = False

    for match in INLINE_GEAR_SIGNATURE_START_RE.finditer(text):
        if match.start() < cursor:
            continue
        next_author = AUTHOR_DATE_RE.search(text, match.end())
        end = next_author.start() if next_author else len(text)
        candidate = compact_space(text[match.start() : end])
        gear_hits = len(GEAR_RE.findall(candidate))
        if gear_hits < 3 or word_count(candidate) > 120:
            continue
        pieces.append(text[cursor : match.start()])
        signatures.append(candidate)
        cursor = end
        removed = True

    if not removed:
        return text, signature_text

    pieces.append(text[cursor:])
    flags.add("inline_gear_signature_removed")
    return compact_space(" ".join(pieces)), compact_space("\n".join(part for part in signatures if part))


def strip_inline_separator_signatures(text: str, signature_text: str, flags: set[str]) -> tuple[str, str]:
    pieces: list[str] = []
    signatures: list[str] = [signature_text] if signature_text else []
    cursor = 0
    removed = False

    for match in INLINE_SIGNATURE_SEPARATOR_RE.finditer(text):
        if match.start() < cursor:
            continue
        next_author = AUTHOR_DATE_RE.search(text, match.end())
        end = next_author.start() if next_author else len(text)
        candidate = compact_space(text[match.end() : end])
        if not candidate:
            continue
        candidate_words = word_count(candidate)
        if candidate_words > 120:
            continue
        is_signature = (
            len(GEAR_RE.findall(candidate)) >= 1
            or "raw_link_removed" in flags
            or "contact_block_removed" in flags
            or candidate_words <= 30
        )
        if not is_signature:
            continue
        pieces.append(text[cursor : match.start()])
        signatures.append(candidate)
        cursor = end
        removed = True

    if not removed:
        return text, signature_text

    pieces.append(text[cursor:])
    flags.add("signature_removed")
    return compact_space(" ".join(pieces)), compact_space("\n".join(part for part in signatures if part))


def cleanup_text(raw_text: str, thread_title: str = "") -> tuple[str, str, list[str]]:
    flags: set[str] = set()
    text = compact_space(raw_text or "")
    text = remove_repeated_thread_title(text, thread_title, flags)
    text = strip_share_fragments(text, flags)
    text = strip_raw_links(text, flags)
    text = strip_contact_text(text, flags)
    text = remove_navigation_lines(text, flags)
    text = strip_quote_markers(text, flags)
    text, signature_text = split_signature(text, flags)
    text, signature_text = strip_inline_separator_signatures(text, signature_text, flags)
    text, signature_text = split_inline_gear_signature(text, signature_text, flags)
    text, signature_text = strip_inline_signature_spans(text, signature_text, flags)
    text = remove_repeated_sentences(text, flags)
    text = compact_space(text)
    return text, compact_space(signature_text), sorted(flags)


def detect_roles(text: str, raw_text: str, signature_text: str, links: list[Any], cleanup_flags: list[str]) -> dict[str, bool]:
    tokens = word_count(text)
    url_count = len(URL_RE.findall(raw_text)) + len(links)
    answer_hits = len(ANSWER_RE.findall(text))
    question_hits = len(QUESTION_RE.findall(text))
    quote_hits = len(QUOTE_RE.findall(raw_text))
    sale_hits = len(SALE_RE.findall(text))
    event_hits = len(EVENT_RE.findall(text))
    strong_event_hits = len(EVENT_STRONG_RE.findall(text))
    opinion_hits = len(OPINION_RE.findall(text))
    advice_like = bool(answer_hits >= 4 or ADVICE_RE.search(text))
    question_like = bool(question_hits and not ADVICE_RE.search(text) and tokens <= 220)
    sale_dominates = bool(sale_hits and not advice_like)
    event_dominates = bool(event_hits and not advice_like and (strong_event_hits or event_hits >= 2))
    roles = {
        "contact_block": "contact_block_removed" in cleanup_flags,
        "gear_signature": bool(signature_text or "gear_signature_removed" in cleanup_flags or "signature_removed" in cleanup_flags),
        "sale_wanted": sale_dominates,
        "event": event_dominates,
        "memorial": bool(MEMORIAL_RE.search(text)),
        "joke_chatter": bool(CHATTER_RE.search(text) and answer_hits < 3),
        "link_only": bool(url_count and (tokens <= 80 or url_count / max(tokens, 1) > 0.05) and answer_hits < 2),
        "question": question_like,
        "answer_advice": advice_like,
        "opinion": bool(opinion_hits and answer_hits < 2 and not event_dominates),
        "quote_heavy": quote_hits >= 3,
    }
    return roles


def choose_role(roles: Mapping[str, bool]) -> str:
    if roles.get("answer_advice"):
        return "answer_advice"
    if roles.get("question"):
        return "question"
    for role in (
        "contact_block",
        "sale_wanted",
        "memorial",
        "event",
        "link_only",
        "gear_signature",
        "opinion",
        "joke_chatter",
    ):
        if roles.get(role):
            return role
    return "unknown"


def score_answer_density(text: str) -> float:
    tokens = max(word_count(text), 1)
    answer_hits = len(ANSWER_RE.findall(text))
    question_hits = len(QUESTION_RE.findall(text))
    density = min(1.0, answer_hits / 8.0 + min(tokens, 300) / 900.0)
    density -= min(0.35, question_hits * 0.07)
    return round(max(0.0, min(1.0, density)), 3)


def score_noise(raw_text: str, clean_text: str, signature_text: str, cleanup_flags: list[str], roles: Mapping[str, bool]) -> float:
    raw_tokens = max(word_count(raw_text), 1)
    url_ratio = len(URL_RE.findall(raw_text)) / raw_tokens
    removed_ratio = max(0, len(raw_text) - len(clean_text)) / max(len(raw_text), 1)
    score = 0.0
    score += min(0.35, len(cleanup_flags) * 0.07)
    score += min(0.25, removed_ratio)
    score += min(0.2, url_ratio * 4)
    if signature_text:
        score += 0.1
    if roles.get("quote_heavy"):
        score += 0.15
    if roles.get("link_only") or roles.get("contact_block"):
        score += 0.2
    if roles.get("sale_wanted") or roles.get("joke_chatter"):
        score += 0.1
    return round(max(0.0, min(1.0, score)), 3)


def quality_score(answer_density: float, noise_score: float, metadata_complete: bool, post_identity: bool) -> float:
    score = 0.5 + (answer_density * 0.35) - (noise_score * 0.45)
    if metadata_complete:
        score += 0.08
    if post_identity:
        score += 0.07
    return round(max(0.0, min(1.0, score)), 3)


def clean_and_classify_chunk(row: Mapping[str, Any]) -> dict[str, Any]:
    normalized_row = normalize_post_identity(normalize_source_metadata(row))
    raw_text = str(normalized_row.get("chunk_text") or normalized_row.get("text") or "")
    clean_text, signature_text, flags = cleanup_text(raw_text, str(normalized_row.get("thread_title") or ""))
    links = as_list(normalized_row.get("links"))
    roles = detect_roles(clean_text, raw_text, signature_text, links, flags)
    role = choose_role(roles)
    metadata_complete, missing_metadata = source_metadata_complete(normalized_row)
    post_identity = post_identity_complete(normalized_row)
    answer_density = score_answer_density(clean_text)
    noise_score = score_noise(raw_text, clean_text, signature_text, flags, roles)

    output = dict(normalized_row)
    output.update(
        {
            "raw_text": raw_text,
            "clean_text": clean_text,
            "answer_text": clean_text,
            "signature_text": signature_text,
            "post_role": role,
            "chunk_role": role,
            "detected_roles": sorted(role_name for role_name, active in roles.items() if active and role_name in ROLES),
            "noise_score": noise_score,
            "answer_density": answer_density,
            "source_metadata_complete": metadata_complete,
            "missing_source_metadata": missing_metadata,
            "post_identity_complete": post_identity,
            "quality_score": quality_score(answer_density, noise_score, metadata_complete, post_identity),
            "cleanup_flags": flags,
        }
    )
    return output


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


def summarize(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    role_counts = Counter(str(row.get("chunk_role") or "unknown") for row in rows)
    flag_counts: Counter[str] = Counter()
    for row in rows:
        flag_counts.update(str(flag) for flag in row.get("cleanup_flags") or [])
    return {
        "rows": len(rows),
        "role_counts": dict(sorted(role_counts.items())),
        "cleanup_flag_counts": dict(sorted(flag_counts.items())),
        "avg_noise_score": round(sum(float(row.get("noise_score") or 0) for row in rows) / max(len(rows), 1), 3),
        "avg_answer_density": round(sum(float(row.get("answer_density") or 0) for row in rows) / max(len(rows), 1), 3),
    }


def update_summary_counts(summary: dict[str, Any], row: Mapping[str, Any]) -> None:
    summary["rows"] += 1
    summary["role_counts"][str(row.get("chunk_role") or "unknown")] += 1
    summary["cleanup_flag_counts"].update(str(flag) for flag in row.get("cleanup_flags") or [])
    summary["noise_score_total"] += float(row.get("noise_score") or 0)
    summary["answer_density_total"] += float(row.get("answer_density") or 0)


def finalize_summary(summary: Mapping[str, Any]) -> dict[str, Any]:
    rows = int(summary["rows"])
    return {
        "rows": rows,
        "role_counts": dict(sorted(summary["role_counts"].items())),
        "cleanup_flag_counts": dict(sorted(summary["cleanup_flag_counts"].items())),
        "avg_noise_score": round(float(summary["noise_score_total"]) / max(rows, 1), 3),
        "avg_answer_density": round(float(summary["answer_density_total"]) / max(rows, 1), 3),
    }


def clean_file(input_path: Path, output_path: Path, *, limit: int | None = None) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "rows": 0,
        "role_counts": Counter(),
        "cleanup_flag_counts": Counter(),
        "noise_score_total": 0.0,
        "answer_density_total": 0.0,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for index, row in enumerate(iter_jsonl(input_path), start=1):
            if limit is not None and index > limit:
                break
            cleaned = clean_and_classify_chunk(row)
            handle.write(json.dumps(cleaned, ensure_ascii=False, sort_keys=True) + "\n")
            update_summary_counts(summary, cleaned)
    return finalize_summary(summary)


def markdown_report(summary: Mapping[str, Any], input_path: Path, output_path: Path) -> str:
    lines = [
        "# Phase 3B Cleaner Classifier Sample Report",
        "",
        f"- Input: `{input_path}`",
        f"- Output: `{output_path}`",
        f"- Rows: `{summary['rows']}`",
        f"- Average noise score: `{summary['avg_noise_score']}`",
        f"- Average answer density: `{summary['avg_answer_density']}`",
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
    parser.add_argument("--input", required=True, type=Path, help="Sample chunk JSONL input.")
    parser.add_argument("--output", required=True, type=Path, help="Derived cleaned/classified sample JSONL output.")
    parser.add_argument("--report", type=Path, help="Optional Markdown sample report.")
    parser.add_argument("--limit", type=int, help="Optional max rows to process.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be at least 1")

    summary = clean_file(args.input, args.output, limit=args.limit)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(markdown_report(summary, args.input, args.output), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
