"""Structured E9 melody and arrangement teaching for Melody Exercise v0.

Copyright status is not a routing or refusal boundary in this module.  The
boundary is accuracy: exact transcription needs identified source material,
while user-entered notes and scale degrees can be placed deterministically.
Long inputs are divided into small lesson sections instead of being rejected.
"""

from __future__ import annotations

import os
import re
from typing import Any, Mapping
from urllib.parse import urlparse

from pocketsteel.amazing_tablature_model import RuntimeRankerPolicy
from pocketsteel.amazing_tablature_product import (
    build_arrangement_contract,
    resolve_arrangement_preferences,
)
from pocketsteel.amazing_tablature_runtime import (
    arrange_melody_routes_with_private_beta,
)
from pocketsteel.melody_arranger import SUPPORTED_CONTOURS, SUPPORTED_TEXTURES
from pocketsteel.melody_decision_rules import (
    MODEL_STATUS,
    MODEL_VERSION,
    normalize_style_family,
    rule_contract_payload,
    style_catalog_payload,
    style_descriptor,
)


ENABLE_MELODY_EXERCISE_ENV = "STEEL_RAG_ENABLE_MELODY_EXERCISE"
MELODY_SCHEMA_VERSION = "melody_exercise_v0"
MAX_EVENTS_PER_SECTION = 16
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
SUPPORTED_CONFIDENCE = {"low", "medium", "high"}
SUPPORTED_KEYS = {
    "C",
    "Db",
    "D",
    "Eb",
    "E",
    "F",
    "F#",
    "G",
    "Ab",
    "A",
    "Bb",
    "B",
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
    *,
    ranker_policy: RuntimeRankerPolicy | None = None,
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

    key = _normalize_key(structured.get("key") or "G")
    if key not in SUPPORTED_KEYS:
        raise MelodyExerciseError("Amazing Tablature needs a major key from C through B.")
    tuning = str(structured.get("tuning") or "E9").strip().upper()
    if tuning != "E9":
        raise MelodyExerciseError("Melody Exercise v0 currently supports E9 tuning only.")

    tokens = [_melody_token(item) for item in raw_melody]
    if any(not token and not (isinstance(item, Mapping) and "string" in item and "fret" in item) for token, item in zip(tokens, raw_melody)):
        raise MelodyExerciseError("Each melody event needs a note name or scale degree from 1 through 7.")
    whole_song = bool(structured.get("wholeSong") or structured.get("whole_song"))
    sections = (
        [{
            "label": "Complete song",
            "eventStart": 0,
            "eventEnd": len(raw_melody),
            "measureStart": _first_measure(raw_melody),
            "measureEnd": _last_measure(raw_melody),
        }]
        if whole_song
        else _section_spans(raw_melody, structured.get("sections"))
    )
    section_number = _positive_int(structured.get("sectionNumber") or structured.get("section_number"), 1)
    total_sections = len(sections)
    if section_number > total_sections:
        raise MelodyExerciseError(f"Section {section_number} is outside this {total_sections}-section melody.")
    section_span = sections[section_number - 1]
    start = section_span["eventStart"]
    end = section_span["eventEnd"]
    section_tokens = tokens[start:end]

    rendering_mode = _choice(
        structured.get("renderingMode") or structured.get("rendering_mode"),
        SUPPORTED_RENDERING_MODES,
        "e9_adaptation" if kind in {"artist_solo_lesson", "song_arrangement_lesson"} else "teaching_simplification",
    )
    requested_accuracy = _choice(structured.get("accuracy"), SUPPORTED_ACCURACY, "")
    source_identified = bool(material.get("sourceUrl") or material.get("recording") or structured.get("sourceProvided"))
    requested_confidence = _choice(
        structured.get("accuracyConfidence") or structured.get("accuracy_confidence"),
        SUPPORTED_CONFIDENCE,
        "",
    )
    requested_accuracy_note = str(structured.get("accuracyNote") or structured.get("accuracy_note") or "").strip()[:320]
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
    if requested_accuracy_note and accuracy != "exact":
        accuracy_note = requested_accuracy_note

    tab_id = f"melody-{key.lower()}-section-{section_number}"
    title = _exercise_title(kind, material, key, section_number, whole_song=whole_song)
    contour_mode = str(structured.get("contourMode") or structured.get("contour_mode") or "closest_playable").strip().lower()
    if contour_mode not in SUPPORTED_CONTOURS:
        raise MelodyExerciseError("Contour mode must be closest playable, ascending, descending, or preserve input.")
    try:
        arrangement_preferences = resolve_arrangement_preferences(structured)
    except ValueError as exc:
        raise MelodyExerciseError(str(exc)) from exc
    texture = arrangement_preferences.arranger_texture
    if texture not in SUPPORTED_TEXTURES:
        raise MelodyExerciseError("Unsupported Amazing Tablature voice mode.")
    meter = str(structured.get("meter") or "4/4").strip()
    if meter not in {"3/4", "4/4"}:
        meter = "4/4"
    try:
        pickup_beats = max(0.0, min(3.0, float(structured.get("pickupBeats") or structured.get("pickup_beats") or 0)))
    except (TypeError, ValueError):
        pickup_beats = 0.0
    source_copedent_id = str(
        structured.get("sourceCopedentId") or structured.get("source_copedent_id") or ""
    ).strip() or None
    target_copedent_id = str(
        structured.get("targetCopedentId") or structured.get("target_copedent_id") or ""
    ).strip() or None
    target_copedent = structured.get("targetCopedent") or structured.get("target_copedent")
    if target_copedent is not None and not isinstance(target_copedent, Mapping):
        raise MelodyExerciseError("A saved target copedent must be a structured profile.")
    try:
        style_family = normalize_style_family(arrangement_preferences.arranger_style)
    except ValueError as exc:
        raise MelodyExerciseError(str(exc)) from exc
    try:
        routes, resolved_phrase, model_metadata = arrange_melody_routes_with_private_beta(
            raw_melody,
            policy=ranker_policy,
            key=key,
            contour_mode=contour_mode,
            texture=texture,
            route_id_prefix=tab_id,
            title=title,
            event_start=start,
            event_end=end,
            meter=meter,
            pickup_beats=pickup_beats,
            sections=structured.get("sections") if isinstance(structured.get("sections"), list) else None,
            source_copedent_id=source_copedent_id,
            target_copedent_id=target_copedent_id,
            target_copedent=target_copedent,
            style_family=style_family,
        )
    except ValueError as exc:
        raise MelodyExerciseError(str(exc)) from exc
    all_routes = routes
    public_routes, arrangement_contract = build_arrangement_contract(
        routes,
        preferences=arrangement_preferences,
        model_metadata=model_metadata,
    )
    selected_route = next(
        route
        for route in public_routes
        if route["id"] == arrangement_contract["recommendedRouteId"]
    )
    faithful_route = next(
        (route for route in all_routes if route["harmonyType"] == "single_note"),
        selected_route,
    )
    selected_style = style_descriptor(style_family)
    # Preserve the established backend contract: ``events`` is the literal
    # melody line. Product clients use ``selectedRouteId`` for the recommended
    # Amazing Tablature rendering.
    event_payloads = faithful_route["events"]
    tab_example = faithful_route["tabExample"]
    fretboard = faithful_route["fretboard"]

    decision_rules = rule_contract_payload(style_family)
    decision_rules["modelMetadata"] = model_metadata
    exercise = {
        "schemaVersion": MELODY_SCHEMA_VERSION,
        "id": tab_example["id"],
        "status": "ready",
        "kind": kind,
        "title": title,
        "material": material,
        "renderingMode": rendering_mode,
        "sourceCopedentId": selected_route["sourceCopedentId"],
        "targetCopedentId": selected_route["targetCopedentId"],
        "targetCopedentLabel": selected_route["arrangedFor"],
        "arrangedFor": selected_route["arrangedFor"],
        "styleFamily": style_family,
        "styleLabel": selected_style["label"],
        "styleReason": selected_style["reason"],
        "styleCatalog": style_catalog_payload(),
        "decisionModelVersion": MODEL_VERSION,
        "decisionModelStatus": MODEL_STATUS,
        "decisionRules": decision_rules,
        "accuracy": {
            "label": accuracy,
            "confidence": requested_confidence or ("high" if accuracy == "exact" else "medium"),
            "note": accuracy_note,
        },
        "section": {
            "number": section_number,
            "total": total_sections,
            "label": section_span["label"],
            "hasMore": section_number < total_sections,
            "previousSection": section_number - 1 if section_number > 1 else None,
            "nextSection": section_number + 1 if section_number < total_sections else None,
            "eventStart": start,
            "eventEnd": end,
            "measureStart": section_span.get("measureStart"),
            "measureEnd": section_span.get("measureEnd"),
        },
        "input": {
            "key": key,
            "tuning": "E9",
            "tokens": section_tokens,
            "contourMode": contour_mode,
            "texture": texture,
            "voiceMode": arrangement_preferences.voice_mode,
            "movementMode": arrangement_preferences.movement_mode,
            "meter": meter,
            "pickupBeats": pickup_beats,
            "resolvedPhrase": resolved_phrase,
            "sourceCopedentId": selected_route["sourceCopedentId"],
            "targetCopedentId": selected_route["targetCopedentId"],
            "styleFamily": style_family,
        },
        "events": event_payloads,
        # ``routes`` remains the full internal/legacy candidate ledger so
        # evaluation can compare learned and deterministic candidates.
        # Product clients consume ``publicRoutes``, which removes exact
        # duplicates and only presents materially different choices.
        "routes": all_routes,
        "publicRoutes": public_routes,
        "selectedRouteId": selected_route["id"],
        "arrangementContract": arrangement_contract,
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
        "tabs": [route["tabExample"] for route in public_routes[:3]],
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
        return str(item.get("token") or item.get("note") or item.get("degree") or item.get("pitch") or "").strip()
    return str(item or "").strip()


def _normalize_key(value: Any) -> str:
    text = str(value or "G").strip().replace("♯", "#").replace("♭", "b")
    aliases = {
        "C#": "Db",
        "D#": "Eb",
        "G#": "Ab",
        "A#": "Bb",
        "Gb": "F#",
    }
    if not text:
        return "G"
    normalized = text[0].upper() + text[1:]
    return aliases.get(normalized, normalized)


def _section_spans(raw_melody: list[Any], requested_sections: Any) -> list[dict[str, Any]]:
    """Return stable phrase sections, preferring reviewed measure boundaries."""

    measures: list[int | None] = []
    for item in raw_melody:
        if isinstance(item, Mapping):
            try:
                measures.append(int(item.get("measure")) if item.get("measure") is not None else None)
            except (TypeError, ValueError):
                measures.append(None)
        else:
            measures.append(None)

    normalized: list[dict[str, Any]] = []
    if isinstance(requested_sections, list):
        for index, item in enumerate(requested_sections, start=1):
            if not isinstance(item, Mapping):
                continue
            try:
                measure_start = int(item.get("startMeasure"))
                measure_end = int(item.get("endMeasure"))
            except (TypeError, ValueError):
                continue
            indexes = [position for position, measure in enumerate(measures) if measure is not None and measure_start <= measure <= measure_end]
            if not indexes:
                continue
            normalized.append({
                "label": str(item.get("label") or f"Phrase {index}")[:80],
                "eventStart": indexes[0],
                "eventEnd": indexes[-1] + 1,
                "measureStart": measure_start,
                "measureEnd": measure_end,
            })
    if normalized:
        return normalized

    present_measures = sorted({measure for measure in measures if measure is not None})
    if present_measures:
        for offset in range(0, len(present_measures), 4):
            group = present_measures[offset : offset + 4]
            indexes = [position for position, measure in enumerate(measures) if measure in group]
            normalized.append({
                "label": f"Measures {group[0]}–{group[-1]}",
                "eventStart": indexes[0],
                "eventEnd": indexes[-1] + 1,
                "measureStart": group[0],
                "measureEnd": group[-1],
            })
        return normalized

    return [
        {
            "label": f"Phrase {index // MAX_EVENTS_PER_SECTION + 1}",
            "eventStart": index,
            "eventEnd": min(len(raw_melody), index + MAX_EVENTS_PER_SECTION),
            "measureStart": None,
            "measureEnd": None,
        }
        for index in range(0, len(raw_melody), MAX_EVENTS_PER_SECTION)
    ]


def _first_measure(raw_melody: list[Any]) -> int | None:
    measures = [_event_measure(item) for item in raw_melody]
    present = [measure for measure in measures if measure is not None]
    return min(present) if present else None


def _last_measure(raw_melody: list[Any]) -> int | None:
    measures = [_event_measure(item) for item in raw_melody]
    present = [measure for measure in measures if measure is not None]
    return max(present) if present else None


def _event_measure(item: Any) -> int | None:
    if not isinstance(item, Mapping) or item.get("measure") is None:
        return None
    try:
        return int(item.get("measure"))
    except (TypeError, ValueError):
        return None


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


def _exercise_title(
    kind: str,
    material: Mapping[str, str],
    key: str,
    section: int,
    *,
    whole_song: bool = False,
) -> str:
    label = _material_label(material)
    if label:
        return f"{label} — Complete E9 lesson" if whole_song else f"{label} — Section {section} E9 lesson"
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
        f"Here is {exercise['title']}, arranged for {exercise.get('arrangedFor', 'the selected E9 copedent')}. "
        "The tab, event steps, fretboard, score, and playback all use the same validated pitches.\n\n"
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
