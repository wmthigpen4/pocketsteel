# 2026-06-26 21:15 - Lane 06 - Selected Explorer Marker Z-Order

## Task Summary

User smoke reported that selecting the G `6-8-10` harmonized-scale path card at fret 3 did not make the matching yellow fretboard markers visible above the overlapping green `6-7-10` A minor marker. The selected card was correct, but the selected SVG marker group was painted underneath overlapping non-selected marker groups.

Completed the smallest UI fix: selected Explorer marker groups now render last in the SVG position payload, so they paint on top of overlapping marker groups. No fretboard data, backend rules, harmonized-scale rows, controls, notation, or filter behavior was changed.

## Files Changed

- `ui/e9-fretboard-explorer.js`
  - Changed Explorer fretboard marker render order so selected marker groups are passed to the SVG renderer last.
- `tests/test_frontend_answer_ui.py`
  - Added a regression assertion that the selected path marker `marker:3:6-8-10:6-8-10` is the last rendered SVG position.
  - Updated a path-mode label assertion to lookup marker labels by marker id instead of relying on array order.

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git diff --cached --name-only
git diff --check
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

- JS syntax checks passed.
- `tests/test_frontend_answer_ui.py`: 23 passed.
- `tests/test_pedal_steel_fretboard_ui.py`: 34 passed.
- `tests/test_fretboard_explorer.py`: 38 passed.
- `git diff --check`: passed.

## Smoke Target

```text
Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=selected-marker-on-top-local
- Cache-busted URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=selected-marker-on-top-local
- Exact URL the user should use: after protected-preview refresh, use the new committed cache-busted Explorer URL from Lane 12
- Auth required: no for local smoke
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 127833e plus this local uncommitted patch at smoke time
- Version endpoint: not checked for local UI-only smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local source files and cache-busted static URL
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant to this scoped Explorer marker smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this scoped Explorer marker smoke
- Who should test this URL: Codex locally; the user after Lane 12 protected-preview refresh
- Do not test these URLs: stale protected URL `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=compact-controls-672ec51` for this fix
- Known caveats: protected preview was not restarted in this Lane 06 task
```

Local browser smoke result:

- Explorer loaded.
- Switched to `Harmonized scale path`.
- First selected card remained `G — G`, fret `3`, strings `6-8-10`.
- SVG marker count: 8.
- Selected marker id: `marker:3:6-8-10:6-8-10`.
- Last rendered SVG marker id: `marker:3:6-8-10:6-8-10`.
- Last rendered marker had `data-explorer-selected-marker="true"`.
- No `[object Object]`.
- Console warnings/errors: none.

## Integration Notes

Root cause: Explorer grouped rows into marker positions correctly, but sorted the selected marker group first before mounting the SVG. Since SVG paints later siblings on top, the selected yellow `6-8-10` marker rendered underneath the overlapping green `6-7-10` marker.

Fix: keep all marker grouping behavior intact, but pass non-selected marker groups first and the selected marker group last.

No API, backend, payload, notation, marker label, or harmonized-scale rule changes were made.

## Risk Assessment

Risk: low. The change only affects SVG paint order for the currently selected Explorer marker group. It does not alter row filtering, row data, marker grouping, or fretboard geometry.

Rollback: revert the `sortedMarkerGroups` ordering change in `ui/e9-fretboard-explorer.js` and the corresponding regression assertions.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-2115-06-selected-explorer-marker-z-order.md`

## Files That Must Not Be Staged

All unrelated parked dirty/untracked work, especially:

- `README.md`
- `corpus_metadata/**`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- corpus/private/generated/design/deployment/auth files

## Recommended Next Lane

Lane 12 protected-preview restart/smoke with a fresh Explorer cache-bust, then user smoke the selected-marker overlap case.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12: restart/refresh protected preview and smoke `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=selected-marker-on-top-<commit>` after this commit, verifying the selected `6-8-10` path marker paints above overlapping `6-7-10` markers.
