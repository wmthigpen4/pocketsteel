"""Stable request and path value objects for the Melody Studio arranger."""

from __future__ import annotations

from dataclasses import dataclass

from pocketsteel.fretboard_examples import absolute_pitch_for_string
from pocketsteel.tab_engine import TabNote


SUPPORTED_CONTOURS = {"closest_playable", "ascending", "descending", "preserve_input"}
SUPPORTED_TEXTURES = {
    "both",
    "single_note",
    "mixed_arrangement",
    "automatic_harmony",
    "thirds",
    "sixths",
    "chord_melody",
}
DEFAULT_ANCHOR_PITCH = 67  # G4: a useful middle/upper E9 melody register.


@dataclass(frozen=True)
class MelodyInput:
    token: str
    note: str
    degree: int
    pitch_class: int
    direction: str = "auto"
    octave_shift: int = 0
    literal: TabNote | None = None
    forced_pitch: int | None = None
    duration_beats: float = 1.0
    measure: int = 1
    beat: float = 1.0
    origin: str = "user_edit"
    tie: str = ""
    lyric: str = ""
    chord: str = ""
    articulation: str = ""


@dataclass(frozen=True)
class PositionCandidate:
    fret: int
    notes: tuple[TabNote, ...]
    top_pitch: int
    controls: tuple[str, ...]
    family: str
    note_names: tuple[str, ...]
    intervals: tuple[str, ...]
    pattern_family: str = ""
    canonical_grip: tuple[int, ...] = ()
    difficulty: str = "common"

    @property
    def top_string(self) -> int:
        aliases = {
            "E": "E-lower",
            "F": "F lever",
            "V": "vertical/Bb",
            "G": "RKL",
            "D": "RKRR",
        }
        controls = tuple(aliases.get(control, control) for control in self.controls)
        return max(
            (note.string for note in self.notes),
            key=lambda string: absolute_pitch_for_string(string, self.fret, controls),
        )
