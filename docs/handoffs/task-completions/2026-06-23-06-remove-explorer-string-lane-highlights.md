# 2026-06-23 06 Remove Explorer String Lane Highlights

## Task Summary

Lane 06 UX/UI Design fixed the Explorer fretboard regression where selecting a string group rendered full horizontal string-row lane highlights across the SVG. The requested behavior was to keep the selected-results strip, cards, counts, row/detail/SVG sync, and localized markers, but remove the whole-string lane overlay.

Completed:

- Removed the shared fretboard renderer path that generated `data-selected-string-group-lanes` and `data-selected-string-row` overlays.
- Removed Explorer mount options that requested selected string-group lane highlighting.
- Kept localized fret/string highlight bands and dots, with `emphasizeVisibleHighlights` still enabled for visible Explorer positions.
- Refreshed the Explorer script query string to `localized-markers-20260623`.
- Added focused tests proving Explorer selected groups render localized markers and no full-string lane DOM.

Intentionally not changed:

- No backend, routing, API, auth, DNS, launchd, tunnel, corpus, Chroma, embeddings, scraping, secrets, or private-source changes.
- No fret/string math or Explorer data changes.
- No changes to answer-page branding or layout.

## Files Changed

- `ui/pedal-steel-fretboard.js`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-remove-explorer-string-lane-highlights.md`
- `docs/handoffs/task-completions/assets/2026-06-23-06-remove-explorer-string-lane-highlights/explorer-g-major-5-6-8-localized.png`
- `docs/handoffs/task-completions/assets/2026-06-23-06-remove-explorer-string-lane-highlights/explorer-g-major-5-8-localized.png`
- `docs/handoffs/task-completions/assets/2026-06-23-06-remove-explorer-string-lane-highlights/answer-g-chord-localized.png`

Deleted files: none.

Generated artifacts: three browser-smoke screenshots listed above.

## Root Cause

Commit `17f2b55` added a selected string-group rendering path to `ui/pedal-steel-fretboard.js` and passed `emphasizeStringGroups` / `selectedStringGroups` from `ui/e9-fretboard-explorer.js`. That created long horizontal row strokes across each selected string. It solved blank/ambiguous SVG feedback but overcorrected into whole-string lane highlighting.

## Fix

The Explorer now filters the returned row/card set and passes those filtered rows as `positions`. The shared fretboard renderer renders those positions using the existing localized grip markers:

- `data-highlight-band`
- `data-highlight-dot`
- `data-highlight-string`
- `data-highlight-strings`

The removed full-lane DOM is:

- `data-selected-string-group-lanes`
- `data-selected-string-row`
- `data-selected-strings`
- `data-selected-string-groups`

## Browser Smoke Target

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=explorer-localized-markers-smoke`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=explorer-localized-markers-smoke`
- Exact URL the user should use: after protected-preview refresh, `/ui/e9-fretboard-explorer.html?v=explorer-localized-markers-smoke`
- Auth required: no for local Explorer page
- Auth provider: none for local Explorer page
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `e22bd08` at task start
- Version endpoint: not used for local smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local filesystem and served script cache-bust
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this task
- Whether `/ui/steel-guitar-rag-mock.html` works: yes on a local dev smoke server
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex locally, Lane 12 protected-preview after commit
- Do not test these URLs: production/public URLs before protected-preview refresh
- Known caveats: port `8770` was running Cloudflare Access auth mode for the answer page, so the answer prompt smoke used the documented local beta smoke server at `http://127.0.0.1:8899/ui/steel-guitar-rag-mock.html?access=beta_user&v=explorer-localized-markers-smoke` without touching the 8770 private-preview process.

## Browser Smoke Results

Explorer page tested at `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?access=beta_user&v=explorer-localized-markers-smoke`.

| State | Cards | SVG highlight groups | Dots | Lane nodes | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| G major / 3-string / 3-4-5 | 8 | 8 | 24 | 0 | Pass |
| G major / 3-string / 5-6-8 | 5 | 5 | 15 | 0 | Pass |
| G major / 3-string / 6-8-10 | 5 | 5 | 15 | 0 | Pass |
| A major / 3-string / 6-8-10 | 5 | 5 | 15 | 0 | Pass |
| G major / 2-string / 5-8 | 4 | 4 | 8 | 0 | Pass |

Additional browser checks:

- No `[object Object]`.
- No raw `five_eight_branch` in learner-facing rendered text.
- Visible cards matched localized SVG highlight groups.
- Highlighted strings matched selected group strings.
- Selected results strip and detail panel remained populated.

Answer page comparison:

- URL tested: `http://127.0.0.1:8899/ui/steel-guitar-rag-mock.html?access=beta_user&v=explorer-localized-markers-smoke`
- Prompt: `How do I play a G chord?`
- Result: fretboard rendered with localized answer-fretboard highlights.
- Highlight groups: 44.
- Highlight dots: 132.
- Lane nodes: 0.
- No `[object Object]`.
- No raw `five_eight_branch`.

Screenshots:

- `docs/handoffs/task-completions/assets/2026-06-23-06-remove-explorer-string-lane-highlights/explorer-g-major-5-6-8-localized.png`
- `docs/handoffs/task-completions/assets/2026-06-23-06-remove-explorer-string-lane-highlights/explorer-g-major-5-8-localized.png`
- `docs/handoffs/task-completions/assets/2026-06-23-06-remove-explorer-string-lane-highlights/answer-g-chord-localized.png`

## Tests And Checks

Passed:

- `git diff --check`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` — 23 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` — 33 passed
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` — 32 passed

Skipped:

- Full pytest was not requested in the latest attached task and was not run.
- Protected-preview smoke was not run in Lane 06 per task instructions.

## Integration Notes

- `ui/e9-fretboard-explorer.html` must be cache-refreshed in protected preview so it fetches `pedal-steel-fretboard.js?v=localized-markers-20260623`.
- The selected-results strip remains the learner-facing indicator for the filtered group.
- The SVG now represents the same filtered rows with localized fret/string positions, matching the answer-page fretboard behavior.

## Risk Assessment

Risk: low.

Reason:

- The full-string lane feature was isolated to one renderer function and two Explorer mount options.
- Focused frontend and fretboard tests passed.
- Local browser smoke covered the exact selected states requested.

Rollback:

- Revert the scoped commit if Lane 12 or user smoke reports unexpected Explorer visibility regressions.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/pedal-steel-fretboard.js`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-remove-explorer-string-lane-highlights.md`
- `docs/handoffs/task-completions/assets/2026-06-23-06-remove-explorer-string-lane-highlights/explorer-g-major-5-6-8-localized.png`
- `docs/handoffs/task-completions/assets/2026-06-23-06-remove-explorer-string-lane-highlights/explorer-g-major-5-8-localized.png`
- `docs/handoffs/task-completions/assets/2026-06-23-06-remove-explorer-string-lane-highlights/answer-g-chord-localized.png`

## Files That Must Not Be Staged

All unrelated parked dirty/untracked files, especially:

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
- `Neon Sign/`
- `corpus-private/`
- `corpus-v2/`
- `source-inbox/provenance.json`
- `.wrangler/`
- `public/`
- `ui/brand/`
- any Chroma/vector store, embedding, scraper, private-source, auth, DNS, tunnel, or deployment secret files.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment: refresh/restart protected-preview runtime and smoke the Explorer URL against the committed cache-bust.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 12: run protected-preview smoke for `/ui/e9-fretboard-explorer.html?v=explorer-localized-markers-smoke` and verify selected Explorer string groups show localized markers only, with no full-string lane overlays.
