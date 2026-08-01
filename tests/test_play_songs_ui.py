from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_songs_catalog_and_player_keep_existing_visual_language() -> None:
    songs = (REPO_ROOT / "ui" / "songs.html").read_text(encoding="utf-8")
    player = (REPO_ROOT / "ui" / "play-song.html").read_text(encoding="utf-8")
    css = (REPO_ROOT / "ui" / "play-songs.css").read_text(encoding="utf-8")

    assert "Steel Guitar RAG" in songs and "Steel Guitar RAG" in player
    assert "Pocket Steel" not in songs + player + css
    assert "Starter Songs" in songs
    assert "My Tracks" in songs
    assert "Add Your Track" in songs
    assert "Audio stays in this browser" in songs
    assert 'class="play-cue is-current"' in player
    assert 'class="play-cue is-next"' in player
    assert player.index('class="play-cue is-current"') < player.index('class="play-cue is-next"')
    assert "Preview grips" in player
    assert "2-bar loop" in player
    assert "4-bar loop" in player
    assert "Full song" in player
    assert "Less help" in player
    assert 'id="play-attribution"' in player
    assert 'id="play-route"' in player
    assert "--gold: #f0bf69" in css
    assert '--lesson: Georgia, "Times New Roman", serif' in css
    assert ".play-fretboard [data-highlight-id=\"play-next\"]" in css
    assert "filter: grayscale(0.6)" in css
    assert "@media (orientation: landscape) and (max-height: 560px)" in css


def test_device_import_is_opfs_only_and_player_is_audio_clock_driven() -> None:
    songs_js = (REPO_ROOT / "ui" / "songs.js").read_text(encoding="utf-8")
    player_js = (REPO_ROOT / "ui" / "play-song.js").read_text(encoding="utf-8")

    assert "navigator.storage.getDirectory" in songs_js
    assert 'storage: "opfs"' in songs_js
    assert 'uploaded: false, networkAllowed: false' in songs_js
    assert "MAX_BYTES = 250 * 1024 * 1024" in songs_js
    assert "MAX_DURATION_SECONDS = 15 * 60" in songs_js
    import_slice = songs_js[songs_js.index("async function importTrack"):songs_js.index("function songCard")]
    assert "fetch(" not in import_slice
    assert "XMLHttpRequest" not in import_slice
    assert "sendBeacon" not in import_slice
    assert "audio.currentTime * 1000" in player_js
    assert "track?.beatTimesMs" in player_js
    assert "track.recordingCredit" in player_js
    assert "track.licenseUrl" in player_js
    assert "selectedRoute()?.positions || track.authoredRoute" in player_js
    assert "function selectedRoute" in player_js
    assert "Move the bar" not in player_js
    assert "Source &amp; license" in songs_js
    assert "setInterval" not in player_js
    assert "function leftAlignSvgStringLabels" in player_js
    assert 'leftAlignSvgStringLabels("play-current")' in player_js
    assert 'leftAlignSvgStringLabels("play-next")' in player_js
    assert "function sameFret" in player_js
    assert "function separateSameFretNextGrip" in player_js
    assert 'positionDisplay(next, "play-next", "next", 2)' in player_js
    assert 'group.setAttribute("transform", `translate(${offset} 0)`)' in player_js
    assert 'caption.textContent = "NEXT · SAME FRET"' in player_js
    assert "renderFretboard(current, next)" in player_js
    assert "const isPickup" in player_js
    assert "Pickup · Bar 1" in player_js
    assert "note.changes" in player_js
    assert '[String(string), controlsByString.get(Number(string))]' in player_js
    assert '.replace(/^(\\d+)(?=\\D)/, "$1 ")' in player_js
    assert 'label.setAttribute("text-anchor", "start")' in player_js
    assert "play-control-tag" not in player_js
    assert "play-string-control-tag" not in player_js
    assert "showStringActionLabels: true" in player_js
    assert 'maxFret: 24' in player_js
    assert "gripMarkup(current?.position, false)" in player_js
    assert "stringActionLabels" in player_js
    assert '${string}${control ? ` ${control}` : ""}' in player_js
    assert "justify-content: flex-start" in (REPO_ROOT / "ui" / "play-songs.css").read_text(encoding="utf-8")
    assert 'opacity: 0.8 !important' in (REPO_ROOT / "ui" / "play-songs.css").read_text(encoding="utf-8")


def test_play_songs_javascript_syntax() -> None:
    for path in ("ui/songs.js", "ui/play-song.js"):
        result = subprocess.run(
            ["node", "--check", path],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
