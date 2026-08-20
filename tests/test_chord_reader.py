from __future__ import annotations

import json
import hashlib
from pathlib import Path
import subprocess
import sys
import shutil

import numpy as np
import pytest
import steel_guitar_rag.chord_reader.student as student_module

from steel_guitar_rag.chord_reader.benchmark import run_hybrid_benchmark, run_prediction_benchmark
from steel_guitar_rag.chord_reader.labels import normalize_chord, transpose_chord
from steel_guitar_rag.chord_reader.btc import load_model_registry, verify_model_snapshot
from steel_guitar_rag.chord_reader.chart_reference import build_chart_reference
from steel_guitar_rag.chord_reader.hybrid import hybridize_predictions
from steel_guitar_rag.chord_reader.datasets import (
    _midi_chord_label,
    _tick_seconds,
    _weighted_midi_chord_label,
    parse_aam_beatinfo,
    parse_guitarset_jams,
    parse_idmt_chords,
    parse_winterreise_chords,
)
from steel_guitar_rag.chord_reader.manifests import (
    WeakLabelDiagnostics,
    admit_weak_label,
    assign_group_splits,
    validate_catalog,
    validate_track_manifest,
)
from steel_guitar_rag.chord_reader.metrics import score_segments
from steel_guitar_rag.chord_reader.student import (
    STUDENT_CLASSES,
    StudentHeterogeneousBoundaryGuidedEnsembleRecognizer,
    _blend_student_factor_logits,
    composition_balance_feature_cache,
    frame_labels,
    frame_label_mask,
    _root_guided_logits,
    _root_then_quality_student_path,
    domain_gate_probability,
    student_audio_profile,
    _quality_guided_logits,
    _mode_guided_logits,
    _extension_guided_logits,
    _factorized_student_path,
    _product_logits,
    merge_feature_caches,
    student_index,
    student_label,
    transpose_student_index,
)
from steel_guitar_rag.chord_reader.routing import ROUTER_FEATURE_NAMES
from steel_guitar_rag.chord_reader.promotion import evaluate_promotion
from steel_guitar_rag.chord_reader.review import build_travis_packet, score_travis_review


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("value", "detailed", "product", "attention"),
    [
        ("C", "C:maj", "C", False),
        ("Bb:min7", "Bb:min7", "Bbm7", False),
        ("F#7", "F#:7", "F#7", False),
        ("G:maj7/B", "G:maj7/B", "G", False),
        ("D:sus4", "D:sus4", "D", True),
        ("C#dim7", "C#:dim7", "C#", True),
        ("N.C.", "N", "N.C.", False),
        ("X", "X", "N.C.", True),
    ],
)
def test_normalize_chord(value: str, detailed: str, product: str, attention: bool) -> None:
    label = normalize_chord(value)
    assert label.detailed_symbol == detailed
    assert label.product_symbol == product
    assert label.needs_attention is attention


def test_transpose_chord_preserves_quality_and_bass() -> None:
    label = transpose_chord("Bb:min7/Db", 2)
    assert label.detailed_symbol == "C:min7/Eb"
    assert label.product_symbol == "Cm7"
    assert label.bass == "Eb"


@pytest.mark.parametrize(
    ("notes", "expected"),
    [
        ([48, 52, 55], "C:maj"),
        ([45, 48, 52], "A:min"),
        ([43, 47, 50, 53], "G:7"),
        ([41, 45, 48, 52], "F:maj7"),
        ([40, 48, 52, 55], "C:maj/E"),
        ([60], None),
    ],
)
def test_midi_chord_label(notes: list[int], expected: str | None) -> None:
    assert _midi_chord_label(notes) == expected


def test_weighted_midi_chord_tolerates_melody_and_uses_bass() -> None:
    assert _weighted_midi_chord_label({0: 3, 4: 2, 7: 3, 2: 1}, 0) == "C:maj"
    assert _weighted_midi_chord_label({0: 3, 4: 2, 7: 3}, 7) == "C:maj/G"


def test_tick_seconds_obeys_tempo_changes() -> None:
    assert _tick_seconds(192, 96, [(0, 500_000), (96, 1_000_000)]) == pytest.approx(1.5)


def test_root_then_quality_decoder_blocks_quality_feedback_into_roots() -> None:
    root_source = np.full((8, 49), -5.0, dtype=np.float32)
    root_source[:4, 1] = 5.0
    root_source[4:, 8] = 5.0
    quality_a = root_source.copy()
    quality_b = root_source.copy()
    quality_b[:, 13:] += 20.0
    path_a = _root_then_quality_student_path(root_source, quality_a, np)
    path_b = _root_then_quality_student_path(root_source, quality_b, np)
    roots_a = [0 if value == 0 else (value - 1) % 12 + 1 for value in path_a]
    roots_b = [0 if value == 0 else (value - 1) % 12 + 1 for value in path_b]
    assert roots_a == roots_b


def test_domain_gate_profile_and_probability_are_finite() -> None:
    features = np.full((20, 61), 1 / 12, dtype=np.float32)
    features[:, -1] = np.linspace(0.1, 0.2, 20)
    profile = student_audio_profile(features, np)
    assert profile.shape == (14,)
    config = json.loads((ROOT / "ui/models/chord-domain-gate-v1.json").read_text())
    probability = domain_gate_probability(features, config, np)
    assert 0 <= probability <= 1


class _FakeStudentExpert:
    def __init__(self, logits: np.ndarray, boundary: np.ndarray | None = None) -> None:
        self.feature_kind = "multiband_chroma_v2"
        self.logits = logits
        self.boundary = boundary
        self.boundary_aware = boundary is not None
        self.boundary_scale = 1.0
        self.boundary_bias = -1.0
        self.calls = 0

    def _logits(self, _features: np.ndarray) -> np.ndarray:
        self.calls += 1
        return self.logits.copy()

    def _outputs(self, _features: np.ndarray) -> np.ndarray:
        self.calls += 1
        if self.boundary is None:
            return self.logits.copy()
        return np.concatenate((self.logits, self.boundary[:, None]), axis=-1)


