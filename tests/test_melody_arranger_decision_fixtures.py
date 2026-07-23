"""Reviewed fixtures for arranger blocking and lever-density decisions."""

from __future__ import annotations

import pytest

import pocketsteel.melody_arranger as melody_arranger
from pocketsteel.e9_copedents import EMMONS_E9
from pocketsteel.melody_arranger import (
    MelodyInput,
    PositionCandidate,
    _learned_start_penalty,
    _runtime_learned_penalty,
    _transition_between,
    choose_mixed_path,
    single_note_candidates,
)
from pocketsteel.melody_ranker import FEATURE_NAMES, score_candidate
from pocketsteel.melody_ranker_adapter import runtime_candidate_feature_record
from pocketsteel.tab_engine import TabNote


def _open_grip(fret: int, strings: tuple[int, ...], top_pitch: int) -> PositionCandidate:
    return PositionCandidate(
        fret=fret,
        notes=tuple(TabNote(string, fret) for string in strings),
        top_pitch=top_pitch,
        controls=(),
        family="reviewed_fixture",
        note_names=tuple("" for _string in strings),
        intervals=tuple("" for _string in strings),
        pattern_family="reviewed blocking fixture",
        canonical_grip=strings,
    )


def _repeated_g_inputs(count: int) -> list[MelodyInput]:
    return [
        MelodyInput(
            "G4",
            "G",
            1,
            7,
            forced_pitch=67,
            duration_beats=1,
            measure=1,
            beat=index + 1,
            chord="G",
        )
        for index in range(count)
    ]


def _lever_entry_count(path: list[PositionCandidate]) -> int:
    entries = 0
    previous: frozenset[str] = frozenset()
    for candidate in path:
        current = frozenset(set(candidate.controls) & {"E", "F"})
        if current and current != previous:
            entries += 1
        previous = current
    return entries


def test_deterministic_fallback_applies_no_unapproved_chord_weight() -> None:
    single = _open_grip(3, (4,), 67)
    triad = _open_grip(3, (4, 5, 6), 67)

    single_penalty = _learned_start_penalty(single, "chord_arrival", 3, "chord_melody")
    triad_penalty = _learned_start_penalty(triad, "chord_arrival", 3, "chord_melody")
    auto_penalty = _learned_start_penalty(triad, "chord_arrival", 3, "auto")

    assert single_penalty == triad_penalty == auto_penalty == 0


def test_deterministic_fallback_applies_no_unapproved_harmony_weight() -> None:
    single = _open_grip(3, (4,), 67)
    dyad = _open_grip(3, (4, 5), 67)
    triad = _open_grip(3, (4, 5, 6), 67)

    penalties = {
        len(candidate.notes): _learned_start_penalty(candidate, "sustained_note", 3, "harmonized")
        for candidate in (single, dyad, triad)
    }

    assert set(penalties.values()) == {0}


def test_runtime_learned_penalty_scores_the_full_shared_feature_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    previous = _open_grip(3, (4,), 67)
    current = _open_grip(5, (4,), 69)
    following = _open_grip(6, (4,), 70)
    weights = {name: (index + 1) / 100 for index, name in enumerate(FEATURE_NAMES)}
    monkeypatch.setattr(melody_arranger, "RANKER_ENABLED", True)
    monkeypatch.setattr(
        melody_arranger,
        "WEIGHTS_BY_STYLE",
        {"single_note_run": weights},
    )

    record = runtime_candidate_feature_record(
        previous,
        current,
        following,
        phrase_role="passing_tone",
        profile=EMMONS_E9,
        current_sustained_strings=(4,),
        following_sustained_strings=(4,),
    )
    penalty = _runtime_learned_penalty(
        previous,
        current,
        following,
        role="passing_tone",
        style_family="single_note_run",
        profile=EMMONS_E9,
    )

    assert penalty == round(score_candidate(record, weights) * 1000)


