"""Generic, deterministic Travis lesson-companion v3 contract.

The browser editor may preserve uncertain musical claims, but this validator
never permits invalid timing, unknown controls, impossible string/fret values,
or an artifact that cannot synchronize with its primary backing track.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re
from typing import Any, Mapping


SCHEMA_VERSION = "lesson_companion_v3"
PROJECT_STATES = {
    "draft",
    "uploading",
    "ready_for_analysis",
    "processing",
    "review_ready",
    "published",
    "analysis_failed",
    "publish_failed",
}
PITCH_RE = re.compile(r"^([A-G])([#b]?)(-?\d+)$")
PITCH_CLASS = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
}


class CompanionValidationError(ValueError):
    """Raised when a draft or release violates the v3 contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CompanionValidationError(message)


def _positive_range(value: Mapping[str, Any], label: str, *, maximum: int | None = None) -> tuple[int, int]:
    start = int(value.get("startMs", -1))
    end = int(value.get("endMs", -1))
    _require(start >= 0 and end > start, f"{label} must have increasing non-negative timing.")
    if maximum is not None:
        _require(end <= maximum, f"{label} extends past its media duration.")
    return start, end


def _pitch_value(label: str) -> int | None:
    match = PITCH_RE.match(label)
    if not match:
        return None
    return (int(match.group(3)) + 1) * 12 + PITCH_CLASS[f"{match.group(1)}{match.group(2)}"]


def _controls(copedent: Mapping[str, Any]) -> dict[str, dict[int, int]]:
    values: dict[str, dict[int, int]] = {}
    for control in copedent.get("controls") or []:
        code = str(control.get("code") or "").strip()
        _require(code and code not in values, "Copedent controls need unique codes.")
        changes: dict[int, int] = {}
        for change in control.get("changes") or []:
            string = int(change.get("string", 0))
            semitones = int(change.get("semitones", 0))
            _require(1 <= string <= 10 and semitones != 0, f"Control {code} has an invalid change.")
            changes[string] = semitones
        _require(changes, f"Control {code} needs explicit string changes.")
        values[code] = changes
    return values


