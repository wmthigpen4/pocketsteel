# 2026-06-23 Lane 12 Fretboard SVG In-Page Cache-Bust Protected Smoke

## Task Summary

Lane 12 verified whether protected preview serves the V-shaped keyhead SVG through the E9 Fretboard Explorer with an in-page cache-busted background request.

Completed:
- Confirmed protected preview restarted from current `feature/answer-api` HEAD.
- Confirmed Cloudflare Access browser session loaded the Explorer route.
- Confirmed the direct SVG URL serves the tracked V-shaped keyhead asset.
- Confirmed the Explorer route still loads and core Explorer regression signals remain present.
- Confirmed the in-page Explorer background request is still unversioned.
- Identified the cache-bust root cause.

Intentionally not changed:
- No product logic.
- No backend behavior.
- No Explorer data rows.
- No corpus, Chroma, embeddings, scraper output, auth, DNS, Cloudflare Access policy, or private source data.
- No UI source edits; this task was verification and blocker routing because the protected browser still used an unversioned in-page SVG request.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=fretboard-svg-cache-bust-20260623`
- Cache-busted URL tested: yes
- Exact URL the user should use: blocked for this slice until the Explorer script cache-bust is refreshed
- Direct SVG URL tested: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`
- Canonical app URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fretboard-svg-cache-bust-20260623`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `64db66b`
- Version endpoint: `/api/version`
- Version endpoint result: local `/api/version` returned `64db66b`, branch `feature/answer-api`, `auth_provider=cloudflare_access`, `retrieval_mode=hybrid_private_first`
- Browser `/api/version` note: direct browser navigation to the protected `/api/version` route was blocked by the browser environment with `net::ERR_BLOCKED_BY_CLIENT`; runtime identity is therefore proven by local loopback `/api/version` plus protected preview restart evidence.
- Whether app root `/` works: not in scope for this cache-bust check
- Whether app root `/` is expected to work: not asserted here
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Lane 12 after Lane 06 cache-bust refresh
- Do not test these URLs: do not use the Explorer protected URL as proof of the in-page SVG cache-bust until script references are refreshed
- Known caveats: direct raw-SVG tab emitted a browser-runtime warning unrelated to the Explorer app page

## Branch And Runtime

- Branch: `feature/answer-api`
- HEAD before smoke: `64db66b fix: cache bust in-page fretboard background`
- Protected preview restart evidence:
  - `screen` session: `steel-rag-private-preview`
  - Listener: Python process on `127.0.0.1:8770`
  - Local `/api/version`: `{"git_sha":"64db66b","git_branch":"feature/answer-api","server_started_at":"2026-06-23T14:55:46.708130+00:00","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`

## Direct SVG Result

Direct URL tested:

`https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`

Result:
- Loaded after Cloudflare Access.
- SVG present.
- `viewBox="0 0 1600 420"` present.
- No root `width` attribute.
- No root `height` attribute.
- Keyhead layer present.
- Tuner layer present.
- Tracked file contains 10 tuners: 5 top and 5 bottom.

Raw SVG tab warning:
- The direct raw SVG tab emitted `Uncaught (in promise) TypeError: Cannot use 'in' operator to search for 'animation' in undefined`.
- This was observed on the raw SVG browser tab and should be treated separately from Explorer app-page console errors.

## In-Page Explorer SVG Request

Explorer URL tested:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=fretboard-svg-cache-bust-20260623`

Observed Explorer script references:

```text
pedal-steel-fretboard.js?v=e9-explorer-explanation-ui-20260623
e9-fretboard-explorer-data.js?v=e9-explorer-explanation-ui-20260623
e9-fretboard-explorer.js?v=e9-explorer-explanation-ui-20260623
```

Observed in-page SVG image href:

```text
/brand/pedal-steel-fretboard-background.svg
```

Expected fixed in-page SVG image href:

```text
/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f
```

Result: **fail** for in-page SVG cache-bust. The Explorer browser DOM still mounts the unversioned SVG request.

## Root Cause

The code in `ui/pedal-steel-fretboard.js` now contains the fixed background constant:

```text
const DECORATIVE_BACKGROUND_HREF = "/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f";
```

The local protected server also serves that fixed JS when requested with a fresh query string.

However, `ui/e9-fretboard-explorer.html` still references `pedal-steel-fretboard.js` with an older script cache-bust:

```text
pedal-steel-fretboard.js?v=e9-explorer-explanation-ui-20260623
```

That stale script reference allows the authenticated browser to reuse an older cached `pedal-steel-fretboard.js`, so the Explorer still mounts:

```text
/brand/pedal-steel-fretboard-background.svg
```

Owning lane: **Lane 06 UX/UI Design** should refresh the Explorer page script cache-busts to a slice-specific value for the fretboard SVG cache-bust fix. After that, Lane 12 should restart/verify protected preview again.

## Canonical App Result

Canonical app URL tested:

`https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=fretboard-svg-cache-bust-20260623`

Result:
- Cloudflare Access succeeded.
- App shell loaded.
- `Explore the E9 Fretboard` entry appeared.
- Entry link points to `/ui/e9-fretboard-explorer.html`.
- No `[object Object]` observed in the app page text.

Observed app page script references:

```text
answer-client.js?v=e9-explorer-home-entry-20260623
pedal-steel-fretboard.js?v=e9-explorer-home-entry-20260623
```

The app page was not the failing route for this specific Explorer in-page SVG check.

## Explorer Regression Result

Explorer route result:
- Page title identifies `E9 Fretboard Explorer`.
- Expanded keys visible: `G`, `C`, `D`, `F`, `Bb`, `Eb`.
- `Showing validated positions` appears.
- Explanation UI appears.
- No raw `N validated rows` primary copy.
- No `[object Object]`.
- No `E-lower+E-lower`.

Blocked item:
- In-page fretboard background still uses the unversioned SVG URL due to stale Explorer script cache-busts.

## Console Errors

Explorer page:
- No Explorer-specific page errors were observed during the targeted DOM verification.

Raw SVG tab:
- Browser-runtime warning observed when opening the raw SVG directly:
  - `Uncaught (in promise) TypeError: Cannot use 'in' operator to search for 'animation' in undefined`
- This warning should not be treated as an Explorer page application error.

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log --oneline -10
git ls-files -- public/brand/pedal-steel-fretboard-background.svg
rg "pedal-steel-fretboard-background.svg" ui tests
node --check ui/pedal-steel-fretboard.js
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest -q
git diff --check
```

Results:
- `node --check ui/pedal-steel-fretboard.js`: passed
- `node --check ui/e9-fretboard-explorer.js`: passed
- `node --check ui/e9-fretboard-explorer-data.js`: passed
- `node --check ui/answer-client.js`: passed
- `tests/test_pedal_steel_fretboard_ui.py`: `31 passed`
- `tests/test_frontend_answer_ui.py`: `23 passed`
- `tests/test_fretboard_explorer.py`: `28 passed`
- Full pytest: `808 passed`
- `git diff --check`: passed

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-23-fretboard-svg-inpage-cache-bust-protected-smoke.md`

No implementation files changed.

## Protected Paths And Parked Work

Unrelated dirty/parked work remains present in the repository, including docs, corpus metadata, RAG scripts, source-inbox inventory, visual assets, and many untracked handoffs/assets. These were not staged or modified by this task.

Protected paths intentionally untouched:
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox/` raw/source data
- scraper output
- auth/DNS/Cloudflare Access configuration
- private source data
- product logic/backend behavior

## Risk Assessment

Risk: **medium** until the Explorer script cache-bust is refreshed.

Reason:
- Direct SVG asset routing is correct.
- Runtime JS source contains the fixed URL.
- The protected Explorer page can still load cached older JS because the Explorer HTML script references were not refreshed for this slice.

Rollback:
- No rollback required for this Lane 12 handoff.
- If Lane 06 updates script cache-busts and a regression appears, revert only that cache-bust/static-reference change.

## Human Decision Needed

Yes.

Decision:
- Route this back to Lane 06 to update `ui/e9-fretboard-explorer.html` script query strings to a new slice-specific cache-bust, then return to Lane 12 for protected-preview verification.

## Safe-To-Stage Exact File List

```text
docs/handoffs/task-completions/2026-06-23-fretboard-svg-inpage-cache-bust-protected-smoke.md
```

## Files That Must Not Be Staged

Do not stage:
- unrelated dirty docs
- unrelated untracked handoffs/assets
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox/`
- scraper output
- `rag_*.py`
- auth/DNS/Cloudflare configuration
- visual/design source assets
- unrelated UI/backend/test files

## Recommended Next Lane

Lane 06 UX/UI Design.

Exact next prompt:

```text
Lane 06 UX/UI Design

Update the E9 Fretboard Explorer script cache-busts so protected preview fetches the current pedal-steel-fretboard.js containing:
/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f

Current failure:
Lane 12 protected-preview smoke at:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=fretboard-svg-cache-bust-20260623
still mounted:
/brand/pedal-steel-fretboard-background.svg

Root cause:
ui/e9-fretboard-explorer.html still references:
pedal-steel-fretboard.js?v=e9-explorer-explanation-ui-20260623

Make the smallest cache-bust/static-reference update, run focused Explorer/fretboard/frontend checks, and write a handoff for Lane 12 to rerun protected-preview verification.
```

## Commit Readiness

Safe to commit the handoff only.
