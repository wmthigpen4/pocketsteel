# Melody Studio arranger protected-preview smoke

## Task summary

Completed authenticated protected-preview smoke for the octave-aware Melody Studio arranger after the asset-cache follow-up. Runtime and browser behavior match commit `338a890`. User smoke may begin.

## Files changed

- `docs/handoffs/task-completions/2026-07-10-1435-12-melody-arranger-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

No implementation files changed during this final smoke.

## Tests and checks

- Full pytest before implementation commit: 918 passed.
- Cache-fix focused frontend/same-origin suite: 41 passed.
- Core JavaScript syntax checks: passed.
- Loopback `/api/version`: `338a890`, `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, `features.melodyExercise=true`.
- Authenticated protected browser smoke: passed.
- Loopback root: 302 to `/ui/steel-guitar-rag-mock.html`.
- Home UI: 200.
- Melody Studio: 200.
- Anonymous API fallback: 401 as expected. This API check is not browser smoke.

## Protected browser results

- Cloudflare Access authenticated state loaded the feature-enabled Studio.
- `5 6 1 3 2 1 3` previewed as `D4 E4 G4 B4 A4 G4 B4`.
- Lesson exposed single note, Recommended Harmony, thirds, sixths, and chord melody.
- Recommended Harmony rendered seven two-note events and a matching multi-string tab.
- Route selection visibly updated the pressed route, active event, active tab label, selected fretboard event, and explanation.
- Literal `S4: 3 2F 7` previewed as `G4 G4 B4` and rendered exactly as string 4, frets 3/2F/7.
- No `[object Object]`, no `Steel Guitar RAG`, and no image background.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-arranger-338a890-20260710`
- Cache-busted URL tested: same as above
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-arranger-338a890-20260710`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `338a890`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: matched `338a890` with the expected branch/auth/feature state
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; 302 to home UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes; 200 loopback and protected session already authenticated
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: stale URLs ending in `4a00fc2`, `6f95e9f`, or `ce20ddf`
- Known caveats: G/C major and standard E9 only; audio/link transcription remains out of scope

## Preview restart result

The installed LaunchDaemon supervised a port-8770 process owned by the local user. Terminating only that listener caused launchd to restart it at the committed checkout without `sudo`; `/api/version` confirmed the new SHA. This is the safe narrow restart path for future committed preview refreshes while the process ownership remains unchanged.

## Risk assessment

Medium feature risk, low deployment risk. Arranger behavior is feature-flagged, mechanically validated, full-suite green, and now browser-verified behind Access.

## Human decision needed

No. User smoke can continue.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-10-1435-12-melody-arranger-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All other dirty/untracked paths.

## Recommended next lane

01 Repo Steward docs-only exact-path commit, then user smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the two coordination docs and ask the user to test closest contour, Recommended Harmony, an octave override, and literal tab at the exact protected URL.
