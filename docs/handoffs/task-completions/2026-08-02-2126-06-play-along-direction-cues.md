# Play-Along Fret Direction Cues

## Task Summary

- Added a persistent movement badge to the upcoming-grip card.
- Higher fret numbers show an up arrow and the exact distance, lower fret
  numbers show a down arrow and the exact distance, and unchanged positions
  state `Same fret` explicitly.
- Kept the detailed fret-to-fret instruction below the grip and hid the new
  badge in Less Help mode with the other detailed movement guidance.
- Added accessible move descriptions that name the starting fret, ending fret,
  direction, and distance.

## Files Changed

- `ui/play-song.html`
- `ui/play-song.js`
- `ui/play-songs.css`
- `ui/play-song-movement-20260802.js`
- `ui/play-songs-movement-20260802.css`
- `tests/test_play_songs_ui.py`
- `docs/handoffs/task-completions/2026-08-02-2126-06-play-along-direction-cues.md`

## Tests And Checks Run

- `npm run check:js` — passed.
- `.venv/bin/pytest -q tests/test_play_songs_ui.py tests/test_practice_tools.py tests/test_song_practice.py` — `33 passed`.
- `.venv/bin/pytest -q` — `1559 passed`.
- `git diff --check` — passed.

## Risks

- Low. The change is presentational and derives its state from the already
  selected current and next fret positions.
- In musical neck terminology, higher fret numbers are labeled `up` and lower
  fret numbers are labeled `down`.

## Human Decision Needed

- None before staging smoke. Product feedback can adjust the wording or icon
  treatment after seeing it on an imported song.

## Safe-To-Stage Exact File List

- `ui/play-song.html`
- `ui/play-song.js`
- `ui/play-songs.css`
- `ui/play-song-movement-20260802.js`
- `ui/play-songs-movement-20260802.css`
- `tests/test_play_songs_ui.py`
- `docs/handoffs/task-completions/2026-08-02-2126-06-play-along-direction-cues.md`

## Files That Must Not Be Staged

- `.venv`
- Local release directories, LaunchAgents, environment files, logs, and
  credentials.

## Recommended Next Lane

- Lane 01 exact-path commit, then Lane 12 staging deployment and browser smoke
  at the current imported-song URL.

## Commit Readiness

- Ready for exact-path staging and commit.
