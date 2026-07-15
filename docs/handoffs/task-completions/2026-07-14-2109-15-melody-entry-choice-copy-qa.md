# QA — Melody Studio Entry Choice Copy

## Task summary

- Verified stable entry-tool names in both initial and replace-current-melody states.
- Confirmed replacement context is carried by unique supporting text rather than three identical primary labels.
- Confirmed the explicit replacement confirmation remains intact.
- No code beyond the scoped implementation and regression files was changed during QA.

## Files changed

- Created this QA handoff.
- Reviewed `ui/melody-workbench.js`, `ui/melody-workbench.html`, `tests/test_melody_workbench_ui.py`, and `tests/test_same_origin_smoke_server.py`.

## Tests and checks

- Direct presentation-helper assertions cover all five entry paths and both normal/replacement context.
- Focused Melody/frontend/static suite: 62 passed.
- Full suite: 1,133 passed.
- JavaScript syntax and repository JavaScript checks: passed.
- Scoped `git diff --check`: passed.
- One first full-suite run found only the intentionally changed cache-key expectation; after the exact related assertion was updated, both focused and full suites passed.

## Integration notes

- Browser smoke must verify the group after a song is loaded, because that is the state where the former repetition appeared.
- Pass criteria: each primary name appears once, `Replace melody` is absent from the choice buttons, helper text communicates alternate-entry consequences, and no warning/error or overflow regression appears.

## Risk assessment

- Risk: low.
- No navigation target, state transition, confirmation logic, or stored data changed.

## Human decision needed

- No.

## Safe-to-stage exact file list

- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-14-2109-06-melody-entry-choice-copy.md`
- `docs/handoffs/task-completions/2026-07-14-2109-15-melody-entry-choice-copy-qa.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` and all unrelated dirty/untracked, private, account-data, corpus, source-inbox, vector, database, brand/design, deployment, auth, and historical handoff files.

## Recommended next lane

- Lane 01 Repo Steward.

## Commit readiness

Safe to commit

## Suggested next step

- Proceed with exact-path commit, isolated preview restart, and authenticated review-state browser smoke.
