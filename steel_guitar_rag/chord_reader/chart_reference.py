"""Convert a reviewed chord chart onto an analyzer timing grid without relabeling it."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .labels import normalize_chord
from .manifests import WeakLabelDiagnostics, admit_weak_label
from .metrics import score_segments


def _timing_boundaries(timing: Mapping[str, Any]) -> list[float]:
    duration = float(timing["durationSeconds"])
    starts = sorted({float(value) for value in timing.get("barStartsSeconds", []) if 0 <= float(value) < duration})
    if not starts:
        raise ValueError("Timing prediction needs at least one bar start.")
    return starts + [duration]


def _append_segment(segments: list[dict[str, Any]], start: float, end: float, label: str) -> None:
    if end <= start:
        return
    normalized = normalize_chord(label).detailed_symbol
    if segments and segments[-1]["label"] == normalized and abs(float(segments[-1]["end"]) - start) < 1e-6:
        segments[-1]["end"] = end
    else:
        segments.append({"start": start, "end": end, "label": normalized})


def _reader_agreement(reference: Sequence[Mapping[str, Any]], readers: Sequence[Mapping[str, Any]]) -> float:
    if len(readers) < 2:
        return 0.0
    values = [score_segments(reference, reader.get("segments", []))["majorMinorWeightedRecall"] for reader in readers]
    return float(min(values))


def build_chart_reference(
    chart: Mapping[str, Any],
    timing: Mapping[str, Any],
    *,
    independent_readers: Sequence[Mapping[str, Any]] = (),
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Map reviewed chart cells to explicit timing-grid spans.

    The chart, not a chord recognizer, owns every output label. A cell may span
    multiple analyzer bars, but that choice must be written explicitly in the
    reviewed chart spec so a challenger cannot influence its own ground truth.
    """

    cells = chart.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError("Chart spec needs a non-empty cells list.")
    boundaries = _timing_boundaries(timing)
    start_index = int(chart.get("startBarIndex", 0))
    if start_index < 0 or start_index >= len(boundaries) - 1:
        raise ValueError("startBarIndex is outside the timing grid.")

    segments: list[dict[str, Any]] = []
    if bool(chart.get("includePrefixNoChord")) and boundaries[start_index] > 0:
        _append_segment(segments, 0.0, boundaries[start_index], "N")

    cursor = start_index
    cell_map: list[dict[str, Any]] = []
    for position, cell in enumerate(cells, start=1):
        span = int(cell.get("gridSpans", 1))
        if span < 1 or cursor + span >= len(boundaries):
            raise ValueError(f"Chart cell {position} exceeds the timing grid.")
        chords = cell.get("chords")
        if not isinstance(chords, list) or not chords:
            raise ValueError(f"Chart cell {position} needs one or more chords.")
        weights = cell.get("weights") or [1.0] * len(chords)
        if len(weights) != len(chords) or any(float(value) <= 0 for value in weights):
            raise ValueError(f"Chart cell {position} has invalid chord weights.")
        start = boundaries[cursor]
        end = boundaries[cursor + span]
        total = sum(float(value) for value in weights)
        chord_start = start
        for chord_index, (chord, weight) in enumerate(zip(chords, weights, strict=True)):
            chord_end = end if chord_index + 1 == len(chords) else chord_start + (end - start) * float(weight) / total
            _append_segment(segments, chord_start, chord_end, str(chord))
            chord_start = chord_end
        cell_map.append(
            {
                "cell": cell.get("cell", position),
                "startBarIndex": cursor,
                "gridSpans": span,
                "start": start,
                "end": end,
            }
        )
        cursor += span

    duration = float(timing["durationSeconds"])
    if bool(chart.get("includeSuffixNoChord")) and segments[-1]["end"] < duration:
        _append_segment(segments, float(segments[-1]["end"]), duration, "N")

    beats = sorted(float(value) for value in timing.get("beatTimesSeconds", []))
    internal_boundaries = [float(item["end"]) for item in segments[:-1]]
    beat_durations = [right - left for left, right in zip(beats, beats[1:], strict=False) if right > left]
    half_beat = (sum(beat_durations) / len(beat_durations) / 2) if beat_durations else 0.25
    aligned = sum(bool(beats) and min(abs(boundary - beat) for beat in beats) <= half_beat for boundary in internal_boundaries)
    boundary_fraction = aligned / max(1, len(internal_boundaries))
    coverage_tolerance = max(0.05, half_beat)
    complete = bool(segments) and segments[0]["start"] <= coverage_tolerance and segments[-1]["end"] >= duration - coverage_tolerance
    diagnostics = WeakLabelDiagnostics(
        complete_coverage=complete,
        monotonic_alignment=all(
            float(left["start"]) <= float(left["end"]) <= float(right["start"]) <= float(right["end"])
            for left, right in zip(segments, segments[1:], strict=False)
        ),
        boundary_within_half_beat_fraction=boundary_fraction,
        dual_reader_duration_agreement=_reader_agreement(segments, independent_readers),
    )
    reference = {
        "schemaVersion": "chord_reference_v1",
        "id": chart.get("id") or timing.get("id"),
        "sourceType": "reviewed_chart_timing_alignment",
        "durationSeconds": duration,
        "segments": segments,
        "alignment": {"timingEngine": timing.get("engine"), "cells": cell_map},
    }
    report = {
        "schemaVersion": "chord_chart_alignment_report_v1",
        "referenceId": reference["id"],
        "admission": admit_weak_label(diagnostics),
        "evaluatedReaders": [reader.get("engine") for reader in independent_readers],
    }
    return reference, report
