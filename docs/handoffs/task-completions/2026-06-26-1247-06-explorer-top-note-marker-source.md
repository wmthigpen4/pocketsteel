# 2026-06-26 12:47 - Lane 06 - Explorer Top-Note Marker Source

## Task Summary

Requested: fix the E9 Fretboard Explorer marker labels so visible fretboard marker text is generated from each position's final top note in the selected key/scale, not from chord-quality intervals, harmony arrays, marker ids, or mixed card labels.

Completed:

- Added a UI display mapper from final displayed note to active key/scale degree.
- Changed non-Notes marker labels to use the active scale sequence for the final top note.
- Changed marker `labelValues` to contain final-top-note labels only.
- Kept harmony formulas such as `3, 1, 5` as supporting card/tooltip detail, not marker-label source.
- Refreshed Explorer script cache-busts to force protected preview to load the updated marker-label code.
- Added focused VM regression assertions for G major / 3-string diatonic / 3-4-5 fret 3 and fret 10 marker clusters across Notes, NNS, Roman, and Numbers.

Intentionally not changed:

- Backend Explorer generation and validation.
- Fretboard geometry.
- Copedent/pedal/lever contracts.
- Corpus, Chroma/vector stores, embeddings, scraping, auth, DNS, deployment, protected-preview runtime, and visual assets.

## Files Changed

- `ui/e9-fretboard-explorer.js`
  - Added key/scale note mapping helpers.
  - `activeTopLabel()` now maps the final top note to selected notation mode.
  - `activeLabelValues()` now returns only the final-top-note label for each row.
  - String-action and tooltip/detail copy now references final note-to-notation mapping.
- `ui/e9-fretboard-explorer.html`
  - Refreshed Explorer script cache-busts to `explorer-top-note-marker-source-20260626`.
- `tests/test_frontend_answer_ui.py`
  - Added exact assertions for `B, C`, `3-, 4`, `iii, IV`, `3m, 4`, plus fret 10 `F#, G`, `7°, 1`, `vii°, I`, `7dim, 1`.
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-top-note-marker-source/explorer-top-note-marker-source-local.png`
  - Local smoke screenshot.
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-top-note-marker-source/explorer-top-note-marker-source-protected.png`
  - Protected-preview smoke screenshot.
- `docs/handoffs/task-completions/2026-06-26-1247-06-explorer-top-note-marker-source.md`
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
- Exact browser URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-top-note-marker-source-local
- Cache-busted URL tested: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-top-note-marker-source-local
- Exact URL the user should use: http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-top-note-marker-source-local
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 5577644 at task start
- Version endpoint: not checked for local static UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local URL served from current working tree
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not required for this Explorer-only local smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this Explorer-only local smoke
- Who should test this URL: Codex
- Do not test these URLs: stale uncache-busted Explorer URLs
- Known caveats: protected-preview smoke still required after commit/cache-bust verification
```

Verified:

- Page loaded.
- Notes mode: `marker:3:3-4-5:3-4-5` shows `B, C`; `marker:10:3-4-5:3-4-5` shows `F#, G`.
- NNS mode: same markers show `3-, 4` and `7°, 1`.
- Roman mode: same markers show `iii, IV` and `vii°, I`.
- Numbers mode: same markers show `3m, 4` and `7dim, 1`.
- Cards and SVG markers stay synchronized.
- Harmony strings such as `3, 1, 5` remain visible only as supporting card/detail context.
- No `[object Object]`.
- No captured browser console errors.

Screenshot:

- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-top-note-marker-source/explorer-top-note-marker-source-local.png`

## Protected-Preview Smoke

Passed.

```text
Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-top-note-marker-source-71a163e
- Cache-busted URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-top-note-marker-source-71a163e
- Exact URL the user should use: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-top-note-marker-source-71a163e
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded in the authenticated in-app browser session
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 71a163e
- Version endpoint: http://127.0.0.1:8770/api/version
- Version endpoint result: git_sha=4040a47; static browser freshness was verified by loaded script cache-busts
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: unauthenticated root redirects to Cloudflare Access
- Whether app root `/` is expected to work: yes, behind Cloudflare Access
- Whether `/ui/steel-guitar-rag-mock.html` works: expected yes; not part of this Explorer-only smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user
- Do not test these URLs: stale uncache-busted Explorer URLs
- Known caveats: `/api/version` reports the long-running backend runtime commit; this UI smoke verifies static asset freshness from the loaded script URLs.
```

Loaded scripts included:

- `https://app.steelguitarrag.com/ui/pedal-steel-fretboard.js?v=explorer-top-note-marker-source-20260626`
- `https://app.steelguitarrag.com/ui/e9-fretboard-explorer-data.js?v=explorer-top-note-marker-source-20260626`
- `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.js?v=explorer-top-note-marker-source-20260626`

Verified:

- Notes mode: `marker:3:3-4-5:3-4-5` shows `B, C`; `marker:10:3-4-5:3-4-5` shows `F#, G`.
- NNS mode: same markers show `3-, 4` and `7°, 1`.
- Roman mode: same markers show `iii, IV` and `vii°, I`.
- Numbers mode: same markers show `3m, 4` and `7dim, 1`.
- Marker labels are not derived from harmony formulas such as `3, 1, 5`.
- Cards and SVG markers remain synchronized.
- No `[object Object]`.
- No captured browser console errors.

Screenshot:

- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-top-note-marker-source/explorer-top-note-marker-source-protected.png`

## Integration Notes

- This is a frontend display-source fix only. It does not alter canonical pitch validation or generated Explorer rows.
- The label source of truth is now final displayed top note mapped into `query.display_scale_notes` for the selected scale, then into the selected notation sequence.
- Exact note matching is tried first; pitch-class fallback exists for enharmonic safety.
- Existing row harmony and chord intervals remain available in supporting detail and tooltips.

## Risk Assessment

Risk: Low to medium.

Why: The change affects shared Explorer label/filter behavior, but uses existing payload display fields and preserves fallback behavior when a note cannot be mapped to the active scale.

Rollback: revert the scoped commit touching `ui/e9-fretboard-explorer.js`, `ui/e9-fretboard-explorer.html`, `tests/test_frontend_answer_ui.py`, and this handoff/screenshot.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-1247-06-explorer-top-note-marker-source.md`
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-top-note-marker-source/explorer-top-note-marker-source-local.png`
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-top-note-marker-source/explorer-top-note-marker-source-protected.png`

## Files That Must Not Be Staged

Do not stage unrelated parked changes or untracked files, including but not limited to:

- `README.md`
- `corpus_metadata/**`
- `rag_*.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- corpus/private/generated/vector/deployment/auth artifacts

## Recommended Next Lane

Lane 12 protected-preview smoke after commit.

## Commit Readiness

Safe to commit.

## Suggested Next Step

User or Lane 15 focused smoke should verify the same protected-preview URL:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-top-note-marker-source-71a163e
```
