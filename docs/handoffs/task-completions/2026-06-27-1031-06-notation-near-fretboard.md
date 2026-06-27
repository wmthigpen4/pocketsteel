# 2026-06-27 10:31 - Lane 06 - Notation Near Fretboard

## Task Summary

Move the E9 Fretboard Explorer Notation selector closer to the visual content it affects. Completed the scoped UI layout change by moving the existing Notes / NNS / Roman / Numbers selector out of the top filter area and into the Explorer fretboard panel, directly before the visible position cards and SVG fretboard.

Intentionally not changed:
- No backend, routing, corpus, Chroma, embeddings, scraping, auth, DNS, deployment, or protected-preview runtime changes.
- No notation logic rewrite.
- No fretboard geometry, Explorer data, copedent data, grip vocabulary, or marker-generation changes.
- No duplicate synced notation selector was added.

## Files Changed

- `ui/e9-fretboard-explorer.html`
  - Added `.explorer-panel-notation` compact toolbar styling.
  - Moved the single `#explorer-notation-control` into `.explorer-panel` before `#explorer-active-results` and `#explorer-fretboard`.
  - Removed the notation selector from the top `.explorer-controls` filter area.
  - Bumped `e9-fretboard-explorer.js` cache-bust to `notation-near-fretboard-20260627`.
- `tests/test_frontend_answer_ui.py`
  - Updated cache-bust assertion.
  - Added assertions that exactly one notation selector exists, it is inside the fretboard panel, it appears before results/SVG, and the top filter area does not retain notation buttons.

Created:
- `docs/handoffs/task-completions/2026-06-27-1031-06-notation-near-fretboard.md`

Deleted files: none.
Generated artifacts: none.

## Tests and Checks

Commands run:

```bash
git status --short
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
git diff --check
git status --short
```

Results:
- `node --check ui/e9-fretboard-explorer.js`: pass
- `node --check ui/e9-fretboard-explorer-data.js`: pass
- `node --check ui/answer-client.js`: pass
- `node --check ui/pedal-steel-fretboard.js`: pass
- `tests/test_frontend_answer_ui.py`: 23 passed
- `tests/test_pedal_steel_fretboard_ui.py`: 34 passed
- `tests/test_fretboard_explorer.py`: 38 passed
- `git diff --check`: pass

Skipped:
- Full pytest was not run; this is a narrow static HTML/CSS/test update and focused UI/fretboard/backend Explorer tests passed.
- Protected-preview smoke was not run in this lane because no runtime restart/deployment was performed.

## Browser Smoke Target

Smoke Target:
- Target type: local
- Result type: browser smoke for placement; interaction update verified by focused frontend VM test, not pointer browser click
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=notation-near-fretboard-local-20260627`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=notation-near-fretboard-local-20260627`
- Exact URL the user should use: after protected-preview update, `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=notation-near-fretboard-20260627`
- Auth required: no for local; yes for protected-preview
- Auth provider: none for local; Cloudflare Access for protected-preview
- Cloudflare Access login result: not required locally / not attempted for protected-preview
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `8d0c9bd` at task start; final commit pending
- Version endpoint: not checked for local static smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local file state and cache-busted static URL
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not needed for direct Explorer local smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not needed for this direct Explorer task
- Who should test this URL: Codex locally; Lane 12/user on protected-preview after commit/runtime refresh
- Do not test these URLs: stale Explorer URLs without `notation-near-fretboard-20260627`
- Known caveats: in-app browser comment overlay intercepted pointer clicks during this run; DOM placement/no-console checks passed, and notation switching behavior remains covered by `tests/test_frontend_answer_ui.py`.

Local browser findings:
- Page loaded at the local cache-busted Explorer URL.
- `#explorer-notation-control` exists inside `.explorer-panel`.
- It appears before `#explorer-active-results` and `#explorer-fretboard` in DOM order.
- It no longer appears inside `.explorer-controls`.
- Four notation buttons are present.
- No `[object Object]` text was found.
- Browser console error log was empty during the successful placement check.

## Integration Notes

- This is a placement-only change. Existing JS still uses `[data-explorer-notation-mode]`, so the same control drives marker labels, cards, path rail, single-note finder, voicing identifier, top-label controls, and impact-preview notation text.
- The cache-bust was updated so protected-preview should request the current Explorer JS bundle alongside the moved markup.
- The old top filter area no longer owns notation, reducing filter clutter.

## Risk Assessment

Risk: low.

Why:
- One existing control was moved; IDs, labels, button data attributes, and event wiring selectors were preserved.
- Focused UI/fretboard tests passed.
- The change is isolated to Explorer static HTML/CSS plus assertions.

Rollback:
- Revert `ui/e9-fretboard-explorer.html` and `tests/test_frontend_answer_ui.py` for this slice.

## Human Decision Needed

No.

## Safe-to-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1031-06-notation-near-fretboard.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty/parked work, including but not limited to:
- `README.md`
- `corpus_metadata/**`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/`
- untracked corpus, source, deploy, design, generated, or private files.

## Recommended Next Lane

Lane 01 exact-path commit for the three safe files, then Lane 12 protected-preview refresh/smoke at:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=notation-near-fretboard-20260627
```

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 01:

```text
Exact-path stage and commit only ui/e9-fretboard-explorer.html, tests/test_frontend_answer_ui.py, and docs/handoffs/task-completions/2026-06-27-1031-06-notation-near-fretboard.md with message: fix: move explorer notation near fretboard
```
