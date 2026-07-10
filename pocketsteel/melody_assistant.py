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

from pocketsteel.answer_tab_examples import fretboard_payload_for_tab_example
from pocketsteel.tab_engine import TabEvent, TabNote, default_e9_copedent_profile, render_tab


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

_KEY_PLACEMENTS: dict[str, dict[str, Any]] = {
    "G": {
        "notes": ("G", "A", "B", "C", "D", "E", "F#"),
        "string": 4,
        "frets": {"G": 3, "A": 5, "B": 7, "C": 8, "D": 10, "E": 12, "F#": 14},
    },
    "C": {
        "notes": ("C", "D", "E", "F", "G", "A", "B"),
        "string": 5,
        "frets": {"C": 1, "D": 3, "E": 5, "F": 6, "G": 8, "A": 10, "B": 12},
    },
}

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
    if key not in _KEY_PLACEMENTS:
        raise MelodyExerciseError("Melody Exercise v0 currently supports the keys of G and C.")
    tuning = str(structured.get("tuning") or "E9").strip().upper()
    if tuning != "E9":
        raise MelodyExerciseError("Melody Exercise v0 currently supports E9 tuning only.")

    tokens = [_melody_token(item) for item in raw_melody]
    if any(not token for token in tokens):
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

    events, interval_rows = _events_for_tokens(section_tokens, key)
    tab_result = render_tab(tuple(event["tabEvent"] for event in events))
    if not tab_result.ok:
        raise MelodyExerciseError("The requested phrase did not pass E9 mechanical validation.")

    profile = default_e9_copedent_profile()
    tab_id = f"melody-{key.lower()}-section-{section_number}"
    event_payloads: list[dict[str, Any]] = []
    for event in events:
        payload = event["tabEvent"].normalized(profile).to_dict()
        payload.update(
            {
                "id": event["id"],
                "step": event["step"],
                "inputToken": event["inputToken"],
                "resolvedNote": event["resolvedNote"],
                "scaleDegree": event["scaleDegree"],
                "technique": "pick",
                "explanation": event["explanation"],
                "renderablePositionId": f"{tab_id}-event-{event['step']}",
            }
        )
        event_payloads.append(payload)

    title = _exercise_title(kind, material, key, section_number)
    tab_example = {
        "id": tab_id,
        "title": title,
        "kind": "melody_exercise",
        "display_tab": True,
        "preferred_display": "tab_and_fretboard",
        "context": {
            "key": key,
            "tuning": "E9",
            "profile": profile.id,
            "difficulty": str(structured.get("difficulty") or "beginner"),
            "materialKind": kind,
            "renderingMode": rendering_mode,
            "section": section_number,
        },
        "rendered_tab": tab_result.tab,
        "validation": {
            "ok": True,
            "issues": [],
            "profile": profile.id,
            "eventCount": len(event_payloads),
        },
        "explanation": "The tab, step list, and fretboard use the same mechanically validated E9 events.",
        "intervals": interval_rows,
        "events": event_payloads,
    }
    fretboard = fretboard_payload_for_tab_example(tab_example)
    if fretboard is None:
        raise MelodyExerciseError("The requested phrase could not produce a synchronized fretboard payload.")

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
        "input": {"key": key, "tuning": "E9", "tokens": section_tokens},
        "events": event_payloads,
        "validation": {
            "ok": True,
            "mechanical": [],
            "musical": [],
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


def _events_for_tokens(tokens: list[str], key: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    placement = _KEY_PLACEMENTS[key]
    scale_notes = placement["notes"]
    string_number = int(placement["string"])
    events: list[dict[str, Any]] = []
    intervals: list[dict[str, Any]] = []
    for index, token in enumerate(tokens, start=1):
        note, degree = _resolve_token(token, scale_notes)
        fret = int(placement["frets"][note])
        event_id = f"melody-step-{index}"
        tab_event = TabEvent(
            notes=(TabNote(string=string_number, fret=fret),),
            chord=note,
            lyric=f"step {index}",
            comment=f"Scale degree {degree} in {key}",
        )
        events.append(
            {
                "id": event_id,
                "step": index,
                "inputToken": token,
                "resolvedNote": note,
                "scaleDegree": degree,
                "explanation": f"Play {note}, scale degree {degree} in {key}, on string {string_number} at fret {fret}.",
                "tabEvent": tab_event,
            }
        )
        intervals.append({"eventId": event_id, "chord": note, "byString": {str(string_number): degree}})
    return events, intervals


def _resolve_token(token: str, scale_notes: tuple[str, ...]) -> tuple[str, str]:
    normalized = token.strip().upper().replace("♯", "#").replace("♭", "B")
    if normalized.isdigit() and 1 <= int(normalized) <= 7:
        degree = int(normalized)
        return scale_notes[degree - 1], str(degree)
    display = normalized[0] + normalized[1:].replace("B", "b") if normalized else normalized
    for index, note in enumerate(scale_notes, start=1):
        if display.upper() == note.upper():
            return note, str(index)
    raise MelodyExerciseError(f"{token!r} is not in the selected major scale for Melody Exercise v0.")


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
