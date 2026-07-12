# Melody Studio starting-choice promotion

## Task summary

- Promoted **Staff editor** and **Browse songbook** into the primary starting-choice row beside note entry and audio.
- Removed their duplicate lower-page buttons and removed the sentence `Choose the easiest way to get the notes in.`
- Preserved draft-replacement confirmation and feature gating for songbook and import paths.
- Intentionally did not change the arranger, score, catalog, API, auth, corpus, source, or deployment contracts.

## Files changed

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-12-1651-06-melody-starting-choices.md`

## Tests and checks

- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `node --check ui/melody-score.js` — passed.
- `node --check ui/melody-workbench.js` — passed.
- `.venv/bin/python -m pytest -q tests/test_melody_workbench_ui.py tests/test_same_origin_smoke_server.py tests/test_frontend_answer_ui.py` — 42 passed.
- `.venv/bin/python -m pytest -q` — 938 passed.
- `git diff --check` — passed.
- Local authenticated browser smoke at `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=starting-choices-local-20260712` — passed.
  - Notes, audio, staff editor, and songbook appeared together as primary starting choices.
  - Staff editor opened its score workspace and remained selected.
  - Songbook opened its catalog workspace, loaded 12 reviewed songs, and remained selected.
  - Import stayed hidden when disabled.
  - The removed helper sentence and duplicate lower buttons were absent.

## Integration notes

- `entryPathForMethod()` now treats score and catalog as first-class entry paths so their primary buttons receive the selected state.
- The songbook choice is feature-gated directly and updates its subtitle to show the loaded catalog count.
- The responsive choice grid uses auto-fit columns and collapses to one column at the existing mobile breakpoint.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=starting-choices-local-20260712`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending protected-preview commit/restart
- Auth required: yes, local scaffold auth
- Auth provider: local scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: working tree based on `a9a862d`
- Version endpoint: `/api/version`
- Version endpoint result: local working-tree smoke; protected result pending
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not tested in this focused local smoke
- Whether app root `/` is expected to work: yes in protected preview
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested in this focused local smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stale `continuous-song-8efb56b` or `wrapped-score-a9a862d` cache keys
- Known caveats: import is intentionally hidden in protected preview when its separate feature flag is off.

## Risk assessment

- Risk: low. This is a client-only hierarchy adjustment with full regression coverage.
- Rollback: revert the scoped implementation commit.

## Human decision needed

- No.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-12-1651-06-melody-starting-choices.md`

## Files that must not be staged

- All unrelated dirty, untracked, corpus, source-inbox, private, brand, generated, deployment, auth, and integration-status files.

## Recommended next lane

- Lane 01 exact-path commit, then Lane 12 protected-preview restart and authenticated smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval with the exact files above, then verify the new primary choices in the protected preview.
