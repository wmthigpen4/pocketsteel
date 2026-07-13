# Explorer Legacy-Fallback Retirement

## Task summary

The protected preview successfully loaded the versioned Explorer manifest and the requested Day E9/C chunk. The loader no longer fetches the legacy 70 MB JavaScript payload when lazy data is unavailable. It renders an honest unavailable state and exposes a short sanitized diagnostic data attribute instead. The legacy artifact itself remains untouched, as required by the no-deletion constraint.

## Lane classification

- Primary lane: 06 UX/UI Design
- Supporting lanes: 12 Self-Hosted Deployment and 15 QA
- Mode: approved Autopilot runtime/static reliability cleanup

## Files changed

- `ui/e9-fretboard-explorer-loader.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- This handoff

## Tests and checks

- Focused Explorer frontend tests — 2 passed, 25 deselected.
- `PYTHONPATH=.:scripts .venv/bin/pytest -q` — 1,023 passed.
- Explorer JavaScript syntax checks — passed.
- `git diff --check` — passed.
- Protected browser smoke — passed with `data-explorer-data-mode="lazy"`, Day E9 selected, C selected, and validated positions rendered.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=runtime-loader-diagnostic-4&copedent=day-e9-basic&key=C`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=runtime-loader-diagnostic-4&copedent=day-e9-basic&key=C`
- Exact URL the user should use: deferred until the full remediation plan reaches user smoke
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `2ce82defaf04ea1d28a213392bf2a7e826838abb` plus this pending static cleanup commit
- Version endpoint: `/api/version`
- Version endpoint result: local tunneled process returned `2ce82de`; static files are served from the working tree and were cache-busted for the protected check
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex during remediation; the user after final automated smoke
- Do not test these URLs: uncached loader revision 3
- Known caveats: the 70 MB legacy fixture remains in Git for compatibility/history but is no longer referenced by the production loader

## Integration notes

- Success state: `data-explorer-data-mode="lazy"`.
- Failure state: `data-explorer-data-mode="unavailable"` plus a sanitized `data-explorer-data-error` value.
- The loader contains no legacy fixture path.
- No Explorer data contract changed.

## Risk assessment

- Risk: low to medium. A manifest/chunk outage now fails honestly instead of downloading 70 MB.
- Rollback: revert this scoped commit to restore the temporary fallback.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/e9-fretboard-explorer-loader.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-07-13-1557-06-explorer-fallback-retirement.md`

## Files that must not be staged

The legacy `ui/e9-fretboard-explorer-data.js`, all unrelated dirty/private/corpus/vector/source-inbox/brand/design/deployment/generated/coordination files, and `docs/handoffs/task-completions/integration-status.md`.

## Recommended next lane

Lane 01 exact-path commit, then continue with the approved Interest-Digest Worker hardening loop.

## Commit readiness

Safe to commit

## Suggested next step

Commit the four exact paths and verify the protected Explorer remains in lazy mode at the new committed HEAD.
