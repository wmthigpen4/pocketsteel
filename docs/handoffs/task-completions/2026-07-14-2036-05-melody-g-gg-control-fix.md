# Melody Studio G/GG control fix

## Task summary

- Fixed the protected-preview user-smoke failure where a valid saved copedent with distinct player labels `G` and `GG` could produce an opaque HTTP 400.
- Preserved both player-defined labels and their distinct half/full mechanical effects.
- Separated internal arranger-code resolution from player-facing alias resolution. Internal render code `G` now resolves by its exact canonical mechanical identity before any user alias lookup.
- Updated the answer client to display the bounded, same-origin validation message returned by the API instead of discarding it and showing only the HTTP status.
- Added a fresh Melody Studio answer-client asset key.
- Did not mutate the saved copedent, weaken deterministic mechanics, or change auth, corpus, Chroma, embeddings, scraping, DNS, Tunnel, secrets, or deployment policy.

## Files changed

- `pocketsteel/copedent_transfer.py`
- `pocketsteel/melody_arranger.py`
- `ui/answer-client.js`
- `ui/melody-workbench.html`
- `tests/test_copedent_transfer.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_workbench_ui.py`
- This handoff and the Lane 15 QA handoff.

## Tests and checks

- Exact G/GG collision regressions — 2 passed.
- Answer-client success/error regressions — 2 passed.
- Relevant backend/frontend/API suite — 446 passed.
- Full suite — 1,133 passed.
- `npm run check:js` — passed.
- Ruff on touched Python/test files — passed.
- `git diff --check` — passed.

## Integration notes

- The existing transfer layer already retains stable control IDs. The defect occurred only when normalized render codes were converted back to display labels through the broader player-alias resolver.
- The new resolver is intentionally internal-code-specific. Ordinary player input continues to use normal alias resolution.
- API error text is collapsed, trimmed, and capped at 240 characters before being displayed with existing text-only UI handling.

## Risk assessment

- Low. The change narrows identity resolution at the renderer boundary and is covered by the exact full-song G/GG regression plus the complete suite.
- Rollback is a normal revert; no profile or stored-data migration is involved.

## Human decision needed

- No. The user explicitly approved the proper end-to-end fix and required preservation of G and GG.

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

- Account databases/profile snapshots, private corpus/training artifacts, source inbox/corpus/vector data, secrets/environment files, unrelated dirty/untracked files, brand/design assets, deployment/auth configuration, and `integration-status.md`.

## Recommended next lane

- Lane 15 QA gate, Lane 01 exact-path commit, then Lane 12 protected-preview smoke.

## Commit readiness

Safe to commit

## Suggested next step

- `Lane 01: Run ExactPathCommit using docs/handoffs/task-completions/2026-07-14-2037-15-melody-g-gg-control-fix-qa.md.`
