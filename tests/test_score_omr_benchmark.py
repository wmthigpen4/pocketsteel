from __future__ import annotations

from steel_guitar_rag.score_omr_benchmark import benchmark_score_omr


def _draft(pitches: list[int], *, flagged: list[str] | None = None) -> dict:
    return {
        "score": {
            "melody": [
                {
                    "id": f"n{index}",
                    "pitchValue": pitch,
                    "beat": index,
                    "durationBeats": 1,
                }
                for index, pitch in enumerate(pitches, start=1)
            ]
        },
        "review": {"flaggedEventIds": flagged or []},
    }


def test_benchmark_acceptance_gates_pass_for_exact_low_correction_cases() -> None:
    cases = [
        {
            "id": f"clean-{index}",
            "clean": True,
            "reference": _draft([60, 62, 64]),
            "candidate": _draft([60, 62, 64]),
            "corrections": 0,
            "manualEntrySeconds": 90,
            "correctionSeconds": 10,
        }
        for index in range(10)
    ]
    result = benchmark_score_omr(cases)
    assert result["passed"] is True
    assert result["metrics"]["exactPitchAccuracy"] == 1
    assert result["metrics"]["exactOnsetDurationAccuracy"] == 1
    assert result["metrics"]["medianCorrectionToManualTimeRatio"] < 1 / 3
    assert result["metrics"]["silentErrorCount"] == 0


def test_benchmark_detects_silent_error_and_attributes_failure_layer() -> None:
    result = benchmark_score_omr(
        [
            {
                "id": "bad-page",
                "clean": True,
                "reference": _draft([60, 62]),
                "candidate": _draft([60, 63]),
                "corrections": 3,
                "manualEntrySeconds": 30,
                "correctionSeconds": 20,
                "failureLayer": "omr",
            }
        ]
    )
    assert result["passed"] is False
    assert result["metrics"]["silentErrorCount"] == 1
    assert result["failuresByLayer"]["omr"] == 1
