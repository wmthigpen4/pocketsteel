"""Beat-aware semi-Markov decoding for factorized chord evidence.

Rhythm is soft evidence, never a boundary gate.  Acoustic change candidates
and beat candidates are unioned, so a syncopated or otherwise off-beat chord
change remains reachable.  When rhythm evidence is missing, malformed, or has
zero confidence, callers can hand control to their frozen decoder without any
serialization or post-processing in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import math
from typing import Any, Callable, Iterable, Mapping, Sequence, TypeVar

from .routing import FactorizedEvidence


BEAT_GRID_SCHEMA = "chord_beat_grid_v1"
SEGMENTAL_SCHEMA = "chord_segmental_decode_v1"
T = TypeVar("T")


def _numpy() -> Any:
    return importlib.import_module("numpy")


def _finite_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number.")
    return result


def _confidence(value: Any, name: str) -> float:
    result = _finite_number(value, name)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be from zero to one.")
    return result


@dataclass(frozen=True)
class BeatPoint:
    time_seconds: float
    confidence: float
    downbeat: bool
    downbeat_confidence: float


@dataclass(frozen=True)
class BeatGrid:
    """Validated beat/downbeat timing evidence."""

    confidence: float
    beats: tuple[BeatPoint, ...]
    source: str | None = None

    @property
    def usable(self) -> bool:
        return self.confidence > 0 and any(
            beat.confidence > 0 or (beat.downbeat and beat.downbeat_confidence > 0)
            for beat in self.beats
        )

    @property
    def mean_downbeat_confidence(self) -> float:
        values = [beat.downbeat_confidence for beat in self.beats if beat.downbeat]
        return sum(values) / len(values) if values else 0.0


def validate_beat_grid(value: Mapping[str, Any], *, duration_seconds: float) -> BeatGrid:
    """Validate the v1 beat-grid artifact and return immutable timing evidence."""

    duration = _finite_number(duration_seconds, "durationSeconds")
    if duration <= 0:
        raise ValueError("durationSeconds must be positive.")
    if not isinstance(value, Mapping) or value.get("schemaVersion") != BEAT_GRID_SCHEMA:
        raise ValueError(f"Beat grid schemaVersion must be {BEAT_GRID_SCHEMA!r}.")
    confidence = _confidence(value.get("confidence"), "beat-grid confidence")
    raw_beats = value.get("beats")
    if not isinstance(raw_beats, list) or not raw_beats:
        raise ValueError("Beat grid beats must be a non-empty list.")

    beats: list[BeatPoint] = []
    previous = -math.inf
    for index, item in enumerate(raw_beats):
        if not isinstance(item, Mapping):
            raise ValueError(f"Beat {index} must be an object.")
        time_seconds = _finite_number(item.get("timeSeconds"), f"beat {index} timeSeconds")
        if time_seconds < 0 or time_seconds > duration:
            raise ValueError(f"Beat {index} lies outside the audio duration.")
        if time_seconds <= previous:
            raise ValueError("Beat times must be strictly increasing.")
        previous = time_seconds
        beat_confidence = _confidence(item.get("confidence"), f"beat {index} confidence")
        downbeat = item.get("downbeat", False)
        if not isinstance(downbeat, bool):
            raise ValueError(f"Beat {index} downbeat must be boolean.")
        downbeat_confidence = _confidence(
            item.get("downbeatConfidence", beat_confidence if downbeat else 0.0),
            f"beat {index} downbeatConfidence",
        )
        if not downbeat and downbeat_confidence != 0:
            raise ValueError("A non-downbeat cannot carry positive downbeatConfidence.")
        beats.append(
            BeatPoint(
                time_seconds=time_seconds,
                confidence=beat_confidence,
                downbeat=downbeat,
                downbeat_confidence=downbeat_confidence,
            )
        )
    source = value.get("source")
    if source is not None and not isinstance(source, str):
        raise ValueError("Beat grid source must be a string when present.")
    return BeatGrid(confidence=confidence, beats=tuple(beats), source=source)


def usable_beat_grid(value: Any, *, duration_seconds: float) -> BeatGrid | None:
    """Return usable rhythm evidence; malformed and zero-confidence grids fail closed."""

    if not isinstance(value, Mapping):
        return None
    try:
        grid = validate_beat_grid(value, duration_seconds=duration_seconds)
    except (KeyError, TypeError, ValueError):
        return None
    return grid if grid.usable else None


def with_optional_beat_grid(
    value: Any,
    *,
    duration_seconds: float,
    fallback_decoder: Callable[[], T],
    beat_decoder: Callable[[BeatGrid], T],
) -> T:
    """Dispatch without touching the fallback result when rhythm is unusable."""

    grid = usable_beat_grid(value, duration_seconds=duration_seconds)
    if grid is None:
        return fallback_decoder()
    return beat_decoder(grid)


@dataclass(frozen=True)
class CandidateSet:
    frames: tuple[int, ...]
    sources: Mapping[int, tuple[str, ...]]


def boundary_candidate_frames(
    boundary_probabilities: Any,
    *,
    frame_seconds: float,
    beat_grid: BeatGrid,
    acoustic_threshold: float = 0.45,
) -> CandidateSet:
    """Union acoustic local maxima with beat/downbeat positions and endpoints."""

    numpy = _numpy()
    values = numpy.asarray(boundary_probabilities)
    if values.ndim == 2 and values.shape[1] == 1:
        values = values[:, 0]
    if values.ndim != 1 or len(values) < 1:
        raise ValueError("Boundary probabilities must be a non-empty vector.")
    if not numpy.all(numpy.isfinite(values)) or numpy.any(values < 0) or numpy.any(values > 1):
        raise ValueError("Boundary probabilities must be finite values from zero to one.")
    frame_width = _finite_number(frame_seconds, "frameSeconds")
    if frame_width <= 0:
        raise ValueError("frameSeconds must be positive.")
    threshold = _confidence(acoustic_threshold, "acousticThreshold")
    frame_count = len(values)
    sources: dict[int, set[str]] = {0: {"start"}, frame_count: {"end"}}

    for frame in range(1, frame_count):
        left = float(values[frame - 1])
        current = float(values[frame])
        right = float(values[frame + 1]) if frame + 1 < frame_count else -math.inf
        if current >= threshold and current >= left and current >= right and (current > left or current > right):
            sources.setdefault(frame, set()).add("acoustic")

    for beat in beat_grid.beats:
        if beat.confidence <= 0 and (not beat.downbeat or beat.downbeat_confidence <= 0):
            continue
        frame = int(round(beat.time_seconds / frame_width))
        if 0 < frame < frame_count:
            sources.setdefault(frame, set()).add("downbeat" if beat.downbeat else "beat")

    frames = tuple(sorted(sources))
    return CandidateSet(
        frames=frames,
        sources={frame: tuple(sorted(names)) for frame, names in sorted(sources.items())},
    )


def beat_alignment_evidence(
    time_seconds: float,
    beat_grid: BeatGrid,
    *,
    sigma_seconds: float = 0.07,
    beat_weight: float = 0.45,
    downbeat_weight: float = 0.35,
) -> float:
    """Return continuous Gaussian beat/downbeat evidence at one boundary time."""

    time = _finite_number(time_seconds, "timeSeconds")
    sigma = _finite_number(sigma_seconds, "sigmaSeconds")
    if sigma <= 0:
        raise ValueError("sigmaSeconds must be positive.")
    if beat_weight < 0 or downbeat_weight < 0:
        raise ValueError("Beat evidence weights must be non-negative.")
    beat_evidence = 0.0
    downbeat_evidence = 0.0
    for beat in beat_grid.beats:
        kernel = math.exp(-0.5 * ((time - beat.time_seconds) / sigma) ** 2)
        beat_evidence = max(beat_evidence, beat.confidence * kernel)
        if beat.downbeat:
            downbeat_evidence = max(downbeat_evidence, beat.downbeat_confidence * kernel)
    return beat_grid.confidence * (
        beat_weight * beat_evidence + downbeat_weight * downbeat_evidence
    )


@dataclass(frozen=True)
class SegmentalConfig:
    acoustic_candidate_threshold: float = 0.45
    boundary_scale: float = 0.8
    beat_sigma_seconds: float = 0.07
    beat_weight: float = 0.45
    downbeat_weight: float = 0.35
    transition_penalty: float = -1.15
    same_root_transition_penalty: float = -0.55
    same_state_boundary_penalty: float = -0.95
    no_chord_transition_penalty: float = -0.75
    short_segment_seconds: float = 0.35
    short_duration_penalty: float = 1.25
    long_segment_seconds: float = 12.0
    long_duration_penalty: float = 0.02
    bass_threshold: float = 0.65

    def validate(self) -> None:
        numeric = tuple(self.__dict__.values())
        if not all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) for value in numeric):
            raise ValueError("Segmental configuration values must be finite numbers.")
        if not 0 <= self.acoustic_candidate_threshold <= 1:
            raise ValueError("acoustic_candidate_threshold must be from zero to one.")
        if self.beat_sigma_seconds <= 0 or self.short_segment_seconds < 0 or self.long_segment_seconds <= 0:
            raise ValueError("Segmental timing constants are invalid.")
        if self.boundary_scale < 0 or self.beat_weight < 0 or self.downbeat_weight < 0:
            raise ValueError("Segmental evidence weights must be non-negative.")
        if self.short_duration_penalty < 0 or self.long_duration_penalty < 0:
            raise ValueError("Segment duration penalties must be non-negative.")
        if not 0 <= self.bass_threshold <= 1:
            raise ValueError("bass_threshold must be from zero to one.")


def _state_mapping(root_classes: int, mode_indices: Sequence[int], none_mode_index: int) -> tuple[tuple[int, int], ...]:
    values = [(0, none_mode_index)]
    for mode in mode_indices:
        values.extend((root, int(mode)) for root in range(1, root_classes))
    return tuple(values)


def _state_emissions(
    evidence: FactorizedEvidence,
    *,
    mode_indices: Sequence[int],
    none_mode_index: int,
    numpy: Any,
) -> tuple[Any, tuple[tuple[int, int], ...]]:
    if not mode_indices:
        raise ValueError("At least one chord mode index is required.")
    if none_mode_index < 0 or none_mode_index >= evidence.mode.shape[1]:
        raise ValueError("none_mode_index is outside the mode vocabulary.")
    if any(index < 0 or index >= evidence.mode.shape[1] or index == none_mode_index for index in mode_indices):
        raise ValueError("mode_indices contain an invalid or no-chord mode.")
    mapping = _state_mapping(evidence.root.shape[1], mode_indices, none_mode_index)
    log_root = numpy.log(numpy.clip(evidence.root, 1e-12, 1.0))
    log_mode = numpy.log(numpy.clip(evidence.mode, 1e-12, 1.0))
    columns = [log_root[:, 0] + log_mode[:, none_mode_index]]
    for mode in mode_indices:
        columns.extend(log_root[:, root] + log_mode[:, mode] for root in range(1, evidence.root.shape[1]))
    return numpy.stack(columns, axis=1), mapping


def _transition_scores(mapping: Sequence[tuple[int, int]], config: SegmentalConfig, numpy: Any) -> Any:
    count = len(mapping)
    output = numpy.full((count, count), config.transition_penalty, dtype=numpy.float64)
    for left, (left_root, left_mode) in enumerate(mapping):
        for right, (right_root, right_mode) in enumerate(mapping):
            if left == right:
                output[left, right] = config.same_state_boundary_penalty
            elif left_root == 0 or right_root == 0:
                output[left, right] = config.no_chord_transition_penalty
            elif left_root == right_root:
                output[left, right] = config.same_root_transition_penalty
    return output


def _duration_prior(duration_seconds: float, config: SegmentalConfig) -> float:
    shortfall = max(0.0, config.short_segment_seconds - duration_seconds)
    excess = max(0.0, duration_seconds - config.long_segment_seconds)
    return -config.short_duration_penalty * shortfall * shortfall - config.long_duration_penalty * excess * excess


def _boundary_score(
    frame: int,
    evidence: FactorizedEvidence,
    beat_grid: BeatGrid,
    frame_seconds: float,
    config: SegmentalConfig,
) -> float:
    probability = min(0.98, max(0.02, float(evidence.boundary[frame])))
    log_odds = math.log(probability / (1.0 - probability))
    rhythm = beat_alignment_evidence(
        frame * frame_seconds,
        beat_grid,
        sigma_seconds=config.beat_sigma_seconds,
        beat_weight=config.beat_weight,
        downbeat_weight=config.downbeat_weight,
    )
    return config.boundary_scale * log_odds + rhythm


def _segment_factors(
    evidence: FactorizedEvidence,
    *,
    start: int,
    end: int,
    root: int,
    mode: int,
    quality_mode_indices: Sequence[int] | None,
    config: SegmentalConfig,
    numpy: Any,
) -> tuple[int, int, float]:
    root_confidence = float(evidence.root[start:end, root].mean())
    mode_confidence = float(evidence.mode[start:end, mode].mean())
    if root == 0:
        return -1, 0, math.sqrt(max(0.0, root_confidence * mode_confidence))

    if quality_mode_indices is None:
        allowed = list(range(evidence.quality.shape[1]))
    else:
        if len(quality_mode_indices) != evidence.quality.shape[1]:
            raise ValueError("quality_mode_indices must align with the quality vocabulary.")
        allowed = [index for index, value in enumerate(quality_mode_indices) if int(value) == mode]
        if not allowed:
            allowed = list(range(evidence.quality.shape[1]))
    log_quality = numpy.log(numpy.clip(evidence.quality[start:end, allowed], 1e-12, 1.0)).sum(axis=0)
    quality = int(allowed[int(log_quality.argmax())])
    quality_confidence = float(evidence.quality[start:end, quality].mean())

    bass_mean = evidence.bass[start:end].mean(axis=0)
    bass = int(bass_mean.argmax())
    if bass == root or bass == 0 or float(bass_mean[bass]) < config.bass_threshold:
        bass = 0
    confidence = max(0.0, root_confidence * mode_confidence * quality_confidence) ** (1.0 / 3.0)
    return quality, bass, confidence


def _collapse_identical_spans(spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for span in spans:
        key = tuple(span[name] for name in ("root", "mode", "quality", "bass"))
        if output and tuple(output[-1][name] for name in ("root", "mode", "quality", "bass")) == key and output[-1]["endFrame"] == span["startFrame"]:
            left_frames = int(output[-1]["endFrame"]) - int(output[-1]["startFrame"])
            right_frames = int(span["endFrame"]) - int(span["startFrame"])
            output[-1]["confidence"] = (
                float(output[-1]["confidence"]) * left_frames + float(span["confidence"]) * right_frames
            ) / max(1, left_frames + right_frames)
            output[-1]["endFrame"] = span["endFrame"]
            output[-1]["endSeconds"] = span["endSeconds"]
        else:
            output.append(dict(span))
    return output


def candidate_boundary_diagnostics(
    candidates: CandidateSet | Sequence[int],
    reference_boundaries_seconds: Iterable[float],
    *,
    frame_seconds: float,
    selected_frames: Sequence[int] = (),
    tolerance_seconds: float = 0.25,
) -> dict[str, Any]:
    """Report candidate reachability and selected-boundary timing offsets."""

    if isinstance(candidates, CandidateSet):
        frames = tuple(
            frame
            for frame in candidates.frames
            if any(source not in {"start", "end"} for source in candidates.sources.get(frame, ()))
        )
    else:
        frames = tuple(candidates)
    references = [float(value) for value in reference_boundaries_seconds]
    candidate_times = [frame * frame_seconds for frame in frames]
    selected_times = [frame * frame_seconds for frame in selected_frames]

    def nearest(times: Sequence[float]) -> list[float]:
        return [min((abs(reference - value) for value in times), default=math.inf) for reference in references]

    candidate_offsets = nearest(candidate_times)
    selected_offsets = nearest(selected_times)
    finite_candidate = [value for value in candidate_offsets if math.isfinite(value)]
    finite_selected = [value for value in selected_offsets if math.isfinite(value)]
    return {
        "referenceBoundaryCount": len(references),
        "candidateBoundaryCount": len(frames),
        "selectedBoundaryCount": len(selected_frames),
        "toleranceSeconds": tolerance_seconds,
        "candidateRecall": (
            sum(value <= tolerance_seconds for value in candidate_offsets) / len(references)
            if references
            else None
        ),
        "meanNearestCandidateOffsetSeconds": (
            sum(finite_candidate) / len(finite_candidate) if finite_candidate else None
        ),
        "maximumNearestCandidateOffsetSeconds": max(finite_candidate) if finite_candidate else None,
        "selectedRecall": (
            sum(value <= tolerance_seconds for value in selected_offsets) / len(references)
            if references
            else None
        ),
        "meanNearestSelectedOffsetSeconds": (
            sum(finite_selected) / len(finite_selected) if finite_selected else None
        ),
    }


def decode_factorized_segments(
    evidence: FactorizedEvidence,
    *,
    duration_seconds: float,
    frame_seconds: float,
    beat_grid: Any,
    fallback_decoder: Callable[[], T],
    mode_indices: Sequence[int] = (1, 2, 3),
    none_mode_index: int = 0,
    quality_mode_indices: Sequence[int] | None = None,
    config: SegmentalConfig = SegmentalConfig(),
    reference_boundaries_seconds: Iterable[float] = (),
) -> dict[str, Any] | T:
    """Decode root/mode segments with prefix evidence and soft rhythm cues.

    Unusable rhythm evidence returns ``fallback_decoder()`` directly.  With a
    valid grid, final quality and inversion are selected independently inside
    each semi-Markov span.
    """

    duration = _finite_number(duration_seconds, "durationSeconds")
    width = _finite_number(frame_seconds, "frameSeconds")
    if duration <= 0 or width <= 0:
        raise ValueError("Duration and frame width must be positive.")
    config.validate()
    grid = usable_beat_grid(beat_grid, duration_seconds=duration)
    if grid is None:
        return fallback_decoder()

    numpy = _numpy()
    candidates = boundary_candidate_frames(
        evidence.boundary,
        frame_seconds=width,
        beat_grid=grid,
        acoustic_threshold=config.acoustic_candidate_threshold,
    )
    positions = candidates.frames
    if len(positions) < 2 or positions[0] != 0 or positions[-1] != evidence.frame_count:
        return fallback_decoder()

    emissions, state_mapping = _state_emissions(
        evidence,
        mode_indices=mode_indices,
        none_mode_index=none_mode_index,
        numpy=numpy,
    )
    # Prefix sums make every possible segment emission O(states), rather than
    # repeatedly summing all frames inside the candidate interval.
    prefix = numpy.concatenate(
        (numpy.zeros((1, emissions.shape[1]), dtype=numpy.float64), numpy.cumsum(emissions, axis=0)),
        axis=0,
    )
    transition = _transition_scores(state_mapping, config, numpy)
    candidate_count = len(positions)
    state_count = len(state_mapping)
    scores = numpy.full((candidate_count, state_count), -numpy.inf, dtype=numpy.float64)
    back_start = numpy.full((candidate_count, state_count), -1, dtype=numpy.int64)
    back_state = numpy.full((candidate_count, state_count), -1, dtype=numpy.int64)

    for end_index in range(1, candidate_count):
        end = positions[end_index]
        for start_index in range(end_index):
            start = positions[start_index]
            if end <= start:
                continue
            duration_prior = _duration_prior((end - start) * width, config)
            segment_evidence = prefix[end] - prefix[start] + duration_prior
            if start_index == 0:
                candidate_scores = segment_evidence
                previous_states = numpy.full(state_count, -1, dtype=numpy.int64)
            else:
                boundary_score = _boundary_score(start, evidence, grid, width, config)
                transitions = scores[start_index][:, None] + transition
                previous_states = transitions.argmax(axis=0)
                candidate_scores = (
                    transitions[previous_states, numpy.arange(state_count)]
                    + boundary_score
                    + segment_evidence
                )
            improved = candidate_scores > scores[end_index]
            scores[end_index, improved] = candidate_scores[improved]
            back_start[end_index, improved] = start_index
            back_state[end_index, improved] = previous_states[improved]

    state = int(scores[-1].argmax())
    if not math.isfinite(float(scores[-1, state])):
        return fallback_decoder()
    raw: list[tuple[int, int, int]] = []
    end_index = candidate_count - 1
    while end_index > 0:
        start_index = int(back_start[end_index, state])
        if start_index < 0:
            return fallback_decoder()
        raw.append((positions[start_index], positions[end_index], state))
        previous_state = int(back_state[end_index, state])
        end_index = start_index
        if end_index > 0:
            if previous_state < 0:
                return fallback_decoder()
            state = previous_state
    raw.reverse()

    spans: list[dict[str, Any]] = []
    for start, end, state in raw:
        root, mode = state_mapping[state]
        quality, bass, confidence = _segment_factors(
            evidence,
            start=start,
            end=end,
            root=root,
            mode=mode,
            quality_mode_indices=quality_mode_indices,
            config=config,
            numpy=numpy,
        )
        spans.append(
            {
                "startFrame": start,
                "endFrame": end,
                "startSeconds": min(duration, start * width),
                "endSeconds": duration if end == evidence.frame_count else min(duration, end * width),
                "root": root,
                "mode": mode,
                "quality": quality,
                "bass": bass,
                "confidence": confidence,
            }
        )
    spans = _collapse_identical_spans(spans)
    selected_frames = [int(span["startFrame"]) for span in spans[1:]]
    diagnostics = candidate_boundary_diagnostics(
        candidates,
        reference_boundaries_seconds,
        frame_seconds=width,
        selected_frames=selected_frames,
    )
    diagnostics.update(
        {
            "prefixLogEvidence": True,
            "semiMarkov": True,
            "beatGridConfidence": grid.confidence,
            "meanDownbeatConfidence": grid.mean_downbeat_confidence,
            "candidateSources": {
                str(frame): list(names) for frame, names in candidates.sources.items()
            },
            "acousticOffbeatCandidateCount": sum(
                "acoustic" in names and "beat" not in names and "downbeat" not in names
                for frame, names in candidates.sources.items()
                if frame not in {0, evidence.frame_count}
            ),
        }
    )
    return {
        "schemaVersion": SEGMENTAL_SCHEMA,
        "decoder": "beat-aware-semi-markov-root-mode-v1",
        "frameSeconds": width,
        "durationSeconds": duration,
        "spans": spans,
        "diagnostics": diagnostics,
    }
