# 2026-06-26 12:19 - Lane 06 - Explorer Notation Marker Labels

## Task Summary

Requested: finish the E9 Fretboard Explorer four-way notation selector by making the visible fretboard marker labels show selected notation-mode values instead of internal/cluster shorthand such as `3+`, `B+`, `Fretboard 3`, or `Fretboard 3+`.

Completed:

- Replaced the old `labels[0] + "+"` marker-cluster shorthand with comma-separated selected notation values.
- Added optional `labelValues` and `labelOverflowCount` fields through the Explorer-to-fretboard display payload.
- Rendered overflow count as a separate SVG `<tspan>` so a count like `+2` is visually distinct from musical notation.
- Updated card marker chips to show the same comma-separated notation values and a separate count badge when needed.
- Added focused tests for comma-separated marker labels, absence of `3+` shorthand, and separated SVG overflow markup.

Intentionally not changed:

- Backend Explorer generation and validation.
- Fretboard geometry.
- Copedent/pedal/lever contracts.
- Corpus, Chroma/vector stores, embeddings, scraping, auth, DNS, deployment, protected-preview runtime, and visual assets.

## Files Changed

- `ui/e9-fretboard-explorer.js`
  - `markerLabelForGroup()` now returns the first one or two notation values joined by `, `.
  - Added `markerLabelValuesForGroup()` and `markerOverflowCountForGroup()`.
  - Marker positions now pass `labelValues` and `labelOverflowCount` to the fretboard renderer.
  - Active result marker chips mirror the marker label and render overflow count separately.
- `ui/e9-fretboard-explorer.html`
  - Added compact styling for separate card-side overflow count badges.
- `ui/pedal-steel-fretboard.js`
  - Normalizes optional `labelValues` / `labelOverflowCount`.
  - Renders marker labels with a main notation `<tspan>` and separate overflow-count `<tspan>`.
- `tests/test_frontend_answer_ui.py`
  - Updated Explorer VM assertions to reject plus-suffixed marker shorthand and expect comma-separated notation values.
- `tests/test_pedal_steel_fretboard_ui.py`
  - Added component-level coverage for `labelValues`, `labelOverflowCount`, and separate SVG overflow markup.
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-notation-marker-labels/explorer-notation-marker-labels-local.png`
  - Local browser-smoke screenshot.
- `docs/handoffs/task-completions/2026-06-26-1219-06-explorer-notation-marker-labels.md`
  - This handoff.

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

- `tests/test_frontend_answer_ui.py`: 23 passed.
- `tests/test_pedal_steel_fretboard_ui.py`: 34 passed.
- `tests/test_fretboard_explorer.py`: 38 passed.

## Local Browser Smoke

```text
Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-notation-marker-labels-local
- Cache-busted URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-notation-marker-labels-local
- Exact URL the user should use: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-notation-marker-labels-local
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 1ede5b5 at task start
- Version endpoint: not checked for local static UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local URL served from current working tree
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not required for this Explorer-only local smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this Explorer-only local smoke
- Who should test this URL: Codex
- Do not test these URLs: protected-preview or production URLs for this local UI slice
- Known caveats: protected-preview cache-bust/restart was not performed in this Lane 06 implementation slice
```

Verified in browser:

- Page loads.
- Notes mode marker labels include notation values such as `B, C`, `G, A`, `F#, G`.
- NNS mode marker labels include values such as `3, 3-`, `1`, `5`.
- Roman mode marker labels include values such as `III, iii`, `I`, `V`.
- Numbers mode marker labels include values such as `3, 3m`, `1`, `5`.
- Marker labels no longer show old plus-suffixed shorthand such as `3+` or `B+`.
- Cards and SVG markers use matching marker text.
- No `[object Object]`.
- Browser console had no captured errors.

Screenshot:

- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-notation-marker-labels/explorer-notation-marker-labels-local.png`

## Protected-Preview Smoke

Not run in this Lane 06 implementation pass.

Protected-preview should be run by Lane 12 after commit with a fresh cache-busted URL:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-notation-marker-labels-<commit>
```

## Integration Notes

- This is a UI display-model fix only. Existing backend top-note/top-interval data remains the source for notation values.
- Existing marker ids are preserved internally for hover/select wiring.
- User-facing marker labels now use musical notation values, while count indicators are separate display elements.
- Current G major 3-string data produced two-value marker clusters in smoke; no natural `+N` overflow case appeared in that dataset, so the separate overflow behavior is covered by focused component tests.

## Risk Assessment

Risk: Low to medium.

Why: The change touches the shared fretboard renderer, but only adds optional display fields and preserves the existing label fallback. Focused Explorer and fretboard renderer tests passed.

Rollback: revert the scoped commit touching `ui/e9-fretboard-explorer.js`, `ui/e9-fretboard-explorer.html`, `ui/pedal-steel-fretboard.js`, `tests/test_frontend_answer_ui.py`, `tests/test_pedal_steel_fretboard_ui.py`, and this handoff/screenshot.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `ui/pedal-steel-fretboard.js`
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `docs/handoffs/task-completions/2026-06-26-1219-06-explorer-notation-marker-labels.md`
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-notation-marker-labels/explorer-notation-marker-labels-local.png`

## Files That Must Not Be Staged

Do not stage unrelated parked changes or untracked files, including but not limited to:

- `README.md`
- `corpus_metadata/**`
- `docs/handoffs/task-completions/integration-status.md` unless refreshed in a separate Repo Steward step
- `rag_*.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- corpus/private/generated/vector/deployment/auth artifacts

## Recommended Next Lane

Lane 12 protected-preview smoke.

Suggested prompt:

```text
Lane 12: Run protected-preview smoke for the E9 Fretboard Explorer notation marker label fix. Use a fresh cache-busted URL and verify Notes, NNS, Roman, and Numbers show selected notation values on SVG markers with no plus-suffixed internal shorthand.
```

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit the scoped Lane 06 UI/test/handoff files, then run Lane 12 protected-preview smoke.
