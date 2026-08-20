from __future__ import annotations

import numpy as np
import pytest

from steel_guitar_rag.chord_reader.routing import FactorizedEvidence
from steel_guitar_rag.chord_reader.segmental import (
    BEAT_GRID_SCHEMA,
    BeatGrid,
    beat_alignment_evidence,
    boundary_candidate_frames,
    candidate_boundary_diagnostics,
    decode_factorized_segments,
    usable_beat_grid,
    validate_beat_grid,
    with_optional_beat_grid,
)


def _grid(
    *,
    confidence: float = 0.9,
    times: tuple[float, ...] = (0.5, 1.0, 1.5),
) -> dict:
    return {
        "schemaVersion": BEAT_GRID_SCHEMA,
        "confidence": confidence,
        "source": "fixture-beat-tracker",
        "beats": [
            {
                "timeSeconds": time,
                "confidence": 0.8,
                "downbeat": index == 1,
                "downbeatConfidence": 0.9 if index == 1 else 0.0,
            }
            for index, time in enumerate(times)
        ],
    }


def _evidence(change_frame: int = 10, *, frames: int = 20) -> FactorizedEvidence:
    root = np.full((frames, 3), 0.02, dtype=np.float64)
    root[:change_frame, 1] = 0.96
    root[change_frame:, 2] = 0.96
    mode = np.full((frames, 3), 0.02, dtype=np.float64)
    mode[:, 1] = 0.96
    quality = np.full((frames, 4), 0.02, dtype=np.float64)
    quality[:change_frame, 0] = 0.94
    quality[change_frame:, 2] = 0.94
    quality /= quality.sum(axis=1, keepdims=True)
    bass = np.full((frames, 3), 0.05, dtype=np.float64)
    bass[:change_frame, 1] = 0.9  # Same as root: should not emit an inversion.
    bass[change_frame:, 1] = 0.85  # Different from root 2: real inversion evidence.
    bass[change_frame:, 0] = 0.1
    bass /= bass.sum(axis=1, keepdims=True)
    boundary = np.full(frames, 0.05, dtype=np.float64)
    boundary[change_frame] = 0.95
    return FactorizedEvidence(
        root=root,
        mode=mode,
        quality=quality,
        bass=bass,
        boundary=boundary,
    )


def test_beat_grid_schema_validation_requires_ordered_bounded_confidence() -> None:
    grid = validate_beat_grid(_grid(), duration_seconds=2.0)
    assert isinstance(grid, BeatGrid)
    assert grid.usable is True
    assert grid.beats[1].downbeat is True
    assert grid.mean_downbeat_confidence == pytest.approx(0.9)

    unordered = _grid()
    unordered["beats"][1]["timeSeconds"] = 0.25
    with pytest.raises(ValueError, match="strictly increasing"):
        validate_beat_grid(unordered, duration_seconds=2.0)

    outside = _grid()
    outside["beats"][-1]["timeSeconds"] = 3.0
    with pytest.raises(ValueError, match="outside"):
        validate_beat_grid(outside, duration_seconds=2.0)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        {"schemaVersion": "wrong"},
        _grid(confidence=0.0),
    ],
)
def test_missing_invalid_and_zero_confidence_rhythm_is_bit_exact_fallback(grid: object) -> None:
    frozen = {
        "schemaVersion": "chord_prediction_v1",
        "segments": [{"start": 0.0, "end": 2.0, "label": "C:maj", "confidence": 0.123456789}],
    }
    beat_decoder_called = False

    def beat_decoder(_grid: BeatGrid) -> dict:
        nonlocal beat_decoder_called
        beat_decoder_called = True
        return {"wrong": True}

    result = with_optional_beat_grid(
        grid,
        duration_seconds=2.0,
        fallback_decoder=lambda: frozen,
        beat_decoder=beat_decoder,
    )
    assert result is frozen
    assert beat_decoder_called is False

    decoded = decode_factorized_segments(
        _evidence(),
        duration_seconds=2.0,
        frame_seconds=0.1,
        beat_grid=grid,
        fallback_decoder=lambda: frozen,
        mode_indices=(1, 2),
        quality_mode_indices=(1, 2, 1, 2),
    )
    assert decoded is frozen


