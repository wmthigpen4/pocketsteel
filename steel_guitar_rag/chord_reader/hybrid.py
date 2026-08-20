"""Beat/bar-stable hybrid decoding from v2 timing and student chord evidence."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .labels import normalize_chord


NO_CHORD = "N.C."


def _overlap(start: float, end: float, segment: Mapping[str, Any]) -> float:
    return max(0.0, min(end, float(segment["end"])) - max(start, float(segment["start"])))


def _dominant(
    segments: Sequence[Mapping[str, Any]], start: float, end: float
) -> tuple[str, float, float]:
    durations: dict[str, float] = {}
    confidence_mass: dict[str, float] = {}
    for segment in segments:
        duration = _overlap(start, end, segment)
        if not duration:
            continue
        label = normalize_chord(str(segment.get("productLabel") or segment.get("label") or "N")).product_symbol
        confidence = float(segment.get("confidence", 0))
        durations[label] = durations.get(label, 0.0) + duration
        confidence_mass[label] = confidence_mass.get(label, 0.0) + duration * confidence
    if not durations:
        return NO_CHORD, 0.0, 0.0
    label = max(durations, key=durations.get)
    coverage = durations[label] / max(1e-12, end - start)
    confidence = confidence_mass[label] / max(1e-12, durations[label])
    return label, coverage, confidence


def _boundaries(v2: Mapping[str, Any]) -> list[float]:
    duration = float(v2["durationSeconds"])
    starts = sorted({float(value) for value in v2.get("barStartsSeconds", []) if 0 <= float(value) < duration})
    if not starts:
        raise ValueError("Hybrid decoding requires v2 bar timing.")
    if starts[0] > 0.05:
        starts.insert(0, 0.0)
    return starts + [duration]


def hybridize_predictions(
    v2: Mapping[str, Any],
    student: Mapping[str, Any],
    *,
    no_chord_confidence: float = 0.75,
    leading_no_chord_min_seconds: float = 3.0,
    student_confidence_ceiling: float = 0.32,
) -> dict[str, Any]:
    """Overlay only strong v2 no-chord regions onto student predictions.

    Student chord boundaries remain intact. This avoids the substantial public
    benchmark regression caused by forcing complex and solo recordings into a
    single chord per detected bar.
    """

    bar_boundaries = _boundaries(v2)
    duration = float(v2["durationSeconds"])
    v2_segments = list(v2.get("segments", []))
    student_segments = list(student.get("segments", []))
    strong_no_chord: list[dict[str, float]] = []
    leading_end = 0.0
    leading_confidence_mass = 0.0
    for segment in sorted(v2_segments, key=lambda item: float(item["start"])):
        label = normalize_chord(str(segment.get("label") or "N")).product_symbol
        start = max(0.0, float(segment["start"]))
        end = min(duration, float(segment["end"]))
        confidence = float(segment.get("confidence", 0))
        if start > leading_end + 0.05 or label != NO_CHORD or confidence < no_chord_confidence:
            break
        leading_confidence_mass += (end - start) * confidence
        leading_end = end
    student_mass = 0.0
    student_duration = 0.0
    for segment in student_segments:
        overlap = _overlap(0.0, leading_end, segment)
        student_mass += overlap * float(segment.get("confidence", 0))
        student_duration += overlap
    student_mean_confidence = student_mass / max(1e-12, student_duration)
    if (
        leading_end >= leading_no_chord_min_seconds
        and student_duration > 0
        and student_mean_confidence <= student_confidence_ceiling
    ):
        strong_no_chord.append(
            {
                "start": 0.0,
                "end": leading_end,
                "confidence": leading_confidence_mass / max(1e-12, leading_end),
            }
        )
    boundaries = {0.0, duration}
    for segment in student_segments:
        boundaries.update((max(0.0, float(segment["start"])), min(duration, float(segment["end"]))))
    for segment in strong_no_chord:
        boundaries.update((segment["start"], segment["end"]))

    segments: list[dict[str, Any]] = []
    ordered = sorted(value for value in boundaries if 0 <= value <= duration)
    for start, end in zip(ordered, ordered[1:], strict=False):
        if end <= start:
            continue
        midpoint = start + (end - start) / 2
        no_chord = next(
            (segment for segment in strong_no_chord if segment["start"] <= midpoint < segment["end"]),
            None,
        )
        if no_chord is not None:
            label, confidence, source = NO_CHORD, no_chord["confidence"], "v2-no-chord"
        else:
            student_label, student_coverage, student_confidence = _dominant(student_segments, start, end)
            if student_coverage:
                label, confidence, source = student_label, student_confidence, "student"
            else:
                base_label, _base_coverage, base_confidence = _dominant(v2_segments, start, end)
                label, confidence, source = base_label, base_confidence, "v2-fallback"
        normalized = normalize_chord(label)
        current = {
            "start": start,
            "end": end,
            "label": normalized.detailed_symbol,
            "productLabel": normalized.product_symbol,
            "confidence": confidence,
            "source": source,
        }
        if segments and segments[-1]["label"] == current["label"] and segments[-1]["source"] == source:
            previous_duration = float(segments[-1]["end"]) - float(segments[-1]["start"])
            current_duration = end - start
            segments[-1]["confidence"] = (
                float(segments[-1]["confidence"]) * previous_duration + confidence * current_duration
            ) / max(1e-12, previous_duration + current_duration)
            segments[-1]["end"] = end
        else:
            segments.append(current)

    bars: list[dict[str, Any]] = []
    for index, (start, end) in enumerate(zip(bar_boundaries, bar_boundaries[1:], strict=False), start=1):
        label, coverage, confidence = _dominant(segments, start, end)
        bars.append(
            {
                "bar": index,
                "start": start,
                "end": end,
                "label": normalize_chord(label).detailed_symbol,
                "productLabel": normalize_chord(label).product_symbol,
                "confidence": confidence,
                "coverage": coverage,
            }
        )
    return {
        "schemaVersion": "chord_prediction_v1",
        "id": student.get("id") or v2.get("id"),
        "engine": "chord-hybrid-v1",
        "durationSeconds": duration,
        "tempo": v2.get("tempo"),
        "meter": v2.get("meter"),
        "key": v2.get("key"),
        "barStartsSeconds": bar_boundaries[:-1],
        "beatTimesSeconds": v2.get("beatTimesSeconds", []),
        "bars": bars,
        "segments": segments,
    }
