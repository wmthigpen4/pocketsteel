# Melody Studio Lesson Header Protected-Smoke Blocker

## Task summary

Implementation commit `deac899` contains the approved lesson-header cleanup: no practice kicker, no exact/confidence/section metadata line, and all available arrangement routes in one visible row.

Local browser smoke and all tests passed. The protected preview restarted and `/api/version` reports `deac899`, but the protected lesson-build request returned HTTP 500 because an unrelated, uncommitted edit appeared in `steel_guitar_rag/melody_arranger.py` during the restart/smoke window. The running process lazily imported the arranger while that separate edit was incomplete and raised `NameError: name 're' is not defined` from `_forced_pitch`.

The file now contains approximately 135 lines of unrelated arranger work, including vocal-steel routing and structured timing/import fields. Restarting again would load that uncommitted feature work into protected preview, so the safe autopilot stop condition applies. The overlapping file was not edited, staged, reverted, reset, cleaned, or committed by this task.

## Files changed

- `docs/handoffs/task-completions/2026-07-11-0815-12-melody-header-protected-smoke-blocker.md`
- `docs/handoffs/task-completions/integration-status.md`

Deleted files: none. Generated artifacts: none.

## Tests and checks

- Implementation commit: `deac899 Clean up Melody Studio lesson header`.
- JavaScript syntax checks: passed.
- Focused UI/frontend/fretboard/same-origin suite: 80 passed.
- Full pytest: 922 passed.
- Local browser smoke: passed; all five available routes appeared in one row and Chord melody switching synchronized correctly.
- Protected loopback `/api/version`: `deac899`, expected branch/auth/retrieval/feature state.
- Protected static page and authenticated session: loaded current assets.
- Protected lesson-build request: failed HTTP 500 due to the unrelated dirty arranger overlap.
- Protected browser smoke result: FAIL; API fallback was not used as a substitute.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-route-row-deac899-20260711`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-route-row-deac899-20260711`
- Exact URL the user should use: none until the overlapping arranger work is reconciled and protected smoke passes
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `deac899`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: HTTP 200, `git_sha=deac899`, expected branch/auth/retrieval/feature state
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not repeated after the API failure; it passed immediately before this adjustment
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not repeated after the API failure; it passed immediately before this adjustment
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex only after the overlap is resolved
- Do not test these URLs: the current protected Melody Studio URL should not be given to the user for smoke while lesson builds return 500
- Known caveats: current worktree `steel_guitar_rag/melody_arranger.py` is unrelated dirty runtime code and cannot safely be loaded or reverted by this task.

## Integration notes

The UI implementation itself is committed and green. Recovery requires the separate arranger task to finish, commit, or otherwise establish an approved stable runtime baseline. Then Lane 12 may restart the listener and repeat the exact protected browser smoke without changing the header implementation.

## Risk assessment

High for another restart while the arranger file is dirty, because it would deploy unrelated uncommitted feature behavior. Low for the committed UI cleanup itself.

## Human decision needed

Yes. Finish or reconcile the separate `steel_guitar_rag/melody_arranger.py` work, then resume this task for protected-preview restart and smoke. No decision about the lesson-header design is needed.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-0815-12-melody-header-protected-smoke-blocker.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

- `steel_guitar_rag/melody_arranger.py`
- all other unrelated dirty and untracked corpus, source-inbox, private-data, brand/design, public asset, deployment, generated-report, and parked documentation paths.

## Recommended next lane

The lane/task that owns the concurrent arranger work must establish a stable committed baseline; then Lane 12 repeats protected preview smoke for `deac899` or its approved descendant.

## Commit readiness

Safe to commit

## Suggested next step

Complete or reconcile the separate arranger change, then resume with: `Lane 12: repeat protected Melody Studio header smoke for implementation deac899 using the blocker handoff.`
