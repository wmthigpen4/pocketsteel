# 2026-06-26 20:57 - Lane 06 - Explorer View Chart Reference Action

## Task Summary

Moved the E9 Explorer `View chart` control out of the primary filter/control area and into the header reference/action area alongside `Glossary` and `Back to app`.

Completed:

- Kept `Glossary` as a reference action.
- Moved `View chart` to the same header action group.
- Preserved the existing `id="explorer-copedent-open"` hook and dialog behavior.
- Removed `View chart` from the E9 setup control row so it is no longer visually grouped with filters.
- Added a regression assertion that the chart trigger is absent from `.explorer-controls` and present in `.explorer-header-actions`.

Intentionally not changed:

- No backend logic.
- No Explorer data rows.
- No fretboard math, notation, or marker logic.
- No corpus, Chroma, embeddings, scraping, auth, DNS, deployment, or visual assets.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`

## Tests And Checks

Passed:

```bash
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

- `tests/test_frontend_answer_ui.py`: 23 passed
- `tests/test_pedal_steel_fretboard_ui.py`: 34 passed
- `tests/test_fretboard_explorer.py`: 38 passed

## Browser Smoke

Smoke Target:

```text
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=view-chart-reference-local
- Cache-busted URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=view-chart-reference-local
- Exact URL the user should use: pending protected-preview smoke after commit
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 03d74e9 before commit
- Version endpoint: not checked for local static UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local working tree served by same-origin preview
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: yes in protected preview; not required for this Explorer-only local smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex locally; user after protected-preview smoke
- Do not test these URLs: uncache-busted Explorer URLs for this slice
- Known caveats: local smoke proves current working-tree UI behavior only, not protected-preview cache freshness
```

Local smoke result:

- `View chart` appeared in `.explorer-header-actions`.
- `View chart` no longer appeared inside `.explorer-controls`.
- `View chart` used the same `explorer-back` reference-action style family as `Glossary`.
- Clicking `View chart` opened the selected E9 setup chart dialog.
- Closing the chart dialog worked.
- Clicking `Glossary` still opened the glossary dialog.
- No `[object Object]`.
- No relevant browser console errors.

## Integration Notes

- The chart dialog remains controlled by the existing `#explorer-copedent-open` element id, so no JS change was needed.
- This is a visual/placement correction only.
- Protected-preview smoke should use a fresh cache-busted Explorer URL after commit.

## Risk Assessment

Risk: low.

Reason:

- HTML-only placement change plus focused regression test.
- Existing JS event binding continues to target the same button id.
- Local browser smoke verified dialog behavior after moving the button.

Rollback:

- Revert the two scoped files from the commit if the header action placement is rejected.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-2057-06-explorer-view-chart-reference-action.md`

## Files That Must Not Be Staged

- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `ui/brand/steel-guitar-rag-landing-alpha.webm`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- Any untracked corpus, design, brand, deployment, private-data, or source-inbox files.

## Recommended Next Lane

Lane 12 protected-preview smoke for the cache-busted Explorer URL after this commit.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Run protected-preview smoke against:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=view-chart-reference-<commit>
```
