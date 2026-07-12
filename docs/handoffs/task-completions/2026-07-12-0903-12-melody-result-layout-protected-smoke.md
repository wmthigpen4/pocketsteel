# Melody Studio result-layout protected-preview smoke

## Task summary

Restarted the protected preview on implementation commit `03a372e` and completed authenticated browser smoke for the simplified Melody Studio result layout. The approved six-comment adjustment passed without browser errors.

No auth, DNS, Cloudflare Access policy, secrets, corpus, source-inbox, Chroma, embeddings, private data, or deployment configuration changed.

## Files changed

- `docs/handoffs/task-completions/2026-07-12-0903-12-melody-result-layout-protected-smoke.md` (this report)

No runtime implementation files changed during protected verification.

## Tests and checks

- Verified the port-8770 listener belonged to the current user and matched the documented preview process.
- Terminated only that listener; the installed LaunchDaemon restarted it as PID 88364.
- Loopback `/api/version` returned `03a372e`, `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, `melodyExercise=true`, and `melodyCatalog=true`.
- Authenticated browser smoke passed at the exact cache-busted Studio URL.
- Browser console errors: none.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-result-layout-03a372e-20260712`
- Cache-busted URL tested: same as above
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-result-layout-03a372e-20260712`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `03a372e672e713812eca7fa9216b1570ffcb17cb`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: exact expected commit, branch, retrieval/auth mode, and Melody flags
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: the prior `melody-print-tab-5007011-20260711` URL or unversioned Studio routes
- Known caveats: the automated smoke did not open the native macOS print dialog; API fallback is not browser smoke

## Browser results

- Reused the signed-in Cloudflare Access Studio session.
- Arranged the reviewed eight-event Amazing Grace draft into an E9 lesson.
- The introductory hero disappeared while the compact Melody Studio header remained.
- Edit melody appeared beside the lesson title and after the tablature.
- Loop options were available as one closed disclosure for the eight-event section.
- Octave colors, String labels, and Note labels began exactly at the fretboard bottom and preceded arrangement choices.
- No route-recommendation paragraph existed.
- Start over and Print shared the same bottom row beneath the tablature; the action label was exactly `Print`.
- Score, fretboard, six arrangement routes, note navigator, and tablature remained synchronized and visible.
- Browser console errors: none.

## Integration notes

- Implementation commit: `03a372e fix: simplify Melody Studio lesson layout`.
- The protected tab was left open on the arranged lesson for user smoke.
- The seven-note short-section loop suppression was verified in local browser smoke; protected smoke verified the complementary eight-note closed-disclosure state.

## Risk assessment

Low. This was a restart and read-only verification of a client-only layout adjustment. No persistent state or configuration migration exists.

## Human decision needed

No. The build is ready for continued user smoke.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-12-0903-12-melody-result-layout-protected-smoke.md`

## Files that must not be staged

Every other modified or untracked path, especially corpus/source/pipeline work, source-inbox data, private-data tooling, deployment files, `public/`, `ui/brand/`, `Neon Sign/`, generated reports, and the separate octave-help recommendation.

## Recommended next lane

`01 Repo Steward` for a separate integration-status refresh, then user smoke.

## Commit readiness

Safe to commit

## Suggested next step

Refresh `integration-status.md`, commit only this protected-smoke report and the status snapshot, and return the exact cache-busted Studio URL to the user.
