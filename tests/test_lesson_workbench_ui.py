from __future__ import annotations

import re
import subprocess
from pathlib import Path


def run_node(source: str) -> None:
    subprocess.run(["node", "-e", source], check=True, text=True, capture_output=True)


def test_lesson_workbench_helpers_normalize_requests_and_links() -> None:
    run_node(
        r"""
const assert = require("node:assert/strict");
const lessons = require("./ui/lesson-workbench.js");

assert.deepEqual(lessons.buildLessonRequest({lessonId: " reviewed-one "}), {lessonId: "reviewed-one"});
assert.deepEqual(lessons.buildLessonRequest({topic: "  blocking ", level: "INTERMEDIATE", duration: "deep_dive"}), {
  topic: "blocking", level: "intermediate", duration: "deep_dive"
});
assert.equal(lessons.normalizeLevel("expert"), "beginner");
assert.equal(lessons.normalizeDuration("hour"), "15_min");
assert.equal(lessons.durationLabel("5_min"), "5 minutes");
assert.deepEqual(lessons.safeLessonLink({type: "explorer", label: "Open", url: "/ui/e9-fretboard-explorer.html?mode=chord"}), {
  type: "explorer", label: "Open", url: "/ui/e9-fretboard-explorer.html?mode=chord"
});
assert.equal(lessons.safeLessonLink({label: "Bad", url: "https://example.test"}), null);
const paths = lessons.normalizeCatalog({paths: [{id: "fundamentals", title: "Fundamentals", lessons: [{id: "one", title: "One", level: "beginner", duration: "5_min"}]}]});
assert.equal(paths[0].lessons[0].title, "One");
const view = lessons.lessonViewModel({
  origin: "reviewed", title: "Test", level: "advanced", duration: "deep_dive",
  links: [{type: "melody", label: "Continue", url: "/ui/melody-workbench.html"}], progressPersistence: false
});
assert.equal(view.origin, "Reviewed lesson");
assert.equal(view.level, "Advanced");
assert.equal(view.duration, "Deep dive");
assert.equal(view.links[0].type, "melody");
"""
    )


def test_lesson_workbench_has_reviewed_custom_and_complete_lesson_surfaces() -> None:
    html = Path("ui/lesson-workbench.html").read_text(encoding="utf-8")
    script = Path("ui/lesson-workbench.js").read_text(encoding="utf-8")
    ids = re.findall(r'id="([^"]+)"', html)

    assert len(ids) == len(set(ids))
    assert "Choose a reviewed path or build a focused lesson" in html
    assert 'id="lesson-catalog"' in html
    assert 'id="custom-lesson-form"' in html
    assert 'id="lesson-topic"' in html
    assert 'id="lesson-level"' in html
    assert 'id="lesson-duration"' in html
    assert 'id="lesson-result" hidden' in html
    assert "Beginner" in html and "Intermediate" in html and "Advanced" in html
    assert "5 minutes" in html and "15 minutes" in html and "Deep dive" in html
    assert "progress is not saved yet" in script
    assert "What to listen for" in script
    assert "Common mistakes" in script
    assert "Session checklist" in script
    assert 'href="/ui/steel-guitar-rag-mock.html">Ask</a>' in html
    assert 'href="/ui/e9-fretboard-explorer.html">Explore</a>' in html
    assert 'href="/ui/melody-workbench.html">Arrange</a>' in html
    assert 'href="/ui/lesson-workbench.html" aria-current="page">Learn</a>' in html
    assert "[object Object]" not in html


def test_four_workspace_navigation_and_explorer_chord_doorway_are_visible() -> None:
    home = Path("ui/steel-guitar-rag-mock.html").read_text(encoding="utf-8")
    explorer = Path("ui/e9-fretboard-explorer.html").read_text(encoding="utf-8")
    melody = Path("ui/melody-workbench.html").read_text(encoding="utf-8")

    for label in (
        "Fretboard Explorer",
        "Melody Studio",
        "Lessons",
        "Ask the Brain",
    ):
        assert label in home
    for label in (">Ask</span>", ">Explore</span>", ">Arrange</span>", ">Learn</span>"):
        assert label in explorer
        assert label in melody
    assert "Find chords and voicings" in explorer
    assert "Chord Studio" not in home + explorer + melody
