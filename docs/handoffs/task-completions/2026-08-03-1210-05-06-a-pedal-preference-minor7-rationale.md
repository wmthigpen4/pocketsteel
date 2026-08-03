# A-Pedal Preference and Minor-7 Rationale

## Task Summary

- Made the route generator canonicalize C to A whenever C affects only string
  5 on the selected grip and A produces the identical played pitches.
- Preserved the mechanically necessary C-pedal exception when string 10 is
  played as the flat seventh of a minor-7 shell.
- Added player guidance for that exception: C raises string 5 while leaving
  string 10 at the ♭7.
- Confirmed that fret-5 strings 5-8-10 spell F#-A-E for F#m7. Removing string
  10 would remove the E and reduce the grip to a minor dyad.

## Files Changed

- `steel_guitar_rag/song_practice.py`
- `ui/play-song.js`
- `ui/play-song-control-rationale-1.js`
- `ui/play-song.html`
- `tests/test_song_practice.py`
- `tests/test_play_songs_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-03-1210-05-06-a-pedal-preference-minor7-rationale.md`

## Tests and Checks

- Focused route, player UI, and same-origin suite: `47 passed`.
- Full Python suite: `1573 passed`.
- `npm run check:js`: passed.
- `git diff --check`: passed.

## Risks

- Low. The canonicalization runs only after proving the replacement produces
  identical pitches on every played string.
- The C-pedal exception remains when A would also raise played string 10 and
  change the requested harmony.

## Human Decision Needed

- None before staging smoke.

## Safe-to-Stage Exact Files

- `steel_guitar_rag/song_practice.py`
- `ui/play-song.js`
- `ui/play-song-control-rationale-1.js`
- `ui/play-song.html`
- `tests/test_song_practice.py`
- `tests/test_play_songs_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-03-1210-05-06-a-pedal-preference-minor7-rationale.md`

## Files That Must Not Be Staged

- `.venv`
- `docs/handoffs/task-completions/integration-status.md`

## Recommended Next Lane

- Exact-path commit, isolated staging release, and authenticated browser smoke
  on the current imported song.

## Commit Readiness

- Ready for exact-path commit and isolated staging release.
