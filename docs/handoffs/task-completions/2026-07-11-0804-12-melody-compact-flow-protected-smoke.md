# Melody Studio Compact Flow Protected Smoke

## Task summary

Verified implementation commit `62a8a3d` on the authenticated protected preview. Melody Studio now opens directly into a compact three-choice phrase workspace and presents one compact note navigator beneath the fretboard.

No auth, DNS, Tunnel, corpus, source, private-data, scraper, vector, brand-asset, or deployment-policy configuration changed. The installed LaunchDaemon refreshed the current runtime after the prior user-owned port-8770 listener was terminated.

## Files changed

- `docs/handoffs/task-completions/2026-07-11-0804-12-melody-compact-flow-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

Deleted files: none. Generated artifacts: none.

## Tests and checks

- Implementation commit: `62a8a3d Simplify Melody Studio flow and navigator`.
- Full pytest: 922 passed.
- Focused Melody Studio/shared-fretboard/frontend/same-origin suite: 80 passed.
- Core JavaScript syntax checks: passed.
- Loopback `/api/version`: `62a8a3d`, branch `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, `features.melodyExercise=true`.
- Cloudflare Access authenticated browser smoke: passed at the exact Melody Studio target.
- Protected root and canonical home-route browser checks: loaded successfully.
- Anonymous protected root request: HTTP 302 to Cloudflare Access, as expected.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-compact-flow-62a8a3d-20260711`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-compact-flow-62a8a3d-20260711`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-compact-flow-62a8a3d-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded for the direct Melody Studio target
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `62a8a3d`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: HTTP 200, `git_sha=62a8a3d`, expected branch, retrieval/auth modes, and Melody feature flag
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; authenticated browser navigation redirected to the home application
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes; the canonical route loaded in the authenticated browser environment
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: earlier octave-map URLs or the unversioned Studio route
- Known caveats: loopback version/API evidence is not browser smoke. The per-string octave overlay continues to represent the unpedaled fret path while exact pedal/lever event markers use mechanically adjusted pitches.

## Smoke result

PASS. Protected browser verification proved:

- the page opens directly on **Enter my phrase** without a Step 1 gate;
- **A song or recording** reveals source fields plus **Faithful solo passage** and **Playable E9 arrangement**;
- switching from a populated faithful-solo path to **Give me an exercise** clears artist/song state and reveals practice presets;
- returning to **Enter my phrase** hides both source fields and exercise presets;
- `5 6 1` with only event 3 raised produced `D4`, `E4`, `G5`;
- the compact navigator shows Octave colors, octave legend, `Note N of N`, concise pitch/position pills, adjacent arrows, and one current-note readout;
- the Next arrow stayed nine pixels after the final pill for the three-note phrase rather than floating at the far edge;
- the visible active-tab sentence and verbose event-detail sentence are absent;
- Next, pill selection, and Recommended harmony updated the selected pill, current-note line, exact fretboard `renderablePositionId`, and tab route together;
- octave hide/show behavior remained functional;
- G5 harmony retained octave 5 for the top voice while its supporting string marker used octave 4;
- page-level horizontal overflow was zero;
- no browser console errors or `[object Object]` text appeared.

## Integration notes

The API still receives the same four request kinds. The three starting points are a frontend simplification: phrase maps to `user_melody`, exercise maps to `original_exercise`, and recording exposes the two source-based request kinds through its treatment selector.

## Risk assessment

Low after verification. The UI flow change is isolated to the feature-gated Melody Studio route; API and shared component contracts did not change. Rollback is commit `62a8a3d`.

## Human decision needed

No. User smoke may continue at the exact URL above.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-0804-12-melody-compact-flow-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All unrelated dirty and untracked corpus, source-inbox, private-data, brand/design, public asset, deployment, generated-report, and parked documentation paths.

## Recommended next lane

User smoke. Any observed defect returns to the approved end-to-end autopilot repair loop.

## Commit readiness

Safe to commit

## Suggested next step

Use the exact cache-busted protected URL and judge whether the direct entry flow and compact navigator now feel appropriately simple during normal practice.
