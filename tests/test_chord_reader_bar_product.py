from __future__ import annotations

import pytest

from steel_guitar_rag.chord_reader.bar_product import (
    aggregate_bar_product_confidence,
    score_bar_product_confidence,
)


def _reference(segments: list[dict], *, duration: float = 8.0, **metadata: object) -> dict:
    return {"durationSeconds": duration, "segments": segments, **metadata}


def _prediction(segments: list[dict], *, duration: float = 8.0, **metadata: object) -> dict:
    return {"durationSeconds": duration, "segments": segments, **metadata}


def test_bar_products_use_enharmonic_product_labels_and_confidence_fallback() -> None:
    reference = _reference(
        [
            {"start": 0, "end": 2, "label": "C:maj"},
            {"start": 2, "end": 4, "label": "D:min"},
            {"start": 4, "end": 6, "label": "G:7"},
            {"start": 6, "end": 8, "label": "F:maj"},
        ],
        barStartsSeconds=[0, 2, 4, 6],
    )
    prediction = _prediction(
        [
            {
                "start": 0,
                "end": 2,
                "label": "F#:dim",
                "productLabel": "B#",
                "productConfidence": 0.99,
                "confidence": 0.01,
            },
            {
                "start": 2,
                "end": 4,
                "label": "D:dim",
                "productLabel": "Dm",
                "confidence": 0.80,
            },
            {"start": 4, "end": 6, "label": "A:maj", "confidence": 0.90},
            {"start": 6, "end": 8, "label": "F:maj", "confidence": 0.40},
        ]
    )

    result = score_bar_product_confidence(
        reference,
        prediction,
        confidence_thresholds=[0.0, 0.50, 0.85, 0.95, 1.0],
    )
    curve = {point["minimumConfidence"]: point for point in result["curve"]}

    assert result["available"] is True
    assert result["grid"]["provenance"] == "explicit-bar-starts"
    assert result["eligibleBarCount"] == 4
    assert result["bars"][0]["predictionProduct"] == "C"
    assert result["bars"][0]["correct"] is True
    assert result["bars"][0]["productConfidence"] == 0.99
    assert result["bars"][1]["predictionProduct"] == "Dm"
    assert result["bars"][1]["productConfidence"] == 0.80
    assert curve[0.50] == {
        "minimumConfidence": 0.50,
        "eligibleBarCount": 4,
        "acceptedBarCount": 3,
        "correctBarCount": 2,
        "barPrecision": pytest.approx(2 / 3),
        "barCoverage": 0.75,
        "hasSupport": True,
    }
    assert curve[0.85]["acceptedBarCount"] == 2
    assert curve[0.85]["correctBarCount"] == 1
    assert curve[0.85]["barPrecision"] == 0.5
    assert curve[0.85]["barCoverage"] == 0.5
    assert curve[0.95]["barPrecision"] == 1.0
    assert curve[0.95]["barCoverage"] == 0.25


def test_half_bar_reference_mix_is_excluded_and_zero_support_is_not_perfect() -> None:
    reference = _reference(
        [
            {"start": 0, "end": 1, "label": "C:maj"},
            {"start": 1, "end": 2, "label": "G:maj"},
        ],
        duration=2,
        barStartsSeconds=[0],
    )
    prediction = _prediction(
        [{"start": 0, "end": 2, "label": "C:maj", "confidence": 1.0}],
        duration=2,
    )

    result = score_bar_product_confidence(
        reference,
        prediction,
        confidence_thresholds=[0.0, 0.98],
    )

    assert result["totalBarCount"] == 1
    assert result["eligibleBarCount"] == 0
    assert result["excludedMixedBarCount"] == 1
    assert result["excludedUncoveredBarCount"] == 0
    assert result["curve"][1] == {
        "minimumConfidence": 0.98,
        "eligibleBarCount": 0,
        "acceptedBarCount": 0,
        "correctBarCount": 0,
        "barPrecision": None,
        "barCoverage": 0.0,
        "hasSupport": False,
    }


def test_prediction_must_cover_bar_and_have_one_dominant_product() -> None:
    reference = _reference(
        [
            {"start": 0, "end": 2, "label": "C:maj"},
            {"start": 2, "end": 4, "label": "D:maj"},
        ],
        duration=4,
        barStartsSeconds=[0, 2],
    )
    prediction = _prediction(
        [
            {"start": 0, "end": 1.4, "label": "C:maj", "confidence": 1.0},
            {"start": 2, "end": 3, "label": "D:maj", "confidence": 1.0},
            {"start": 3, "end": 4, "label": "A:maj", "confidence": 1.0},
        ],
        duration=4,
    )

    result = score_bar_product_confidence(
        reference,
        prediction,
        confidence_thresholds=[0.0],
    )

    assert result["eligibleBarCount"] == 2
    assert result["predictionUncoveredBarCount"] == 1
    assert result["predictionMixedBarCount"] == 1
    assert result["scorablePredictionBarCount"] == 0
    assert result["curve"][0]["barPrecision"] is None
    assert result["curve"][0]["hasSupport"] is False


