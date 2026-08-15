from __future__ import annotations

import json
from pathlib import Path

import pytest

from steel_guitar_rag.ttt_concept_graph import (
    TttConceptGraphError,
    compile_concept_graph,
    discover_timestamped_transcripts,
    parse_timestamped_transcript,
)


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY = json.loads(
    (ROOT / "partner_companions" / "travis_practice_guide" / "content" / "concept-taxonomy.json").read_text(
        encoding="utf-8"
    )
)


def _write_transcript(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_parse_timestamped_transcript_rejects_non_cue_lines(tmp_path: Path) -> None:
    path = tmp_path / "bad.timestamped.txt"
    path.write_text("private prose without a cue\n", encoding="utf-8")
    with pytest.raises(TttConceptGraphError, match="not a timestamped cue"):
        parse_timestamped_transcript(path)


def test_discovery_excludes_zoom_meetings(tmp_path: Path) -> None:
    _write_transcript(tmp_path / "Lessons" / "Intervals-Explained.timestamped.txt", ["[00:00:00.000 - 00:00:02.000] intervals"])
    _write_transcript(tmp_path / "Zoom Meetings" / "Zoom.timestamped.txt", ["[00:00:00.000 - 00:00:02.000] intervals"])
    paths = discover_timestamped_transcripts(tmp_path)
    assert [path.name for path in paths] == ["Intervals-Explained.timestamped.txt"]


def test_compiler_retains_exact_cue_evidence_and_deterministic_hash(tmp_path: Path) -> None:
    _write_transcript(
        tmp_path / "Theory" / "Intervals-Explained" / "Intervals-Explained.timestamped.txt",
        [
            "[00:00:01.000 - 00:00:03.000] Intervals are scale degrees in a key.",
            "[00:00:03.000 - 00:00:05.000] A dominant 7 is a major chord with a flat seven note.",
        ],
    )
    catalog = {
        "schemaVersion": "ttt_lesson_catalog_v1",
        "revision": "test",
        "lessons": [
            {
                "id": "intervals-explained",
                "title": "Intervals Explained",
                "sourceSlug": "Intervals-Explained",
                "url": "https://travis-toy-tutorials.teachable.com/courses/test/lectures/123",
                "durationMs": 5000,
                "depth": "quick",
                "dedicatedConceptIds": ["intervals"],
                "isZoom": False,
            }
        ],
    }
    first = compile_concept_graph(tmp_path, TAXONOMY, catalog)
    second = compile_concept_graph(tmp_path, TAXONOMY, catalog)
    assert first == second
    assert first["sourcePolicy"]["nonZoomOnly"] is True
    assert first["sourcePolicy"]["rawTranscriptDeployable"] is False
    assert first["sourcePolicy"]["commentsIncluded"] is False
    assert first["sourcePolicy"]["modelCallsAllowedAtRuntime"] is False
    assert first["sourcePolicy"]["authoringDiscoveryMode"] == "offline_semantic_token_overlap"
    assert first["sourcePolicy"]["semanticCandidatesAutoPublished"] is False
    mentions = {(item["conceptId"], item["startMs"], item["endMs"]) for item in first["mentions"]}
    assert ("intervals", 1000, 3000) in mentions
    assert ("dominant_7", 3000, 5000) in mentions
    assert first["graphSha256"]


def test_semantic_candidates_enter_private_review_queue_but_not_mentions(tmp_path: Path) -> None:
    _write_transcript(
        tmp_path / "Theory" / "Other-Lesson" / "Other-Lesson.timestamped.txt",
        ["[00:00:01.000 - 00:00:03.000] Listen to the distance between two notes before moving."],
    )
    catalog = {
        "schemaVersion": "ttt_lesson_catalog_v1",
        "revision": "test",
        "lessons": [
            {
                "id": "other-lesson",
                "title": "Other Lesson",
                "sourceSlug": "Other-Lesson",
                "url": "https://travis-toy-tutorials.teachable.com/courses/test/lectures/124",
                "durationMs": 3000,
                "depth": "focused",
                "dedicatedConceptIds": [],
                "isZoom": False,
            }
        ],
    }
    graph = compile_concept_graph(tmp_path, TAXONOMY, catalog)
    interval_candidates = [item for item in graph["reviewQueue"] if item.get("conceptId") == "intervals"]
    assert interval_candidates
    assert all(item["autoPublishAllowed"] is False for item in interval_candidates)
    assert not [item for item in graph["mentions"] if item["conceptId"] == "intervals"]


def test_explicit_dedicated_lesson_ranks_before_generic_definition(tmp_path: Path) -> None:
    _write_transcript(
        tmp_path / "Theory" / "Generic-Seventh" / "Generic-Seventh.timestamped.txt",
        ["[00:00:01.000 - 00:00:03.000] A dominant 7 is a major chord with a flat seven note."],
    )
    _write_transcript(
        tmp_path / "Theory" / "Dom7th-Chords---Common-Positions" / "Dom7th-Chords---Common-Positions.timestamped.txt",
        ["[00:00:01.000 - 00:00:03.000] Here is a dominant 7 position on these strings."],
    )
    catalog = {
        "schemaVersion": "ttt_lesson_catalog_v1",
        "revision": "test",
        "lessons": [
            {
                "id": "generic-seventh",
                "title": "Generic Seventh",
                "sourceSlug": "Generic-Seventh",
                "url": "https://travis-toy-tutorials.teachable.com/courses/test/lectures/125",
                "durationMs": 3000,
                "depth": "focused",
                "dedicatedConceptIds": [],
                "isZoom": False,
            },
            {
                "id": "dominant-seven-positions",
                "title": "Dom7th Chords - Common Positions",
                "sourceSlug": "Dom7th-Chords---Common-Positions",
                "url": "https://travis-toy-tutorials.teachable.com/courses/test/lectures/126",
                "durationMs": 3000,
                "depth": "focused",
                "dedicatedConceptIds": ["dominant_7"],
                "isZoom": False,
            },
        ],
    }
    graph = compile_concept_graph(tmp_path, TAXONOMY, catalog)
    top = next(item for item in graph["recommendations"] if item["conceptId"] == "dominant_7" and item["rank"] == 1)
    assert top["lessonId"] == "dominant-seven-positions"
    assert top["dedicatedLesson"] is True
    assert next(item for item in graph["rankingAudit"] if item["conceptId"] == "dominant_7")["dedicatedFirstPassed"] is True


def test_short_prerequisite_ranks_before_longer_non_dedicated_lesson(tmp_path: Path) -> None:
    for slug in ("Quick-Primer", "Focused-Discussion"):
        _write_transcript(
            tmp_path / "Theory" / slug / f"{slug}.timestamped.txt",
            ["[00:00:01.000 - 00:00:03.000] What this means is intervals are scale degrees."],
        )
    catalog = {
        "schemaVersion": "ttt_lesson_catalog_v1",
        "revision": "test",
        "lessons": [
            {
                "id": "quick-primer",
                "title": "Quick Primer",
                "sourceSlug": "Quick-Primer",
                "url": "https://travis-toy-tutorials.teachable.com/courses/test/lectures/127",
                "durationMs": 3000,
                "depth": "quick",
                "dedicatedConceptIds": [],
                "isZoom": False,
            },
            {
                "id": "focused-discussion",
                "title": "Focused Discussion",
                "sourceSlug": "Focused-Discussion",
                "url": "https://travis-toy-tutorials.teachable.com/courses/test/lectures/128",
                "durationMs": 120000,
                "depth": "focused",
                "dedicatedConceptIds": [],
                "isZoom": False,
            },
        ],
    }
    graph = compile_concept_graph(tmp_path, TAXONOMY, catalog)
    top = next(item for item in graph["recommendations"] if item["conceptId"] == "intervals" and item["rank"] == 1)
    assert top["lessonId"] == "quick-primer"
