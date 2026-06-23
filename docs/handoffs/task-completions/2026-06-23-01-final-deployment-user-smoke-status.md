# 2026-06-23 Lane 01 Final Deployment User-Smoke Status

## Task Summary

Requested: refresh integration status after LaunchDaemon supervision and protected-preview smoke progressed, reconcile latest Lane 12/Lane 06/Lane 15 handoffs, and record the current deployment/runtime/user-smoke readiness state.

Completed:
- Read required repo governance/status files and latest handoffs.
- Reconciled the latest launchd-supervised protected-preview smoke with the Explorer 5&8 label-leak fix.
- Updated `integration-status.md` with current branch, HEAD, runtime `/api/version`, LaunchDaemon status, Cloudflare Tunnel status, protected-preview smoke result, user-smoke URLs, G 5&8 backend/API QA status, Explorer UI status, remaining caveats, and next lane guidance.

Intentionally not changed:
- No backend, UI, deployment, launchd, auth, DNS, Cloudflare, corpus, Chroma/vector, embedding, source, secret, or runtime files were modified.
- No services were restarted.
- No protected-preview smoke was run by this Lane 01 refresh.

## Pass / Warn / Fail

PASS.

Protected preview is ready for user smoke based on the latest Lane 12 handoff.

## Branch And Head

- Branch: `feature/answer-api`
- Starting HEAD: `f15ef6c docs: record protected smoke after five eight label fix`
- Final HEAD before this docs-only handoff commit: `f15ef6c docs: record protected smoke after five eight label fix`
- Latest protected-preview runtime `/api/version`: `3a07c8f`

## Deployment Readiness

Ready for user smoke.

Evidence from `2026-06-23-12-protected-smoke-after-five-eight-label-fix.md`:

- LaunchDaemon is loaded and running.
- launchd owns the app runtime on `127.0.0.1:8770`.
- Manual screen runtime is gone.
- Cloudflare Tunnel is running.
- Cloudflare Access login succeeded.
- Main app browser smoke passed.
- Explorer browser smoke passed.

## Protected-Preview Readiness

Ready.

Exact URLs for user smoke after Cloudflare Access login:

```text
Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=3a07c8f

E9 Fretboard Explorer:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=3a07c8f
```

Root caveat:

- `https://app.steelguitarrag.com/?v=3a07c8f` redirects to `/ui/steel-guitar-rag-mock.html` and drops the query string.
- Use the direct `/ui/...?...` URLs above for cache-busted smoke.

## User-Smoke Status

- User-smoke status: protected preview ready for user smoke.
- User smoke itself was not performed by this Lane 01 docs refresh.
- Latest Lane 12 protected-preview smoke passed and explicitly says the user can proceed with user smoke.

## G 5&8 Status

Backend/API:

- `c08cc95 feat: add deterministic G harmonized scale rules` is in branch history.
- Lane 15 QA passed for the exact `Show me a G harmonized scale on strings 5 and 8.` backend/API behavior.
- The deterministic answer is fretboard-first, source-free, warning-free, tab-free, and includes the validated frets/routes.

Explorer UI:

- `0d10843 fix: label g five eight fretboard branch` exposed the `5&8 branch positions` UI and `5-8` filter.
- `3a07c8f fix: hide five eight internal branch label` fixed the raw internal label leak.
- Latest protected-preview smoke confirmed raw `five_eight_branch` no longer appears in visible Explorer text.

## Files Changed

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-01-final-deployment-user-smoke-status.md`

## Tests And Checks Run

Read/inspection commands:

```bash
git status --short
git diff --cached --name-only
git diff --check
git branch --show-current
git rev-parse --short HEAD
git log --oneline -20
```

Required commit-gate checks to run after staging:

```bash
git diff --cached --name-only
git diff --cached
git diff --cached --check
```

## Risks

Low.

This is docs-only status refresh work. The main risk is status drift if runtime is restarted from a later commit without another Lane 12 handoff.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-01-final-deployment-user-smoke-status.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files shown by `git status --short`.
- Backend, UI, deployment, launchd, auth, DNS, Cloudflare, corpus, Chroma/vector, embedding, source, source-inbox, private data, generated reports, brand/design asset, or runtime files.

## Recommended Next Lane

User smoke can continue. Route new defects by owning lane:

- Lane 05 for backend answer/routing/source issues.
- Lane 06 for UI/fretboard/tab/Explorer rendering issues.
- Lane 11 for Cloudflare Access/auth issues.
- Lane 12 for runtime/version/restart/deployment issues.
- Lane 15 for regression/smoke QA issues.

## Commit Readiness

Safe to commit after exact-path staging and cached diff review.
