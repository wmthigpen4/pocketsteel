# 2026-06-23 - Lane 06 - Fix Header Button Font

## Task Summary

Requested: remove the chunky/decorative/display font from both upper-right header buttons and keep them as matching plain UI controls.

Completed:
- Changed only the shared `.header-action-button` font stack to a neutral system UI stack.
- Preserved the separate `Explore Fretboard` link target: `/ui/e9-fretboard-explorer.html`.
- Preserved `Go Backstage` / backstage-settings behavior on `.backstage-trigger`.
- Updated the focused frontend test so the header action rule must not use `var(--font-ui)`, `var(--font-lesson)`, or `Gill Sans`.

Intentionally not changed:
- App-wide `--font-ui` remains unchanged for the rest of the page.
- Backend files, Explorer data, prompt chips, auth, DNS, launchd, tunnel, corpus, Chroma, embeddings, scraping, secrets, private-source files, and unrelated dirty files were not touched.

## Pass / Warn / Fail

Pass.

Warning: protected-preview smoke is still recommended because local visual smoke used a static `http.server`, not the launchd/protected-preview runtime.

## Branch / HEAD

- Branch: `feature/answer-api`
- Starting HEAD: `f31b9ca`
- Final HEAD / commit hash if committed: pending at handoff creation

## Root Cause

The shared header button style used `font-family: var(--font-ui)`. In this app, `--font-ui` begins with `"Gill Sans", "Gill Sans MT"`, which rendered the header action buttons in the chunky/decorative-looking face during user smoke. The prior fix made both buttons match each other, but matched them through the wrong font stack.

## Files Touched

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-fix-header-button-font.md`

## What Changed

- `.header-action-button` now uses:
  `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
- The root app font remains `var(--font-ui)`.
- The focused test extracts the `.header-action-button` CSS rule and asserts it uses the neutral system stack and does not use `var(--font-ui)`, `var(--font-lesson)`, or `Gill Sans`.

## Visual Smoke Result

Smoke target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8896/ui/steel-guitar-rag-mock.html?access=beta_user&v=header-button-font-smoke`
- Cache-busted URL tested: same as above
- Auth required: no
- Auth provider: none
- Local backend URL: none, static `http.server`
- Expected backend port: not applicable
- Expected git HEAD: `f31b9ca` before commit
- Version endpoint: not applicable to static smoke
- Whether app root `/` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Who should test this URL: Codex locally; Lane 12 should test protected preview next
- Known caveats: `/api/session` returned 404 under static server, expected for this smoke method and unrelated to header styling.

Computed browser style results:
- `Explore Fretboard` font family: `-apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
- `Go Backstage` font family: `-apple-system, "system-ui", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
- `usesGillSans`: false
- Both controls retained matching class family, font size, weight, padding, radius, height, icon count, and top alignment.

## Checks Run

Passed:
- `git diff --check`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/e9-fretboard-explorer.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - 23 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - 32 passed

One intermediate test run failed because the first patch hit the root font declaration instead of the header rule. That was corrected before this handoff; the final focused test runs passed.

## Risks

Low.

Reason:
- Scope is one CSS declaration and one focused frontend test assertion.
- No route, data, backend, deployment, or asset behavior changed.

Rollback:
- Revert the `.header-action-button` font-family line and the related test assertion.

## Blockers

None.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-fix-header-button-font.md`

## Files That Must Remain Unstaged

- All unrelated parked files shown by `git status --short`, including README/docs/provenance/corpus/source-inbox changes, RAG helper scripts, `ui/brand/` files, `public/`, raw design assets, corpus/private/source-inbox data, generated reports, deployment/auth/DNS/secrets, and unrelated untracked files.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment: protected-preview smoke for the header button font fix.

Then Lane 15 QA can run focused header-control verification if needed.

## Commit Readiness

Safe to commit.

## Suggested Next Step

```text
Lane 12: Run protected-preview smoke for commit <commit> and verify both upper-right header buttons use the plain UI font: Explore Fretboard opens /ui/e9-fretboard-explorer.html, and Go Backstage remains the backstage/settings control.
```
