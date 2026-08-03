# Song Review Teaching and Targeted Public Check

## Task Summary

- Replaced the unexplained `N.C.` display with the plain-language label
  **No chord** while preserving `N.C.` as the stored project symbol.
- Replaced ASCII Nashville accidentals such as `b7` with musical symbols such
  as `♭7`.
- Added selected-measure teaching copy. In A major, a selected G chord now
  explains that `♭7` is G and that the flat-seven sits one whole step below the
  1 chord.
- Added a direct selected-chord link to the existing E9 virtual fretboard chord
  finder. The link carries the song key, chord root, and chord quality so the
  player can explore the exact harmony without reconstructing it manually.
- Chord edits now commit with Enter in addition to the existing change/blur
  behavior, making keyboard review explicit and reliable.
- Cross-checked the current Sammy Kershaw recording against public chord charts.
  The sources agree on A major and the core vocabulary A, D, E, F#m, and G.
  This supports a targeted review of low-confidence chord quality, but it is not
  treated as proof of exact bar timing.
- No lyrics or complete chart text were copied into the project or repository.

## Files Changed

- `ui/practice-tools.js`
- `ui/practice-tools-review-teaching-1.js`
- `ui/setup-song.js`
- `ui/setup-song-review-v2-12.js`
- `ui/setup-song-review-v2-13.js`
- `ui/setup-song.html`
- `ui/play-songs.css`
- `ui/play-songs-review-v6.css`
- `ui/songs.html`
- `ui/play-song.html`
- `tests/test_same_origin_smoke_server.py`
- `tests/test_practice_tools.py`
- `tests/test_play_songs_ui.py`
- `docs/handoffs/task-completions/2026-08-03-1134-06-song-review-teaching-and-public-check.md`

## Tests and Checks

- Focused Practice Tools and Review UI suite: 8 passed.
- Full Python suite: 1,572 passed.
- Asset-size budget: passed for 1,252 tracked files and 51 Explorer chunks.
- JavaScript syntax checks: passed.
- `git diff --check`: passed.

## Public Verification Scope

- Exact Ultimate Guitar page supplied by the user:
  `https://tabs.ultimate-guitar.com/tab/sammy-kershaw/queen-of-my-double-wide-trailer-chords-2260203`
- Independent corroboration was also found on E-Chords, Songsterr, ChordU, and
  other public chord-index results.
- The safe correction is limited to uncertain chord-quality events: normalize
  uncertain E7 detections to E and uncertain F#m7 detections to F#m. Uncertain
  A, D, and G detections can be accepted unchanged where the audio-derived
  timing remains intact.
- Accepted No chord measures are not changed by this source check because the
  public charts do not establish recording-specific silence, speech, pickup, or
  fade timing.

## Risks

- A public chord chart establishes vocabulary and broad progression context,
  not recording-specific bar alignment. It must not overwrite audio-derived
  timing or strongly supported chromatic events automatically.
- The fretboard handoff supports one selected chord. Two-chord measures retain
  normal editing and playback but do not show a single ambiguous explorer link.

## Safe-to-Stage Exact Files

- `ui/practice-tools.js`
- `ui/practice-tools-review-teaching-1.js`
- `ui/setup-song.js`
- `ui/setup-song-review-v2-12.js`
- `ui/setup-song-review-v2-13.js`
- `ui/setup-song.html`
- `ui/play-songs.css`
- `ui/play-songs-review-v6.css`
- `ui/songs.html`
- `ui/play-song.html`
- `tests/test_practice_tools.py`
- `tests/test_play_songs_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-03-1134-06-song-review-teaching-and-public-check.md`

## Files That Must Not Be Staged

- `.venv`
- `docs/handoffs/task-completions/integration-status.md`

## Recommended Next Lane

- Exact-path commit, then isolated staging release and authenticated browser
  smoke on the saved local project.

## Commit Readiness

- Ready for exact-path commit.
