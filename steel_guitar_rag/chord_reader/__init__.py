"""Training, evaluation, and runtime contracts for Chord Reader ML."""

from .labels import ChordLabel, normalize_chord, transpose_chord
from .manifests import (
    WeakLabelDiagnostics,
    admit_weak_label,
    assign_group_splits,
    validate_catalog,
    validate_track_manifest,
)
from .metrics import score_segments

__all__ = [
    "ChordLabel",
    "WeakLabelDiagnostics",
    "admit_weak_label",
    "assign_group_splits",
    "normalize_chord",
    "score_segments",
    "transpose_chord",
    "validate_catalog",
    "validate_track_manifest",
]
