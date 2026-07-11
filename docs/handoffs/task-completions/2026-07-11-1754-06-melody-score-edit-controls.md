# Melody Score Edit Controls

## Task summary

User-smoke adjustment for the Melody Studio lead-sheet editor. Deletion is now available beside the visible score selection and through Delete/Backspace when focus is outside editable fields. Whole-score controls now move all pitched events up or down by one octave; the existing transpose controls are explicitly labeled as one-semitone operations. No audio analysis, arranger contract, auth, corpus, or deployment-policy behavior changed.

## Lane classification

- Primary lane: 06 UX/UI Design
- Supporting lanes: 15 QA / Answer Eval, 01 Repo Steward, 12 Self-Hosted Deployment
- Mode: approved user-smoke adjustment / Autopilot

## Files changed

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- This handoff

No files were deleted or generated.

## Tests and checks

- `node --check ui/melody-workbench.js` — pass
- `node --check ui/melody-score.js` — pass
- `PYTHONPATH=. .venv/bin/pytest -q tests/test_melody_workbench_ui.py tests/test_same_origin_smoke_server.py` — 16 passed
- `PYTHONPATH=. .venv/bin/pytest -q` — 935 passed
- `git diff --check -- <scoped files>` — pass
- Local browser smoke — pass:
  - Built G4, A4, B4 in the score editor.
  - Visible `Delete selected note` removed B4 and selected A4.
  - Keyboard Delete removed A4 and selected G4.
  - `All notes up 1 octave` changed the selected B4 to B5 and reported success.
  - A fresh G4, A4, B4 draft arranged into `Your melody exercise in G` when the documented local development-access query was present.

The initial local arrange attempt without `access=beta_user` returned the expected local-development 401. That was a smoke URL configuration issue, not a feature failure; the authenticated local rerun passed.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?v=melody-score-edit-controls-local-20260711&access=beta_user`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending protected-preview commit and restart
- Auth required: yes
- Auth provider: local development scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: pre-commit working tree based on `5cab816`
- Version endpoint: `/api/version`
- Version endpoint result: not used for the local working-tree smoke
- If version endpoint missing, how version is inferred: cache-busted working-tree assets
- Whether app root `/` works: yes, redirects to the home UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: the uncommitted working-tree URL as a user-smoke handoff
- Known caveats: local scaffold access requires `access=beta_user`; protected smoke remains required

## Integration notes

- The existing score model already supported arbitrary semitone transposition; the UI now invokes it with `12` or `-12` for whole-score octave movement.
- Rests remain unchanged because the score model transposes only events with numeric pitch values.
- Keyboard deletion is suppressed while an input, textarea, or select owns focus.
- The previous event-editor removal button remains as a secondary path and shares the same deletion function.

## Risk assessment

Low. The changes are limited to Melody Studio score-editor controls and reuse existing score-draft operations. Rollback is the scoped implementation commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-11-1754-06-melody-score-edit-controls.md`

## Files that must not be staged

All unrelated dirty corpus, source-inbox, private-data, deployment, public/brand, Neon Sign, RAG pipeline, README, and pre-existing documentation files.

## Recommended next lane

01 Repo Steward for exact-path commit, then 12 Self-Hosted Deployment for protected-preview restart and authenticated smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval, commit only the safe-to-stage list, restart the protected preview, verify the committed version, run authenticated browser smoke, and refresh `integration-status.md` separately.
