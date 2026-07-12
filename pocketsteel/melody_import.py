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
import struct
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from xml.etree import ElementTree as ET


ENABLE_MELODY_IMPORT_ENV = "STEEL_RAG_ENABLE_MELODY_IMPORT"
MELODY_VISION_MODEL_ENV = "STEEL_RAG_MELODY_VISION_MODEL"
OLLAMA_URL_ENV = "OLLAMA_URL"
DEFAULT_VISION_MODEL = "gemma4:12b"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
SCORE_DRAFT_SCHEMA_VERSION = "score_draft_v1"
MAX_IMPORT_BODY_BYTES = 12 * 1024 * 1024
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_SCORE_BYTES = 2 * 1024 * 1024
MAX_MIDI_BYTES = 1024 * 1024
MAX_MXL_EXPANDED_BYTES = 4 * 1024 * 1024
MAX_EVENTS = 128
MAX_MEASURES = 64
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

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
    if source_type == "image":
        mime_type = str(payload.get("mimeType") or payload.get("mime_type") or "").strip().lower()
        if mime_type not in SUPPORTED_IMAGE_TYPES:
            raise MelodyImportError("Upload a JPG, PNG, or WebP image. For PDF music, upload a page screenshot.")
        raw = _decode_file(payload, MAX_IMAGE_BYTES)
        encoded = base64.b64encode(raw).decode("ascii")
        client = vision_client or _ollama_vision_client
        interpreted = client(encoded, mime_type)
        return normalize_score_draft(
            interpreted,
            source={
                "type": "image",
                "title": _safe_title(payload.get("title"), "Uploaded score"),
                "url": None,
                "rightsLabel": "unreviewed",
                "retained": False,
            },
            review_status="needs_review",
        )
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
    melody: list[dict[str, Any]] = []
    for index, item in enumerate(raw_melody[:MAX_EVENTS], start=1):
        if not isinstance(item, Mapping):
            continue
        if item.get("rest"):
            melody.append(
                {
                    "id": str(item.get("id") or f"m{index}"),
                    "measure": _bounded_int(item.get("measure"), 1, MAX_MEASURES, 1),
                    "beat": _positive_number(item.get("beat"), 1.0),
                    "durationBeats": _positive_number(item.get("durationBeats") or item.get("duration"), 1.0),
                    "rest": True,
                    "origin": str(item.get("origin") or "source"),
                    "confidence": _confidence(item.get("confidence")),
                }
            )
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
            "origin": str(item.get("origin") or "source"),
            "confidence": _confidence(item.get("confidence")),
        }
        for source_key, target_key in (("tie", "tie"), ("lyric", "lyric"), ("phraseLabel", "phraseLabel")):
            if item.get(source_key):
                event[target_key] = str(item[source_key])[:80]
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

    raw_source = source or (value.get("source") if isinstance(value.get("source"), Mapping) else {})
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
    ):
        if raw_source.get(key):
            normalized_source[key] = str(raw_source[key])[:500]

    source_key = str(raw_score.get("sourceKey") or raw_score.get("key") or "G").upper()
    arrangement_key = str(raw_score.get("arrangementKey") or source_key).upper()
    warnings = list((value.get("review") or {}).get("warnings") or []) if isinstance(value.get("review"), Mapping) else []
    if arrangement_key not in {"G", "C"}:
        warnings.append("Choose G or C as the E9 arrangement key before arranging this score.")
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
            "meter": "3/4" if str(raw_score.get("meter")) == "3/4" else "4/4",
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