def validate_companion_v3(data: Mapping[str, Any], *, for_publish: bool = False) -> None:
    """Validate a generic companion draft or immutable published revision."""

    _require(data.get("schemaVersion") == SCHEMA_VERSION, f"Companion schema must be {SCHEMA_VERSION}.")
    _require(str(data.get("companionId") or "").strip(), "Companion ID is required.")
    _require(str(data.get("revision") or "").strip(), "Companion revision is required.")
    state = str(data.get("state") or "")
    _require(state in PROJECT_STATES, "Companion state is invalid.")

    lesson = data.get("lesson") or {}
    _require(str(lesson.get("slug") or "").strip(), "Lesson slug is required.")
    _require(str(lesson.get("title") or "").strip(), "Lesson title is required.")
    teachable = lesson.get("teachable") or {}
    _require(str(teachable.get("courseId") or "").strip(), "Teachable course ID is required.")
    _require(str(teachable.get("lessonId") or "").strip(), "Teachable lesson ID is required.")

    copedent = data.get("copedentSnapshot") or {}
    strings = copedent.get("stringsHighToLow") or []
    _require(len(strings) == 10, "The v1 workflow requires a ten-string E9 copedent snapshot.")
    open_pitches: dict[int, int] = {}
    for item in strings:
        string = int(item.get("string", 0))
        pitch = _pitch_value(str(item.get("openPitch") or ""))
        _require(1 <= string <= 10 and pitch is not None, "Every copedent string needs a scientific open pitch.")
        open_pitches[string] = pitch
    _require(len(open_pitches) == 10, "Copedent string numbers must be unique.")
    controls = _controls(copedent)

    media = data.get("media") or {}
    video = media.get("lessonVideo") or {}
    tracks = media.get("backingTracks") or []
    _require(str(video.get("assetId") or "").strip(), "Lesson video is required.")
    video_duration = int(video.get("durationMs", 0))
    _require(video_duration > 0, "Lesson video duration is required.")
    _require(bool(tracks), "At least one backing track is required.")
    primary = [track for track in tracks if track.get("primary") is True]
    _require(len(primary) == 1, "Exactly one backing track must be primary.")
    primary_track = primary[0]
    primary_id = str(primary_track.get("assetId") or "")
    _require(primary_id == str(data.get("primaryTrackId") or ""), "Primary-track ID does not match media.")
    primary_duration = int(primary_track.get("durationMs", 0))
    _require(primary_duration > 0, "Primary backing-track duration is required.")
    if for_publish:
        _require(primary_track.get("visibleToLearners") is True, "The primary track must be learner-playable.")

    timeline = data.get("songChordTimeline") or []
    _require(bool(timeline), "A full primary-track chord timeline is required.")
    cursor = 0
    chord_ids: set[str] = set()
    for index, chord in enumerate(timeline, start=1):
        chord_id = str(chord.get("id") or "")
        _require(chord_id and chord_id not in chord_ids, "Chord IDs must be present and unique.")
        chord_ids.add(chord_id)
        start, end = _positive_range(chord, f"Chord {chord_id}", maximum=primary_duration)
        _require(start == cursor, f"Chord {index} does not continue the full-song chart.")
        symbol = chord.get("symbol")
        uncertain = chord.get("reviewStatus") in {"uncertain", "generated_unconfirmed"}
        _require(bool(str(symbol or "").strip()) or uncertain, f"Chord {chord_id} needs a symbol or uncertainty marker.")
        cursor = end
    _require(cursor == primary_duration, "The chord timeline must cover the complete primary backing track.")

    passages = data.get("passages") or []
    _require(bool(passages), "At least one selected tablature passage is required.")
    passage_ids: set[str] = set()
    event_ids: set[str] = set()
    for passage in passages:
        passage_id = str(passage.get("id") or "")
        _require(passage_id and passage_id not in passage_ids, "Passage IDs must be present and unique.")
        passage_ids.add(passage_id)
        _positive_range(passage.get("videoRange") or {}, f"Passage {passage_id} video range", maximum=video_duration)
        track_start, track_end = _positive_range(
            passage.get("trackRange") or {}, f"Passage {passage_id} backing-track range", maximum=primary_duration
        )
        events = passage.get("tabEvents") or []
        _require(bool(events), f"Passage {passage_id} needs at least one tablature event.")
        previous_start = track_start
        for event in events:
            event_id = str(event.get("id") or "")
            _require(event_id and event_id not in event_ids, "Tab event IDs must be present and globally unique.")
            event_ids.add(event_id)
            start, end = _positive_range(event, f"Tab event {event_id}")
            _require(track_start <= start < end <= track_end, f"Tab event {event_id} is outside its backing-track range.")
            _require(start >= previous_start, f"Tab events in passage {passage_id} must be time ordered.")
            previous_start = start
            notes = event.get("notes") or []
            _require(bool(notes), f"Tab event {event_id} needs at least one note.")
            for note in notes:
                string = int(note.get("string", 0))
                fret = int(note.get("fret", -1))
                _require(1 <= string <= 10 and 0 <= fret <= 36, f"Tab event {event_id} has an invalid string or fret.")
                sounding = open_pitches[string] + fret
                for code in note.get("controls") or []:
                    _require(code in controls, f"Tab event {event_id} uses unknown control {code}.")
                    _require(string in controls[code], f"Control {code} does not change string {string}.")
                    sounding += controls[code][string]
                if note.get("pitchValue") is not None:
                    _require(int(note["pitchValue"]) == sounding, f"Tab event {event_id} fails copedent pitch validation.")

    if for_publish:
        _require(state == "published", "Published validation requires state published.")
        publication = data.get("publication") or {}
        _require(str(publication.get("publishedAt") or "").strip(), "Published timestamp is required.")
        _require(str(publication.get("contentSha256") or "").strip(), "Published content hash is required.")


def canonical_companion_bytes(data: Mapping[str, Any]) -> bytes:
    payload = deepcopy(dict(data))
    publication = payload.get("publication")
    if isinstance(publication, dict):
        publication.pop("contentSha256", None)
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def companion_sha256(data: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_companion_bytes(data)).hexdigest()


def _legacy_control_changes(code: str, strings: list[int]) -> list[dict[str, int]]:
    semitones = {"A": 2, "B": 1, "E": -1, "H1": 1}.get(code)
    if semitones is None:
        raise CompanionValidationError(f"Legacy Howdy control {code} needs an explicit v3 semitone mapping.")
    return [{"string": int(string), "semitones": semitones} for string in strings]


