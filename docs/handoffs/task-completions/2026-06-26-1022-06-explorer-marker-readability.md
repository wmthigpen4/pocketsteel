# Lane 06 - Explorer Marker Readability

## Task Summary
- Requested: fix unreadable inline fretboard marker labels in the E9 Fretboard Explorer.
- Completed: replaced default SVG marker labels with short marker numbers (`1`, `1+`, etc.), linked cards to those marker numbers, and preserved full notes/intervals/pedals/levers in tooltips and selected-card detail.
- Intentionally not changed: backend Explorer rules, fretboard geometry, Explorer data rows, copedent data, corpus, Chroma, scraping, embeddings, auth, DNS, deployment, and visual brand assets.

## Files Changed
- `ui/e9-fretboard-explorer.js`
  - Groups same-fret/string-group positions into numbered markers.
  - Adds `data-marker-id` to visible result cards.
  - Adds selected/hover marker synchronization between cards and SVG markers.
  - Keeps full harmonic detail in tooltip and selected detail.
- `ui/e9-fretboard-explorer.html`
  - Adds compact `Marker N` card badge styling.
  - Adds selected/hover SVG marker emphasis styling.
- `tests/test_frontend_answer_ui.py`
  - Adds assertions that SVG labels are short marker IDs, not note/interval blobs.
  - Adds assertions that cards expose marker IDs and card hover/click maps back to SVG marker state.
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-marker-readability/local-explorer-marker-readability.png`
  - Local browser smoke screenshot.
- `docs/handoffs/task-completions/2026-06-26-1022-06-explorer-marker-readability.md`
  - This handoff.

## Smoke Target
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-marker-readability-20260626`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-marker-readability-20260626`
- Exact URL the user should use: after protected-preview restart/smoke, use the Lane 12 cache-busted protected URL
- Auth required: no for local
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `51006ae` at task start; final commit to be recorded after commit
- Version endpoint: not checked for local UI smoke
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: local workspace file smoke
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not part of this task
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not part of this task
- Who should test this URL: Codex locally; Lane 12/user on protected preview after commit
- Do not test these URLs: production without cache-busting for this change
- Known caveats: local smoke does not prove protected-preview cache freshness.

## Browser Smoke Result
- PASS: default SVG marker labels are numeric and short.
- PASS: no long labels were detected in the rendered marker set.
- PASS: full marker tooltip detail remains available via SVG marker interaction.
- PASS: card text includes `Marker N`, and every visible card has `data-marker-id`.
- PASS: clicking a card sets one selected marker.
- PASS: no `[object Object]` in page text.
- PASS: Notes/Intervals controls remain present.
- PASS: no console errors captured during local smoke.
- Screenshot: `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-marker-readability/local-explorer-marker-readability.png`

## Tests And Checks
- `node --check ui/e9-fretboard-explorer.js` - passed
- `node --check ui/e9-fretboard-explorer-data.js` - passed
- `node --check ui/answer-client.js` - passed
- `node --check ui/pedal-steel-fretboard.js` - passed
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - 23 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - 34 passed
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - 38 passed
- `git diff --check` - passed

## Integration Notes
- This is a rendering-model fix: the SVG no longer tries to teach harmonic content inline.
- Full learner detail remains available in cards, selected detail, and marker tooltip/aria labels.
- Card-to-marker discoverability is now explicit through `Marker N` badges and hover/selected marker styles.
- No API/schema changes.

## Risk Assessment
- Risk: low.
- Reason: frontend-only, scoped to Explorer marker presentation and tests.
- Rollback: revert the scoped commit to restore previous marker labels and styles.

## Human Decision Needed
- No.

## Safe-To-Stage Exact File List
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-1022-06-explorer-marker-readability.md`
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-marker-readability/local-explorer-marker-readability.png`

## Files That Must Not Be Staged
- Any unrelated dirty or untracked files outside the safe-to-stage list.
- Specifically avoid staging parked corpus/source files, `rag_*.py`, `source-inbox/`, `ui/brand/`, `public/brand/`, `Neon Sign/`, deployment artifacts, private/generated data, and existing unrelated handoffs.

## Recommended Next Lane
- Lane 12 protected-preview restart/smoke, then Lane 15 focused browser QA for Explorer marker readability.

## Commit Readiness
- Safe to commit.

## Suggested Next Step
- Lane 12: run protected-preview smoke against `/ui/e9-fretboard-explorer.html?v=<commit-or-slice-cachebuster>` and verify numeric marker labels, card-marker mapping, and tooltip/detail discoverability.
