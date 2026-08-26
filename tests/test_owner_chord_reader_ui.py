from __future__ import annotations

from pathlib import Path

from scripts.serve_owner_chord_reader import STATIC_PATHS, _clean_title, _slug


ROOT = Path(__file__).resolve().parents[1]
PAGE_ROOT = ROOT / "ui/chord-reader-owner-test"


def test_owner_page_is_a_local_drop_and_listening_surface() -> None:
    html = (PAGE_ROOT / "index.html").read_text(encoding="utf-8")
    script = (PAGE_ROOT / "owner-test.js").read_text(encoding="utf-8")
    timing = (PAGE_ROOT / "timing.js").read_text(encoding="utf-8")
    server = (ROOT / "scripts/serve_owner_chord_reader.py").read_text(encoding="utf-8")

    assert "My Chord Reader Test" in html
    assert "Private owner workbench" in html
    assert 'id="drop-zone"' in html
    assert 'id="file-input"' in html
    assert "Stays on this Mac" in html
    assert "Confidence is not accuracy" in html
    assert 'id="bar-grid"' in html
    assert 'id="song-key"' in html
    assert 'data-notation="nns"' in html
    assert 'id="transport-toggle"' in html
    assert 'id="timing-mode"' in html
    assert 'src="./timing.js?v=2"' in html
    assert 'src="./owner-test.js?v=3"' in html
    assert 'aria-label="Persistent playback controls"' in html
    assert 'addEventListener("drop"' in script
    assert "fetch(`${API}/analyze`" in script
    assert "fetch(`${API}/tracks`" in script
    assert "travis-phase-safe-timing-v2" in server
    assert "scripts/build_current_chord_reader_bars.js" in server
    assert "scripts/chord_reader_v2.js" in server
    assert 'default="127.0.0.1"' in server
    assert "may bind only to localhost" in server
    assert "Accept-Ranges" in server
    assert "HTTPStatus.PARTIAL_CONTENT" in server
    assert "pathname in STATIC_PATHS" in server
    assert 'let displayMode = "nns"' in script
    assert "function chordToNns" in script
    assert 'addEventListener("play", syncTransport)' in script
    assert 'setAttribute("aria-current", "true")' in script
    assert "OwnerChordTiming.itemsForTrack" in script
    assert 'phaseAnchored = track.rhythm?.phase?.status === "anchored"' in timing
    assert 'mode: "exact-model-transitions"' in timing
    assert "chordIndexAt" in timing
    styles = (PAGE_ROOT / "owner-test.css").read_text(encoding="utf-8")
    assert "position: sticky" in styles
    assert 'content: "NOW"' in styles
    assert ".bar-card.active" in styles


def test_owner_test_generated_library_is_ignored() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "ui/chord-reader-owner-test/local-data/" in ignore


def test_owner_test_names_are_bounded_and_browser_safe() -> None:
    assert _slug("Goodness of God (Radio Version)") == "goodness-of-god-radio-version"
    assert _slug("***") == "song"
    assert _clean_title("  Goodness   of God  ", "fallback.mov") == "Goodness of God"
    assert _clean_title("", "fallback.mov") == "fallback"


def test_owner_server_static_allowlist_does_not_expose_repo_files() -> None:
    assert "/ui/chord-reader-owner-test/" in STATIC_PATHS
    assert "/ui/chord-reader-owner-test/owner-test.js" in STATIC_PATHS
    assert "/.git/config" not in STATIC_PATHS
    assert "/scripts/serve_owner_chord_reader.py" not in STATIC_PATHS
