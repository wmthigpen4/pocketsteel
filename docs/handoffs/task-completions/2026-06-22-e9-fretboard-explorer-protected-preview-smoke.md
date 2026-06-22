# E9 Fretboard Explorer Protected Preview Smoke

## Task Summary

Lane: 12 Self-Hosted Deployment / Protected Preview

Requested:
- Verify the exact protected-preview E9 Fretboard Explorer URL after Lane 15 local smoke passed but protected-preview smoke was blocked by Cloudflare Access.
- Use an authenticated Cloudflare Access browser session where available.
- Do not modify app code, corpus, embeddings, Chroma, scraper output, auth config, DNS, deployment config, assets, or private source data.

Completed:
- Read the required E9 Explorer handoffs and current integration status.
- Confirmed repo branch and HEAD.
- Confirmed the local protected-preview runtime on `127.0.0.1:8770` reports commit `a9dfd70`, which includes both commits under test.
- Attempted the exact protected-preview URL in the in-app browser.
- Attempted Chrome authenticated-browser fallback after the in-app browser landed on Cloudflare Access.
- Ran all requested automated checks.
- Confirmed local same-origin asset route for the expected fretboard background asset.
- Confirmed unauthenticated protected-preview requests to the Explorer URL and background asset redirect to Cloudflare Access.

Intentionally not changed:
- No implementation files.
- No backend, UI, auth, DNS, deployment config, assets, corpus, embeddings, Chroma, scraper output, source-inbox, private source data, or vector data.
- No protected-preview restart or deployment was performed.

## Pass / Warn / Fail

**Warn / blocked for authenticated protected-preview browser smoke.**

Runtime/version evidence is current, and all requested automated checks passed. The exact protected-preview Explorer URL still cannot be product-smoked in an authenticated browser from this environment because:

- the in-app browser opens the Cloudflare Access login page, not the authenticated Explorer page;
- Chrome extension browser control is unavailable after the required retry.

This is an authenticated-browser tooling/session blocker, not a confirmed E9 Explorer product defect.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke blocked by Cloudflare Access / unavailable authenticated browser control
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: not authenticated in the in-app browser; exact URL redirected to Cloudflare Access login
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `a9dfd70`, containing `a5389f2` and `a9dfd70`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"a9dfd70","git_branch":"feature/answer-api","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not needed; endpoint exists
- Whether app root `/` works: not retested for this Explorer-specific smoke
- Whether app root `/` is expected to work: yes, but this task targets the direct Explorer URL
- Whether `/ui/steel-guitar-rag-mock.html` works: not retested in authenticated browser
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user or Lane 12 with a working authenticated browser session
- Do not test these URLs: local `127.0.0.1` as proof of protected-preview browser behavior; app root as a substitute for the Explorer URL
- Known caveats: API/local evidence does not prove authenticated protected-preview UI behavior

## Commit / Runtime Evidence

Branch:

```text
feature/answer-api
```

Current HEAD:

```text
a9dfd70
```

Recent commits include:

```text
a9dfd70 docs: record E9 explorer browser smoke
a5389f2 feat: add e9 fretboard explorer surface
cabb639 docs: record E9 explorer display QA
a3fc8a4 fix: render explorer display spellings in fretboard UI
c42b236 fix: add key-aware explorer display spelling
```

Local protected-preview process:

```text
Python PID 82107 listening on 127.0.0.1:8770
```

`/api/version`:

```json
{
  "git_sha": "a9dfd70",
  "git_branch": "feature/answer-api",
  "server_started_at": "2026-06-22T19:38:25.673547+00:00",
  "python_module": "pocketsteel.api",
  "retrieval_mode": "hybrid_private_first",
  "auth_provider": "cloudflare_access"
}
```

## Browser Smoke Results

### In-App Browser

