from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_songs_catalog_and_player_keep_existing_visual_language() -> None:
    songs = (REPO_ROOT / "ui" / "songs.html").read_text(encoding="utf-8")
    player = (REPO_ROOT / "ui" / "play-song.html").read_text(encoding="utf-8")
    setup = (REPO_ROOT / "ui" / "setup-song.html").read_text(encoding="utf-8")
    css = (REPO_ROOT / "ui" / "play-songs.css").read_text(encoding="utf-8")

    assert "Steel Guitar RAG" in songs and "Steel Guitar RAG" in player
    assert "Pocket Steel" not in songs + player + css
    assert "Starter Songs" in songs
    assert "My Tracks" in songs
    assert "Add a Song" in songs
    assert "Audio stays in this browser" in songs
    assert 'class="play-cue is-current"' in player
    assert 'class="play-cue is-next"' in player
    assert player.index('class="play-cue is-current"') < player.index('class="play-cue is-next"')
    assert "Preview grips" in player
    assert "Repeat the saved bar range" in player
    assert "Full song" in player
    assert "Less help" in player
    assert "Song Map" in player
    assert 'id="review-song-map"' in setup
    assert 'id="review-editor"' in setup
    assert 'id="reference-panel"' in setup
    assert 'id="validate-reference"' in setup
    assert 'id="review-show-chords"' in setup
    assert 'id="review-show-nns"' in setup
    assert "The app does not fetch this page" in setup
    assert "coral bars need attention" in setup
    assert ">NNS<" in player
    assert "Count-in" in player and "Metronome" in player
    assert 'id="play-attribution"' in player
    assert 'id="play-key"' in player
    assert 'id="next-direction"' in player
    assert 'id="next-move"' not in player
    assert 'id="play-route"' in player
    assert 'id="play-objective"' in player
    assert 'id="current-melody"' in player
    assert 'id="next-melody"' in player
    assert 'id="play-why"' in player
    assert "Why this position?" in player
    assert "--gold: #f0bf69" in css
    assert '--lesson: Georgia, "Times New Roman", serif' in css
    assert ".play-fretboard [data-highlight-id=\"play-next\"]" in css
    assert ".play-fretboard .play-melody-tag" in css
    assert ".play-why" in css
    assert "filter: grayscale(0.6)" in css
    assert "@media (orientation: landscape) and (max-height: 560px)" in css
    assert ".play-fretboard svg { max-height: 205px; }" in css
    assert ".song-map-dialog" in css


