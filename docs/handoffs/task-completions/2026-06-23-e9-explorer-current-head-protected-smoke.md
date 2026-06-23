# 2026-06-23 Lane 12 - E9 Explorer Current HEAD Protected Smoke

## Task Summary

Requested: run ProtectedPreviewSmoke for the E9 Fretboard Explorer app entry at current HEAD after the latest Lane 06/Lane 12 cache-bust work.

Completed:

- Confirmed current branch and HEAD.
- Restarted the protected-preview runtime on `127.0.0.1:8770`.
- Confirmed local `/api/version` reports current HEAD `9562e90` on `feature/answer-api`.
- Verified unauthenticated protected root and `/api/version` redirect to Cloudflare Access.
- Verified authenticated browser access to root, canonical app URL, Explorer route, and direct SVG asset URL.
- Verified root `/` redirects to `/ui/steel-guitar-rag-mock.html` and drops the query string.
- Verified the canonical app URL remains the right demo target.
- Verified the app page home entry opens the Explorer route.
- Verified expanded keys, spelling, mode controls, explanation/detail behavior, advanced `5-7-8` handling, SVG routing, and narrow viewport behavior.

Intentionally not changed:

- Product logic.
- Backend pitch validation.
- Explorer data rows.
- Corpus, embeddings, Chroma/vector stores, source-inbox, scraper output, private source data, auth, DNS, Cloudflare Access policy, and deployment config.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested:
  - Root: `https://app.steelguitarrag.com/?v=e9-explorer-current-head-20260623`
  - Canonical app: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`
  - Explorer: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-home-entry-20260623`
  - SVG asset: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`
- Cache-busted URL tested: yes, exact URLs above.
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded in authenticated browser; product pages loaded rather than Access login
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `9562e90`
- Version endpoint: `/api/version`
- Version endpoint result: local tunnel target returned `git_sha: 9562e90`, branch `feature/answer-api`, auth provider `cloudflare_access`
- If version endpoint missing, how version is inferred: not missing locally; protected shell access redirects to Cloudflare Access as expected
- Whether app root `/` works: yes, by redirect
- Whether app root `/` is expected to work: yes as an entry URL, but it is not the canonical cache-preserving demo URL
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, canonical tested app URL
- Who should test this URL: the user
- Do not test these URLs: stale uncached app or Explorer URLs when verifying this slice
- Known caveats:
  - Root `/` redirects to `/ui/steel-guitar-rag-mock.html` and drops the `?v=e9-explorer-current-head-20260623` query string.
  - Direct raw SVG tab can emit a browser-runtime warning unrelated to Explorer app-page behavior.

## Current Branch And HEAD

- Current branch: `feature/answer-api`
- Current HEAD: `9562e90 fix: cache-bust fretboard background svg`
- Related prior integration refresh: `00442ec docs: refresh e9 explorer integration status`

## Protected Preview Restart Evidence

Restarted with the existing Lane 12 protected-preview workflow in a detached `screen` session.

Observed after restart:

- `screen` session: `steel-rag-private-preview`
- Listener: `Python ... TCP 127.0.0.1:8770 (LISTEN)`
- Local `/api/version`:

```json
{
  "git_sha": "9562e90",
  "git_branch": "feature/answer-api",
  "python_module": "pocketsteel.api",
  "retrieval_mode": "hybrid_private_first",
  "auth_provider": "cloudflare_access"
}
```

Unauthenticated shell checks:

- `https://app.steelguitarrag.com/?v=e9-explorer-current-head-20260623`: `302` to Cloudflare Access login.
- `https://app.steelguitarrag.com/api/version`: `302` to Cloudflare Access login.

## Root URL Behavior

PASS with cache-bust caveat.

- Root URL tested: `https://app.steelguitarrag.com/?v=e9-explorer-current-head-20260623`
- Authenticated final URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`
- Behavior: root redirects to the app shell.
- Query string preservation: not preserved.
- Result: root can be used as an entry URL, but canonical cache-busted smoke/demo should use `/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`.

## Canonical App URL Behavior

PASS.

- URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`
- App shell loaded.
- Q&A/search remained visible and primary.
- Question placeholder: `Ask a steel guitar question...`
- `Explore the E9 Fretboard` entry appeared.
- `Open Fretboard Explorer` link appeared.
- Link target: `/ui/e9-fretboard-explorer.html`
- Script cache-busts observed:
  - `answer-client.js?v=e9-explorer-home-entry-20260623`
  - `pedal-steel-fretboard.js?v=e9-explorer-home-entry-20260623`
- No `[object Object]`.

## Home-Entry Result

PASS.

