# Melody Studio route-to-score synchronization protected smoke

## Task summary

Refreshed the protected runtime at implementation commit `a54e5c5` and verified through authenticated Cloudflare Access browser smoke that the musical score now changes with the selected arrangement route. The installed LaunchDaemon respawned the service after only the user-owned port-8770 listener was terminated; no administrator credential was requested or stored.

## Files changed

- this handoff
- `docs/handoffs/task-completions/integration-status.md` (separate coordination refresh)

No runtime implementation, auth, DNS, Tunnel, secrets, corpus, private-data, source, or deployment-policy files changed during this lane.

## Tests and checks

- Implementation commit: `a54e5c5 Sync Melody Studio score with arrangement routes`
- Loopback `/api/version`: `a54e5c5`, branch `feature/answer-api`, `features.melodyExercise=true`
- Authenticated Cloudflare Access browser load: pass
- Protected `1 2 3 5` arrangement: pass
- Faithful melody: one staff note head per event
- Recommended harmony: two staff note heads per event
- Chord melody: three staff note heads per event
- Fretboard, tab, route selection, staff labels, and staff note heads synchronized: pass
- VexFlow 5.0.0 renderer: pass
- `[object Object]`: absent
- Browser warnings/errors: none
- Authenticated root redirect and canonical home UI: pass
- Anonymous protected root: HTTP 302 to Cloudflare Access, expected

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-route-score-a54e5c5-20260711`
- Cache-busted URL tested: same as above
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-route-score-a54e5c5-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `a54e5c5`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `a54e5c5`, expected branch, auth provider, retrieval mode, and Melody Exercise feature
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; authenticated root redirected to the canonical home UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes; the canonical home UI loaded with the Melody Studio link
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: unversioned or earlier protected Melody Studio cache keys
- Known caveats: staff pitch content is synchronized; this fix does not change how the browser synthesizer plays a grip

## Smoke result

PASS.

- Faithful labels: `G4`, `A4`, `B4`, `D5`.
- Recommended harmony labels: `B3, G4`; `F#4, A4`; `G4, B4`; `F#4, D5`.
- Chord melody labels: `B3, E4, G4`; `D4, F#4, A4`; `E4, G4, B4`; `F#4, A4, D5`.
- Every chord-melody event retained the original resolved melody as its highest pitch.
- API fallback status: loopback `/api/version` passed; it is not browser smoke.

## Integration notes

The result score now consumes the same validated route event pitches as the fretboard and tab. Existing single-note score behavior remains unchanged.

## Risk assessment

Low. The protected browser verified all three score textures and the complete 935-test suite passed before commit.

## Human decision needed

No. User smoke may continue at the exact URL above.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-2329-12-melody-route-score-sync-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All unrelated dirty and untracked corpus, source-inbox, private-data, generated-report, deployment, public/brand, `ui/brand/`, `Neon Sign/`, and parked documentation paths.

## Recommended next lane

User smoke. Any reported defect returns to the existing end-to-end Autopilot repair loop.

## Commit readiness

Safe to commit

## Suggested next step

Use the exact cache-busted URL, enter a short phrase, and switch between Faithful melody, Recommended harmony, and Chord melody while watching the staff, fretboard, and tab change together.