def test_device_import_is_opfs_only_and_player_is_audio_clock_driven() -> None:
    songs_js = (REPO_ROOT / "ui" / "songs.js").read_text(encoding="utf-8")
    player_js = (REPO_ROOT / "ui" / "play-song.js").read_text(encoding="utf-8")
    tools_js = (REPO_ROOT / "ui" / "practice-tools.js").read_text(encoding="utf-8")

    assert "navigator.storage.getDirectory" in tools_js
    assert 'storage: "opfs"' in songs_js
    assert 'uploaded: false, networkAllowed: false' in songs_js
    assert "MAX_BYTES = 250 * 1024 * 1024" in songs_js
    assert "MAX_DURATION_SECONDS = 15 * 60" in songs_js
    assert "CURRENT_ANALYSIS_CALIBRATION_VERSION = 11" in songs_js
    assert "function analysisIsCurrent" in songs_js
    assert "Analysis update required" in songs_js
    import_slice = songs_js[songs_js.index("async function importTrack"):songs_js.index("function songCard")]
    assert "fetch(" not in import_slice
    assert "XMLHttpRequest" not in import_slice
    assert "sendBeacon" not in import_slice
    assert "audio.currentTime * 1000" in player_js
    assert "track?.beatTimesMs" in player_js
    assert "ACCOUNT_COPEDENT_STARTUP_BUDGET_MS = 1500" in player_js
    assert "async function configurePlayAlongCopedent" in player_js
    assert "await Promise.race" in player_js
    assert "await global.STEEL_RAG_COPEDENTS?.configureAccount?.(session" not in player_js
    assert "playAlongCopedentContext" in player_js
    assert "function showLoadingState" in player_js
    assert "app.hidden = false" in player_js
    assert 'responseMode: "play_along_lessons"' in player_js
    assert "const catalogRequest = fetch" in player_js
    assert 'if (projectId.startsWith("local-")) await configurePlayAlongCopedent();' in player_js
    assert "prepareTrackShell();" in player_js
    assert "global.STEEL_RAG_COPEDENTS?.requestContext?.()" in player_js
    assert "session?.features?.accountCopedents && requestContext?.profileId" in player_js
    assert "track.recordingCredit" in player_js
    assert "track.licenseUrl" in player_js
    assert "route?.positions || track.authoredRoute" in player_js
    assert "function selectedChordRoute" in player_js
    assert "Move the bar" not in player_js
    assert "Source &amp; license" in songs_js
    assert 'track.playAlongReady === true' in songs_js
    assert "track.availabilityLabel" in songs_js
    assert 'track.playAlongReady !== true' in player_js
    assert "CURRENT_ANALYSIS_CALIBRATION_VERSION = 11" in player_js
    assert 'global.location.replace(`/setup/${encodeURIComponent(project.id)}`)' in player_js
    assert "This song map needs the current local analysis" in player_js
    assert "setInterval" not in player_js
    assert "function leftAlignSvgStringLabels" in player_js
    assert 'leftAlignSvgStringLabels("play-current")' in player_js
    assert 'leftAlignSvgStringLabels("play-next")' in player_js
    assert "function sameFret" in player_js
    assert "function samePosition" in player_js
    assert "function movementIndicator" in player_js
    assert 'symbol: change > 0 ? "↑" : "↓"' in player_js
    assert 'label: "Same fret"' in player_js
    assert "renderMovementIndicator(current, next)" in player_js
    assert "function movementInstruction" not in player_js
    assert "function addFretMovementArrow" in player_js
    assert 'label.textContent = distance >= 4 ? `MOVE ${distance}` : `SLIDE ${distance}`' in player_js
    assert "addFretMovementArrow(displayedCurrent?.position, visibleNext?.position)" in player_js
    assert "centerSameFretCurrentGrip();" in player_js
    assert "function separateSameFretNextGrip" in player_js
    assert 'positionDisplay(visibleNext, "play-next", "next", 2)' in player_js
    assert "const visibleNext = assistanceReduced || displayedCurrent === next || samePosition(displayedCurrent?.position, next?.position) ? null : next" in player_js
    assert "C is intentional: it raises string 5 while leaving string 10 at the ♭7." in player_js
    assert 'const offset = sideOffset - renderOffsetX(group);' in player_js
    assert 'group.setAttribute("transform", `translate(${offset} 0)`)' in player_js
    assert 'caption.textContent = "NEXT · SAME FRET"' in player_js
    assert "renderFretboard(current, next, timeMs)" in player_js
    assert 'fetch("/api/amazing-tablature/arrange"' in player_js
    assert "track?.melodyTimeline" in player_js
    assert 'label: "Follow the Melody"' in player_js
    assert '"Chord Foundation · Move the Bar"' in player_js
    assert "Chord Foundation · Stay Near Fret ${routeOption.homeFret ?? 3}" in player_js
    assert 'routePreference: "move_bar"' in player_js
    assert 'routePreference: "stay_near"' in player_js
    assert "request.routePreference = route?.routePreference" in player_js
    assert 'label: "Full Chord Melody · Advanced"' in player_js
    assert "payload?.playAlongLessons" in player_js
    assert 'playAlongOpeningChordMelodyEvents: 3' in player_js
    assert "lessonPlans" in player_js
    assert "position.melodyString" in player_js
    assert "★ MELODY" in player_js
    assert "renderWhyDetails(current)" in player_js
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
    assert 'class="play-grip__strings"' in player_js
    assert "justify-content: flex-start" in (REPO_ROOT / "ui" / "play-songs.css").read_text(encoding="utf-8")
    assert "grid-template-columns: repeat(2, minmax(0, 430px))" in (REPO_ROOT / "ui" / "play-songs.css").read_text(encoding="utf-8")
    assert "flex-direction: column" in (REPO_ROOT / "ui" / "play-songs.css").read_text(encoding="utf-8")
    assert ".play-direction__arrow" in (REPO_ROOT / "ui" / "play-songs.css").read_text(encoding="utf-8")
    assert ".play-fret-move-arrow__line" in (REPO_ROOT / "ui" / "play-songs.css").read_text(encoding="utf-8")
    assert 'opacity: 0.8 !important' in (REPO_ROOT / "ui" / "play-songs.css").read_text(encoding="utf-8")


