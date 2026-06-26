# Lane 12 - Explorer Compact Copedent Protected Smoke Rerun

## Task Summary

Requested rerun of Lane 12 protected-preview smoke for the compact Explorer copedent UI after the user performed the interactive Mac mini restart.

Completed:
- Inspected repo guidance and Mac mini runtime guidance.
- Confirmed current branch and HEAD.
- Confirmed current HEAD contains the expected UI code commit `5a59739`.
- Confirmed local `/api/version` is no longer the stale `ffac52a` runtime.
- Attempted protected-preview browser smoke at the exact cache-busted Explorer URL.
- Stopped before Explorer UI assertions because the in-app browser landed on Cloudflare Access login / verification-code flow.

Intentionally not changed:
- No app runtime/UI code was edited.
- No DNS, Cloudflare Access policy, secrets, auth policy, scraping, embeddings, Chroma/vector stores, raw corpus, private transcript files, or deployment config was changed.
- API fallback was not reported as browser smoke.

## Smoke Target

- Target type: protected-preview
- Result type: blocked browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625`
- Exact URL the user should use: blocked pending Cloudflare Access completion in the in-app browser
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: blocked; browser landed on Cloudflare Access login / verification-code flow
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected UI code commit: `5a59739`
- Expected runtime: `4040a47` or later is acceptable because it contains `5a59739`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `git_sha=4040a47`, `git_branch=feature/answer-api`, `auth_provider=cloudflare_access`, `retrieval_mode=hybrid_private_first`, `server_started_at=2026-06-26T01:51:23.747502+00:00`
- Runtime HEAD contains `5a59739`: yes; `git merge-base --is-ancestor 5a59739 HEAD` returned `0`
- Whether app root `/` works: not tested past Cloudflare Access because authentication blocked protected browser access
- Whether app root `/` is expected to work: yes, with known redirect/query-string caveat from prior smoke docs
- Whether `/ui/e9-fretboard-explorer.html` works: not verified past Cloudflare Access in protected browser
- Whether `/ui/e9-fretboard-explorer.html` is expected to work: yes after Access login
- Who should test this URL: Lane 12 after Cloudflare Access verification is completed in the in-app browser
- Do not test these URLs: do not treat local `127.0.0.1` as protected-preview browser proof
- Known caveats: direct `/ui/...?...` URL is required for cache-busted Explorer validation because root drops query strings

## Runtime Verification

- Branch: `feature/answer-api`
- Starting HEAD: `4040a47`
- Current HEAD before this docs handoff: `4040a47`
- `4040a47` is a docs-only commit after `5a59739`.
- Runtime `/api/version` reports `4040a47`.
- Runtime no longer reports stale `ffac52a`.
- The expected UI code commit `5a59739` is contained in current HEAD.

## Protected Browser Result

Attempted URL:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625
```

Observed:

- Final browser URL was a Cloudflare Access URL under `late-waterfall-73da.cloudflareaccess.com`.
- Page title: `Sign in ・ Cloudflare Access`.
- Page body showed `Log in to Steel Guitar RAG Private Preview`, `Private Beta Access`, `Email`, and `Send login code`.
- A subsequent tab check showed the in-app browser on Cloudflare Access `verify-code`.

Protected Explorer smoke was therefore blocked by authentication and did not reach the app page.

## Explorer Smoke Criteria

Not executed because Cloudflare Access blocked protected browser access.

Pending checks after authentication succeeds:

- Page loads at the cache-busted protected-preview URL.
- Fretboard is visible without unnecessary scroll on normal desktop/laptop viewport.
- Compact filters are usable.
- Copedent chart is hidden by default behind `View chart`.
- `View chart` opens and closes the chart near the copedent selector.
- Emmons E9 does not include LKV/B-to-Bb.
- `Custom E9 (with LKV)` exists as the custom setup.
- Pedal/lever impact preview is compact and interactive.
- Notes / Intervals toggle works.
- Fretboard cells do not combine fret number with note/interval text.
- Console has no relevant errors.

## Root URL Behavior

Not tested past Cloudflare Access in this rerun.

Known from prior integration notes:
- Root redirects to `/ui/steel-guitar-rag-mock.html`.
- Root drops query strings.
- Direct `/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625` remains the correct cache-busted Explorer smoke URL.

## API Fallback Status

API fallback was not used as browser smoke.

Local `/api/version` was used only as a runtime version gate.

## Files Changed

- Created: `docs/handoffs/task-completions/2026-06-25-2052-12-explorer-compact-copedent-protected-smoke-rerun.md`
- Updated: `docs/handoffs/task-completions/integration-status.md`

No implementation files were changed.

## Tests And Checks Run

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git merge-base --is-ancestor 5a59739 HEAD`
- `curl -sS http://127.0.0.1:8770/api/version`
- `git diff --check`
- `git diff --cached --name-only`
- In-app browser attempt at the exact protected-preview Explorer URL
- In-app browser tab listing to check for an authenticated tab

Skipped:
- Protected Explorer UI assertions, because Cloudflare Access blocked access before the app page loaded.
- Screenshots, because the app page was not reached.

## Risks

Risk: medium.

The runtime is now correct, but user smoke is not ready because protected-preview browser behavior remains unverified. The remaining blocker is Cloudflare Access session completion in the in-app browser, not stale runtime.

## Human Decision Needed

Yes.

Complete the Cloudflare Access verification-code flow in the in-app browser, then rerun Lane 12 protected-preview smoke against:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625
```

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-25-2052-12-explorer-compact-copedent-protected-smoke-rerun.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- Any backend/runtime/UI/test files outside this docs-only smoke update
- Auth, DNS, Cloudflare, tunnel, LaunchDaemon, or private env files
- Corpus, private corpus, Chroma/vector stores, embeddings, scraper output, source-inbox raw/provenance files, credentials, logs, generated/private artifacts, and unrelated dirty work

## Recommended Next Lane

Lane 12 Self-Hosted Deployment.

## Commit Readiness

Safe to commit for docs-only smoke/status update if staged with exact paths only.

## Suggested Next Step

```text
Lane 12: Cloudflare Access is on the verification-code page in the in-app browser. After the Access flow is completed, rerun protected-preview smoke for https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625. Runtime /api/version already reports 4040a47, which contains 5a59739.
```
