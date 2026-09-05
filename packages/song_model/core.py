"""Product-neutral song, clock, chord, and steel-event contract behavior."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from packages.steel_theory import (
    CopedentControl,
    CopedentProfile,
    ControlChange,
    StringTuning,
    canonical_snapshot,
    resolve_note,
    snapshot_digest,
)


SCHEMA_VERSION = "steel_platform_timeline_v1"
CLOCK_KINDS = frozenset({"media", "window"})
STRUCTURE_KINDS = frozenset({"section", "measure", "phrase"})
STEEL_ROLES = frozenset({"comp", "melody", "harmony", "unspecified"})
VALIDITY_STATUSES = frozenset({"valid", "invalid", "unverified"})
ARTICULATION_KINDS = frozenset({"pick", "repick", "sustain", "release", "unspecified"})
TRANSITION_KINDS = frozenset({"bar-slide", "control-change", "mixed", "unspecified"})


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    summary: str


class TimelineValidationError(ValueError):
    """Raised when a timeline cannot satisfy the shared contract."""

    def __init__(self, issues: Sequence[ValidationIssue]):
        self.issues = tuple(issues)
        detail = "; ".join(f"{issue.path}: {issue.summary}" for issue in self.issues)
        super().__init__(detail)


@dataclass(frozen=True)
class ClockParentMapping:
    parent_clock_id: str
    parent_start_ms: int


@dataclass(frozen=True)
class ClockDomain:
    id: str
    kind: str
    duration_ms: int
    parent_mapping: ClockParentMapping | None


@dataclass(frozen=True)
class MechanicalValidity:
    status: str
    checks: tuple[str, ...]


@dataclass(frozen=True)
class NoteState:
    string: int
    fret: int
    controls: tuple[str, ...]
    midi: int
    label: str


@dataclass(frozen=True)
class FretboardPosition:
    id: str
    notes: tuple[NoteState, ...]
    validity: MechanicalValidity


@dataclass(frozen=True)
class SongStructure:
    id: str
    kind: str
    clock_id: str
    start_ms: int
    end_ms: int
    event_ids: tuple[str, ...]


@dataclass(frozen=True)
class Articulation:
    kind: str


@dataclass(frozen=True)
class Transition:
    kind: str
    from_fret: int | None = None
    to_fret: int | None = None
    controls_added: tuple[str, ...] = ()
    controls_released: tuple[str, ...] = ()


@dataclass(frozen=True)
class SteelNote:
    string: int
    fret: int
    controls: tuple[str, ...]
    midi: int
    label: str
    articulations: tuple[Articulation, ...]
    transitions: tuple[Transition, ...]


@dataclass(frozen=True)
class ChordBody:
    symbol: str
    position_id: str | None


@dataclass(frozen=True)
class SteelBody:
    role: str
    chord_event_id: str | None
    position_id: str | None
    notes: tuple[SteelNote, ...]
    validity: MechanicalValidity


@dataclass(frozen=True)
class TimedEvent:
    id: str
    kind: str
    track_id: str
    clock_id: str
    start_ms: int
    end_ms: int
    structure_ids: tuple[str, ...]
    body: ChordBody | SteelBody


@dataclass(frozen=True)
class SongTimeline:
    schema_version: str
    id: str
    revision: int
    clocks: tuple[ClockDomain, ...]
    copedent: CopedentProfile
    positions: tuple[FretboardPosition, ...]
    structures: tuple[SongStructure, ...]
    events: tuple[TimedEvent, ...]


@dataclass(frozen=True)
class SelectionState:
    phase: str
    current_event_id: str | None
    next_event_id: str | None


def _issue(code: str, path: str, summary: str) -> TimelineValidationError:
    return TimelineValidationError((ValidationIssue(code, path, summary),))


def _mapping(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise _issue("type", path, "must be an object")
    return value


def _sequence(value: object, path: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise _issue("type", path, "must be an array")
    return value


def _fields(
    value: object,
    path: str,
    *,
    required: frozenset[str],
    optional: frozenset[str] = frozenset(),
) -> Mapping[str, object]:
    result = _mapping(value, path)
    names = set(result)
    missing = required - names
    unknown = names - required - optional
    if missing:
        raise _issue("missing-field", path, f"missing {', '.join(sorted(missing))}")
    if unknown:
        raise _issue("unknown-field", path, f"unknown {', '.join(sorted(unknown))}")
    return result


def _string(value: object, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise _issue("type", path, "must be a non-empty string")
    return value


def _integer(value: object, path: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise _issue("type", path, "must be an integer")
    return value


def _nullable_string(value: object, path: str) -> str | None:
    return None if value is None else _string(value, path)


def _string_tuple(value: object, path: str) -> tuple[str, ...]:
    return tuple(_string(item, f"{path}[{index}]") for index, item in enumerate(_sequence(value, path)))


def _enum(value: object, path: str, allowed: frozenset[str]) -> str:
    result = _string(value, path)
    if result not in allowed:
        raise _issue("enum", path, f"unsupported value {result!r}")
    return result


def _ensure_unique(values: Sequence[str], path: str) -> None:
    if len(set(values)) != len(values):
        raise _issue("duplicate", path, "values must be unique")


def _parse_profile(value: object, path: str) -> CopedentProfile:
    source = _fields(
        value,
        path,
        required=frozenset({"profileId", "revision", "snapshotDigest", "snapshot"}),
    )
    snapshot = _fields(
        source["snapshot"],
        f"{path}.snapshot",
        required=frozenset({"tuning", "stringOrder", "strings", "controls"}),
    )
    if snapshot["stringOrder"] != "numbered-high-to-low":
        raise _issue("string-order", f"{path}.snapshot.stringOrder", "must be numbered-high-to-low")

    strings: list[StringTuning] = []
    for index, raw_string in enumerate(_sequence(snapshot["strings"], f"{path}.snapshot.strings")):
        item_path = f"{path}.snapshot.strings[{index}]"
        item = _fields(raw_string, item_path, required=frozenset({"string", "openPitch"}))
        pitch = _fields(
            item["openPitch"],
            f"{item_path}.openPitch",
            required=frozenset({"midi", "label"}),
        )
        strings.append(
            StringTuning(
                _integer(item["string"], f"{item_path}.string"),
                _integer(pitch["midi"], f"{item_path}.openPitch.midi"),
                _string(pitch["label"], f"{item_path}.openPitch.label"),
            )
        )

    controls: list[CopedentControl] = []
    for index, raw_control in enumerate(_sequence(snapshot["controls"], f"{path}.snapshot.controls")):
        item_path = f"{path}.snapshot.controls[{index}]"
        item = _fields(raw_control, item_path, required=frozenset({"id", "changes"}))
        changes: list[ControlChange] = []
        for change_index, raw_change in enumerate(_sequence(item["changes"], f"{item_path}.changes")):
            change_path = f"{item_path}.changes[{change_index}]"
            change = _fields(raw_change, change_path, required=frozenset({"string", "semitones"}))
            changes.append(
                ControlChange(
                    _integer(change["string"], f"{change_path}.string"),
                    _integer(change["semitones"], f"{change_path}.semitones"),
                )
            )
        controls.append(CopedentControl(_string(item["id"], f"{item_path}.id"), tuple(changes)))

    try:
        profile = CopedentProfile(
            id=_string(source["profileId"], f"{path}.profileId"),
            revision=_integer(source["revision"], f"{path}.revision"),
            tuning=_string(snapshot["tuning"], f"{path}.snapshot.tuning"),
            strings=tuple(strings),
            controls=tuple(controls),
        )
    except ValueError as exc:
        raise _issue("copedent", path, str(exc)) from exc
    if canonical_snapshot(profile) != dict(snapshot):
        raise _issue("copedent-snapshot", f"{path}.snapshot", "is not in canonical form")
    digest = _string(source["snapshotDigest"], f"{path}.snapshotDigest")
    if digest != snapshot_digest(profile):
        raise _issue("digest", f"{path}.snapshotDigest", "does not match the canonical snapshot")
    return profile


def _parse_validity(value: object, path: str) -> MechanicalValidity:
    source = _fields(value, path, required=frozenset({"status", "checks"}))
    checks = _string_tuple(source["checks"], f"{path}.checks")
    _ensure_unique(checks, f"{path}.checks")
    return MechanicalValidity(
        _enum(source["status"], f"{path}.status", VALIDITY_STATUSES),
        checks,
    )


def _parse_note_state(value: object, path: str, profile: CopedentProfile) -> NoteState:
    source = _fields(
        value,
        path,
        required=frozenset({"string", "fret", "controls", "pitch"}),
    )
    controls = _string_tuple(source["controls"], f"{path}.controls")
    if controls != tuple(sorted(set(controls))):
        raise _issue("controls-order", f"{path}.controls", "must be sorted and unique")
    pitch = _fields(source["pitch"], f"{path}.pitch", required=frozenset({"midi", "label"}))
    string = _integer(source["string"], f"{path}.string")
    fret = _integer(source["fret"], f"{path}.fret")
    midi = _integer(pitch["midi"], f"{path}.pitch.midi")
    label = _string(pitch["label"], f"{path}.pitch.label")
    try:
        resolved = resolve_note(profile, string=string, fret=fret, controls=controls)
    except ValueError as exc:
        raise _issue("mechanical-state", path, str(exc)) from exc
    if (midi, label) != (resolved.midi, resolved.label):
        raise _issue("pitch", f"{path}.pitch", "does not match the copedent state")
    return NoteState(string, fret, controls, midi, label)


def _parse_transition(value: object, path: str, profile: CopedentProfile) -> Transition:
    source = _fields(
        value,
        path,
        required=frozenset({"kind"}),
        optional=frozenset({"fromFret", "toFret", "controlsAdded", "controlsReleased"}),
    )
    added = _string_tuple(source.get("controlsAdded", ()), f"{path}.controlsAdded")
    released = _string_tuple(source.get("controlsReleased", ()), f"{path}.controlsReleased")
    for field, controls in (("controlsAdded", added), ("controlsReleased", released)):
        if controls != tuple(sorted(set(controls))):
            raise _issue("controls-order", f"{path}.{field}", "must be sorted and unique")
        unknown = set(controls) - set(profile.controls_by_id())
        if unknown:
            raise _issue("control", f"{path}.{field}", f"unknown {', '.join(sorted(unknown))}")
    from_fret = None if "fromFret" not in source else _integer(source["fromFret"], f"{path}.fromFret")
    to_fret = None if "toFret" not in source else _integer(source["toFret"], f"{path}.toFret")
    for field, fret in (("fromFret", from_fret), ("toFret", to_fret)):
        if fret is not None and not 0 <= fret <= 24:
            raise _issue("fret", f"{path}.{field}", "must be between 0 and 24")
    return Transition(
        _enum(source["kind"], f"{path}.kind", TRANSITION_KINDS),
        from_fret,
        to_fret,
        added,
        released,
    )


def _parse_steel_note(value: object, path: str, profile: CopedentProfile) -> SteelNote:
    source = _fields(
        value,
        path,
        required=frozenset({"string", "fret", "controls", "pitch", "articulations", "transitions"}),
    )
    state = _parse_note_state(
        {name: source[name] for name in ("string", "fret", "controls", "pitch")},
        path,
        profile,
    )
    articulations: list[Articulation] = []
    for index, raw in enumerate(_sequence(source["articulations"], f"{path}.articulations")):
        item_path = f"{path}.articulations[{index}]"
        item = _fields(raw, item_path, required=frozenset({"kind"}))
        articulations.append(Articulation(_enum(item["kind"], f"{item_path}.kind", ARTICULATION_KINDS)))
    transitions = tuple(
        _parse_transition(raw, f"{path}.transitions[{index}]", profile)
        for index, raw in enumerate(_sequence(source["transitions"], f"{path}.transitions"))
    )
    return SteelNote(
        state.string,
        state.fret,
        state.controls,
        state.midi,
        state.label,
        tuple(articulations),
        transitions,
    )


def _parse_clock(value: object, path: str) -> ClockDomain:
    source = _fields(
        value,
        path,
        required=frozenset({"id", "kind", "durationMs", "parentMapping"}),
    )
    raw_mapping = source["parentMapping"]
    mapping = None
    if raw_mapping is not None:
        item = _fields(
            raw_mapping,
            f"{path}.parentMapping",
            required=frozenset({"parentClockId", "parentStartMs"}),
        )
        mapping = ClockParentMapping(
            _string(item["parentClockId"], f"{path}.parentMapping.parentClockId"),
            _integer(item["parentStartMs"], f"{path}.parentMapping.parentStartMs"),
        )
    return ClockDomain(
        _string(source["id"], f"{path}.id"),
        _enum(source["kind"], f"{path}.kind", CLOCK_KINDS),
        _integer(source["durationMs"], f"{path}.durationMs"),
        mapping,
    )


def _parse_position(value: object, path: str, profile: CopedentProfile) -> FretboardPosition:
    source = _fields(value, path, required=frozenset({"id", "notes", "validity"}))
    notes = tuple(
        _parse_note_state(raw, f"{path}.notes[{index}]", profile)
        for index, raw in enumerate(_sequence(source["notes"], f"{path}.notes"))
    )
    return FretboardPosition(
        _string(source["id"], f"{path}.id"),
        notes,
        _parse_validity(source["validity"], f"{path}.validity"),
    )


def _parse_structure(value: object, path: str) -> SongStructure:
    source = _fields(
        value,
        path,
        required=frozenset({"id", "kind", "clockId", "startMs", "endMs", "eventIds"}),
    )
    event_ids = _string_tuple(source["eventIds"], f"{path}.eventIds")
    _ensure_unique(event_ids, f"{path}.eventIds")
    return SongStructure(
        _string(source["id"], f"{path}.id"),
        _enum(source["kind"], f"{path}.kind", STRUCTURE_KINDS),
        _string(source["clockId"], f"{path}.clockId"),
        _integer(source["startMs"], f"{path}.startMs"),
        _integer(source["endMs"], f"{path}.endMs"),
        event_ids,
    )


def _parse_event(value: object, path: str, profile: CopedentProfile) -> TimedEvent:
    source = _fields(
        value,
        path,
        required=frozenset(
            {"id", "kind", "trackId", "clockId", "startMs", "endMs", "structureIds", "body"}
        ),
    )
    kind = _enum(source["kind"], f"{path}.kind", frozenset({"chord", "steel"}))
    body_path = f"{path}.body"
    if kind == "chord":
        body_source = _fields(source["body"], body_path, required=frozenset({"symbol", "positionId"}))
        body: ChordBody | SteelBody = ChordBody(
            _string(body_source["symbol"], f"{body_path}.symbol"),
            _nullable_string(body_source["positionId"], f"{body_path}.positionId"),
        )
    else:
        body_source = _fields(
            source["body"],
            body_path,
            required=frozenset({"role", "chordEventId", "positionId", "notes", "validity"}),
        )
        notes = tuple(
            _parse_steel_note(raw, f"{body_path}.notes[{index}]", profile)
            for index, raw in enumerate(_sequence(body_source["notes"], f"{body_path}.notes"))
        )
        body = SteelBody(
            _enum(body_source["role"], f"{body_path}.role", STEEL_ROLES),
            _nullable_string(body_source["chordEventId"], f"{body_path}.chordEventId"),
            _nullable_string(body_source["positionId"], f"{body_path}.positionId"),
            notes,
            _parse_validity(body_source["validity"], f"{body_path}.validity"),
        )
    structure_ids = _string_tuple(source["structureIds"], f"{path}.structureIds")
    _ensure_unique(structure_ids, f"{path}.structureIds")
    return TimedEvent(
        _string(source["id"], f"{path}.id"),
        kind,
        _string(source["trackId"], f"{path}.trackId"),
        _string(source["clockId"], f"{path}.clockId"),
        _integer(source["startMs"], f"{path}.startMs"),
        _integer(source["endMs"], f"{path}.endMs"),
        structure_ids,
        body,
    )


def timeline_from_dict(value: object) -> SongTimeline:
    """Parse and validate one strict v1 interchange document."""

    source = _fields(
        value,
        "$",
        required=frozenset(
            {"schemaVersion", "id", "revision", "clocks", "copedent", "positions", "structures", "events"}
        ),
    )
    version = _string(source["schemaVersion"], "$.schemaVersion")
    if version != SCHEMA_VERSION:
        raise _issue("schema-version", "$.schemaVersion", f"must be {SCHEMA_VERSION}")
    profile = _parse_profile(source["copedent"], "$.copedent")
    timeline = SongTimeline(
        version,
        _string(source["id"], "$.id"),
        _integer(source["revision"], "$.revision"),
        tuple(
            _parse_clock(raw, f"$.clocks[{index}]")
            for index, raw in enumerate(_sequence(source["clocks"], "$.clocks"))
        ),
        profile,
        tuple(
            _parse_position(raw, f"$.positions[{index}]", profile)
            for index, raw in enumerate(_sequence(source["positions"], "$.positions"))
        ),
        tuple(
            _parse_structure(raw, f"$.structures[{index}]")
            for index, raw in enumerate(_sequence(source["structures"], "$.structures"))
        ),
        tuple(
            _parse_event(raw, f"$.events[{index}]", profile)
            for index, raw in enumerate(_sequence(source["events"], "$.events"))
        ),
    )
    issues = validate_timeline(timeline)
    if issues:
        raise TimelineValidationError(issues)
    return timeline


def _ids_are_valid(items: Sequence[Any], path: str, issues: list[ValidationIssue]) -> None:
    ids = tuple(item.id for item in items)
    if not ids:
        issues.append(ValidationIssue("empty", path, "must not be empty"))
    if any(not item_id for item_id in ids):
        issues.append(ValidationIssue("id", path, "ids must be non-empty"))
    if len(set(ids)) != len(ids):
        issues.append(ValidationIssue("duplicate-id", path, "ids must be unique"))


def _validate_validity(validity: MechanicalValidity, path: str, issues: list[ValidationIssue]) -> None:
    if validity.status not in VALIDITY_STATUSES:
        issues.append(ValidationIssue("validity-status", f"{path}.status", "has an unsupported value"))
    if len(set(validity.checks)) != len(validity.checks) or any(not check for check in validity.checks):
        issues.append(ValidationIssue("validity-checks", f"{path}.checks", "must be non-empty unique strings"))


def _validate_note_state(
    note: NoteState | SteelNote,
    profile: CopedentProfile,
    path: str,
    issues: list[ValidationIssue],
) -> None:
    if note.controls != tuple(sorted(set(note.controls))):
        issues.append(ValidationIssue("controls-order", f"{path}.controls", "must be sorted and unique"))
    try:
        resolved = resolve_note(profile, string=note.string, fret=note.fret, controls=note.controls)
    except ValueError as exc:
        issues.append(ValidationIssue("mechanical-state", path, str(exc)))
        return
    if (note.midi, note.label) != (resolved.midi, resolved.label):
        issues.append(ValidationIssue("pitch", f"{path}.pitch", "does not match the copedent state"))


def _clock_root_range(
    clocks: Mapping[str, ClockDomain],
    clock_id: str,
    start_ms: int,
    end_ms: int,
) -> tuple[str, int, int]:
    seen: set[str] = set()
    while True:
        if clock_id in seen:
            raise ValueError("clock graph contains a cycle")
        seen.add(clock_id)
        clock = clocks[clock_id]
        if clock.parent_mapping is None:
            return clock_id, start_ms, end_ms
        start_ms += clock.parent_mapping.parent_start_ms
        end_ms += clock.parent_mapping.parent_start_ms
        clock_id = clock.parent_mapping.parent_clock_id


def map_clock_range_to_root(
    timeline: SongTimeline,
    clock_id: str,
    start_ms: int,
    end_ms: int,
) -> tuple[str, int, int]:
    """Map a local half-open range into its root media clock."""

    clocks = {clock.id: clock for clock in timeline.clocks}
    if clock_id not in clocks:
        raise ValueError(f"Unknown clock: {clock_id}")
    if not 0 <= start_ms < end_ms <= clocks[clock_id].duration_ms:
        raise ValueError("Clock range must fit its local clock")
    return _clock_root_range(clocks, clock_id, start_ms, end_ms)


def validate_timeline(timeline: SongTimeline) -> tuple[ValidationIssue, ...]:
    """Return all reference, range, graph, and ordering failures."""

    issues: list[ValidationIssue] = []
    if timeline.schema_version != SCHEMA_VERSION:
        issues.append(ValidationIssue("schema-version", "$.schemaVersion", f"must be {SCHEMA_VERSION}"))
    if not timeline.id:
        issues.append(ValidationIssue("id", "$.id", "must be a non-empty string"))
    if timeline.revision < 1:
        issues.append(ValidationIssue("revision", "$.revision", "must be positive"))

    _ids_are_valid(timeline.clocks, "$.clocks", issues)
    _ids_are_valid(timeline.positions, "$.positions", issues)
    _ids_are_valid(timeline.structures, "$.structures", issues)
    _ids_are_valid(timeline.events, "$.events", issues)
    clocks = {clock.id: clock for clock in timeline.clocks}
    positions = {position.id: position for position in timeline.positions}
    structures = {structure.id: structure for structure in timeline.structures}
    events = {event.id: event for event in timeline.events}

    for index, clock in enumerate(timeline.clocks):
        path = f"$.clocks[{index}]"
        if clock.kind not in CLOCK_KINDS:
            issues.append(ValidationIssue("clock-kind", f"{path}.kind", "has an unsupported value"))
        if clock.duration_ms <= 0:
            issues.append(ValidationIssue("duration", f"{path}.durationMs", "must be positive"))
        mapping = clock.parent_mapping
        if clock.kind == "media" and mapping is not None:
            issues.append(ValidationIssue("clock-kind", f"{path}.parentMapping", "media clocks must be roots"))
        if clock.kind == "window" and mapping is None:
            issues.append(ValidationIssue("clock-kind", f"{path}.parentMapping", "window clocks need a parent"))
        if mapping is not None:
            parent = clocks.get(mapping.parent_clock_id)
            if parent is None:
                issues.append(ValidationIssue("clock-reference", f"{path}.parentMapping", "parent does not exist"))
            elif mapping.parent_start_ms < 0 or mapping.parent_start_ms + clock.duration_ms > parent.duration_ms:
                issues.append(ValidationIssue("clock-window", f"{path}.parentMapping", "window does not fit parent"))
        try:
            _clock_root_range(clocks, clock.id, 0, max(clock.duration_ms, 1))
        except (KeyError, ValueError):
            issues.append(ValidationIssue("clock-graph", path, "clock graph must be complete and acyclic"))

    for index, position in enumerate(timeline.positions):
        path = f"$.positions[{index}]"
        if not position.notes:
            issues.append(ValidationIssue("position-notes", f"{path}.notes", "must not be empty"))
        _validate_validity(position.validity, f"{path}.validity", issues)
        for note_index, position_note in enumerate(position.notes):
            _validate_note_state(position_note, timeline.copedent, f"{path}.notes[{note_index}]", issues)

    for index, structure in enumerate(timeline.structures):
        path = f"$.structures[{index}]"
        if structure.kind not in STRUCTURE_KINDS:
            issues.append(ValidationIssue("structure-kind", f"{path}.kind", "has an unsupported value"))
        structure_clock = clocks.get(structure.clock_id)
        if structure_clock is None:
            issues.append(ValidationIssue("clock-reference", f"{path}.clockId", "clock does not exist"))
        elif not 0 <= structure.start_ms < structure.end_ms <= structure_clock.duration_ms:
            issues.append(ValidationIssue("range", path, "range must fit its clock"))
        for event_id in structure.event_ids:
            event = events.get(event_id)
            if event is None:
                issues.append(ValidationIssue("event-reference", f"{path}.eventIds", f"{event_id} does not exist"))
                continue
            if structure.id not in event.structure_ids:
                issues.append(ValidationIssue("structure-membership", f"{path}.eventIds", f"{event_id} is not reciprocal"))
            if structure_clock is not None and event.clock_id in clocks:
                try:
                    structure_range = _clock_root_range(
                        clocks, structure.clock_id, structure.start_ms, structure.end_ms
                    )
                    event_range = _clock_root_range(clocks, event.clock_id, event.start_ms, event.end_ms)
                    if (
                        structure_range[0] != event_range[0]
                        or not structure_range[1] <= event_range[1] < event_range[2] <= structure_range[2]
                    ):
                        issues.append(
                            ValidationIssue("structure-range", f"{path}.eventIds", f"{event_id} falls outside structure")
                        )
                except (KeyError, ValueError):
                    pass

    canonical_events = tuple(
        sorted(
            timeline.events,
            key=lambda event: (event.clock_id, event.start_ms, event.end_ms, event.track_id, event.id),
        )
    )
    if timeline.events != canonical_events:
        issues.append(ValidationIssue("event-order", "$.events", "events are not canonically ordered"))

    previous_by_track: dict[tuple[str, str], TimedEvent] = {}
    for index, event in enumerate(timeline.events):
        path = f"$.events[{index}]"
        expected_kind = "chord" if isinstance(event.body, ChordBody) else "steel"
        if event.kind != expected_kind:
            issues.append(ValidationIssue("event-kind", f"{path}.kind", f"must be {expected_kind} for its body"))
        if not event.track_id:
            issues.append(ValidationIssue("track-id", f"{path}.trackId", "must be non-empty"))
        event_clock = clocks.get(event.clock_id)
        if event_clock is None:
            issues.append(ValidationIssue("clock-reference", f"{path}.clockId", "clock does not exist"))
        elif not 0 <= event.start_ms < event.end_ms <= event_clock.duration_ms:
            issues.append(ValidationIssue("range", path, "range must fit its clock"))
        for structure_id in event.structure_ids:
            member_structure = structures.get(structure_id)
            if member_structure is None:
                issues.append(
                    ValidationIssue("structure-reference", f"{path}.structureIds", f"{structure_id} does not exist")
                )
            elif event.id not in member_structure.event_ids:
                issues.append(
                    ValidationIssue("structure-membership", f"{path}.structureIds", f"{structure_id} is not reciprocal")
                )
        key = (event.clock_id, event.track_id)
        previous = previous_by_track.get(key)
        if previous is not None and previous.end_ms > event.start_ms:
            issues.append(ValidationIssue("event-overlap", path, f"overlaps {previous.id} on the same track"))
        previous_by_track[key] = event

        position_id = event.body.position_id
        if position_id is not None and position_id not in positions:
            issues.append(ValidationIssue("position-reference", f"{path}.body.positionId", "position does not exist"))
        if isinstance(event.body, SteelBody):
            if event.body.role not in STEEL_ROLES:
                issues.append(ValidationIssue("steel-role", f"{path}.body.role", "has an unsupported value"))
            if not event.body.notes:
                issues.append(ValidationIssue("steel-notes", f"{path}.body.notes", "must not be empty"))
            _validate_validity(event.body.validity, f"{path}.body.validity", issues)
            for note_index, steel_note in enumerate(event.body.notes):
                note_path = f"{path}.body.notes[{note_index}]"
                _validate_note_state(steel_note, timeline.copedent, note_path, issues)
                for articulation_index, articulation in enumerate(steel_note.articulations):
                    if articulation.kind not in ARTICULATION_KINDS:
                        issues.append(
                            ValidationIssue(
                                "articulation-kind",
                                f"{note_path}.articulations[{articulation_index}].kind",
                                "has an unsupported value",
                            )
                        )
                for transition_index, transition in enumerate(steel_note.transitions):
                    transition_path = f"{note_path}.transitions[{transition_index}]"
                    if transition.kind not in TRANSITION_KINDS:
                        issues.append(
                            ValidationIssue("transition-kind", f"{transition_path}.kind", "has an unsupported value")
                        )
                    for field, fret in (("fromFret", transition.from_fret), ("toFret", transition.to_fret)):
                        if fret is not None and not 0 <= fret <= 24:
                            issues.append(
                                ValidationIssue("fret", f"{transition_path}.{field}", "must be between 0 and 24")
                            )
                    for field, controls in (
                        ("controlsAdded", transition.controls_added),
                        ("controlsReleased", transition.controls_released),
                    ):
                        if controls != tuple(sorted(set(controls))):
                            issues.append(
                                ValidationIssue(
                                    "controls-order",
                                    f"{transition_path}.{field}",
                                    "must be sorted and unique",
                                )
                            )
                        unknown = set(controls) - set(timeline.copedent.controls_by_id())
                        if unknown:
                            issues.append(
                                ValidationIssue(
                                    "control",
                                    f"{transition_path}.{field}",
                                    f"unknown {', '.join(sorted(unknown))}",
                                )
                            )
            chord_id = event.body.chord_event_id
            if chord_id is not None:
                chord = events.get(chord_id)
                if chord is None or not isinstance(chord.body, ChordBody):
                    issues.append(
                        ValidationIssue("chord-reference", f"{path}.body.chordEventId", "must reference a chord event")
                    )
                elif (
                    chord.clock_id != event.clock_id
                    or not chord.start_ms <= event.start_ms < event.end_ms <= chord.end_ms
                ):
                    issues.append(
                        ValidationIssue(
                            "chord-range",
                            f"{path}.body.chordEventId",
                            "chord must contain the steel event on the same clock",
                        )
                    )
    return tuple(issues)


def _validity_dict(validity: MechanicalValidity) -> dict[str, object]:
    return {"status": validity.status, "checks": list(validity.checks)}


def _note_state_dict(note: NoteState | SteelNote) -> dict[str, object]:
    return {
        "string": note.string,
        "fret": note.fret,
        "controls": list(note.controls),
        "pitch": {"midi": note.midi, "label": note.label},
    }


def timeline_to_dict(timeline: SongTimeline) -> dict[str, object]:
    """Serialize a valid timeline using the exact v1 field vocabulary."""

    issues = validate_timeline(timeline)
    if issues:
        raise TimelineValidationError(issues)
    events: list[dict[str, object]] = []
    for event in timeline.events:
        if isinstance(event.body, ChordBody):
            body: dict[str, object] = {
                "symbol": event.body.symbol,
                "positionId": event.body.position_id,
            }
        else:
            notes: list[dict[str, object]] = []
            for note in event.body.notes:
                note_value = _note_state_dict(note)
                note_value["articulations"] = [{"kind": item.kind} for item in note.articulations]
                transitions: list[dict[str, object]] = []
                for transition in note.transitions:
                    transition_value: dict[str, object] = {"kind": transition.kind}
                    if transition.from_fret is not None:
                        transition_value["fromFret"] = transition.from_fret
                    if transition.to_fret is not None:
                        transition_value["toFret"] = transition.to_fret
                    if transition.controls_added:
                        transition_value["controlsAdded"] = list(transition.controls_added)
                    if transition.controls_released:
                        transition_value["controlsReleased"] = list(transition.controls_released)
                    transitions.append(transition_value)
                note_value["transitions"] = transitions
                notes.append(note_value)
            body = {
                "role": event.body.role,
                "chordEventId": event.body.chord_event_id,
                "positionId": event.body.position_id,
                "notes": notes,
                "validity": _validity_dict(event.body.validity),
            }
        events.append(
            {
                "id": event.id,
                "kind": event.kind,
                "trackId": event.track_id,
                "clockId": event.clock_id,
                "startMs": event.start_ms,
                "endMs": event.end_ms,
                "structureIds": list(event.structure_ids),
                "body": body,
            }
        )
    return {
        "schemaVersion": timeline.schema_version,
        "id": timeline.id,
        "revision": timeline.revision,
        "clocks": [
            {
                "id": clock.id,
                "kind": clock.kind,
                "durationMs": clock.duration_ms,
                "parentMapping": None
                if clock.parent_mapping is None
                else {
                    "parentClockId": clock.parent_mapping.parent_clock_id,
                    "parentStartMs": clock.parent_mapping.parent_start_ms,
                },
            }
            for clock in timeline.clocks
        ],
        "copedent": {
            "profileId": timeline.copedent.id,
            "revision": timeline.copedent.revision,
            "snapshotDigest": snapshot_digest(timeline.copedent),
            "snapshot": canonical_snapshot(timeline.copedent),
        },
        "positions": [
            {
                "id": position.id,
                "notes": [_note_state_dict(note) for note in position.notes],
                "validity": _validity_dict(position.validity),
            }
            for position in timeline.positions
        ],
        "structures": [
            {
                "id": structure.id,
                "kind": structure.kind,
                "clockId": structure.clock_id,
                "startMs": structure.start_ms,
                "endMs": structure.end_ms,
                "eventIds": list(structure.event_ids),
            }
            for structure in timeline.structures
        ],
        "events": events,
    }


def canonical_timeline_json(timeline: SongTimeline) -> str:
    """Return reproducible UTF-8-compatible JSON without insignificant whitespace."""

    return json.dumps(timeline_to_dict(timeline), ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def timeline_digest(timeline: SongTimeline) -> str:
    payload = canonical_timeline_json(timeline).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def select_event(timeline: SongTimeline, *, clock_id: str, track_id: str, time_ms: int) -> SelectionState:
    """Select nullable current/next event IDs on one logical stream."""

    events = tuple(
        event for event in timeline.events if event.clock_id == clock_id and event.track_id == track_id
    )
    if not events:
        raise ValueError(f"No events for clock {clock_id!r} and track {track_id!r}")
    if time_ms < events[0].start_ms:
        return SelectionState("pre-roll", None, events[0].id)
    if time_ms >= events[-1].end_ms:
        return SelectionState("post-roll", None, None)
    for index, event in enumerate(events):
        next_id = events[index + 1].id if index + 1 < len(events) else None
        if event.start_ms <= time_ms < event.end_ms:
            return SelectionState("active", event.id, next_id)
        if time_ms < event.start_ms:
            return SelectionState("active", None, event.id)
    raise AssertionError("validated event selection must terminate")
