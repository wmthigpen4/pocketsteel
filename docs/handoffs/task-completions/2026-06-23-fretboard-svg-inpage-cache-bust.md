# Fretboard SVG In-Page Cache-Bust Verification

## Task Summary

Lane: 06 UX/UI Design

Requested fix: force the in-page E9 fretboard renderer used by the Explorer/app UI to request:

`/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`

Completed:
- Inspected `ui/pedal-steel-fretboard.js`, Explorer/app files, and tests for `pedal-steel-fretboard-background.svg`.
- Verified the in-page renderer already uses the cache-busted asset URL at current HEAD:
  `const DECORATIVE_BACKGROUND_HREF = "/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f";`
- Verified focused tests already assert the rendered SVG underlay includes `keyhead-vshape-bce771f`.
- Ran requested syntax checks and test suites.

Implementation note:
- No additional implementation patch was needed in this task because commit `9562e90` already changed the in-page renderer and focused tests. Current HEAD `7c36c49` includes that change.

Intentionally not changed:
- Fretboard geometry, Explorer data, backend pitch validation, corpus, Chroma, embeddings, scraper output, auth, DNS, deployment config, private source data, and unrelated dirty worktree files.

## Files Changed

- `docs/handoffs/task-completions/2026-06-23-fretboard-svg-inpage-cache-bust.md`

Files inspected but not changed:
- `ui/pedal-steel-fretboard.js`
- `ui/e9-fretboard-explorer.js`
- `ui/answer-client.js`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_frontend_answer_ui.py`

Deleted files: none.

Generated artifacts: none.

## Evidence

Command:

```bash
rg "pedal-steel-fretboard-background.svg" ui tests
```

Relevant result:

```text
ui/pedal-steel-fretboard.js:  const DECORATIVE_BACKGROUND_HREF = "/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f";
tests/test_pedal_steel_fretboard_ui.py:const backgroundHref = '/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f';
tests/test_pedal_steel_fretboard_ui.py:    assert 'const DECORATIVE_BACKGROUND_HREF = "/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f";' in source
```

The only bare `/brand/pedal-steel-fretboard-background.svg` reference left is in `tests/test_same_origin_smoke_server.py`, where it checks the static asset route directly. That is not the in-page renderer and should remain capable of serving the base asset path.

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
rg "pedal-steel-fretboard-background.svg" ui tests
node --check ui/pedal-steel-fretboard.js
node --check ui/e9-fretboard-explorer.js
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest -q
git diff --check
git diff --cached --check
```

Results:
- `node --check ui/pedal-steel-fretboard.js`: passed.
- `node --check ui/e9-fretboard-explorer.js`: passed.
- `node --check ui/answer-client.js`: passed.
- `tests/test_pedal_steel_fretboard_ui.py`: 31 passed.
- `tests/test_frontend_answer_ui.py`: 23 passed.
- Full pytest: 808 passed.
- `git diff --check`: passed.
- `git diff --cached --check`: passed after exact-path staging.

## Integration Notes

The protected-preview/app page can still show a stale fretboard if the runtime is serving a stale JS file or the browser has cached the app script itself. The in-page renderer code now requests the cache-busted SVG, so the next verification step should inspect the browser network request for:

`/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`

If the browser still requests `/brand/pedal-steel-fretboard-background.svg` without the query string, the loaded `ui/pedal-steel-fretboard.js` file is stale and Lane 12 should refresh/restart protected preview or update the page script cache-bust.

## Risk Assessment

Risk: low.

Reason:
- This task introduced no implementation changes beyond the prior committed cache-bust.
- Current checks confirm the renderer and tests already include the cache-busted URL.

Rollback:
- No rollback required for this handoff. The implementation rollback, if ever needed, is reverting commit `9562e90`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-fretboard-svg-inpage-cache-bust.md`

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

Lane 12 Self-Hosted Deployment should verify the protected-preview browser is loading current `ui/pedal-steel-fretboard.js` and that the Network panel shows the SVG request with `?v=keyhead-vshape-bce771f`.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12: refresh protected preview or app script cache-bust if the browser still loads stale `ui/pedal-steel-fretboard.js`.
