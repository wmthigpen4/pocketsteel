# 2026-06-27 06 Grip Vocabulary And Pad Roles

## Task Summary

Expanded the E9 Fretboard Explorer grip vocabulary so learner-facing UI can expose common real-world tab grips, dyads, and pad/sustain roles without cluttering the default beginner views.

Completed:

- Added a compact `Grip vocabulary` selector for Single grip mode.
- Kept Core as the default vocabulary.
- Added Extended, Two-string, and All practical vocabulary options.
- Added deterministic grip metadata with tier and role labels.
- Added role filtering in the Grip Finder / Build grip workflow for non-core vocabulary.
- Added pad/sustain language as a possible role, not as a separate Explorer mode.
- Added glossary definitions for core grip, extended grip, dyad, pad/sustain, and partial voicing.
- Updated tests for vocabulary visibility, role metadata, pad/sustain copy, and no `[object Object]`.

Intentionally not changed:

- No backend Explorer generation.
- No fretboard geometry.
- No corpus, Chroma, embeddings, scraping, auth, DNS, deployment, or private-source files.
- No protected-preview restart or deployment.

## Files Changed

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1011-06-grip-vocabulary-and-pad-roles.md`

No files deleted. No generated assets changed.

## Grip Tiers Added

Core:

- `3-4-5`
- `4-5-6`
- `5-6-8`
- `6-8-10`
- `5-6-7`
- `6-7-10`

Extended:

- `4-6-10`
- `3-5-8`
- `5-6-9`
- `4-6-9`
- `3-5-6`
- `4-5-8`
- `5-8-10`

Two-string:

- `3-5`
- `3-6`
- `4-6`
- `4-8`
- `5-8`
- `5-9`
- `6-9`
- `6-10`
- `8-10`

Advanced:

- `5-7-8`
- `4-5-6-9`

## Grip Roles Added

Role metadata now supports:

- Melody harmony
- Pads
- Chord / voicing
- Dominant color
- Bass/root support
- Passing color

The UI only shows the role filter in Grip Finder / Build grip contexts where it is useful. Harmonized Scale Path does not show the vocabulary control or role filter, so the default path view stays clean.

## Pad/Sustain Handling

Pad/sustain appears as a possible role on selected support dyads and wide grips. The copy avoids claiming every dyad is a pad. Result cards can show:

> Pad use: this dyad can be sustained as a support layer while another voice moves.

## Tests And Checks

Passed:

- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
  - `23 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`
  - `34 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
  - `38 passed`
- `git diff --check`

Skipped:

- Full pytest was not run. The touched scope was UI/test-only and the focused Explorer/frontend/fretboard checks passed.
- Protected-preview smoke was not run. This slice has not been committed/restarted into protected preview yet.

## Local Smoke Result

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=grip-vocabulary-local-20260627`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=grip-vocabulary-local-20260627`
- Exact URL the user should use: not ready for protected-preview user smoke until committed and restarted
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `9048687` plus local uncommitted UI changes
- Version endpoint: not checked for local smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local worktree and cache-busted URL
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not relevant to this local Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this local Explorer smoke
- Who should test this URL: Codex locally; user after protected-preview restart
- Do not test these URLs: uncache-busted protected-preview Explorer URLs for this slice
- Known caveats: browser automation verified select-based vocabulary behavior and console cleanliness; the browser click path did not switch the Note Finder workflow, so role-filter behavior is covered by the focused frontend test rather than live click smoke.

Verified locally:

- Page loads.
- Core is the default vocabulary.
- Core string list is limited to core grips.
- Extended vocabulary reveals `4-6-10`, `3-5-8`, `5-6-9`, `4-6-9`, plus other extended/advanced practical grips.
- Two-string vocabulary reveals `3-5`, `3-6`, `4-6`, `4-8`, `5-8`, `5-9`, `6-9`, `6-10`, and `8-10`.
- Harmonized Scale Path hides/disables the top-level Grip vocabulary control.
- No `[object Object]`.
- No browser console errors.

## Integration Notes

- `ui/e9-fretboard-explorer.html` now cache-busts the Explorer script with `grip-vocabulary-20260627`.
- The grip registry is currently frontend-local metadata. Backend deterministic row generation was not changed.
- Grip Finder now computes practical grip rows from the selected copedent for selected vocabulary groups when possible.
- Existing core/path behavior is preserved by hiding vocabulary controls in Harmonized Scale Path mode.

## Risk Assessment

Risk: medium.

Why:

- The change adds meaningful frontend logic for computed practical grip rows and role filters.
- Focused tests pass, but full pytest and protected-preview smoke were not run in this handoff.

Rollback:

- Revert the scoped changes to `ui/e9-fretboard-explorer.js`, `ui/e9-fretboard-explorer.html`, and `tests/test_frontend_answer_ui.py`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1011-06-grip-vocabulary-and-pad-roles.md`

## Files That Must Not Be Staged

All unrelated dirty/untracked files currently parked in the worktree, including but not limited to:

- `README.md`
- `corpus_metadata/*`
- `docs/answer-eval-report.md`
- `docs/current-commands.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/*`
- `ui/brand/*`
- `public/brand/*`
- `Neon Sign/`
- `data/`
- `config/`

## Recommended Next Lane

Lane 01 exact-path commit for the scoped UI/test/handoff files, then Lane 12 protected-preview restart/smoke, then Lane 15 focused Explorer smoke.

## Commit Readiness

Safe to commit, subject to exact-path staging only.

## Suggested Next Step

Lane 01:

> Exact-path stage and commit `ui/e9-fretboard-explorer.js`, `ui/e9-fretboard-explorer.html`, `tests/test_frontend_answer_ui.py`, and `docs/handoffs/task-completions/2026-06-27-1011-06-grip-vocabulary-and-pad-roles.md`. Do not stage unrelated dirty files. Commit message: `feat: expand explorer grip vocabulary`.
