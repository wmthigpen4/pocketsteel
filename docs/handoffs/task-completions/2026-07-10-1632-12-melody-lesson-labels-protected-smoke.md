# Melody Studio lesson labels protected smoke

## Task summary

Verified the committed Melody Studio lesson-label cleanup on the authenticated protected preview. Artificial lyric-step tab rows are gone, event selectors use plain-language note positions, and the recommended harmony route is labeled once.

No auth, DNS, Tunnel, corpus, source, private-data, or deployment-policy changes were made. The installed LaunchDaemon restarted the user-owned preview process after the prior listener was terminated.

## Files changed

- `docs/handoffs/task-completions/2026-07-10-1632-12-melody-lesson-labels-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Tests and checks

- Implementation commit: `1249201 fix melody lesson labels`.
- Full pytest before commit: 921 passed.
- Loopback `/api/version`: `1249201`, branch `feature/answer-api`, `features.melodyExercise=true`.
- Cloudflare Access authenticated browser smoke: passed.
- Protected root and canonical home-route browser smoke: passed.
- Anonymous protected root request: HTTP 302 to the access flow, as expected.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-lesson-labels-1249201-20260710`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-lesson-labels-1249201-20260710`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-lesson-labels-1249201-20260710`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `1249201`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `1249201`, expected branch and feature flag
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; authenticated browser loaded the home application
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: stale Melody Studio cache keys from earlier commits
- Known caveats: protected runtime version was verified through the loopback endpoint of the same tunneled process; API verification is not browser smoke

## Smoke result

PASS. Generated the G-major song-arrangement phrase `5 6 1 3 2 1 3` and verified:

- primary routes were `Playable single-note melody` and `Recommended harmony`;
- `Recommended · Recommended harmony` was absent;
- first event selector displayed `1. D4` and `String 5 · Fret 3 · Open`;
- second event selector displayed `2. E4` and `String 5 · Fret 3 · A pedal`;
- active-tab caption displayed `Active tab note 1: D4 · String 5 · Fret 3 · Open`;
- no compact `S5 F3`-style position text remained in the transport area;
- tab contained no `Ly |` row;
- no `[object Object]` text rendered;
- root `/` and `/ui/steel-guitar-rag-mock.html` loaded the authenticated home UI.

## Integration notes

Real lyric rows remain supported by the shared tab engine. Only Melody Studio's generated `step N` lyric metadata was removed.

## Risk assessment

Low. Mechanical tab validation, pitch placement, fretboard synchronization, and harmony routing are unchanged. Rollback is commit `1249201`.

## Human decision needed

No. User smoke may continue at the exact URL above.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-10-1632-12-melody-lesson-labels-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All unrelated dirty and untracked corpus, source-inbox, brand, deployment, private-data, generated-report, and parked documentation paths.

## Recommended next lane

User smoke, with any observed defect returning to the autopilot repair loop.

## Commit readiness

Safe to commit

## Suggested next step

Confirm the tab and event-selector labels feel natural to a steel player at the exact protected URL.