def convert_howdy_v1(source: Mapping[str, Any]) -> dict[str, Any]:
    """Convert the existing Howdy artifact into the reusable v3 draft shape."""

    _require(source.get("schemaVersion") == "lesson_companion_v1", "Howdy converter expects lesson_companion_v1.")
    duration = int((source.get("media") or {}).get("durationMs") or 0)
    scopes = (source.get("media") or {}).get("scopes") or {}
    full_scope = scopes.get("fullSong") or {}
    full_duration = int(full_scope.get("durationMs") or duration)
    video_duration = max(
        duration,
        max((int(moment.get("endMs") or moment.get("startMs") or 0) for moment in source.get("lessonMoments") or []), default=0),
    )
    video_duration = max(video_duration, full_duration)
    legacy_controls = (source.get("copedent") or {}).get("controls") or []
    chord_source = source.get("songChordTimeline") or source.get("chordTimeline") or []
    chord_timeline: list[dict[str, Any]] = []
    cursor = 0
    for index, chord in enumerate(chord_source, start=1):
        start = int(chord.get("startMs", cursor))
        end = int(chord.get("endMs", full_duration))
        if source.get("songChordTimeline") is None:
            start = round((start / max(1, duration)) * full_duration)
            end = round((end / max(1, duration)) * full_duration)
        start = cursor
        if index == len(chord_source):
            end = full_duration
        chord_timeline.append(
            {
                "id": str(chord.get("id") or f"chord-{index:03d}"),
                "startMs": start,
                "endMs": end,
                "symbol": chord.get("symbol"),
                "nns": chord.get("nns"),
                "sectionLabel": chord.get("sectionLabel") or "Howdy",
                "reviewStatus": "approved" if chord.get("verified") else "uncertain",
                "confidence": chord.get("confidence"),
                "provenance": chord.get("sourceKind") or "legacy_howdy_v1",
            }
        )
        cursor = end
    if not chord_timeline:
        chord_timeline = [{
            "id": "chord-001",
            "startMs": 0,
            "endMs": full_duration,
            "symbol": None,
            "nns": None,
            "sectionLabel": "Howdy",
            "reviewStatus": "uncertain",
            "confidence": None,
            "provenance": "legacy_howdy_v1",
        }]

    passage_start = int((scopes.get("taughtSolo") or {}).get("startMs") or 0)
    passage_duration = int((scopes.get("taughtSolo") or {}).get("durationMs") or duration)
    passage_end = min(full_duration, passage_start + passage_duration)
    events: list[dict[str, Any]] = []
    for index, event in enumerate(source.get("events") or [], start=1):
        source_start = int(event.get("startMs", 0))
        source_end = int(event.get("endMs", source_start + 1))
        start = passage_start + source_start
        end = min(passage_end, passage_start + source_end)
        notes = []
        for note in event.get("tabNotes") or []:
            notes.append(
                {
                    "string": int(note["string"]),
                    "fret": int(note["fret"]),
                    "controls": list(note.get("controls") or []),
                    "technique": note.get("technique") or "pick",
                }
            )
        events.append(
            {
                "id": str(event.get("id") or f"event-{index:03d}"),
                "startMs": start,
                "endMs": max(start + 1, end),
                "notes": notes,
                "instruction": event.get("instruction") or "",
                "reviewStatus": "approved" if event.get("musicalVerified") else "generated_unconfirmed",
                "confidence": 1 if event.get("musicalVerified") else None,
                "provenance": "legacy_howdy_v1",
            }
        )

    return {
        "schemaVersion": SCHEMA_VERSION,
        "companionId": source.get("companionId") or "travis-toy-tutorials-howdy",
        "revision": f"{source.get('revision') or 'howdy-draft'}.v3",
        "state": "review_ready",
        "lesson": {
            "slug": "howdy",
            "title": source.get("title") or "Howdy Solo",
            "subtitle": source.get("subtitle") or "",
            "key": (source.get("display") or {}).get("key") or "D",
            "meter": (source.get("display") or {}).get("meter") or "4/4",
            "teachable": {
                "school": (source.get("lesson") or {}).get("school") or "Travis Toy Tutorials",
                "courseId": str((source.get("lesson") or {}).get("courseId") or "configured-course"),
                "lessonId": str((source.get("lesson") or {}).get("lectureId") or "66525061"),
            },
        },
        "copedentSnapshot": {
            "id": (source.get("copedent") or {}).get("id") or "travis-e9",
            "label": (source.get("copedent") or {}).get("label") or "Travis E9",
            "stringsHighToLow": deepcopy((source.get("copedent") or {}).get("stringsHighToLow") or []),
            "controls": [
                {
                    "code": control["code"],
                    "label": control.get("label") or control["code"],
                    "changes": _legacy_control_changes(str(control["code"]), list(control.get("strings") or [])),
                }
                for control in legacy_controls
            ],
        },
        "media": {
            "lessonVideo": {
                "assetId": "howdy-lesson-video",
                "fileName": "howdy-lesson-video.mp4",
                "durationMs": video_duration,
                "sha256": None,
            },
            "backingTracks": [{
                "assetId": "howdy-primary-backing",
                "fileName": (source.get("media") or {}).get("audioFileName") or "howdy-backing-track.mp3",
                "label": "Howdy backing track",
                "durationMs": full_duration,
                "sha256": (source.get("media") or {}).get("audioSha256"),
                "primary": True,
                "visibleToLearners": True,
                "downloadable": True,
                "synchronized": True,
            }],
        },
        "primaryTrackId": "howdy-primary-backing",
        "songChordTimeline": chord_timeline,
        "passages": [{
            "id": "howdy-taught-solo",
            "label": "Taught solo",
            "videoRange": {"startMs": 0, "endMs": max(1, min(video_duration, duration or passage_duration))},
            "trackRange": {"startMs": passage_start, "endMs": passage_end},
            "alignment": {"status": "legacy_reviewed", "confidence": 1},
            "tabEvents": events,
        }],
        "analysis": {
            "status": "legacy_converted",
            "modelVersions": {},
            "sourceRevision": source.get("revision"),
        },
        "publication": {
            "publishedAt": None,
            "contentSha256": None,
            "uncertaintyVisible": True,
        },
    }
