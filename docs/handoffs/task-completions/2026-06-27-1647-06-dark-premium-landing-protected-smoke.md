# 2026-06-27 16:47 - Lane 06 - Dark Premium Landing Protected Smoke

## Task Summary

Protected-preview smoke was run after commit `4181985 feat: redesign public landing page`.

## Smoke Target

```text
Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: https://app.steelguitarrag.com/ui/steel-guitar-rag-landing.html?v=dark-premium-landing-4181985
- Cache-busted URL tested: https://app.steelguitarrag.com/ui/steel-guitar-rag-landing.html?v=dark-premium-landing-4181985
- Exact URL the user should use: https://app.steelguitarrag.com/ui/steel-guitar-rag-landing.html?v=dark-premium-landing-4181985
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded via existing authenticated in-app browser session
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 4181985
- Version endpoint: http://127.0.0.1:8770/api/version
- Version endpoint result: git_sha=a6abc61, branch=feature/answer-api
- If version endpoint missing, how version is inferred: not missing; runtime SHA is older because this was a static landing-page smoke. Cache-busted protected static URL served the redesigned landing page.
- Whether app root `/` works: yes, redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes under current routing; it is not the static landing route
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user
- Do not test these URLs: unversioned landing URL for this slice
- Known caveats: root still redirects to the app shell and drops query strings; runtime SHA does not prove this static-only commit
```

## Protected Smoke Result

PASS with root-routing/runtime-version caveats.

Verified direct protected landing URL:
- Page loaded the redesigned dark premium landing page.
- H1 rendered: `Explore the neck. Ask better questions.`
- Top-left hanging sign was present.
- Landing sign WebM/PNG references were present.
- Premium Explorer preview was present.
- Five mode cards rendered.
- Brain section rendered.
- `Unlock the full explorer` pricing/early-access section rendered.
- No public app-shell content was exposed from the static landing page.
- No page-level horizontal overflow on desktop.
- No page-level horizontal overflow at narrow/mobile viewport.
- No `[object Object]`.
- Browser console had no relevant warnings/errors.

Verified root/app behavior:
- `https://app.steelguitarrag.com/?v=dark-premium-landing-4181985` redirected to `/ui/steel-guitar-rag-mock.html` and dropped the query string.
- Direct app shell URL loaded and did not show the landing hero.

## Files Changed

None in this smoke handoff aside from this report.

## Tests And Checks

Implementation checks are recorded in `docs/handoffs/task-completions/2026-06-27-1640-06-dark-premium-landing-redesign.md`.

Additional check:

```bash
curl -s --max-time 5 http://127.0.0.1:8770/api/version
```

Result:
- `git_sha=a6abc61`
- `git_branch=feature/answer-api`
- `auth_provider=cloudflare_access`

## Risks

Medium-low:
- Root does not serve the static landing page. Direct `/ui/steel-guitar-rag-landing.html?...` URL is required for user smoke.
- Runtime SHA is older than the static landing commit; this smoke proves cache-busted static/browser behavior, not a restarted Python runtime.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-27-1647-06-dark-premium-landing-protected-smoke.md`

## Files That Must Not Be Staged

- Existing unrelated dirty/untracked corpus, source-inbox, RAG scripts, brand/public asset work, raw design assets, generated reports, and parked docs.

## Recommended Next Lane

User smoke or Lane 15 visual QA at:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-landing.html?v=dark-premium-landing-4181985
```

## Commit Readiness

Safe to commit.

## Suggested Next Step

Manually compare the direct protected landing URL against the attached dark premium references.
