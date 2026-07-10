"""Structured E9 melody and arrangement teaching for Melody Exercise v0.

Copyright status is not a routing or refusal boundary in this module.  The
boundary is accuracy: exact transcription needs identified source material,
while user-entered notes and scale degrees can be placed deterministically.
Long inputs are divided into small lesson sections instead of being rejected.
"""

from __future__ import annotations

import math
import os
import re
from typing import Any, Mapping
from urllib.parse import urlparse

from pocketsteel.melody_arranger import SUPPORTED_CONTOURS, SUPPORTED_TEXTURES, arrange_melody_routes


ENABLE_MELODY_EXERCISE_ENV = "STEEL_RAG_ENABLE_MELODY_EXERCISE"
MELODY_SCHEMA_VERSION = "melody_exercise_v0"
MAX_EVENTS_PER_SECTION = 8
SUPPORTED_KINDS = {
    "original_exercise",
    "user_melody",
    "artist_solo_lesson",
    "song_arrangement_lesson",
}
SUPPORTED_RENDERING_MODES = {
    "transcription",
    "e9_adaptation",
    "teaching_simplification",
}
SUPPORTED_ACCURACY = {"exact", "approximate", "interpretive"}
SUPPORTED_KEYS = {"G", "C"}

_TEACHING_REQUEST_RE = re.compile(
    r"\b(?:tab|tablature|transcrib\w*|arrang\w*|teach|learn|play)\b.*"
    r"\b(?:song|solo|recording|youtube|video|artist|version|arrangement|rag)\b|"
    r"\b(?:whole|full|entire)\b.*\b(?:song|solo|arrangement|tab)\b|"
    r"\bsolo\s+(?:from|on|by)\b",
    re.I,
)


class MelodyExerciseError(ValueError):
    """A user-correctable structured Melody Exercise request error."""


def configured_melody_exercise_enabled(env: Mapping[str, str] | None = None) -> bool:
    value = (env or os.environ).get(ENABLE_MELODY_EXERCISE_ENV, "")
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def is_melody_teaching_request(question: str) -> bool:
    return bool(_TEACHING_REQUEST_RE.search(str(question or "")))


