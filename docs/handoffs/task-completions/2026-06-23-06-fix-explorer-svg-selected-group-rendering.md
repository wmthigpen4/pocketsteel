# 2026-06-23 06 Fix Explorer SVG Selected Group Rendering

## Task Summary

- Lane: 06 UX/UI Design.
- Request: fix the E9 Fretboard Explorer so selected string-combination results visibly render on the SVG fretboard itself, not only as cards.
- Completed:
  - Reproduced the user state locally before the patch.
  - Added an optional selected-string-row lane layer to `PedalSteelFretboard`.
  - Wired the Explorer to enable selected string-row lanes when one or more string groups are selected.
  - Emphasized visible filtered markers so selected group positions read as the active SVG state.
  - Refreshed the Explorer script cache-bust so browser smoke loads the patched renderer.
  - Added focused tests for Explorer render options and direct SVG selected-string lane output.
- Intentionally not changed:
  - Backend deterministic Explorer rules.
  - Fret math, string math, Explorer data rows, answer routing, auth, DNS, launchd/tunnel, corpus, Chroma, embeddings, scraping, secrets, private-source data, or visual assets.

## Branch And Head

- Branch: `feature/answer-api`.
- Starting HEAD: `9b23827`.
- Final HEAD / commit: committed in this run; exact hash reported in final response.

## Exact Root Cause

The Explorer card/result strip filtering was working, but the SVG did not provide a clear visual treatment for the selected string group. Selected rows were passed into `mountPedalSteelFretboard`, yet the SVG only drew per-position dots/bands and the Explorer hid labels/tools. That left users seeing a mostly ambiguous fretboard without obvious selected string rows.

Browser reproduction before the fix also showed the risk of stale cached renderer scripts: the page had 5 cards and 15 dot elements for G major / 3-string / 5-6-8, but no selected string-row indicators. The Explorer HTML still used the previous `selected-group-results-20260623` script query.

## Files Changed

- `ui/pedal-steel-fretboard.js`
  - Added optional selected-string-row lane rendering.
  - Added `emphasizeVisibleHighlights` handling.
  - Added `data-selected-string-group-lanes`, `data-selected-string-row`, `data-selected-strings`, and `data-emphasized-visible` hooks.
- `ui/e9-fretboard-explorer.js`
  - Passes `emphasizeStringGroups`, `emphasizeVisibleHighlights`, and `selectedStringGroups` to the fretboard renderer.
  - Enables selected string rows only when explicit string-group filters are active.
- `ui/e9-fretboard-explorer.html`
  - Refreshed Explorer script cache-busts to `selected-svg-render-20260623`.
- `tests/test_frontend_answer_ui.py`
  - Updated script cache-bust assertions.
  - Added Explorer VM assertions for selected string-group render options.
- `tests/test_pedal_steel_fretboard_ui.py`
  - Added direct component test proving selected-string lanes, emphasized markers, and layer order.
- `docs/handoffs/task-completions/assets/2026-06-23-06-fix-explorer-svg-selected-group-rendering/g-major-5-6-8-selected-strings.png`
  - Browser smoke full-page screenshot.
- `docs/handoffs/task-completions/assets/2026-06-23-06-fix-explorer-svg-selected-group-rendering/g-major-5-6-8-fretboard-crop.png`
  - Browser smoke fretboard crop.
- `docs/handoffs/task-completions/2026-06-23-06-fix-explorer-svg-selected-group-rendering.md`
  - This report.

## Browser Smoke Target

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=selected-svg-render-smoke`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=selected-svg-render-smoke`
- Exact URL the user should use: after Lane 12 restart, use the protected-preview URL with a fresh cache-bust supplied by Lane 12
- Auth required: no for local URL
- Auth provider: none for local URL
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `9b23827` plus local scoped UI changes
- Version endpoint: not checked for local static UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local file smoke against current working tree and refreshed script query
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant to this Explorer direct-page smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this Explorer direct-page smoke
- Who should test this URL: Codex locally; Lane 12 should test protected-preview next
- Do not test these URLs: production/DNS URLs for this Lane 06 local fix
- Known caveats: local smoke does not prove protected-preview cache/runtime freshness

## Browser Smoke Evidence

URL tested:

`http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=selected-svg-render-smoke`

States tested:

