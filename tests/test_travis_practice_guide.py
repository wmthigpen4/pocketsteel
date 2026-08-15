from __future__ import annotations

import json
from pathlib import Path

import pytest

from partner_companions.travis_practice_guide.release import (
    DEFAULT_CATALOG,
    DEFAULT_COLLECTION,
    DEFAULT_TAXONOMY,
    PracticeGuideReleaseError,
    build_practice_guide_bundle,
    validate_collection,
)


ROOT = Path(__file__).resolve().parents[1]


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_pilot_collection_is_deterministic_and_bounded() -> None:
    collection = _json(DEFAULT_COLLECTION)
    taxonomy = _json(DEFAULT_TAXONOMY)
    catalog = _json(DEFAULT_CATALOG)
    validate_collection(collection, taxonomy, catalog)
    assert collection["runtimeMode"] == "published_deterministic"
    assert collection["modelCallsAllowed"] is False
    assert len(collection["guides"]) == 4
    expected_blocks = ["point", "moments", "practice", "diagnostics", "conceptTrails", "visualization", "nextLessons"]
    assert all(guide["orderedGuideBlocks"] == expected_blocks for guide in collection["guides"])
    assert all(guide["runtime"] == {"mode": "published_deterministic", "modelCallsAllowed": False} for guide in collection["guides"])
    assert all(3 <= len(guide["moments"]) <= 7 for guide in collection["guides"])
    assert all(len(trail["targets"]) <= 3 for guide in collection["guides"] for trail in guide["conceptTrails"])
    assert all(
        1 <= len(target["evidenceExcerpt"].split()) <= 22
        for guide in collection["guides"]
        for trail in guide["conceptTrails"]
        for target in trail["targets"]
    )
    assert all(item["isZoom"] is False for item in catalog["lessons"])


def test_dominant_and_major_seventh_remain_distinct() -> None:
    concepts = {item["id"]: item for item in _json(DEFAULT_TAXONOMY)["concepts"]}
    assert concepts["dominant_7"]["formula"] == "1-3-5-b7"
    assert concepts["major_7"]["formula"] == "1-3-5-7"
    assert "major_7" in concepts["dominant_7"]["confusionConceptIds"]
    assert "dominant_7" in concepts["major_7"]["confusionConceptIds"]


def test_four_pilots_cover_the_required_companion_types_and_vertical_contract() -> None:
    collection = _json(DEFAULT_COLLECTION)
    guides = {item["lessonId"]: item for item in collection["guides"]}
    assert {lesson_id: guide["type"] for lesson_id, guide in guides.items()} == {
        "right-hand-exercise-1": "technique_coach",
        "pedals-really-doing": "pedal_theory_lab",
        "pockets-positions-1": "fretboard_path_guide",
        "howdy-solo": "application_guide",
    }
    assert {lesson_id: guide["visualization"]["type"] for lesson_id, guide in guides.items()} == {
        "right-hand-exercise-1": "motion_sequence",
        "pedals-really-doing": "pedal_interval_map",
        "pockets-positions-1": "position_path",
        "howdy-solo": "phrase_map",
    }
    assert all(guide["searchEnabled"] is (guide["durationMs"] > 600_000) for guide in guides.values())
    assert all(2 <= len(guide["nextLessons"]) <= 3 for guide in guides.values())
    assert all(len(trail["targets"]) <= 3 for guide in guides.values() for trail in guide["conceptTrails"])
    assert all(
        claim["provenance"] in {"transcript", "deterministic_rule", "editorial", "human_transcription"}
        and claim["reviewStatus"]
        for guide in guides.values()
        for claim in guide["claims"]
    )
    howdy = guides["howdy-solo"]
    assert howdy["setup"]["key"].startswith("D;")
    assert not any(key in howdy for key in ("events", "tablature", "chordTimeline", "audio"))
    template = (
        ROOT / "partner_companions" / "travis_practice_guide" / "templates" / "guide.html"
    ).read_text(encoding="utf-8")
    assert template.index("data-guide-root") < template.index("teachable-comments")


def test_invalid_theory_formula_fails_closed() -> None:
    collection = _json(DEFAULT_COLLECTION)
    taxonomy = _json(DEFAULT_TAXONOMY)
    catalog = _json(DEFAULT_CATALOG)
    dominant = next(item for item in taxonomy["concepts"] if item["id"] == "dominant_7")
    dominant["formula"] = "1-3-5-7"
    with pytest.raises(PracticeGuideReleaseError, match="theory validation failed"):
        validate_collection(collection, taxonomy, catalog)


def test_local_bundle_is_allowlisted_and_contains_four_pdf_cards(tmp_path: Path) -> None:
    output = tmp_path / "preview"
    manifest = build_practice_guide_bundle(output)
    assert manifest["deployment"] == "not_performed_local_ungated"
    assert manifest["sourceVerification"] == {"status": "not_requested"}
    assert (output / "practice-guide" / "index.html").is_file()
    assert (output / "practice-guide" / "jump" / "index.html").is_file()
    assert len(list((output / "assets").rglob("*-practice-card.pdf"))) == 4
    public_data = json.loads(next((output / "assets").rglob("practice-guides.json")).read_text(encoding="utf-8"))
    assert public_data["buildSha"] == manifest["gitSha"]
    assert manifest["assetToken"]
    serialized = json.dumps(public_data).lower()
    assert "sourcerelpath" not in serialized
    assert "sourceslug" not in serialized
    assert "semanticseeds" not in serialized
    assert "reviewqueue" not in serialized
    assert "dedicatedconceptids" not in serialized
    assert ".timestamped.txt" not in serialized
    assert public_data["sourcePolicy"]["rawTranscriptsIncluded"] is False
    assert public_data["sourcePolicy"]["rawCommentsIncluded"] is False
