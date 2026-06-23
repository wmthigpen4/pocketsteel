# Fretboard SVG Script Cache-Bust

## Task Summary

Lane: 06 UX/UI Design

Requested fix: refresh the Explorer page script cache-bust so `ui/e9-fretboard-explorer.html` fetches the current `pedal-steel-fretboard.js`, which contains the cache-busted V-shaped keyhead SVG reference:

`/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`

Completed:
- Updated only the Explorer page `pedal-steel-fretboard.js` script query string from:
  `e9-explorer-explanation-ui-20260623`
  to:
  `fretboard-svg-cache-bust-20260623b`
- Updated focused frontend assertions to require the refreshed Explorer `pedal-steel-fretboard.js` cache-bust and reject the stale value for that script.
- Left Explorer data/controller script cache-busts unchanged because they are not involved in the stale SVG renderer issue.

Intentionally not changed:
- Fretboard renderer logic.
- Fretboard/SVG geometry.
- Explorer data rows.
- Backend code.
- Corpus, Chroma/vector stores, embeddings, scraper output, auth, DNS, deployment config, private source data, and unrelated dirty worktree files.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-fretboard-svg-script-cache-bust.md`

Deleted files: none.

Generated artifacts: none.

## What Changed

Explorer script tag before:

```html
<script src="pedal-steel-fretboard.js?v=e9-explorer-explanation-ui-20260623"></script>
```

Explorer script tag after:

```html
<script src="pedal-steel-fretboard.js?v=fretboard-svg-cache-bust-20260623b"></script>
```

This forces the Explorer page to fetch the current fretboard renderer script instead of a cached copy that may still reference the unversioned SVG path.

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
rg "pedal-steel-fretboard.js" ui/e9-fretboard-explorer.html tests
node --check ui/e9-fretboard-explorer.js
node --check ui/pedal-steel-fretboard.js
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest -q
git diff --check
git diff --cached --name-only
git diff --cached
git diff --cached --check
```

Results:
- `node --check ui/e9-fretboard-explorer.js`: passed.
- `node --check ui/pedal-steel-fretboard.js`: passed.
- `node --check ui/answer-client.js`: passed.
- `tests/test_frontend_answer_ui.py`: 23 passed.
- `tests/test_pedal_steel_fretboard_ui.py`: 31 passed.
- `tests/test_fretboard_explorer.py`: 28 passed.
- Full pytest: 808 passed.
- `git diff --check`: passed.
- `git diff --cached --name-only`: reviewed scoped paths only.
- `git diff --cached`: reviewed scoped diff.
- `git diff --cached --check`: passed.

## Integration Notes

The direct SVG URL and renderer URL are already correct. The stale protected-preview symptom was consistent with the Explorer HTML loading an old cached `pedal-steel-fretboard.js` because the script query string had not changed since the explanation UI slice.

Expected Explorer page behavior after protected-preview refresh:
- Explorer HTML requests `pedal-steel-fretboard.js?v=fretboard-svg-cache-bust-20260623b`.
- That script requests `/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`.

## Risk Assessment

Risk: low.

Reason:
- Change is limited to one Explorer HTML script query string and one focused frontend assertion.
- Full pytest passed.
- No runtime logic, backend, data rows, or SVG geometry changed.

Rollback:
- Revert the `pedal-steel-fretboard.js` query string in `ui/e9-fretboard-explorer.html` and the corresponding assertion.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-fretboard-svg-script-cache-bust.md`

## Files That Must Not Be Staged

All unrelated dirty and untracked files, especially:
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
- `data/`
- `config/`
- any corpus, Chroma/vector, embedding, scraping, deployment, auth, DNS, private source, raw design, or generated report files.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment should refresh protected preview and verify the Explorer page requests:

`/ui/pedal-steel-fretboard.js?v=fretboard-svg-cache-bust-20260623b`

Then verify the renderer requests:

`/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12: refresh protected preview and browser-smoke the Explorer page network requests for the refreshed script and cache-busted SVG.
