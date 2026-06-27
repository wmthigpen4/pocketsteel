# 2026-06-27 10:37 - Lane 06 - Grip Help Disclosure

## Task Summary

User smoke flagged that the Explorer grip explanation was visible all the time in the filter area and should be reconsidered. Completed a scoped UI cleanup by replacing the always-visible `explorer-controls-note` paragraph with a compact closed disclosure labeled `About grip vocabulary`.

Intentionally not changed:
- No Explorer logic, fretboard rendering, notation logic, grip vocabulary data, backend, corpus, Chroma, embeddings, scraping, auth, DNS, deployment, or protected-preview runtime changes.
- No glossary behavior changes.
- No source-card or provenance changes.

## Files Changed

- `ui/e9-fretboard-explorer.html`
  - Removed the always-visible `.explorer-controls-note` paragraph.
  - Added `.explorer-grip-help-disclosure` styling.
  - Added a closed `<details>` disclosure with the same grip vocabulary note behind an on-demand `About grip vocabulary` summary.
- `tests/test_frontend_answer_ui.py`
  - Updated assertions to require no `.explorer-controls-note`.
  - Added assertions that the grip vocabulary explanation is in a closed disclosure, not open by default.

Created:
- `docs/handoffs/task-completions/2026-06-27-1037-06-grip-help-disclosure.md`

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
- Full pytest was not run; focused Explorer/UI/fretboard tests passed for this narrow HTML/CSS/test change.
- Protected-preview smoke was not run; this lane did not restart or deploy protected preview.

## Browser Smoke Target

Smoke Target:
- Target type: local
- Result type: attempted browser smoke; browser connector timed out before completing the rendered check
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=grip-help-disclosure-local-20260627`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=grip-help-disclosure-local-20260627`
- Exact URL the user should use: after protected-preview update, `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=grip-help-disclosure-20260627`
- Auth required: no for local; yes for protected-preview
- Auth provider: none for local; Cloudflare Access for protected-preview
- Cloudflare Access login result: not required locally / not attempted for protected-preview
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: final commit pending at handoff creation
- Version endpoint: not checked
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local file state and focused tests
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not needed for direct Explorer task
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not needed for this direct Explorer task
- Who should test this URL: Lane 12/user after protected-preview refresh
- Do not test these URLs: stale `voicing-controls-de7f545` for this fix
- Known caveats: browser connector timed out during local rendered check; static/focused tests verify the disclosure contract.

## Integration Notes

- The grip vocabulary explanation is still available, but no longer visible by default.
- Existing glossary definitions for core/extended/two-string grips remain the broader reference location.
- The protected-preview URL in the user comment was stale (`voicing-controls-de7f545`); this fix requires a new cache-busted URL after commit.

## Risk Assessment

Risk: low.

Why:
- No JS logic changed.
- Existing content moved behind a native HTML disclosure.
- Focused tests assert the old always-visible paragraph is gone and the disclosure is closed by default.

Rollback:
- Revert this commit to restore the prior always-visible paragraph.

## Human Decision Needed

No.

## Safe-to-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-1037-06-grip-help-disclosure.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty/parked work, including:
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

Lane 12 protected-preview refresh/smoke, then user smoke the Explorer filter area.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12 smoke after commit:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=grip-help-disclosure-20260627
```
