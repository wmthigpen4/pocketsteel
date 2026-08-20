"""Non-negotiable automated and Travis review promotion gates."""

from __future__ import annotations

from typing import Any, Mapping


MAJMIN_GAIN = 0.08
ROOT_GAIN = 0.05
STEEL_GAIN = 0.05
MAX_STRATUM_REGRESSION = 0.03
MAX_BOUNDARY_REGRESSION = 0.02
MAX_FOUR_MINUTE_SECONDS = 15.0
MAX_RESIDENT_MEMORY_BYTES = int(1.2 * 1024**3)


def _gate(name: str, passed: bool, actual: Any, required: str) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "actual": actual, "required": required}


def evaluate_promotion(
    baseline: Mapping[str, Any],
    challenger: Mapping[str, Any],
    *,
    require_steel: bool = False,
    travis_review: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    base = baseline["aggregate"]
    candidate = challenger["aggregate"]
    majmin_gain = float(candidate["majorMinorWeightedRecall"]) - float(base["majorMinorWeightedRecall"])
    root_gain = float(candidate["rootWeightedRecall"]) - float(base["rootWeightedRecall"])
    boundary_change = float(candidate["boundaryF1Macro"]) - float(base["boundaryF1Macro"])
    audio_seconds = sum(float(item.get("audioDurationSeconds") or 0) for item in challenger.get("tracks", []))
    projected_four_minutes = float(candidate["elapsedSeconds"]) / max(1e-12, audio_seconds) * 240
    gates = [
        _gate("pooled-major-minor-wcsr", majmin_gain >= MAJMIN_GAIN, majmin_gain, f">= +{MAJMIN_GAIN:.2f}"),
        _gate("pooled-root-wcsr", root_gain >= ROOT_GAIN, root_gain, f">= +{ROOT_GAIN:.2f}"),
        _gate(
            "boundary-f1",
            boundary_change >= -MAX_BOUNDARY_REGRESSION,
            boundary_change,
            f">= -{MAX_BOUNDARY_REGRESSION:.2f}",
        ),
        _gate(
            "four-minute-runtime",
            projected_four_minutes <= MAX_FOUR_MINUTE_SECONDS,
            projected_four_minutes,
            f"<= {MAX_FOUR_MINUTE_SECONDS:.1f} seconds",
        ),
        _gate(
            "resident-memory",
            int(challenger.get("peakResidentMemoryBytes", 0)) <= MAX_RESIDENT_MEMORY_BYTES,
            int(challenger.get("peakResidentMemoryBytes", 0)),
            f"<= {MAX_RESIDENT_MEMORY_BYTES} bytes",
        ),
    ]
    shared = sorted(set(baseline.get("strata", {})) & set(challenger.get("strata", {})))
    regressions = {
        name: float(challenger["strata"][name]["majorMinorWeightedRecall"])
        - float(baseline["strata"][name]["majorMinorWeightedRecall"])
        for name in shared
    }
    gates.append(
        _gate(
            "no-stratum-regression",
            all(value >= -MAX_STRATUM_REGRESSION for value in regressions.values()),
            regressions,
            f"every stratum >= -{MAX_STRATUM_REGRESSION:.2f}",
        )
    )
    if require_steel:
        steel_base = baseline.get("strata", {}).get("sgf_steel_reference")
        steel_candidate = challenger.get("strata", {}).get("sgf_steel_reference")
        steel_gain = None
        if steel_base and steel_candidate:
            steel_gain = float(steel_candidate["majorMinorWeightedRecall"]) - float(
                steel_base["majorMinorWeightedRecall"]
            )
        gates.append(_gate("steel-wcsr", steel_gain is not None and steel_gain >= STEEL_GAIN, steel_gain, ">= +0.05"))
    if travis_review is not None:
        comparisons = list(travis_review.get("comparisons", []))
        preferred = sum(item.get("preferred") == "challenger" for item in comparisons)
        baseline_corrections = sum(int(item.get("baselineCorrections", 0)) for item in comparisons)
        challenger_corrections = sum(int(item.get("challengerCorrections", 0)) for item in comparisons)
        correction_reduction = 1 - challenger_corrections / max(1, baseline_corrections)
        gates.extend(
            [
                _gate("travis-preference", len(comparisons) == 10 and preferred >= 7, preferred, ">= 7 of 10"),
                _gate("travis-corrections", correction_reduction >= 0.3, correction_reduction, ">= 30% fewer"),
            ]
        )
    return {
        "schemaVersion": "chord_promotion_report_v1",
        "passed": all(item["passed"] for item in gates),
        "baselineEngine": baseline.get("engine"),
        "challengerEngine": challenger.get("engine"),
        "gates": gates,
    }