def parse_musicxml(raw: bytes, *, compressed: bool = False, selected_part: Any = None) -> dict[str, Any]:
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
    pickup_beats = 0.0
    for part in root.findall("./part"):
        part_id = part.attrib.get("id", "")
        events: list[dict[str, Any]] = []
        derived_harmony: list[dict[str, Any]] = []
        divisions = 1
        time_beats = 4
        measure_lengths: list[float] = []
        for measure_index, measure in enumerate(part.findall("measure"), start=1):
            attributes = measure.find("attributes")
            if attributes is not None:
                divisions = int(attributes.findtext("divisions") or divisions or 1)
                if attributes.find("time") is not None:
                    time_beats = int(attributes.findtext("time/beats") or time_beats)
                    beat_type = int(attributes.findtext("time/beat-type") or 4)
                    meter = f"{time_beats}/{beat_type}"
                if attributes.find("key") is not None:
                    fifths = int(attributes.findtext("key/fifths") or 0)
                    source_key = {0: "C", 1: "G"}.get(fifths, _key_from_fifths(fifths))
            cursor = 0
            last_onset = 0
            sounding: dict[int, list[tuple[int, int, ET.Element]]] = defaultdict(list)
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
                    pitch = child.find("pitch")
                    if pitch is not None:
                        pitch_value = _musicxml_pitch_value(pitch)
                        voice = int(child.findtext("voice") or 1)
                        sounding[onset].append((pitch_value, duration, child))
                    if child.find("chord") is None:
                        cursor += duration
            measure_beats = max((onset + max(item[1] for item in group) for onset, group in sounding.items()), default=cursor) / divisions
            measure_lengths.append(measure_beats)
            for onset, group in sorted(sounding.items()):
                derived_symbol = _derived_chord_symbol([item[0] for item in group])
                if derived_symbol:
                    derived_harmony.append(
                        {
                            "measure": measure_index,
                            "beat": round((onset / divisions) + 1, 3),
                            "symbol": derived_symbol,
                            "basis": "derived",
                            "confidence": 0.7,
                        }
                    )
                pitch_value, duration, node = max(group, key=lambda item: item[0])
                lyric = node.findtext("lyric/text") or ""
                events.append(
                    {
                        "id": f"{part_id or 'part'}-m{measure_index}-{onset}",
                        "measure": measure_index,
                        "beat": round((onset / divisions) + 1, 3),
                        "durationBeats": round(max(duration / divisions, 0.125), 3),
                        "pitch": _pitch_label(pitch_value),
                        "pitchValue": pitch_value,
                        "lyric": lyric[:80],
                        "origin": "source",
                        "confidence": 1.0,
                    }
                )
        if measure_lengths and 0 < measure_lengths[0] < time_beats:
            pickup_beats = measure_lengths[0]
        if events:
            parsed_parts.append(
                {
                    "id": part_id,
                    "name": part_names.get(part_id, part_id or "Part"),
                    "events": events,
                    "averagePitch": sum(item["pitchValue"] for item in events) / len(events),
                    "derivedHarmony": derived_harmony,
                }
            )
    if not parsed_parts:
        raise MelodyImportError("That MusicXML file did not contain a readable melody part.")
    selected = next((part for part in parsed_parts if part["id"] == str(selected_part)), None)
    selected = selected or max(parsed_parts, key=lambda item: (item["averagePitch"], len(item["events"])))
    title = root.findtext("./work/work-title") or root.findtext("./movement-title") or "Imported MusicXML"
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
            "warnings": [] if len(parsed_parts) == 1 else [f"Using {selected['name']} as the melody; choose another part if needed."],
        },
        "parts": [{"id": item["id"], "name": item["name"], "eventCount": len(item["events"])} for item in parsed_parts],
    }
    normalized = normalize_score_draft(draft)
    normalized["parts"] = draft["parts"]
    normalized["selectedPartId"] = selected["id"]
    return normalized


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


def _ollama_vision_client(encoded_image: str, mime_type: str) -> Mapping[str, Any]:
    prompt = (
        "Read this single-page melody or lead-sheet image. Return JSON only with a score object containing "
        "sourceKey, arrangementKey (G or C when known), meter (3/4 or 4/4), pickupBeats, melody, and harmony. "
        "Each melody item needs measure, beat, durationBeats, pitch in scientific notation, confidence 0..1, "
        "and optional lyric. Each harmony item needs measure, beat, symbol, basis='source', and confidence. "
        "Use at most 64 melody events. Do not guess unreadable notes; omit them and add review.warnings."
    )
    payload = {
        "model": os.environ.get(MELODY_VISION_MODEL_ENV, DEFAULT_VISION_MODEL),
        "messages": [{"role": "user", "content": prompt, "images": [encoded_image]}],
        "format": "json",
        "stream": False,
        "options": {"temperature": 0},
    }
    request = urllib.request.Request(
        f"{os.environ.get(OLLAMA_URL_ENV, DEFAULT_OLLAMA_URL).rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise MelodyImportError("The local score reader is unavailable. You can still enter the passage manually.") from exc
    content = str((body.get("message") or {}).get("content") or "").strip()
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.I | re.S)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise MelodyImportError("The score reader returned an unreadable draft. Try a tighter, straighter photo.") from exc
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


def _confidence(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value if value is not None else 1.0))), 3)
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
