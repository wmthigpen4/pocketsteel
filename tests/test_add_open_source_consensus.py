from __future__ import annotations

import numpy as np

from scripts.add_open_source_consensus import build_consensus
from steel_guitar_rag.chord_reader.btc import probability_viterbi_products


def test_probability_viterbi_products_suppresses_one_frame_btc_blip() -> None:
    chord_map = {0: "C:maj", 1: "G:maj"}
    raw_indices = [0, 0, 1, 0, 0, 1, 1, 1]
    probabilities = np.asarray(
        [
            [0.95, 0.05],
            [0.90, 0.10],
            [0.45, 0.55],
            [0.88, 0.12],
            [0.80, 0.20],
            [0.20, 0.80],
            [0.10, 0.90],
            [0.05, 0.95],
        ]
    )

    decoded, confidence = probability_viterbi_products(
        np,
        probabilities,
        chord_map,
        raw_indices,
    )

    assert decoded[:5] == ["C"] * 5
    assert decoded[5:] == ["G"] * 3
    assert len(confidence) == len(decoded)
    assert all(0 < value <= 1 for value in confidence)


def test_three_system_consensus_prioritizes_all_disagree_then_our_outlier() -> None:
    ours = [
        {"start": 0, "end": 1, "productLabel": "C"},
        {"start": 1, "end": 2, "productLabel": "D"},
        {"start": 2, "end": 3, "productLabel": "F"},
        {"start": 3, "end": 4, "productLabel": "G"},
    ]
    chordify = [
        {"start": 0, "end": 1, "productLabel": "C"},
        {"start": 1, "end": 2, "productLabel": "G"},
        {"start": 2, "end": 3, "productLabel": "G"},
        {"start": 3, "end": 4, "productLabel": "G"},
    ]
    btc = [
        {"start": 0, "end": 1, "productLabel": "C"},
        {"start": 1, "end": 2, "productLabel": "A"},
        {"start": 2, "end": 3, "productLabel": "G"},
        {"start": 3, "end": 4, "productLabel": "D"},
    ]

    result = build_consensus(ours, chordify, btc)

    assert result["coveredSeconds"] == 4
    assert result["allAgreeFraction"] == 0.25
    assert result["ourSupportedFraction"] == 0.5
    assert result["priorityReviewSeconds"] == 2
    assert result["chordifyDisagreementSeconds"] == 2
    assert result["btcSupportsOurFraction"] == 0
    assert result["btcSupportsChordifyFraction"] == 0.5
    assert result["btcSupportsNeitherFraction"] == 0.5
    assert [(row["ourChord"], row["chordifyChord"]) for row in result["pairVotes"]] == [("D", "G"), ("F", "G")]
    assert [row["category"] for row in result["reviewWindows"]] == [
        "all_disagree",
        "our_engine_outlier",
        "btc_outlier",
    ]
    assert result["reviewWindows"][1]["ourChord"] == "F"
    assert result["reviewWindows"][1]["chordifyChord"] == result["reviewWindows"][1]["btcChord"] == "G"


def test_consensus_normalizes_enharmonic_and_extended_labels() -> None:
    ours = [{"start": 0, "end": 2, "label": "G#maj7"}]
    chordify = [{"start": 0, "end": 2, "productLabel": "Ab"}]
    btc = [{"start": 0, "end": 2, "label": "G#:7"}]

    result = build_consensus(ours, chordify, btc)

    assert result["allAgreeFraction"] == 1
    assert result["reviewWindows"] == []
