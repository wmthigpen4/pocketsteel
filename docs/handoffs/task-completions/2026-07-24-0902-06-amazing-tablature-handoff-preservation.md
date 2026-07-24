# Amazing Tablature handoff preservation

## Task summary

Protected-preview browser smoke found that Fretboard Explorer generated the intended Amazing Tablature deep link, including its selected chord, but Melody Studio dropped that chord when it synchronized the visible phrase field before submission. The receiver now preserves per-event chord context, note direction, and octave edits while reparsing visible phrase text.

This is a scoped user-smoke fix within the approved Amazing Tablature productization run. No corpus, training, validation, sealed-test, retrieval, auth, deployment-policy, or source files were opened or changed.

## Files changed

- `ui/melody-workbench.js`
  - Added `mergePhraseEdits`.
  - Preserved incoming chord context while synchronizing visible phrase edits.
- `ui/melody-workbench.html`
  - Bumped the Melody Studio script cache tag.
- `tests/test_melody_workbench_ui.py`
  - Added a regression proving chord, direction, and octave context survive phrase synchronization.
- `tests/test_same_origin_smoke_server.py`
  - Updated the exact cache-tag assertion.
- This handoff.

No files were deleted.

## Tests and checks

- `node --check ui/melody-workbench.js` — pass.
- `.venv/bin/pytest -q tests/test_melody_workbench_ui.py tests/test_same_origin_smoke_server.py tests/test_song_projects_ui.py tests/test_frontend_answer_ui.py` — 73 passed.
- `git diff --check` — pass.

## Integration notes

Explorer and Song Practice handoffs may supply a chord alongside one or more melody notes. Melody Studio must retain that chord in each matching event so `three_voice` can resolve a validated chord-melody grip instead of falling back to a single note.

The protected preview was still serving commit `110a1fe` during the discovery smoke. A new exact release and protected-preview smoke are required after this fix is committed.

## Risk assessment

Low. The change only preserves already-parsed event context while reparsing the same visible notes. If no chord is present, behavior is unchanged. Rollback is the scoped commit revert.

## Human decision needed

No product decision. The existing activation command requires the user's administrator authentication.

## Safe-to-stage exact file list

- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-24-0902-06-amazing-tablature-handoff-preservation.md`

## Files that must not be staged

- `corpus-private/`
- validation or sealed-test artifacts
- generated reports
- all unrelated dirty or untracked handoffs
- `docs/handoffs/task-completions/integration-status.md` in the implementation commit

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 12 exact-release activation and authenticated protected-preview smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the five paths listed above, create an exact detached release, activate it with the documented LaunchDaemon workflow, and verify the Explorer-to-three-voice handoff in the protected preview.
