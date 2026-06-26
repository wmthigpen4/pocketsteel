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
  - Refreshed Explorer script cache-busts to `explorer-notation-marker-labels-20260626` after protected preview initially served stale Explorer scripts.
- `ui/pedal-steel-fretboard.js`
  - Normalizes optional `labelValues` / `labelOverflowCount`.
  - Renders marker labels with a main notation `<tspan>` and separate overflow-count `<tspan>`.
- `tests/test_frontend_answer_ui.py`
  - Updated Explorer VM assertions to reject plus-suffixed marker shorthand and expect comma-separated notation values.
- `tests/test_pedal_steel_fretboard_ui.py`
  - Added component-level coverage for `labelValues`, `labelOverflowCount`, and separate SVG overflow markup.
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-notation-marker-labels/explorer-notation-marker-labels-local.png`
  - Local browser-smoke screenshot.
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-notation-marker-labels/explorer-notation-marker-labels-protected.png`
  - Protected-preview browser-smoke screenshot.
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

First protected-preview check after implementation commit `ced9955` failed freshness verification because the page still loaded stale script cache-busts:

- `pedal-steel-fretboard.js?v=explorer-compact-copedent-20260625`
- `e9-fretboard-explorer-data.js?v=explorer-compact-copedent-20260625`
- `e9-fretboard-explorer.js?v=explorer-harmonized-scale-clarity-20260626`

Follow-up commit `0b113af` refreshed those Explorer script query strings to `explorer-notation-marker-labels-20260626`.

Protected-preview smoke after `0b113af`: **PASS**.

```text
Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-notation-marker-labels-0b113af
- Cache-busted URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-notation-marker-labels-0b113af
- Exact URL the user should use: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-notation-marker-labels-0b113af
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded in the authenticated in-app browser; the Explorer page loaded with no Access/challenge text.
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 0b113af for this static UI slice
- Version endpoint: http://127.0.0.1:8770/api/version
- Version endpoint result: git_sha=4040a47, git_branch=feature/answer-api, auth_provider=cloudflare_access
- If version endpoint missing, how version is inferred: not applicable; note that `/api/version` reports the backend runtime commit while the browser smoke verifies static UI asset freshness through script URLs.
- Whether app root `/` works: unauthenticated shell check returns Cloudflare Access 302 to login.
- Whether app root `/` is expected to work: yes after Cloudflare Access authentication, but root was not the primary URL for this Explorer-only smoke.
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked in this Explorer-only smoke.
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes.
- Who should test this URL: the user
- Do not test these URLs: stale uncache-busted Explorer URLs or the earlier `ced9955` URL for this fix.
- Known caveats: `/api/version` still reports backend runtime `4040a47`; this does not mean the protected static Explorer page is stale. Browser asset URLs confirmed the refreshed static scripts.
```

Protected script URLs observed:

```text
https://app.steelguitarrag.com/ui/pedal-steel-fretboard.js?v=explorer-notation-marker-labels-20260626
https://app.steelguitarrag.com/ui/e9-fretboard-explorer-data.js?v=explorer-notation-marker-labels-20260626
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.js?v=explorer-notation-marker-labels-20260626
```

Verified in protected browser:

- Notes mode marker labels include actual note labels such as `B, C`, `G, A`, `F#`, and `D`; no `B+`/`G+` shorthand.
- NNS mode marker labels include `3, 3-`, `1`, and `5`; no `3+`.
- Roman mode marker labels include `III, iii`, `I`, and `V`; no `III+`.
- Numbers mode marker labels include `3, 3m`, `1`, and `5`; no plus-suffixed internal shorthand.
- Cards and SVG markers use matching visible marker text, for example `B, C` in Notes mode.
- No `[object Object]`.
- No captured browser console errors.

Screenshot:

- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-notation-marker-labels/explorer-notation-marker-labels-protected.png`

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
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-notation-marker-labels/explorer-notation-marker-labels-protected.png`

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

Lane 15 focused QA or user smoke on the protected-preview Explorer URL.

Suggested prompt:

```text
Lane 12: Run protected-preview smoke for the E9 Fretboard Explorer notation marker label fix. Use a fresh cache-busted URL and verify Notes, NNS, Roman, and Numbers show selected notation values on SVG markers with no plus-suffixed internal shorthand.
```

## Commit Readiness

Safe to commit.

## Suggested Next Step

Run focused QA/user smoke on `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-notation-marker-labels-0b113af`.