def melody_exercise_response(
    question: str,
    request: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Build a teaching response from structured input or a song/solo request."""

    structured = dict(request or {})
    if not structured and not is_melody_teaching_request(question):
        return None

    kind = _choice(structured.get("kind"), SUPPORTED_KINDS, _kind_for_question(question))
    material = _material_payload(structured, question)
    if kind == "original_exercise":
        material = {}
    raw_melody = structured.get("melody") or structured.get("tokens") or structured.get("events")
    if not isinstance(raw_melody, list) or not raw_melody:
        return _needs_source_response(question, kind, material, structured)

    key = str(structured.get("key") or "G").strip().upper()
    if key not in SUPPORTED_KEYS:
        raise MelodyExerciseError("Melody Exercise v0 currently supports the keys of G and C.")
    tuning = str(structured.get("tuning") or "E9").strip().upper()
    if tuning != "E9":
        raise MelodyExerciseError("Melody Exercise v0 currently supports E9 tuning only.")

    tokens = [_melody_token(item) for item in raw_melody]
    if any(not token and not (isinstance(item, Mapping) and "string" in item and "fret" in item) for token, item in zip(tokens, raw_melody)):
        raise MelodyExerciseError("Each melody event needs a note name or scale degree from 1 through 7.")
    section_number = _positive_int(structured.get("sectionNumber") or structured.get("section_number"), 1)
    total_sections = max(1, math.ceil(len(tokens) / MAX_EVENTS_PER_SECTION))
    if section_number > total_sections:
        raise MelodyExerciseError(f"Section {section_number} is outside this {total_sections}-section melody.")
    start = (section_number - 1) * MAX_EVENTS_PER_SECTION
    section_tokens = tokens[start : start + MAX_EVENTS_PER_SECTION]

    rendering_mode = _choice(
        structured.get("renderingMode") or structured.get("rendering_mode"),
        SUPPORTED_RENDERING_MODES,
        "e9_adaptation" if kind in {"artist_solo_lesson", "song_arrangement_lesson"} else "teaching_simplification",
    )
    requested_accuracy = _choice(structured.get("accuracy"), SUPPORTED_ACCURACY, "")
    source_identified = bool(material.get("sourceUrl") or material.get("recording") or structured.get("sourceProvided"))
    if requested_accuracy == "exact" and kind in {"artist_solo_lesson", "song_arrangement_lesson"} and not source_identified:
        accuracy = "approximate"
        accuracy_note = "Exact transcription needs an identified recording or user-supplied passage; this placement is an E9 teaching adaptation."
    else:
        accuracy = requested_accuracy or ("exact" if kind in {"original_exercise", "user_melody"} else "approximate")
        accuracy_note = (
            "The notes match the structured input; fret and string placement is deterministic for the selected key."
            if accuracy == "exact"
            else "Treat this as a teaching interpretation until it is checked against the identified recording."
        )

    tab_id = f"melody-{key.lower()}-section-{section_number}"
    title = _exercise_title(kind, material, key, section_number)
    contour_mode = str(structured.get("contourMode") or structured.get("contour_mode") or "closest_playable").strip().lower()
    if contour_mode not in SUPPORTED_CONTOURS:
        raise MelodyExerciseError("Contour mode must be closest playable, ascending, descending, or preserve input.")
    texture = str(structured.get("texture") or "both").strip().lower()
    if texture not in SUPPORTED_TEXTURES:
        raise MelodyExerciseError("Unsupported Melody Studio texture.")
    try:
        routes, resolved_phrase = arrange_melody_routes(
            raw_melody,
            key=key,
            contour_mode=contour_mode,
            texture=texture,
            route_id_prefix=tab_id,
            title=title,
            event_start=start,
            event_end=start + MAX_EVENTS_PER_SECTION,
        )
    except ValueError as exc:
        raise MelodyExerciseError(str(exc)) from exc
    selected_route = routes[0]
    event_payloads = selected_route["events"]
    tab_example = selected_route["tabExample"]
    fretboard = selected_route["fretboard"]

    exercise = {
        "schemaVersion": MELODY_SCHEMA_VERSION,
        "id": tab_example["id"],
        "status": "ready",
        "kind": kind,
        "title": title,
        "material": material,
        "renderingMode": rendering_mode,
        "accuracy": {
            "label": accuracy,
            "confidence": "high" if accuracy == "exact" else "medium",
            "note": accuracy_note,
        },
        "section": {
            "number": section_number,
            "total": total_sections,
            "label": str(material.get("section") or f"Section {section_number}"),
            "hasMore": section_number < total_sections,
            "nextSection": section_number + 1 if section_number < total_sections else None,
        },
        "input": {
            "key": key,
            "tuning": "E9",
            "tokens": section_tokens,
            "contourMode": contour_mode,
            "texture": texture,
            "resolvedPhrase": resolved_phrase,
        },
        "events": event_payloads,
        "routes": routes,
        "selectedRouteId": selected_route["id"],
        "validation": {
            "ok": True,
            "mechanical": [],
            "musical": ["Melody contour and harmony routes are octave-aware and pitch validated."],
            "steelPractical": [],
            "accuracy": [accuracy_note],
        },
    }
    answer = _ready_answer(exercise)
    return {
        "answer": answer,
        "melody_exercise": exercise,
        "tab_example": tab_example,
        "fretboard": fretboard,
        "sources": _source_cards(material),
        "warnings": [],
    }


def _needs_source_response(
    question: str,
    kind: str,
    material: dict[str, str],
    request: Mapping[str, Any],
) -> dict[str, Any]:
    rendering_mode = _choice(
        request.get("renderingMode") or request.get("rendering_mode"),
        SUPPORTED_RENDERING_MODES,
        "transcription" if "transcrib" in question.lower() else "e9_adaptation",
    )
    title = _exercise_title(kind, material, str(request.get("key") or "G").upper(), 1)
    source_label = _material_label(material) or "that solo or arrangement"
    answer = (
        f"Yes—I can teach {source_label} on E9. I’ll divide longer material into numbered sections and start with Section 1.\n\n"
        "To keep the notes honest, send the recording or video link, upload the passage, paste the notes/tab, or name the exact artist, version, and section. "
        "Once the source is identified, I can provide a faithful transcription, an E9 adaptation, or a simplified teaching arrangement."
    )
    exercise = {
        "schemaVersion": MELODY_SCHEMA_VERSION,
        "id": "melody-source-needed",
        "status": "needs_source",
        "kind": kind,
        "title": title,
        "material": material,
        "renderingMode": rendering_mode,
        "accuracy": {
            "label": "approximate",
            "confidence": "low",
            "note": "No exact notes are shown until the recording or passage is identified.",
        },
        "section": {"number": 1, "total": None, "label": str(material.get("section") or "Section 1"), "hasMore": True, "nextSection": 2},
        "events": [],
        "validation": {"ok": False, "mechanical": [], "musical": [], "steelPractical": [], "accuracy": ["Source material needed."]},
    }
    return {
        "answer": answer,
        "melody_exercise": exercise,
        "sources": _source_cards(material),
        "warnings": [],
    }


def _melody_token(item: Any) -> str:
    if isinstance(item, Mapping):
        return str(item.get("token") or item.get("note") or item.get("degree") or "").strip()
    return str(item or "").strip()


def _material_payload(value: Any, question: str) -> dict[str, str]:
    request = value if isinstance(value, Mapping) else {}
    nested = request.get("material")
    source = dict(request)
    if isinstance(nested, Mapping):
        source.update(nested)
    material = {
        "artist": _text(source.get("artist")),
        "song": _text(source.get("song") or source.get("title")),
        "recording": _text(source.get("recording") or source.get("version")),
        "section": _text(source.get("section")),
        "sourceUrl": _safe_url(source.get("sourceUrl") or source.get("source_url") or source.get("url")),
        "sourceReference": _text(source.get("sourceReference") or source.get("source_reference")),
    }
    if not any(material.values()):
        material["sourceReference"] = _text(question)
    return {key: value for key, value in material.items() if value}


def _source_cards(material: Mapping[str, str]) -> list[dict[str, Any]]:
    url = str(material.get("sourceUrl") or "")
    if not url:
        return []
    title = _material_label(material) or "Teaching source"
    return [
        {
            "title": title,
            "forumName": "Recording / arrangement reference",
            "url": url,
            "excerpt": "Source reference supplied for this teaching transcription or E9 adaptation.",
            "score": 1.0,
            "chunkId": "melody-source-reference",
            "postUid": None,
        }
    ]


def _kind_for_question(question: str) -> str:
    lowered = question.lower()
    if "solo" in lowered:
        return "artist_solo_lesson"
    if any(term in lowered for term in ("song", "arrangement", "tab", "tablature", "rag")):
        return "song_arrangement_lesson"
    return "user_melody"


def _exercise_title(kind: str, material: Mapping[str, str], key: str, section: int) -> str:
    label = _material_label(material)
    if label:
        return f"{label} — Section {section} E9 lesson"
    kind_label = {
        "artist_solo_lesson": "Artist solo lesson",
        "song_arrangement_lesson": "Song arrangement lesson",
        "original_exercise": "Original melody exercise",
        "user_melody": "Your melody exercise",
    }[kind]
    return f"{kind_label} in {key}"


def _material_label(material: Mapping[str, str]) -> str:
    artist = str(material.get("artist") or "")
    song = str(material.get("song") or "")
    recording = str(material.get("recording") or "")
    label = " — ".join(value for value in (artist, song) if value)
    if recording:
        label = f"{label} ({recording})" if label else recording
    return label


def _ready_answer(exercise: Mapping[str, Any]) -> str:
    section = exercise["section"]
    accuracy = exercise["accuracy"]
    continuation = (
        f" Continue with Section {section['nextSection']} when this section is clean."
        if section.get("hasMore")
        else ""
    )
    return (
        f"Here is {exercise['title']}. The tab, event steps, and fretboard all use the same validated E9 notes.\n\n"
        f"Accuracy: {str(accuracy['label']).title()} ({accuracy['confidence']} confidence). {accuracy['note']}\n\n"
        "Practice one event at a time, keep the bar centered, and connect the notes only after each pitch is clean."
        f"{continuation}"
    )


def _choice(value: Any, allowed: set[str], default: str) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in allowed else default


def _positive_int(value: Any, default: int) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return default


def _safe_url(value: Any) -> str:
    text = _text(value)
    if not text:
        return ""
    parsed = urlparse(text)
    return text if parsed.scheme in {"http", "https"} and parsed.netloc else ""


def _text(value: Any) -> str:
    return str(value or "").strip()
