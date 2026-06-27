# Lane 06 - Explorer Mode Above Filters

## Task Summary

Requested from user smoke feedback: the `Explore mode` control is the primary driver of what a learner is exploring and should live above the filters, not inside the filter grid.

Completed:

- Moved `Explore mode` into its own compact panel above the filter controls.
- Renamed the lower filter section's accessible label from `Explorer controls` to `Explorer filters` to reflect the hierarchy.
- Added a short, subtle line explaining that users should choose the exploration type first, then narrow with filters.
- Preserved the existing `Single grip`, `Harmonized scale path`, and `Single-note finder` behavior.
- Preserved existing Key, Copedent, Scale, Path Family, String group, Notation, fretboard, and card behavior.

Intentionally not changed:

- No backend, Explorer data, fretboard logic, notation logic, harmonized-scale data, corpus, Chroma, embeddings, auth, DNS, deployment, or design assets.

## Files Changed

- `ui/e9-fretboard-explorer.html`
  - Added `.explorer-mode-panel` and `.explorer-mode-panel__copy` styles.
  - Moved `#explorer-explore-mode` above the filters into its own `section`.
  - Changed the filter grid `aria-label` to `Explorer filters`.
- `tests/test_frontend_answer_ui.py`
  - Added assertions that `Explore mode` renders above filters.
  - Added assertions that `Explore mode` is not nested inside the filters.
  - Added assertions for the new mode panel copy and CSS.
- `docs/handoffs/task-completions/2026-06-27-0820-06-explorer-mode-above-filters.md`
  - This handoff.

## Tests And Checks

Run:

```bash
node --check ui/e9-fretboard-explorer.js
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
git diff --check
```

Results:

- `node --check ui/e9-fretboard-explorer.js`: passed.
- `node --check ui/answer-client.js`: passed.
- `node --check ui/pedal-steel-fretboard.js`: passed.
- `tests/test_frontend_answer_ui.py`: `23 passed`.
- `tests/test_pedal_steel_fretboard_ui.py`: `34 passed`.
- `git diff --check`: passed before handoff; rerun after handoff as final gate.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=mode-above-filters-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=mode-above-filters-local`
- Exact URL the user should use: protected-preview URL should use a fresh commit/cache-bust after Lane 12 refresh
- Auth required: no for local
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `0d9540b` at start of task
- Version endpoint: not checked for local static UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local worktree and cache-busted URL
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant to this scoped Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this scoped Explorer smoke
- Who should test this URL: Codex locally; user should test protected-preview after Lane 12 refresh
- Do not test these URLs: uncache-busted Explorer URLs for this slice
- Known caveats: local browser smoke does not prove protected-preview cache freshness

Local smoke result:

- Explorer loaded.
- `Explore mode` exists in `.explorer-mode-panel`.
- Filter grid exists as `.explorer-controls[aria-label="Explorer filters"]`.
- `Explore mode` appears before filters in DOM order.
- `Explore mode` appears visually above filters.
- `Explore mode` is not nested inside the filter grid.
- Switching to `Harmonized scale path` still reveals Path Family and hides String Group.
- No `[object Object]` found.
- No relevant console errors.

Measured local DOM values:

```json
{
  "modeExists": true,
  "filtersExists": true,
  "modeBeforeFiltersInDom": true,
  "modeAboveFiltersVisually": true,
  "modeInsideFilters": false,
  "afterPathMode": {
    "selectedMode": "path",
    "pathFamilyHidden": false,
    "stringGroupHidden": true
  },
  "noObjectObject": true
}
```

## Integration Notes

- `Explore mode` now reads as the primary mode selector rather than another peer filter.
- Existing JS still uses the same `#explorer-explore-mode` id, so no controller changes were needed.
- Existing mode behavior was verified after moving the control.

## Risk Assessment

Risk: low.

Reason:

- Markup/CSS hierarchy change only.
- Existing element ids and JS behavior are unchanged.
- Focused tests cover structure and continued mode options.

Rollback:

- Revert this commit to move `Explore mode` back inside `.explorer-controls`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-0820-06-explorer-mode-above-filters.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked work, including but not limited to:

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
- `Neon Sign/**`
- private/corpus/vector/generated/design/deployment/auth assets or data

## Recommended Next Lane

Lane 12 protected-preview refresh/smoke, then user smoke on the Explorer header/control hierarchy.

## Commit Readiness

Safe to commit after final `git diff --check`, exact-path staging review, and `git diff --cached --check` pass.

## Suggested Next Step

Lane 12: run protected-preview smoke against a cache-busted Explorer URL and verify `Explore mode` is above the filters and mode switching still works.
