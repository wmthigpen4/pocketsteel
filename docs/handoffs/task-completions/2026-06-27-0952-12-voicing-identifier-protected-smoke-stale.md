# 2026-06-27 Lane 12 Voicing Identifier Protected Smoke Stale Runtime

## Task Summary

Requested as part of the Voicing Identifier extended-chord fix autopilot: run protected-preview smoke after committing the scoped Explorer fix.

Completed:

- Verified the implementation commit exists locally.
- Checked local `/api/version`.
- Opened the protected-preview Explorer URL after Cloudflare Access.
- Ran the same interaction script used for local smoke against protected preview.
- Determined protected preview is serving stale static Explorer assets for this slice.

Intentionally not changed:

- No protected-preview restart or deployment was performed.
- No auth, DNS, Cloudflare Access, secrets, corpus, Chroma, embeddings, scraper, or source data were touched.
- No files were modified by this Lane 12 smoke except this handoff and the integration-status refresh.

## Smoke Target

```text
Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-extended-chords-f305c49
- Cache-busted URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-extended-chords-f305c49
- Exact URL the user should use: not ready for user smoke; protected preview is stale for this slice
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded / existing session accepted; Explorer page loaded without Access prompt
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: f305c49
- Version endpoint: http://127.0.0.1:8770/api/version
- Version endpoint result: git_sha=4040a47, git_branch=feature/answer-api, server_started_at=2026-06-26T01:51:23.747502+00:00
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: yes, but not relevant to this Explorer-only smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, but not relevant to this Explorer-only smoke
- Who should test this URL: Lane 12 after protected-preview update/restart
- Do not test these URLs: stale protected Explorer URL above for user acceptance
- Known caveats: API fallback was not used; protected page loaded but served stale Explorer static assets
```

## Protected Smoke Result

Fail / stale protected-preview assets.

Observed protected behavior at the cache-busted URL:

- Page loaded and Cloudflare Access did not block the in-app browser.
- `G / fret 3 / strings 5-6-9 / A+B` still rendered `Dominant 7 / V7 grip` and did not show `Fmaj7(no3)`.
- `G / fret 3 / strings 5-7-9 / A+B` did not show `Fmaj7(no5)`.
- `F / fret 1 / strings 3-4-9 / open` did not show `F7(no5)`.
- No `[object Object]`.
- No browser warn/error logs.

This does not invalidate the committed implementation. It indicates protected preview has not picked up commit `f305c49`.

## Local Baseline

The same interaction script passed locally at:

```text
http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=voicing-extended-chords-local-20260627
```

Local smoke verified:

- `Fmaj7(no3)` for `G / fret 3 / strings 5-6-9 / A+B`.
- `Fmaj7(no5)` for `G / fret 3 / strings 5-7-9 / A+B`.
- `F7(no5)` for `F / fret 1 / strings 3-4-9 / open`.
- No dominant/V7 leak on major-7 partials.
- No `[object Object]`.
- No browser warn/error logs.

## Files Changed

- `docs/handoffs/task-completions/2026-06-27-0952-12-voicing-identifier-protected-smoke-stale.md`
- `docs/handoffs/task-completions/integration-status.md`

## Tests And Checks

Commands/checks run:

- `git rev-parse --short HEAD`
- `curl -sS 'http://127.0.0.1:8770/api/version'`
- In-app browser smoke against protected-preview URL listed above.

Results:

- Current committed HEAD: `f305c49`.
- `/api/version`: `4040a47`.
- Protected browser smoke: fail due stale protected static assets.

## Risks

Risk: medium.

The code is committed and locally verified, but protected preview is not serving the committed static Explorer assets. User smoke should not proceed until Lane 12 updates/restarts protected preview and records a pass.

## Human Decision Needed

No product decision needed.

Operational action needed:

- Lane 12 should update/restart protected preview from commit `f305c49` using the documented deployment/runtime procedure, then rerun the protected Explorer smoke.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-27-0952-12-voicing-identifier-protected-smoke-stale.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- All parked corpus/RAG/source/brand/private/generated files in the dirty worktree.
- `corpus-private/`
- `corpus-v2/`
- `source-inbox/` raw/provenance files
- Chroma/vector/embedding artifacts
- auth, DNS, deployment, or Cloudflare config files

## Recommended Next Lane

Lane 12 Self-Hosted Deployment.

## Commit Readiness

Safe to commit as docs/status refresh only.

## Suggested Next Step

```text
Lane 12: Update/restart protected preview for commit f305c49, then rerun protected-preview browser smoke at https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-extended-chords-f305c49. Verify Fmaj7(no3), Fmaj7(no5), F7(no5), omitted-tone wording, no Dominant/V7 leak on major-7 partials, no [object Object], and no relevant console errors.
```
