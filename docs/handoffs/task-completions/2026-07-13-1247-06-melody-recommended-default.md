# Melody Studio Recommended Arrangement Default

## Task summary

- Requested: make **Recommended arrangement** the primary/default Melody Studio route.
- Completed: Melody Studio now selects the `mixed_arrangement` route on initial render whenever it is available.
- Faithful melody remains the first comparison route, can still be selected manually, and remains the fallback when no mixed route exists.
- The API's top-level Faithful/single-note compatibility fields were intentionally not changed.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lanes: `15 QA / Answer Eval`, `01 Repo Steward`, then `12 Self-Hosted Deployment`
- Task mode: YELLOW UI behavior change, explicitly approved by the user's direct implementation request and covered by the Autopilot loop.

## Files changed

- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- This handoff.

No files were deleted. No generated artifacts were added.

## Tests and checks

- `node --check ui/melody-workbench.js` — passed.
- `node --check ui/melody-score.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `.venv/bin/python -m pytest -q tests/test_melody_workbench_ui.py tests/test_same_origin_smoke_server.py tests/test_melody_assistant.py tests/test_tab_engine.py` — **86 passed**.
- `.venv/bin/python -m pytest -q` — **971 passed**.
- Scoped `git diff --check` — passed.
- Authenticated browser smoke against the working-tree assets — passed.

## Browser smoke

Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=recommended-default-working-tree-20260713`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending the committed protected-preview restart
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded through the existing signed-in session
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: working tree based on `4ea8f7c`
- Version endpoint: `https://app.steelguitarrag.com/api/version`
- Version endpoint result: `4ea8f7c` before the implementation commit/restart
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not retested before commit
- Whether app root `/` is expected to work: yes, redirect to the home UI
- Whether `/ui/steel-guitar-rag-mock.html` works: not retested before commit
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stale pre-change cache keys
- Known caveats: this pre-commit smoke exercised working-tree static assets while `/api/version` still identified the prior commit; the full protected-preview version check follows the exact-path commit.

Observed:

- Entering `1 2 3 5` and arranging for E9 opened **Recommended arrangement** with `aria-pressed="true"`.
- The score showed the mixed two-voice/single-voice result rather than Faithful melody's single-note-only result.
- Selecting **Faithful melody** switched its pressed state to true and Recommended arrangement to false.
- No page-level horizontal overflow, no `[object Object]`, and no browser warning/error logs were present.

## Integration notes

- `preferredStudioRoute(exercise)` is an exported client helper so route precedence and fallbacks are testable without a DOM.
- Route precedence is: mixed arrangement, API-selected route, first route, then null.
- No API, arranger, score, tab, fretboard, auth, corpus, or deployment contract changed.

## Risk assessment

- Low. This changes only the initial Melody Studio presentation and retains manual switching plus the existing fallback.
- Rollback: revert the scoped implementation commit.

## Human decision needed

- No.

## Safe-to-stage exact file list

- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-13-1247-06-melody-recommended-default.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` in the implementation commit.
- Existing protected-preview coordination handoffs.
- All unrelated corpus, source-inbox, private, public, brand, Neon Sign, generated, deployment, auth, config, and design files.

## Recommended next lane

- Lane 01 exact-path commit, followed by Lane 12 protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

- Commit the exact six paths above, restart the protected preview, verify `/api/version`, and repeat the selected-route browser assertion at one new cache-busted URL.
