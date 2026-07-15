# Melody Studio G/GG control fix QA

## Task summary

- Verified the scoped G/GG control-resolution and safe-error-display fix against the exact collision shape, full-song arrangement behavior, related frontend/API behavior, and the complete regression suite.
- Confirmed the fix preserves distinct G and GG controls and does not rename or mutate the saved copedent.
- Confirmed no auth, corpus, Chroma, source, deployment-policy, or private-training behavior changed.

## Files changed

- Created this QA handoff only.

## Tests and checks

- `tests/test_copedent_transfer.py -k 'g_label or distinct_g_and_gg'` — 2 passed.
- `tests/test_frontend_answer_ui.py -k 'safe_api_validation_error or posts_and_normalizes_melody_exercise'` — 2 passed.
- Relevant seven-file backend/frontend/API regression suite — 446 passed.
- `.venv/bin/python -m pytest -q` — 1,133 passed.
- `npm run check:js` — passed.
- Ruff — passed.
- `git diff --check` — passed.

## Integration notes

- Exact regression: a complete C-major song now arranges successfully for a saved E9 profile containing player-facing G and GG controls where internal arranger code G previously collided.
- The safe API error test confirms actionable server validation text is displayed; malformed/non-JSON responses retain the generic HTTP fallback.
- Protected browser verification remains the post-commit Lane 12 gate.

## Risk assessment

- Low. The identity boundary is narrower, all relevant and full tests pass, and deterministic effect validation remains unchanged.

## Human decision needed

- No. The user approved this Autopilot bug fix.

## Safe-to-stage exact file list

- `pocketsteel/copedent_transfer.py`
- `pocketsteel/melody_arranger.py`
- `ui/answer-client.js`
- `ui/melody-workbench.html`
- `tests/test_copedent_transfer.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_workbench_ui.py`
- `docs/handoffs/task-completions/2026-07-14-2036-05-melody-g-gg-control-fix.md`
- `docs/handoffs/task-completions/2026-07-14-2037-15-melody-g-gg-control-fix-qa.md`

## Files that must not be staged

- All private/account data and all unrelated dirty/untracked paths, including `integration-status.md`.

## Recommended next lane

- Lane 01 exact-path commit, followed by Lane 12 protected-preview update and authenticated browser smoke of the reported song.

## Commit readiness

Safe to commit

## Suggested next step

- `Lane 01: Commit only the exact approved paths, then Lane 12: verify When the Saints Go Marching In with the saved G/GG copedent.`
