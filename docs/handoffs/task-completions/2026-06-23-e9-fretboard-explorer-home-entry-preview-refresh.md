# 2026-06-23 Lane 12 - E9 Fretboard Explorer Home Entry Preview Refresh

## Task Summary

Lane 12 refreshed the protected-preview app page for the committed E9 Fretboard Explorer home-entry slice and verified that the app page links to the Explorer route.

Completed:

- Updated the app-page script cache-busts to `e9-explorer-home-entry-20260623`.
- Restarted the protected-preview runtime on `127.0.0.1:8770`.
- Verified the app page loads through Cloudflare Access.
- Verified the app page shows `Explore the E9 Fretboard`.
- Verified the entry link points to `/ui/e9-fretboard-explorer.html`.
- Verified the Explorer route loads through Cloudflare Access.
- Verified `/brand/pedal-steel-fretboard-background.svg` loads on protected preview.

Intentionally not changed:

- Product logic.
- Auth, DNS, Cloudflare Access policy, tunnel config, deployment config, Chroma/vector stores, embeddings, corpus/source data, scraper output, or private source data.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`
- Explorer URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-home-entry-20260623`
- Asset URL tested: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=e9-explorer-home-entry-20260623`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; protected pages loaded without Access login screen
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `3081261` or later containing `feat: add e9 explorer home entry`
- Version endpoint: `/api/version`
- Version endpoint result: local tunnel target returned `{"git_sha":"3081261","git_branch":"feature/answer-api","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- Protected browser `/api/version` note: direct navigation to `https://app.steelguitarrag.com/api/version` was blocked by the browser automation client with `net::ERR_BLOCKED_BY_CLIENT`; the runtime version was confirmed from the local tunnel target.
- Whether app root `/` works: not tested in this task
- Whether app root `/` is expected to work: not the target for this task
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Lane 15 / the user after Lane 15 full protected-preview smoke
- Do not test these URLs: uncached stale variants for this slice
- Known caveats: raw SVG direct navigation can emit a browser-runtime warning unrelated to the Explorer app page

## Files Changed

- `ui/steel-guitar-rag-mock.html`
  - Refreshed `answer-client.js` and `pedal-steel-fretboard.js` query strings to `e9-explorer-home-entry-20260623`.
- `tests/test_frontend_answer_ui.py`
  - Updated cache-bust assertion for the app page.
- `tests/test_same_origin_smoke_server.py`
  - Updated same-origin app-page cache-bust assertion.
- `docs/handoffs/task-completions/2026-06-23-e9-fretboard-explorer-home-entry-preview-refresh.md`
  - Added this handoff.

Deleted files: none.

Generated artifacts: none.

## Protected Preview Restart Evidence

Command class used: existing Lane 12 protected-preview workflow via detached `screen` session.

Observed:

- `screen` session: `steel-rag-private-preview`
- Listener: `Python ... TCP 127.0.0.1:8770 (LISTEN)`
- `/api/version` on local tunnel target reported:

```json
{
  "git_sha": "3081261",
  "git_branch": "feature/answer-api",
  "python_module": "steel_guitar_rag.api",
  "retrieval_mode": "hybrid_private_first",
  "auth_provider": "cloudflare_access"
}
```

## Browser Smoke Result

Pass with one noted version-route automation caveat.

App page:

- URL loaded: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`
- Cloudflare Access result: succeeded
- `Explore the E9 Fretboard`: present
- Link target: `/ui/e9-fretboard-explorer.html`
- Resolved link: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html`
- Script cache-busts observed:
  - `answer-client.js?v=e9-explorer-home-entry-20260623`
  - `pedal-steel-fretboard.js?v=e9-explorer-home-entry-20260623`
- `[object Object]`: not present

Explorer route:

- URL loaded: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-home-entry-20260623`
- Cloudflare Access result: succeeded
- Page identified as E9 Fretboard Explorer: yes
- `Showing validated positions`: present
- Expanded keys observed: `G`, `C`, `D`, `F`, `Bb`, `Eb`
- Explorer references `/brand/pedal-steel-fretboard-background.svg`: yes
- Explanation UI present: yes
- `[object Object]`: not present

Asset route:

- URL loaded: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=e9-explorer-home-entry-20260623`
- Cloudflare Access result: succeeded
- SVG loaded: yes
- `viewBox="0 0 1600 420"`: present

Console errors:

- App page: no app-page error observed.
- Explorer page: no Explorer app-page error observed.
- Direct raw SVG tab produced a browser-runtime warning: `TypeError: Cannot use 'in' operator to search for 'animation' in undefined`. This matched the known raw-SVG-tab caveat and was not observed as an Explorer app-page failure.

## Tests And Checks

Run:

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - `23 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - `31 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - `28 passed`
- `.venv/bin/python -m pytest tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_ui_and_answer_client -q` - `1 passed`
- `.venv/bin/python -m pytest -q` - `808 passed`
- `git diff --check`

## Integration Notes

- Lane 15 can run full protected-preview app smoke from the home page into the Explorer using:
  - `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`
  - `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-home-entry-20260623`
- The app page now carries slice-specific script cache-busts for the home-entry verification.
- The Explorer page still carries its own existing `e9-explorer-explanation-ui-20260623` script cache-busts; that was not changed because this task targeted the app-page home entry.

## Risk Assessment

Risk: low.

Why:

- The implementation change is limited to static query strings on app-page scripts and matching tests.
- No product logic, routing, auth, DNS, corpus, Chroma, embeddings, scraper output, or private data changed.
- Full pytest passed.

Rollback:

- Revert the cache-bust changes in `ui/steel-guitar-rag-mock.html`, `tests/test_frontend_answer_ui.py`, and `tests/test_same_origin_smoke_server.py`.
- Restart the protected-preview runtime with the standard Lane 12 command if needed.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-06-23-e9-fretboard-explorer-home-entry-preview-refresh.md`

## Files That Must Not Be Staged

- Unrelated parked docs, corpus metadata, source-inbox, brand/video assets, generated reports, scraper outputs, private data, Chroma/vector stores, embeddings, and all other dirty/untracked files not listed above.
- `docs/handoffs/task-completions/2026-06-23-01-keyhead-vshape-asset-commit.md` remains parked.

## Recommended Next Lane

Lane 15 QA / Answer Eval.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 15 should run full protected-preview app smoke from the home page into the Explorer:

```text
Lane 15: Run protected-preview browser smoke for the E9 Fretboard Explorer home-entry flow using https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623 and confirm navigation into /ui/e9-fretboard-explorer.html.
```
