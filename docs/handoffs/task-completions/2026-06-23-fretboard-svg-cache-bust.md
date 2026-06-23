# Fretboard SVG Cache-Bust

## Task Summary

Lane: 06 UX/UI Design

Requested fix: ensure the E9 Fretboard Explorer/app UI loads the tracked V-shaped keyhead background asset instead of a stale cached copy of `public/brand/pedal-steel-fretboard-background.svg`.

Completed:
- Updated the decorative fretboard background URL in `ui/pedal-steel-fretboard.js` to include a cache-bust query string:
  `/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`
- Updated focused fretboard UI tests to assert the cache-busted SVG reference is rendered exactly once.
- Preserved fretboard geometry, Explorer data, backend behavior, corpus, Chroma, embeddings, auth, DNS, and deployment configuration.

Intentionally not changed:
- The tracked SVG asset itself.
- Fret spacing, string math, markers, highlights, Explorer data, backend routes, corpus/private data, deployment/auth/DNS settings, and unrelated dirty worktree files.

## Files Changed

- `ui/pedal-steel-fretboard.js`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/2026-06-23-fretboard-svg-cache-bust.md`

Deleted files: none.

Generated artifacts: none.

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest -q
git diff --check
git diff --cached --check
```

Results:
- JS syntax checks passed.
- `tests/test_pedal_steel_fretboard_ui.py`: 31 passed.
- `tests/test_frontend_answer_ui.py`: 23 passed.
- `tests/test_fretboard_explorer.py`: 28 passed.
- Full pytest: 808 passed.
- `git diff --check`: passed.
- `git diff --cached --check`: passed after exact-path staging.

## Integration Notes

The app and Explorer still use `/brand/pedal-steel-fretboard-background.svg`; the only runtime change is the query string `?v=keyhead-vshape-bce771f`. This should force protected-preview browsers to request the tracked V-shaped keyhead SVG rather than reuse a stale cached asset.

No component API, payload schema, Explorer data contract, or backend behavior changed.

## Risk Assessment

Risk: low.

Reason:
- The change is limited to the decorative SVG asset URL.
- Existing fretboard renderer tests verify layer order still includes the background underlay before functional fretboard geometry.
- Full pytest passed.

Rollback:
- Revert the query string in `DECORATIVE_BACKGROUND_HREF` and the corresponding test expectations.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/pedal-steel-fretboard.js`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/2026-06-23-fretboard-svg-cache-bust.md`

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

Lane 12 Self-Hosted Deployment should refresh/restart protected preview if needed, then verify the Explorer/app UI fetches:

`/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`

Lane 15 QA can then run the protected-preview Explorer smoke against the refreshed URL.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12: refresh the protected-preview runtime/cache-bust and verify the E9 Fretboard Explorer displays the V-shaped keyhead SVG background in the browser.
