# Melody Studio Songbook-First Start Choice

## Task summary

- Requested: put **Browse songbook** first in the list under **Add a melody**.
- Completed: Browse songbook is now the first visible starting choice, followed by Type or tap notes, Record or upload audio, Staff editor, and Import music.
- Intentionally unchanged: Type or tap notes remains the selected default input method. The catalog does not open automatically merely because its control is first.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lanes: `15 QA / Answer Eval`, `01 Repo Steward`, then `12 Self-Hosted Deployment`
- Task mode: YELLOW UI-flow adjustment, explicitly approved by the user's direct request and covered by the Autopilot loop.

## Files changed

- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- This handoff.

No files were deleted or generated.

## Tests and checks

- `node --check ui/melody-workbench.js` — passed.
- `.venv/bin/python -m pytest -q tests/test_melody_workbench_ui.py tests/test_same_origin_smoke_server.py` — **16 passed**.
- `.venv/bin/python -m pytest -q` — **971 passed**.
- Scoped `git diff --check` — passed.

## Integration notes

- A focused static regression verifies that catalog precedes phrase and phrase precedes audio.
- The same test verifies that Type or tap notes retains `aria-pressed="true"` initially.
- No JavaScript, API, catalog, arranger, score, tab, fretboard, auth, corpus, or deployment behavior changed.

## Risk assessment

- Low. This is a markup-order change with an explicit ordering regression test.
- Rollback: revert the scoped implementation commit.

## Human decision needed

- No.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `docs/handoffs/task-completions/2026-07-13-1254-06-songbook-first-start-choice.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` in the implementation commit.
- Existing protected-preview coordination handoffs.
- All unrelated corpus, source-inbox, private, public, brand, Neon Sign, generated, deployment, auth, config, and design files.

## Recommended next lane

- Lane 01 exact-path commit, followed by Lane 12 protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

- Commit the exact three files above, restart the protected preview, and verify the visible Add a melody order at one new cache-busted URL.
