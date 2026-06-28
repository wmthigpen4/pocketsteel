# 2026-06-27 22:33 - Lane 06 - Chord Map Card Label Cleanup

## Task Summary

User smoke found two Explorer Chord / Voicing Finder display issues:

- Chord-map candidate card field text could visually write over itself in narrow cards.
- SVG marker labels above chord-map grips were ambiguous for chord targets such as F dominant 7.

Completed a scoped UI fix:

- Chord-map candidate cards now use a dedicated label/value field layout with wrapping.
- Chord-map candidate cards have a slightly larger minimum card width.
- Chord / Voicing Finder fretboard rendering disables SVG top labels, leaving top-note/marker context in the cards and tooltip/detail surfaces.
- Other Explorer modes keep SVG marker labels.

Intentionally not changed:

- Music rules, chord/voicing logic, Explorer data, backend routing, corpus, Chroma, embeddings, auth, DNS, deployment, or brand assets.

## Files Changed

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-2233-06-chord-map-card-label-cleanup.md`

## Tests And Checks

Passed:

- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/answer-client.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - 24 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - 36 passed

Passed after implementation:

- `git diff --check`
- `git diff --cached --check`
- staged diff review

## Browser Smoke

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=chord-map-label-cleanup-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=chord-map-label-cleanup-local`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-label-cleanup-bec3847`
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `bec3847`
- Version endpoint: not checked for local static UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: direct local static file smoke
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not relevant to this UI slice
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this UI slice
- Who should test this URL: Codex locally; user after protected-preview smoke
- Do not test these URLs: stale `?v=string-action-labels-d5a8b63` for this fix
- Known caveats: local browser smoke does not prove protected-preview cache freshness

Local smoke result: PASS.

Verified:

- Explorer loaded.
- Chord / Voicing Finder selected.
- F dominant 7 scenario rendered candidate cards.
- First card field rows used two-column label/value CSS with `overflow-wrap: anywhere`.
- SVG marker top labels were absent in Chord / Voicing Finder mode.
- Marker tooltips/aria labels remained available.
- No `[object Object]`.
- No page-level horizontal overflow.
- No relevant console errors.

Protected-preview smoke result: PASS.

Smoke Target:

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-label-cleanup-bec3847`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-label-cleanup-bec3847`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-label-cleanup-bec3847`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: already authenticated in the in-app browser
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `bec3847`
- Version endpoint: not checked for this static UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: page served the refreshed `e9-fretboard-explorer.js?v=chord-map-label-cleanup-20260627` script and protected DOM behavior matched the commit
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not relevant to this direct Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this direct Explorer smoke
- Who should test this URL: the user
- Do not test these URLs: stale `?v=string-action-labels-d5a8b63` for this fix
- Known caveats: this verifies cache-busted static/browser behavior, not a protected-preview restart

Verified:

- Chord / Voicing Finder with `F` + `Dominant 7`.
- Refreshed Explorer script cache-bust loaded.
- Candidate card fields used label/value grid rows with `overflow-wrap: anywhere`.
- SVG marker top labels were absent in Chord / Voicing Finder mode.
- No `[object Object]`.
- No page-level horizontal overflow.
- No relevant console errors.

## Integration Notes

- `renderFretboard(rows, options = {})` now accepts `showHighlightLabels: false`.
- Chord / Voicing Finder calls `renderFretboard(rowsForMap, { showHighlightLabels: false })`.
- Path, scale, single-grip, and other Explorer modes keep default marker labels.

## Risk Assessment

Risk: Low.

Reason: This is a scoped presentation fix with focused tests and local browser smoke. It does not alter deterministic music logic or payload data.

Rollback: revert the scoped UI/test commit.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-2233-06-chord-map-card-label-cleanup.md`

## Files That Must Not Be Staged

- Unrelated dirty or untracked work listed by `git status --short`
- `README.md`
- corpus/source/provenance files
- `ui/brand/`
- `public/`
- `Neon Sign/`
- deployment/auth/DNS/secrets files
- private/generated/source-inbox data

## Recommended Next Lane

Lane 12 protected-preview smoke after the scoped commit.

## Commit Readiness

Safe to commit. Implementation commit created:

- `bec3847 fix: clean up chord map card labels`

## Suggested Next Step

User smoke:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-label-cleanup-bec3847`
