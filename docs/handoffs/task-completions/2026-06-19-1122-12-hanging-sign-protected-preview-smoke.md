# Hanging Sign Protected Preview Smoke

## Task summary
- Requested: verify the committed hanging-sign alignment fix `4b8ac0c fix: align hanging sign placement` on the public landing page and protected-preview app.
- Completed: inspected repo governance/status, verified runtime version, measured public and app hanging-sign placement at desktop and mobile breakpoints, deployed the current static landing artifact when the live public page proved stale, remeasured exact cache-busted URLs, checked app root behavior, checked Cloudflare Access behavior, and recorded console/overflow results.
- Intentionally not changed: no backend, UI source, auth policy, DNS, Cloudflare Access policy, corpus, embeddings, Chroma, scraping, or private source files were modified.

## Files changed
- Created:
  - `docs/handoffs/task-completions/2026-06-19-1122-12-hanging-sign-protected-preview-smoke.md`
- Changed files:
  - None besides this handoff.
- Deleted files:
  - None.
- Generated artifacts:
  - None.

## Tests and checks
- Governance/status inspection:
  - `AGENTS.md`
  - `agents.md`
  - `PLAN.md` missing
  - `plan.md` missing
  - `README.md`
  - `docs/handoffs/task-completions/integration-status.md`
  - root `integration-status.md` missing
- Git/runtime state:
  - `git status --short`: broad unrelated dirty/parked work exists and was preserved.
  - `git rev-parse --short HEAD`: `4b8ac0c`
  - `git log -1 --oneline`: `4b8ac0c fix: align hanging sign placement`
  - `git diff --name-only`: unrelated parked files only before this handoff.
  - `git diff --cached --name-only`: empty before this handoff.
- Runtime/version:
  - `curl -sS http://127.0.0.1:8770/api/version`
  - Result: `git_sha` `4b8ac0c`, branch `feature/answer-api`, `retrieval_mode` `hybrid_private_first`, `auth_provider` `cloudflare_access`.
- Public/protected headers:
  - `curl -sS -I 'https://steelguitarrag.com/?v=4b8ac0c'`: `HTTP/2 200`.
  - `curl -sS -I 'https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=4b8ac0c'`: `HTTP/2 302` to Cloudflare Access for unauthenticated curl, expected.
- Deployment command run after initial public measurements showed stale landing placement:
  - `CLOUDFLARE_ACCOUNT_ID=7b941aeb1d27d10a4cd5a23781e99ae0 npx --yes wrangler@latest pages deploy deploy/landing --project-name steel-guitar-rag-landing --branch feature/answer-api --commit-dirty=true`
  - Result: success; deployment URL `https://5fb9cedf.steel-guitar-rag-landing.pages.dev`.
- Final check:
  - `git diff --check`: passed.
  - Staged-diff checks recorded in final response.

## Smoke Target
```text
Smoke Target:
- Target type: public landing + protected preview browser smoke
- Result type: browser smoke
- Exact public URL tested: https://steelguitarrag.com/?v=4b8ac0c
- Exact app UI URL tested: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=4b8ac0c
- Cache-busted URL tested: yes, commit hash cachebuster
- Exact URL the user should use:
  - https://steelguitarrag.com/?v=4b8ac0c
  - https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=4b8ac0c
- Auth required: public no; app yes
- Auth provider: public none; app Cloudflare Access
- Cloudflare Access login result: succeeded; protected-preview app loaded, not the login page.
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 4b8ac0c
- Version endpoint: /api/version
- Version endpoint result: local origin returned git_sha 4b8ac0c. Unauthenticated public app curl redirects to Cloudflare Access as expected.
- If version endpoint missing, how version is inferred: not missing.
- Whether app root `/` works: yes; https://app.steelguitarrag.com/?v=4b8ac0c redirects to https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html and loads the app.
- Whether app root `/` is expected to work: yes as an entry route, with redirect to the UI shell.
- Whether `/ui/steel-guitar-rag-mock.html` works: yes.
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes.
- Who should test this URL: Codex and the user.
- Do not test these URLs: unauthenticated app curl as proof of app rendering; local API fallback as protected-preview browser proof.
- Known caveats: app root redirects to /ui/steel-guitar-rag-mock.html and drops the query string; direct UI URL preserves the cachebuster.
- API fallback status: not used as browser proof.
- Desktop viewport result: pass.
- Mobile viewport result: pass.
- Horizontal overflow result: pass, no overflow.
- Console errors: none captured.
```

