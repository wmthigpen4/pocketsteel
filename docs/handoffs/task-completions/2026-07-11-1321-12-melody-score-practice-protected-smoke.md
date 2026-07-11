# Melody Studio score-practice protected-preview smoke

## Task summary

Refreshed the installed protected preview to implementation `74520ca` and completed authenticated browser smoke for the Melody Studio score-practice and chord-aware arranger upgrade.

The repeated-B score bug is closed in the protected build. Melody-only input produces no staff chord annotations. A real G chord entered through Build a score renders once at the actual change, survives arrangement, and informs the route recommendation and validated grip ranking.

No auth, DNS, Tunnel, Cloudflare Access, secret, corpus, Chroma, scraping, source-inbox, private-data, brand, or deployment-policy configuration changed. The protected import/catalog feature remains default off.

## Files changed

- `docs/handoffs/task-completions/2026-07-11-1321-12-melody-score-practice-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

Deleted files: none. Generated artifacts: none.

## Tests and checks

- Implementation commit: `74520ca Expand Melody Studio score practice`.
- Final focused Melody/same-origin suite: `37 passed`.
- Full pytest: `934 passed in 38.19s`.
- Core JavaScript syntax checks: passed.
- Protected refresh: passed by terminating only the user-owned port-8770 listener and allowing the installed LaunchDaemon to restart it.
- Loopback `/api/version`: HTTP 200, `git_sha=74520ca`, branch `feature/answer-api`, retrieval `hybrid_private_first`, auth `cloudflare_access`, `features.melodyExercise=true`.
- Loopback root: HTTP 302 to `/ui/steel-guitar-rag-mock.html`.
- Loopback canonical home, Melody Studio, score script, and workbench script: HTTP 200.
- Anonymous loopback answer: HTTP 401.
- Anonymous public root: HTTP 302 to Cloudflare Access.
- Cloudflare Access browser authentication: succeeded.
- Protected browser smoke: passed.
- Browser warning/error logs: empty.
- Page-level horizontal overflow: zero.
- `[object Object]`: absent.

Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-score-practice-74520ca-20260711`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-score-practice-74520ca-20260711`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-score-practice-74520ca-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `74520ca`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: HTTP 200, `git_sha=74520ca` with expected branch, retrieval, auth, and Melody feature state
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; authenticated navigation redirected to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: production; unversioned Studio route; external upload destinations
- Known caveats: score playback uses a deliberately simple browser synthesizer whose tone varies by device; protected import/catalog remains unavailable until separately authorized through the existing environment flag

API fallback was not used as a substitute for browser smoke. Loopback checks supplied only service freshness, route, asset, and auth-boundary evidence.

## Smoke result

PASS.

Authenticated protected browser verification covered:

- `5 6 1 3 2 1 3` renders D4, E4, G4, B4, A4, G4, B4 with zero chord annotations;
- the result uses `vexflow-5.0.0`, displays the G key signature, and exposes all six arrangement routes;
- selecting and playing from G4 advanced the staff, current-note readout, and navigator together to B4;
- Pause changed to Resume without losing the selected note;
- selected-note loop controls reported `Looping notes 4–7` and no duplicate DOM IDs exist;
- a real G chord renders exactly once and the route states `Chord-aware ranking used: G`;
- Chord melody selection displayed strings 4+5+6 at fret 3, selected the matching fretboard position, and rendered a tab chord row with one G change rather than repeated note-name labels;
- authenticated root navigation reached the canonical home UI;
- no console warnings/errors, object-string rendering, or page overflow appeared.

## Integration notes

The protected runtime is ready for user smoke of the complete score-practice slice. The current exact URL must be used so the new score/workbench asset keys are loaded.

## Risk assessment

Low after protected browser verification. Residual variation is limited to browser/device audio tone and timing; the visual and deterministic arrangement contracts are verified.

## Human decision needed

No implementation decision. User smoke is now required.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-1321-12-melody-score-practice-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All other dirty or untracked paths, especially corpus/source-inbox, private-data, vector/Chroma, scraping, public/brand/design, deployment, environment, secret, and generated-report files.

## Recommended next lane

User smoke on the exact protected URL. Any observed defect returns to the end-to-end Autopilot bug-fix loop.

## Commit readiness

Safe to commit

## Suggested next step

User smoke the score-practice controls, chord entry, and at least one harmony route at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-score-practice-74520ca-20260711`.
