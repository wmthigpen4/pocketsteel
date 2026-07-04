# Lane 06 / Lane 12 - Impact Preview Under Fretboard

## Task Summary

The user reported that the Explorer Pedal and Lever Impact preview was poor UX because it sat at the bottom of the page instead of directly under the fretboard. This task moved `#explorer-control-impact-preview` into the Explorer fretboard panel immediately after `#explorer-fretboard` and before `#explorer-active-results`.

Intentionally not changed:

- Backend/API behavior.
- Explorer data rows, pitch validation, copedent logic, or route semantics.
- Cloudflare Access, DNS, LaunchDaemon, tunnel, auth, corpus, Chroma, embeddings, scraping, private source data, or visual assets.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?mode=path&source=movement-card&key=G&progression=I-IV&v=impact-under-fretboard-20260704`
- Cache-busted URL tested: yes, `?v=impact-under-fretboard-20260704`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?mode=path&source=movement-card&key=G&progression=I-IV&v=impact-under-fretboard-20260704`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; authenticated session loaded the Explorer page
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: current branch HEAD after this fix
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"7dcd8cb","git_branch":"feature/answer-api","auth_provider":"cloudflare_access","retrieval_mode":"hybrid_private_first"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not retested for this scoped UI placement fix
- Whether app root `/` is expected to work: root historically redirects to `/ui/steel-guitar-rag-mock.html` and may drop query strings
- Whether `/ui/steel-guitar-rag-mock.html` works: not retested; unaffected by this Explorer-only placement change
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex and the user
- Do not test these URLs: do not use root `/` as the cache-busted Explorer URL for this fix
- Known caveats: `/api/version` reports the Python runtime SHA, currently `7dcd8cb`; this fix is static Explorer HTML and was verified through the protected browser with a cache-busted URL.

## Files Changed

- `ui/e9-fretboard-explorer.html`
  - Moved `section#explorer-control-impact-preview` directly under `div#explorer-fretboard` and before `div#explorer-active-results`.
- `tests/test_frontend_answer_ui.py`
  - Updated the Explorer markup assertions so the panel slice includes the moved impact preview.
  - Added explicit ordering checks: fretboard -> impact preview -> active result cards.
- `docs/handoffs/task-completions/integration-status.md`
  - Added current status for this protected-preview smoke result.
- `docs/handoffs/task-completions/assets/2026-07-04-impact-preview-under-fretboard/protected-impact-under-fretboard-desktop.png`
- `docs/handoffs/task-completions/assets/2026-07-04-impact-preview-under-fretboard/protected-impact-under-fretboard-mobile.png`
- `docs/handoffs/task-completions/2026-07-04-0930-06-impact-preview-under-fretboard.md`

## Tests And Checks

Passed:

- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
  - `24 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
  - `43 passed`
- `git diff --check`
- Protected-preview browser smoke at the exact URL above.

Protected browser smoke results:

- Cloudflare Access: passed; no Access login page visible.
- Page: `E9 Fretboard Explorer`.
- `#explorer-control-impact-preview`: visible.
- DOM order: `#explorer-fretboard` -> `#explorer-control-impact-preview` -> `#explorer-active-results`.
- Active path/result cards: visible; 8 path/result controls detected.
- Right-side selected-position inspector: visible.
- Old `#explorer-row-list`: hidden.
- Desktop page-level horizontal overflow: no.
- Mobile/narrow viewport page-level horizontal overflow: no.
- `[object Object]`: no.
- Console errors: none returned by the browser error log.

Screenshots:

- `docs/handoffs/task-completions/assets/2026-07-04-impact-preview-under-fretboard/protected-impact-under-fretboard-desktop.png`
- `docs/handoffs/task-completions/assets/2026-07-04-impact-preview-under-fretboard/protected-impact-under-fretboard-mobile.png`

## Integration Notes

The impact preview remains the same functional control surface; only its placement changed. It now follows the physical/learning model more closely: first the fretboard, then the controls that change the instrument, then the visible result/path cards.

The test file had unrelated parked progression-guide edits before this task. Only the Explorer ordering assertions are part of this fix.

## Risk Assessment

Risk: low.

Reason: the change is limited to static Explorer DOM placement plus focused test assertions. The existing JS still targets the same `#explorer-control-impact-preview` id, and protected-preview browser smoke confirmed the component renders and remains interactive enough for this scope.

Rollback:

- Revert this scoped commit or move `section#explorer-control-impact-preview` back below the workbench.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py` selected Explorer-ordering hunks only
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-04-0930-06-impact-preview-under-fretboard.md`
- `docs/handoffs/task-completions/assets/2026-07-04-impact-preview-under-fretboard/protected-impact-under-fretboard-desktop.png`
- `docs/handoffs/task-completions/assets/2026-07-04-impact-preview-under-fretboard/protected-impact-under-fretboard-mobile.png`

## Files That Must Not Be Staged

- Unrelated dirty runtime/code/docs files already parked in the worktree.
- Corpus, Chroma/vector stores, embeddings, source-inbox raw/provenance data, private source data, auth/DNS/secrets/deployment config, and unrelated generated artifacts.
- Existing unrelated progression-guide hunks in `tests/test_frontend_answer_ui.py`.

## Recommended Next Lane

Lane 01 Repo Steward, if a separate integration-status/handoff hygiene pass is desired. Otherwise user smoke can continue at the exact cache-busted Explorer URL.

## Commit Readiness

Safe to commit, with exact-path/exact-hunk staging only.

## Suggested Next Step

User smoke the movement Explorer URL:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?mode=path&source=movement-card&key=G&progression=I-IV&v=impact-under-fretboard-20260704
```
