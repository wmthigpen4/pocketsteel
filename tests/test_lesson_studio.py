from __future__ import annotations

import pytest

from steel_guitar_rag.lesson_curriculum import CONCEPTS, VALID_KEYS, curriculum_count, mechanics_for
from steel_guitar_rag.lesson_studio import LessonStudioError, build_lesson, build_lesson_response, lesson_catalog


def test_reviewed_catalog_has_five_deep_paths_and_no_progress_claim() -> None:
    catalog = lesson_catalog()

    assert catalog["schemaVersion"] == "lesson_catalog_v2"
    assert catalog["progressPersistence"] is False
    assert catalog["conceptCount"] == curriculum_count() >= 60
    assert [path["id"] for path in catalog["paths"]] == [
        "fundamentals",
        "pedals-levers",
        "chords-movement",
        "technique",
        "applied-playing",
    ]
    assert all(len(path["lessons"]) >= 10 for path in catalog["paths"])


def test_legacy_reviewed_id_builds_lesson_v2_with_complete_teaching_contract() -> None:
    lesson = build_lesson({"lessonId": "chords-i-iv-same-fret"})

    assert lesson["schemaVersion"] == "lesson_v2"
    assert lesson["origin"] == "reviewed"
    assert lesson["pathId"] == "chords-movement"
    assert lesson["whyItMatters"]
    assert lesson["workedExamples"]
    assert lesson["mechanics"]
    assert all(mechanic["validated"] for mechanic in lesson["mechanics"])
    assert len(lesson["exercises"]) == 3
    assert lesson["progressPersistence"] is False


def test_ambiguous_sevenths_request_requires_a_real_choice() -> None:
    response = build_lesson_response({"topic": "Sevenths", "level": "advanced", "duration": "15_min"})

    assert response["status"] == "needs_clarification"
    assert response["clarification"]["id"] == "seventh-quality"
    assert {option["value"] for option in response["clarification"]["options"]} == {
        "dominant-seventh", "major-seventh", "minor-seventh", "seventh-harmony"
    }


def test_clarification_answer_builds_requested_seventh_lesson() -> None:
    response = build_lesson_response(
        {
            "topic": "Sevenths",
            "level": "advanced",
            "duration": "15_min",
            "clarificationAnswers": {"seventh-quality": "dominant-seventh"},
        }
    )

    assert response["status"] == "ready"
    lesson = response["lesson"]
    assert lesson["conceptId"] == "dominant-seventh"
    assert lesson["mechanics"][0]["strings"] == [5, 6, 8, 9]
    assert set(lesson["mechanics"][0]["notes"].values()) == {"G", "B", "D", "F"}
    assert "controlled, musical practice loop" not in str(lesson)


def test_f_lever_lesson_uses_pitch_validated_position_families() -> None:
    lesson = build_lesson({"topic": "F lever", "level": "intermediate", "duration": "15_min", "key": "G"})

    assert lesson["conceptId"] == "f-lever"
    assert lesson["title"] == "Connect the A+F major position"
    assert "strings 4 and 8" in lesson["explanation"]
    assert [(item["fret"], item["pedals"], item["levers"]) for item in lesson["mechanics"]] == [
        (3, [], []),
        (6, ["A"], ["F"]),
    ]
    assert set(lesson["mechanics"][1]["notes"].values()) == {"G", "B", "D"}


def test_unsupported_topic_is_truthfully_unavailable() -> None:
    response = build_lesson_response({"topic": "teleportation theory", "level": "beginner", "duration": "15_min"})

    assert response["status"] == "unavailable"
    assert "mechanically trustworthy" in response["message"]
    assert response["suggestedTopics"]


def test_forum_sources_are_attribution_only_and_unsafe_values_are_removed() -> None:
    response = build_lesson_response(
        {"topic": "pick blocking", "level": "beginner", "duration": "15_min"},
        source_results=[
            {"thread_title": "Blocking discussion", "forum_name": "Steel Guitar Forum", "thread_url": "https://example.test/thread", "excerpt": "RAW PRIVATE-LIKE BODY"},
            {"thread_title": "Bad", "thread_url": "/Users/person/private.txt", "excerpt": "WEBVTT"},
        ],
    )

    lesson = response["lesson"]
    assert lesson["teachingSources"] == [{"type": "forum", "title": "Blocking discussion", "publisher": "Steel Guitar Forum", "url": "https://example.test/thread"}]
    assert "RAW PRIVATE-LIKE BODY" not in str(lesson)
    assert "/Users/" not in str(lesson)


@pytest.mark.parametrize("key", VALID_KEYS)
def test_every_mechanical_concept_validates_in_each_supported_key(key: str) -> None:
    for concept in CONCEPTS:
        mechanics = mechanics_for(concept, key)
        assert all(item["validated"] and item["notes"] for item in mechanics)


def test_every_curriculum_concept_builds_without_generic_filler() -> None:
    forbidden = (
        "controlled, musical practice loop",
        "Begin with one small, repeatable piece of the neck",
        "Compare two practical choices, but keep one as the reference position",
    )
    for concept in CONCEPTS:
        response = build_lesson_response({"lessonId": concept.id})
        assert response["status"] == "ready"
        lesson_text = str(response["lesson"])
        assert response["lesson"]["explanation"] == concept.definition
        assert response["lesson"]["whyItMatters"] == concept.purpose
        assert not any(text in lesson_text for text in forbidden)


@pytest.mark.parametrize("level", ("beginner", "intermediate", "advanced"))
def test_quality_matrix_covers_every_concept_at_every_level(level: str) -> None:
    for concept in CONCEPTS:
        response = build_lesson_response(
            {"lessonId": concept.id, "level": level, "duration": "15_min", "focus": "application"}
        )
        lesson = response["lesson"]
        assert response["status"] == "ready"
        assert lesson["level"] == level
        assert len(lesson["exercises"]) == 3
        assert concept.purpose in lesson["exercises"][2]["steps"][0]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({}, "topic must contain at least 3 characters"),
        ({"topic": "blocking", "level": "expert"}, "level must be"),
        ({"topic": "blocking", "duration": "hour"}, "duration must be"),
        ({"lessonId": "missing"}, "unknown reviewed lesson"),
    ],
)
def test_invalid_lesson_requests_are_rejected(payload: dict[str, str], message: str) -> None:
    with pytest.raises(LessonStudioError, match=message):
        build_lesson(payload)
