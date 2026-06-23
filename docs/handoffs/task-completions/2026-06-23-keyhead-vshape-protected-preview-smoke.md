# 2026-06-23 Keyhead V-Shape Protected Preview Smoke

## Task Summary

Lane 12 verified the V-shaped pedal-steel fretboard background SVG route and the E9 Fretboard Explorer protected-preview route.

Completed:
- Verified the protected SVG URL loads through the authenticated Cloudflare Access browser session.
- Verified the SVG contains the V-shaped keyhead shell and 10 tuner groups.
- Verified the tuner layout remains 5 top / 5 bottom and tapers toward the roller-nut side.
- Verified the E9 Fretboard Explorer route loads, references `/brand/pedal-steel-fretboard-background.svg` in-page, and still shows the explanation UI.
- Ran focused syntax and frontend tests.

Intentionally not changed:
- No product logic, corpus, Chroma/vector stores, embeddings, scraper output, auth, DNS, deployment config, private source data, or asset files were modified.
- No staging or commit was performed.

Important warning:
- The SVG asset is still untracked in this checkout: `?? public/brand/pedal-steel-fretboard-background.svg`.
- `git ls-files -- public/brand/pedal-steel-fretboard-background.svg` returned no tracked path, and `git log --oneline --all -- public/brand/pedal-steel-fretboard-background.svg` returned no history.
- Therefore this smoke can verify protected-preview runtime serving of the current working-tree asset, but it cannot prove the SVG is a committed asset until Lane 01 commits the approved SVG path.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke with committed-asset provenance warning
- Exact browser URL tested: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-20260623`
- Cache-busted URL tested: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-20260623`
- Explorer URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-explanation-ui-20260623`
- Exact URL the user should use for asset smoke: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-20260623`
- Exact URL the user should use for Explorer smoke: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-explanation-ui-20260623`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; both protected URLs loaded as product/static routes, not Access login pages
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: SVG commit or later; current runtime HEAD observed as `b5fd09a`
- Version endpoint: `/api/version`
- Version endpoint result: local loopback returned `git_sha: b5fd09a`, branch `feature/answer-api`, module `pocketsteel.api`, retrieval mode `hybrid_private_first`, auth provider `cloudflare_access`
- If version endpoint missing, how version is inferred: not missing locally
- Whether app root `/` works: not tested for this task
- Whether app root `/` is expected to work: not required for this task
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested for this task
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, but outside this task's scope
- Who should test this URL: Lane 12 / Lane 15 / the user after Lane 01 resolves commit provenance
- Do not test these URLs: uncached SVG/Explorer URLs when validating this slice
- Known caveats: direct SVG browser tab logs one browser-runtime promise error after loading raw SVG; Explorer page renders normally.

## Pass / Warn / Fail

WARN.

Runtime protected-preview serving and Explorer render checks passed. The committed-asset criterion is not satisfied because the SVG path is untracked and has no git history in this checkout.

## Exact URLs Tested

- `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-20260623`
- `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-explanation-ui-20260623`

## Auth Result

PASS. Cloudflare Access session succeeded. The browser did not land on an Access login page for either protected URL.

## Version / Commit Result

WARN.

- Current branch: `feature/answer-api`
- Current repo HEAD during this task: `b5fd09a fix: show e9 explorer row explanations`
- Local `/api/version`: `b5fd09a`
- SVG provenance: not committed/tracked in this checkout.
- `public/brand/pedal-steel-fretboard-background.svg` remains untracked and must be handled by Lane 01 before this can be called a committed-asset protected-preview pass.

## Asset Routing Result

PASS for runtime serving.

The exact protected SVG URL loaded an SVG document:

- `svg` element present
- `viewBox`: `0 0 1600 420`
- Cloudflare Access login page: not present
- `data-layer="headstock-keyhead-shell"` present
- `data-layer="10-tuning-keys"` present

## Visual Result

PASS for the runtime-served asset.

Observed SVG structure:

- V-shaped keyhead shell path present.
- Top tuner groups: 5.
- Bottom tuner groups: 5.
- Tuner count: 10.
- Top tuner y-values by increasing x: `[135, 125, 115, 105, 95]`.
- Bottom tuner y-values by increasing x: `[271, 281, 291, 301, 311]`.
- The two tuner rows taper in opposite directions, consistent with a V-shaped keyhead widening toward the roller-nut side.

## Explorer Result

PASS.

The protected Explorer route loaded and showed:

- `E9 Fretboard Explorer`
- `Showing validated positions`
- explanation UI present
- one embedded fretboard SVG
- in-page SVG image reference: `/brand/pedal-steel-fretboard-background.svg`
- no `[object Object]`
- no `validated rows` primary copy

Loaded scripts used the expected explanation UI cache-bust:

- `pedal-steel-fretboard.js?v=e9-explorer-explanation-ui-20260623`
- `e9-fretboard-explorer-data.js?v=e9-explorer-explanation-ui-20260623`
- `e9-fretboard-explorer.js?v=e9-explorer-explanation-ui-20260623`

## Console Errors

WARN.

The raw SVG asset tab logged:

```text
Uncaught (in promise) TypeError: Cannot use 'in' operator to search for 'animation' in undefined
```

The SVG still loaded and rendered. The same browser log feed was visible while checking the Explorer tab, but the timestamp matched the raw SVG tab load. No Explorer rendering failure was observed.

## Tests Run

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log --oneline -8`
- `git ls-files -- public/brand/pedal-steel-fretboard-background.svg`
- `git log --oneline --all -- public/brand/pedal-steel-fretboard-background.svg`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/e9-fretboard-explorer.js`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - `31 passed`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - `23 passed`
- `curl -sS http://127.0.0.1:8770/api/version`
- Authenticated in-app browser smoke for the exact protected SVG URL
- Authenticated in-app browser smoke for the exact protected Explorer URL

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-23-keyhead-vshape-protected-preview-smoke.md`

No implementation, asset, corpus, Chroma, embedding, scraper, auth, DNS, deployment, or private-source files were changed.

## Risks

Medium until Lane 01 resolves commit provenance.

Reason: protected preview is serving the current working-tree SVG, but that SVG is not tracked. A clean checkout or another machine would not have a committed `public/brand/pedal-steel-fretboard-background.svg` unless Lane 01 adds it explicitly.

Rollback note: once committed, rollback should revert only `public/brand/pedal-steel-fretboard-background.svg` to the prior approved SVG geometry.

## Human Decision Needed

Yes.

Lane 01 needs to decide whether to exact-stage and commit:

- `public/brand/pedal-steel-fretboard-background.svg`
- `docs/handoffs/task-completions/2026-06-23-19-keyhead-vshape-svg.md`

This Lane 12 smoke handoff should also be staged only if the team wants the warning documented in git.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-keyhead-vshape-protected-preview-smoke.md`

For Lane 01 only, after exact-path review:

- `public/brand/pedal-steel-fretboard-background.svg`
- `docs/handoffs/task-completions/2026-06-23-19-keyhead-vshape-svg.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files shown by `git status --short`
- Corpus files
- Chroma/vector stores
- Embeddings
- Scraper output
- Private source data
- Auth, DNS, Cloudflare, or deployment configuration
- Brand/design assets other than the explicitly approved SVG path above

## Recommended Next Lane

Lane 01 Repo Steward.

## Commit Readiness

Needs human review first.

## Recommended Next Prompt

```text
Lane 01 Repo Steward: Resolve the keyhead SVG commit provenance. Exact-stage only public/brand/pedal-steel-fretboard-background.svg and docs/handoffs/task-completions/2026-06-23-19-keyhead-vshape-svg.md if the untracked asset path is approved. Run git diff --cached --name-only, git diff --cached, and git diff --cached --check. Commit only if no unrelated files, corpus data, Chroma/vector stores, embeddings, private data, auth/DNS/deployment config, or unapproved assets are staged. Then ask Lane 12 to rerun protected-preview smoke for the committed SVG asset.
```
