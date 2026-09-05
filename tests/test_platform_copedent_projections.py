from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from packages.steel_theory import (
    ApprovedProfileMatch,
    CopedentProfile,
    analyze_grip,
    canonical_snapshot,
    major_key_degree,
    project_howdy_copedent,
    project_rag_copedent,
    resolve_note,
    snapshot_digest,
    standard_emmons_e9_basic,
)
from steel_guitar_rag.e9_copedents import get_e9_copedent_profile


ROOT = Path(__file__).resolve().parents[1]
HOWDY_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "platform_howdy_contract_v1.json"
RAG_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "platform_rag_contract_v1.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def approved_howdy_match(fixture: dict[str, Any]) -> ApprovedProfileMatch:
    metadata = fixture["copedentMatch"]
    profile = standard_emmons_e9_basic()
    assert metadata["status"] == "approved-for-m1b-synthetic-projection-only"
    assert metadata["canonicalProfileId"] == profile.id
    assert metadata["canonicalRevision"] == profile.revision
    return ApprovedProfileMatch(
        approval_id=metadata["approvalId"],
        source_profile_id=metadata["sourceProfileId"],
        canonical_profile=profile,
    )


def assert_m1a_gold_grips(profile: CopedentProfile) -> None:
    two_minor = major_key_degree("G", 2)
    assert analyze_grip(
        profile,
        root=two_minor.root,
        quality=two_minor.quality,
        fret=3,
        strings=(5, 6, 7),
        controls=("A", "B"),
    ).is_exact
    assert analyze_grip(
        profile,
        root="G",
        quality="dominant7",
        fret=3,
        strings=(4, 5, 6, 9),
    ).is_exact


def test_rag_projection_matches_the_shared_profile_and_characterized_pitches() -> None:
    source = get_e9_copedent_profile().to_dict(include_options=False)
    projection = project_rag_copedent(source)
    shared = standard_emmons_e9_basic()

    assert projection.errors == ()
    assert {item.code for item in projection.warnings} == {"controls_outside_m1a"}
    assert projection.profile is not None
    assert projection.profile.id == shared.id
    assert projection.profile.revision == shared.revision
    assert canonical_snapshot(projection.profile) == canonical_snapshot(shared)
    assert projection.digest == snapshot_digest(shared)

    rag_fixture = load_json(RAG_FIXTURE_PATH)
    for event in rag_fixture["expectedPlanProjection"]["events"]:
        for note in event["position"]["notes"]:
            resolved = resolve_note(
                projection.profile,
                string=note["string"],
                fret=note["fret"],
                controls=note["changes"],
            )
            assert resolved.label == note["pitchLabel"]

    assert_m1a_gold_grips(projection.profile)


def test_howdy_projection_uses_only_the_approved_synthetic_profile_match() -> None:
    fixture = load_json(HOWDY_FIXTURE_PATH)
    source = fixture["syntheticContract"]["copedent"]
    approved_match = approved_howdy_match(fixture)
    projection = project_howdy_copedent(source, approved_match=approved_match)
    shared = standard_emmons_e9_basic()

    assert projection.errors == ()
    assert {item.code for item in projection.warnings} == {
        "control_deltas_supplied_by_approved_match",
        "revision_supplied_by_approved_match",
    }
    assert projection.approval_id == fixture["copedentMatch"]["approvalId"]
    assert projection.profile is not None
    assert canonical_snapshot(projection.profile) == canonical_snapshot(shared)
    assert projection.digest == snapshot_digest(shared)
    assert_m1a_gold_grips(projection.profile)


def test_howdy_projection_fails_closed_without_an_explicit_match() -> None:
    fixture = load_json(HOWDY_FIXTURE_PATH)
    source = fixture["syntheticContract"]["copedent"]

    projection = project_howdy_copedent(source, approved_match=None)

    assert projection.profile is None
    assert [item.code for item in projection.errors] == ["missing_approved_profile_match"]


def test_howdy_projection_rejects_a_control_membership_mismatch() -> None:
    fixture = load_json(HOWDY_FIXTURE_PATH)
    source = deepcopy(fixture["syntheticContract"]["copedent"])
    source["controls"][0]["strings"] = [5]

    projection = project_howdy_copedent(source, approved_match=approved_howdy_match(fixture))

    assert projection.profile is None
    assert [item.code for item in projection.errors] == ["control_string_mismatch"]


def test_howdy_projection_rejects_an_explicit_control_delta_mismatch() -> None:
    fixture = load_json(HOWDY_FIXTURE_PATH)
    source = deepcopy(fixture["syntheticContract"]["copedent"])
    source["controls"][0]["changes"] = [
        {"string": 5, "semitones": 1},
        {"string": 10, "semitones": 2},
    ]

    projection = project_howdy_copedent(source, approved_match=approved_howdy_match(fixture))

    assert projection.profile is None
    assert [item.code for item in projection.errors] == ["control_delta_mismatch"]


def test_rag_projection_rejects_a_pitch_label_disagreement() -> None:
    source = deepcopy(get_e9_copedent_profile().to_dict(include_options=False))
    source["strings"][4]["open_scientific_pitch"] = "C4"

    projection = project_rag_copedent(source)

    assert projection.profile is None
    assert [item.code for item in projection.errors] == ["invalid_copedent"]
