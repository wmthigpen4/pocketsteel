# 2026-06-23 - Lane 06 Smoke Feedback UI / Explorer Polish

## Task Summary

Requested Lane 06 UX/UI smoke-feedback polish for the protected-preview home page and E9 Fretboard Explorer.

Completed:

- Replaced the large home-page Explorer feature card with a compact top-page button-style link: `Explore the E9 Fretboard`.
- Kept the link target at `/ui/e9-fretboard-explorer.html`.
- Replaced two vague auto-submit prompt chips with self-contained prompts:
  - `Show me a G to C move on E9.`
  - `Explain a simple G turnaround on E9.`
- Updated Explorer copy to avoid raw/internal RAG terminology in learner-facing text.
- Made the Explorer string-group control support multiple selected groups.
- Added learner help for advanced swaps, the 5&8 branch relationship to 2-string harmonized scale, and shorthand such as `m7b5`, `ø`, `°`, `vii°`, and `partial`.
- Added focused frontend regression coverage.

Intentionally not changed:

- Backend routing, Explorer generation, pitch validation, answer routing, tab engine behavior, corpus, Chroma/vector data, embeddings, scraping, auth, DNS, deployment config, private source data, and visual assets.

## Files Changed

- `ui/steel-guitar-rag-mock.html`
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-smoke-feedback-ui-explorer-polish.md`

Deleted files: none.

Generated artifacts: none.

## UI Behavior Changed

Home page:

- The Explorer entry is now a compact header button-style link instead of a secondary full-width card below the prompt chips.
- Q&A/search remains the primary flow.
- The old `Open Fretboard Explorer` card is gone.
- The two vague prompt chips named in the task are no longer present.

Explorer:

- The string-group selector is now a multi-select control.
- Selecting multiple groups filters the rendered rows and fretboard positions to those groups.
- If no specific group is selected, `All` behavior remains the default.
- `5&8 branch positions (2-string)` visibly connects the branch to the 2-string harmonized-scale concept.
- `Advanced swaps` are explained as less direct string combinations or lever/pocket logic.
- Music shorthand help is visible for `m7b5`, `ø`, `°`, `vii°`, and `partial`.
- Raw `five_eight_branch` remains internal metadata only; tests continue to assert it is not rendered in row/detail copy.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8898/ui/steel-guitar-rag-mock.html?v=smoke-feedback-ui-explorer-polish`
- Cache-busted URL tested: `http://127.0.0.1:8898/ui/steel-guitar-rag-mock.html?v=smoke-feedback-ui-explorer-polish`
- Exact URL the user should use: protected preview should use `/ui/steel-guitar-rag-mock.html` after Lane 12 restart/cache refresh
- Auth required: no for local smoke
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: static local server at `http://127.0.0.1:8898`
- Expected backend port: not applicable for static local smoke
- Expected git HEAD: `3811a8c` before commit
- Version endpoint: not used
- Version endpoint result: not used
- If version endpoint missing, how version is inferred: local working tree was served directly
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant for static local smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex locally; Lane 12 should test protected preview after restart/cache refresh
- Do not test these URLs: production `app.steelguitarrag.com` without Lane 12 restart/cache refresh
- Known caveats: the simple local static server returned 404 for `/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f` because protected-preview asset mapping is not reproduced by `python3 -m http.server` from repo root. This did not affect the smoke checks for entry link, prompt copy, Explorer controls, or learner copy.

## Tests And Checks

Passed:

- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` -> `23 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` -> `32 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` -> `30 passed`
- `.venv/bin/python -m pytest -q` -> `827 passed`
- `git diff --check`

Browser smoke:

- Home page compact Explorer link present with `href="/ui/e9-fretboard-explorer.html"`.
- Old Explorer card absent.
- Old vague prompt chips absent.
- Replacement prompt chips present.
- Explorer string-group control is `multiple`.
- `5&8 branch positions (2-string)` option visible.
- Advanced swap and shorthand help visible.
- No `[object Object]` found in the smoke page text.

## Integration Notes

- No schema/API/data contract changes.
- Explorer multi-select is implemented entirely in the UI layer by reading selected `<option>` values.
- Existing `All` string-group behavior remains the default when no specific group is selected.
- Existing shared fretboard component filters remain hidden in the Explorer via `hideFilterControls: true`.

## Risk Assessment

Risk: medium-low.

Why:

- The changes are scoped to static UI and tests.
- The Explorer string-group selector changed from single-select to multi-select, which is a visible interaction change. Tests cover multi-select behavior, but Lane 12/Lane 15 should verify protected-preview browser behavior.
- The compact header entry may need visual tuning on very narrow mobile widths if it competes with the Backstage button.

Rollback notes:

- Revert the scoped changes in `ui/steel-guitar-rag-mock.html`, `ui/e9-fretboard-explorer.html`, `ui/e9-fretboard-explorer.js`, and `tests/test_frontend_answer_ui.py`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/steel-guitar-rag-mock.html`
- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-smoke-feedback-ui-explorer-polish.md`

## Files That Must Not Be Staged

- Existing unrelated dirty files shown by `git status --short`, including but not limited to backend/RAG files, corpus metadata, source-inbox files, UI/brand assets, public brand assets, deploy artifacts, and other untracked handoffs/assets.
- Do not stage with `git add .`.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment should refresh protected-preview runtime/cache and smoke:

1. Home page compact Explorer entry.
2. Explorer multi-select string-group behavior.
3. Absence of the old vague prompt chips.
4. Absence of raw/internal Explorer wording in protected preview.

Then Lane 15 QA / Answer Eval should run protected-preview user-smoke regression for the Explorer flow.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12 prompt:

```text
Lane 12: restart/refresh protected preview for commit <new commit hash>, then smoke the app home page and /ui/e9-fretboard-explorer.html. Verify the compact Explorer entry, multi-select string group behavior, 5&8 branch learner labeling, advanced-swap/shorthand help, and no raw internal labels or vague prompt chips.
```
