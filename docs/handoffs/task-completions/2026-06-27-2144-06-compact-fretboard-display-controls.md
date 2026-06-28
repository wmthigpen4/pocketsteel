# Lane 06 - Compact Fretboard Display Controls

## Task Summary

User smoke feedback on the E9 Fretboard Explorer identified two learner-facing clutter issues:

- Remove the active-result summary text such as `all 3-string groups: 33 visible positions` and `Cards match the SVG markers below.`
- Shrink the marker-detail control into a compact on/off toggle and place Notation, Pitch register, and Labels in one simpler row.

Completed the scoped UI cleanup. No backend, fretboard music rules, notation logic, Explorer data, corpus, Chroma, auth, DNS, deployment, private data, or assets were changed.

## Files Changed

- `ui/e9-fretboard-explorer.html`
  - Added a single `explorer-fretboard-tools` row around Notation, Pitch register, and Labels.
  - Renamed learner-facing `Marker detail` label to `Labels`.
  - Replaced the wider `String labels` pill with a compact switch-style toggle.
  - Kept control help text accessible but visually hidden to reduce page height.
  - Refreshed the `e9-fretboard-explorer.js` script cache-bust so protected preview fetches the updated active-result renderer.
- `ui/e9-fretboard-explorer.js`
  - Removed the normal active-result header text above the cards.
  - Left empty-state, path rail, note finder, voicing identifier, and chord finder text paths intact.
- `tests/test_frontend_answer_ui.py`
  - Added assertions for the compact display controls row and switch markup.
  - Added assertions that the removed active-result summary strings do not render.
  - Updated the Explorer script cache-bust assertion to lock the fresh UI slice.

## Tests And Checks

Commands run:

```bash
node --check ui/e9-fretboard-explorer.js
node --check ui/pedal-steel-fretboard.js
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
git diff --check
```

Results:

- `node --check ui/e9-fretboard-explorer.js`: passed
- `node --check ui/pedal-steel-fretboard.js`: passed
- `node --check ui/answer-client.js`: passed
- `tests/test_frontend_answer_ui.py`: 24 passed
- `tests/test_pedal_steel_fretboard_ui.py`: 36 passed
- `git diff --check`: passed

## Browser Smoke

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=compact-fretboard-tools-local`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=compact-fretboard-tools-local`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=compact-fretboard-tools-e974e64`
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `e1d1ede` plus local scoped UI changes before commit
- Version endpoint: not checked for local static-file smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local working tree files loaded by local same-origin server
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not relevant to this scoped Explorer check
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not relevant to this scoped Explorer check
- Who should test this URL: Codex locally; Lane 12/user on protected preview after cache-bust
- Do not test these URLs: unversioned protected Explorer URL for freshness-sensitive visual QA
- Known caveats: Browser viewport override did not force the exact requested width, but the measured page reported no horizontal overflow.

Smoke results:

- Explorer loaded.
- Active result summary text no longer rendered in the active-result card area.
- Notation, Pitch register, and Labels controls rendered before the card list/fretboard in the same display-control row.
- `Marker detail` text was not present.
- String labels toggle measured compactly at about 129px by 30px.
- Toggle switched on and mounted string-action labels in the SVG.
- No `[object Object]`.
- No console errors.
- No page-level horizontal overflow in the measured browser viewport.

Additional protected-preview finding before the cache-bust update:

- URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=compact-fretboard-tools-8538645`
- Result: Cloudflare Access was already authenticated and the page loaded, but the active-result summary text still appeared because the HTML was requesting stale `e9-fretboard-explorer.js?v=explorer-octave-register-20260627`.
- Follow-up fix in this slice: changed the Explorer script URL to `e9-fretboard-explorer.js?v=compact-fretboard-tools-20260627`.

Protected-preview verification after cache-bust update:

- URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=compact-fretboard-tools-e974e64`
- Cloudflare Access login result: already authenticated in the in-app browser.
- Result: passed.
- Verified `e9-fretboard-explorer.js?v=compact-fretboard-tools-20260627` was present in page scripts.
- Verified the active-result summary text was removed.
- Verified the compact Labels toggle rendered at about 129px by 30px.
- Verified `Marker detail` text was absent.
- Verified no `[object Object]`, no console errors, and no horizontal overflow in the measured viewport.

## Integration Notes

- This is a presentation-only change.
- Existing string-action label behavior was preserved; the control is only visually compacted.
- Existing active-result cards still render and still drive SVG markers.
- The removed active-result header text was redundant with the cards and fretboard state.

## Risk Assessment

Risk: Low.

Reason: The change removes redundant copy and changes only layout/markup/CSS around existing controls. Focused frontend tests and browser smoke passed.

Rollback: Revert `ui/e9-fretboard-explorer.html`, `ui/e9-fretboard-explorer.js`, and the related test assertions.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-27-2144-06-compact-fretboard-display-controls.md`

## Files That Must Not Be Staged

- Any corpus, Chroma/vector, embedding, scraper, auth, DNS, deployment, private-source, `source-inbox`, `public/`, `ui/brand/`, `Neon Sign/`, generated report, or unrelated parked worktree files.

## Recommended Next Lane

User smoke on the verified protected-preview URL.

## Commit Readiness

Safe to commit.

## Suggested Next Step

User smoke: open `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=compact-fretboard-tools-e974e64` and verify the active-result summary is gone and the Labels switch is compact.
