"""Read-only product copedent projections into the shared steel-theory core."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal, cast

from packages.steel_theory.core import (
    CopedentControl,
    CopedentProfile,
    ControlChange,
    StringTuning,
    snapshot_digest,
)


DiagnosticSeverity = Literal["warning", "error"]
ProjectionSource = Literal["rag", "howdy"]


@dataclass(frozen=True)
class ProjectionDiagnostic:
    severity: DiagnosticSeverity
    code: str
    path: str
    summary: str


@dataclass(frozen=True)
class ApprovedProfileMatch:
    """An explicit, bounded approval to expand a compact product profile."""

    approval_id: str
    source_profile_id: str
    canonical_profile: CopedentProfile

    def __post_init__(self) -> None:
        if not self.approval_id:
            raise ValueError("Approved profile match requires an approval id")
        if not self.source_profile_id:
            raise ValueError("Approved profile match requires a source profile id")


@dataclass(frozen=True)
class CopedentProjection:
    source: ProjectionSource
    source_profile_id: str
    profile: CopedentProfile | None
    diagnostics: tuple[ProjectionDiagnostic, ...]
    approval_id: str | None = None

    @property
    def errors(self) -> tuple[ProjectionDiagnostic, ...]:
        return tuple(item for item in self.diagnostics if item.severity == "error")

    @property
    def warnings(self) -> tuple[ProjectionDiagnostic, ...]:
        return tuple(item for item in self.diagnostics if item.severity == "warning")

    @property
    def digest(self) -> str | None:
        return snapshot_digest(self.profile) if self.profile is not None else None


class _ProjectionInputError(ValueError):
    def __init__(self, code: str, path: str, summary: str) -> None:
        super().__init__(summary)
        self.code = code
        self.path = path
        self.summary = summary


def _mapping(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise _ProjectionInputError("invalid_shape", path, "Expected an object")
    return cast(Mapping[str, object], value)


def _sequence(value: object, path: str) -> Sequence[object]:
    if not isinstance(value, (list, tuple)):
        raise _ProjectionInputError("invalid_shape", path, "Expected an array")
    return cast(Sequence[object], value)


def _string(value: object, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise _ProjectionInputError("invalid_value", path, "Expected a non-empty string")
    return value


def _integer(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise _ProjectionInputError("invalid_value", path, "Expected an integer")
    return value


def _error_projection(
    *,
    source: ProjectionSource,
    source_profile_id: str,
    issue: _ProjectionInputError,
    approval_id: str | None = None,
) -> CopedentProjection:
    return CopedentProjection(
        source=source,
        source_profile_id=source_profile_id,
        profile=None,
        diagnostics=(ProjectionDiagnostic("error", issue.code, issue.path, issue.summary),),
        approval_id=approval_id,
    )


def project_rag_copedent(
    source: Mapping[str, object],
    *,
    control_ids: Sequence[str] = ("A", "B"),
) -> CopedentProjection:
    """Project the reviewed M1a portion of a RAG copedent payload."""

    source_profile_id = str(source.get("id") or "")
    diagnostics: list[ProjectionDiagnostic] = []
    try:
        source_profile_id = _string(source.get("id"), "$.id")
        revision = _integer(source.get("revision"), "$.revision")
        tuning = _string(source.get("instrument"), "$.instrument")

        strings = tuple(
            StringTuning(
                string=_integer(item.get("string"), f"$.strings[{index}].string"),
                open_midi=_integer(item.get("open_pitch_value"), f"$.strings[{index}].open_pitch_value"),
                open_label=_string(
                    item.get("open_scientific_pitch"),
                    f"$.strings[{index}].open_scientific_pitch",
                ),
            )
            for index, item in (
                (index, _mapping(value, f"$.strings[{index}]"))
                for index, value in enumerate(_sequence(source.get("strings"), "$.strings"))
            )
        )

        source_controls = tuple(
            _mapping(value, f"$.controls[{index}]")
            for index, value in enumerate(_sequence(source.get("controls"), "$.controls"))
        )
        controls_by_id = {
            _string(item.get("id"), f"$.controls[{index}].id"): (index, item)
            for index, item in enumerate(source_controls)
        }
        if len(controls_by_id) != len(source_controls):
            raise _ProjectionInputError(
                "duplicate_control",
                "$.controls",
                "RAG control ids must be unique",
            )
        missing = tuple(control_id for control_id in control_ids if control_id not in controls_by_id)
        if missing:
            raise _ProjectionInputError(
                "missing_control",
                "$.controls",
                f"Required M1a controls are missing: {', '.join(missing)}",
            )

        controls: list[CopedentControl] = []
        for control_id in control_ids:
            control_index, source_control = controls_by_id[control_id]
            changes = tuple(
                ControlChange(
                    string=_integer(
                        change.get("string"),
                        f"$.controls[{control_index}].changes[{change_index}].string",
                    ),
                    semitones=_integer(
                        change.get("semitones"),
                        f"$.controls[{control_index}].changes[{change_index}].semitones",
                    ),
                )
                for change_index, change in (
                    (change_index, _mapping(value, f"$.controls[{control_index}].changes[{change_index}]"))
                    for change_index, value in enumerate(
                        _sequence(source_control.get("changes"), f"$.controls[{control_index}].changes")
                    )
                )
            )
            controls.append(CopedentControl(control_id, changes))

        extra_controls = tuple(control_id for control_id in controls_by_id if control_id not in control_ids)
        if extra_controls:
            diagnostics.append(
                ProjectionDiagnostic(
                    "warning",
                    "controls_outside_m1a",
                    "$.controls",
                    "Controls outside the approved A/B core remain in the RAG product profile",
                )
            )

        profile = CopedentProfile(
            id=source_profile_id,
            revision=revision,
            tuning=tuning,
            strings=strings,
            controls=tuple(controls),
        )
    except _ProjectionInputError as exc:
        return _error_projection(source="rag", source_profile_id=source_profile_id, issue=exc)
    except ValueError as exc:
        return _error_projection(
            source="rag",
            source_profile_id=source_profile_id,
            issue=_ProjectionInputError("invalid_copedent", "$", str(exc)),
        )

    return CopedentProjection(
        source="rag",
        source_profile_id=source_profile_id,
        profile=profile,
        diagnostics=tuple(diagnostics),
    )


def project_howdy_copedent(
    source: Mapping[str, object],
    *,
    approved_match: ApprovedProfileMatch | None,
) -> CopedentProjection:
    """Expand a compact Howdy copedent only through an explicit profile match."""

    source_profile_id = str(source.get("id") or "")
    if approved_match is None:
        return _error_projection(
            source="howdy",
            source_profile_id=source_profile_id,
            issue=_ProjectionInputError(
                "missing_approved_profile_match",
                "$",
                "Howdy copedent expansion requires an explicitly approved canonical profile match",
            ),
        )

    diagnostics: list[ProjectionDiagnostic] = []
    try:
        source_profile_id = _string(source.get("id"), "$.id")
        if source_profile_id != approved_match.source_profile_id:
            raise _ProjectionInputError(
                "profile_match_id_mismatch",
                "$.id",
                "Howdy source profile does not match the approved source profile id",
            )

        source_strings = tuple(
            (
                _integer(item.get("string"), f"$.stringsHighToLow[{index}].string"),
                _string(item.get("openPitch"), f"$.stringsHighToLow[{index}].openPitch"),
            )
            for index, item in (
                (index, _mapping(value, f"$.stringsHighToLow[{index}]"))
                for index, value in enumerate(_sequence(source.get("stringsHighToLow"), "$.stringsHighToLow"))
            )
        )
        canonical_strings = tuple((item.string, item.open_label) for item in approved_match.canonical_profile.strings)
        if source_strings != canonical_strings:
            raise _ProjectionInputError(
                "open_string_mismatch",
                "$.stringsHighToLow",
                "Howdy open strings do not match the approved canonical profile",
            )

        source_controls = tuple(
            _mapping(value, f"$.controls[{index}]")
            for index, value in enumerate(_sequence(source.get("controls"), "$.controls"))
        )
        source_control_strings: dict[str, tuple[int, ...]] = {}
        source_control_changes: dict[str, tuple[tuple[int, int], ...]] = {}
        control_ids: list[str] = []
        for index, item in enumerate(source_controls):
            control_id = _string(item.get("code"), f"$.controls[{index}].code")
            control_ids.append(control_id)
            source_control_strings[control_id] = tuple(
                _integer(value, f"$.controls[{index}].strings[{string_index}]")
                for string_index, value in enumerate(_sequence(item.get("strings"), f"$.controls[{index}].strings"))
            )
            if "changes" in item:
                source_control_changes[control_id] = tuple(
                    (
                        _integer(
                            change.get("string"),
                            f"$.controls[{index}].changes[{change_index}].string",
                        ),
                        _integer(
                            change.get("semitones"),
                            f"$.controls[{index}].changes[{change_index}].semitones",
                        ),
                    )
                    for change_index, change in (
                        (
                            change_index,
                            _mapping(value, f"$.controls[{index}].changes[{change_index}]"),
                        )
                        for change_index, value in enumerate(
                            _sequence(item.get("changes"), f"$.controls[{index}].changes")
                        )
                    )
                )

        if len(set(control_ids)) != len(control_ids):
            raise _ProjectionInputError(
                "duplicate_control",
                "$.controls",
                "Howdy control codes must be unique",
            )

        canonical_control_strings = {
            control.id: tuple(change.string for change in control.changes)
            for control in approved_match.canonical_profile.controls
        }
        if source_control_strings != canonical_control_strings:
            raise _ProjectionInputError(
                "control_string_mismatch",
                "$.controls",
                "Howdy control membership does not match the approved canonical profile",
            )

        canonical_control_changes = {
            control.id: tuple((change.string, change.semitones) for change in control.changes)
            for control in approved_match.canonical_profile.controls
        }
        for control_id, changes in source_control_changes.items():
            if changes != canonical_control_changes[control_id]:
                raise _ProjectionInputError(
                    "control_delta_mismatch",
                    "$.controls",
                    "Howdy control deltas do not match the approved canonical profile",
                )

        if source.get("revision") is None:
            diagnostics.append(
                ProjectionDiagnostic(
                    "warning",
                    "revision_supplied_by_approved_match",
                    "$.revision",
                    "The compact Howdy source omits revision; the approved match supplies it",
                )
            )
        elif _integer(source.get("revision"), "$.revision") != approved_match.canonical_profile.revision:
            raise _ProjectionInputError(
                "revision_mismatch",
                "$.revision",
                "Howdy revision does not match the approved canonical profile",
            )

        if set(source_control_changes) != set(source_control_strings):
            diagnostics.append(
                ProjectionDiagnostic(
                    "warning",
                    "control_deltas_supplied_by_approved_match",
                    "$.controls",
                    "The compact Howdy source omits semitone deltas; the approved match supplies them",
                )
            )
    except _ProjectionInputError as exc:
        return _error_projection(
            source="howdy",
            source_profile_id=source_profile_id,
            issue=exc,
            approval_id=approved_match.approval_id,
        )

    return CopedentProjection(
        source="howdy",
        source_profile_id=source_profile_id,
        profile=approved_match.canonical_profile,
        diagnostics=tuple(diagnostics),
        approval_id=approved_match.approval_id,
    )
