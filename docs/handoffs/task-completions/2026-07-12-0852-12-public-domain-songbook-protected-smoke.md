# Public-domain songbook protected-preview smoke

## Task summary

Restarted the protected preview on committed feature HEAD `d2dc94d` and completed authenticated browser smoke for the 12-song Melody Studio songbook. The full catalog, search, staff review, and E9 arrangement journey passed. No auth, DNS, Cloudflare policy, secret, corpus, source-inbox, Chroma, embedding, private-data, or deployment configuration was changed.

## Files changed

- `docs/handoffs/task-completions/2026-07-12-0852-12-public-domain-songbook-protected-smoke.md` (this report)

No runtime files were changed during deployment verification.

## Tests and checks

- Verified the existing port-8770 listener belonged to the current user and matched the documented preview command.
- Terminated only that listener; the installed LaunchDaemon restarted it as PID 83216.
- Loopback `/api/version` returned commit `d2dc94d`, branch `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, `melodyExercise=true`, and `melodyCatalog=true`.
- Authenticated protected browser smoke passed at the exact cache-busted Studio URL.
- Protected browser console errors: none.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-songbook-d2dc94d-20260712`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-songbook-d2dc94d-20260712`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-songbook-d2dc94d-20260712`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `d2dc94dd1e768ac0fae1a002e283e71f7f1c8406`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `d2dc94d`, expected branch/retrieval/auth mode, `melodyExercise=true`, `melodyCatalog=true`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; protected root redirected to the canonical home route
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: bare domain without the direct Studio path/cache bust; local port 8770 as evidence of Cloudflare Access browser behavior
- Known caveats: direct JSON navigation to the public `/api/version` URL was blocked by the browser client, so exact version identity was verified at loopback; authenticated catalog/API behavior was verified through the protected Studio browser journey. API fallback is not browser smoke.

## Browser results

- The direct Studio URL loaded in the existing signed-in Cloudflare Access session.
- Built-in songbook opened with all 12 cards, complete metadata, filters, and attribution.
- Search for `Shenandoah` produced exactly one result and the `1 of 12` status.
- Review melody opened Shenandoah as a confirmed C-major, 3/4 staff with 16 selectable events.
- Arrange for E9 rendered Section 1 with source attribution, score, fretboard, tab, six arrangement routes, active-note controls, Print tablature, and Continue to Section 2.
- The result retained the melody as the lesson identity and rendered no browser console errors.

## Integration notes

- Feature commit: `d2dc94d feat: add Melody Studio public-domain songbook`.
- User uploads/imports remain disabled unless `melodyImport=true`; the built-in songbook is independently available through `melodyCatalog=true`.
- The signed-in Studio tab was left open on the arranged Shenandoah lesson for user smoke.

## Risk assessment

Low. This was a restart and read-only verification of the approved committed feature. Rollback would restart the prior commit; no data or configuration migration exists.

## Human decision needed

No. The build is ready for user smoke.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-12-0852-12-public-domain-songbook-protected-smoke.md`

## Files that must not be staged

Every other modified or untracked file, including corpus/source/pipeline work, source-inbox data, private-data tooling, deployment files, public/brand assets, `ui/brand/`, `Neon Sign/`, generated reports, and the separate octave-help recommendation.

## Recommended next lane

`01 Repo Steward` for a separate integration-status refresh, then user smoke.

## Commit readiness

Safe to commit

## Suggested next step

Refresh `integration-status.md` to HEAD `d2dc94d`, commit only the protected-smoke handoff and status snapshot, and hand the exact cache-busted Studio URL to the user.