def _fake_soft_router_recognizer(
    *,
    soft_router: dict[str, object] | None,
) -> StudentHeterogeneousBoundaryGuidedEnsembleRecognizer:
    frames = 6
    base = np.full((frames, STUDENT_CLASSES), -9.0, dtype=np.float64)
    base[:3, student_index("C:maj")] = 9.0
    base[3:, student_index("G:maj")] = 9.0
    quality = np.full_like(base, -9.0)
    quality[:3, student_index("C:7")] = 9.0
    quality[3:, student_index("G:7")] = 9.0
    guide_boundary = np.asarray([-8.0, -8.0, 8.0, -8.0, -8.0, -8.0])
    secondary_boundary = np.asarray([-8.0, 5.0, 5.0, -8.0, -8.0, -8.0])

    recognizer = StudentHeterogeneousBoundaryGuidedEnsembleRecognizer.__new__(
        StudentHeterogeneousBoundaryGuidedEnsembleRecognizer
    )
    recognizer.members = [_FakeStudentExpert(base), _FakeStudentExpert(base), _FakeStudentExpert(base)]
    recognizer.weights = [0.5, 0.5, 0.0]
    recognizer.root_guide_only = True
    recognizer.guide = _FakeStudentExpert(base, guide_boundary)
    recognizer.secondary_guide = _FakeStudentExpert(base, secondary_boundary)
    recognizer.secondary_boundary_weight = 0.5
    recognizer.domain_gate = None
    recognizer.soft_router = soft_router
    recognizer.numpy = np
    recognizer.quality_guides = [_FakeStudentExpert(quality), _FakeStudentExpert(quality)]
    recognizer.quality_mode_threshold = 0.6
    recognizer.quality_extension_threshold = 0.7
    recognizer.factorized_decoder = True
    recognizer.product_boundary_scale = 1.3
    recognizer.product_boundary_bias = -2.0
    return recognizer


def _fake_multiband_features(_audio: Path, _kind: str) -> tuple[np.ndarray, float]:
    features = np.full((6, 61), 1 / 12, dtype=np.float32)
    features[:, -1] = np.linspace(0.1, 0.2, 6)
    return features, 0.6


def _student_root_probabilities(logits: np.ndarray) -> np.ndarray:
    values = np.exp(logits - logits.max(axis=1, keepdims=True))
    values /= values.sum(axis=1, keepdims=True)
    output = np.zeros((len(values), 13))
    output[:, 0] = values[:, 0]
    for quality in range(4):
        output[:, 1:] += values[:, 1 + quality * 12 : 1 + (quality + 1) * 12]
    return output


def test_soft_router_and_legacy_domain_gate_are_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="mutually exclusive"):
        StudentHeterogeneousBoundaryGuidedEnsembleRecognizer(
            [],
            [],
            Path("boundary.onnx"),
            domain_gate=Path("domain-gate.json"),
            soft_router=Path("soft-router.json"),
        )


def test_factor_blend_has_exact_endpoints_and_quality_cannot_move_root() -> None:
    expanded = np.full((2, STUDENT_CLASSES), -6.0)
    conservative = np.full((2, STUDENT_CLASSES), -6.0)
    expanded[:, student_index("C:maj")] = 7.0
    expanded[:, student_index("G:min7")] = 2.0
    conservative[:, student_index("C:7")] = 2.0
    conservative[:, student_index("G:min")] = 7.0

    assert _blend_student_factor_logits(expanded, conservative, 0.0, np) is expanded
    assert _blend_student_factor_logits(expanded, conservative, 1.0, np) is conservative
    mixed = _blend_student_factor_logits(expanded, conservative, 0.35, np)
    expected_root = 0.65 * _student_root_probabilities(expanded) + 0.35 * _student_root_probabilities(
        conservative
    )
    assert _student_root_probabilities(mixed) == pytest.approx(expected_root)


def test_invalid_or_zero_soft_router_preserves_existing_prediction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(student_module, "extract_student_features", _fake_multiband_features)
    baseline = _fake_soft_router_recognizer(soft_router=None).predict(Path("fixture.wav"))
    invalid = _fake_soft_router_recognizer(soft_router={"schemaVersion": "invalid"}).predict(
        Path("fixture.wav")
    )
    monkeypatch.setattr(student_module, "router_weight", lambda _features, _artifact: 0.0)
    zero = _fake_soft_router_recognizer(soft_router={}).predict(Path("fixture.wav"))
    assert invalid == baseline
    assert zero == baseline


