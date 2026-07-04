# 2026-07-04 12:45 - Lane 12 - Voicing Identifier Readability Protected Smoke

## Task Summary

Requested: verify the committed Voicing Identifier readability UI change on protected preview and record the exact URL for user smoke.

Completed:
- Opened the protected-preview Explorer URL with a commit-specific cache key.
- Verified Cloudflare Access was already authenticated.
- Verified the page served the refreshed `voicing-readability-20260704` Explorer scripts.
- Verified the structured Voicing Identifier result panel for the no-3rd 5-7-8 case and the E-lower full-chord case.
- Verified protected root behavior.

Intentionally not changed:
- No files were modified for runtime behavior during smoke.
- No deployment, DNS, auth, corpus, scraping, embeddings, Chroma/vector stores, private transcripts, licensing metadata, secrets, or unrelated assets were touched.

## Files Changed

- `docs/handoffs/task-completions/2026-07-04-1245-12-voicing-identifier-readability-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md` after status refresh

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-readability-b1ca2c1`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-readability-b1ca2c1`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-readability-b1ca2c1`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded from existing authenticated browser session
- Local backend URL: not used for protected smoke
- Expected backend port: not applicable for protected static/browser smoke
- Expected git HEAD: `b1ca2c1` implementation commit; docs refresh commit followed separately
- Version endpoint: `https://app.steelguitarrag.com/api/version?v=voicing-readability-b1ca2c1`
- Version endpoint result: browser direct navigation was blocked with `net::ERR_BLOCKED_BY_CLIENT`
- If version endpoint missing, how version is inferred: protected page served `e9-music-rules.js?v=voicing-readability-20260704` and `e9-fretboard-explorer.js?v=voicing-readability-20260704` at the exact cache-busted Explorer URL
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes, by redirecting to the app shell
- Whether `/ui/steel-guitar-rag-mock.html` works: yes by root redirect observation
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: uncache-busted Explorer URLs for this slice
- Known caveats: version endpoint was blocked by the browser client, so this is protected static/browser proof rather than strict `/api/version` SHA proof

## Smoke Results

Protected Explorer URL:
- Loaded `E9 Fretboard Explorer - Steel Guitar RAG`.
- Served:
  - `pedal-steel-fretboard.js?v=explorer-harmonized-path-mode-20260626`
  - `e9-fretboard-explorer-data.js?v=single-grip-octave-results-20260628`
  - `e9-music-rules.js?v=voicing-readability-20260704`
  - `e9-fretboard-explorer.js?v=voicing-readability-20260704`

Voicing Identifier, fret 3, strings 5-7-8, open controls:
- Showed `G color voicing - no 3rd`.
- Showed `Technical name: G5/add9(no3)`.
- Showed `Color voicing / no 3rd`.
- Showed `Confidence: Medium`.
- Showed string roles:
  - `String 5` / `D` / `= 5th`
  - `String 7` / `A` / `= 9th / 2nd`
  - `String 8` / `G` / `= root`
- Showed omitted `3rd (B)`.
- Explained that no 3rd means it does not define major vs minor by itself.
- Showed alternate readings and warning/caution copy.
- Did not render the old dense `G5/add9(no3) voicing: D, A, G...` paragraph.
- Did not overclaim `G chord: D, A, G`.

Voicing Identifier, fret 8, strings 5-7-8, E-lower:
- Showed `G chord`.
- Showed `Technical name: G`.
- Showed string roles:
  - `String 5` / `G` / `= root`
  - `String 7` / `D` / `= 5th`
  - `String 8` / `B` / `= 3rd`
- Did not show the no-3rd caution.

Console:
- No relevant warnings/errors observed.

Object rendering:
- No `[object Object]` observed.

Root behavior:
- `https://app.steelguitarrag.com/?v=voicing-readability-b1ca2c1` redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- Root/app shell loaded with the app page content.

## Tests And Checks

Run before protected smoke in the implementation handoff:
- `git diff --check` passed.
- `node --check ui/e9-fretboard-explorer.js` passed.
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` passed with `24 passed`.
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` passed with `43 passed`.

## Integration Notes

- The protected static/browser surface reflects the committed readability UI through the refreshed script cache-bust.
- `/api/version` could not be read through direct browser navigation because the browser client reported `net::ERR_BLOCKED_BY_CLIENT`.
- API fallback was not used and is not claimed as browser smoke.

## Risk Assessment

Risk: Low.

Reason:
- The protected browser DOM served the expected scripts and rendered the expected structured result states.
- Remaining caveat is version endpoint access, not observed UI behavior.

Rollback:
- Revert `b1ca2c1` if user smoke finds a regression in the structured Voicing Identifier renderer.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-07-04-1245-12-voicing-identifier-readability-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- Any unrelated dirty files from the pre-existing worktree.
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox/` raw/provenance files
- `.wrangler/`
- DNS/deploy secrets
- `public/`
- `ui/brand/`
- `Neon Sign/`
- raw design assets
- generated reports or private transcript/licensing material

## Recommended Next Lane

User smoke at the exact cache-busted protected Explorer URL.

## Commit Readiness

Safe to commit.

## Suggested Next Step

User smoke:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-readability-b1ca2c1`
