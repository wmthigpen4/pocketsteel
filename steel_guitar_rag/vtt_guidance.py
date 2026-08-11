"""Isolated private VTT teaching-card retrieval and rendering.

This module never reads SGF data and never returns private source metadata to
the public answer contract. Runtime retrieval accepts only human-approved,
quote-disabled cards from a dedicated, checksummed SQLite FTS5 index.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "vtt_guidance_card_v2"
INDEX_SCHEMA_VERSION = "vtt_guidance_fts_v2"
BUILD_VERSION = "vtt-guidance-v2.0"
CONTENT_LAYER = "vtt_curated_guidance_v2"
DEFAULT_ROOT = Path("corpus-private/vtt-guidance-v2")
DEFAULT_APPROVED_CARDS = DEFAULT_ROOT / "approved/cards.jsonl"
DEFAULT_INDEX = DEFAULT_ROOT / "index/vtt-guidance-v2.sqlite"
ENABLE_VTT_GUIDANCE_RETRIEVAL_ENV = "ENABLE_VTT_GUIDANCE_RETRIEVAL"
ENABLE_VTT_GUIDANCE_IN_ANSWER_ENV = "ENABLE_VTT_GUIDANCE_IN_ANSWER"
VTT_GUIDANCE_INDEX_PATH_ENV = "VTT_GUIDANCE_INDEX_PATH"
MAX_RENDERED_CHARACTERS = 1_200
MAX_RUNTIME_CARDS = 3
MAX_RUNTIME_SOURCES = 2

CARD_TYPES = {
    "overview",
    "concept",
    "setup",
    "procedure",
    "common_mistake",
    "transfer",
}
RUNTIME_INSTRUMENTS = {"E9", "general"}
ALL_INSTRUMENTS = RUNTIME_INSTRUMENTS | {"C6", "non_pedal", "unknown"}

PRIVATE_MARKERS = {
    "presenter_or_brand": re.compile(
        r"\b(?:Travis|Toy Tutorials|TTT Members|Sunday Night Steel)\b", re.I
    ),
    "member_or_request": re.compile(
        r"\b(?:subscriber|member|requested|asked me|sent me|Facebook group|Zoom|email me)\b",
        re.I,
    ),
    "site_or_course": re.compile(
        r"\b(?:website|course|download|track below|next video|previous video|teachable)\b",
        re.I,
    ),
    "contact_or_link": re.compile(
        r"(?:[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|https?://|www\.|\b\d{3}[-.) ]\d{3}[-. ]\d{4}\b)",
        re.I,
    ),
    "personal_life": re.compile(
        r"\b(?:my (?:wife|husband|son|daughter|family)|i live in|my address|phone number)\b",
        re.I,
    ),
}
PATH_MARKER_RE = re.compile(
    r"(?:corpus-private|guidance-cleaned|summary-draft|full-draft|\.clean\.txt|\.vtt\b|/Users/|\\Users\\)",
    re.I,
)
TOKEN_RE = re.compile(r"[a-z0-9]+(?:['+#-][a-z0-9]+)*", re.I)
FORUM_WISDOM_RE = re.compile(
    r"\b(?:what\s+do\s+(?:players|people|forum|steelers)|players?\s+(?:say|think|report)|"
    r"forum\s+(?:players|wisdom|opinions?)|public\s+forum)\b",
    re.I,
)
EXCLUDED_QUERY_RE = re.compile(
    r"\b(?:who\s+(?:is|was)|history\s+of|biography|amp|amplifier|pickup|speaker|buy|price|"
    r"recording\s+gear|complete\s+(?:song|solo|transcript)|lyrics?)\b",
    re.I,
)
TEACHING_QUERY_RE = re.compile(
    r"\b(?:how|teach|practice|exercise|technique|blocking|picking|bar|intonation|vibrato|"
    r"pedal|lever|fret|grip|string|scale|lick|chord|copedent|tuning|harmonic|chime)\b",
    re.I,
)


class VttGuidanceError(RuntimeError):
    """Raised when isolated VTT guidance artifacts fail closed."""


@dataclass(frozen=True)
class VttGuidanceResult:
    card_id: str
    source_id: str
    parent_overview_id: str
    card_type: str
    instrument: str
    concept: str
    procedure: tuple[str, ...]
    common_mistakes: tuple[str, ...]
    score: float
    corpus_version: str

    def internal_dict(self) -> dict[str, object]:
        return {
            "card_id": self.card_id,
            "source_id": self.source_id,
            "parent_overview_id": self.parent_overview_id,
            "card_type": self.card_type,
            "instrument": self.instrument,
            "concept": self.concept,
            "procedure": list(self.procedure),
            "common_mistakes": list(self.common_mistakes),
            "score": self.score,
            "corpus_version": self.corpus_version,
        }


def env_flag(name: str, env: Mapping[str, str] | None = None) -> bool:
    value = (env or os.environ).get(name, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def vtt_guidance_retrieval_enabled(env: Mapping[str, str] | None = None) -> bool:
    return env_flag(ENABLE_VTT_GUIDANCE_RETRIEVAL_ENV, env)


def vtt_guidance_answer_enabled(env: Mapping[str, str] | None = None) -> bool:
    return env_flag(ENABLE_VTT_GUIDANCE_IN_ANSWER_ENV, env)


def configured_index_path(env: Mapping[str, str] | None = None) -> Path:
    configured = (env or os.environ).get(VTT_GUIDANCE_INDEX_PATH_ENV, "").strip()
    return Path(configured).expanduser() if configured else DEFAULT_INDEX


def is_vtt_teaching_query(question: str) -> bool:
    value = str(question or "")
    return bool(
        value.strip()
        and TEACHING_QUERY_RE.search(value)
        and not FORUM_WISDOM_RE.search(value)
        and not EXCLUDED_QUERY_RE.search(value)
    )


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(*parts: object) -> str:
    payload = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalized_words(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(str(text or ""))]


def contains_source_ngram(candidate: str, source: str, *, size: int = 10) -> bool:
    candidate_words = normalized_words(candidate)
    source_words = normalized_words(source)
    if len(candidate_words) < size or len(source_words) < size:
        return False
    source_ngrams = {
        tuple(source_words[index : index + size])
        for index in range(len(source_words) - size + 1)
    }
    return any(
        tuple(candidate_words[index : index + size]) in source_ngrams
        for index in range(len(candidate_words) - size + 1)
    )


def card_renderable_text(card: Mapping[str, object]) -> str:
    fields: list[str] = [str(card.get("concept") or "")]
    for key in ("setup", "procedure", "common_mistakes", "transfer"):
        value = card.get(key)
        if isinstance(value, (list, tuple)):
            fields.extend(str(item) for item in value)
    return "\n".join(part.strip() for part in fields if part.strip())


def privacy_findings(text: str) -> list[str]:
    findings = [name for name, pattern in PRIVATE_MARKERS.items() if pattern.search(text)]
    if PATH_MARKER_RE.search(text):
        findings.append("private_path_or_filename")
    return sorted(set(findings))


def _string_list(value: object, *, field: str, max_items: int = 16) -> list[str]:
    if not isinstance(value, list):
        raise VttGuidanceError(f"{field} must be a list")
    if len(value) > max_items:
        raise VttGuidanceError(f"{field} contains too many items")
    items = [" ".join(str(item).split()) for item in value]
    if any(not item for item in items):
        raise VttGuidanceError(f"{field} contains an empty item")
    return items


def _integer_anchor(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("boolean is not an integer anchor")
    if isinstance(value, int):
        return value
    normalized = str(value).strip().lower()
    match = re.fullmatch(r"(\d+)(?:st|nd|rd|th)?(?:\s+(?:string|fret))?", normalized)
    if not match:
        raise ValueError("invalid integer anchor")
    return int(match.group(1))


def validate_technical_anchors(anchors: object, *, instrument: str) -> list[str]:
    if not isinstance(anchors, dict):
        return ["technical_anchors_not_object"]
    findings: list[str] = []
    try:
        strings = [_integer_anchor(value) for value in anchors.get("strings") or []]
        frets = [_integer_anchor(value) for value in anchors.get("frets") or []]
    except (TypeError, ValueError):
        return ["technical_anchor_not_integer"]
    if any(value < 1 or value > 10 for value in strings):
        findings.append("invalid_e9_string")
    if any(value < 0 or value > 36 for value in frets):
        findings.append("invalid_fret")
    if instrument == "E9":
        from steel_guitar_rag.e9_copedents import get_e9_copedent_profile

        profile = get_e9_copedent_profile()
        valid_controls: set[str] = set()
        for control in profile.controls:
            valid_controls.update(
                {
                    control.id.lower(),
                    control.label.lower(),
                    *(value.lower() for value in control.player_shorthand),
                    *(value.lower() for value in control.compatibility_aliases),
                }
            )
        for field in ("pedals", "levers"):
            for value in anchors.get(field) or []:
                normalized = str(value).strip().lower()
                components = [part.strip() for part in re.split(r"\+|&|\band\b", normalized) if part.strip()]
                if not components or any(component not in valid_controls for component in components):
                    findings.append(f"invalid_e9_{field[:-1]}")
    return sorted(set(findings))


def validate_card(
    card: Mapping[str, object],
    *,
    source_text: str | None = None,
    require_human_approval: bool = False,
) -> list[str]:
    findings: list[str] = []
    required_strings = (
        "schema_version",
        "card_id",
        "source_id",
        "parent_overview_id",
        "card_type",
        "instrument",
        "concept",
        "source_sha256",
        "corpus_class",
        "privacy_action",
        "licensing_action",
        "generation_model",
        "generator_version",
        "privacy_review_model",
        "review_status",
    )
    for field in required_strings:
        if not isinstance(card.get(field), str) or not str(card.get(field)).strip():
            findings.append(f"missing_{field}")
    if card.get("schema_version") != SCHEMA_VERSION:
        findings.append("invalid_schema_version")
    if card.get("card_type") not in CARD_TYPES:
        findings.append("invalid_card_type")
    instrument = str(card.get("instrument") or "")
    if instrument not in ALL_INSTRUMENTS:
        findings.append("invalid_instrument")
    if card.get("answer_quote_allowed") is not False:
        findings.append("answer_quote_must_be_false")
    if card.get("allowed_for_embedding") is not False:
        findings.append("embedding_must_be_false")
    for field in ("setup", "procedure", "common_mistakes", "transfer"):
        try:
            _string_list(card.get(field), field=field)
        except VttGuidanceError as exc:
            findings.append(str(exc))
    text = card_renderable_text(card)
    findings.extend(privacy_findings(text))
    findings.extend(validate_technical_anchors(card.get("technical_anchors"), instrument=instrument))
    if source_text is not None and contains_source_ngram(text, source_text):
        findings.append("source_ten_word_overlap")
    if require_human_approval:
        if card.get("review_status") != "approved" or card.get("human_approved") is not True:
            findings.append("human_approval_required")
        if instrument not in RUNTIME_INSTRUMENTS:
            findings.append("instrument_not_runtime_eligible")
        if card.get("music_validation_status") != "passed":
            findings.append("music_validation_required")
        if card.get("privacy_review_status") != "passed":
            findings.append("privacy_review_required")
    return sorted(set(findings))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise VttGuidanceError(f"{path.name}:{line_number} must be an object")
            rows.append(value)
    return rows


def corpus_digest(cards: Sequence[Mapping[str, object]]) -> str:
    ordered = sorted(cards, key=lambda card: str(card.get("card_id") or ""))
    return sha256_bytes(canonical_json(ordered).encode("utf-8"))


def _anchor_text(card: Mapping[str, object]) -> str:
    anchors = card.get("technical_anchors")
    if not isinstance(anchors, dict):
        return ""
    values: list[str] = []
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
        values.extend(str(value) for value in anchors.get(field) or [])
    return " ".join(values)


def build_fts_index(cards_path: Path, index_path: Path = DEFAULT_INDEX) -> dict[str, object]:
    cards = read_jsonl(cards_path)
    if not cards:
        raise VttGuidanceError("approved card file is empty")
    findings: dict[str, list[str]] = {}
    card_ids: set[str] = set()
    for card in cards:
        card_id = str(card.get("card_id") or "")
        card_findings = validate_card(card, require_human_approval=True)
        if card_id in card_ids:
            card_findings.append("duplicate_card_id")
        card_ids.add(card_id)
        if card_findings:
            findings[card_id or "missing-card-id"] = sorted(set(card_findings))
    if findings:
        raise VttGuidanceError(f"approved cards failed validation: {canonical_json(findings)}")

    digest = corpus_digest(cards)
    corpus_version = f"{SCHEMA_VERSION}:{digest[:16]}"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{index_path.name}.", suffix=".tmp", dir=index_path.parent, delete=False
    ) as handle:
        temp_path = Path(handle.name)
    try:
        connection = sqlite3.connect(temp_path)
        try:
            connection.executescript(
                """
                PRAGMA journal_mode=DELETE;
                PRAGMA synchronous=FULL;
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE cards (
                    card_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    parent_overview_id TEXT NOT NULL,
                    card_type TEXT NOT NULL,
                    instrument TEXT NOT NULL,
                    concept TEXT NOT NULL,
                    procedure_json TEXT NOT NULL,
                    common_mistakes_json TEXT NOT NULL,
                    corpus_version TEXT NOT NULL
                );
                CREATE VIRTUAL TABLE cards_fts USING fts5(
                    card_id UNINDEXED,
                    source_id UNINDEXED,
                    card_type,
                    instrument,
                    concept,
                    procedure,
                    common_mistakes,
                    anchor_text,
                    tokenize='unicode61 remove_diacritics 2'
                );
                """
            )
            metadata = {
                "index_schema_version": INDEX_SCHEMA_VERSION,
                "card_schema_version": SCHEMA_VERSION,
                "build_version": BUILD_VERSION,
                "corpus_sha256": digest,
                "corpus_version": corpus_version,
                "card_count": str(len(cards)),
                "source_count": str(len({str(card["source_id"]) for card in cards})),
            }
            connection.executemany("INSERT INTO metadata(key, value) VALUES (?, ?)", metadata.items())
            for card in sorted(cards, key=lambda item: str(item["card_id"])):
                procedure = _string_list(card.get("procedure"), field="procedure")
                mistakes = _string_list(card.get("common_mistakes"), field="common_mistakes")
                row = (
                    str(card["card_id"]),
                    str(card["source_id"]),
                    str(card["parent_overview_id"]),
                    str(card["card_type"]),
                    str(card["instrument"]),
                    str(card["concept"]),
                    json.dumps(procedure, ensure_ascii=False),
                    json.dumps(mistakes, ensure_ascii=False),
                    corpus_version,
                )
                connection.execute("INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
                connection.execute(
                    "INSERT INTO cards_fts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        row[0],
                        row[1],
                        row[3],
                        row[4],
                        row[5],
                        " ".join(procedure),
                        " ".join(mistakes),
                        _anchor_text(card),
                    ),
                )
            connection.commit()
            quick_check = connection.execute("PRAGMA quick_check").fetchone()
            if not quick_check or quick_check[0] != "ok":
                raise VttGuidanceError("generated VTT guidance index failed quick_check")
        finally:
            connection.close()
        os.replace(temp_path, index_path)
        sidecar = index_path.with_suffix(index_path.suffix + ".sha256")
        sidecar.write_text(f"{sha256_file(index_path)}  {index_path.name}\n", encoding="utf-8")
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return {
        "index_path": index_path.as_posix(),
        "corpus_version": corpus_version,
        "corpus_sha256": digest,
        "card_count": len(cards),
        "source_count": len({str(card["source_id"]) for card in cards}),
    }


def _verify_index_checksum(index_path: Path) -> None:
    sidecar = index_path.with_suffix(index_path.suffix + ".sha256")
    if not index_path.is_file() or not sidecar.is_file():
        raise VttGuidanceError("VTT guidance index or checksum is missing")
    expected = sidecar.read_text(encoding="utf-8").strip().split(maxsplit=1)[0]
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or sha256_file(index_path) != expected:
        raise VttGuidanceError("VTT guidance index checksum mismatch")


def _fts_query(question: str) -> str:
    tokens = []
    for token in normalized_words(question):
        if len(token) < 2 or token in {"how", "what", "where", "when", "with", "from", "that", "this"}:
            continue
        if token not in tokens:
            tokens.append(token)
    lowered = question.lower()
    if "b+c" in lowered or "b + c" in lowered:
        tokens.extend(["pedal", "minor", "movement"])
    if "a+b" in lowered or "a + b" in lowered:
        tokens.extend(["pedal", "major", "movement"])
    if "pick blocking" in lowered:
        tokens.extend(["blocking", "picking", "mute"])
    unique = list(dict.fromkeys(tokens))[:16]
    return " OR ".join(f'"{token.replace(chr(34), "")}"' for token in unique)


def _search_index_ranked(
    index_path: Path,
    question: str,
    *,
    top_k: int,
    max_cards: int,
    max_sources: int,
) -> list[VttGuidanceResult]:
    if top_k <= 0 or not is_vtt_teaching_query(question):
        return []
    _verify_index_checksum(index_path)
    query = _fts_query(question)
    if not query:
        return []
    connection = sqlite3.connect(f"file:{index_path.resolve().as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        metadata = dict(connection.execute("SELECT key, value FROM metadata").fetchall())
        if metadata.get("index_schema_version") != INDEX_SCHEMA_VERSION:
            raise VttGuidanceError("VTT guidance index schema mismatch")
        if metadata.get("card_schema_version") != SCHEMA_VERSION:
            raise VttGuidanceError("VTT guidance card schema mismatch")
        if metadata.get("build_version") != BUILD_VERSION:
            raise VttGuidanceError("VTT guidance build version mismatch")
        corpus_sha256 = str(metadata.get("corpus_sha256") or "")
        expected_corpus_version = f"{SCHEMA_VERSION}:{corpus_sha256[:16]}"
        if not re.fullmatch(r"[0-9a-f]{64}", corpus_sha256):
            raise VttGuidanceError("VTT guidance corpus hash is invalid")
        if metadata.get("corpus_version") != expected_corpus_version:
            raise VttGuidanceError("VTT guidance corpus version mismatch")
        expected_card_count = int(metadata.get("card_count") or 0)
        expected_source_count = int(metadata.get("source_count") or 0)
        actual_card_count = int(connection.execute("SELECT COUNT(*) FROM cards").fetchone()[0])
        actual_source_count = int(
            connection.execute("SELECT COUNT(DISTINCT source_id) FROM cards").fetchone()[0]
        )
        actual_fts_count = int(connection.execute("SELECT COUNT(*) FROM cards_fts").fetchone()[0])
        if expected_card_count <= 0:
            raise VttGuidanceError("VTT guidance index contains no cards")
        if (expected_card_count, expected_source_count) != (actual_card_count, actual_source_count):
            raise VttGuidanceError("VTT guidance index count mismatch")
        if actual_fts_count != actual_card_count:
            raise VttGuidanceError("VTT guidance FTS count mismatch")
        mismatched_versions = int(
            connection.execute(
                "SELECT COUNT(*) FROM cards WHERE corpus_version != ?",
                (expected_corpus_version,),
            ).fetchone()[0]
        )
        if mismatched_versions:
            raise VttGuidanceError("VTT guidance row version mismatch")

        def ranked_rows(*, overview: bool) -> list[sqlite3.Row]:
            card_filter = "c.card_type = 'overview'" if overview else "c.card_type != 'overview'"
            return connection.execute(
                f"""
            SELECT c.*, bm25(cards_fts, 0.0, 0.0, 0.25, 0.25, 2.5, 1.8, 1.2, 3.0) AS rank
            FROM cards_fts
            JOIN cards AS c ON c.card_id = cards_fts.card_id
            WHERE cards_fts MATCH ? AND {card_filter}
            ORDER BY rank ASC, c.card_id ASC
            LIMIT 60
            """,
                (query,),
            ).fetchall()

        overview_rows = ranked_rows(overview=True)
        detail_rows = ranked_rows(overview=False)
    except (sqlite3.DatabaseError, TypeError, ValueError) as exc:
        raise VttGuidanceError("VTT guidance index could not be read") from exc
    finally:
        connection.close()

    def make_result(row: sqlite3.Row) -> VttGuidanceResult:
        score = round(1.0 / (1.0 + abs(float(row["rank"]))), 6)
        return VttGuidanceResult(
            card_id=str(row["card_id"]),
            source_id=str(row["source_id"]),
            parent_overview_id=str(row["parent_overview_id"]),
            card_type=str(row["card_type"]),
            instrument=str(row["instrument"]),
            concept=str(row["concept"]),
            procedure=tuple(json.loads(str(row["procedure_json"]))),
            common_mistakes=tuple(json.loads(str(row["common_mistakes_json"]))),
            score=score,
            corpus_version=str(row["corpus_version"]),
        )

    overview_by_source: dict[str, VttGuidanceResult] = {}
    detail_by_source: dict[str, VttGuidanceResult] = {}
    source_rank: dict[str, tuple[int, int]] = {}
    for rank, row in enumerate(overview_rows):
        result = make_result(row)
        overview_by_source.setdefault(result.source_id, result)
        source_rank.setdefault(result.source_id, (rank, 60))
    for rank, row in enumerate(detail_rows):
        result = make_result(row)
        detail_by_source.setdefault(result.source_id, result)
        overview_rank, _ = source_rank.get(result.source_id, (60, 60))
        source_rank[result.source_id] = (overview_rank, rank)

    source_order = sorted(
        source_rank,
        key=lambda source_id: (
            min(source_rank[source_id]),
            sum(source_rank[source_id]),
            source_id,
        ),
    )[:max_sources]
    results: list[VttGuidanceResult] = []
    result_limit = min(top_k, max_cards)
    for source_id in source_order:
        overview = overview_by_source.get(source_id)
        detail = detail_by_source.get(source_id)
        if overview is not None:
            results.append(overview)
        if detail is not None and len(results) < result_limit:
            results.append(detail)
        if len(results) >= result_limit:
            break
    return results[:result_limit]


def search_index(
    index_path: Path,
    question: str,
    *,
    top_k: int = MAX_RUNTIME_CARDS,
) -> list[VttGuidanceResult]:
    return _search_index_ranked(
        index_path,
        question,
        top_k=top_k,
        max_cards=MAX_RUNTIME_CARDS,
        max_sources=MAX_RUNTIME_SOURCES,
    )


def evaluate_index(index_path: Path, probes_path: Path, report_path: Path) -> dict[str, object]:
    probes = read_jsonl(probes_path)
    kinds = {"detail", "broad", "human"}
    counts = {kind: sum(row.get("kind") == kind for row in probes) for kind in kinds}
    if counts["detail"] != 43 or counts["broad"] != 10 or counts["human"] <= 0:
        raise VttGuidanceError("evaluation requires 43 detail, 10 broad, and at least one human probe")

    detail_ranks: list[int | None] = []
    broad_top3_hits = 0
    human_top3_hits = 0
    wrong_instrument_results = 0
    for probe in probes:
        probe_id = str(probe.get("probe_id") or "").strip()
        question = str(probe.get("question") or "").strip()
        kind = str(probe.get("kind") or "")
        raw_sources = probe.get("useful_source_ids")
        useful_sources = (
            {str(value) for value in raw_sources if str(value)}
            if isinstance(raw_sources, list)
            else set()
        )
        if not probe_id or kind not in kinds or not useful_sources or not is_vtt_teaching_query(question):
            raise VttGuidanceError("evaluation probe schema or query eligibility is invalid")
        ranked = _search_index_ranked(
            index_path,
            question,
            top_k=10,
            max_cards=10,
            max_sources=5,
        )
        source_results: list[VttGuidanceResult] = []
        seen_sources: set[str] = set()
        for result in ranked:
            if result.source_id not in seen_sources:
                source_results.append(result)
                seen_sources.add(result.source_id)
        matched_rank = next(
            (
                rank
                for rank, result in enumerate(source_results[:5], start=1)
                if result.source_id in useful_sources
            ),
            None,
        )
        if kind == "detail":
            detail_ranks.append(matched_rank)
        elif kind == "broad":
            broad_top3_hits += int(matched_rank is not None and matched_rank <= 3)
        else:
            human_top3_hits += int(matched_rank is not None and matched_rank <= 3)
            raw_instruments = probe.get("expected_instruments")
            expected_instruments = (
                {str(value) for value in raw_instruments if str(value)}
                if isinstance(raw_instruments, list)
                else set()
            )
            if not expected_instruments:
                raise VttGuidanceError("human probes require expected_instruments")
            wrong_instrument_results += sum(
                result.instrument not in expected_instruments for result in source_results[:3]
            )

    detail_top3 = sum(rank is not None and rank <= 3 for rank in detail_ranks)
    detail_top5 = sum(rank is not None and rank <= 5 for rank in detail_ranks)
    detail_mrr = sum((1.0 / rank) if rank else 0.0 for rank in detail_ranks) / len(detail_ranks)
    human_useful_rate = human_top3_hits / counts["human"]
    gates = {
        "detail_top3": detail_top3 >= 14,
        "detail_top5": detail_top5 >= 23,
        "detail_mrr": detail_mrr >= 0.30,
        "broad_top3": broad_top3_hits == 10,
        "human_useful_top3": human_useful_rate >= 0.80,
        "wrong_instrument": wrong_instrument_results == 0,
    }
    report: dict[str, object] = {
        "schema_version": "vtt_guidance_retrieval_eval_v2",
        "probe_counts": counts,
        "detail": {"top3": detail_top3, "top5": detail_top5, "mrr": round(detail_mrr, 4)},
        "broad": {"useful_top3": broad_top3_hits},
        "human": {
            "useful_top3": human_top3_hits,
            "useful_top3_rate": round(human_useful_rate, 4),
            "wrong_instrument_results": wrong_instrument_results,
        },
        "gates": gates,
        "gate_passed": all(gates.values()),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(canonical_json(report) + "\n", encoding="utf-8")
    return report


def search_vtt_guidance(
    question: str,
    *,
    top_k: int = MAX_RUNTIME_CARDS,
    index_path: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> list[dict[str, object]]:
    if not vtt_guidance_retrieval_enabled(env):
        return []
    path = index_path or configured_index_path(env)
    return [item.internal_dict() for item in search_index(path, question, top_k=top_k)]


def _coerce_result(value: Mapping[str, object] | VttGuidanceResult) -> VttGuidanceResult:
    if isinstance(value, VttGuidanceResult):
        return value
    raw_procedure = value.get("procedure")
    procedure = raw_procedure if isinstance(raw_procedure, (list, tuple)) else []
    raw_mistakes = value.get("common_mistakes")
    mistakes = raw_mistakes if isinstance(raw_mistakes, (list, tuple)) else []
    raw_score = value.get("score")
    score = float(raw_score) if isinstance(raw_score, (int, float, str)) else 0.0
    return VttGuidanceResult(
        card_id=str(value.get("card_id") or ""),
        source_id=str(value.get("source_id") or ""),
        parent_overview_id=str(value.get("parent_overview_id") or ""),
        card_type=str(value.get("card_type") or ""),
        instrument=str(value.get("instrument") or ""),
        concept=" ".join(str(value.get("concept") or "").split()),
        procedure=tuple(" ".join(str(item).split()) for item in procedure),
        common_mistakes=tuple(" ".join(str(item).split()) for item in mistakes),
        score=score,
        corpus_version=str(value.get("corpus_version") or ""),
    )


def render_guidance_section(
    results: Sequence[Mapping[str, object] | VttGuidanceResult],
) -> dict[str, str] | None:
    selected = [_coerce_result(value) for value in results[:MAX_RUNTIME_CARDS]]
    if not selected:
        return None
    concepts: list[str] = []
    procedures: list[str] = []
    mistakes: list[str] = []
    for result in selected:
        if result.concept and result.concept not in concepts:
            concepts.append(result.concept)
        for step in result.procedure:
            if step and step not in procedures:
                procedures.append(step)
        for mistake in result.common_mistakes:
            if mistake and mistake not in mistakes:
                mistakes.append(mistake)
    parts: list[str] = []
    if concepts:
        parts.append(concepts[0])
    if procedures:
        parts.append("Try this:\n" + "\n".join(f"- {step}" for step in procedures[:3]))
    if mistakes:
        parts.append(f"Common mistake: {mistakes[0]}")
    body = "\n\n".join(parts).strip()
    if len(body) > MAX_RENDERED_CHARACTERS:
        body = body[: MAX_RENDERED_CHARACTERS - 3].rstrip() + "..."
    if not body or privacy_findings(body):
        return None
    return {"title": "Curated lesson guidance", "style": "guidance", "body": body}


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(canonical_json(dict(row)) + "\n")
