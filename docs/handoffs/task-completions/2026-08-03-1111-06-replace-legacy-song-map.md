# Replace Legacy Song Map With Current Analysis

## Task Summary

- Removed the legacy Song Map as a reviewable alternative.
- Existing projects with `timeline.analysisVersion < 2` now enter a single
  **Updating Song Map** state when Review opens.
- The app runs the current key-aware analysis locally and automatically saves
  the v2 timeline before revealing the Review controls and Song Map.
- If the local analysis fails, the old map remains stored for recovery but is
  not displayed or offered for Play Along; the only action is **Try update
  again**.
- Current v2 projects open normally. Tempo or meter edits retain their separate
  preview-and-apply safety flow because that flow protects an already-current
  reviewed map rather than offering an obsolete analysis method.

## Files Changed

- `ui/setup-song.html`
- `ui/setup-song.js`
- `ui/setup-song-review-v2-11.js`
- `tests/test_play_songs_ui.py`
- `tests/test_practice_analysis_v2.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-03-1111-06-replace-legacy-song-map.md`

## Tests and Checks

- Focused Review/analysis/server suite — 26 passed.
- Full Python suite — 1,572 passed.
- Asset-size budget — passed for 1,250 tracked files and 51 Explorer chunks.
- JavaScript syntax checks — passed.
- `git diff --check` — passed.
- Protected-preview `/api/version` — `e9c5bc91` during functional smoke.
- Protected-preview browser smoke on the existing 4:50 legacy project — passed:
  - opened directly into **Updating Song Map**, with the legacy grid hidden;
  - completed local analysis as C# major, 4/4, 157 BPM, Method v2;
  - automatically saved and revealed a 203-bar current **Song Map**;
  - exposed no **Legacy Song Map**, reanalyze-method, or keep-old-map choice;
  - retained the per-song NNS preference; and
  - reopened directly as Method v2 without repeating the upgrade.

## Risks

- The first Review visit for an old project must complete an on-device analysis
  before the map can be edited or played. Long recordings may take noticeable
  time on slower devices.
- A failed upgrade intentionally blocks use of the obsolete map. Its project
  data is retained so retrying remains non-destructive.

## Human Decision Needed

- None for implementation. User smoke should confirm the one-time upgrade
  progress and resulting current Song Map on a real legacy recording.

## Safe-to-Stage Exact Files

- `ui/setup-song.html`
- `ui/setup-song.js`
- `ui/setup-song-review-v2-11.js`
- `tests/test_play_songs_ui.py`
- `tests/test_practice_analysis_v2.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-08-03-1111-06-replace-legacy-song-map.md`

## Files That Must Not Be Staged

- `.venv`
- `docs/handoffs/task-completions/integration-status.md`

## Recommended Next Lane

- Lane 01 for exact-path commit, then Lane 12 for the isolated staging release
  and browser smoke.

## Commit Readiness

- Implemented and committed. The functional staging smoke ran on `e9c5bc91`;
  the final commit differs only by this verification record.
