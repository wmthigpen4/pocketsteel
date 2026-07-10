# Melody Studio fretboard cleanup protected smoke

## Task summary

Verified the committed Melody Studio fretboard-card cleanup on the authenticated protected preview. The generic position-card strip, filters, legend, and full technical inspector are absent. A compact Current note readout gives the active note's string, fret, and control state, and the visible fretboard highlight follows Previous/Next note navigation.

No implementation, auth, DNS, Tunnel, corpus, source, private-data, or deployment-policy changes were made during smoke. The already-installed LaunchDaemon restarted the user-owned preview process after its previous listener was terminated.

## Files changed

- `docs/handoffs/task-completions/2026-07-10-1611-12-melody-fretboard-cleanup-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Tests and checks

- Implementation commit: `6c51a47 fix melody fretboard lesson clarity`.
- Loopback `/api/version`: `6c51a47`, branch `feature/answer-api`, `features.melodyExercise=true`.
- Cloudflare Access authenticated browser smoke: passed.
- Protected root browser smoke: passed.
- Protected canonical home-route browser smoke: passed.
- Melody Studio G-major `5 6 1 3` generation and event synchronization: passed.
- Anonymous protected root request: HTTP 302 to the access flow, as expected.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-fretboard-cleanup-6c51a47-20260710`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-fretboard-cleanup-6c51a47-20260710`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-fretboard-cleanup-6c51a47-20260710`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `6c51a47dcb17e386fc825e01f0ce452921b381a7`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `6c51a47`, expected branch and feature flag
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; authenticated browser loaded the home application
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: stale Melody Studio cache keys from earlier commits
- Known caveats: direct protected JSON navigation to `/api/version` was blocked by the browser client, so the protected runtime version was verified through the loopback endpoint of the same tunneled process; this version check is API verification, not browser smoke

## Smoke result

PASS.

- Initial active event: `D (D4)`, `String 7 · Fret 8 · Open`.
- After Next note: `E (E4)`, `String 6 · Fret 8 · Open`.
- The figure's selected position and visible `.is-selected` fretboard highlight both advanced from event 1 to event 2.
- Selector cards: zero.
- Technical detail boxes: zero.
- Fretboard filter panels: zero.
- Fretboard legends: zero.
- `[object Object]`: absent.
- Root `/` and `/ui/steel-guitar-rag-mock.html` both loaded the authenticated home UI with the Melody Studio header link.
- API fallback status: loopback `/api/version` passed; it is not browser smoke.

## Integration notes

Protected runtime was refreshed without prompting for a password by terminating only the user-owned port-8770 listener. The installed LaunchDaemon restarted it at the current commit.

## Risk assessment

Low. The committed scope is UI clarity plus a covered selection helper compatibility change. Rollback is commit `6c51a47`.

## Human decision needed

No. User smoke may continue at the exact URL above.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-10-1611-12-melody-fretboard-cleanup-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All unrelated dirty and untracked corpus, source-inbox, brand, deployment, private-data, generated-report, and parked documentation paths.

## Recommended next lane

User smoke, with any observed defect returning to the autopilot repair loop.

## Commit readiness

Safe to commit

## Suggested next step

Test whether the compact Current note readout and the highlighted string/fret make the active position immediately understandable without the removed technical inspector.
