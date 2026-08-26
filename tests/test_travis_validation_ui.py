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
    assert 'data-status="timing"' in html
    assert 'data-status="unsure"' in html
    assert 'id="finish-track"' in html
    assert 'id="song-key"' in html
    assert 'data-notation="chords"' in html
    assert 'data-notation="nns"' in html
    assert 'class="active"\n                      data-notation="nns"' in html
    assert "Right chord (only if different)" in html
    assert "Split/slash chord" in html
    assert 'class="rail-labels"' in html
    assert 'id="song-notes"' in html
    assert 'id="export-feedback"' in html
    assert 'class="box-number"' in html
    assert 'id="merge-selected"' in html
    assert 'id="song-meter"' in html
    assert 'id="song-tempo"' in html
    assert 'id="grid-earlier"' in html
    assert 'id="grid-later"' in html
    assert 'id="downbeat-phase"' in html
    assert 'id="set-downbeat-here"' in html
    assert 'id="click-track"' in html
    assert 'src="./phase-anchor.js?v=8"' in html
    assert 'class="beat-grid"' in html
    assert 'class="merge-select"' in html
    assert 'class="unmerge-button"' in html
    assert 'const DATA_URL = "./local-data/proof.json"' in script
    assert 'get("session") || "default"' in script
    assert "localStorage.setItem" in script
    assert 'const FEEDBACK_URL = "/api/travis-validation/feedback"' in script
    assert "Saving securely" in script
    assert "saveRemoteTrack" in script
    assert "keepalive: true" in script
    assert 'schemaVersion: "chord_reader_travis_feedback_v1"' in script
    assert 'status: "assumed_correct"' in script
    assert 'displayMode: "nns"' in script
    assert '"pending_assumed_correct"' in script
    assert "record.reviewComplete" in script
    assert "highestConfidence" in script
    assert "Highest-confidence starting track" in script
    assert "scrollIntoView" in script
    assert "function inferKey" in script
    assert "function chordToNns" in script
    assert 'replace(/7/g, "⁷")' in script
    assert "function isLowConfidenceTransient" in script
    assert "function mergeSelectedBoxes" in script
    assert "function rhythmicDisplayItems" in script
    assert "function chordDecisionForBar" in script
    assert "supported half-bar split" in script
    assert "possible half-bar split — verify" in script
    assert "function displayItemChordAt" in script
    assert "timingOffsetSeconds" in script
    assert "downbeatOffsetBeats" in script
    assert "downbeatPhaseSource" in script
    assert "function auditionBeatAt" in script
    assert "function playGridClick" in script
    assert 'windowItem("pickup"' in script
    assert "unstable raw changes collapsed" in script
    assert "requestAnimationFrame" in script
    assert "beat-aligned bars" in script
    assert "provisional — please confirm" in script
    assert "boxMerges" in script
    assert 'return "Lead-in · N.C."' in script
    assert "predictedNns" in script
    assert 'keySource = "reviewer"' in script
    assert "modelConfidence" in script
    assert ".chord-card.corrected" in css
    assert ".chord-card.selected-for-merge" in css
    assert ".chord-card.manual-merge" in css
    assert "box-shadow: inset 0 -3px 0 var(--gold)" in css
    assert "background: rgba(237, 196, 110, 0.18)" in css
    assert ".chord-grid {" in css
    assert "display: flex" in css
    assert "overflow: hidden" in css


def test_local_builder_creates_browser_ready_output_urls_and_clean_titles(tmp_path: Path) -> None:
    numbered = tmp_path / "07 - That's The Way Love Goes.mp3"
    assert _display_title(numbered) == "That's The Way Love Goes"

    destination = ROOT / "ui/chord-reader-travis-validation/local-data/audio/test.mp3"
    assert _audio_url(destination) == "/ui/chord-reader-travis-validation/local-data/audio/test.mp3"


def test_validation_generated_data_is_git_ignored() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "ui/chord-reader-travis-validation/local-data/" in ignore


def test_protected_worker_routes_the_phase_anchor_asset() -> None:
    worker = (
        ROOT / "workers/chord-reader-validation/src/index.ts"
    ).read_text(encoding="utf-8")
    assert '`${APP_BASE}/phase-anchor.js`' in worker
    assert 'return "app/phase-anchor.js"' in worker