| State | Cards | SVG highlight groups | SVG dots | Selected string rows | Selected strings | Console errors |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| G major / 3-string / 5-6-8 | 5 | 5 | 15 | 3 | 5, 6, 8 | 0 |
| G major / 3-string / 6-8-10 | 5 | 5 | 15 | 3 | 6, 8, 10 | 0 |
| A major / 3-string / 6-8-10 | 5 | 5 | 15 | 3 | 6, 8, 10 | 0 |
| G major / 2-string / 5-8 | 4 | 4 | 8 | 2 | 5, 8 | 0 |
| Switch back G major / 3-string / 5-6-8 | 5 | 5 | 15 | 3 | 5, 6, 8 | 0 |

Additional browser checks:

- `data-selected-string-group-lanes` rendered for explicit group selections.
- `data-selected-string-row` matched the selected group strings.
- `data-emphasized-visible="true"` matched visible filtered highlight groups.
- No `[object Object]`.
- No raw `five_eight_branch`.
- G major / 5-6-8 now visibly renders selected rows on the SVG.
- A major / 6-8-10 now visibly renders selected rows on the SVG.

Screenshots:

- `docs/handoffs/task-completions/assets/2026-06-23-06-fix-explorer-svg-selected-group-rendering/g-major-5-6-8-selected-strings.png`
- `docs/handoffs/task-completions/assets/2026-06-23-06-fix-explorer-svg-selected-group-rendering/g-major-5-6-8-fretboard-crop.png`

## Tests And Checks

Passed:

- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`
  - `23 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`
  - `33 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
  - `32 passed`
- `git diff --check`

Skipped:

- Full pytest was not requested for this scoped UI fix and was not run. Required focused UI/Explorer checks passed.
- Protected-preview smoke was not run in Lane 06 per task instructions; Lane 12 should run it after commit.

## Integration Notes

- The Explorer still uses backend-provided deterministic rows; no frontend row inference was added.
- The selected-string lane layer is opt-in through renderer options and is currently enabled by Explorer only when explicit string groups are selected.
- The fretboard renderer remains backward-compatible for answer-page fretboard payloads because the new options default off.
- The refreshed script query is required for browser/protected-preview freshness.
- Lane 05 backend metadata is not needed for this fix.

## Risk Assessment

- Risk: low to medium.
- Reason: change is UI-only, opt-in for selected Explorer groups, and covered by focused tests plus local browser smoke.
- Rollback: revert the scoped changes to `ui/pedal-steel-fretboard.js`, `ui/e9-fretboard-explorer.js`, `ui/e9-fretboard-explorer.html`, and the two focused tests.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/pedal-steel-fretboard.js`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-fix-explorer-svg-selected-group-rendering.md`
- `docs/handoffs/task-completions/assets/2026-06-23-06-fix-explorer-svg-selected-group-rendering/g-major-5-6-8-selected-strings.png`
- `docs/handoffs/task-completions/assets/2026-06-23-06-fix-explorer-svg-selected-group-rendering/g-major-5-6-8-fretboard-crop.png`

## Files That Must Not Be Staged

- Parked dirty files listed by `git status --short`, including but not limited to:
  - `README.md`
  - `corpus_metadata/source_policies/README.md`
  - `corpus_metadata/source_registry.json`
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
  - `source-inbox/inventory.json`
  - `ui/brand/steel-guitar-rag-landing-alpha.webm`
  - `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- Protected/private/generated paths:
  - `corpus-private/`
  - `corpus-v2/`
  - Chroma/vector stores
  - embeddings
  - scraper output
  - `.wrangler/`
  - DNS/auth/deployment secrets
  - private source/source-inbox raw/provenance files
  - unrelated `public/`, `ui/brand/`, `Neon Sign/`, and raw design assets

## Recommended Next Lane

Lane 12 Self-Hosted Deployment should run protected-preview smoke against the launchd-supervised runtime and verify the Explorer no longer appears blank/ambiguous for selected groups.

## Commit Readiness

Safe to commit after exact-path staged diff review and `git diff --cached --check`.

## Suggested Next Step

Lane 12 prompt:

```text
Lane 12: Run protected-preview smoke for the committed Explorer selected-string SVG rendering fix. Use a fresh cache-busted Explorer URL. Verify G major / 3-string / 5-6-8, G major / 3-string / 6-8-10, A major / 3-string / 6-8-10, and G major / 2-string / 5-8 show selected string-row lanes and matching SVG highlights. Confirm no console errors, no [object Object], and no raw five_eight_branch.
```
