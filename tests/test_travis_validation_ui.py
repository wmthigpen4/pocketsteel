from __future__ import annotations

from pathlib import Path

from scripts.build_local_chord_reader_test import _audio_url, _display_title


ROOT = Path(__file__).resolve().parents[1]
VALIDATION_ROOT = ROOT / "ui/chord-reader-travis-validation"


def test_private_validation_page_exposes_review_and_export_controls() -> None:
    html = (VALIDATION_ROOT / "index.html").read_text(encoding="utf-8")
    script = (VALIDATION_ROOT / "validation.js").read_text(encoding="utf-8")
    css = (VALIDATION_ROOT / "validation.css").read_text(encoding="utf-8")

    assert "Chord Reader — Travis Validation" in html
    assert '<audio id="audio" controls' in html
    assert 'id="chord-grid"' in html
    assert 'data-status="confirmed"' in html
    assert 'data-status="corrected"' in html
    assert 'data-status="timing"' in html
    assert 'data-status="unsure"' in html
    assert 'id="song-notes"' in html
    assert 'id="export-feedback"' in html
    assert 'const DATA_URL = "./local-data/proof.json"' in script
    assert 'get("session") || "default"' in script
    assert "localStorage.setItem" in script
    assert 'schemaVersion: "chord_reader_travis_feedback_v1"' in script
    assert 'status: "unreviewed"' in script
    assert "modelConfidence" in script
    assert ".chord-card.corrected" in css


def test_local_builder_creates_browser_ready_output_urls_and_clean_titles(tmp_path: Path) -> None:
    numbered = tmp_path / "07 - That's The Way Love Goes.mp3"
    assert _display_title(numbered) == "That's The Way Love Goes"

    destination = ROOT / "ui/chord-reader-travis-validation/local-data/audio/test.mp3"
    assert _audio_url(destination) == "/ui/chord-reader-travis-validation/local-data/audio/test.mp3"


def test_validation_generated_data_is_git_ignored() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "ui/chord-reader-travis-validation/local-data/" in ignore
