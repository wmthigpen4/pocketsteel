"""Deterministic, private build-time concept indexing for TTT lesson transcripts.

The compiler reads timestamped transcript text, not deployed companion data.  Its
output is intended for the ignored ``corpus-private`` authoring area.  A separate
reviewed companion artifact may copy short, approved excerpts and exact cue
times, but never the raw transcript or this graph wholesale.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "ttt_concept_graph_v1"
BUILD_VERSION = "ttt-concept-graph-v1.1"
TIMESTAMP_RE = re.compile(
    r"^\[(?P<start>\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?)\s+-\s+"
    r"(?P<end>\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?)\]\s*(?P<text>.*)$"
)
ZOOM_RE = re.compile(r"\b(?:zoom meetings?|ttt members|sunday night steel)\b", re.I)
APPLICATION_RE = re.compile(r"\b(?:songs?|solos?|licks?|intros?|outros?|bar room|application)\b", re.I)
DEFINITION_RE = re.compile(
    r"\b(?:what (?:that|this|it) means|what I mean|is just|is really|is a|means|referring to|"
    r"formed from|constructed of|made of|made up of)\b",
    re.I,
)
CONTRAST_RE = re.compile(r"\b(?:rather than|instead of|different|not the same|versus|vs\.?|but)\b", re.I)
DEMONSTRATION_RE = re.compile(
    r"\b(?:strings?|frets?|pedals?|levers?|grips?|raise|lower|position|notes?)\b",
    re.I,
)
TROUBLESHOOT_RE = re.compile(r"\b(?:problem|mistake|don't|do not|if you|make sure|avoid)\b", re.I)
CORRECTION_RE = re.compile(
    r"\b(?:correction|i misspoke|should have said|that(?:'s| is| was) wrong|i said .{0,50} but)\b",
    re.I,
)
SEMANTIC_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "between",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "one",
    "or",
    "the",
    "this",
    "to",
    "use",
    "with",
}
SEMANTIC_REVIEW_THRESHOLD = 0.80


class TttConceptGraphError(ValueError):
    """Raised when private transcript evidence cannot be compiled safely."""


@dataclass(frozen=True)
class TranscriptCue:
    start_ms: int
    end_ms: int
    text: str


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(*parts: object) -> str:
    return hashlib.sha256("\x1f".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:24]


def timestamp_to_ms(value: str) -> int:
    match = re.fullmatch(r"(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,3}))?", value.strip())
    if not match:
        raise TttConceptGraphError(f"Invalid timestamp: {value!r}")
    hours, minutes, seconds, fraction = match.groups()
    milliseconds = int((fraction or "0").ljust(3, "0"))
    return ((int(hours) * 60 * 60) + (int(minutes) * 60) + int(seconds)) * 1000 + milliseconds


def parse_timestamped_transcript(path: Path) -> list[TranscriptCue]:
    cues: list[TranscriptCue] = []
    previous_start = -1
    for line_number, raw_line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        match = TIMESTAMP_RE.match(line)
        if not match:
            raise TttConceptGraphError(f"{path.name}:{line_number} is not a timestamped cue")
        start_ms = timestamp_to_ms(match.group("start"))
        end_ms = timestamp_to_ms(match.group("end"))
        text = " ".join(match.group("text").split())
        if start_ms < previous_start or end_ms <= start_ms or not text:
            raise TttConceptGraphError(f"{path.name}:{line_number} has invalid cue timing or text")
        cues.append(TranscriptCue(start_ms=start_ms, end_ms=end_ms, text=text))
        previous_start = start_ms
    if not cues:
        raise TttConceptGraphError(f"Transcript contains no cues: {path}")
    return cues


def _normalized(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")


def _concept_pattern(aliases: Sequence[str]) -> re.Pattern[str]:
    if not aliases:
        raise TttConceptGraphError("Every concept requires at least one alias")
    terms: list[str] = []
    for alias in sorted({" ".join(str(item).split()).lower() for item in aliases if str(item).strip()}, key=len, reverse=True):
        escaped = re.escape(alias).replace(r"\ ", r"[\s-]+")
        terms.append(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")
    return re.compile("|".join(terms), re.I)


def validate_taxonomy(taxonomy: Mapping[str, Any]) -> None:
    if taxonomy.get("schemaVersion") != "ttt_concept_taxonomy_v1":
        raise TttConceptGraphError("Unsupported concept taxonomy schema")
    concepts = taxonomy.get("concepts")
    if not isinstance(concepts, list) or not concepts:
        raise TttConceptGraphError("Concept taxonomy requires concepts")
    ids = [str(item.get("id") or "") for item in concepts]
    if "" in ids or len(ids) != len(set(ids)):
        raise TttConceptGraphError("Concept IDs must be present and unique")
    known = set(ids)
    for concept in concepts:
        if not str(concept.get("label") or "").strip():
            raise TttConceptGraphError(f"Concept {concept.get('id')} requires a label")
        _concept_pattern(concept.get("aliases") or [])
        semantic_seeds = concept.get("semanticSeeds") or []
        if not isinstance(semantic_seeds, list) or not semantic_seeds or any(
            len(_semantic_tokens(seed)) < 2 for seed in semantic_seeds
        ):
            raise TttConceptGraphError(f"Concept {concept.get('id')} requires useful semanticSeeds")
        for field in ("prerequisiteConceptIds", "deeperConceptIds", "confusionConceptIds"):
            values = concept.get(field) or []
            if not isinstance(values, list) or any(str(value) not in known for value in values):
                raise TttConceptGraphError(f"Concept {concept.get('id')} has an unknown {field} reference")
        formula = concept.get("formula")
        if formula is not None and not re.fullmatch(r"[1-9](?:[-–][#b♭♯]?[1-9]){1,7}", str(formula)):
            raise TttConceptGraphError(f"Concept {concept.get('id')} has an invalid interval formula")


def validate_catalog(catalog: Mapping[str, Any]) -> None:
    if catalog.get("schemaVersion") != "ttt_lesson_catalog_v1":
        raise TttConceptGraphError("Unsupported lesson catalog schema")
    lessons = catalog.get("lessons")
    if not isinstance(lessons, list) or not lessons:
        raise TttConceptGraphError("Lesson catalog requires lessons")
    ids = [str(item.get("id") or "") for item in lessons]
    if "" in ids or len(ids) != len(set(ids)):
        raise TttConceptGraphError("Lesson IDs must be present and unique")
    for lesson in lessons:
        source_slug = str(lesson.get("sourceSlug") or "")
        if not source_slug or ZOOM_RE.search(source_slug) or lesson.get("isZoom") is not False:
            raise TttConceptGraphError(f"Lesson {lesson.get('id')} must be an explicit non-Zoom source")
        if lesson.get("depth") not in {"quick", "foundation", "focused", "advanced", "application"}:
            raise TttConceptGraphError(f"Lesson {lesson.get('id')} has an invalid depth")
        dedicated_concepts = lesson.get("dedicatedConceptIds")
        if not isinstance(dedicated_concepts, list) or any(not str(item).strip() for item in dedicated_concepts):
            raise TttConceptGraphError(f"Lesson {lesson.get('id')} requires dedicatedConceptIds")
        url = str(lesson.get("url") or "")
        if url and not re.fullmatch(r"https://travis-toy-tutorials\.teachable\.com/courses/[^\s]+/lectures/\d+", url):
            raise TttConceptGraphError(f"Lesson {lesson.get('id')} has an invalid TTT URL")


def discover_timestamped_transcripts(root: Path) -> list[Path]:
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise TttConceptGraphError(f"Transcript root does not exist: {root}")
    paths = []
    for path in sorted(root.rglob("*.timestamped.txt")):
        relative = path.relative_to(root).as_posix()
        if ZOOM_RE.search(relative):
            continue
        paths.append(path)
    if not paths:
        raise TttConceptGraphError("No non-Zoom timestamped transcripts were found")
    return paths


def _inferred_depth(relative_path: str, title: str) -> str:
    value = f"{relative_path} {title}"
    if re.search(r"\bquick tips?\b", value, re.I):
        return "quick"
    if re.search(r"\badvanced\b", value, re.I):
        return "advanced"
    if APPLICATION_RE.search(value):
        return "application"
    if re.search(r"\b(?:basics?|explained|introduction|getting started)\b", value, re.I):
        return "foundation"
    return "focused"


def _semantic_stem(token: str) -> str:
    for suffix in ("ing", "ers", "ies", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def _semantic_tokens(value: object) -> set[str]:
    return {
        _semantic_stem(token)
        for token in re.findall(r"[a-z0-9]+", str(value or "").lower())
        if token not in SEMANTIC_STOP_WORDS and len(token) > 1
    }


def _semantic_seed_match(text: str, seeds: Sequence[str]) -> tuple[float, str, tuple[str, ...]]:
    cue_tokens = _semantic_tokens(text)
    best_score = 0.0
    best_seed = ""
    best_overlap: tuple[str, ...] = ()
    for seed in seeds:
        seed_tokens = _semantic_tokens(seed)
        overlap = tuple(sorted(cue_tokens & seed_tokens))
        if len(overlap) < 2:
            continue
        coverage = len(overlap) / len(seed_tokens)
        precision = len(overlap) / max(len(cue_tokens), 1)
        score = 0.75 * coverage + 0.25 * min(1.0, precision * 3)
        if score > best_score:
            best_score = score
            best_seed = str(seed)
            best_overlap = overlap
    return best_score, best_seed, best_overlap


def _role_for(cue: TranscriptCue, *, relative_path: str, confusion_patterns: Iterable[re.Pattern[str]]) -> str:
    text = cue.text
    if CONTRAST_RE.search(text) and any(pattern.search(text) for pattern in confusion_patterns):
        return "contrast"
    if DEFINITION_RE.search(text):
        return "definition"
    if APPLICATION_RE.search(relative_path) or re.search(r"\b(?:song|lick|solo|track|record)\b", text, re.I):
        return "application"
    if TROUBLESHOOT_RE.search(text):
        return "troubleshooting"
    if DEMONSTRATION_RE.search(text):
        return "demonstration"
    return "mention"


def _candidate_score(lesson: Mapping[str, Any], moment: Mapping[str, Any], concept: Mapping[str, Any]) -> tuple[int, int, int, str]:
    depth_points = {"quick": 80, "foundation": 70, "focused": 55, "advanced": 40, "application": 30}
    role_points = {"definition": 30, "demonstration": 22, "contrast": 20, "application": 16, "troubleshooting": 12, "mention": 0}
    title = str(lesson.get("title") or "")
    concept_id = str(concept.get("id") or "")
    explicit_dedicated = 300 if concept_id in (lesson.get("dedicatedConceptIds") or []) else 0
    title_dedicated = 80 if _concept_pattern(concept.get("aliases") or []).search(title) else 0
    curated_clarity = 20 if lesson.get("cataloged") is True else 0
    return (
        explicit_dedicated
        + title_dedicated
        + curated_clarity
        + depth_points.get(str(lesson.get("depth")), 0)
        + role_points.get(str(moment.get("role")), 0),
        -int(moment.get("startMs", 0)),
        -int(lesson.get("durationMs", 0) or 0),
        str(lesson.get("id") or ""),
    )


def compile_concept_graph(
    transcript_root: Path,
    taxonomy: Mapping[str, Any],
    catalog: Mapping[str, Any],
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    validate_taxonomy(taxonomy)
    validate_catalog(catalog)
    concepts = list(taxonomy["concepts"])
    concept_by_id = {str(item["id"]): item for item in concepts}
    known_concept_ids = set(concept_by_id)
    for lesson in catalog["lessons"]:
        unknown = set(map(str, lesson.get("dedicatedConceptIds") or [])) - known_concept_ids
        if unknown:
            raise TttConceptGraphError(f"Lesson {lesson.get('id')} has unknown dedicated concepts: {sorted(unknown)}")
    concept_patterns = {concept_id: _concept_pattern(item.get("aliases") or []) for concept_id, item in concept_by_id.items()}
    catalog_by_slug = {_normalized(item["sourceSlug"]): dict(item) for item in catalog["lessons"]}
    paths = discover_timestamped_transcripts(transcript_root)
    if limit is not None:
        paths = paths[: max(0, int(limit))]

    lessons: list[dict[str, Any]] = []
    mentions: list[dict[str, Any]] = []
    review_queue: list[dict[str, Any]] = []
    transcript_root = Path(transcript_root).expanduser().resolve()
    for path in paths:
        relative_path = path.relative_to(transcript_root).as_posix()
        source_slug = _normalized(path.name.removesuffix(".timestamped.txt"))
        catalog_lesson = dict(catalog_by_slug.get(source_slug) or {})
        lesson_id = str(catalog_lesson.get("id") or f"ttt-source-{stable_id(relative_path)}")
        title = str(catalog_lesson.get("title") or path.name.removesuffix(".timestamped.txt").replace("-", " "))
        cues = parse_timestamped_transcript(path)
        lesson = {
            "id": lesson_id,
            "title": title,
            "sourceSlug": source_slug,
            "sourceRelpath": relative_path,
            "sourceSha256": sha256_file(path),
            "durationMs": int(catalog_lesson.get("durationMs") or cues[-1].end_ms),
            "depth": catalog_lesson.get("depth") or _inferred_depth(relative_path, title),
            "cataloged": bool(catalog_lesson),
            "dedicatedConceptIds": list(catalog_lesson.get("dedicatedConceptIds") or []),
            "url": catalog_lesson.get("url"),
            "isZoom": False,
        }
        lessons.append(lesson)
        for cue in cues:
            exact_concept_ids = [concept_id for concept_id, pattern in concept_patterns.items() if pattern.search(cue.text)]
            cue_roles: dict[str, str] = {}
            for concept_id in exact_concept_ids:
                concept = concept_by_id[concept_id]
                confusion_patterns = [
                    concept_patterns[item]
                    for item in concept.get("confusionConceptIds") or []
                    if item in concept_patterns
                ]
                role = _role_for(cue, relative_path=relative_path, confusion_patterns=confusion_patterns)
                cue_roles[concept_id] = role
                publication_eligible = role != "mention" or concept_id in lesson["dedicatedConceptIds"]
                mentions.append(
                    {
                        "id": f"mention-{stable_id(lesson_id, concept_id, cue.start_ms, cue.end_ms)}",
                        "lessonId": lesson_id,
                        "conceptId": concept_id,
                        "startMs": cue.start_ms,
                        "endMs": cue.end_ms,
                        "role": role,
                        "matchMethod": "exact_alias",
                        "publicationEligible": publication_eligible,
                        "evidence": cue.text,
                        "evidenceSha256": sha256_bytes(cue.text.encode("utf-8")),
                        "exactCueValidated": True,
                    }
                )

            semantic_candidates: list[dict[str, Any]] = []
            for concept_id, concept in concept_by_id.items():
                if concept_id in exact_concept_ids:
                    continue
                score, seed, overlap = _semantic_seed_match(cue.text, concept.get("semanticSeeds") or [])
                if score < SEMANTIC_REVIEW_THRESHOLD:
                    continue
                semantic_candidates.append(
                    {
                        "conceptId": concept_id,
                        "score": round(score, 3),
                        "semanticSeed": seed,
                        "overlapTokens": list(overlap),
                    }
                )
            semantic_candidates.sort(key=lambda item: (-float(item["score"]), str(item["conceptId"])))
            if semantic_candidates:
                top_score = float(semantic_candidates[0]["score"])
                finalists = [item for item in semantic_candidates if top_score - float(item["score"]) <= 0.06]
                reason = "ambiguous_semantic_match" if len(finalists) > 1 else "implied_concept_candidate"
                for candidate in finalists:
                    review_queue.append(
                        {
                            "id": f"review-{stable_id(lesson_id, cue.start_ms, cue.end_ms, candidate['conceptId'], reason)}",
                            "lessonId": lesson_id,
                            "conceptId": candidate["conceptId"],
                            "startMs": cue.start_ms,
                            "endMs": cue.end_ms,
                            "reason": reason,
                            "status": "review_required",
                            "score": candidate["score"],
                            "semanticSeed": candidate["semanticSeed"],
                            "overlapTokens": candidate["overlapTokens"],
                            "evidence": cue.text,
                            "evidenceSha256": sha256_bytes(cue.text.encode("utf-8")),
                            "exactCueValidated": True,
                            "autoPublishAllowed": False,
                        }
                    )

            if CORRECTION_RE.search(cue.text):
                review_queue.append(
                    {
                        "id": f"review-{stable_id(lesson_id, cue.start_ms, cue.end_ms, 'musical-correction')}",
                        "lessonId": lesson_id,
                        "conceptId": None,
                        "startMs": cue.start_ms,
                        "endMs": cue.end_ms,
                        "reason": "possible_musical_correction",
                        "status": "review_required",
                        "evidence": cue.text,
                        "evidenceSha256": sha256_bytes(cue.text.encode("utf-8")),
                        "exactCueValidated": True,
                        "autoPublishAllowed": False,
                    }
                )

            exact_set = set(exact_concept_ids)
            confusion_pairs = {
                tuple(sorted((concept_id, str(confusion_id))))
                for concept_id in exact_set
                for confusion_id in concept_by_id[concept_id].get("confusionConceptIds") or []
                if str(confusion_id) in exact_set
            }
            if confusion_pairs and not any(role == "contrast" for role in cue_roles.values()):
                for pair in sorted(confusion_pairs):
                    review_queue.append(
                        {
                            "id": f"review-{stable_id(lesson_id, cue.start_ms, cue.end_ms, *pair)}",
                            "lessonId": lesson_id,
                            "conceptIds": list(pair),
                            "startMs": cue.start_ms,
                            "endMs": cue.end_ms,
                            "reason": "confusion_pair_requires_role_review",
                            "status": "review_required",
                            "evidence": cue.text,
                            "evidenceSha256": sha256_bytes(cue.text.encode("utf-8")),
                            "exactCueValidated": True,
                            "autoPublishAllowed": False,
                        }
                    )

    lessons.sort(key=lambda item: str(item["id"]))
    mentions.sort(key=lambda item: (str(item["lessonId"]), int(item["startMs"]), str(item["conceptId"])))
    lesson_by_id = {str(item["id"]): item for item in lessons}
    recommendations: list[dict[str, Any]] = []
    for concept in concepts:
        concept_id = str(concept["id"])
        best_by_lesson: dict[str, dict[str, Any]] = {}
        for moment in (
            item
            for item in mentions
            if item["conceptId"] == concept_id and item.get("publicationEligible") is True
        ):
            lesson = lesson_by_id[str(moment["lessonId"])]
            current = best_by_lesson.get(str(lesson["id"]))
            if current is None or _candidate_score(lesson, moment, concept) > _candidate_score(lesson, current, concept):
                best_by_lesson[str(lesson["id"])] = moment
        ranked = sorted(
            best_by_lesson.values(),
            key=lambda item: _candidate_score(lesson_by_id[str(item["lessonId"])], item, concept),
            reverse=True,
        )[:8]
        for rank, moment in enumerate(ranked, start=1):
            target = lesson_by_id[str(moment["lessonId"])]
            recommendations.append(
                {
                    "conceptId": concept_id,
                    "rank": rank,
                    "lessonId": target["id"],
                    "momentId": moment["id"],
                    "startMs": moment["startMs"],
                    "endMs": moment["endMs"],
                    "role": moment["role"],
                    "depth": target["depth"],
                    "exactCueValidated": True,
                    "dedicatedLesson": concept_id in (target.get("dedicatedConceptIds") or []),
                }
            )

    ranking_audit: list[dict[str, Any]] = []
    for concept in concepts:
        concept_id = str(concept["id"])
        dedicated_lessons_with_evidence = {
            str(lesson["id"])
            for lesson in lessons
            if concept_id in (lesson.get("dedicatedConceptIds") or [])
            and any(
                mention["lessonId"] == lesson["id"]
                and mention["conceptId"] == concept_id
                and mention.get("publicationEligible") is True
                for mention in mentions
            )
        }
        top = next((item for item in recommendations if item["conceptId"] == concept_id and item["rank"] == 1), None)
        passed = not dedicated_lessons_with_evidence or (
            top is not None and str(top["lessonId"]) in dedicated_lessons_with_evidence
        )
        ranking_audit.append(
            {
                "conceptId": concept_id,
                "dedicatedLessonsWithEvidence": sorted(dedicated_lessons_with_evidence),
                "topLessonId": top.get("lessonId") if top else None,
                "dedicatedFirstPassed": passed,
            }
        )
        if not passed:
            raise TttConceptGraphError(f"Dedicated-lesson ranking invariant failed for {concept_id}")

    review_queue.sort(
        key=lambda item: (
            str(item["lessonId"]),
            int(item["startMs"]),
            str(item.get("reason") or ""),
            str(item.get("conceptId") or item.get("conceptIds") or ""),
        )
    )

    payload: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "buildVersion": BUILD_VERSION,
        "sourcePolicy": {
            "nonZoomOnly": True,
            "rawTranscriptDeployable": False,
            "commentsIncluded": False,
            "modelCallsAllowedAtRuntime": False,
            "authoringDiscoveryMode": "offline_semantic_token_overlap",
            "semanticCandidatesAutoPublished": False,
            "reviewQueueIsPrivate": True,
        },
        "concepts": concepts,
        "lessons": lessons,
        "mentions": mentions,
        "recommendations": recommendations,
        "reviewQueue": review_queue,
        "rankingAudit": ranking_audit,
        "counts": {
            "concepts": len(concepts),
            "lessons": len(lessons),
            "mentions": len(mentions),
            "recommendations": len(recommendations),
            "publicationEligibleMentions": sum(item.get("publicationEligible") is True for item in mentions),
            "reviewQueue": len(review_queue),
        },
        "graphSha256": "",
    }
    payload["graphSha256"] = sha256_bytes(canonical_json_bytes(payload))
    return payload


def graph_report(graph: Mapping[str, Any]) -> dict[str, Any]:
    roles: dict[str, int] = {}
    for mention in graph.get("mentions") or []:
        role = str(mention.get("role") or "unknown")
        roles[role] = roles.get(role, 0) + 1
    review_reasons: dict[str, int] = {}
    for item in graph.get("reviewQueue") or []:
        reason = str(item.get("reason") or "unknown")
        review_reasons[reason] = review_reasons.get(reason, 0) + 1
    ranking_audit = list(graph.get("rankingAudit") or [])
    return {
        "schemaVersion": graph.get("schemaVersion"),
        "buildVersion": graph.get("buildVersion"),
        "graphSha256": graph.get("graphSha256"),
        "counts": graph.get("counts"),
        "roles": dict(sorted(roles.items())),
        "reviewReasons": dict(sorted(review_reasons.items())),
        "dedicatedFirstPassed": all(item.get("dedicatedFirstPassed") is True for item in ranking_audit),
        "nonZoomOnly": all(item.get("isZoom") is False for item in graph.get("lessons") or []),
        "rawTranscriptDeployable": False,
    }
