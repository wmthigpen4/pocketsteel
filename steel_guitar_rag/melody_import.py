"""Transient score import and public-domain catalog support for Melody Studio.

The importer deliberately has no persistence layer. Uploaded bytes are decoded
and parsed in memory, and callers receive a reviewable ``score_draft_v1``
payload. Images may be interpreted by the loopback Ollama service; no source
body is written to disk or included in application logs.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import socket
import struct
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from xml.etree import ElementTree as ET

from steel_guitar_rag.score_omr import (
    AudiverisOmrProvider,
    HomrOmrProvider,
    LocalVisionOmrProvider,
    ScoreOmrError,
    inspect_pdf,
    recognize_printed_document,
)


ENABLE_MELODY_IMPORT_ENV = "STEEL_RAG_ENABLE_MELODY_IMPORT"
MELODY_VISION_MODEL_ENV = "STEEL_RAG_MELODY_VISION_MODEL"
OLLAMA_URL_ENV = "OLLAMA_URL"
MELODY_VISION_TIMEOUT_ENV = "STEEL_RAG_MELODY_VISION_TIMEOUT_SECONDS"
SCORE_OMR_PROVIDER_ENV = "STEEL_RAG_SCORE_OMR_PROVIDER"
DEFAULT_VISION_MODEL = "gemma4:12b"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MELODY_VISION_TIMEOUT_SECONDS = 45.0
SCORE_DRAFT_SCHEMA_VERSION = "score_draft_v1"
MAX_IMPORT_BODY_BYTES = 12 * 1024 * 1024
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_PDF_BYTES = 8 * 1024 * 1024
MAX_SCORE_BYTES = 2 * 1024 * 1024
MAX_MIDI_BYTES = 1024 * 1024
MAX_MXL_EXPANDED_BYTES = 4 * 1024 * 1024
MAX_EVENTS = 128
MAX_MEASURES = 64
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
SUPPORTED_PRINTED_DOCUMENT_TYPES = {*SUPPORTED_IMAGE_TYPES, "application/pdf"}

_RESOURCE_ROOT = Path(__file__).resolve().parent / "resources" / "public_domain_songs"
_AMAZING_GRACE_PATH = _RESOURCE_ROOT / "amazing_grace_new_britain.json"
_STARTER_SONGBOOK_PATH = _RESOURCE_ROOT / "starter_songbook_v1.json"
_NOTE_VALUES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_PITCH_RE = re.compile(r"^([A-Ga-g])([#b]?)(-?\d+)$")


class MelodyImportError(ValueError):
    """A safe, user-facing score import error."""


class MelodyImportTooLargeError(MelodyImportError):
    """An import rejected before expensive parsing or model work."""


def configured_melody_import_enabled(env: Mapping[str, str] | None = None) -> bool:
    value = (env or os.environ).get(ENABLE_MELODY_IMPORT_ENV, "")
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_major_key(value: object) -> str:
    text = str(value or "G").strip().replace("♯", "#").replace("♭", "b")
    if not text:
        return "G"
    normalized = text[0].upper() + text[1:]
    return {
        "C#": "Db",
        "D#": "Eb",
        "G#": "Ab",
        "A#": "Bb",
        "Gb": "F#",
    }.get(normalized, normalized)


def public_song_catalog() -> list[dict[str, Any]]:
    """Return compact catalog cards without exposing internal score bodies."""
    cards: list[dict[str, Any]] = []
    for catalog_id, record, metadata in _catalog_records():
        source = record["source"]
        score = record["score"]
        event_count = len([event for event in score["melody"] if not event.get("rest")])
        measure_count = max((int(event.get("measure") or 1) for event in score["melody"]), default=1)
        sections = list(score.get("sections") or [])
        cards.append(
            {
                "id": catalog_id,
                "title": source["title"],
                "subtitle": source.get("subtitle", ""),
                "rightsLabel": source["rightsLabel"],
                "key": score["arrangementKey"],
                "meter": score["meter"],
                "sourceUrl": source.get("url", ""),
                "attribution": source.get("attribution", ""),
                "difficulty": metadata.get("difficulty", "starter"),
                "feel": metadata.get("feel", "traditional"),
                "eventCount": event_count,
                "measureCount": measure_count,
                "sectionCount": max(1, len(sections) or (measure_count + 3) // 4),
                "formLabel": metadata.get("formLabel", "Complete melody"),
                "accuracy": source.get("accuracy", "interpretive"),
            }
        )
    return cards


def import_score_draft(
    payload: Mapping[str, Any],
    *,
    vision_client: Callable[[str, str], Mapping[str, Any]] | None = None,
    progress_callback: Callable[[int, int, int], None] | None = None,
) -> dict[str, Any]:
    source_type = str(payload.get("sourceType") or payload.get("source_type") or "").strip().lower()
    if source_type == "catalog":
        catalog_id = str(payload.get("catalogId") or payload.get("catalog_id") or "").strip()
        record = next((record for item_id, record, _metadata in _catalog_records() if item_id == catalog_id), None)
        if record is None:
            raise MelodyImportError("That public-domain song is not in the reviewed Melody Studio catalog.")
        return record
    if source_type in {"musicxml", "mxl"}:
        raw = _decode_file(payload, MAX_SCORE_BYTES)
        return parse_musicxml(raw, compressed=source_type == "mxl", selected_part=payload.get("partId"))
    if source_type == "midi":
        raw = _decode_file(payload, MAX_MIDI_BYTES)
        return parse_midi(raw, selected_track=payload.get("trackIndex"))
    if source_type in {"image", "pdf"}:
        if payload.get("rightsAcknowledged") is not True:
            raise MelodyImportError(
                "Confirm that you own this material, have permission, or otherwise have the right to process it."
            )
        mime_type = str(payload.get("mimeType") or payload.get("mime_type") or "").strip().lower()
        expected_mime = "application/pdf" if source_type == "pdf" else mime_type
        if expected_mime not in SUPPORTED_PRINTED_DOCUMENT_TYPES:
            raise MelodyImportError("Upload a PDF, JPG, PNG, or WebP file containing clean printed notation.")
        raw = _decode_file(payload, MAX_PDF_BYTES if source_type == "pdf" else MAX_IMAGE_BYTES)
        if source_type == "pdf" and payload.get("inspectOnly") is True:
            try:
                return inspect_pdf(raw)
            except ScoreOmrError as exc:
                raise MelodyImportError(str(exc)) from exc
        selected_part = str(payload.get("partId") or "").strip() or None
        if vision_client is not None:
            provider = LocalVisionOmrProvider(vision_client)
        else:
            parse_recognized_musicxml = lambda musicxml, *, compressed: parse_musicxml(
                musicxml,
                compressed=compressed,
                selected_part=selected_part,
                recognized=True,
            )
            configured_provider = str(os.environ.get(SCORE_OMR_PROVIDER_ENV) or "audiveris").strip().lower()
            audiveris_provider = AudiverisOmrProvider(
                parse_recognized_musicxml
            )
            homr_provider = HomrOmrProvider(
                lambda musicxml, *, compressed: parse_musicxml(
                    musicxml,
                    compressed=compressed,
                    selected_part=selected_part,
                    recognized=True,
                )
            )
            if configured_provider == "homr":
                if not homr_provider.available:
                    raise MelodyImportError(
                        "The configured Homr score reader is not installed on this server."
                    )
                provider = homr_provider
            elif audiveris_provider.available:
                provider = audiveris_provider
            else:
                provider = LocalVisionOmrProvider(
                    lambda encoded, mime: _ollama_vision_client(
                        encoded,
                        mime,
                        selected_part=selected_part,
                    )
                )
        try:
            return recognize_printed_document(
                raw=raw,
                source_type="pdf" if source_type == "pdf" else mime_type,
                title=_safe_title(payload.get("title") or payload.get("filename"), "Uploaded score"),
                selected_pages=payload.get("selectedPages"),
                selected_part=selected_part,
                provider=provider,
                normalize=normalize_score_draft,
                progress_callback=progress_callback,
            )
        except ScoreOmrError as exc:
            raise MelodyImportError(str(exc)) from exc
    if source_type in {"pasted", "microphone", "composed_in_studio", "manual_phrase", "youtube"}:
        return normalize_score_draft(payload.get("draft") or payload)
    raise MelodyImportError("Choose a supported Melody Studio input method.")


def normalize_score_draft(
    value: Mapping[str, Any],
    *,
    source: Mapping[str, Any] | None = None,
    review_status: str | None = None,
) -> dict[str, Any]:
    raw_score = value.get("score") if isinstance(value.get("score"), Mapping) else value
    raw_melody = raw_score.get("melody") if isinstance(raw_score, Mapping) else None
    if not isinstance(raw_melody, Sequence) or isinstance(raw_melody, (str, bytes)):
        raise MelodyImportError("The imported material did not contain a readable melody.")
    raw_source = source or (
        value.get("source") if isinstance(value.get("source"), Mapping) else {}
    )
    recognized_source = str(raw_source.get("type") or "") in {"image", "pdf"}
    melody: list[dict[str, Any]] = []
    for index, item in enumerate(raw_melody[:MAX_EVENTS], start=1):
        if not isinstance(item, Mapping):
            continue
        if item.get("rest"):
            event = {
                "id": str(item.get("id") or f"m{index}"),
                "measure": _bounded_int(item.get("measure"), 1, MAX_MEASURES, 1),
                "beat": _positive_number(item.get("beat"), 1.0),
                "durationBeats": _positive_number(item.get("durationBeats") or item.get("duration"), 1.0),
                "rest": True,
                "origin": str(item.get("origin") or ("recognized" if recognized_source else "source")),
                "confidence": _confidence(
                    item.get("confidence"),
                    default=0.5 if recognized_source else 1.0,
                ),
            }
            for key in ("confidenceBasis", "staff", "voice"):
                if item.get(key):
                    event[key] = str(item[key])[:80]
            if item.get("sourcePage") is not None:
                event["sourcePage"] = _bounded_int(item.get("sourcePage"), 1, 999, 1)
            melody.append(event)
            continue
        pitch_value = _pitch_value(item.get("pitchValue"), item.get("pitch") or item.get("note"))
        if pitch_value is None or not 47 <= pitch_value <= 94:
            continue
        event = {
            "id": str(item.get("id") or f"m{index}"),
            "measure": _bounded_int(item.get("measure"), 1, MAX_MEASURES, 1),
            "beat": _positive_number(item.get("beat"), 1.0),
            "durationBeats": _positive_number(item.get("durationBeats") or item.get("duration"), 1.0),
            "pitch": _pitch_label(pitch_value),
            "pitchValue": pitch_value,
            "origin": str(item.get("origin") or ("recognized" if recognized_source else "source")),
            "confidence": _confidence(
                item.get("confidence"),
                default=0.5 if recognized_source else 1.0,
            ),
        }
        for source_key, target_key in (
            ("tie", "tie"),
            ("lyric", "lyric"),
            ("phraseLabel", "phraseLabel"),
            ("confidenceBasis", "confidenceBasis"),
            ("staff", "staff"),
            ("voice", "voice"),
        ):
            if item.get(source_key):
                event[target_key] = str(item[source_key])[:80]
        if isinstance(item.get("pitches"), Sequence) and not isinstance(
            item.get("pitches"), (str, bytes)
        ):
            pitches = sorted(
                {
                    int(value)
                    for value in item["pitches"]
                    if isinstance(value, (int, float)) and 47 <= int(value) <= 94
                }
            )
            if pitches:
                event["pitches"] = pitches
        if item.get("sourcePage") is not None:
            event["sourcePage"] = _bounded_int(item.get("sourcePage"), 1, 999, 1)
        melody.append(event)
    playable = [event for event in melody if not event.get("rest")]
    if not playable:
        raise MelodyImportError("The imported material did not contain a playable melody in the supported E9 register.")

    raw_harmony = raw_score.get("harmony") if isinstance(raw_score, Mapping) else []
    harmony: list[dict[str, Any]] = []
    if isinstance(raw_harmony, Sequence) and not isinstance(raw_harmony, (str, bytes)):
        for item in raw_harmony[:64]:
            if not isinstance(item, Mapping) or not item.get("symbol"):
                continue
            harmony.append(
                {
                    "measure": _bounded_int(item.get("measure"), 1, MAX_MEASURES, 1),
                    "beat": _positive_number(item.get("beat"), 1.0),
                    "symbol": str(item.get("symbol"))[:24],
                    "basis": str(item.get("basis") or "user"),
                    "confidence": _confidence(item.get("confidence")),
                }
            )

    normalized_source = {
        "type": str(raw_source.get("type") or "pasted"),
        "title": _safe_title(raw_source.get("title"), "Untitled melody"),
        "url": _safe_source_url(raw_source.get("url")),
        "rightsLabel": str(raw_source.get("rightsLabel") or "user_provided"),
        "retained": False,
    }
    for key in (
        "subtitle",
        "attribution",
        "sourceChecksum",
        "catalogId",
        "accuracy",
        "accuracyConfidence",
        "accuracyNote",
        "difficulty",
        "feel",
        "sectionLabel",
        "formLabel",
        "providerId",
        "retentionPolicy",
    ):
        if raw_source.get(key):
            normalized_source[key] = str(raw_source[key])[:500]
    normalized_source["private"] = bool(raw_source.get("private", normalized_source["type"] in {"image", "pdf"}))
    normalized_source["trainingUse"] = False
    if isinstance(raw_source.get("selectedPages"), Sequence):
        normalized_source["selectedPages"] = [
            _bounded_int(item, 1, 999, 1) for item in raw_source["selectedPages"]
        ][:8]
    if raw_source.get("pageCount") is not None:
        normalized_source["pageCount"] = _bounded_int(raw_source["pageCount"], 1, 999, 1)

    source_key = _normalize_major_key(raw_score.get("sourceKey") or raw_score.get("key") or "G")
    arrangement_key = _normalize_major_key(raw_score.get("arrangementKey") or source_key)
    warnings = list((value.get("review") or {}).get("warnings") or []) if isinstance(value.get("review"), Mapping) else []
    if arrangement_key not in {"C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"}:
        warnings.append("Choose a supported major key before arranging this score.")
    raw_meter = str(raw_score.get("meter") or "4/4").strip()
    supported_meter = raw_meter if raw_meter in {"2/2", "2/4", "3/4", "4/4", "6/8"} else ""
    if not supported_meter:
        warnings.append("Confirm the time signature before arranging this score.")
    raw_sections = raw_score.get("sections") if isinstance(raw_score, Mapping) else []
    sections: list[dict[str, Any]] = []
    if isinstance(raw_sections, Sequence) and not isinstance(raw_sections, (str, bytes)):
        for index, item in enumerate(raw_sections[:32], start=1):
            if not isinstance(item, Mapping):
                continue
            start_measure = _bounded_int(item.get("startMeasure"), 1, MAX_MEASURES, 1)
            end_measure = _bounded_int(item.get("endMeasure"), start_measure, MAX_MEASURES, start_measure)
            sections.append(
                {
                    "number": index,
                    "label": str(item.get("label") or f"Phrase {index}")[:80],
                    "startMeasure": start_measure,
                    "endMeasure": end_measure,
                }
            )
    return {
        "schemaVersion": SCORE_DRAFT_SCHEMA_VERSION,
        "source": normalized_source,
        "score": {
            "sourceKey": source_key,
            "arrangementKey": arrangement_key,
            "meter": supported_meter or "4/4",
            "pickupBeats": max(0.0, min(3.0, float(raw_score.get("pickupBeats") or 0))),
            "melody": melody,
            "harmony": harmony,
            "sections": sections,
        },
        "review": {
            "status": review_status or str((value.get("review") or {}).get("status") or "needs_review"),
            "warnings": [str(item)[:240] for item in warnings[:12]],
        },
    }


def parse_musicxml(
    raw: bytes,
    *,
    compressed: bool = False,
    selected_part: Any = None,
    recognized: bool = False,
) -> dict[str, Any]:
    xml_bytes = _mxl_xml_bytes(raw) if compressed or raw[:2] == b"PK" else raw
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise MelodyImportError("That MusicXML file could not be parsed.") from exc
    part_names = {
        item.attrib.get("id", ""): item.findtext("part-name") or item.attrib.get("id", "Part")
        for item in root.findall("./part-list/score-part")
    }
    parsed_parts: list[dict[str, Any]] = []
    explicit_harmony: list[dict[str, Any]] = []
    meter = "4/4"
    source_key = "G"
    metadata = {"keySignature": False, "timeSignature": False}
    for part in root.findall("./part"):
        part_id = part.attrib.get("id", "")
        divisions = 1
        candidate_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        candidate_harmony: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        candidate_measure_lengths: dict[tuple[str, str], list[float]] = defaultdict(list)
        clefs: dict[str, str] = {}
        for measure_index, measure in enumerate(part.findall("measure"), start=1):
            for attributes in measure.findall("attributes"):
                divisions = int(attributes.findtext("divisions") or divisions or 1)
                if attributes.find("time") is not None:
                    time_beats = int(attributes.findtext("time/beats") or 4)
                    beat_type = int(attributes.findtext("time/beat-type") or 4)
                    meter = f"{time_beats}/{beat_type}"
                    metadata["timeSignature"] = True
                if attributes.find("key") is not None:
                    fifths = int(attributes.findtext("key/fifths") or 0)
                    source_key = {0: "C", 1: "G"}.get(fifths, _key_from_fifths(fifths))
                    metadata["keySignature"] = True
                for clef in attributes.findall("clef"):
                    staff_number = str(clef.attrib.get("number") or "1")
                    sign = str(clef.findtext("sign") or "").strip()
                    line = str(clef.findtext("line") or "").strip()
                    clefs[staff_number] = f"{sign}{line}" if sign else ""
            cursor = 0
            last_onset = 0
            groups: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
            for child in list(measure):
                if child.tag == "backup":
                    cursor -= int(child.findtext("duration") or 0)
                elif child.tag == "forward":
                    cursor += int(child.findtext("duration") or 0)
                elif child.tag == "harmony":
                    explicit_harmony.append(
                        {
                            "measure": measure_index,
                            "beat": round((cursor / divisions) + 1, 3),
                            "symbol": _musicxml_chord_symbol(child),
                            "basis": "source",
                            "confidence": 1.0,
                        }
                    )
                elif child.tag == "note":
                    duration = int(child.findtext("duration") or 0)
                    onset = last_onset if child.find("chord") is not None else cursor
                    if child.find("chord") is None:
                        last_onset = onset
                    staff = str(child.findtext("staff") or "1")
                    voice = str(child.findtext("voice") or "1")
                    pitch = child.find("pitch")
                    tie_types = {
                        str(item.attrib.get("type") or "")
                        for item in [*child.findall("tie"), *child.findall("notations/tied")]
                        if item.attrib.get("type")
                    }
                    slur_starts = {
                        str(item.attrib.get("number") or "1")
                        for item in child.findall("notations/slur")
                        if item.attrib.get("type") == "start"
                    }
                    slur_stops = {
                        str(item.attrib.get("number") or "1")
                        for item in child.findall("notations/slur")
                        if item.attrib.get("type") == "stop"
                    }
                    groups[(staff, voice, onset)].append(
                        {
                            "pitchValue": _musicxml_pitch_value(pitch) if pitch is not None else None,
                            "duration": duration,
                            "rest": child.find("rest") is not None,
                            "lyric": (child.findtext("lyric/text") or "")[:80],
                            "tieTypes": tie_types,
                            "slurStarts": slur_starts,
                            "slurStops": slur_stops,
                        }
                    )
                    if child.find("chord") is None:
                        cursor += duration
            measure_ends: dict[tuple[str, str], int] = defaultdict(int)
            for (staff, voice, onset), group in sorted(groups.items()):
                pitches = [
                    int(item["pitchValue"])
                    for item in group
                    if item.get("pitchValue") is not None
                ]
                duration = max((int(item.get("duration") or 0) for item in group), default=0)
                candidate = (staff, voice)
                measure_ends[candidate] = max(measure_ends[candidate], onset + duration)
                derived_symbol = _derived_chord_symbol(pitches)
                if derived_symbol:
                    candidate_harmony[candidate].append(
                        {
                            "measure": measure_index,
                            "beat": round((onset / divisions) + 1, 3),
                            "symbol": derived_symbol,
                            "basis": "derived",
                            "confidence": 0.7,
                        }
                    )
                event_id = (
                    f"{part_id or 'part'}-s{staff}-v{voice}-m{measure_index}-{onset}"
                )
                event: dict[str, Any] = {
                    "id": event_id,
                    "measure": measure_index,
                    "beat": round((onset / divisions) + 1, 3),
                    "durationBeats": round(max(duration / divisions, 0.125), 3),
                    "origin": "recognized" if recognized else "source",
                    "confidence": 0.8 if recognized else 1.0,
                    "confidenceBasis": (
                        "provider_not_reported_structural_review_required"
                        if recognized
                        else "user_supplied_musicxml"
                    ),
                    "staff": staff,
                    "voice": voice,
                    "_slurStarts": sorted(
                        {
                            number
                            for item in group
                            for number in item.get("slurStarts", set())
                        }
                    ),
                    "_slurStops": sorted(
                        {
                            number
                            for item in group
                            for number in item.get("slurStops", set())
                        }
                    ),
                    "_tieTypes": sorted(
                        {
                            tie_type
                            for item in group
                            for tie_type in item.get("tieTypes", set())
                        }
                    ),
                }
                if pitches:
                    pitch_value = max(pitches)
                    event.update(
                        {
                            "pitch": _pitch_label(pitch_value),
                            "pitchValue": pitch_value,
                            "lyric": next(
                                (
                                    str(item.get("lyric") or "")
                                    for item in reversed(group)
                                    if item.get("pitchValue") == pitch_value
                                ),
                                "",
                            ),
                        }
                    )
                    if len(set(pitches)) > 1:
                        event["pitches"] = sorted(set(pitches))
                else:
                    event["rest"] = True
                candidate_groups[candidate].append(event)
            for candidate, end in measure_ends.items():
                candidate_measure_lengths[candidate].append(end / divisions)
        for (staff, voice), events in candidate_groups.items():
            _infer_musicxml_ties(events)
            playable = [event for event in events if not event.get("rest")]
            if not playable:
                continue
            candidate_id = f"{part_id or 'part'}:staff:{staff}:voice:{voice}"
            name = part_names.get(part_id, part_id or "Part")
            if len(candidate_groups) > 1:
                name = f"{name} · staff {staff} · voice {voice}"
            parsed_parts.append(
                {
                    "id": candidate_id,
                    "parentPartId": part_id,
                    "staff": staff,
                    "voice": voice,
                    "clef": clefs.get(staff, ""),
                    "name": name,
                    "events": events,
                    "averagePitch": sum(item["pitchValue"] for item in playable) / len(playable),
                    "derivedHarmony": candidate_harmony[(staff, voice)],
                    "measureLengths": candidate_measure_lengths[(staff, voice)],
                }
            )
    if not parsed_parts:
        raise MelodyImportError("That MusicXML file did not contain a readable melody part.")
    requested_part = str(selected_part or "")
    selected = next((part for part in parsed_parts if part["id"] == requested_part), None)
    if selected is None and requested_part:
        matching_parent_parts = [
            part for part in parsed_parts if part["parentPartId"] == requested_part
        ]
        if len(matching_parent_parts) == 1:
            selected = matching_parent_parts[0]
    selection_matched = selected is not None
    selected = selected or max(parsed_parts, key=lambda item: (item["averagePitch"], len(item["events"])))
    beats, beat_type = _meter_components(meter)
    measure_capacity = beats * (4 / beat_type) if beats and beat_type else 4.0
    pickup_beats = 0.0
    measure_lengths = selected["measureLengths"]
    if measure_lengths and 0 < measure_lengths[0] < measure_capacity:
        pickup_beats = measure_lengths[0]
    title = root.findtext("./work/work-title") or root.findtext("./movement-title") or "Imported MusicXML"
    selection_required = len(parsed_parts) > 1 and not selection_matched
    draft = {
        "source": {
            "type": "musicxml",
            "title": title,
            "url": None,
            "rightsLabel": "user_provided",
            "retained": False,
        },
        "score": {
            "sourceKey": source_key,
            "arrangementKey": source_key,
            "meter": meter,
            "pickupBeats": pickup_beats,
            "melody": selected["events"][:MAX_EVENTS],
            "harmony": [item for item in explicit_harmony if item["symbol"]] or selected["derivedHarmony"],
        },
        "review": {
            "status": "needs_review",
            "warnings": (
                [f"Select the intended staff or voice before arranging; {selected['name']} is shown provisionally."]
                if selection_required
                else []
            ),
        },
        "parts": [
            {
                "id": item["id"],
                "name": item["name"],
                "eventCount": len(item["events"]),
                "parentPartId": item["parentPartId"],
                "staff": item["staff"],
                "voice": item["voice"],
                "clef": item["clef"],
            }
            for item in parsed_parts
        ],
    }
    normalized = normalize_score_draft(draft)
    normalized["parts"] = draft["parts"]
    normalized["selectedPartId"] = selected["id"]
    normalized["selectionRequired"] = selection_required
    normalized["metadataRecognition"] = {
        "keySignature": metadata["keySignature"],
        "timeSignature": metadata["timeSignature"],
    }
    return normalized


def _infer_musicxml_ties(events: list[dict[str, Any]]) -> None:
    """Preserve explicit ties and convert same-pitch Homr slurs into ties."""

    for index, event in enumerate(events):
        explicit = set(event.pop("_tieTypes", []))
        starts = set(event.pop("_slurStarts", []))
        stops = set(event.pop("_slurStops", []))
        if "start" in explicit:
            event["tie"] = "start"
        elif "stop" in explicit:
            event["tie"] = "stop"
        if index + 1 >= len(events) or event.get("rest"):
            continue
        following = events[index + 1]
        following_stops = set(following.get("_slurStops", []))
        if (
            starts.intersection(following_stops)
            and not following.get("rest")
            and event.get("pitchValue") == following.get("pitchValue")
        ):
            event["tie"] = "start"
            following["_tieTypes"] = sorted(
                set(following.get("_tieTypes", [])).union({"stop"})
            )
        if stops and event.get("tie") is None and "stop" in explicit:
            event["tie"] = "stop"


def _meter_components(meter: str) -> tuple[int, int]:
    try:
        beats_text, beat_type_text = str(meter).split("/", 1)
        return int(beats_text), int(beat_type_text)
    except (TypeError, ValueError):
        return 0, 0


def parse_midi(raw: bytes, *, selected_track: Any = None) -> dict[str, Any]:
    if len(raw) < 14 or raw[:4] != b"MThd":
        raise MelodyImportError("That MIDI file has an invalid header.")
    header_size = struct.unpack(">I", raw[4:8])[0]
    _format, track_count, division = struct.unpack(">HHH", raw[8:14])
    if division & 0x8000 or division <= 0:
        raise MelodyImportError("SMPTE-timed MIDI files are not supported in this Melody Studio version.")
    offset = 8 + header_size
    tracks: list[list[dict[str, Any]]] = []
    key = "G"
    for track_index in range(track_count):
        if raw[offset : offset + 4] != b"MTrk" or offset + 8 > len(raw):
            raise MelodyImportError("That MIDI file has a damaged track.")
        length = struct.unpack(">I", raw[offset + 4 : offset + 8])[0]
        data = raw[offset + 8 : offset + 8 + length]
        offset += 8 + length
        notes, detected_key = _parse_midi_track(data, division, track_index)
        if detected_key:
            key = detected_key
        tracks.append(notes)
    nonempty = [(index, notes) for index, notes in enumerate(tracks) if notes]
    if not nonempty:
        raise MelodyImportError("That MIDI file did not contain note events.")
    requested = _optional_int(selected_track)
    chosen_index, chosen = next(((index, notes) for index, notes in nonempty if index == requested), (None, None))
    if chosen is None:
        chosen_index, chosen = max(nonempty, key=lambda item: (sum(note["pitchValue"] for note in item[1]) / len(item[1]), len(item[1])))
    grouped: dict[float, list[dict[str, Any]]] = defaultdict(list)
    for note in chosen:
        grouped[note["startBeat"]].append(note)
    melody: list[dict[str, Any]] = []
    harmony: list[dict[str, Any]] = []
    for index, (start, group) in enumerate(sorted(grouped.items())[:MAX_EVENTS], start=1):
        note = max(group, key=lambda item: item["pitchValue"])
        measure = int(start // 4) + 1
        symbol = _derived_chord_symbol([item["pitchValue"] for item in group])
        if symbol:
            harmony.append(
                {
                    "measure": measure,
                    "beat": round((start % 4) + 1, 3),
                    "symbol": symbol,
                    "basis": "derived",
                    "confidence": 0.7,
                }
            )
        melody.append(
            {
                "id": f"midi-{chosen_index}-{index}",
                "measure": measure,
                "beat": round((start % 4) + 1, 3),
                "durationBeats": note["durationBeats"],
                "pitch": _pitch_label(note["pitchValue"]),
                "pitchValue": note["pitchValue"],
                "origin": "source",
                "confidence": 1.0,
            }
        )
    draft = normalize_score_draft(
        {
            "source": {"type": "midi", "title": "Imported MIDI", "rightsLabel": "user_provided", "retained": False},
            "score": {"sourceKey": key, "arrangementKey": key, "meter": "4/4", "pickupBeats": 0, "melody": melody, "harmony": harmony},
            "review": {"status": "needs_review", "warnings": [f"Using MIDI track {chosen_index + 1} as the melody."]},
        }
    )
    draft["parts"] = [{"id": str(index), "name": f"Track {index + 1}", "eventCount": len(notes)} for index, notes in nonempty]
    draft["selectedTrackIndex"] = chosen_index
    return draft


def _parse_midi_track(data: bytes, division: int, track_index: int) -> tuple[list[dict[str, Any]], str | None]:
    position = 0
    ticks = 0
    running_status: int | None = None
    active: dict[tuple[int, int], list[int]] = defaultdict(list)
    notes: list[dict[str, Any]] = []
    detected_key: str | None = None
    while position < len(data):
        delta, position = _read_varlen(data, position)
        ticks += delta
        if position >= len(data):
            break
        status = data[position]
        if status < 0x80:
            if running_status is None:
                raise MelodyImportError("That MIDI track has invalid running status.")
            status = running_status
        else:
            position += 1
            if status < 0xF0:
                running_status = status
        if status == 0xFF:
            if position >= len(data):
                break
            meta_type = data[position]
            position += 1
            length, position = _read_varlen(data, position)
            value = data[position : position + length]
            position += length
            if meta_type == 0x59 and value:
                fifths = struct.unpack("b", value[:1])[0]
                detected_key = _key_from_fifths(fifths)
            continue
        if status in {0xF0, 0xF7}:
            length, position = _read_varlen(data, position)
            position += length
            continue
        message = status & 0xF0
        channel = status & 0x0F
        data_length = 1 if message in {0xC0, 0xD0} else 2
        if position + data_length > len(data):
            break
        values = data[position : position + data_length]
        position += data_length
        if message == 0x90 and values[1] > 0:
            active[(channel, values[0])].append(ticks)
        elif message == 0x80 or (message == 0x90 and values[1] == 0):
            starts = active.get((channel, values[0])) or []
            if starts:
                start = starts.pop(0)
                notes.append(
                    {
                        "track": track_index,
                        "pitchValue": int(values[0]),
                        "startBeat": round(start / division, 6),
                        "durationBeats": round(max((ticks - start) / division, 0.125), 6),
                    }
                )
    return notes, detected_key


def _read_varlen(data: bytes, position: int) -> tuple[int, int]:
    value = 0
    for _ in range(4):
        if position >= len(data):
            raise MelodyImportError("That MIDI file ended unexpectedly.")
        byte = data[position]
        position += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, position
    raise MelodyImportError("That MIDI file contains an invalid variable-length value.")


def _ollama_vision_client(
    encoded_image: str,
    mime_type: str,
    *,
    selected_part: str | None = None,
) -> Mapping[str, Any]:
    part_instruction = (
        f" Read only the staff or instrument whose part id is {selected_part!r}."
        if selected_part
        else ""
    )
    prompt = (
        "Assess and read this single-page image of clean printed Western notation. Handwriting, handwritten "
        "chord charts, and existing tablature are unsupported. Return JSON only with inputAssessment "
        "(kind: printed_notation, handwritten, tablature, or unreadable; accepted boolean; rescanGuidance) "
        "and a score object containing "
        "sourceKey, arrangementKey (major key when known), meter (including cut time as 2/2), pickupBeats, "
        "melody, and harmony. "
        "Each melody item needs measure, beat, durationBeats, pitch in scientific notation, confidence 0..1, "
        "and optional lyric. Each harmony item needs measure, beat, symbol, basis='source', and confidence. "
        "Use at most 64 melody events. Do not guess unreadable notes, key signatures, time signatures, octaves, "
        "or melody parts; omit uncertain events, lower confidence, and add review.warnings. Also return parts as "
        "staff summaries with id, name, eventCount, and melodyProbability, plus selectedPartId. Choose the likely "
        "melody automatically only when unambiguous."
        + part_instruction
    )
    payload = {
        "model": os.environ.get(MELODY_VISION_MODEL_ENV, DEFAULT_VISION_MODEL),
        "messages": [{"role": "user", "content": prompt, "images": [encoded_image]}],
        "format": "json",
        "stream": False,
        "think": False,
        "options": {"temperature": 0},
    }
    request = urllib.request.Request(
        f"{os.environ.get(OLLAMA_URL_ENV, DEFAULT_OLLAMA_URL).rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        timeout_seconds = float(
            os.environ.get(MELODY_VISION_TIMEOUT_ENV) or DEFAULT_MELODY_VISION_TIMEOUT_SECONDS
        )
    except (TypeError, ValueError):
        timeout_seconds = DEFAULT_MELODY_VISION_TIMEOUT_SECONDS
    timeout_seconds = max(5.0, min(timeout_seconds, 75.0))
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, socket.timeout, json.JSONDecodeError) as exc:
        raise MelodyImportError(
            "Printed-score recognition could not complete. Confirm that Ollama is running, then try again."
        ) from exc
    content = str((body.get("message") or {}).get("content") or "").strip()
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.I | re.S)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise MelodyImportError(
            "The score reader returned an unreadable draft. This is an internal recognition failure."
        ) from exc
    if not isinstance(parsed, Mapping):
        raise MelodyImportError("The score reader did not return a reviewable melody draft.")
    return parsed


def _decode_file(payload: Mapping[str, Any], limit: int) -> bytes:
    encoded = payload.get("contentBase64") or payload.get("content_base64")
    if not isinstance(encoded, str) or not encoded:
        raise MelodyImportError("The selected file did not include readable content.")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise MelodyImportError("The selected file could not be decoded.") from exc
    if len(raw) > limit:
        raise MelodyImportTooLargeError("That file is larger than the Melody Studio import limit.")
    return raw


def _mxl_xml_bytes(raw: bytes) -> bytes:
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos = [item for item in archive.infolist() if not item.is_dir()]
            if any(item.file_size > MAX_MXL_EXPANDED_BYTES for item in infos) or sum(item.file_size for item in infos) > MAX_MXL_EXPANDED_BYTES:
                raise MelodyImportError("That compressed MusicXML file expands beyond the safe import limit.")
            if any(".." in Path(item.filename).parts or item.filename.startswith(("/", "\\")) for item in infos):
                raise MelodyImportError("That compressed MusicXML file contains unsafe paths.")
            candidates = [item for item in infos if item.filename.lower().endswith((".musicxml", ".xml")) and "meta-inf" not in item.filename.lower()]
            if not candidates:
                raise MelodyImportError("That MXL file did not contain MusicXML.")
            return archive.read(candidates[0])
    except zipfile.BadZipFile as exc:
        raise MelodyImportError("That MXL file is not a valid compressed MusicXML archive.") from exc


def _musicxml_pitch_value(pitch: ET.Element) -> int:
    step = pitch.findtext("step") or "C"
    alter = int(pitch.findtext("alter") or 0)
    octave = int(pitch.findtext("octave") or 4)
    return 12 * (octave + 1) + _NOTE_VALUES[step] + alter


def _musicxml_chord_symbol(node: ET.Element) -> str:
    root = node.findtext("root/root-step") or ""
    alter = int(node.findtext("root/root-alter") or 0)
    accidental = "#" if alter == 1 else "b" if alter == -1 else ""
    kind_node = node.find("kind")
    kind = (kind_node.attrib.get("text") if kind_node is not None else "") or (kind_node.text if kind_node is not None else "") or ""
    suffix = {"major": "", "minor": "m", "dominant": "7", "major-seventh": "maj7", "minor-seventh": "m7"}.get(kind, kind)
    return f"{root}{accidental}{suffix}" if root else ""


def _derived_chord_symbol(pitches: Sequence[int]) -> str:
    pitch_classes = {int(pitch) % 12 for pitch in pitches}
    if len(pitch_classes) < 3:
        return ""
    names = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
    for root in sorted(pitch_classes):
        intervals = {(pitch - root) % 12 for pitch in pitch_classes}
        if {0, 4, 7}.issubset(intervals):
            return names[root]
        if {0, 3, 7}.issubset(intervals):
            return f"{names[root]}m"
        if {0, 3, 6}.issubset(intervals):
            return f"{names[root]}dim"
    return ""


def _pitch_value(raw_value: Any, raw_pitch: Any) -> int | None:
    try:
        if raw_value is not None and str(raw_value).strip() != "":
            return int(raw_value)
    except (TypeError, ValueError):
        pass
    match = _PITCH_RE.match(str(raw_pitch or "").strip())
    if not match:
        return None
    step, accidental, octave_text = match.groups()
    alter = 1 if accidental == "#" else -1 if accidental == "b" else 0
    return 12 * (int(octave_text) + 1) + _NOTE_VALUES[step.upper()] + alter


def _pitch_label(value: int) -> str:
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    return f"{names[value % 12]}{(value // 12) - 1}"


def _key_from_fifths(fifths: int) -> str:
    return {-7: "Cb", -6: "Gb", -5: "Db", -4: "Ab", -3: "Eb", -2: "Bb", -1: "F", 0: "C", 1: "G", 2: "D", 3: "A", 4: "E", 5: "B", 6: "F#", 7: "C#"}.get(fifths, "G")


def _safe_source_url(value: Any) -> str | None:
    text = str(value or "").strip()
    return text[:1000] if text.startswith(("https://", "http://")) else None


def _safe_title(value: Any, default: str) -> str:
    return str(value or default).strip()[:160] or default


def _confidence(value: Any, *, default: float = 1.0) -> float:
    try:
        return round(max(0.0, min(1.0, float(value if value is not None else default))), 3)
    except (TypeError, ValueError):
        return 0.5


def _positive_number(value: Any, default: float) -> float:
    try:
        return round(max(0.125, float(value)), 3)
    except (TypeError, ValueError):
        return default


def _bounded_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        return max(minimum, min(maximum, int(value)))
    except (TypeError, ValueError):
        return default


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _load_catalog_record(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MelodyImportError("The reviewed song catalog is unavailable.") from exc
    if isinstance(payload.get("score"), Mapping) and payload["score"].get("melodyMeasures"):
        payload = _expand_compact_catalog_record(payload)
    return normalize_score_draft(payload, review_status="confirmed")


def _catalog_records() -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    amazing_grace = _load_catalog_record(_AMAZING_GRACE_PATH)
    records: list[tuple[str, dict[str, Any], dict[str, Any]]] = [
        (
            "amazing-grace-new-britain",
            amazing_grace,
            {"order": 1, "difficulty": "starter", "feel": "hymn", "formLabel": "Complete verse melody"},
        )
    ]
    try:
        payload = json.loads(_STARTER_SONGBOOK_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MelodyImportError("The reviewed song catalog is unavailable.") from exc
    songs = payload.get("songs") if isinstance(payload, Mapping) else None
    if not isinstance(songs, Sequence) or isinstance(songs, (str, bytes)):
        raise MelodyImportError("The reviewed song catalog is unavailable.")
    for compact in songs:
        if not isinstance(compact, Mapping):
            continue
        expanded = _expand_compact_catalog_record(compact)
        catalog_id = str(expanded["source"].get("catalogId") or "")
        metadata = dict(compact.get("catalog") or {})
        records.append((catalog_id, normalize_score_draft(expanded, review_status="confirmed"), metadata))
    return sorted(records, key=lambda item: (int(item[2].get("order") or 999), item[1]["source"]["title"]))


def _expand_compact_catalog_record(compact: Mapping[str, Any]) -> dict[str, Any]:
    source = dict(compact.get("source") or {})
    score = dict(compact.get("score") or {})
    measures_pattern = score.pop("melodyMeasures", [])
    pattern = score.pop("melodyPattern", [])
    if not isinstance(pattern, Sequence) or isinstance(pattern, (str, bytes)):
        pattern = []
    beats_per_measure = 3 if str(score.get("meter")) == "3/4" else 4
    melody: list[dict[str, Any]] = []
    indexed_items: list[tuple[int, float, Sequence[Any]]] = []
    if isinstance(measures_pattern, Sequence) and not isinstance(measures_pattern, (str, bytes)):
        for measure_number, measure_items in enumerate(measures_pattern, start=1):
            if not isinstance(measure_items, Sequence) or isinstance(measure_items, (str, bytes)):
                continue
            beat = 1.0
            for item in measure_items:
                if not isinstance(item, Sequence) or isinstance(item, (str, bytes)) or not item:
                    continue
                indexed_items.append((measure_number, beat, item))
                beat += float(item[1]) if len(item) > 1 else 1.0
    else:
        cursor = 0.0
        for item in pattern:
            if not isinstance(item, Sequence) or isinstance(item, (str, bytes)) or not item:
                continue
            indexed_items.append((int(cursor // beats_per_measure) + 1, (cursor % beats_per_measure) + 1, item))
            cursor += float(item[1]) if len(item) > 1 else 1.0
    for index, (measure_number, beat, item) in enumerate(indexed_items, start=1):
        if not isinstance(item, Sequence) or isinstance(item, (str, bytes)) or not item:
            continue
        pitch = str(item[0])
        duration = float(item[1]) if len(item) > 1 else 1.0
        event = {
            "id": f"{source.get('catalogId', 'song')}-{index}",
            "measure": measure_number,
            "beat": beat,
            "durationBeats": duration,
            "origin": "reviewed_teaching_version",
            "confidence": 1,
        }
        if pitch.lower() == "z":
            event["rest"] = True
        else:
            event["pitch"] = pitch
        melody.append(event)
    harmony: list[dict[str, Any]] = []
    for item in score.pop("harmonyPattern", []):
        if not isinstance(item, Sequence) or isinstance(item, (str, bytes)) or len(item) < 2:
            continue
        event_index = max(0, min(len(melody) - 1, int(item[0])))
        if not melody:
            continue
        event = melody[event_index]
        harmony.append(
            {
                "measure": event["measure"],
                "beat": event["beat"],
                "symbol": str(item[1]),
                "basis": "reviewed_teaching_version",
                "confidence": 1,
            }
        )
    for item in score.pop("harmonyMeasures", []):
        if not isinstance(item, Sequence) or isinstance(item, (str, bytes)) or len(item) < 2:
            continue
        harmony.append(
            {
                "measure": int(item[0]),
                "beat": float(item[1]) if len(item) > 2 else 1.0,
                "symbol": str(item[2] if len(item) > 2 else item[1]),
                "basis": "reviewed_teaching_version",
                "confidence": 1,
            }
        )
    checksum_source = json.dumps(compact, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    source.setdefault("sourceChecksum", f"sha256:{hashlib.sha256(checksum_source).hexdigest()}")
    score["melody"] = melody
    score["harmony"] = harmony
    return {"schemaVersion": SCORE_DRAFT_SCHEMA_VERSION, "source": source, "score": score, "review": {"status": "confirmed", "warnings": []}}
