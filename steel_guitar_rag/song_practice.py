"""Deterministic Stage 1 song-practice planning and pilot-track catalog.

The browser owns recordings and project identity.  This module receives only a
timed harmonic timeline and an already-resolved E9 copedent profile.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from steel_guitar_rag.melody_import import import_score_draft
from steel_guitar_rag.song_catalog_pipeline import SongCatalogPipelineError, published_project_ids
from steel_guitar_rag.copedent_transfer import (
    absolute_pitch_for_profile,
    candidate_control_states,
    control_affects_string,
    control_display_label,
)
from steel_guitar_rag.e9_copedents import (
    CANONICAL_NOTES,
    NOTE_TO_SEMITONE,
    E9CopedentProfile,
    scientific_pitch_for_value,
)


ENABLE_SONG_PRACTICE_ENV = "STEEL_RAG_ENABLE_SONG_PRACTICE"
REQUEST_SCHEMA = "song_practice_request_v1"
PLAN_SCHEMA = "song_practice_plan_v1"
CATALOG_SCHEMA = "song_practice_catalog_v1"
LEVEL_CHORD_KARAOKE = "chord_karaoke"
MAX_EVENTS = 512
MAX_FRET = 24
TRACKED_ASSET_LIMIT = 2 * 1024 * 1024
_MANIFEST_PATH = Path(__file__).with_name("resources") / "song_practice_tracks" / "manifest.json"
_REPO_ROOT = Path(__file__).resolve().parents[1]
_CHORD_RE = re.compile(r"^([A-Ga-g])([#b]?)([^/]*)?(?:/([A-Ga-g])([#b]?))?$")
_FORBIDDEN_REQUEST_KEYS = {
    "artist",
    "audio",
    "audioblob",
    "audiobytes",
    "audiodata",
    "audiosource",
    "cue",
    "cuetext",
    "filename",
    "lyrics",
    "song",
    "songtitle",
    "title",
}
_GRIPS: tuple[tuple[int, ...], ...] = (
    (4, 5, 6),
    (3, 4, 5),
    (5, 6, 8),
    (6, 8, 10),
    (3, 5, 6),
    (4, 6, 8),
    (5, 8, 10),
    (4, 5, 8),
    (5, 6, 10),
)

_CURATED_ORDER = {
    "amazing-grace-guided": 1,
    "when-the-saints-guided": 2,
    "hard-times-guided": 3,
}

_AMAZING_GRACE_PROJECT_ID = "amazing-grace-guided"
_AMAZING_GRACE_MELODY_CATALOG_ID = "amazing-grace-new-britain"


def _chart_bar_chords(chart: object) -> list[str]:
    bars: list[str] = []
    for raw_bar in str(chart or "").split("|"):
        chord = re.sub(r"\[[^\]]+\]", "", raw_bar).strip()
        if chord:
            bars.append(chord)
    return bars


def _interpolated_beat_time(beat_times: Sequence[int], beat_index: float, duration_ms: int) -> int:
    lower = int(beat_index)
    fraction = float(beat_index) - lower
    if lower >= len(beat_times):
        return int(duration_ms)
    if not fraction or lower + 1 >= len(beat_times):
        return int(beat_times[lower])
    return round(beat_times[lower] + ((beat_times[lower + 1] - beat_times[lower]) * fraction))


def _amazing_grace_melody_timeline(track: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if str(track.get("projectId") or track.get("id") or "") != _AMAZING_GRACE_PROJECT_ID:
        return [], {}
    draft = import_score_draft({"sourceType": "catalog", "catalogId": _AMAZING_GRACE_MELODY_CATALOG_ID})
    source = draft["source"]
    melody = draft["score"]["melody"]
    beat_times = list(track.get("beatTimesMs") or [])
    duration_ms = int(track["durationMs"])
    bar_chords = _chart_bar_chords(track.get("chart"))
    sections = list(track.get("sections") or [])
    lyric_cues = list(track.get("lyricCues") or [])
    if len(melody) != 35 or len(beat_times) < 51 or len(bar_chords) < 15:
        raise SongPracticeError("Amazing Grace melody timing is incomplete")

    timeline: list[dict[str, Any]] = []
    for index, event in enumerate(melody, start=1):
        measure = int(event["measure"])
        beat = float(event["beat"])
        duration_beats = float(event["durationBeats"])
        is_pickup = measure == 1
        bar = 1 if is_pickup else measure - 1
        base_beat_index = 5 if is_pickup else 6 + ((measure - 2) * 3)
        start_beat_index = base_beat_index + (beat - 1)
        end_beat_index = start_beat_index + duration_beats
        start_ms = _interpolated_beat_time(beat_times, start_beat_index, duration_ms)
        end_ms = _interpolated_beat_time(beat_times, end_beat_index, duration_ms)
        active_chord = bar_chords[min(max(bar - 1, 0), len(bar_chords) - 1)]
        section = next(
            (
                item
                for item in sections
                if int(item.get("startBar") or 1) <= bar <= int(item.get("endBar") or bar)
            ),
            None,
        )
        phrase = next(
            (
                str(cue.get("text") or "")
                for cue in lyric_cues
                if int(cue.get("startMs") or 0) <= start_ms < int(cue.get("endMs") or 0)
            ),
            "",
        )
        pitch = str(event["pitch"])
        timeline.append(
            {
                "id": f"amazing-grace-melody-{index}",
                "token": pitch,
                "pitch": pitch,
                "pitchValue": int(event["pitchValue"]),
                "durationBeats": duration_beats,
                "measure": measure,
                "beat": beat,
                "bar": bar,
                "isPickup": is_pickup,
                "startMs": start_ms,
                "endMs": end_ms,
                "chord": active_chord,
                "sectionId": str((section or {}).get("id") or "opening"),
                "phrase": phrase,
                "origin": "reviewed_teaching_version",
                "confirmationState": "confirmed",
            }
        )
    return timeline, {
        "catalogId": _AMAZING_GRACE_MELODY_CATALOG_ID,
        "title": source.get("title") or "Amazing Grace",
        "subtitle": source.get("subtitle") or "Complete verse melody · NEW BRITAIN",
        "url": source.get("url") or "",
        "attribution": source.get("attribution") or "",
        "rightsLabel": source.get("rightsLabel") or "public_domain",
        "accuracy": source.get("accuracy") or "interpretive",
        "accuracyConfidence": source.get("accuracyConfidence") or "high",
        "reviewStatus": draft.get("review", {}).get("status") or "confirmed",
    }

class SongPracticeError(ValueError):
    """Raised when a Song Practice request cannot be planned safely."""


@dataclass(frozen=True)
class ParsedChord:
    symbol: str
    root: str
    root_pc: int
    quality: str
    tone_intervals: tuple[int, ...]
    required_intervals: tuple[int, ...]
    bass: str = ""

    @property
    def tone_pitch_classes(self) -> frozenset[int]:
        return frozenset((self.root_pc + interval) % 12 for interval in self.tone_intervals)

    @property
    def required_pitch_classes(self) -> frozenset[int]:
        return frozenset((self.root_pc + interval) % 12 for interval in self.required_intervals)


@dataclass(frozen=True)
class ChordCandidate:
    fret: int
    strings: tuple[int, ...]
    controls: tuple[str, ...]
    pitches: tuple[int, ...]
    completeness: str
    base_cost: float


def configured_song_practice_enabled() -> bool:
    configured = os.environ.get(ENABLE_SONG_PRACTICE_ENV)
    if configured is None:
        return True
    return configured.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _normalized_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def _reject_private_media_fields(value: object, path: str = "request") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalized_key(key)
            if normalized in _FORBIDDEN_REQUEST_KEYS or normalized.startswith("audio"):
                raise SongPracticeError(f"{path}.{key} is not allowed in a song-practice request")
            _reject_private_media_fields(nested, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_private_media_fields(nested, f"{path}[{index}]")


def _normalize_note(letter: str, accidental: str = "") -> str:
    note = f"{letter.upper()}{accidental}"
    if note not in NOTE_TO_SEMITONE:
        raise SongPracticeError(f"Unsupported note spelling: {note}")
    return note


def parse_chord_symbol(symbol: object) -> ParsedChord | None:
    raw = str(symbol or "").strip()
    match = _CHORD_RE.fullmatch(raw)
    if not match:
        return None
    root = _normalize_note(match.group(1), match.group(2))
    suffix = str(match.group(3) or "").strip().lower().replace(" ", "")
    bass = _normalize_note(match.group(4), match.group(5)) if match.group(4) else ""
    qualities: dict[str, tuple[str, tuple[int, ...], tuple[int, ...]]] = {
        "": ("major", (0, 4, 7), (0, 4, 7)),
        "maj": ("major", (0, 4, 7), (0, 4, 7)),
        "m": ("minor", (0, 3, 7), (0, 3, 7)),
        "min": ("minor", (0, 3, 7), (0, 3, 7)),
        "-": ("minor", (0, 3, 7), (0, 3, 7)),
        "7": ("dominant7", (0, 4, 7, 10), (0, 4, 10)),
        "dom7": ("dominant7", (0, 4, 7, 10), (0, 4, 10)),
        "m7": ("minor7", (0, 3, 7, 10), (0, 3, 10)),
        "min7": ("minor7", (0, 3, 7, 10), (0, 3, 10)),
        "-7": ("minor7", (0, 3, 7, 10), (0, 3, 10)),
    }
    quality_spec = qualities.get(suffix)
    if quality_spec is None:
        return None
    quality, tones, required = quality_spec
    return ParsedChord(
        symbol=raw,
        root=root,
        root_pc=NOTE_TO_SEMITONE[root],
        quality=quality,
        tone_intervals=tones,
        required_intervals=required,
        bass=bass,
    )


def _candidate_base_cost(candidate: ChordCandidate) -> float:
    center_cost = abs(candidate.fret - 6) * 0.12
    control_cost = sum(0.65 if control in {"A", "B"} else 1.8 for control in candidate.controls)
    grip_cost = 0.0 if candidate.strings == (4, 5, 6) else 0.55
    shell_cost = 0.35 if candidate.completeness == "shell" else 0.0
    return round(center_cost + control_cost + grip_cost + shell_cost, 4)


def _candidate_key(candidate: ChordCandidate) -> tuple[object, ...]:
    return candidate.fret, candidate.strings, candidate.controls, candidate.pitches


def _prefer_a_over_c_for_fifth_string_only(
    profile: E9CopedentProfile,
    grip: tuple[int, ...],
    controls: tuple[str, ...],
) -> tuple[str, ...]:
    """Use A when C only duplicates A's string-5 raise on the played grip.

    The controls are not interchangeable when string 10 is played: A also
    raises string 10, while C leaves it available as a chord tone.
    """
    controls_by_id = profile.controls_by_id()
    if "C" not in controls or "A" in controls or "A" not in controls_by_id:
        return controls
    c_strings = tuple(
        string for string in grip if control_affects_string(profile, "C", string)
    )
    if c_strings != (5,):
        return controls
    replacement_ids = (set(controls) - {"C"}) | {"A"}
    replacement = tuple(control for control in controls_by_id if control in replacement_ids)
    original_pitches = tuple(
        absolute_pitch_for_profile(profile, string, 0, controls) for string in grip
    )
    replacement_pitches = tuple(
        absolute_pitch_for_profile(profile, string, 0, replacement) for string in grip
    )
    return replacement if replacement_pitches == original_pitches else controls


def _chord_candidates(chord: ParsedChord, profile: E9CopedentProfile) -> list[ChordCandidate]:
    tone_pcs = chord.tone_pitch_classes
    required_pcs = chord.required_pitch_classes
    candidates: dict[tuple[object, ...], ChordCandidate] = {}
    for raw_controls in candidate_control_states(profile):
        for grip in _GRIPS:
            controls = tuple(
                control
                for control in raw_controls
                if any(control_affects_string(profile, control, string) for string in grip)
            )
            if raw_controls and not controls:
                continue
            controls = _prefer_a_over_c_for_fifth_string_only(profile, grip, controls)
            for fret in range(MAX_FRET + 1):
                pitches = tuple(
                    absolute_pitch_for_profile(profile, string, fret, controls)
                    for string in grip
                )
                pitch_classes = frozenset(pitch % 12 for pitch in pitches)
                if not required_pcs.issubset(pitch_classes) or not pitch_classes.issubset(tone_pcs):
                    continue
                completeness = "full" if tone_pcs.issubset(pitch_classes) else "shell"
                draft = ChordCandidate(
                    fret=fret,
                    strings=grip,
                    controls=controls,
                    pitches=pitches,
                    completeness=completeness,
                    base_cost=0.0,
                )
                draft = ChordCandidate(**{**draft.__dict__, "base_cost": _candidate_base_cost(draft)})
                candidates[_candidate_key(draft)] = draft
    return sorted(
        candidates.values(),
        key=lambda item: (item.base_cost, item.fret, len(item.controls), item.strings, item.controls),
    )


def _common_voice_count(left: ChordCandidate, right: ChordCandidate) -> int:
    left_by_string = dict(zip(left.strings, left.pitches, strict=True))
    right_by_string = dict(zip(right.strings, right.pitches, strict=True))
    return sum(
        1
        for string in set(left_by_string).intersection(right_by_string)
        if left_by_string[string] == right_by_string[string]
    )


def _transition_cost(left: ChordCandidate, right: ChordCandidate) -> float:
    fret_cost = abs(left.fret - right.fret) * 1.15
    control_cost = len(set(left.controls).symmetric_difference(right.controls)) * 1.4
    grip_cost = len(set(left.strings).symmetric_difference(right.strings)) * 0.45
    voice_credit = _common_voice_count(left, right) * 0.8
    return round(fret_cost + control_cost + grip_cost - voice_credit, 4)


def _coherent_route(
    groups: Sequence[list[ChordCandidate] | None],
    *,
    route_preference: str = "balanced",
    home_fret: int = 6,
) -> list[ChordCandidate | None]:
    route: list[ChordCandidate | None] = [None] * len(groups)
    supported_indexes = [index for index, group in enumerate(groups) if group]
    if not supported_indexes:
        return route
    trimmed = {index: list(groups[index] or [])[:48] for index in supported_indexes}
    costs: dict[int, list[float]] = {}
    parents: dict[int, list[int | None]] = {}
    previous_index: int | None = None
    for index in supported_indexes:
        candidates = trimmed[index]
        if previous_index is None:
            costs[index] = [
                candidate.base_cost
                + (abs(candidate.fret - home_fret) * 1.8 if route_preference == "stay_near" else 0)
                for candidate in candidates
            ]
            parents[index] = [None] * len(candidates)
        else:
            previous = trimmed[previous_index]
            previous_costs = costs[previous_index]
            current_costs: list[float] = []
            current_parents: list[int | None] = []
            for candidate in candidates:
                choices = []
                chord_changed = groups[index] is not groups[previous_index]
                for parent, source in enumerate(previous):
                    preference_cost = 0.0
                    if route_preference == "stay_near":
                        preference_cost = abs(candidate.fret - home_fret) * 1.8
                    elif route_preference == "move_bar" and chord_changed:
                        distance = abs(candidate.fret - source.fret)
                        if distance == 0:
                            preference_cost = 4.0
                        elif 2 <= distance <= 5:
                            preference_cost = -1.6
                        elif distance > 8:
                            preference_cost = (distance - 8) * 0.8
                    choices.append((
                        previous_costs[parent]
                        + _transition_cost(source, candidate)
                        + candidate.base_cost
                        + preference_cost,
                        parent,
                    ))
                best_cost, best_parent = min(choices, key=lambda item: (item[0], item[1]))
                current_costs.append(best_cost)
                current_parents.append(best_parent)
            costs[index] = current_costs
            parents[index] = current_parents
        previous_index = index
    assert previous_index is not None
    selected = min(range(len(costs[previous_index])), key=lambda item: (costs[previous_index][item], item))
    for index in reversed(supported_indexes):
        route[index] = trimmed[index][selected]
        parent = parents[index][selected]
        if parent is not None:
            selected = parent
    return route


def _controls_payload(profile: E9CopedentProfile, controls: Sequence[str]) -> tuple[list[str], list[str]]:
    ids = [str(control) for control in controls]
    labels = [control_display_label(profile, control) for control in controls]
    return ids, labels


def _position_payload(
    candidate: ChordCandidate,
    *,
    chord: ParsedChord,
    profile: E9CopedentProfile,
    position_id: str,
) -> dict[str, Any]:
    controls, control_labels = _controls_payload(profile, candidate.controls)
    controls_by_id = profile.controls_by_id()
    pedal_labels = [
        control_display_label(profile, control)
        for control in candidate.controls
        if controls_by_id.get(control) and controls_by_id[control].control_type == "pedal"
    ]
    lever_labels = [
        control_display_label(profile, control)
        for control in candidate.controls
        if controls_by_id.get(control) and controls_by_id[control].control_type == "lever"
    ]
    notes: list[dict[str, Any]] = []
    for string, pitch in zip(candidate.strings, candidate.pitches, strict=True):
        changes = [
            control
            for control in candidate.controls
            if control_affects_string(profile, control, string)
        ]
        notes.append(
            {
                "string": string,
                "fret": candidate.fret,
                "pitch": pitch,
                "pitchLabel": scientific_pitch_for_value(pitch),
                "note": CANONICAL_NOTES[pitch % 12],
                "changes": changes,
                "changeLabels": [control_display_label(profile, change) for change in changes],
            }
        )
    posture = "+".join(control_labels) if control_labels else "open"
    quality_note = "complete chord" if candidate.completeness == "full" else "honest three-note shell"
    disclosure = f" Slash bass {chord.bass} is not represented by this upper E9 grip." if chord.bass else ""
    return {
        "id": position_id,
        "status": "validated",
        "validation": ["absolute_pitch", "chord_tones", "mechanical_controls"],
        "chord": chord.symbol,
        "root": chord.root,
        "quality": chord.quality,
        "completeness": candidate.completeness,
        "fret": candidate.fret,
        "strings": list(candidate.strings),
        "grip": "-".join(str(string) for string in candidate.strings),
        "controls": controls,
        "controlLabels": control_labels,
        "pedals": pedal_labels,
        "levers": lever_labels,
        "notes": notes,
        "instruction": (
            f"Fret {candidate.fret}, strings {'-'.join(str(string) for string in candidate.strings)}, "
            f"{posture}; {quality_note}.{disclosure}"
        ),
    }


def _canonical_timeline_hash(payload: Mapping[str, Any], events: Sequence[Mapping[str, Any]]) -> str:
    canonical = {
        "schemaVersion": REQUEST_SCHEMA,
        "level": LEVEL_CHORD_KARAOKE,
        "key": payload["key"],
        "meter": payload["meter"],
        "style": payload["style"],
        "routePreference": payload.get("routePreference", "balanced"),
        "homeFret": payload.get("homeFret", 6),
        "events": list(events),
    }
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validated_events(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_events = payload.get("events")
    if not isinstance(raw_events, list) or not raw_events:
        raise SongPracticeError("events must be a non-empty array")
    if len(raw_events) > MAX_EVENTS:
        raise SongPracticeError(f"events may contain at most {MAX_EVENTS} items")
    events: list[dict[str, Any]] = []
    previous_start = -1
    for index, raw_event in enumerate(raw_events, start=1):
        if not isinstance(raw_event, Mapping):
            raise SongPracticeError(f"events[{index - 1}] must be an object")
        event_id = str(raw_event.get("id") or f"chord-{index}").strip()
        measure_id = str(raw_event.get("measureId") or "").strip()
        section_id = str(raw_event.get("sectionId") or "").strip()
        chord = str(raw_event.get("chord") or "").strip()
        role = str(raw_event.get("role") or "comp").strip().lower()
        if role not in {"comp", "rest"}:
            raise SongPracticeError(f"events[{index - 1}].role is not available in Chord Karaoke")
        if role == "comp" and not chord:
            raise SongPracticeError(f"events[{index - 1}].chord is required")
        try:
            start_ms = int(raw_event.get("startMs"))
            end_ms = int(raw_event.get("endMs"))
        except (TypeError, ValueError) as exc:
            raise SongPracticeError(f"events[{index - 1}] requires integer startMs and endMs") from exc
        if start_ms < 0 or end_ms <= start_ms:
            raise SongPracticeError(f"events[{index - 1}] has an invalid time range")
        if start_ms < previous_start:
            raise SongPracticeError("events must be ordered by startMs")
        previous_start = start_ms
        event = {
            "id": event_id,
            "measureId": measure_id,
            "sectionId": section_id,
            "chord": chord,
            "startMs": start_ms,
            "endMs": end_ms,
            "role": role,
        }
        raw_hint = raw_event.get("positionHint")
        if raw_hint is not None:
            if not isinstance(raw_hint, Mapping):
                raise SongPracticeError(f"events[{index - 1}].positionHint must be an object")
            try:
                hint_fret = int(raw_hint.get("fret"))
                hint_strings = tuple(int(value) for value in raw_hint.get("strings", []))
                hint_controls = tuple(str(value) for value in raw_hint.get("controls", []))
            except (TypeError, ValueError) as exc:
                raise SongPracticeError(f"events[{index - 1}].positionHint is invalid") from exc
            if not 0 <= hint_fret <= MAX_FRET or len(hint_strings) != 3 or len(set(hint_strings)) != 3:
                raise SongPracticeError(f"events[{index - 1}].positionHint is invalid")
            event["positionHint"] = {
                "fret": hint_fret,
                "strings": list(hint_strings),
                "controls": list(hint_controls),
            }
        events.append(event)
    return events


def arrange_song_practice(
    request_payload: Mapping[str, Any],
    *,
    copedent_profile: E9CopedentProfile,
    copedent_revision: int,
) -> dict[str, Any]:
    if not isinstance(request_payload, Mapping):
        raise SongPracticeError("song-practice request must be an object")
    _reject_private_media_fields(request_payload)
    if request_payload.get("schemaVersion") != REQUEST_SCHEMA:
        raise SongPracticeError(f"schemaVersion must be {REQUEST_SCHEMA}")
    if request_payload.get("level") != LEVEL_CHORD_KARAOKE:
        raise SongPracticeError("Only Chord Karaoke is available in Stage 1")
    key = str(request_payload.get("key") or "").strip()
    if key not in NOTE_TO_SEMITONE:
        raise SongPracticeError("key must be a supported letter key")
    meter = str(request_payload.get("meter") or "").strip()
    if meter not in {"2/4", "3/4", "4/4", "6/8"}:
        raise SongPracticeError("meter must be 2/4, 3/4, 4/4, or 6/8")
    style = str(request_payload.get("style") or "classic_country").strip()[:40]
    route_preference = str(request_payload.get("routePreference") or "balanced").strip()
    if route_preference not in {"balanced", "move_bar", "stay_near"}:
        raise SongPracticeError("routePreference must be balanced, move_bar, or stay_near")
    try:
        home_fret = int(request_payload.get("homeFret", (NOTE_TO_SEMITONE[key] - NOTE_TO_SEMITONE["E"]) % 12))
    except (TypeError, ValueError) as exc:
        raise SongPracticeError("homeFret must be an integer from 0 through 24") from exc
    if not 0 <= home_fret <= MAX_FRET:
        raise SongPracticeError("homeFret must be an integer from 0 through 24")
    normalized_payload = {
        "key": key,
        "meter": meter,
        "style": style,
        "routePreference": route_preference,
        "homeFret": home_fret,
    }
    events = _validated_events(request_payload)

    parsed: list[ParsedChord | None] = [
        parse_chord_symbol(event["chord"]) if event["role"] == "comp" else None
        for event in events
    ]
    cache: dict[tuple[str, str], list[ChordCandidate]] = {}
    groups: list[list[ChordCandidate] | None] = []
    for event, chord in zip(events, parsed, strict=True):
        if event["role"] == "rest" or chord is None:
            groups.append(None)
            continue
        cache_key = (chord.root, chord.quality)
        if cache_key not in cache:
            cache[cache_key] = _chord_candidates(chord, copedent_profile)
        groups.append(cache[cache_key] or None)
    selected = _coherent_route(groups, route_preference=route_preference, home_fret=home_fret)
    for index, (event, group) in enumerate(zip(events, groups, strict=True)):
        hint = event.get("positionHint")
        if not hint or not group:
            continue
        hinted_candidate = next(
            (
                candidate
                for candidate in group
                if candidate.fret == hint["fret"]
                and list(candidate.strings) == hint["strings"]
                and set(candidate.controls) == set(hint["controls"])
            ),
            None,
        )
        if hinted_candidate is None:
            raise SongPracticeError(f"events[{index}].positionHint is not pitch-valid for {event['chord']}")
        selected[index] = hinted_candidate

    planned_events: list[dict[str, Any]] = []
    warnings: list[str] = []
    for index, (event, chord, candidate, group) in enumerate(
        zip(events, parsed, selected, groups, strict=True),
        start=1,
    ):
        planned = dict(event)
        if event["role"] == "rest":
            planned.update({"status": "rest", "position": None, "alternatives": []})
        elif chord is None or candidate is None or not group:
            planned.update(
                {
                    "status": "manual_position_needed",
                    "position": None,
                    "alternatives": [],
                    "warning": f"{event['chord']} needs a manually reviewed E9 position.",
                }
            )
            warnings.append(planned["warning"])
        else:
            position = _position_payload(
                candidate,
                chord=chord,
                profile=copedent_profile,
                position_id=f"song-position-{index}",
            )
            alternative_candidates = [item for item in group if item != candidate][:3]
            alternatives = [
                _position_payload(
                    item,
                    chord=chord,
                    profile=copedent_profile,
                    position_id=f"song-position-{index}-alt-{alternative_index}",
                )
                for alternative_index, item in enumerate(alternative_candidates, start=1)
            ]
            planned.update(
                {
                    "status": "ready",
                    "position": position,
                    "alternatives": alternatives,
                }
            )
            if chord.bass:
                planned["disclosure"] = f"Slash bass {chord.bass} is not represented by the upper E9 grip."
        planned_events.append(planned)

    timeline_hash = _canonical_timeline_hash(normalized_payload, events)
    return {
        "schemaVersion": PLAN_SCHEMA,
        "level": LEVEL_CHORD_KARAOKE,
        "timelineHash": timeline_hash,
        "targetCopedentId": copedent_profile.id,
        "targetCopedentLabel": copedent_profile.label,
        "targetCopedentRevision": int(copedent_revision),
        "route": {
            "id": f"song-route-{timeline_hash[:12]}",
            "label": "Recommended chord route",
            "coherentAcrossChart": True,
            "preference": route_preference,
            "homeFret": home_fret,
            "selectionPriorities": [
                "hard pitch and chord-tone validity",
                "common sounding voices",
                "grip continuity",
                "fret travel",
                "familiar control posture",
            ],
        },
        "events": planned_events,
        "warnings": list(dict.fromkeys(warnings)),
        "provenance": {
            "kind": "deterministic_e9_chord_route",
            "audioReceived": False,
            "lyricsReceived": False,
            "ragUsed": False,
            "stage": 1,
        },
    }


def _play_along_melody_position(event: Mapping[str, Any], chord_symbol: str) -> dict[str, Any] | None:
    raw_notes = event.get("notes")
    if not isinstance(raw_notes, list) or not raw_notes:
        return None
    pitch_by_string = event.get("mechanicalPitchesByString") or {}
    note_by_string = event.get("mechanicalNotesByString") or {}
    notes: list[dict[str, Any]] = []
    for raw_note in raw_notes:
        string = int(raw_note["string"])
        pitch = int(pitch_by_string[str(string)])
        changes = [str(change) for change in raw_note.get("changes") or []]
        notes.append(
            {
                "string": string,
                "fret": int(raw_note["fret"]),
                "pitch": pitch,
                "pitchLabel": scientific_pitch_for_value(pitch),
                "note": str(note_by_string.get(str(string)) or CANONICAL_NOTES[pitch % 12]),
                "changes": changes,
                "changeLabels": changes,
            }
        )
    melody_pitch = int(event["pitchValue"])
    melody_note = next((note for note in notes if note["pitch"] == melody_pitch), None)
    if melody_note is None or melody_pitch != max(note["pitch"] for note in notes):
        raise SongPracticeError("Amazing Tablature did not keep the exact melody as the highest voice")
    parsed_chord = parse_chord_symbol(chord_symbol)
    strings = [note["string"] for note in notes]
    return {
        "id": str(event.get("renderablePositionId") or event.get("id") or ""),
        "status": "validated",
        "validation": ["exact_melody_pitch", "top_voice", "mechanical_controls"],
        "root": parsed_chord.root if parsed_chord else chord_symbol,
        "quality": parsed_chord.quality if parsed_chord else "major",
        "fret": notes[0]["fret"],
        "strings": strings,
        "grip": str(event.get("canonicalGrip") or "-".join(str(string) for string in strings)),
        "controls": [str(control) for control in event.get("performanceControls") or []],
        "controlLabels": [str(control) for control in event.get("performanceControlLabels") or []],
        "pedals": [str(control) for control in event.get("pedalControls") or []],
        "levers": [str(control) for control in event.get("leverControls") or []],
        "notes": notes,
        "melodyString": melody_note["string"],
        "melodyPitchValue": melody_pitch,
        "melodyPitchLabel": str(event.get("resolvedPitch") or scientific_pitch_for_value(melody_pitch)),
        "instruction": str(event.get("explanation") or "Exact melody position validated by Amazing Tablature."),
    }


def build_play_along_melody_lessons(
    exercise: Mapping[str, Any],
    timeline: Sequence[Mapping[str, Any]],
    *,
    opening_chord_melody_events: int = 0,
) -> dict[str, Any]:
    """Join reviewed audio-clock events to validated Amazing Tablature routes."""

    source_events = [dict(event) for event in timeline]
    if not source_events or len(source_events) > MAX_EVENTS:
        raise SongPracticeError("playAlongTimeline must contain confirmed melody events")
    routes = exercise.get("publicRoutes") or exercise.get("routes") or []
    if not isinstance(routes, list):
        raise SongPracticeError("Amazing Tablature routes are unavailable")
    routes_by_type = {
        str(route.get("harmonyType")): route
        for route in routes
        if isinstance(route, Mapping)
    }
    mixed = routes_by_type.get("mixed_arrangement")
    chord_melody = routes_by_type.get("chord_melody")
    if mixed is None or chord_melody is None:
        raise SongPracticeError("Amazing Tablature did not return both melody lesson routes")

    opening_count = max(0, min(int(opening_chord_melody_events), len(source_events)))
    lesson_specs = (
        ("follow-melody", mixed, opening_count),
        ("full-chord-melody", chord_melody, 0),
    )
    lessons: list[dict[str, Any]] = []
    for lesson_id, route, use_opening_count in lesson_specs:
        route_events = list(route.get("events") or [])
        chord_events = list(chord_melody.get("events") or [])
        if len(route_events) != len(source_events) or len(chord_events) != len(source_events):
            raise SongPracticeError("Amazing Tablature did not preserve every reviewed melody event")
        joined: list[dict[str, Any]] = []
        for index, source in enumerate(source_events):
            arranged = dict(chord_events[index] if index < use_opening_count else route_events[index])
            expected_pitch = int(source["pitchValue"])
            if int(arranged["pitchValue"]) != expected_pitch:
                raise SongPracticeError("Amazing Tablature changed a reviewed melody pitch or register")
            chord = str(source.get("chord") or arranged.get("harmonySymbol") or arranged.get("activeChord") or "")
            position = _play_along_melody_position(arranged, chord)
            alternatives = []
            for alternative in arranged.get("alternatePositions") or []:
                pitch_values = [int(value) for value in alternative.get("pitchValues") or []]
                if pitch_values and max(pitch_values) == expected_pitch:
                    alternatives.append(dict(alternative))
            joined_event = dict(arranged)
            joined_event.update(
                {
                    "id": str(source.get("id") or arranged.get("id") or f"melody-event-{index + 1}"),
                    "chord": chord,
                    "startMs": int(source["startMs"]),
                    "endMs": int(source["endMs"]),
                    "durationBeats": float(source["durationBeats"]),
                    "measure": int(source["measure"]),
                    "beat": float(source["beat"]),
                    "bar": int(source["bar"]),
                    "isPickup": bool(source.get("isPickup")),
                    "sectionId": str(source.get("sectionId") or ""),
                    "phrase": str(source.get("phrase") or ""),
                    "position": position,
                    "supportingPitches": list(arranged.get("supportingPitches") or []),
                    "alternatives": alternatives[:2],
                }
            )
            if index == 2 and position and position["grip"] == "3-4-5":
                joined_event["selectionReason"] = (
                    "Strings 3–4–5 put B4 above G4 and D4. Staying on 4–5–6 at fret 3 "
                    "would leave G4 on top."
                )
            joined.append(joined_event)
        lessons.append(
            {
                "id": lesson_id,
                "route": {
                    "id": str(route.get("id") or lesson_id),
                    "label": str(route.get("label") or lesson_id),
                    "recommendation": str(route.get("recommendation") or ""),
                },
                "events": joined,
            }
        )
    return {"schemaVersion": "play_along_melody_lessons_v1", "lessons": lessons}


def _manifest_payload() -> dict[str, Any]:
    try:
        payload = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SongPracticeError("song-practice track manifest is unavailable") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("tracks"), list):
        raise SongPracticeError("song-practice track manifest is invalid")
    return payload


def _validated_track(track: Mapping[str, Any]) -> dict[str, Any] | None:
    required = {
        "id",
        "title",
        "compositionSource",
        "compositionStatus",
        "arrangementOwner",
        "arrangementRightsBasis",
        "masterOwner",
        "masterRightsBasis",
        "performerCredits",
        "checksumSha256",
        "durationMs",
        "key",
        "meter",
        "barStartsMs",
        "noSteel",
        "melodyLead",
        "countInBars",
        "learnerReady",
        "audioPath",
        "launchStatus",
    }
    if any(track.get(field) is None or track.get(field) == "" or track.get(field) is False for field in required) or track.get("noSteel") is not True:
        return None
    asset = (_REPO_ROOT / str(track["audioPath"])).resolve()
    try:
        asset.relative_to((_REPO_ROOT / "ui" / "assets" / "song-practice").resolve())
        size = asset.stat().st_size
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    except (OSError, ValueError):
        return None
    if size >= TRACKED_ASSET_LIMIT or digest != track.get("checksumSha256"):
        return None
    starts = track.get("barStartsMs")
    if not isinstance(starts, list) or not starts or any(not isinstance(value, int) or value < 0 for value in starts):
        return None
    beat_times = track.get("beatTimesMs") or []
    if beat_times and (
        not isinstance(beat_times, list)
        or any(not isinstance(value, int) or value < 0 for value in beat_times)
        or beat_times != sorted(set(beat_times))
        or any(start not in beat_times for start in starts)
    ):
        return None
    route_options = track.get("routeOptions") or []
    if route_options and (
        not isinstance(route_options, list)
        or any(
            not isinstance(option, Mapping)
            or not str(option.get("id") or "").strip()
            or not str(option.get("label") or "").strip()
            or not isinstance(option.get("positions"), list)
            or len(option["positions"]) != len(starts)
            for option in route_options
        )
    ):
        return None
    default_route_id = str(track.get("defaultRouteId") or "")
    default_route = next((option for option in route_options if option.get("id") == default_route_id), None)
    if route_options and default_route is None:
        return None
    authored_route = list(default_route.get("positions") or []) if default_route else list(track.get("authoredRoute") or [])
    if authored_route and len(authored_route) != len(starts):
        return None
    rights_document_url = ""
    rights_document_path = track.get("rightsDocumentPath")
    if rights_document_path:
        rights_asset = (_REPO_ROOT / str(rights_document_path)).resolve()
        try:
            rights_asset.relative_to((_REPO_ROOT / "ui" / "assets" / "song-practice").resolve())
            rights_digest = hashlib.sha256(rights_asset.read_bytes()).hexdigest()
        except (OSError, ValueError):
            return None
        if rights_digest != track.get("rightsDocumentChecksumSha256"):
            return None
        rights_document_url = "/" + str(rights_document_path).lstrip("/")
    project_id = track.get("projectId") or track["id"]
    audio_url = "/" + str(track["audioPath"]).lstrip("/")
    try:
        melody_timeline, melody_source = _amazing_grace_melody_timeline(track)
    except (KeyError, OSError, TypeError, ValueError, SongPracticeError):
        return None
    readiness_issues: list[str] = []
    launch_status = str(track["launchStatus"])
    if "review_required" in launch_status:
        readiness_issues.append("recording rights")
    if not (melody_timeline or authored_route or route_options):
        readiness_issues.append("beginner E9 route")
    if not track.get("chart") or not starts:
        readiness_issues.append("synchronized chord timeline")
    play_along_ready = bool(
        track["learnerReady"]
        and track.get("publicationState") != "coming_soon"
        and not readiness_issues
    )
    if play_along_ready:
        availability_label = "Play Along"
        availability_reason = ""
    elif "recording rights" in readiness_issues and "beginner E9 route" in readiness_issues:
        availability_label = "Track & lesson in review"
        availability_reason = "The recording rights and beginner E9 route must be approved before this lesson opens."
    elif "recording rights" in readiness_issues:
        availability_label = "Track in review"
        availability_reason = "The recording rights must be approved before this lesson opens."
    else:
        availability_label = "Lesson in review"
        availability_reason = "The synchronized beginner E9 lesson must be approved before this song opens."
    practice_project = {
        "schemaVersion": "practice_project_v1",
        "id": project_id,
        "audio": {
            "kind": "bundled",
            "url": audio_url,
            "durationMs": track["durationMs"],
        },
        "timeline": {
            "meter": track["meter"],
            "beatTimesMs": beat_times,
            "barStartsMs": starts,
            "chart": track.get("chart") or "",
            "melodyEvents": melody_timeline,
            "confirmationState": "confirmed",
        },
        "sections": track.get("sections") or [],
        "lyrics": track.get("lyricCues") or [],
        "e9Profile": {"defaultProfileId": "emmons-e9-basic"},
        "loop": {"enabled": False, "startMs": 0, "endMs": 0},
        "authoredRoute": authored_route,
        "defaultRouteId": default_route_id,
        "routeOptions": route_options,
        "melodySource": melody_source,
    }
    return {
        "id": track["id"],
        "projectId": project_id,
        "title": track["title"],
        "performer": track.get("performer") or track["performerCredits"],
        "description": track.get("description") or "Follow a prepared chord route with synchronized audio.",
        "difficulty": track.get("difficulty") or "Beginner",
        "teachingFocus": track.get("teachingFocus") or "Smooth chord changes",
        "tempo": track.get("tempo"),
        "recordingCredit": track.get("recordingCredit") or track["performerCredits"],
        "rightsUrl": track.get("rightsUrl") or "",
        "rightsDocumentUrl": rights_document_url,
        "license": track.get("license") or "",
        "licenseUrl": track.get("licenseUrl") or "",
        "modifications": track.get("modifications") or "",
        "publicationState": track.get("publicationState") or "private_preview",
        "playAlongReady": play_along_ready,
        "availabilityLabel": availability_label,
        "availabilityReason": availability_reason,
        "compositionSource": track["compositionSource"],
        "compositionStatus": track["compositionStatus"],
        "arrangementOwner": track["arrangementOwner"],
        "masterOwner": track["masterOwner"],
        "performerCredits": track["performerCredits"],
        "durationMs": track["durationMs"],
        "key": track["key"],
        "meter": track["meter"],
        "beatTimesMs": beat_times,
        "barStartsMs": starts,
        "chart": track.get("chart") or "",
        "sections": track.get("sections") or [],
        "lyricCues": track.get("lyricCues") or [],
        "melodyTimeline": melody_timeline,
        "melodySource": melody_source,
        "authoredRoute": authored_route,
        "defaultRouteId": default_route_id,
        "routeOptions": route_options,
        "noSteel": True,
        "melodyLead": track["melodyLead"],
        "countInBars": track["countInBars"],
        "learnerReady": track["learnerReady"],
        "audioUrl": audio_url,
        "practiceProject": practice_project,
        "launchStatus": track["launchStatus"],
    }


def list_curated_lessons() -> list[dict[str, Any]]:
    manifest = _manifest_payload()
    tracks = [validated for item in manifest["tracks"] if (validated := _validated_track(item))]
    try:
        approved_projects = published_project_ids()
    except SongCatalogPipelineError as exc:
        raise SongPracticeError("song catalog publication registry is invalid") from exc
    published = [
        track
        for track in tracks
        if track.get("playAlongReady") is True and track.get("projectId") in approved_projects
    ]
    return sorted(published, key=lambda item: _CURATED_ORDER.get(str(item.get("projectId")), 999))


def get_curated_practice_project(project_id: str) -> dict[str, Any] | None:
    normalized = str(project_id or "").strip()
    for lesson in list_curated_lessons():
        if lesson.get("projectId") == normalized or lesson.get("id") == normalized:
            return lesson if lesson.get("playAlongReady") is True else None
    return None


def song_practice_catalog() -> dict[str, Any]:
    return {
        "schemaVersion": CATALOG_SCHEMA,
        "tracks": list_curated_lessons(),
        "rightsNotice": (
            "Curated masters are loaded only when opened. Device imports remain local to this browser."
        ),
    }
