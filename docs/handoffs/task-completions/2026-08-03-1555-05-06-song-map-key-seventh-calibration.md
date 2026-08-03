# Song Map Key Refresh And Seventh Calibration

## Bug Summary

- Changing the Song key did not visibly update the NNS map until asynchronous
  re-decoding finished, making the control appear ineffective.
- Weak flat-seven energy could receive enough sequence-context support to turn
  repeated plain major/minor chords into dominant/minor sevenths.
- The Key control did not explain that it changes analysis context and NNS but
  does not transpose the recording.

## Lane Classification

- Mixed Lane 05 analysis calibration, Lane 06 Review UI, and QA regression
  coverage.

## Implementation

- The Song Map now updates its key/NNS context immediately, then safely applies
  the retained-score re-decode. Stale overlapping key changes cannot overwrite
  the newest selection.
- Added an evidence-margin calibration for dominant and minor sevenths against
  their matching triads. A clear added seventh remains a seventh; weak extension
  evidence falls back to the triad.
- Existing unedited v2 maps automatically receive calibration once on opening.
  Manually corrected maps are not silently replaced.
- Renamed the control to **Song key** and added visible copy explaining that it
  updates chord context and NNS without transposing audio.

## Files Changed

- `ui/practice-analysis-worker.js`
- `ui/setup-song.js`
- `ui/setup-song.html`
- `ui/play-songs.css`
- `tests/test_practice_analysis_v2.py`
- `tests/test_play_songs_ui.py`

## Tests And Checks

- Focused Play-Along analysis/UI/same-origin suite: `27 passed`.
- Full Python suite: `1574 passed in 80.15s`.
- `npm run check:js`: passed.
- `npm run check:assets`: passed for 1265 tracked files and 51 Explorer chunks.
- `npm run check:locks`: passed for five environments.
- Secret-pattern scan: passed.
- `git diff --check`: passed.
- Regression fixtures verify that weak seventh evidence resolves to a triad,
  clear seventh evidence remains a seventh, and legacy retained candidate
  scores are recalibrated during re-decode.

## Commit

- Implementation commit: `a50f7b4c` (`fix: recalibrate song map chord context`).

## Smoke Target

- Target type: protected staging user-song Review page.
- Exact browser URL: `https://test.steelguitarrag.com/setup/local-21785986-f95a-4374-9b1a-6abe5f3e1e89`
- Cache-busted URL: `https://test.steelguitarrag.com/setup/local-21785986-f95a-4374-9b1a-6abe5f3e1e89?v=song-map-calibration-a50f7b4c-20260803`
- Auth required: yes.
- Auth provider: Cloudflare Access.
- Local backend URL: `http://127.0.0.1:8771`.
- Expected backend port: `8771`.
- Expected git HEAD: `a50f7b4c`.
- Version endpoint result: not run; staging was not restarted.
- Root URL status: not rerun; staging was not restarted.
- API fallback status: not applicable to this browser-local analysis bug.
- Exact URL the user should test: the cache-busted URL above after staging activation.

## Smoke Result And Blocker

- Pre-fix authenticated browser inspection reproduced the excessive seventh
  map on the exact user project.
- Post-fix protected browser smoke is blocked before deployment. The repository
  documents the staging LaunchAgent name and port but does not document an
  approved staging restart/activation command. The autopilot protocol requires
  stopping when that command is missing or ambiguous.
- Production was not changed.

## Integration Status

- The canonical integration-status file already contains an unrelated
  uncommitted update. It remains parked and was not staged or overwritten, so
  this task could not safely add its required refresh there.

## Remaining Caveats

- Chord recognition remains probabilistic on dense full-band recordings.
- Existing manually corrected maps are intentionally excluded from automatic
  replacement; changing Song key still explicitly requests a fresh context
  decode.

## User Smoke Readiness

- Source and tests are ready.
- User smoke cannot continue on staging until an approved staging activation
  command is provided or documented and commit `a50f7b4c` is deployed.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-08-03-1555-05-06-song-map-key-seventh-calibration.md`

## Files That Must Not Be Staged

- `.venv`
- `docs/handoffs/task-completions/integration-status.md`
- Staging LaunchAgent files, environment files, release directories, logs,
  credentials, corpus/vector data, and unrelated worktree files.