def test_soft_router_conservative_endpoint_matches_counterfactual(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(student_module, "extract_student_features", _fake_multiband_features)
    monkeypatch.setattr(student_module, "router_weight", lambda _features, _artifact: 1.0)
    routed = _fake_soft_router_recognizer(soft_router={}).predict(Path("fixture.wav"))
    counterfactual = _fake_soft_router_recognizer(soft_router={}).predict_counterfactuals(
        Path("fixture.wav")
    )
    assert routed["domainRoute"] == "conservative-sparse"
    assert routed["softRouterWeight"] == 1.0
    assert routed["segments"] == counterfactual["conservative"]["segments"]


def test_counterfactual_api_emits_named_features_from_one_inference_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(student_module, "extract_student_features", _fake_multiband_features)
    recognizer = _fake_soft_router_recognizer(soft_router=None)
    result = recognizer.predict_counterfactuals(
        Path("fixture.wav"),
        prediction_id="fixture",
        router_context={"beatConfidence": 0.8, "downbeatConfidence": 0.7, "oodDistance": 0.2},
    )
    experts = recognizer.members + recognizer.quality_guides + [recognizer.guide, recognizer.secondary_guide]
    assert all(expert.calls == 1 for expert in experts)
    assert result["schemaVersion"] == "chord_router_counterfactual_v1"
    assert list(result["routerFeatures"]) == list(ROUTER_FEATURE_NAMES)
    assert result["routerFeatures"]["beatConfidence"] == 0.8
    assert result["routerFeatures"]["downbeatConfidence"] == 0.7
    assert result["routerFeatures"]["oodDistance"] == 0.2
    assert result["expanded"]["domainRoute"] == "expanded-mixture"
    assert result["conservative"]["domainRoute"] == "conservative-sparse"
    with pytest.raises(TypeError):
        recognizer.predict_counterfactuals(Path("fixture.wav"), reference={})  # type: ignore[call-arg]


def test_group_splits_prevent_composition_leakage() -> None:
    tracks = [
        {"id": "a", "datasetId": "aam", "groupId": "render-1", "compositionId": "same-song"},
        {"id": "b", "datasetId": "guitarset", "groupId": "player-2", "compositionId": "same-song"},
        {"id": "c", "datasetId": "aam", "groupId": "render-3", "compositionId": "other-song"},
    ]
    first = assign_group_splits(tracks)
    second = assign_group_splits(reversed(tracks))
    assert first[0]["split"] == first[1]["split"]
    assert {item["id"]: item["split"] for item in first} == {item["id"]: item["split"] for item in second}


def test_manifest_rejects_split_leakage_and_weak_weight_overflow() -> None:
    base = {
        "schemaVersion": "chord_track_manifest_v1",
        "tracks": [
            {
                "id": "a",
                "datasetId": "sgf_steel_reference",
                "split": "train",
                "splitGroup": "song",
                "labelSource": "weak_chart_alignment",
                "trainingWeight": 0.36,
            }
        ],
    }
    with pytest.raises(ValueError, match="weight ceiling"):
        validate_track_manifest(base)
    base["tracks"][0]["trainingWeight"] = 0.35
    base["tracks"].append({**base["tracks"][0], "id": "b", "split": "test", "trainingWeight": 0})
    with pytest.raises(ValueError, match="Split leakage"):
        validate_track_manifest(base)


def test_weak_label_admission_gate() -> None:
    passing = admit_weak_label(WeakLabelDiagnostics(True, True, 0.91, 0.8))
    failing = admit_weak_label(WeakLabelDiagnostics(True, True, 0.89, 0.95))
    assert passing == {
        "admitted": True,
        "trainingWeight": 0.35,
        "reasons": [],
        "diagnostics": {
            "complete_coverage": True,
            "monotonic_alignment": True,
            "boundary_within_half_beat_fraction": 0.91,
            "dual_reader_duration_agreement": 0.8,
        },
    }
    assert failing["admitted"] is False
    assert failing["trainingWeight"] == 0


def test_chart_reference_uses_explicit_chart_spans_and_reports_admission() -> None:
    timing = {
        "id": "song",
        "engine": "timing-only",
        "durationSeconds": 4,
        "barStartsSeconds": [0, 2],
        "beatTimesSeconds": [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5],
    }
    chart = {
        "id": "song-chart",
        "cells": [
            {"cell": 1, "chords": ["C"]},
            {"cell": 2, "chords": ["G7", "C"], "weights": [1, 1]},
        ],
    }
    reader = {
        "engine": "reader-a",
        "segments": [
            {"start": 0, "end": 2, "label": "C"},
            {"start": 2, "end": 3, "label": "G"},
            {"start": 3, "end": 4, "label": "C"},
        ],
    }
    reference, report = build_chart_reference(chart, timing, independent_readers=[reader, reader])
    assert reference["segments"] == [
        {"start": 0.0, "end": 2.0, "label": "C:maj"},
        {"start": 2.0, "end": 3.0, "label": "G:7"},
        {"start": 3.0, "end": 4.0, "label": "C:maj"},
    ]
    assert report["admission"]["admitted"] is True


def test_chart_reference_never_uses_reader_labels_as_ground_truth() -> None:
    timing = {"durationSeconds": 1, "barStartsSeconds": [0], "beatTimesSeconds": [0, 0.5]}
    chart = {"cells": [{"chords": ["F:min"]}]}
    wrong = {"engine": "wrong", "segments": [{"start": 0, "end": 1, "label": "B"}]}
    reference, report = build_chart_reference(chart, timing, independent_readers=[wrong, wrong])
    assert reference["segments"][0]["label"] == "F:min"
    assert report["admission"]["admitted"] is False


def test_catalog_is_valid_and_has_ten_steel_candidates() -> None:
    value = json.loads((ROOT / "chord_reader/datasets/catalog.json").read_text(encoding="utf-8"))
    validate_catalog(value)
    assert {item["id"] for item in value["datasets"]} == {
        "aam",
            "guitarset",
            "idmt_guitar",
        "lofi_chords",
        "sgf_steel_reference",
        "winterreise",
    }
    assert len(value["steelReferenceCandidates"]) == 10


def test_segment_metrics_measure_roots_qualities_boundaries_and_edits() -> None:
    reference = [
        {"start": 0, "end": 2, "label": "C"},
        {"start": 2, "end": 4, "label": "G7"},
    ]
    prediction = [
        {"start": 0, "end": 2.1, "label": "C:maj7"},
        {"start": 2.1, "end": 4, "label": "G"},
    ]
    result = score_segments(reference, prediction, boundary_tolerance_seconds=0.25)
    assert result["evaluatedDurationSeconds"] == pytest.approx(4)
    assert result["rootWeightedRecall"] == pytest.approx(0.975)
    assert result["majorMinorWeightedRecall"] == pytest.approx(0.975)
    assert result["detailedWeightedRecall"] == 0
    assert result["boundary"]["f1"] == 1
    assert result["sequenceEditRate"] == pytest.approx(0.5)


def test_segment_metrics_treat_enharmonic_chord_spellings_as_equivalent() -> None:
    reference = [
        {"start": 0, "end": 2, "label": "Eb:maj/Bb"},
        {"start": 2, "end": 4, "label": "Db:min"},
    ]
    prediction = [
        {"start": 0, "end": 2, "label": "D#:maj/A#"},
        {"start": 2, "end": 4, "label": "C#:min"},
    ]

    result = score_segments(reference, prediction)

    assert result["rootWeightedRecall"] == 1
    assert result["majorMinorWeightedRecall"] == 1
    assert result["detailedWeightedRecall"] == 1
    assert result["sequenceEditRate"] == 0


def test_segment_metrics_keep_enharmonic_quality_and_bass_errors_visible() -> None:
    reference = [{"start": 0, "end": 2, "label": "Eb:min/Bb"}]
    prediction = [{"start": 0, "end": 2, "label": "D#:maj/G#"}]

    result = score_segments(reference, prediction)

    assert result["rootWeightedRecall"] == 1
    assert result["majorMinorWeightedRecall"] == 0
    assert result["detailedWeightedRecall"] == 0


def test_segment_metrics_report_exact_vocabulary_ceiling_and_oov_duration() -> None:
    reference = [
        {"start": 0, "end": 1, "label": "Eb:7"},
        {"start": 1, "end": 3, "label": "C:maj7"},
        {"start": 3, "end": 4, "label": "D:sus4"},
        {"start": 4, "end": 5, "label": "A:min/C"},
    ]
    prediction = [{"start": 0, "end": 5, "label": "N", "confidence": 0.1}]

    result = score_segments(reference, prediction)
    coverage = result["vocabularyCoverage"]

    assert coverage["available"] is True
    assert coverage["vocabularySize"] == 49
    assert coverage["referenceDurationSeconds"] == 5
    assert coverage["supportedDurationSeconds"] == 1
    assert coverage["outOfVocabularyDurationSeconds"] == 4
    assert coverage["exactDetailedWeightedRecallCeiling"] == pytest.approx(0.2)
    assert coverage["outOfVocabulary"] == [
        {"label": "C:maj7", "durationSeconds": 2.0},
        {"label": "A:min/C", "durationSeconds": 1.0},
        {"label": "D:sus4", "durationSeconds": 1.0},
    ]


def test_segment_metrics_report_duration_weighted_confusion_and_confidence_curve() -> None:
    reference = [
        {"start": 0, "end": 1, "label": "C:maj"},
        {"start": 1, "end": 2, "label": "G:maj"},
    ]
    prediction = [
        {"start": 0, "end": 1, "label": "C:maj", "confidence": 0.9},
        {"start": 1, "end": 2, "label": "D:maj", "confidence": 0.2},
    ]

    result = score_segments(reference, prediction)

    assert result["confusion"]["root"]["cells"] == [
        {"reference": "C", "prediction": "C", "durationSeconds": 1.0},
        {"reference": "G", "prediction": "D", "durationSeconds": 1.0},
    ]
    curve = {
        point["minimumConfidence"]: point for point in result["confidenceCoverage"]["curve"]
    }
    assert curve[0.0]["coverage"] == 1
    assert curve[0.0]["detailedPrecision"] == pytest.approx(0.5)
    assert curve[0.5]["coverage"] == pytest.approx(0.5)
    assert curve[0.5]["detailedPrecision"] == 1
    assert curve[0.95]["coverage"] == 0
    assert curve[0.95]["detailedPrecision"] is None
    assert result["confidenceCoverage"]["calibration"]["expectedCalibrationError"][
        "detailed"
    ] == pytest.approx(0.15)


def test_segment_metrics_keep_play_along_product_precision_separate_from_detail() -> None:
    reference = [{"start": 0, "end": 2, "label": "C:maj7/E"}]
    prediction = [{"start": 0, "end": 2, "label": "C:maj", "confidence": 0.9}]

    result = score_segments(reference, prediction)
    curve = {
        point["minimumConfidence"]: point for point in result["confidenceCoverage"]["curve"]
    }

    assert result["productWeightedRecall"] == 1
    assert result["detailedWeightedRecall"] == 0
    assert curve[0.5]["productPrecision"] == 1
    assert curve[0.5]["detailedPrecision"] == 0
    assert curve[0.5]["productCorrectDurationSeconds"] == 2
    product_cell = result["confusion"]["product"]["cells"][0]
    assert product_cell == {"reference": "C", "prediction": "C", "durationSeconds": 2.0}


@pytest.mark.parametrize(
    ("reference_labels", "prediction_labels", "operation", "counts"),
    [
        (["C", "D"], ["C", "G", "D"], "insert", (1, 0, 0)),
        (["C", "G", "D"], ["C", "D"], "delete", (0, 1, 0)),
        (["C", "G"], ["C", "D"], "substitute", (0, 0, 1)),
    ],
)
def test_segment_metrics_report_levenshtein_operation_counts(
    reference_labels: list[str],
    prediction_labels: list[str],
    operation: str,
    counts: tuple[int, int, int],
) -> None:
    reference = [
        {"start": index, "end": index + 1, "label": label}
        for index, label in enumerate(reference_labels)
    ]
    prediction_duration = len(reference_labels)
    prediction = [
        {
            "start": index * prediction_duration / len(prediction_labels),
            "end": (index + 1) * prediction_duration / len(prediction_labels),
            "label": label,
        }
        for index, label in enumerate(prediction_labels)
    ]

    edits = score_segments(reference, prediction)["sequenceEdits"]

    assert edits["distance"] == 1
    assert edits["counts"] == {
        "insertions": counts[0],
        "deletions": counts[1],
        "substitutions": counts[2],
    }
    assert [item["operation"] for item in edits["operations"]] == [operation]


def test_segment_metrics_use_collapsed_musical_changes_for_canonical_boundaries() -> None:
    reference = [
        {"start": 0, "end": 1, "label": "C:maj"},
        {"start": 1, "end": 2, "label": "B#:maj7"},
        {"start": 2, "end": 3, "label": "G:maj"},
    ]
    prediction = [
        {"start": 0, "end": 2, "label": "C:maj"},
        {"start": 2, "end": 3, "label": "G:maj"},
    ]

    result = score_segments(reference, prediction)

    assert result["boundary"]["f1"] == 1
    assert result["authoredSegmentBoundary"]["f1"] == pytest.approx(2 / 3)


def test_hybrid_preserves_strong_no_chord_without_forcing_bar_labels() -> None:
    v2 = {
        "id": "song",
        "durationSeconds": 6,
        "barStartsSeconds": [0, 2, 4],
        "segments": [
            {"start": 0, "end": 2, "label": "N.C.", "confidence": 0.98},
            {"start": 2, "end": 4, "label": "N.C.", "confidence": 0.98},
            {"start": 4, "end": 6, "label": "C", "confidence": 0.9},
        ],
    }
    student = {
        "id": "song",
        "segments": [
            {"start": 0, "end": 1, "label": "E:maj", "confidence": 0.3},
            {"start": 1, "end": 4.4, "label": "E:min", "confidence": 0.3},
            {"start": 4.4, "end": 6, "label": "G:7", "confidence": 0.7},
        ],
    }
    result = hybridize_predictions(v2, student)
    assert [{key: value for key, value in segment.items() if key != "confidence"} for segment in result["segments"]] == [
        {
            "start": 0.0,
            "end": 4.0,
            "label": "N",
            "productLabel": "N.C.",
            "source": "v2-no-chord",
        },
        {
            "start": 4.0,
            "end": 4.4,
            "label": "E:min",
            "productLabel": "Em",
            "source": "student",
        },
        {
            "start": 4.4,
            "end": 6.0,
            "label": "G:7",
            "productLabel": "G7",
            "source": "student",
        },
    ]
    assert [segment["confidence"] for segment in result["segments"]] == pytest.approx([0.98, 0.3, 0.7])


def test_hybrid_benchmark_scores_and_freezes_existing_predictions(tmp_path: Path) -> None:
    reference = tmp_path / "reference.json"
    reference.write_text(
        json.dumps({"segments": [{"start": 0, "end": 4, "label": "C:maj"}]}),
        encoding="utf-8",
    )
    v2_root = tmp_path / "v2"
    student_root = tmp_path / "student"
    v2_root.mkdir()
    student_root.mkdir()
    (v2_root / "track.json").write_text(
        json.dumps(
            {
                "durationSeconds": 4,
                "barStartsSeconds": [0],
                "segments": [{"start": 0, "end": 4, "label": "N.C.", "confidence": 0.9}],
            }
        ),
        encoding="utf-8",
    )
    (student_root / "track.json").write_text(
        json.dumps({"durationSeconds": 4, "segments": [{"start": 0, "end": 4, "label": "C:maj", "confidence": 0.8}]}),
        encoding="utf-8",
    )
    report = run_hybrid_benchmark(
        {
            "tracks": [
                {
                    "id": "track",
                    "datasetId": "fixture",
                    "split": "test",
                    "referencePath": str(reference),
                }
            ]
        },
        v2_prediction_root=v2_root,
        student_prediction_root=student_root,
        output_root=tmp_path / "out",
    )
    assert report["engine"] == "hybrid"
    assert report["aggregate"]["trackCount"] == 1
    assert report["aggregate"]["majorMinorWeightedRecall"] == 1
    frozen = json.loads((tmp_path / "out/predictions/hybrid/track.json").read_text(encoding="utf-8"))
    assert frozen["segments"][0]["productLabel"] == "C"


def test_prediction_benchmark_rescores_frozen_predictions_enharmonically(tmp_path: Path) -> None:
    reference = tmp_path / "reference.json"
    reference.write_text(
        json.dumps({"segments": [{"start": 0, "end": 4, "label": "Eb:maj"}]}),
        encoding="utf-8",
    )
    prediction_root = tmp_path / "predictions"
    prediction_root.mkdir()
    (prediction_root / "track.json").write_text(
        json.dumps({"durationSeconds": 4, "segments": [{"start": 0, "end": 4, "label": "D#:maj"}]}),
        encoding="utf-8",
    )

    report = run_prediction_benchmark(
        {
            "tracks": [
                {
                    "id": "track",
                    "datasetId": "fixture",
                    "split": "test",
                    "referencePath": str(reference),
                }
            ]
        },
        prediction_root=prediction_root,
        engine="student-ensemble",
    )

    assert report["rescoredFromFrozenPredictions"] is True
    assert report["aggregate"]["majorMinorWeightedRecall"] == 1
    assert report["aggregate"]["detailedWeightedRecall"] == 1


def test_prediction_benchmark_aggregates_domain_routes_and_extended_diagnostics(
    tmp_path: Path,
) -> None:
    prediction_root = tmp_path / "predictions"
    prediction_root.mkdir()
    tracks = []
    cases = [
        ("sparse", "C:maj", "C:maj", 0.9, "conservative-sparse", 0.8),
        ("mixture", "D:maj", "G:maj", 0.4, "expanded-mixture", 0.2),
    ]
    for identifier, truth, predicted, confidence, route, gate_probability in cases:
        reference = tmp_path / f"{identifier}-reference.json"
        reference.write_text(
            json.dumps({"segments": [{"start": 0, "end": 2, "label": truth}]}),
            encoding="utf-8",
        )
        (prediction_root / f"{identifier}.json").write_text(
            json.dumps(
                {
                    "engine": "chord-student-v1",
                    "durationSeconds": 2,
                    "domainRoute": route,
                    "domainGateProbability": gate_probability,
                    "segments": [
                        {
                            "start": 0,
                            "end": 2,
                            "label": predicted,
                            "confidence": confidence,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        tracks.append(
            {
                "id": identifier,
                "datasetId": "fixture",
                "split": "test",
                "referencePath": str(reference),
            }
        )

    report = run_prediction_benchmark(
        {"tracks": tracks},
        prediction_root=prediction_root,
        engine="student-v8",
    )

    aggregate = report["aggregate"]
    assert aggregate["vocabularyCoverage"]["exactDetailedWeightedRecallCeiling"] == 1
    assert aggregate["sequenceEdits"]["counts"]["substitutions"] == 1
    assert aggregate["confusion"]["root"]["totalDurationSeconds"] == 4
    confidence_curve = {
        point["minimumConfidence"]: point for point in aggregate["confidenceCoverage"]["curve"]
    }
    assert confidence_curve[0.5]["coverage"] == pytest.approx(0.5)
    assert confidence_curve[0.5]["detailedPrecision"] == 1
    assert aggregate["domainRoutes"]["availableTrackCount"] == 2
    assert aggregate["domainRoutes"]["meanDomainGateProbability"] == pytest.approx(0.5)
    assert aggregate["domainRoutes"]["routes"]["conservative-sparse"][
        "detailedWeightedRecall"
    ] == 1
    assert aggregate["domainRoutes"]["routes"]["expanded-mixture"][
        "detailedWeightedRecall"
    ] == 0
    assert report["strata"]["fixture"]["domainRoutes"]["availableTrackCount"] == 2


def test_cli_scores_json_segments(tmp_path: Path) -> None:
    reference = tmp_path / "reference.json"
    prediction = tmp_path / "prediction.json"
    output = tmp_path / "report.json"
    reference.write_text(json.dumps({"id": "truth", "segments": [{"start": 0, "end": 1, "label": "D"}]}))
    prediction.write_text(json.dumps({"id": "model", "segments": [{"start": 0, "end": 1, "label": "D"}]}))
    result = subprocess.run(
        [sys.executable, "scripts/chord_reader.py", "score", str(reference), str(prediction), "--output", str(output)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["rootWeightedRecall"] == 1
    assert report["referenceId"] == "truth"
    assert report["predictionId"] == "model"


def test_btc_registry_is_pinned_and_snapshot_verification_rejects_changes(tmp_path: Path) -> None:
    registry = load_model_registry()
    assert len(registry["upstream"]["revision"]) == 40
    fixture = tmp_path / "artifact.bin"
    fixture.write_bytes(b"trusted")
    import hashlib

    local_registry = {"files": {"artifact.bin": hashlib.sha256(b"trusted").hexdigest()}}
    verify_model_snapshot(tmp_path, local_registry)
    fixture.write_bytes(b"changed")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_model_snapshot(tmp_path, local_registry)


def test_aam_adapter_collapses_beat_labels_to_chord_segments(tmp_path: Path) -> None:
    path = tmp_path / "0001_beatinfo.arff"
    path.write_text(
        "@RELATION test\n@DATA\n0.0,1,1,'Fmaj'\n0.5,1,2,'Fmaj'\n1.0,1,3,'C7'\n1.5,1,4,'C7'\n",
        encoding="utf-8",
    )
    segments, metadata = parse_aam_beatinfo(path, end_seconds=2.0)
    assert segments == [
        {"start": 0.0, "end": 1.0, "label": "F:maj"},
        {"start": 1.0, "end": 2.0, "label": "C:7"},
    ]
    assert metadata["tempo"] == 120


def test_aam_adapter_reads_official_files_without_data_marker(tmp_path: Path) -> None:
    path = tmp_path / "0001_beatinfo.arff"
    path.write_text(
        "@RELATION official\n@ATTRIBUTE time NUMERIC\n@ATTRIBUTE bar NUMERIC\n"
        "@ATTRIBUTE beat NUMERIC\n@ATTRIBUTE chord STRING\n\n"
        "0.0,1,1,'Fmaj'\n0.5,1,2,'Fmaj'\n1.0,1,3,'C7'\n",
        encoding="utf-8",
    )
    segments, metadata = parse_aam_beatinfo(path, end_seconds=1.5)
    assert segments == [
        {"start": 0.0, "end": 1.0, "label": "F:maj"},
        {"start": 1.0, "end": 1.5, "label": "C:7"},
    ]
    assert metadata["tempo"] == 120


def test_guitarset_adapter_reads_chord_namespace(tmp_path: Path) -> None:
    path = tmp_path / "track_comp.jams"
    path.write_text(
        json.dumps(
            {
                "file_metadata": {"duration": 2, "title": "track_comp"},
                "sandbox": {"tempo": 100, "time_signature": "4/4"},
                "annotations": [
                    {
                        "namespace": "chord",
                        "data": [
                            {"time": 0, "duration": 1, "value": "G:maj"},
                            {"time": 1, "duration": 1, "value": "D:7"},
                        ],
                    },
                    {
                        "namespace": "chord",
                        "annotation_metadata": {
                            "annotation_rules": (
                                "Chord sheet-informed symbolic chord transcription based on "
                                "the included separate string note transcriptions with the "
                                "chord segmentation and root derived from sheet music."
                            ),
                            "data_source": "Semi-automatic chord transcription with manual verification",
                        },
                        "data": [
                            {"time": 0, "duration": 1, "value": "G:maj/1"},
                            {"time": 1, "duration": 1, "value": "D:maj/5"},
                        ],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    segments, metadata = parse_guitarset_jams(path)
    assert segments[-1] == {"start": 1.0, "end": 2.0, "label": "D:7"}
    assert metadata["tempo"] == 100
    assert metadata["performanceRole"] == "comp"
    assert metadata["performedSegments"][-1]["label"] == "D:maj/5"


def test_winterreise_adapter_reads_audio_aligned_chords(tmp_path: Path) -> None:
    path = tmp_path / "song.csv"
    path.write_text(
        "start;end;shorthand;extended;majmin;majmin_inv\n"
        '0.24;1.5;"C:min";"C:(b3,5)";"C:min";"C:min"\n'
        '1.5;2.0;"G:7/B";"G:(3,5,b7)/B";"G:maj";"G:maj/B"\n',
        encoding="utf-8",
    )
    assert parse_winterreise_chords(path) == [
        {"start": 0.24, "end": 1.5, "label": "C:min"},
        {"start": 1.5, "end": 2.0, "label": "G:7/B"},
    ]


def test_student_vocabulary_preserves_product_qualities_and_transposes() -> None:
    assert STUDENT_CLASSES == 49
    assert student_label(student_index("Bb:maj7")) == "A#:maj"
    assert student_label(student_index("D:min7")) == "D:min7"
    assert student_label(transpose_student_index(student_index("G:7"), 2)) == "A:7"
    assert student_label(student_index("N")) == "N"


def test_idmt_parser_expands_changes_and_normalizes_dataset_notation(tmp_path: Path) -> None:
    path = tmp_path / "jazz_1_120BPM.csv"
    path.write_text(
        "8.0,1.1:Bb7913/Ab\n8.5,1.2\n9.0,1.3:Emin75b\n9.5,1.4:NC\n1,1\n4,4\n4,4\n",
        encoding="utf-8",
    )
    segments, metadata = parse_idmt_chords(path, end_seconds=10.0)
    assert segments == [
        {"start": 8.0, "end": 9.0, "label": "Bb:13/Ab"},
        {"start": 9.0, "end": 9.5, "label": "E:hdim7"},
        {"start": 9.5, "end": 10.0, "label": "N"},
    ]
    assert metadata["tempo"] == 120.0
    assert metadata["meter"] == "4/4"
    assert metadata["barStartsSeconds"] == [8.0]
    assert metadata["gridStartSeconds"] == 8.0
    assert metadata["prefixExcludedSeconds"] == 8.0
    assert metadata["timingProvenance"]["barStartsSeconds"]["status"] == "explicit"


def test_student_frame_labels_use_time_aligned_reference() -> None:
    labels = frame_labels(
        [{"start": 0, "end": 0.2, "label": "C"}, {"start": 0.2, "end": 0.4, "label": "F:min"}],
        5,
    )
    assert [student_label(value) for value in labels] == ["C:maj", "C:maj", "F:min", "F:min", "N"]
    assert frame_label_mask(
        [{"start": 0.1, "end": 0.3, "label": "C"}, {"start": 0.4, "end": 0.5, "label": "N"}],
        6,
    ) == [False, True, True, False, True, False]


def test_feature_caches_merge_without_changing_splits() -> None:
    base = {
        "schemaVersion": "chord_feature_cache_v1",
        "sampleRate": 11025,
        "frameSeconds": 0.1,
        "featureCount": 13,
    }
    merged = merge_feature_caches(
        [
            {**base, "tracks": [{"id": "guitar", "datasetId": "guitarset", "split": "train"}]},
            {**base, "tracks": [{"id": "song", "datasetId": "winterreise", "split": "test"}]},
        ]
    )
    assert merged["datasets"] == ["guitarset", "winterreise"]
    assert merged["featureKind"] == "worker_chroma_v1"
    assert [(track["id"], track["split"]) for track in merged["tracks"]] == [
        ("guitar", "train"),
        ("song", "test"),
    ]


def test_feature_caches_reject_different_harmonic_front_ends() -> None:
    base = {
        "schemaVersion": "chord_feature_cache_v1",
        "sampleRate": 11025,
        "frameSeconds": 0.1,
        "tracks": [],
    }
    with pytest.raises(ValueError, match="contracts do not match"):
        merge_feature_caches(
            [
                {**base, "featureKind": "worker_chroma_v1", "featureCount": 13},
                {**base, "featureKind": "multiband_chroma_v2", "featureCount": 61},
            ]
        )


def test_feature_cache_composition_balancing_downweights_duplicate_renditions() -> None:
    cache = {
        "tracks": [
            {"id": "a-1", "datasetId": "set", "split": "train", "path": "/a"},
            {"id": "a-2", "datasetId": "set", "split": "train", "path": "/b"},
            {"id": "b-1", "datasetId": "set", "split": "train", "path": "/c"},
        ]
    }
    tracks = {
        "tracks": [
            {"id": "a-1", "compositionId": "a"},
            {"id": "a-2", "compositionId": "a"},
            {"id": "b-1", "compositionId": "b"},
        ]
    }

    balanced = composition_balance_feature_cache(cache, [tracks])

    assert balanced["compositionBalanced"] is True
    assert [item["trainingWeightOverride"] for item in balanced["tracks"]] == [0.5, 0.5, 1]


def test_root_guidance_preserves_base_conditional_quality_evidence() -> None:
    base = np.zeros((1, STUDENT_CLASSES), dtype=np.float32)
    guide = np.zeros((1, STUDENT_CLASSES), dtype=np.float32)
    g_major = student_index("G:maj")
    g_minor = student_index("G:min")
    base[0, g_major] = 2
    base[0, g_minor] = -1
    guide[0, g_major] = -2
    guide[0, g_minor] = 5

    guided = _root_guided_logits(base, guide, 0.3, np)

    assert guided[0, g_major] - guided[0, g_minor] == pytest.approx(3)
    assert guided[0, g_major] > base[0, g_major]


def test_quality_guidance_preserves_base_root_marginals() -> None:
    base = np.linspace(-3, 3, STUDENT_CLASSES, dtype=np.float32)[None]
    guide = np.linspace(2, -2, STUDENT_CLASSES, dtype=np.float32)[None]

    guided = _quality_guided_logits(base, guide, 0.4, np)

    for root in range(12):
        indices = [1 + quality * 12 + root for quality in range(4)]
        base_marginal = np.logaddexp.reduce(base[0, indices])
        guided_marginal = np.logaddexp.reduce(guided[0, indices])
        assert guided_marginal == pytest.approx(base_marginal, abs=1e-6)
    assert guided[0, 0] == base[0, 0]


def test_quality_guidance_validates_weight() -> None:
    logits = np.zeros((1, STUDENT_CLASSES), dtype=np.float32)

    with pytest.raises(ValueError, match="Quality-guide weight"):
        _quality_guided_logits(logits, logits, 1.1, np)


def test_quality_guidance_accepts_per_root_weights() -> None:
    base = np.linspace(-3, 3, STUDENT_CLASSES, dtype=np.float32)[None]
    guide = np.linspace(2, -2, STUDENT_CLASSES, dtype=np.float32)[None]
    weights = np.zeros((1, 12), dtype=np.float32)
    weights[:, 4] = 0.5

    guided = _quality_guided_logits(base, guide, weights, np)

    untouched = [1 + quality * 12 + 3 for quality in range(4)]
    changed = [1 + quality * 12 + 4 for quality in range(4)]
    assert guided[0, untouched] == pytest.approx(base[0, untouched])
    assert not np.allclose(guided[0, changed], base[0, changed])


def test_mode_guidance_preserves_root_and_extension_evidence() -> None:
    base = np.linspace(-2, 2, STUDENT_CLASSES, dtype=np.float32)[None]
    guide = np.linspace(3, -3, STUDENT_CLASSES, dtype=np.float32)[None]

    guided = _mode_guided_logits(base, guide, 0.6, np)

    for root in range(12):
        indices = [1 + quality * 12 + root for quality in range(4)]
        assert np.logaddexp.reduce(guided[0, indices]) == pytest.approx(
            np.logaddexp.reduce(base[0, indices]), abs=1e-6
        )
        assert guided[0, indices[0]] - guided[0, indices[2]] == pytest.approx(
            base[0, indices[0]] - base[0, indices[2]], abs=1e-6
        )
        assert guided[0, indices[1]] - guided[0, indices[3]] == pytest.approx(
            base[0, indices[1]] - base[0, indices[3]], abs=1e-6
        )
    assert guided[0, 0] == base[0, 0]


def test_extension_guidance_preserves_root_and_mode_evidence() -> None:
    base = np.linspace(-2, 2, STUDENT_CLASSES, dtype=np.float32)[None]
    guide = np.linspace(3, -3, STUDENT_CLASSES, dtype=np.float32)[None]
    weights = np.ones((1, 12, 2), dtype=np.float32) * 0.6

    guided = _extension_guided_logits(base, guide, weights, np)

    for root in range(12):
        major = [1 + root, 1 + 2 * 12 + root]
        minor = [1 + 1 * 12 + root, 1 + 3 * 12 + root]
        assert np.logaddexp.reduce(guided[0, major]) == pytest.approx(
            np.logaddexp.reduce(base[0, major]), abs=1e-6
        )
        assert np.logaddexp.reduce(guided[0, minor]) == pytest.approx(
            np.logaddexp.reduce(base[0, minor]), abs=1e-6
        )
    assert guided[0, 0] == base[0, 0]


def test_factorized_product_path_is_invariant_to_extension_guidance() -> None:
    rng = np.random.default_rng(20260820)
    base = rng.normal(size=(12, STUDENT_CLASSES)).astype(np.float32)
    guide = rng.normal(size=(12, STUDENT_CLASSES)).astype(np.float32)
    weights = np.ones((12, 12, 2), dtype=np.float32) * 0.8

    guided = _extension_guided_logits(base, guide, weights, np)

    assert _product_logits(guided, np) == pytest.approx(_product_logits(base, np), abs=1e-6)
    assert [
        (value - 1) % 12 if value else -1 for value in _factorized_student_path(guided, np)
    ] == [(value - 1) % 12 if value else -1 for value in _factorized_student_path(base, np)]


def test_promotion_gate_requires_material_gain_and_runtime() -> None:
    def report(engine: str, major_minor: float, root: float, boundary: float) -> dict:
        aggregate = {
            "majorMinorWeightedRecall": major_minor,
            "rootWeightedRecall": root,
            "boundaryF1Macro": boundary,
            "elapsedSeconds": 10,
        }
        return {
            "schemaVersion": "chord_benchmark_report_v1",
            "engine": engine,
            "aggregate": aggregate,
            "strata": {"guitarset": aggregate},
            "peakResidentMemoryBytes": 400_000_000,
            "tracks": [{"audioDurationSeconds": 240}],
        }

    passing = evaluate_promotion(report("v2", 0.4, 0.45, 0.5), report("student", 0.49, 0.51, 0.49))
    failing = evaluate_promotion(report("v2", 0.4, 0.45, 0.5), report("btc", 0.44, 0.48, 0.52))
    assert passing["passed"] is True
    assert failing["passed"] is False


def test_travis_packet_is_blinded_deterministic_and_scores_roles(tmp_path: Path) -> None:
    tracks = [
        {
            "id": f"steel-{number}",
            "split": "steel_test",
            "title": f"Song {number}",
            "audioPath": f"/private/song-{number}.wav",
        }
        for number in range(10)
    ]
    manifest = {"tracks": tracks}
    reports = tmp_path / "reports"
    for role in ("baseline", "challenger"):
        rows = []
        for track in tracks:
            prediction = reports / role / "predictions" / f"{track['id']}.json"
            prediction.parent.mkdir(parents=True, exist_ok=True)
            prediction.write_text(
                json.dumps(
                    {
                        "engine": role,
                        "durationSeconds": 1,
                        "segments": [{"start": 0, "end": 1, "label": "C" if role == "baseline" else "G"}],
                    }
                ),
                encoding="utf-8",
            )
            rows.append({"id": track["id"], "predictionFile": f"predictions/{track['id']}.json"})
        (reports / role / "report.json").write_text(
            json.dumps({"engine": role, "tracks": rows}), encoding="utf-8"
        )
    packet_root = tmp_path / "packet"
    key_path = tmp_path / "sealed-key.json"
    packet, key = build_travis_packet(
        manifest,
        reports / "baseline/report.json",
        reports / "challenger/report.json",
        packet_root,
        key_path,
    )
    assert len(packet["items"]) == 10
    assert "engine" not in json.loads((packet_root / "predictions/01-A.json").read_text(encoding="utf-8"))
    assert {item["A"] for item in key["items"]} == {"baseline", "challenger"}
    for item in packet["items"]:
        item["review"] = {"preferred": "A", "aCorrections": 1, "bCorrections": 2}
    scored = score_travis_review(packet, key)
    assert len(scored["comparisons"]) == 10
    assert all(item["baselineCorrections"] in {1, 2} for item in scored["comparisons"])


def test_travis_packet_rejects_answer_key_inside_packet(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside"):
        build_travis_packet({"tracks": []}, tmp_path / "a.json", tmp_path / "b.json", tmp_path, tmp_path / "key.json")


def test_tracked_student_model_matches_model_card_and_export() -> None:
    model = ROOT / "ui/models/chord-student-v1.onnx"
    card = json.loads((ROOT / "chord_reader/models/chord-student-v1.json").read_text(encoding="utf-8"))
    export = json.loads((ROOT / "chord_reader/models/chord-student-v1-export.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(model.read_bytes()).hexdigest()
    assert digest == card["model"]["sha256"] == export["sha256"]
    assert model.stat().st_size == card["model"]["bytes"] == export["bytes"]
    assert export["maximumAbsoluteError"] < 1e-4


@pytest.mark.skipif(shutil.which("node") is None or not (ROOT / "node_modules/onnxruntime-web").is_dir(), reason="Node ONNX runtime required")
def test_browser_runtime_executes_student_onnx_on_synthetic_c_major() -> None:
    script = """
      const fs=require('fs'),ort=require('onnxruntime-web'),ml=require('./ui/chord-reader-ml-worker.js');
      (async()=>{ort.env.wasm.numThreads=1;const sr=11025,ms=2000,s=new Float32Array(sr*2);
      for(let i=0;i<s.length;i++){const t=i/sr;s[i]=(Math.sin(2*Math.PI*261.626*t)+Math.sin(2*Math.PI*329.628*t)+Math.sin(2*Math.PI*391.995*t))/3;}
      const f=ml.spectralFeatures(s,sr,ms),session=await ort.InferenceSession.create(new Uint8Array(fs.readFileSync('ui/models/chord-student-v1.onnx')),{executionProviders:['wasm']});
      const r=await session.run({features:new ort.Tensor('float32',f.values,[1,f.frameCount,13])});
      const segments=ml.segmentsFromLogits(r.logits.data,f.frameCount,ms);console.log(JSON.stringify({dims:r.logits.dims,segments}));
      })().catch(e=>{console.error(e);process.exit(1)});
    """
    result = subprocess.run(["node", "-e", script], cwd=ROOT, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value["dims"] == [1, 20, 49]
    assert value["segments"][0]["symbol"] == "C"


@pytest.mark.skipif(shutil.which("node") is None, reason="Node required")
def test_browser_client_overlays_no_chord_without_forcing_bar_labels() -> None:
    script = """
      global.window={localStorage:{getItem:()=>null}};require('./ui/practice-analysis-client.js');
      const c=window.STEEL_RAG_ANALYSIS_CLIENT;
      const base={durationMs:6000,barStartsMs:[0,2000,4000],beatTimesMs:[0,500,1000,1500,2000,2500,3000,3500,4000,4500,5000,5500],chords:[{startMs:0,endMs:2000,symbol:'N.C.',confidence:.98},{startMs:2000,endMs:4000,symbol:'N.C.',confidence:.98}]};
      const ml={engine:'chord-student-v1',segments:[{startMs:0,endMs:1000,symbol:'E',confidence:.3},{startMs:1000,endMs:4080,symbol:'Em',confidence:.3},{startMs:4080,endMs:6000,symbol:'G7',confidence:.7}]};
      const result=c.mergeMlAnalysis(base,ml);console.log(JSON.stringify(result));
    """
    result = subprocess.run(["node", "-e", script], cwd=ROOT, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value["analysisVersion"] == 3
    assert value["chordReaderEngine"] == "hybrid-v1"
    assert [(item["bar"], item["symbol"], item["needsAttention"], item["sourceEngine"]) for item in value["chords"]] == [
        (1, "N.C.", False, "v2-no-chord"),
        (3, "Em", True, "student"),
        (3, "G7", True, "student"),
    ]


@pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("node") is None, reason="Node and FFmpeg required")
def test_v2_adapter_emits_benchmark_segments_for_licensed_fixture(tmp_path: Path) -> None:
    audio = ROOT / "ui/assets/song-practice/amazing-grace-2011-guide.mp3"
    rights = ROOT / "ui/assets/song-practice/amazing-grace-2011-guide.RIGHTS.md"
    output = tmp_path / "v2.json"
    assert audio.is_file() and "CC BY 3.0" in rights.read_text(encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "scripts/chord_reader.py",
            "predict-v2",
            str(audio),
            "--output",
            str(output),
            "--id",
            "amazing-grace-fixture",
            "--key",
            "G",
            "--mode",
            "major",
            "--meter",
            "3/4",
            "--tempo",
            "75",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    prediction = json.loads(output.read_text(encoding="utf-8"))
    assert prediction["schemaVersion"] == "chord_prediction_v1"
    assert prediction["engine"] == "play-along-v2"
    assert prediction["analysisVersion"] == 2
    assert prediction["id"] == "amazing-grace-fixture"
    assert prediction["segments"][0]["start"] == 0
    assert prediction["segments"][-1]["end"] == pytest.approx(prediction["durationSeconds"])
    assert prediction["key"] == "G"
    assert prediction["meter"] == "3/4"