def test_candidate_union_keeps_strong_acoustic_offbeats() -> None:
    grid = validate_beat_grid(_grid(times=(0.5, 1.0, 1.5)), duration_seconds=2.0)
    boundary = np.full(20, 0.05)
    boundary[7] = 0.92
    candidates = boundary_candidate_frames(
        boundary,
        frame_seconds=0.1,
        beat_grid=grid,
        acoustic_threshold=0.45,
    )

    assert candidates.frames == (0, 5, 7, 10, 15, 20)
    assert candidates.sources[7] == ("acoustic",)
    assert candidates.sources[10] == ("downbeat",)


def test_beat_and_downbeat_evidence_is_gaussian_not_a_hard_gate() -> None:
    grid = validate_beat_grid(_grid(times=(1.0, 1.5)), duration_seconds=2.0)
    exact = beat_alignment_evidence(1.5, grid, sigma_seconds=0.08)
    near = beat_alignment_evidence(1.55, grid, sigma_seconds=0.08)
    far = beat_alignment_evidence(1.75, grid, sigma_seconds=0.08)

    assert exact > near > far >= 0
    assert beat_alignment_evidence(1.501, grid, sigma_seconds=0.08) < exact


def test_semi_markov_decoder_uses_prefix_evidence_and_picks_quality_and_bass_per_span() -> None:
    decoded = decode_factorized_segments(
        _evidence(change_frame=10),
        duration_seconds=2.0,
        frame_seconds=0.1,
        beat_grid=_grid(times=(0.5, 1.0, 1.5)),
        fallback_decoder=lambda: pytest.fail("valid rhythm must not fall back"),
        mode_indices=(1, 2),
        quality_mode_indices=(1, 2, 1, 2),
        reference_boundaries_seconds=(1.0,),
    )

    assert decoded["decoder"] == "beat-aware-semi-markov-root-mode-v1"
    assert decoded["diagnostics"]["prefixLogEvidence"] is True
    assert decoded["diagnostics"]["semiMarkov"] is True
    assert [(span["root"], span["mode"]) for span in decoded["spans"]] == [(1, 1), (2, 1)]
    assert [span["quality"] for span in decoded["spans"]] == [0, 2]
    assert [span["bass"] for span in decoded["spans"]] == [0, 1]
    assert decoded["spans"][0]["endFrame"] == 10
    assert decoded["diagnostics"]["candidateRecall"] == 1


def test_semi_markov_decoder_can_select_a_syncopated_offbeat_boundary() -> None:
    evidence = _evidence(change_frame=7)
    decoded = decode_factorized_segments(
        evidence,
        duration_seconds=2.0,
        frame_seconds=0.1,
        beat_grid=_grid(times=(0.5, 1.0, 1.5)),
        fallback_decoder=lambda: pytest.fail("valid rhythm must not fall back"),
        mode_indices=(1, 2),
        quality_mode_indices=(1, 2, 1, 2),
        reference_boundaries_seconds=(0.7,),
    )

    assert decoded["spans"][0]["endFrame"] == 7
    assert decoded["diagnostics"]["acousticOffbeatCandidateCount"] == 1
    assert "acoustic" in decoded["diagnostics"]["candidateSources"]["7"]


def test_candidate_recall_and_selected_offset_diagnostics_are_explicit() -> None:
    diagnostics = candidate_boundary_diagnostics(
        (0, 5, 11, 18, 20),
        (0.52, 1.0, 1.8),
        frame_seconds=0.1,
        selected_frames=(5, 11),
        tolerance_seconds=0.15,
    )

    assert diagnostics["referenceBoundaryCount"] == 3
    assert diagnostics["candidateRecall"] == 1
    assert diagnostics["selectedRecall"] == pytest.approx(2 / 3)
    assert diagnostics["meanNearestCandidateOffsetSeconds"] == pytest.approx(
        (0.02 + 0.1 + 0.0) / 3
    )


def test_malformed_rhythm_fails_closed_in_safe_parser() -> None:
    malformed = _grid()
    malformed["beats"][0]["confidence"] = float("nan")
    assert usable_beat_grid(malformed, duration_seconds=2.0) is None