def test_play_songs_javascript_syntax() -> None:
    for path in (
        "ui/songs.js", "ui/setup-song.js", "ui/play-song.js", "ui/practice-tools.js",
        "ui/practice-transport.js", "ui/practice-analysis-worker.js",
        "ui/practice-reference-validation.js",
    ):
        result = subprocess.run(
            ["node", "--check", path],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr


def test_review_automatically_replaces_legacy_map_and_keeps_timing_preview() -> None:
    setup_js = (REPO_ROOT / "ui" / "setup-song.js").read_text(encoding="utf-8")
    setup_html = (REPO_ROOT / "ui" / "setup-song.html").read_text(encoding="utf-8")

    assert "Legacy Song Map" not in setup_js
    assert "Legacy chord map shown" not in setup_js
    assert "function upgradeLegacyAnalysis(useExistingKeyHint = true)" in setup_js
    assert "if (needsUpgrade) await upgradeLegacyAnalysis(true)" in setup_js
    assert 'project.timeline = { ...result.analysis, confirmationState: "detected" }' in setup_js
    assert 'setUpgradeVisibility(true)' in setup_js
    assert 'The older map is not offered as an alternative.' in setup_js
    assert "Improved Analysis Preview" in setup_js
    assert "function activeTimeline()" in setup_js
    assert "if (legacyTimeline()) return false" in setup_js
    assert "This preview has not replaced your saved map" in setup_js
    assert 'loadProviderReference("user-supplied"' in setup_js
    assert "Reference-confirmed" in setup_js
    assert "function chordForReview" in setup_js
    assert 'tools.chordForDisplay' in setup_js
    assert 'No chord means there is no sustained harmony' in setup_js
    assert 'e9-fretboard-explorer.html?mode=chord' in setup_js
    assert 'The flat-seven chord sits one whole step below the 1 chord' in setup_js
    assert 'if (event.key !== "Enter") return' in setup_js
    assert 'referencePanel.hidden = false' not in setup_js
    assert '`${confidenceLabel} confident${externalState ? ` · ${externalState}` : ""}`' in setup_js
    assert 'confidence · Needs attention' in setup_js
    assert 'externalState || "Accepted"' not in setup_js
    assert 'tools.saveSession(practiceSession)' in setup_js
    assert "Chord names (editing)" in setup_js
    assert "Nashville number" in setup_js
    assert "keyRegions: immediateRegions" in setup_js
    assert "Song Map updated for ${requestedKey} ${requestedMode}. The audio was not transposed." in setup_js
    assert "qualityCalibrationVersion" in (REPO_ROOT / "ui" / "practice-analysis-worker.js").read_text(encoding="utf-8")
    assert "Updates the first section and NNS; it does not transpose the audio." in setup_html
    assert "Starting key" in setup_html
    assert 'id="review-key-journey"' in setup_html
    assert "function updateSectionKey" in setup_js
    assert "function toggleKeyBoundary" in setup_js
    assert "analysisClient.redecodeRegions" in setup_js
    assert "preserveManualChordEdits" in setup_js
    assert "seventhEvidenceTeaching" in setup_js
    assert "Audio ♭7 evidence" in setup_js
    assert 'qualityCalibrationVersion || 0) < 11) await upgradeLegacyAnalysis(false)' in setup_js
    assert "New key ·" in setup_js
    assert 'event.symbol === "N.C." ? "No chord"' in setup_js
    assert 'NO\\s+CHORD' in setup_js
    assert "calibrateRelativeMinorQualities" in (REPO_ROOT / "ui" / "practice-analysis-worker.js").read_text(encoding="utf-8")


def test_play_along_uses_active_section_key_for_nns_and_key_markers() -> None:
    player_js = (REPO_ROOT / "ui" / "play-song.js").read_text(encoding="utf-8")
    player_html = (REPO_ROOT / "ui" / "play-song.html").read_text(encoding="utf-8")
    assert "function keyContextForBar" in player_js
    assert "keyRegions: timeline.keyRegions || []" in player_js
    assert "displayedChord(chord.symbol, bar.barNumber)" in player_js
    assert "activeKey.key" in player_js
    assert "New key ·" in player_js
    assert 'id="play-key-journey"' in player_html
    assert "Current key" in player_html
    assert "practiceTools.chartTextForTimeline(timeline.barStartsMs, timelineChords)" in player_js


def test_play_along_surfaces_key_changes_in_now_and_next_cues() -> None:
    player_js = (REPO_ROOT / "ui" / "play-song.js").read_text(encoding="utf-8")
    player_html = (REPO_ROOT / "ui" / "play-song.html").read_text(encoding="utf-8")
    player_css = (REPO_ROOT / "ui" / "play-songs.css").read_text(encoding="utf-8")
    assert 'id="current-key-change"' in player_html
    assert 'id="next-key-change"' in player_html
    assert '"Key change"' in player_js
    assert '"Key change ahead"' in player_js
    assert "activeKey.region?.startBar === currentBar" in player_js
    assert ".play-key-change.is-ahead" in player_css
    assert ".play-cue.has-key-change" in player_css
    assert "play-song-analysis-calibration-v7.js" in player_html
    assert "play-songs-rest-size-v3.css" in player_html


def test_play_along_keeps_a_fretboard_position_visible_during_no_chord() -> None:
    player_js = (REPO_ROOT / "ui" / "play-song.js").read_text(encoding="utf-8")
    player_html = (REPO_ROOT / "ui" / "play-song.html").read_text(encoding="utf-8")
    assert "function noChordEvent" in player_js
    assert "function fretboardAnchorEvent" in player_js
    assert "const displayedCurrent = fretboardAnchorEvent(current, next, timeMs)" in player_js
    assert "renderFretboard(current, next, timeMs)" in player_js
    assert 'return "Rest · keep your place and listen."' in player_js
    assert 'currentIsNoChord ? "No chord"' in player_js
    assert '"<span>No chord</span>"' in player_js
    assert 'classList.toggle("is-no-chord", currentIsNoChord)' in player_js
    assert ".play-cue__chord.is-no-chord" in (REPO_ROOT / "ui" / "play-songs.css").read_text(encoding="utf-8")
    assert "play-song-analysis-calibration-v7.js" in player_html
