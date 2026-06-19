# 2026-06-19 - Lane 12 Private Preview Landing Deploy Smoke

## Task Summary

Requested Lane 12 deployment/smoke for commit `0bbdef0 refresh private preview landing page`.

Completed:

- Confirmed local HEAD is `0bbdef0`.
- Confirmed `ui/steel-guitar-rag-landing.html` and `deploy/landing/index.html` are synced.
- Ran focused public landing tests.
- Deployed the committed `deploy/landing` artifact to Cloudflare Pages using the documented project workflow.
- Verified the refreshed landing copy on the Pages deployment URL and the public custom domains.
- Browser-smoked desktop and mobile layouts at the public landing root.

Intentionally not changed: backend behavior, auth/session behavior, DNS, Cloudflare Access policy, corpus, scraping, embeddings, Chroma/vector stores, secrets, private transcripts, and form routing.

## Smoke Target

- Target type: public landing + Cloudflare Pages deployment smoke
- Result type: browser smoke
- Exact browser URL tested: `https://steelguitarrag.com/?v=0bbdef0`
- Cache-busted URL tested: `https://steelguitarrag.com/?v=0bbdef0`
- Exact URL the user should use: `https://steelguitarrag.com/?v=0bbdef0`
- Auth required: no for the public landing page
- Auth provider: none for public landing; Cloudflare Access remains on `app.steelguitarrag.com`
- Cloudflare Access login result: not required for public landing smoke
- Local backend URL: not applicable
- Expected backend port: not applicable
- Expected git HEAD: `0bbdef0`
- Version endpoint: not available for static public landing
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: Pages deployment was created from local HEAD `0bbdef0` and verified by live HTML copy matching the committed landing artifact
- Whether app root `/` works: `https://app.steelguitarrag.com/?v=0bbdef0` remains Cloudflare Access protected; it is not the public landing deploy target
- Whether app root `/` is expected to work: yes for the protected app shell after Access; not expected to serve the public Pages landing
- Whether `/ui/steel-guitar-rag-mock.html` works: not part of this public landing smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes for protected app smoke, but not relevant here
- Who should test this URL: the user
- Do not test these URLs: do not treat `https://app.steelguitarrag.com/?v=0bbdef0` as the public landing deploy smoke URL
- Known caveats: root `app.steelguitarrag.com` is separate and protected by Cloudflare Access; the public landing page is served by Cloudflare Pages at `steelguitarrag.com` and `www.steelguitarrag.com`

## Deployment / Publish Action

Used the documented Cloudflare Pages direct-upload workflow from `docs/cloudflare-pages-landing.md`:

```bash
CLOUDFLARE_ACCOUNT_ID=7b941aeb1d27d10a4cd5a23781e99ae0 npx --yes wrangler@latest pages deploy deploy/landing --project-name steel-guitar-rag-landing --branch feature/answer-api --commit-dirty=true
```

Result:

- Wrangler version: `4.103.0`
- Deploy result: success
- Pages deployment URL: `https://841e0459.steel-guitar-rag-landing.pages.dev`
- Uploaded files: `1` uploaded, `7` already uploaded

No DNS, auth, Tunnel, Cloudflare Access policy, backend, corpus, Chroma, embeddings, or scraping changes were made.

## Deployed Commit

- Local HEAD before deploy: `0bbdef0`
- Commit: `0bbdef0 refresh private preview landing page`
- `deploy/landing/index.html` and `ui/steel-guitar-rag-landing.html`: synced by `cmp -s`

## URLs Checked

- `https://841e0459.steel-guitar-rag-landing.pages.dev/?v=0bbdef0`
- `https://steelguitarrag.com/?v=0bbdef0`
- `https://www.steelguitarrag.com/?v=0bbdef0`
- `https://app.steelguitarrag.com/?v=0bbdef0` for root behavior only

## Root Behavior

- `https://steelguitarrag.com/?v=0bbdef0`: `200 text/html; charset=utf-8`
- `https://www.steelguitarrag.com/?v=0bbdef0`: live HTML contains the refreshed landing copy
- `https://app.steelguitarrag.com/?v=0bbdef0`: redirects through Cloudflare Access, then serves the protected app shell. This is expected because `app` is the private-preview app, not the public landing page.

## Landing Page Behavior

Live HTML on Pages and custom domains includes the refreshed copy:

- `private-preview assistant built for E9 players`
- `Built for pedal steel`
- `grips, pedals, levers`
- `Useful examples without crossing provenance lines`
- `No live RAG access is exposed from this public landing page`

Live HTML still contains the landing sign markup:

- `.hero-hanging-sign`
- `brand/steel-guitar-rag-landing-alpha.webm`
- `brand/steel-guitar-rag-landing-fallback-alpha.png`

The deployed page does not contain `/api/answer`.

## Form Behavior

Verified without submitting data:

- Form is present and visible.
- Form method remains `post`.
- Form action remains `/api/interest`.
- Client fetch still posts to `/api/interest`.
- Email field is visible.
- Submit button is visible and labeled `Join the interest list`.

No test submission was performed because this task did not identify a documented safe no-op submission path.

## Desktop Smoke

Browser URL:

`https://steelguitarrag.com/?v=0bbdef0`

