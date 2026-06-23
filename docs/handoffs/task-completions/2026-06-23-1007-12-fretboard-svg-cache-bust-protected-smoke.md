# 2026-06-23 10:07 - Lane 12 Fretboard SVG Cache-Bust Protected Smoke

## Task summary

- Requested: verify that the protected-preview E9 Fretboard Explorer loads the refreshed `pedal-steel-fretboard.js` script and uses the in-page cache-busted fretboard background SVG.
- Completed: authenticated protected-preview browser smoke for the exact Explorer URL, local runtime version check, DOM/resource checks for the script and SVG, console-error check, and focused syntax checks.
- Intentionally not changed: app code, deployment config, DNS, Cloudflare Access policy, corpus, embeddings, Chroma/vector stores, scraper output, private source data, and unrelated dirty work.

## Smoke Target

```text
Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=fretboard-svg-cache-bust-20260623b
- Cache-busted URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=fretboard-svg-cache-bust-20260623b
- Exact URL the user should use: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=fretboard-svg-cache-bust-20260623b
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; the protected page loaded as the Explorer, not the Access login page
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 7ec5e3a or later containing the fretboard SVG cache-bust refresh
- Version endpoint: /api/version
- Version endpoint result: local loopback reported git_sha 7ec5e3a, git_branch feature/answer-api, retrieval_mode hybrid_private_first, auth_provider cloudflare_access
- If version endpoint missing, how version is inferred: not missing; authenticated direct browser navigation to /api/version was blocked by the browser runtime with net::ERR_BLOCKED_BY_CLIENT, so version evidence is from local loopback on the protected-preview process
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not part of this smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, but not part of this smoke
- Who should test this URL: Codex and the user
- Do not test these URLs: root-only URLs as a substitute for this exact cache-busted Explorer URL
- Known caveats: protected /api/version browser navigation was blocked by the browser runtime; local loopback version check was used for runtime identity
```

## Browser verification

- Exact Explorer URL loaded: pass.
- Page title: `E9 Fretboard Explorer - Steel Guitar RAG`.
- H1: `E9 Fretboard Explorer`.
- Explorer primary copy/state: `Showing validated positions` appeared.
- `pedal-steel-fretboard.js` script reference: pass.
  - Observed in DOM: `pedal-steel-fretboard.js?v=fretboard-svg-cache-bust-20260623b`.
  - Observed as page asset resource: `https://app.steelguitarrag.com/ui/pedal-steel-fretboard.js?v=fretboard-svg-cache-bust-20260623b`.
- In-page SVG request: pass.
  - Observed SVG image element href: `/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`.
  - Observed as page asset resource: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f`.
- V-shaped keyhead inside Explorer: pass by rendered browser screenshot/visual inspection; the keyhead/tuner area appeared in the Explorer fretboard.
- Fretboard component mounted: pass.
  - `.pedal-steel-fretboard` / `data-component="PedalSteelFretboard"` count: 1.
  - `svg.pedal-steel-fretboard__svg` count: 1.
- `[object Object]`: not found in rendered page text.
- Console errors: none returned by browser console error log check.

## Files changed

- Created: `docs/handoffs/task-completions/2026-06-23-1007-12-fretboard-svg-cache-bust-protected-smoke.md`
- Changed files: none besides this handoff.
- Deleted files: none.
- Generated artifacts: none committed. A browser screenshot was emitted for visual verification but not written into the repo.

## Tests and checks

- `git status --short`
  - Result: completed; broad unrelated dirty/untracked work remains parked.
- `git branch --show-current`
  - Result: `feature/answer-api`.
- `git rev-parse --short HEAD`
  - Result: `7ec5e3a`.
- `git log -1 --oneline`
  - Result: `7ec5e3a fix: refresh explorer fretboard script cache-bust`.
- `git diff --cached --name-only`
  - Result before handoff: no staged files.
- `rg -n "pedal-steel-fretboard|fretboard-svg-cache-bust|keyhead-vshape|pedal-steel-fretboard-background" ui/e9-fretboard-explorer.html ui/pedal-steel-fretboard.js`
  - Result: expected script and SVG cache-bust references found.
- `curl -sS http://127.0.0.1:8770/api/version`
  - Result: `git_sha` `7ec5e3a`, branch `feature/answer-api`, `auth_provider` `cloudflare_access`.
- `curl -sS 'http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=fretboard-svg-cache-bust-20260623b' | rg 'pedal-steel-fretboard.js|e9-fretboard-explorer'`
  - Result: HTML includes `pedal-steel-fretboard.js?v=fretboard-svg-cache-bust-20260623b`.
- Browser smoke against protected-preview exact URL.
  - Result: pass with the `/api/version` caveat noted above.
- `node --check ui/pedal-steel-fretboard.js`
  - Result: pass.
- `node --check ui/e9-fretboard-explorer.js`
  - Result: pass.
- `git diff --check`
  - Result: pass.

## Integration notes

- Protected preview is serving the refreshed Explorer HTML and the refreshed `pedal-steel-fretboard.js` asset reference.
- The in-page fretboard background SVG request now uses the intended `/brand/pedal-steel-fretboard-background.svg?v=keyhead-vshape-bce771f` URL.
- No product logic, data contract, auth behavior, DNS, Cloudflare Access policy, corpus, Chroma/vector, embedding, or scraping behavior changed.
- The latest integration-status handoff is stale relative to current HEAD `7ec5e3a`; this smoke confirms the protected-preview runtime has moved past the older E9 Explorer cache-bust commits.

## Risk assessment

- Risk: low.
- Reason: this was a read-only protected-preview smoke plus a docs-only handoff.
- Rollback notes: no runtime changes were made. If this handoff commit is not wanted, revert only the handoff commit.

## Human decision needed

- No for this smoke result.
- Optional: decide whether to refresh `docs/handoffs/task-completions/integration-status.md` to include `7ec5e3a` and this protected-preview smoke result.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-06-23-1007-12-fretboard-svg-cache-bust-protected-smoke.md`

## Files that must not be staged

- Any unrelated dirty/untracked files.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Deployment/auth/DNS/secrets files.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, unrelated app code, unrelated tests, and parked handoffs.

## Recommended next lane

- Lane 01 Repo Steward if integration status should be refreshed.
- Lane 15 QA / Answer Eval only if broader Explorer regression smoke is requested.

## Commit readiness

Safe to commit

## Suggested next step

Lane 01: refresh `docs/handoffs/task-completions/integration-status.md` to record `7ec5e3a` and this protected-preview cache-bust smoke if the current E9 Explorer deployment state should become the new coordination baseline.
