from __future__ import annotations

import pytest

from pocketsteel.lesson_studio import LessonStudioError, build_lesson, lesson_catalog


def test_reviewed_catalog_has_five_paths_and_no_progress_claim() -> None:
    catalog = lesson_catalog()

    assert catalog["schemaVersion"] == "lesson_catalog_v1"
    assert catalog["progressPersistence"] is False
    assert [path["id"] for path in catalog["paths"]] == [
        "fundamentals",
        "pedals-levers",
        "chords-movement",
        "technique",
        "applied-playing",
    ]
    assert all(len(path["lessons"]) == 2 for path in catalog["paths"])


def test_reviewed_chord_lesson_has_complete_practice_contract_and_explorer_link() -> None:
    lesson = build_lesson({"lessonId": "chords-i-iv-same-fret"})

    assert lesson["schemaVersion"] == "lesson_v1"
    assert lesson["origin"] == "reviewed"
    assert lesson["pathId"] == "chords-movement"
    assert lesson["level"] == "beginner"
    assert len(lesson["exercises"]) == 3
    assert all(exercise["listenFor"] for exercise in lesson["exercises"])
    assert lesson["whatToListenFor"]
    assert lesson["commonMistakes"]
    assert lesson["practiceChecklist"]
    assert lesson["nextStep"]
    assert lesson["links"][0]["url"].startswith("/ui/e9-fretboard-explorer.html?mode=chord")
    assert lesson["progressPersistence"] is False


def test_custom_lesson_classifies_topic_and_respects_level_and_duration() -> None:
    lesson = build_lesson(
        {"topic": "E-lower lever movement", "level": "advanced", "duration": "deep_dive"}
    )

    assert lesson["origin"] == "custom"
    assert lesson["topic"] == "E-lower lever movement"
    assert lesson["level"] == "advanced"
    assert lesson["duration"] == "deep_dive"
    assert len(lesson["exercises"]) == 4
    assert "control-impact" in lesson["nextStep"].lower()


def test_custom_f_lever_lesson_teaches_the_actual_e9_move() -> None:
    lesson = build_lesson({"topic": "F lever", "level": "intermediate", "duration": "15_min"})

    assert lesson["title"] == "Learn the F lever through a G-major inversion"
    assert "strings 4 and 8 from E to F" in lesson["explanation"]
    assert "fret 6 on strings 4-5-6" in lesson["explanation"]
    assert "B-G-D" in lesson["explanation"]
    assert any("fret 3" in step and "G-D-B" in step for step in lesson["exercises"][0]["steps"])
    assert any("F lever without the A pedal" in item for item in lesson["commonMistakes"])
    assert "controlled, musical practice loop" not in lesson["goal"]


def test_custom_sevenths_lesson_teaches_a_complete_g7_and_resolution() -> None:
    lesson = build_lesson({"topic": "Sevenths", "level": "advanced", "duration": "15_min"})

    assert lesson["title"] == "Build and resolve a G7 chord"
    assert "strings 5-6-8-9" in lesson["explanation"]
    assert "D-B-G-F" in lesson["explanation"]
    assert "A+B on strings 5-6-8" in lesson["explanation"]
    assert lesson["practiceChecklist"][0] == "I can spell G7 as G-B-D-F."
    assert lesson["links"][0]["url"].endswith("quality=dominant7&source=lesson")
    assert all("Compare two practical choices" not in step for exercise in lesson["exercises"] for step in exercise["steps"])


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
