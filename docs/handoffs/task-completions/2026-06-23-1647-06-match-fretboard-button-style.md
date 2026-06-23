# 2026-06-23 16:47 - Lane 06 - Match Fretboard Button Style

## Task Summary

Requested: fix the home/header visual defect where `Explore Fretboard` used a different decorative/display treatment than the `Go Backstage` settings button.

Completed:
- Added a shared `header-action-button` style used by both header controls.
- Kept `Explore Fretboard` as the separate virtual fretboard link to `/ui/e9-fretboard-explorer.html`.
- Kept `Go Backstage` / backstage pass behavior tied to the backstage/settings dialog.
- Added the same icon treatment and explicit UI typography to the fretboard link so it does not inherit decorative/display font styling.

Intentionally not changed:
- Backend answer routing, Explorer data, prompt chips, auth, DNS, launchd, tunnel, corpus, Chroma, embeddings, scraping, secrets, private-source files, brand assets, and unrelated dirty files.

## Files Changed

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-1647-06-match-fretboard-button-style.md`

Deleted files: none.

Generated artifacts: none.

## Visual Smoke Result

Smoke target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8896/ui/steel-guitar-rag-mock.html?access=beta_user&v=explorer-button-style-smoke`
- Cache-busted URL tested: same as above
- Auth required: no for local static smoke
- Auth provider: none
- Local backend URL: none, static `http.server`
- Expected backend port: not applicable
- Expected git HEAD: `19d1845` before commit
- Version endpoint: not applicable to static smoke
- Whether app root `/` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Who should test this URL: Codex locally; Lane 12 should test protected preview next
- Known caveats: static `http.server` does not match protected-preview asset routing.

Computed style check from the browser:
- `Explore Fretboard` and `Go Backstage` both use `header-action-button`.
- Both rendered with the same font family, font size, font weight, padding, border, border radius, min-height, icon count, gap, and top alignment.
- `Explore Fretboard` still links to `/ui/e9-fretboard-explorer.html`.
- `Go Backstage` remains a button with `aria-controls="backstage"`.

## Tests And Checks

Passed:
- `git diff --check`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/e9-fretboard-explorer.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - 23 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - 32 passed

Skipped:
- Full pytest; task scope was a small HTML/CSS/test UI change and the requested checks were focused frontend/fretboard checks.

## Integration Notes

- The Explorer link remains a normal anchor and does not use `backstage-trigger`, so the backstage dialog JavaScript still binds only to the settings/backstage button.
- The visible current backstage text can change from `Get a Backstage Pass` to `Go Backstage` after access/session logic runs; this task did not alter that behavior.

## Risk Assessment

Risk: low.

Reason:
- Change is limited to shared header action styling and a focused assertion.
- No routing, data, backend, deployment, or asset changes.

Rollback:
- Revert the shared `header-action-button` class/style and restore the prior explorer link markup.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-1647-06-match-fretboard-button-style.md`

## Files That Must Not Be Staged

- Broad parked work shown by `git status --short`, including README/docs/provenance/corpus/source-inbox changes, RAG helper scripts, `ui/brand/` files, `public/`, raw design assets, corpus/private/source-inbox data, generated reports, deployment/auth/DNS/secrets, and all unrelated untracked files.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment: protected-preview smoke for the header button visual fix.

Then Lane 15 QA can rerun the focused MAIN-01/header-control check.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12 prompt:

```text
Lane 12: Run protected-preview smoke for commit <commit> and verify the main app header shows matching upper-right controls: Explore Fretboard links to /ui/e9-fretboard-explorer.html, and Go Backstage remains the backstage/settings dialog control.
```
