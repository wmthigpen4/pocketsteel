# Melody Studio lesson-focus protected-preview smoke

## Task summary

Restarted the committed protected runtime and verified the current Melody Studio lesson-focus adjustment through authenticated Cloudflare Access browser smoke. The system LaunchDaemon helper still requested an administrator password, so no credential was entered; the documented password-free fallback terminated only the user-owned port-8770 listener, and the installed LaunchDaemon respawned it at commit `9600f90`.

## Files changed

- this handoff
- `docs/handoffs/task-completions/integration-status.md` (separate coordination refresh)

No runtime implementation, auth, DNS, Tunnel, secrets, corpus, private-data, source, or deployment-policy files changed during this lane.

## Tests and checks

- Implementation commit: `9600f90 Simplify Melody Studio lesson controls`
- Loopback `/api/version`: `9600f90`, branch `feature/answer-api`, `features.melodyExercise=true`
- Authenticated Cloudflare Access browser load: pass
- Twelve-note phrase arrangement: pass; section one contained eight events and exposed Continue to Section 2
- Six route choices directly below fretboard: pass
- One active note card with readable string/fret/control text: pass
- Next-note synchronization: pass
- Octave colors default-off and adjacent hidden legend: pass
- Melody-only chord-backing suppression: pass
- Redundant deterministic explanation removal: pass
- `[object Object]`: absent
- Browser warnings/errors: none
- Authenticated root redirect and canonical home UI: pass
- Anonymous protected root: HTTP 302 to Cloudflare Access, expected

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-lesson-focus-9600f90-20260711`
- Cache-busted URL tested: same as above
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-lesson-focus-9600f90-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `9600f90`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `9600f90`, expected branch, auth provider, retrieval mode, and Melody Exercise feature
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; authenticated root redirected to the canonical home UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes; it loaded through the authenticated root redirect and displayed the Melody Studio header link
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: unversioned or prior protected Melody Studio cache keys
- Known caveats: the protected environment keeps score-image/catalog import disabled; this does not affect the tested phrase, staff, or audio workflows

## Smoke result

PASS.

- Protected event card began at `Note 1 of 8 · G4 · String 8 · Fret 15 · Open`.
- Next advanced it to `Note 2 of 8 · A4 · String 7 · Fret 15 · Open` and updated the fretboard.
- Octave colors began off with no visible legend; enabling the control revealed the adjacent 2–6 legend and fretboard overlay.
- Route order in the result DOM was fretboard, arrangement choices, then tab.
- The melody-only result did not show Play chord backing.
- API fallback status: loopback `/api/version` passed; it is not browser smoke.

## Integration notes

The protected runtime was refreshed without accepting or storing administrator credentials. The attempted system helper was stopped at its password prompt; only the user-owned listener was then terminated.

## Risk assessment

Low. This lane performed a documented listener refresh and read-only protected verification. Rollback is the implementation commit.

## Human decision needed

No. User smoke may continue at the exact URL above.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-2318-12-melody-lesson-focus-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All unrelated dirty and untracked corpus, source-inbox, private-data, generated-report, deployment, public/brand, `ui/brand/`, `Neon Sign/`, and parked documentation paths.

## Recommended next lane

User smoke. Any reported defect returns to the existing end-to-end Autopilot repair loop.

## Commit readiness

Safe to commit

## Suggested next step

Use the exact cache-busted protected URL and verify that the simplified navigator, route placement, optional octave map, and progressive rhythm controls feel clear in normal use.
