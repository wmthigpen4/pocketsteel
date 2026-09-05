"""Read-only projection from RAG Song Practice plans into the shared timeline."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from typing import Literal, cast

from packages.song_model.core import (
    SCHEMA_VERSION,
    ChordBody,
    ClockDomain,
    FretboardPosition,
    MechanicalValidity,
    NoteState,
    SongStructure,
    SongTimeline,
    SteelBody,
    SteelNote,
    TimedEvent,
    validate_timeline,
)
from packages.steel_theory import CopedentProfile, resolve_note


DiagnosticSeverity = Literal["warning", "error"]
RAG_PLAN_SCHEMA = "song_practice_plan_v1"
MECHANICAL_CHECKS = (
    "string-bounds",
    "fret-bounds",
    "controls-defined",
    "pitch-consistency",
)


@dataclass(frozen=True)
class AdapterDiagnostic:
    severity: DiagnosticSeverity
    code: str
    path: str
    summary: str


@dataclass(frozen=True)
class RagTimelineProjection:
    timeline: SongTimeline | None
    product_metadata: Mapping[str, object]
    diagnostics: tuple[AdapterDiagnostic, ...]

    @property
    def errors(self) -> tuple[AdapterDiagnostic, ...]:
        return tuple(item for item in self.diagnostics if item.severity == "error")

    @property
    def warnings(self) -> tuple[AdapterDiagnostic, ...]:
        return tuple(item for item in self.diagnostics if item.severity == "warning")


class _AdapterInputError(ValueError):
    def __init__(self, code: str, path: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.path = path
        self.summary = summary


def _mapping(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise _AdapterInputError("invalid_shape", path, "Expected an object")
    return cast(Mapping[str, object], value)


def _sequence(value: object, path: str) -> Sequence[object]:
    if not isinstance(value, (list, tuple)):
        raise _AdapterInputError("invalid_shape", path, "Expected an array")
    return cast(Sequence[object], value)


def _string(value: object, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise _AdapterInputError("invalid_value", path, "Expected a non-empty string")
    return value


def _integer(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise _AdapterInputError("invalid_value", path, "Expected an integer")
    return value


def _string_tuple(value: object, path: str) -> tuple[str, ...]:
    controls = tuple(
        _string(item, f"{path}[{index}]")
        for index, item in enumerate(_sequence(value, path))
    )
    if controls != tuple(sorted(set(controls))):
        raise _AdapterInputError(
            "controls_not_canonical",
            path,
            "Controls must be sorted and unique",
        )
    return controls


def _source_copy(source: Mapping[str, object]) -> dict[str, object]:
    return deepcopy(dict(source))


def _error_result(
    source: Mapping[str, object],
    issue: _AdapterInputError,
    diagnostics: Sequence[AdapterDiagnostic] = (),
) -> RagTimelineProjection:
    return RagTimelineProjection(
        timeline=None,
        product_metadata=_source_copy(source),
        diagnostics=tuple(diagnostics)
        + (AdapterDiagnostic("error", issue.code, issue.path, issue.summary),),
    )


def _metadata_and_diagnostics(
    source: Mapping[str, object],
) -> tuple[dict[str, object], list[AdapterDiagnostic]]:
    """Remove mapped values while preserving every RAG-only source field."""

    metadata = _source_copy(source)
    diagnostics: list[AdapterDiagnostic] = []
    for key in ("targetCopedentId", "targetCopedentRevision", "timelineHash"):
        metadata.pop(key, None)

    raw_events = _sequence(metadata.get("events"), "$.events")
    event_metadata: list[dict[str, object]] = []
    for event_index, raw_event in enumerate(raw_events):
        event_path = f"$.events[{event_index}]"
        item = dict(_mapping(raw_event, event_path))
        for key in ("measureId", "sectionId", "chord", "startMs", "endMs", "role"):
            item.pop(key, None)
        raw_position = item.get("position")
        if raw_position is not None:
            position = dict(_mapping(raw_position, f"{event_path}.position"))
            for key in ("fret", "strings", "controls"):
                position.pop(key, None)
            raw_notes = _sequence(position.get("notes"), f"{event_path}.position.notes")
            note_metadata: list[dict[str, object]] = []
            for note_index, raw_note in enumerate(raw_notes):
                note = dict(_mapping(raw_note, f"{event_path}.position.notes[{note_index}]"))
                for key in ("fret", "changes", "pitch", "pitchLabel"):
                    note.pop(key, None)
                for key in note:
                    if key != "string":
                        diagnostics.append(
                            AdapterDiagnostic(
                                "warning",
                                "product_field_retained",
                                f"{event_path}.position.notes[{note_index}].{key}",
                                "RAG-only note metadata remains outside the shared timeline",
                            )
                        )
                note_metadata.append(note)
            position["notes"] = note_metadata
            for key in position:
                if key not in {"id", "notes"}:
                    diagnostics.append(
                        AdapterDiagnostic(
                            "warning",
                            "product_field_retained",
                            f"{event_path}.position.{key}",
                            "RAG-only position metadata remains outside the shared timeline",
                        )
                    )
            item["position"] = position
        for key in item:
            if key not in {"id", "position"}:
                diagnostics.append(
                    AdapterDiagnostic(
                        "warning",
                        "product_field_retained",
                        f"{event_path}.{key}",
                        "RAG-only event metadata remains outside the shared timeline",
                    )
                )
        event_metadata.append(item)
    metadata["events"] = event_metadata

    for key in metadata:
        if key != "events":
            diagnostics.append(
                AdapterDiagnostic(
                    "warning",
                    "product_field_retained",
                    f"$.{key}",
                    "RAG-only plan metadata remains outside the shared timeline",
                )
            )
    return metadata, diagnostics


def _position_from_source(
    value: object,
    *,
    path: str,
    profile: CopedentProfile,
) -> FretboardPosition:
    source = _mapping(value, path)
    position_id = _string(source.get("id"), f"{path}.id")
    position_fret = _integer(source.get("fret"), f"{path}.fret")
    position_strings = tuple(
        _integer(item, f"{path}.strings[{index}]")
        for index, item in enumerate(_sequence(source.get("strings"), f"{path}.strings"))
    )
    position_controls = _string_tuple(source.get("controls"), f"{path}.controls")

    notes: list[NoteState] = []
    for note_index, raw_note in enumerate(_sequence(source.get("notes"), f"{path}.notes")):
        note_path = f"{path}.notes[{note_index}]"
        note = _mapping(raw_note, note_path)
        string = _integer(note.get("string"), f"{note_path}.string")
        fret = _integer(note.get("fret"), f"{note_path}.fret")
        controls = _string_tuple(note.get("changes"), f"{note_path}.changes")
        source_midi = _integer(note.get("pitch"), f"{note_path}.pitch")
        source_label = _string(note.get("pitchLabel"), f"{note_path}.pitchLabel")
        try:
            resolved = resolve_note(profile, string=string, fret=fret, controls=controls)
        except ValueError as exc:
            raise _AdapterInputError("invalid_mechanical_state", note_path, str(exc)) from exc
        if (source_midi, source_label) != (resolved.midi, resolved.label):
            raise _AdapterInputError(
                "pitch_mismatch",
                note_path,
                "RAG pitch does not match the shared copedent state",
            )
        notes.append(NoteState(string, fret, controls, resolved.midi, resolved.label))

    if not notes:
        raise _AdapterInputError("missing_notes", f"{path}.notes", "A shared position requires notes")
    if position_fret != notes[0].fret or any(note.fret != position_fret for note in notes):
        raise _AdapterInputError(
            "position_fret_mismatch",
            f"{path}.fret",
            "Position fret does not match every note",
        )
    if position_strings != tuple(note.string for note in notes):
        raise _AdapterInputError(
            "position_string_mismatch",
            f"{path}.strings",
            "Position strings do not match note order",
        )
    note_controls = {control for note in notes for control in note.controls}
    if set(position_controls) != note_controls:
        raise _AdapterInputError(
            "position_control_mismatch",
            f"{path}.controls",
            "Position controls do not match the controls used by its notes",
        )
    return FretboardPosition(
        id=f"rag:position:{position_id}",
        notes=tuple(notes),
        validity=MechanicalValidity("valid", MECHANICAL_CHECKS),
    )


def project_rag_song_practice(
    source: Mapping[str, object],
    *,
    copedent: CopedentProfile,
) -> RagTimelineProjection:
    """Project one RAG plan without mutating or replacing its source record."""

    try:
        metadata, diagnostics = _metadata_and_diagnostics(source)
        schema = _string(source.get("schemaVersion"), "$.schemaVersion")
        if schema != RAG_PLAN_SCHEMA:
            raise _AdapterInputError(
                "unsupported_schema",
                "$.schemaVersion",
                f"Expected {RAG_PLAN_SCHEMA}",
            )
        source_profile_id = _string(source.get("targetCopedentId"), "$.targetCopedentId")
        source_revision = _integer(source.get("targetCopedentRevision"), "$.targetCopedentRevision")
        if (source_profile_id, source_revision) != (copedent.id, copedent.revision):
            raise _AdapterInputError(
                "copedent_identity_mismatch",
                "$.targetCopedentId",
                "RAG plan copedent identity/revision does not match the supplied shared profile",
            )
        timeline_hash = _string(source.get("timelineHash"), "$.timelineHash")
        raw_events = _sequence(source.get("events"), "$.events")
        if not raw_events:
            raise _AdapterInputError("missing_events", "$.events", "RAG plan has no events")

        positions_by_id: dict[str, FretboardPosition] = {}
        source_events: list[tuple[Mapping[str, object], FretboardPosition, int, int]] = []
        source_order: list[tuple[int, int, str]] = []
        for event_index, raw_event in enumerate(raw_events):
            event_path = f"$.events[{event_index}]"
            event = _mapping(raw_event, event_path)
            event_id = _string(event.get("id"), f"{event_path}.id")
            start_ms = _integer(event.get("startMs"), f"{event_path}.startMs")
            end_ms = _integer(event.get("endMs"), f"{event_path}.endMs")
            if not 0 <= start_ms < end_ms:
                raise _AdapterInputError(
                    "invalid_event_range",
                    event_path,
                    "Event timing must be a positive half-open range",
                )
            status = _string(event.get("status"), f"{event_path}.status")
            if status != "ready" or event.get("position") is None:
                raise _AdapterInputError(
                    "event_not_projectable",
                    event_path,
                    "Only ready RAG events with resolved positions can enter the shared timeline",
                )
            position = _position_from_source(
                event.get("position"),
                path=f"{event_path}.position",
                profile=copedent,
            )
            previous = positions_by_id.get(position.id)
            if previous is not None and previous != position:
                raise _AdapterInputError(
                    "position_id_conflict",
                    f"{event_path}.position.id",
                    "One RAG position id resolves to different mechanical states",
                )
            positions_by_id[position.id] = position
            source_events.append((event, position, start_ms, end_ms))
            source_order.append((start_ms, end_ms, event_id))

        if source_order != sorted(source_order):
            diagnostics.append(
                AdapterDiagnostic(
                    "warning",
                    "source_events_reordered",
                    "$.events",
                    "Shared events use canonical timing order; the RAG source remains unchanged",
                )
            )

        duration_ms = max(end_ms for _, _, _, end_ms in source_events)
        diagnostics.extend(
            (
                AdapterDiagnostic(
                    "warning",
                    "clock_duration_derived",
                    "$.events",
                    "RAG plan has no media duration; the projection ends at its final event",
                ),
                AdapterDiagnostic(
                    "warning",
                    "post_roll_selection_differs",
                    "$.events",
                    "RAG presentation retains the final item; canonical selection becomes null after it ends",
                ),
            )
        )

        structure_members: dict[tuple[str, str], list[tuple[str, int, int]]] = {}
        events: list[TimedEvent] = []
        for event, position, start_ms, end_ms in source_events:
            source_id = _string(event.get("id"), "$.events[].id")
            chord = _string(event.get("chord"), f"$.events[{source_id}].chord")
            role = _string(event.get("role"), f"$.events[{source_id}].role")
            if role not in {"comp", "melody", "harmony", "unspecified"}:
                raise _AdapterInputError(
                    "unsupported_role",
                    f"$.events[{source_id}].role",
                    "RAG event role has no shared steel-event equivalent",
                )
            section_id = _string(event.get("sectionId"), f"$.events[{source_id}].sectionId")
            measure_id = _string(event.get("measureId"), f"$.events[{source_id}].measureId")
            shared_structure_ids = (
                f"rag:section:{section_id}",
                f"rag:measure:{measure_id}",
            )
            chord_id = f"rag:chord:{source_id}"
            steel_id = f"rag:steel:{source_id}"
            for kind, raw_id in (("section", section_id), ("measure", measure_id)):
                structure_members.setdefault((kind, raw_id), []).extend(
                    ((chord_id, start_ms, end_ms), (steel_id, start_ms, end_ms))
                )
            events.extend(
                (
                    TimedEvent(
                        id=chord_id,
                        kind="chord",
                        track_id="chords",
                        clock_id="rag:media",
                        start_ms=start_ms,
                        end_ms=end_ms,
                        structure_ids=shared_structure_ids,
                        body=ChordBody(chord, position.id),
                    ),
                    TimedEvent(
                        id=steel_id,
                        kind="steel",
                        track_id="steel-main",
                        clock_id="rag:media",
                        start_ms=start_ms,
                        end_ms=end_ms,
                        structure_ids=shared_structure_ids,
                        body=SteelBody(
                            role=role,
                            chord_event_id=chord_id,
                            position_id=position.id,
                            notes=tuple(
                                SteelNote(
                                    note.string,
                                    note.fret,
                                    note.controls,
                                    note.midi,
                                    note.label,
                                    (),
                                    (),
                                )
                                for note in position.notes
                            ),
                            validity=MechanicalValidity("valid", MECHANICAL_CHECKS),
                        ),
                    ),
                )
            )

        structures: list[SongStructure] = []
        for kind in ("section", "measure"):
            for (member_kind, raw_id), members in sorted(structure_members.items()):
                if member_kind != kind:
                    continue
                shared_id = f"rag:{kind}:{raw_id}"
                structures.append(
                    SongStructure(
                        id=shared_id,
                        kind=kind,
                        clock_id="rag:media",
                        start_ms=min(start for _, start, _ in members),
                        end_ms=max(end for _, _, end in members),
                        event_ids=tuple(event_id for event_id, _, _ in members),
                    )
                )
                diagnostics.append(
                    AdapterDiagnostic(
                        "warning",
                        "structure_range_derived",
                        f"$.events.*.{kind}Id",
                        f"RAG {kind} ranges are derived from their referenced event boundaries",
                    )
                )

        canonical_events = tuple(
            sorted(
                events,
                key=lambda event: (
                    event.clock_id,
                    event.start_ms,
                    event.end_ms,
                    event.track_id,
                    event.id,
                ),
            )
        )
        timeline = SongTimeline(
            schema_version=SCHEMA_VERSION,
            id=f"rag:song-practice:{timeline_hash}",
            revision=1,
            clocks=(ClockDomain("rag:media", "media", duration_ms, None),),
            copedent=copedent,
            positions=tuple(positions_by_id[position_id] for position_id in sorted(positions_by_id)),
            structures=tuple(structures),
            events=canonical_events,
        )
        issues = validate_timeline(timeline)
        if issues:
            return RagTimelineProjection(
                timeline=None,
                product_metadata=metadata,
                diagnostics=tuple(diagnostics)
                + tuple(
                    AdapterDiagnostic("error", f"shared_{item.code}", item.path, item.summary)
                    for item in issues
                ),
            )
        return RagTimelineProjection(timeline, metadata, tuple(diagnostics))
    except _AdapterInputError as exc:
        return _error_result(source, exc)