## Deployed/runtime commit observed
- Repo HEAD: `4b8ac0c`.
- Local protected-preview runtime `/api/version`: `4b8ac0c`.
- Public landing page has no runtime commit endpoint; the final browser measurements after Cloudflare Pages deployment match the `4b8ac0c` placement.
- Cloudflare Pages deployment URL: `https://5fb9cedf.steel-guitar-rag-landing.pages.dev`.

## Desktop result
Final exact URL measurements at `1280 x 720`:

| Surface | URL | Sign rect | Overflow | Console errors |
| --- | --- | --- | --- | --- |
| Public root | `https://steelguitarrag.com/?v=4b8ac0c` | `top -46.24`, `left -18`, `width 305.79`, `height 232.78` | none, `overflowDelta 0` | none |
| Protected app UI | `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=4b8ac0c` | `top -46.24`, `left -18`, `width 305.79`, `height 232.78` | none, `overflowDelta 0` | none |
| Public `www` check | `https://www.steelguitarrag.com/?v=4b8ac0c-after-deploy` | `top -46.24`, `left -18`, `width 305.79`, `height 232.78` | none, `overflowDelta 0` | none |

Result: pass. The public and app desktop sign placement visually match and use the app-preferred rect from the Lane 06 report.

## Mobile result
Final exact URL measurements at `390 x 844`:

| Surface | URL | Sign rect | Overflow | Console errors |
| --- | --- | --- | --- | --- |
| Public root | `https://steelguitarrag.com/?v=4b8ac0c` | `top 2.39`, `left -18`, `width 218.64`, `height 166.43` | none, `overflowDelta 0` | none |
| Protected app UI | `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=4b8ac0c` | `top 2.39`, `left -18`, `width 218.64`, `height 166.43` | none, `overflowDelta 0` | none |

Result: pass. The public and app mobile sign placement visually match and use the app-preferred rect from the Lane 06 report.

## Root URL behavior
- `https://steelguitarrag.com/?v=4b8ac0c`: loads the public landing page directly.
- `https://app.steelguitarrag.com/?v=4b8ac0c`: redirects to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`, loads the protected app, and drops the query string.
- Direct protected-preview UI path with the cachebuster works and should be used for app smoke:
  - `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=4b8ac0c`

## Console errors
- Public desktop: none captured.
- Public mobile: none captured.
- Protected app desktop: none captured.
- Protected app mobile: none captured.
- `www` public check: none captured.

## Horizontal overflow result
- Public desktop: pass, no horizontal overflow.
- Public mobile: pass, no horizontal overflow.
- Protected app desktop: pass, no horizontal overflow.
- Protected app mobile: pass, no horizontal overflow.

## Blockers
- None for the hanging-sign placement smoke.

## Risk assessment
- Risk: Low.
- Reason: the verification involved only browser smoke and a documented static Cloudflare Pages deploy of `deploy/landing`; no source code, auth, DNS, backend, Chroma/vector, corpus, or scraping changes were made.
- Rollback notes: use Cloudflare Pages rollback/promote controls to restore a prior landing deployment if a public landing regression appears. Protected preview runtime is already at `4b8ac0c`; no restart was required.

## Human decision needed
- No.

## Safe-to-stage exact file list
- `docs/handoffs/task-completions/2026-06-19-1122-12-hanging-sign-protected-preview-smoke.md`

## Files that must not be staged
- All unrelated dirty/parked files shown by `git status --short`.
- Runtime/source/UI files not touched by this task.
- Corpus, Chroma/vector stores, embeddings, `source-inbox`, `.wrangler`, `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated/private artifacts, and deployment/auth/DNS policy files.

## Recommended next lane
- Lane 01 Repo Steward: refresh `docs/handoffs/task-completions/integration-status.md` with `4b8ac0c` and this Lane 12 smoke result.

## Commit readiness
Safe to commit

## Suggested next step
User smoke these URLs:

```text
https://steelguitarrag.com/?v=4b8ac0c
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=4b8ac0c
```

Then run Lane 01 integration-status refresh:

```text
Lane 01 Repo Steward: Refresh docs/handoffs/task-completions/integration-status.md with Lane 06 commit 4b8ac0c and Lane 12 handoff docs/handoffs/task-completions/2026-06-19-1122-12-hanging-sign-protected-preview-smoke.md. Preserve unrelated dirty work, stage exact paths only, and do not touch corpus, Chroma, embeddings, scraping, auth, DNS, or Cloudflare Access policy.
```
