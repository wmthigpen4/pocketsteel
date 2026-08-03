# Review Page Style Recovery

## Task Summary

- Fixed the protected Review page rendering its new Song Map markup with an
  older cached stylesheet.
- Added cache-safe stylesheet and Review-script asset filenames so the visual
  layout cannot fall back to the legacy table presentation.
- Reworked the page hierarchy: the page heading is now **Review Song**, the
  recording title is a separate secondary heading, and the instructions now
  explain the user action directly.
- Prevented Play Along and Review action labels from wrapping into narrow
  circular buttons.
- Preserved the visual Song Map, selected-bar editor, local project data, and
  chord-analysis behavior.

## Files Changed

- `ui/play-songs.css`
- `ui/play-songs-review-v2.css`
- `ui/setup-song.html`
- `ui/setup-song.js`
- `ui/setup-song-review-v2-4.js`
- `docs/handoffs/task-completions/2026-08-03-1012-review-page-style-recovery.md`

## Verification

- `node --check ui/setup-song.js` — passed.
- `.venv/bin/pytest -q tests/test_play_songs_ui.py tests/test_same_origin_smoke_server.py`
  — 18 passed.
- `npm run check:assets` — passed for 1233 tracked files and 51 Explorer chunks.
- `npm run check:js` — passed.
- `.venv/bin/pytest -q` — 1567 passed in 79.06s.
- `git diff --check` — passed.
- Protected staging browser smoke — wide layout shows the four-card analysis
  summary, four-column Song Map, and adjacent selected-bar editor; narrow layout
  shows a two-column tile map and stacked controls with unwrapped actions.

## Files That Must Not Be Staged

- `.venv`
- `docs/handoffs/task-completions/integration-status.md`

## Risk

- Low. This is a presentation and cache-boundary correction. It does not alter
  saved projects, analysis results, production, DNS, Access, or Tunnel rules.