def test_infers_deterministic_four_four_bar_grid_from_quarter_note_tempo() -> None:
    reference = _reference(
        [{"start": 0, "end": 8, "label": "Bb:maj"}],
        tempo=120,
        meter="4/4",
    )
    prediction = _prediction(
        [{"start": 0, "end": 8, "label": "A#:maj", "confidence": 0.99}],
    )

    result = score_bar_product_confidence(
        reference,
        prediction,
        confidence_thresholds=[0.98],
    )

    assert result["grid"] == {
        "available": True,
        "provenance": "inferred-tempo-meter",
        "source": "tempo-meter",
        "barStartsSeconds": [0.0, 2.0, 4.0, 6.0],
        "barCount": 4,
        "durationSeconds": 8.0,
        "tempo": 120.0,
        "meter": "4/4",
        "barDurationSeconds": 2.0,
        "tempoUnit": "quarter-note-bpm",
        "tempoSource": "reference",
        "meterSource": "reference",
    }
    assert result["eligibleBarCount"] == 4
    assert result["curve"][0]["acceptedBarCount"] == 4
    assert result["curve"][0]["correctBarCount"] == 4
    assert result["curve"][0]["barPrecision"] == 1.0
    assert result["curve"][0]["barCoverage"] == 1.0


def test_missing_bar_grid_is_explicitly_unavailable() -> None:
    reference = _reference([{"start": 0, "end": 2, "label": "C:maj"}], duration=2)
    prediction = _prediction(
        [{"start": 0, "end": 2, "label": "C:maj", "confidence": 1.0}],
        duration=2,
        # A challenger is not allowed to define the grid used to score itself.
        barStartsSeconds=[0],
        tempo=120,
        meter="4/4",
    )

    result = score_bar_product_confidence(reference, prediction)

    assert result["available"] is False
    assert result["grid"]["provenance"] == "unavailable"
    assert "barStartsSeconds" in result["grid"]["reason"]
    assert result["curve"] == []


@pytest.mark.parametrize("starts", ([1.0], [0.0, 1.0, 0.5], [0.0, 3.0]))
def test_invalid_explicit_reference_bar_grid_is_rejected(starts: list[float]) -> None:
    reference = _reference(
        [{"start": 0, "end": 2, "label": "C:maj"}],
        duration=2,
        barStartsSeconds=starts,
    )
    prediction = _prediction(
        [{"start": 0, "end": 2, "label": "C:maj", "confidence": 1.0}],
        duration=2,
    )

    with pytest.raises(ValueError, match="barStartsSeconds"):
        score_bar_product_confidence(reference, prediction)


def test_missing_winning_product_confidence_cannot_create_precision_support() -> None:
    reference = _reference(
        [{"start": 0, "end": 2, "label": "C:maj"}],
        duration=2,
        barStartsSeconds=[0],
    )
    prediction = _prediction(
        [{"start": 0, "end": 2, "label": "C:maj"}],
        duration=2,
    )

    result = score_bar_product_confidence(
        reference,
        prediction,
        confidence_thresholds=[0.0, 0.98],
    )

    assert result["eligibleBarCount"] == 1
    assert result["confidenceMissingBarCount"] == 1
    assert result["scorablePredictionBarCount"] == 0
    assert all(point["barPrecision"] is None for point in result["curve"])
    assert all(point["hasSupport"] is False for point in result["curve"])


def test_aggregate_sums_bar_counts_and_keeps_zero_support_null() -> None:
    reference = _reference(
        [{"start": 0, "end": 2, "label": "C:maj"}],
        duration=2,
        barStartsSeconds=[0],
    )
    correct = score_bar_product_confidence(
        reference,
        _prediction(
            [{"start": 0, "end": 2, "label": "C:maj", "confidence": 0.90}],
            duration=2,
        ),
        confidence_thresholds=[0.0, 0.95],
    )
    wrong = score_bar_product_confidence(
        reference,
        _prediction(
            [{"start": 0, "end": 2, "label": "G:maj", "confidence": 0.90}],
            duration=2,
        ),
        confidence_thresholds=[0.0, 0.95],
    )
    unavailable = score_bar_product_confidence(
        _reference([{"start": 0, "end": 2, "label": "C:maj"}], duration=2),
        _prediction(
            [{"start": 0, "end": 2, "label": "C:maj", "confidence": 1.0}],
            duration=2,
        ),
        confidence_thresholds=[0.0, 0.95],
    )

    aggregate = aggregate_bar_product_confidence([correct, wrong, unavailable])
    curve = {point["minimumConfidence"]: point for point in aggregate["curve"]}

    assert aggregate["trackCount"] == 3
    assert aggregate["availableTrackCount"] == 2
    assert aggregate["unavailableTrackCount"] == 1
    assert aggregate["eligibleBarCount"] == 2
    assert aggregate["gridProvenanceTrackCounts"] == {
        "explicit-bar-starts": 2,
        "unavailable": 1,
    }
    assert curve[0.0]["acceptedBarCount"] == 2
    assert curve[0.0]["correctBarCount"] == 1
    assert curve[0.0]["barPrecision"] == 0.5
    assert curve[0.0]["barCoverage"] == 1.0
    assert curve[0.95]["acceptedBarCount"] == 0
    assert curve[0.95]["barPrecision"] is None
    assert curve[0.95]["barCoverage"] == 0.0
    assert curve[0.95]["hasSupport"] is False
