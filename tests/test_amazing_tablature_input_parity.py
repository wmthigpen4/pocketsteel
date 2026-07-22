from __future__ import annotations

from pocketsteel.amazing_tablature_input_parity import (
    INPUT_MODALITIES,
    structured_input_parity_report,
)


def test_structured_input_parity_matrix_is_exact_and_content_free() -> None:
    report = structured_input_parity_report()

    assert report["modalities"] == list(INPUT_MODALITIES)
    assert report["fixtureCount"] == 8
    assert report["eventCountPerModality"] >= 39
    assert report["totalAdapterEvents"] == (
        report["eventCountPerModality"] * len(INPUT_MODALITIES)
    )
    assert report["parityPassed"] is True
    assert report["accuracyClaim"] == "none_adapter_equivalence_only"
    assert report["validationAccessed"] is False
    assert report["sealedTestAccessed"] is False
    assert len(report["reportDigest"]) == 64
    assert all(
        fixture["pitchParity"] and fixture["arrangementParity"]
        for fixture in report["fixtures"]
    )