def test_learned_path_search_preserves_following_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _open_grip(3, (4,), 67)
    expensive_middle = _open_grip(10, (4,), 74)
    preferred_middle = _open_grip(5, (4,), 69)
    last = _open_grip(7, (4,), 71)
    monkeypatch.setattr(melody_arranger, "RANKER_ENABLED", True)
    monkeypatch.setattr(
        melody_arranger,
        "WEIGHTS_BY_STYLE",
        {"single_note_run": {name: 0.0 for name in FEATURE_NAMES}},
    )
    monkeypatch.setattr(
        melody_arranger,
        "_mixed_start_cost",
        lambda *_args, **_kwargs: (0,) * 16,
    )
    monkeypatch.setattr(
        melody_arranger,
        "_mixed_transition_cost",
        lambda *_args, **_kwargs: (0,) * 16,
    )
    monkeypatch.setattr(
        melody_arranger,
        "_runtime_learned_penalty",
        lambda _previous, current, _following, **_kwargs: current.fret,
    )

    path = choose_mixed_path(
        [[first], [expensive_middle, preferred_middle], [last]],
        inputs=_repeated_g_inputs(3),
        key="G",
        style_family="single_note_run",
    )

    assert [candidate.fret for candidate in path] == [3, 5, 7]


def test_blocking_fixture_full_grip_slide_sustains_every_attacked_string() -> None:
    source = _open_grip(3, (4, 5, 6), 67)
    target = _open_grip(5, (4, 5, 6), 69)

    transition = _transition_between("blocking", 1, source, target)

    assert transition is not None
    assert transition["scope"] == "full_grip"
    assert transition["sustainedStrings"] == [4, 5, 6]
    assert transition["releasedStrings"] == transition["repickedStrings"] == []
    assert transition["voiceActions"] == [
        {"string": 4, "action": "bar_slide"},
        {"string": 5, "action": "bar_slide"},
        {"string": 6, "action": "bar_slide"},
    ]
    assert all(word not in transition["label"] for word in ("block", "repick", "add string"))


def test_blocking_fixture_changed_grip_separates_block_repick_and_add() -> None:
    source = _open_grip(3, (4, 5, 6), 67)
    target = _open_grip(5, (4, 5, 7), 69)

    transition = _transition_between("blocking", 1, source, target)

    assert transition is not None
    assert transition["scope"] == "melody_voice"
    assert transition["sustainedStrings"] == [4]
    assert transition["releasedStrings"] == [5, 6]
    assert transition["repickedStrings"] == [5, 7]
    assert transition["voiceActions"] == [
        {"string": 4, "action": "bar_slide"},
        {"string": 5, "action": "release"},
        {"string": 6, "action": "release"},
        {"string": 5, "action": "repick"},
        {"string": 7, "action": "add"},
    ]
    assert "block strings 5, 6 before the slide" in transition["label"]
    assert "repick string 5 at the arrival" in transition["label"]
    assert "add string 7 at the arrival" in transition["label"]


def test_lever_density_fixture_avoids_unneeded_e_and_f_entries() -> None:
    candidates = single_note_candidates(_repeated_g_inputs(1)[0], 67)
    open_position = next(
        candidate
        for candidate in candidates
        if candidate.fret == 3 and candidate.top_string == 4 and not candidate.controls
    )
    e_lower = next(
        candidate
        for candidate in candidates
        if candidate.fret == 4 and candidate.top_string == 4 and candidate.controls == ("E",)
    )
    f_lever = next(
        candidate
        for candidate in candidates
        if candidate.fret == 2 and candidate.top_string == 4 and candidate.controls == ("F",)
    )

    path = choose_mixed_path(
        [[open_position, e_lower, f_lever] for _index in range(4)],
        inputs=_repeated_g_inputs(4),
        key="G",
    )

    assert [(candidate.fret, candidate.controls) for candidate in path] == [(3, ())] * 4
    assert _lever_entry_count(path) == 0


@pytest.mark.parametrize(
    ("controls", "fret"),
    [(('E',), 4), (('F',), 2)],
)
def test_lever_density_fixture_keeps_one_established_lever_span(
    controls: tuple[str, ...],
    fret: int,
) -> None:
    candidates = single_note_candidates(_repeated_g_inputs(1)[0], 67)
    open_position = next(
        candidate
        for candidate in candidates
        if candidate.fret == 3 and candidate.top_string == 4 and not candidate.controls
    )
    lever_position = next(
        candidate
        for candidate in candidates
        if candidate.fret == fret and candidate.top_string == 4 and candidate.controls == controls
    )

    path = choose_mixed_path(
        [
            [lever_position],
            [lever_position, open_position],
            [lever_position],
            [lever_position, open_position],
        ],
        inputs=_repeated_g_inputs(4),
        key="G",
    )

    assert [(candidate.fret, candidate.controls) for candidate in path[:3]] == [(fret, controls)] * 3
    assert _lever_entry_count(path) == 1