- Clicked the app-page Explorer entry.
- Link count for `/ui/e9-fretboard-explorer.html`: `1`.
- Final URL after click: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html`.
- Explorer loaded and identified itself as `E9 Fretboard Explorer`.

## Explorer Result

PASS.

Verified:

- Explorer route loads at `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-home-entry-20260623`.
- Key selector includes `G`, `C`, `D`, `F`, `Bb`, `Eb`.
- `Showing validated positions` appears.
- Raw `N validated rows` primary copy does not appear.
- `E-lower+E-lower` does not appear.
- `[object Object]` does not appear.
- Core grip rows and advanced swap rows remain visually separated.
- `5-7-8` remains available as an advanced group in 3-string mode.
- Selecting `5-7-8` returns only E-lower advanced-pocket rows.
- Selected-row detail panel appears.
- `Why this position works` / explanation content appears.
- Technical details remain behind the technical-detail control.
- Per-string mechanics are visible in selected-row detail.
- Partial/diminished warning language remains available where applicable.

## Expanded Key Result

PASS.

Observed key options:

- `G`
- `C`
- `D`
- `F`
- `Bb`
- `Eb`

Spelling checks:

- G natural minor: `G A Bb C D Eb F` appears.
- Bad G natural minor spelling `G A A# C D D# F` does not appear.
- C natural minor: `C D Eb F G Ab Bb` appears.

Sharp-oriented E9 mechanical labels remain present where appropriate:

- `F#`
- `D#`
- `G#`
- `Eb/D#`

## Mode Result

PASS.

2-string mode on G major:

- Mode: `two_string_harmonized`
- Options observed:
  - `All 2-string groups`
  - `3-5`
  - `5-6`
  - `6-10`
  - `4-6`
  - `3-4`

3-string mode on G major:

- Mode: `three_string_diatonic`
- Core options observed:
  - `3-4-5`
  - `4-5-6`
  - `5-6-8`
  - `6-8-10`
- Advanced options observed:
  - `5-6-7`
  - `6-7-10`
  - `5-7-8`

Note: 2-string mode is disabled for C natural minor in the current UI state. It works for G major, which satisfies this smoke target without implying unsupported natural-minor two-string behavior.

## SVG Asset Result

PASS with raw-SVG-tab caveat.

Direct asset URL:

- `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`

Observed:

- Protected asset URL loaded after Cloudflare Access auth.
- Root element: `svg`.
- `viewBox="0 0 1600 420"` present.
- No root `width` attribute.
- No root `height` attribute.
- `data-layer="headstock-keyhead-shell"` present.
- `data-layer="10-tuning-keys"` present.
- In-page Explorer markup references `/brand/pedal-steel-fretboard-background.svg`.

Visual/context result:

- Fretboard background asset appears in the Explorer page context.
- V-shaped keyhead/tuner asset is reachable and structurally present.

Caveat:

- Direct raw SVG browser tab emitted the known browser-runtime warning: `TypeError: Cannot use 'in' operator to search for 'animation' in undefined`. This is not an Explorer page error.

## Console Errors

PASS for app and Explorer pages.

- Root/app page console errors: none observed before direct SVG navigation.
- Canonical app page console errors: none observed.
- Explorer app-page console errors: none observed in the main app/Explorer checks.
- Direct raw SVG tab warning recorded separately as a non-blocking caveat.

## Mobile / Narrow Viewport Result

PASS.

Tested around `390x844`.

App page:

- Q&A/search visible.
- `Explore the E9 Fretboard` entry visible.
- No document-level horizontal overflow.
- No `[object Object]`.

Explorer page:

- Explorer title visible.
- Key/scale/harmony/string-group controls visible.
- `Showing validated positions` present.
- Fretboard background reference present.
- No document-level horizontal overflow.
- No `[object Object]`.

## Tests And Checks

Run:

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log --oneline -10`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - `23 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - `31 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - `28 passed`
- `.venv/bin/python -m pytest -q` - `808 passed`
- `git diff --check`

## Files Changed

- `docs/handoffs/task-completions/2026-06-23-e9-explorer-current-head-protected-smoke.md`

Deleted files: none.

Generated artifacts: none.

## Integration Notes

- The latest runtime is `9562e90`, newer than the integration-status refresh `00442ec`.
- Root `/` now has a certified behavior: it redirects to `/ui/steel-guitar-rag-mock.html` but does not preserve the query string.
- The canonical app URL remains `/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`.
- User demo can start at the canonical app URL. Root is acceptable as an entry path but not as a cache-busted verification URL.

## Risk Assessment

Risk: low.

Why:

- This task changed only the Lane 12 smoke handoff.
- No runtime files, product logic, auth, DNS, corpus, Chroma, embeddings, scraper output, or private data changed.
- Focused checks and full pytest passed.

Rollback:

- No runtime rollback needed for this handoff-only task.
- Protected preview is currently running from HEAD `9562e90`.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-e9-explorer-current-head-protected-smoke.md`

## Files That Must Not Be Staged

- All unrelated dirty/untracked files.
- Corpus/private/vector/embedding/source-inbox/scraper outputs.
- Auth, DNS, Cloudflare, deployment config, env, credentials, or secrets.
- Brand/design assets and parked visual work.
- Parked closeout handoffs unless explicitly requested.

## Recommended Next Lane

Lane 15 only if user-smoke feedback identifies issues.

## Commit Readiness

Safe to commit.

## Suggested Next Step

If this passes user demo, refresh integration status with:

```text
Lane 01: Refresh integration-status.md after Lane 12 certified current HEAD E9 Explorer protected-preview smoke at 9562e90. Record root redirect behavior, canonical app URL, Explorer route result, SVG asset result, and that user demo can proceed from the canonical app URL.
```