Viewport:

- `1280 x 900`

Result:

- Refreshed landing copy visible.
- Interest form visible.
- No `/api/answer` reference in DOM.
- No horizontal overflow.
- Sign visible and not dominating the landing page:
  - sign rect: top `-46.24`, left `-18`, width `305.79`, height `232.78`
  - viewport share: about `24%` width and `26%` height
- Console errors: none observed.

## Mobile Smoke

Browser URL:

`https://steelguitarrag.com/?v=0bbdef0`

Viewport:

- `390 x 844`

Result:

- Refreshed landing copy visible.
- Interest form visible.
- No `/api/answer` reference in DOM.
- No horizontal overflow.
- Sign visible and not dominating the landing page:
  - sign rect: top `2.39`, left `-18`, width `218.64`, height `166.43`
  - viewport share: about `56%` width and `20%` height
- Console errors: none observed.

## Checks Run

```bash
sed -n '1,220p' AGENTS.md
for f in agents.md PLAN.md plan.md README.md docs/handoffs/task-completions/integration-status.md; do ...
git status --short
git rev-parse --short HEAD
git log --oneline -8
git diff --name-only
git diff --cached --name-only
rg -n "landing|wrangler|pages deploy|Cloudflare Pages|deploy/landing|steel-guitar-rag-landing|pages.dev" docs README.md package.json pyproject.toml scripts deploy -S
sed -n '1,260p' docs/cloudflare-pages-landing.md
sed -n '1,240p' /Users/cory/.codex/skills/wrangler/SKILL.md
cmp -s ui/steel-guitar-rag-landing.html deploy/landing/index.html
git diff --check
.venv/bin/python -m pytest tests/test_public_landing_page.py -q
rg -n "/api/answer|/api/interest|pedal steel|grips|pedals|levers|tone|copedent|blocking|fretboard-aware|source-aware|copyright|provenance|private-preview" ui/steel-guitar-rag-landing.html deploy/landing/index.html
find deploy/landing -maxdepth 3 -type f | sort
npx --yes wrangler@latest --version
CLOUDFLARE_ACCOUNT_ID=7b941aeb1d27d10a4cd5a23781e99ae0 npx --yes wrangler@latest pages deploy deploy/landing --project-name steel-guitar-rag-landing --branch feature/answer-api --commit-dirty=true
curl -L -sS -H 'Cache-Control: no-cache' 'https://841e0459.steel-guitar-rag-landing.pages.dev/?v=0bbdef0' | rg ...
curl -L -sS -H 'Cache-Control: no-cache' 'https://steelguitarrag.com/?v=0bbdef0' | rg ...
curl -L -sS -H 'Cache-Control: no-cache' 'https://www.steelguitarrag.com/?v=0bbdef0' | rg ...
curl -L -sSI -H 'Cache-Control: no-cache' 'https://steelguitarrag.com/?v=0bbdef0'
curl -L -sSI -H 'Cache-Control: no-cache' 'https://app.steelguitarrag.com/?v=0bbdef0'
```

Results:

- `git diff --check`: passed before deploy.
- `tests/test_public_landing_page.py`: `31 passed`.
- Wrangler deploy: passed.
- Browser smoke desktop/mobile: passed.
- Console errors: none observed.
- Final `git diff --check` after handoff creation: passed.

## Risks

Risk: low.

Notes:

- The deploy was performed from the documented `deploy/landing` static artifact with `--commit-dirty=true`, which is the current early-preview Pages workflow.
- Broad unrelated dirty/untracked work remains parked.
- `app.steelguitarrag.com` remains the protected app route, not the public Pages landing route.
- The Pages deployment is direct-upload/manual; another deploy from an older artifact could overwrite it.

## Blockers

None for the public landing deploy/smoke.

## Unrelated Dirty Files Left Untouched

The task began with broad unrelated dirty/untracked files, including docs/corpus metadata, root RAG scripts, source-inbox metadata, generated/private-helper scripts, historical handoffs/assets, `public/`, `ui/brand/`, `Neon Sign/`, and deployment/static asset files outside this exact task. They were not staged or modified by this task.

## Human Decision Needed

No for the deploy/smoke result.

If the user approves the visual/copy result, the next decision is whether Lane 01 should refresh `integration-status.md`.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-19-12-private-preview-landing-deploy-smoke.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox/`
- `.wrangler/`
- `public/`
- `ui/brand/`
- `Neon Sign/`
- raw design assets
- generated/private data
- credentials or environment files

## Recommended Next Lane

- User smoke the refreshed public landing page.
- Lane 01 Repo Steward: refresh `docs/handoffs/task-completions/integration-status.md` if user smoke passes.
- Lane 06 UX/UI Design: handle any visual/copy defects from user smoke.
- Lane 12 or Lane 11: handle deployment/root/auth behavior failures if reported.

## Commit Readiness

Safe to commit.

Only this docs handoff should be staged if committing this Lane 12 smoke report.

## Suggested Next Step

User smoke:

- `https://steelguitarrag.com/?v=0bbdef0`
- `https://www.steelguitarrag.com/?v=0bbdef0`

If approved, run Lane 01 integration-status refresh for commit `0bbdef0` and this Lane 12 deploy/smoke result.
