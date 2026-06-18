"""Deterministic E9 tab validation and fixed-width rendering.

This module is intentionally small and rules-based. It validates structured
tab events before rendering so the app does not emit mechanically impossible
pedal/lever markings as if they were valid pedal-steel tab.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


E9_OPEN_STRINGS: dict[int, str] = {
    1: "F#",
    2: "D#",
    3: "G#",
    4: "E",
    5: "B",
    6: "G#",
    7: "F#",
    8: "E",
    9: "D",
    10: "B",
}


@dataclass(frozen=True)
class PedalLeverEffect:
    code: str
    user_label: str
    affected_strings: tuple[int, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "userLabel": self.user_label,
            "affectedStrings": list(self.affected_strings),
        }


@dataclass(frozen=True)
class CopedentProfile:
    id: str
    label: str
    open_strings: dict[int, str]
    changes: dict[str, PedalLeverEffect]
    control_labels: dict[str, str]

    def normalize_change(self, change: str) -> str:
        normalized = str(change or "").strip()
        if not normalized:
            return ""
        lowered = normalized.lower().replace("_", "-")
        aliases = {
            "p1": "A",
            "a-pedal": "A",
            "a pedal": "A",
            "p2": "B",
            "b-pedal": "B",
            "b pedal": "B",
            "p3": "C",
            "c-pedal": "C",
            "c pedal": "C",
            "lkl": "F",
            "f lever": "F",
            "e-raise": "F",
            "lkr": "E",
            "e-lower": "E",
            "e lower": "E",
            "lkv": "V",
            "vertical": "V",
            "vertical/bb": "V",
            "bb": "V",
            "rkl": "G",
            "g lever": "G",
            "6-lower": "G",
            "rkr": "D",
            "d lever": "D",
            "2/9-lower": "D",
        }
        return aliases.get(lowered, normalized.upper())


def default_e9_copedent_profile() -> CopedentProfile:
    return CopedentProfile(
        id="default_e9",
        label="Default 10-string E9",
        open_strings=dict(E9_OPEN_STRINGS),
        changes={
            "A": PedalLeverEffect("A", "A pedal", (5, 10)),
            "B": PedalLeverEffect("B", "B pedal", (3, 6)),
            "C": PedalLeverEffect("C", "C pedal", (4, 5)),
            "E": PedalLeverEffect("E", "E-lower lever", (4, 8)),
            "F": PedalLeverEffect("F", "F lever", (4, 8)),
            "V": PedalLeverEffect("V", "vertical/Bb lever", (5, 10)),
            "G": PedalLeverEffect("G", "6-lower/RKL lever", (1, 6)),
            "D": PedalLeverEffect("D", "2/9-lower/RKR lever", (2, 9)),
        },
        control_labels={
            "P1": "A",
            "P2": "B",
            "P3": "C",
            "LKL": "F",
            "LKR": "E",
            "LKV": "V",
            "RKL": "G",
            "RKR": "D",
        },
    )


@dataclass(frozen=True)
class TabNote:
    string: int
    fret: int
    changes: tuple[str, ...] = ()
    articulation: str | None = None

    def normalized(self, profile: CopedentProfile) -> "TabNote":
        changes = tuple(
            sorted(
                {
                    normalized
                    for change in self.changes
                    if (normalized := profile.normalize_change(change))
                }
            )
        )
        return TabNote(
            string=int(self.string),
            fret=int(self.fret),
            changes=changes,
            articulation=self.articulation,
        )

    def render_token(self) -> str:
        return f"{self.fret}{''.join(self.changes)}"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "string": self.string,
            "fret": self.fret,
            "changes": list(self.changes),
        }
        if self.articulation:
            payload["articulation"] = self.articulation
        return payload


@dataclass(frozen=True)
class TabEvent:
    notes: tuple[TabNote, ...]
    chord: str | None = None
    lyric: str | None = None
    comment: str | None = None

    def normalized(self, profile: CopedentProfile) -> "TabEvent":
        return TabEvent(
            notes=tuple(note.normalized(profile) for note in self.notes),
            chord=self.chord,
            lyric=self.lyric,
            comment=self.comment,
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"notes": [note.to_dict() for note in self.notes]}
        if self.chord:
            payload["chord"] = self.chord
        if self.lyric:
            payload["lyric"] = self.lyric
        if self.comment:
            payload["comment"] = self.comment
        return payload


@dataclass(frozen=True)
class TabValidationIssue:
    code: str
    message: str
    event_index: int | None = None
    note_index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.event_index is not None:
            payload["eventIndex"] = self.event_index
        if self.note_index is not None:
            payload["noteIndex"] = self.note_index
        return payload


@dataclass(frozen=True)
class TabRenderResult:
    ok: bool
    tab: str
    issues: tuple[TabValidationIssue, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "tab": self.tab,
            "issues": [issue.to_dict() for issue in self.issues],
            "metadata": dict(self.metadata),
        }


def tab_note_from_dict(payload: dict[str, Any]) -> TabNote:
    raw_changes = payload.get("changes") or ()
    if isinstance(raw_changes, str):
        raw_changes = (raw_changes,)
    return TabNote(
        string=_coerce_int(payload.get("string"), default=0),
        fret=_coerce_int(payload.get("fret"), default=-1),
        changes=tuple(raw_changes),
        articulation=payload.get("articulation"),
    )


def tab_event_from_dict(payload: dict[str, Any]) -> TabEvent:
    notes = payload.get("notes")
    if not isinstance(notes, list):
        notes = []
    return TabEvent(
        notes=tuple(tab_note_from_dict(note) for note in notes if isinstance(note, dict)),
        chord=_optional_text(payload.get("chord")),
        lyric=_optional_text(payload.get("lyric")),
        comment=_optional_text(payload.get("comment")),
    )


def events_from_payload(payload: dict[str, Any]) -> tuple[TabEvent, ...]:
    events = payload.get("events")
    if not isinstance(events, list):
        return ()
    return tuple(tab_event_from_dict(event) for event in events if isinstance(event, dict))


def render_tab_from_payload(payload: dict[str, Any]) -> TabRenderResult:
    profile = default_e9_copedent_profile()
    profile_id = str(payload.get("profile") or profile.id)
    if profile_id != profile.id:
        return TabRenderResult(
            ok=False,
            tab="",
            issues=(
                TabValidationIssue(
                    code="unsupported_profile",
                    message=f"Unsupported tab profile: {profile_id}",
                ),
            ),
            metadata={"profile": profile.id, "event_count": 0},
        )
    return render_tab(events_from_payload(payload), profile=profile)


def validate_events(
    events: tuple[TabEvent, ...] | list[TabEvent],
    *,
    profile: CopedentProfile | None = None,
) -> tuple[TabValidationIssue, ...]:
    profile = profile or default_e9_copedent_profile()
    issues: list[TabValidationIssue] = []
    for event_index, raw_event in enumerate(events):
        event = raw_event.normalized(profile)
        if not event.notes:
            issues.append(
                TabValidationIssue(
                    code="empty_event",
                    message="Each tab event must include at least one note.",
                    event_index=event_index,
                )
            )
            continue
        if len(event.notes) > 3:
            issues.append(
                TabValidationIssue(
                    code="too_many_notes",
                    message="MVP tab events support one to three notes.",
                    event_index=event_index,
                )
            )
        frets = {note.fret for note in event.notes}
        if len(frets) > 1:
            issues.append(
                TabValidationIssue(
                    code="mixed_frets",
                    message="Multi-note events must stay on one fret until slant support is added.",
                    event_index=event_index,
                )
            )
        strings_seen: set[int] = set()
        for note_index, note in enumerate(event.notes):
            if note.string < 1 or note.string > 10:
                issues.append(
                    TabValidationIssue(
                        code="invalid_string",
                        message=f"String {note.string} is outside the 1-10 E9 range.",
                        event_index=event_index,
                        note_index=note_index,
                    )
                )
            if note.string in strings_seen:
                issues.append(
                    TabValidationIssue(
                        code="duplicate_string",
                        message=f"String {note.string} appears more than once in the same event.",
                        event_index=event_index,
                        note_index=note_index,
                    )
                )
            strings_seen.add(note.string)
            if note.fret < 0 or note.fret > 24:
                issues.append(
                    TabValidationIssue(
                        code="invalid_fret",
                        message=f"Fret {note.fret} is outside the supported 0-24 range.",
                        event_index=event_index,
                        note_index=note_index,
                    )
                )
            for change in note.changes:
                effect = profile.changes.get(change)
                if effect is None:
                    issues.append(
                        TabValidationIssue(
                            code="unknown_change",
                            message=f"Change {change} is not recognized for {profile.label}.",
                            event_index=event_index,
                            note_index=note_index,
                        )
                    )
                    continue
                if note.string not in effect.affected_strings:
                    issues.append(
                        TabValidationIssue(
                            code="unaffected_string_change",
                            message=f"Change {change} does not affect string {note.string}.",
                            event_index=event_index,
                            note_index=note_index,
                        )
                    )
    return tuple(issues)


def render_tab(
    events: tuple[TabEvent, ...] | list[TabEvent],
    *,
    profile: CopedentProfile | None = None,
) -> TabRenderResult:
    profile = profile or default_e9_copedent_profile()
    normalized_events = tuple(event.normalized(profile) for event in events)
    issues = validate_events(normalized_events, profile=profile)
    metadata = {"profile": profile.id, "event_count": len(normalized_events)}
    if issues:
        return TabRenderResult(ok=False, tab="", issues=issues, metadata=metadata)

    event_widths = [_event_width(event) for event in normalized_events]
    has_chords = any(event.chord for event in normalized_events)
    has_lyrics = any(event.lyric for event in normalized_events)
    lines: list[str] = []

    if has_chords:
        lines.append(_render_label_row("Ch |", [_optional_text(event.chord) for event in normalized_events], event_widths))
    if has_lyrics:
        lines.append(_render_label_row("Ly |", [_optional_text(event.lyric) for event in normalized_events], event_widths))

    for string_number in range(1, 11):
        tokens: list[str] = []
        for event in normalized_events:
            tokens.append(_note_token_for_string(event, string_number))
        lines.append(_render_label_row(f"{string_number:>2} |", tokens, event_widths))

    return TabRenderResult(ok=True, tab="\n".join(lines), issues=(), metadata=metadata)


def tab_examples() -> dict[str, tuple[TabEvent, ...]]:
    return {
        "g_major_open": (
            TabEvent(
                chord="G",
                notes=(
                    TabNote(4, 3),
                    TabNote(5, 3),
                    TabNote(6, 3),
                ),
            ),
        ),
        "g_to_c": (
            TabEvent(
                chord="G",
                notes=(TabNote(4, 3), TabNote(5, 3), TabNote(6, 3)),
            ),
            TabEvent(
                chord="C partial",
                notes=(TabNote(5, 3, ("A",)), TabNote(6, 3, ("B",))),
            ),
        ),
        "ab_major": (
            TabEvent(
                chord="A+B",
                notes=(TabNote(3, 10, ("B",)), TabNote(4, 10), TabNote(5, 10, ("A",))),
            ),
        ),
        "e_lower_color": (
            TabEvent(
                chord="E-lower",
                notes=(TabNote(4, 3, ("E",)), TabNote(5, 3), TabNote(6, 3)),
            ),
        ),
        "beginner_lick": (
            TabEvent(
                chord="G",
                lyric="pick",
                notes=(TabNote(4, 3), TabNote(5, 3), TabNote(6, 3)),
            ),
            TabEvent(
                chord="C partial",
                lyric="press",
                notes=(TabNote(5, 3, ("A",)), TabNote(6, 3, ("B",))),
            ),
            TabEvent(
                chord="G",
                lyric="release",
                notes=(TabNote(4, 3), TabNote(5, 3), TabNote(6, 3)),
            ),
        ),
    }


def render_example(name: str) -> TabRenderResult:
    examples = tab_examples()
    try:
        events = examples[name]
    except KeyError:
        return TabRenderResult(
            ok=False,
            tab="",
            issues=(TabValidationIssue(code="unknown_example", message=f"Unknown tab example: {name}"),),
            metadata={"profile": "default_e9", "event_count": 0},
        )
    return render_tab(events)


def _event_width(event: TabEvent) -> int:
    tokens = [note.render_token() for note in event.notes]
    if event.chord:
        tokens.append(event.chord)
    if event.lyric:
        tokens.append(event.lyric)
    return max(4, *(len(token) for token in tokens)) + 2


def _render_label_row(label: str, tokens: list[str], widths: list[int]) -> str:
    cells = "".join(token.ljust(width) for token, width in zip(tokens, widths))
    return f"{label}{cells}".rstrip()


def _note_token_for_string(event: TabEvent, string_number: int) -> str:
    for note in event.notes:
        if note.string == string_number:
            return note.render_token()
    return ""


def _optional_text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _coerce_int(value: object, *, default: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default
