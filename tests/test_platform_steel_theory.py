from __future__ import annotations

import json
from pathlib import Path

import pytest

from packages.steel_theory import (
    BASIC_GRIP_FAMILIES,
    analyze_grip,
    canonical_snapshot,
    classify_exact_grip,
    find_exact_positions,
    major_key_degree,
    resolve_note,
    snapshot_digest,
    standard_emmons_e9_basic,
)


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_PATH = ROOT / "tests" / "fixtures" / "platform_shared_contract_v1_candidate.json"


def test_basic_profile_matches_the_reviewed_candidate_snapshot() -> None:
    candidate = json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))
    profile = standard_emmons_e9_basic()

    assert profile.id == candidate["copedent"]["profileId"]
    assert profile.revision == candidate["copedent"]["revision"]
    assert canonical_snapshot(profile) == candidate["copedent"]["snapshot"]
    assert snapshot_digest(profile) == candidate["copedent"]["snapshotDigest"]


def test_a_and_b_controls_resolve_only_their_declared_strings() -> None:
    profile = standard_emmons_e9_basic()

    assert resolve_note(profile, string=5, fret=0, controls=("A",)).label == "C#4"
    assert resolve_note(profile, string=6, fret=0, controls=("B",)).label == "A3"
    assert resolve_note(profile, string=7, fret=0, controls=("A", "B")).label == "F#3"
    assert resolve_note(profile, string=4, fret=3, controls=("B", "A")).controls == ("A", "B")


@pytest.mark.parametrize(
    ("fret", "key", "expected_root", "expected_labels"),
    [
        (0, "E", "F#", ("C#4", "A3", "F#3")),
        (3, "G", "A", ("E4", "C4", "A3")),
    ],
)
def test_ab_567_is_the_two_minor_in_the_open_major_position(
    fret: int,
    key: str,
    expected_root: str,
    expected_labels: tuple[str, ...],
) -> None:
    profile = standard_emmons_e9_basic()
    two_minor = major_key_degree(key, 2)
    analysis = analyze_grip(
        profile,
        root=two_minor.root,
        quality=two_minor.quality,
        fret=fret,
        strings=(5, 6, 7),
        controls=("A", "B"),
    )

    assert two_minor.root == expected_root
    assert two_minor.quality == "minor"
    assert tuple(note.label for note in analysis.notes) == expected_labels
    assert analysis.intervals == (7, 3, 0)
    assert analysis.is_exact is True
    assert {
        (match.chord.root, match.chord.quality)
        for match in classify_exact_grip(
            profile,
            fret=fret,
            strings=(5, 6, 7),
            controls=("A", "B"),
        )
    } == {(expected_root, "minor")}


@pytest.mark.parametrize(
    ("fret", "root", "expected_labels"),
    [
        (0, "E", ("E4", "B3", "G#3", "D3")),
        (3, "G", ("G4", "D4", "B3", "F3")),
    ],
)
def test_string_9_completes_transposable_dominant_seventh_grips(
    fret: int,
    root: str,
    expected_labels: tuple[str, ...],
) -> None:
    analysis = analyze_grip(
        standard_emmons_e9_basic(),
        root=root,
        quality="dominant 7",
        fret=fret,
        strings=(4, 5, 6, 9),
    )

    assert tuple(note.label for note in analysis.notes) == expected_labels
    assert analysis.intervals == (0, 7, 4, 10)
    assert analysis.is_exact is True


def test_exact_position_search_finds_the_named_rule_families() -> None:
    profile = standard_emmons_e9_basic()
    families = {family.id: family for family in BASIC_GRIP_FAMILIES}

    g7_family = families["open-dominant7-4569"]
    g7_positions = find_exact_positions(
        profile,
        root="G",
        quality=g7_family.quality,
        grips=(g7_family.strings,),
        control_sets=(g7_family.controls,),
        frets=range(13),
    )
    assert [(position.fret, position.strings, position.controls) for position in g7_positions] == [
        (3, (4, 5, 6, 9), ()),
    ]

    two_minor_family = families["two-minor-ab-567"]
    a_minor_positions = find_exact_positions(
        profile,
        root="A",
        quality=two_minor_family.quality,
        grips=(two_minor_family.strings,),
        control_sets=(two_minor_family.controls,),
        frets=range(13),
    )
    assert [(position.fret, position.strings, position.controls) for position in a_minor_positions] == [
        (3, (5, 6, 7), ("A", "B")),
    ]


def test_invalid_mechanical_requests_fail_closed() -> None:
    profile = standard_emmons_e9_basic()

    with pytest.raises(ValueError, match="Fret is out of range"):
        resolve_note(profile, string=5, fret=25)
    with pytest.raises(ValueError, match="String is not defined"):
        resolve_note(profile, string=11, fret=0)
    with pytest.raises(ValueError, match="Unknown copedent control"):
        resolve_note(profile, string=5, fret=0, controls=("mystery",))
    with pytest.raises(ValueError, match="at least two unique strings"):
        analyze_grip(profile, root="E", quality="major", fret=0, strings=(5, 5))
