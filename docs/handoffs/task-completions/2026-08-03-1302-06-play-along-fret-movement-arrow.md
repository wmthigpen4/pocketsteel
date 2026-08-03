# Play-Along Fret Movement Arrow

## Task Summary

- Removed the sentence-length upcoming movement instruction beneath the Next
  chord card.
- Added a directional arrow directly to the fretboard whenever the next grip
  moves to another fret.
- Short moves use a gold `SLIDE` cue with the fret distance. Moves of four or
  more frets use a coral `MOVE` cue so large jumps are distinguishable at a
  glance.
- Preserved the existing compact Same Fret indicator for pedal, lever, or grip
  changes that do not move the bar.

## Files Changed

- `ui/play-song.html`
- `ui/play-song.js`
- `ui/play-song-fret-arrow-1.js`
- `ui/play-songs.css`
- `ui/play-songs-fret-arrow-1.css`
- `tests/test_play_songs_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-03-1302-06-play-along-fret-movement-arrow.md`

## Tests and Checks Run

- Focused player and same-origin tests: `19 passed`.
- Full Python suite: `1573 passed`.
- `npm run check:js`: passed.
- `git diff --check`: passed.

## Risks

- Low. The arrow is a player-only SVG overlay derived from the already chosen
  current and next fret positions; it does not alter the musical route.
- Same-position and same-fret changes intentionally do not receive a fret
  movement arrow.

## Human Decision Needed

- None before staging smoke. User smoke can tune the four-fret threshold or
  the `SLIDE`/`MOVE` labels after seeing them with real recordings.

## Safe-to-Stage Exact Files

- `ui/play-song.html`
- `ui/play-song.js`
- `ui/play-song-fret-arrow-1.js`
- `ui/play-songs.css`
- `ui/play-songs-fret-arrow-1.css`
- `tests/test_play_songs_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-03-1302-06-play-along-fret-movement-arrow.md`

## Files That Must Not Be Staged

- `.venv`
- `docs/handoffs/task-completions/integration-status.md`

## Recommended Next Lane

- Lane 01 exact-path commit, then Lane 12 isolated staging deployment and
  authenticated browser smoke on the reported imported song.

## Commit Readiness

- Ready for exact-path commit and isolated staging release.
