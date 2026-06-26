# Lane 06 - Explorer Marker Script Cache Bust

## Task Summary
- Requested scope: fix unreadable E9 Fretboard Explorer marker labels.
- Follow-up found during protected-preview smoke: the protected page still loaded the old Explorer script query string, so it reproduced the old long interval labels even after the marker readability commit.
- Completed: refreshed the `e9-fretboard-explorer.js` script query string and added a focused HTML assertion.
- Intentionally not changed: Explorer data, backend, fretboard geometry, pedal/lever logic, corpus, Chroma, scraping, embeddings, auth, DNS, deployment, and brand assets.

## Files Changed
- `ui/e9-fretboard-explorer.html`
  - Changed `e9-fretboard-explorer.js` query string to `explorer-marker-readability-20260626`.
- `tests/test_frontend_answer_ui.py`
  - Updated the script-cache assertion and added a negative assertion for the stale Explorer script query string.
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-marker-readability/protected-explorer-marker-readability.png`
  - Protected-preview smoke screenshot.
- `docs/handoffs/task-completions/2026-06-26-1030-06-explorer-marker-script-cache-bust.md`
  - This handoff.

## Smoke Target
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-marker-readability-20260626b`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-marker-readability-20260626b`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-marker-readability-20260626b`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: already authenticated in the in-app browser; page loaded without an Access challenge
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `0ec8932` for the marker-rendering commit; this cache-bust follow-up commit to be recorded after commit
- Version endpoint: not checked
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: protected page loaded changed script path from workspace
- Whether app root `/` works: not checked
- Whether app root `/` is expected to work: not part of this task
- Whether `/ui/steel-guitar-rag-mock.html` works: not checked
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not part of this task
- Who should test this URL: the user and Lane 15
- Do not test these URLs: stale Explorer URLs without `?v=explorer-marker-readability-20260626b`
- Known caveats: `/api/version` was not checked in this UI-only browser smoke.

## Protected Browser Smoke Result
- PASS: protected page loaded the fresh script `e9-fretboard-explorer.js?v=explorer-marker-readability-20260626`.
- PASS: rendered marker labels are short numeric labels: `1+`, `2+`, `3`, etc.
- PASS: `longLabels` was empty.
- PASS: cards include marker text and `data-marker-id`.
- PASS: clicking a card left one selected card and one selected SVG marker.
- PASS: no `[object Object]`.
- PASS: no console errors captured.
- Screenshot: `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-marker-readability/protected-explorer-marker-readability.png`

## Tests And Checks
- `node --check ui/e9-fretboard-explorer.js` - passed
- `node --check ui/e9-fretboard-explorer-data.js` - passed
- `node --check ui/answer-client.js` - passed
- `node --check ui/pedal-steel-fretboard.js` - passed
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - 23 passed
- `git diff --check` - passed

## Integration Notes
- The main marker readability behavior is in commit `0ec8932`.
- This follow-up is required for protected-preview freshness; without it, the page can still mount the old cached Explorer script.

## Risk Assessment
- Risk: low.
- Reason: HTML cache-bust/test-only follow-up.
- Rollback: revert this cache-bust commit and the page will return to the prior script query string.

## Human Decision Needed
- No.

## Safe-To-Stage Exact File List
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-26-1030-06-explorer-marker-script-cache-bust.md`
- `docs/handoffs/task-completions/assets/2026-06-26-06-explorer-marker-readability/protected-explorer-marker-readability.png`

## Files That Must Not Be Staged
- Any unrelated dirty or untracked files outside the safe-to-stage list.
- Specifically avoid parked corpus/source files, `rag_*.py`, `source-inbox/`, `ui/brand/`, `public/brand/`, `Neon Sign/`, deployment artifacts, private/generated data, and unrelated handoffs.

## Recommended Next Lane
- Lane 15 focused protected-preview QA for Explorer marker readability.

## Commit Readiness
- Safe to commit.

## Suggested Next Step
- Lane 15: smoke `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-marker-readability-20260626b` and verify numeric marker labels, marker-linked cards, tooltip/detail access, and no console errors.