Exact URL opened:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622
```

Observed:

```text
Title: Sign in ・ Cloudflare Access
URL: https://late-waterfall-73da.cloudflareaccess.com/cdn-cgi/access/login/app.steelguitarrag.com?...&redirect_url=%2Fui%2Fe9-fretboard-explorer.html%3Fv%3De9-explorer-browser-surface-20260622
```

Result:

- Cloudflare Access redirected the unauthenticated in-app browser to login.
- Redirect preserved the Explorer path and cache-bust query in `redirect_url`.
- The Explorer page did not load in the in-app browser session.

### Chrome Authenticated Fallback

Attempted because the task requires authenticated Cloudflare Access browser verification and the in-app browser was not authenticated.

Result:

```text
Browser is not available: extension
```

After reading Chrome troubleshooting guidance, a lightweight retry was performed. Retry result:

```json
{
  "available": false,
  "error": "Browser is not available: extension"
}
```

No Chrome browser smoke was possible.

### Checklist Status

Because the authenticated protected page did not load, these protected-preview browser checks remain blocked rather than passed:

- Exact URL loads after Cloudflare Access authentication.
- Page title/entry identifies E9 Fretboard Explorer.
- Controls render.
- G major rows display.
- G natural minor displays `G A Bb C D Eb F`.
- Sharp-oriented E9 mechanical labels remain visible.
- Core grips and advanced swaps are visually separated.
- `5-7-8` appears only as advanced / E-lower pocket.
- Partial diminished / partial m7b5 warnings are visible.
- Per-string pedal/lever changes are visible.
- No `[object Object]`.
- No console errors.
- Landing entry exists on protected-preview mock/landing surface.
- Narrow/mobile protected-preview viewport is usable.

Those behaviors passed previously in local same-origin Lane 15 smoke, but they are not re-claimed here as protected-preview browser passes.

## Asset Routing Result

Local same-origin asset route:

```bash
curl -sSI http://127.0.0.1:8770/brand/pedal-steel-fretboard-background.svg
```

Result:

```text
HTTP/1.0 200 OK
Content-Type: image/svg+xml; charset=utf-8
```

Protected-preview unauthenticated asset route:

```bash
curl -sSI https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg
```

Result:

```text
HTTP/2 302
location: https://late-waterfall-73da.cloudflareaccess.com/cdn-cgi/access/login/app.steelguitarrag.com?...redirect_url=%2Fbrand%2Fpedal-steel-fretboard-background.svg
www-authenticate: Cloudflare-Access ...
```

Interpretation:
- The asset exists and serves locally from the running protected-preview app process.
- The protected-preview hostname correctly gates the asset behind Cloudflare Access for unauthenticated requests.
- Authenticated protected-preview asset loading remains unverified because authenticated browser access was blocked.

## Console Errors

- In-app browser: no Explorer-page console errors could be evaluated because the page did not pass Cloudflare Access.
- Chrome: unavailable.

## Mobile / Narrow Viewport Result

Not tested on protected preview because authenticated browser access was blocked.

Previous Lane 15 local fallback smoke verified narrow viewport usability, but this handoff does not count that as protected-preview browser evidence.

## Automated Tests Run

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/pedal-steel-fretboard.js
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest -q
git diff --check
```

Results:

- Branch: `feature/answer-api`.
- HEAD: `a9dfd70`.
- JS syntax checks: passed.
- `tests/test_pedal_steel_fretboard_ui.py -q`: 31 passed.
- `tests/test_frontend_answer_ui.py -q`: 22 passed.
- `tests/test_fretboard_explorer.py -q`: 11 passed.
- Full pytest: 790 passed.
- `git diff --check`: passed before this handoff was created.

## Files Changed

Created:

- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-protected-preview-smoke.md`

No implementation files were changed.

## Issues Found

Authenticated browser verification is blocked from this environment:

- in-app browser is unauthenticated and reaches Cloudflare Access login;
- Chrome extension browser control is unavailable.

No product defect was found by automated checks or runtime version checks.

## Blockers

Protected-preview browser smoke cannot be completed until an authenticated browser session is available to the automation surface or the user manually verifies the exact URL.

## Risks

Risk: medium.

Why:
- Runtime identity and automated checks are current and green.
- Local protected-preview server can serve the expected background asset.
- The exact protected-preview URL is gated by Cloudflare Access as expected.
- The actual authenticated protected-preview Explorer UI remains unverified in browser in this run.

Rollback notes:
- No code/config changes were made; no rollback required.

## Human Decision Needed

Yes.

Decision needed:
- Either provide/restore an authenticated browser automation session that can pass Cloudflare Access for `app.steelguitarrag.com`, or manually smoke the exact URL:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622
```

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-protected-preview-smoke.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked files, especially:

- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings.
- `source-inbox/` raw/provenance files.
- `.wrangler/`, DNS/deployment/auth/secrets files.
- `public/`, `ui/brand/`, `Neon Sign/`, raw/generated design assets.
- Existing parked docs/corpus metadata/root RAG script changes.
- Any implementation files under `pocketsteel/`, `ui/`, `scripts/`, or `tests` not explicitly scoped by a new handoff.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment / Protected Preview.

Suggested next prompt:

```text
Lane 12: Re-run authenticated protected-preview browser smoke for https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622 after confirming the browser automation session is authenticated through Cloudflare Access. Verify the full E9 Explorer checklist from the previous handoff and record whether the protected-preview page matches local smoke.
```

## Commit Readiness

Safe to commit as a docs-only blocked protected-preview smoke handoff.

## Suggested Next Step

Restore an authenticated browser session for protected-preview smoke, then rerun this exact verification. Do not route this back to Lane 06 or Lane 05 unless the authenticated protected-preview page loads and shows an actual Explorer UI defect.
