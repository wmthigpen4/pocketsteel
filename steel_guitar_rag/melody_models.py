"""Stable request and path value objects for the Melody Studio arranger."""

from __future__ import annotations

from dataclasses import dataclass

from steel_guitar_rag.fretboard_examples import absolute_pitch_for_string
from steel_guitar_rag.tab_engine import TabNote


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
    source_action: dict[str, object] | None = None


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
    voice_pitches: tuple[int, ...] = ()

    @property
    def top_string(self) -> int:
        if self.voice_pitches and len(self.voice_pitches) == len(self.notes):
            return self.notes[max(range(len(self.notes)), key=lambda index: self.voice_pitches[index])].string
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
