# Confidence-First Song Map Status

## Task Summary

- Removed the repeated **Accepted** label from completed Song Map bars.
- Completed bars now show concise confidence language such as **83% confident**.
- Bars that still require action show **83% confidence · Needs attention**.
- The selected-measure badge uses the same confidence-first language.
- Reference-confirmed or reference-resolved states remain visible as additional
  context when they exist.
- No analysis values, review decisions, or saved project data are changed.

## Files Changed

- `ui/setup-song.js`
- `ui/setup-song-review-v2-15.js`
- `ui/setup-song.html`
- `tests/test_play_songs_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-03-1157-06-confidence-first-song-map-status.md`

## Tests and Checks

- Focused Review UI and same-origin server suite: 19 passed.
- JavaScript syntax checks: passed.
- `git diff --check`: passed.

## Risks

- Low. This is a display-only change; review state remains unchanged.

## Human Decision Needed

- None before staging smoke.

## Safe-to-Stage Exact Files

- `ui/setup-song.js`
- `ui/setup-song-review-v2-15.js`
- `ui/setup-song.html`
- `tests/test_play_songs_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-03-1157-06-confidence-first-song-map-status.md`

## Files That Must Not Be Staged

- `.venv`
- `docs/handoffs/task-completions/integration-status.md`

## Recommended Next Lane

- Exact-path commit, isolated staging release, and authenticated browser smoke.

## Commit Readiness

- Ready for exact-path commit.
