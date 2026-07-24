from __future__ import annotations

import pytest

from steel_guitar_rag.amazing_tablature_score_sequence import (
    GROUP_END_TOKEN,
    MIN_PITCH,
    PITCH_TOKEN_OFFSET,
    ScoreSequenceTrainingError,
    collapse_ctc_path,
    decode_pitch_tokens,
    encode_pitch_groups,
    grouped_development_split,
    sequence_metrics,
)


def test_pitch_group_tokens_round_trip_chords_repeats_and_unisons() -> None:
    groups = [[60], [60], [64, 64, 67], [62]]
    encoded = encode_pitch_groups(groups)

    decoded, well_formed = decode_pitch_tokens(encoded)

    assert decoded == groups
    assert well_formed is True
    assert encoded.count(GROUP_END_TOKEN) == 4


def test_ctc_collapse_preserves_repeat_separated_by_blank_or_group() -> None:
    c4 = PITCH_TOKEN_OFFSET + 60 - MIN_PITCH
    raw_path = [0, c4, c4, 0, c4, GROUP_END_TOKEN, GROUP_END_TOKEN, 0]

    assert collapse_ctc_path(raw_path) == [c4, c4, GROUP_END_TOKEN]


def test_decode_rejects_incomplete_or_blank_prediction() -> None:
    c4 = PITCH_TOKEN_OFFSET + 60 - MIN_PITCH

    groups, complete = decode_pitch_tokens([c4])
    blank_groups, blank_complete = decode_pitch_tokens([])

    assert groups == [[60]]
    assert complete is False
    assert blank_groups == []
    assert blank_complete is False


def test_encode_rejects_empty_and_out_of_vocabulary_groups() -> None:
    with pytest.raises(ScoreSequenceTrainingError):
        encode_pitch_groups([])
    with pytest.raises(ScoreSequenceTrainingError):
        encode_pitch_groups([[20]])


def test_sequence_metrics_penalize_missing_attacks_and_blank_output() -> None:
    metrics = sequence_metrics(
        [[[60], [62]], [[64, 67]]],
        [[[60]], []],
        well_formed=[True, False],
    )

    assert metrics["sequenceExactLineCount"] == 0
    assert metrics["attackCountExactLineCount"] == 0
    assert metrics["exactAttackGroupCount"] == 1
    assert metrics["wellFormedLineCount"] == 1
    assert metrics["blankLineCount"] == 1
    assert metrics["tokenErrorRate"] > 0


def test_grouped_development_split_keeps_content_units_together() -> None:
    cases = [
        {"caseId": "a1", "contentUnitId": "a"},
        {"caseId": "a2", "contentUnitId": "a"},
        {"caseId": "b1", "contentUnitId": "b"},
        {"caseId": "c1", "contentUnitId": "c"},
        {"caseId": "d1", "contentUnitId": "d"},
    ]

    training, calibration = grouped_development_split(cases)

    assert set(training).isdisjoint(calibration)
    assert set(training) | set(calibration) == {"a1", "a2", "b1", "c1", "d1"}
    assert ({"a1", "a2"} <= set(training)) or ({"a1", "a2"} <= set(calibration))
    assert grouped_development_split(cases) == (training, calibration)
