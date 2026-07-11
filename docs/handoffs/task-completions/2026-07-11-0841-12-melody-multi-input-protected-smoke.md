# Melody Studio multi-input protected-preview smoke

## Task summary

Restarted the installed protected-preview app service from committed implementation `b0944c7` and completed authenticated browser smoke for the six-input Melody Studio and lead-sheet builder.

The prior `re`/arranger blocker is closed. No auth, DNS, Tunnel, Cloudflare Access, secret, corpus, Chroma, scraping, source-inbox, private-data, brand, or deployment-policy configuration changed. The current protected environment does not set `STEEL_RAG_ENABLE_MELODY_IMPORT`, so the default-off catalog/import endpoint remains disabled there as designed. Local authenticated smoke with that flag enabled already passed and is recorded in the implementation handoff.

## Files changed

- `docs/handoffs/task-completions/2026-07-11-0841-12-melody-multi-input-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

Deleted files: none. Generated artifacts: none.

## Tests and checks

- Implementation commit: `b0944c7 Build Melody Studio multi-input score workflow`.
- Full pytest before commit: `933 passed`.
- Focused final melody/API/UI/import tests: `39 passed, 300 deselected`.
- JavaScript syntax: passed for answer client, score module, and Melody Studio controller.
- Protected listener restart: passed by terminating only the user-owned port-8770 listener and allowing the installed LaunchDaemon to restart it; `sudo` restart was not used after it requested a password.
- Loopback `/api/version`: HTTP 200, `git_sha=b0944c7`, branch `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, `melodyExercise=true`.
- Loopback root: HTTP 302 to the canonical home UI.
- Loopback canonical home: HTTP 200.
- Loopback Melody Studio: HTTP 200.
- Loopback local VexFlow 5 bundle: HTTP 200.
- Loopback catalog endpoint: HTTP 404, expected because the default-off import flag is not enabled in protected-preview configuration.
- Cloudflare Access browser authentication: succeeded.
- Protected browser smoke: pass.

Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-multi-input-b0944c7-20260711`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-multi-input-b0944c7-20260711`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-multi-input-b0944c7-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `b0944c7`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: HTTP 200, `git_sha=b0944c7`, expected branch/retrieval/auth mode, `melodyExercise=true`; `melodyImport` absent/default off
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; authenticated navigation redirected to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: production; unversioned Studio route; external upload destinations
- Known caveats: protected catalog/image/MusicXML/MIDI import stays unavailable until a separately approved protected-environment flag change; image recognition additionally requires the configured local vision model

## Smoke result

PASS for the protected feature surface currently enabled.

Verified in the authenticated browser:

- all six input cards render and the existing **Enter notes or intervals** workflow remains the default;
- a manual eight-note Amazing Grace phrase builds successfully with exact E9 positions D4 S5/F3, G4 S4/F3, B4 S3/F3, A4 S1/F3, and E4 S5/F3+A;
- Faithful melody, Vocal steel, Recommended harmony, thirds, sixths, and chord-melody routes appear together;
- the result score uses the locally served `vexflow-5.0.0` renderer;
- staff, fretboard, note navigator, and tab stay synchronized;
- the score builder adds and edits notes, displays two events, has no rhythm warnings, uses VexFlow, and arranges to a synchronized E9 result;
- page-level horizontal overflow is absent;
- no `[object Object]` text or browser console errors appeared;
- **Pick a song** shows the correct disabled-state message because `melodyImport` is not enabled in the protected environment;
- protected root and canonical home routes load successfully.

API fallback was not used as a substitute for browser smoke. Loopback checks were only freshness and route evidence.

## Integration notes

- The protected runtime now serves the fixed arranger and multi-input UI at `b0944c7`.
- `STEEL_RAG_ENABLE_MELODY_IMPORT` remains default off. Enabling catalog/upload imports in protected preview requires a separate explicit environment/secrets authorization.
- User smoke may continue on manual phrase entry, score creation, microphone capture, and recording/reference companion behavior. The protected catalog/upload card correctly reports that its server import feature is not enabled.

## Risk assessment

Low for the enabled protected surface after browser verification. Medium residual risk remains for browser microphone variation and the not-yet-enabled protected import path. Rollback is implementation commit `b0944c7`, or leave `STEEL_RAG_ENABLE_MELODY_IMPORT` off.

## Human decision needed

No for user smoke of the enabled protected surface. Yes only if protected-preview catalog/upload import should be enabled: explicitly authorize the environment flag change and local vision-model readiness check.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-0841-12-melody-multi-input-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All other dirty/untracked paths, especially corpus/source-inbox, private-data, vector/Chroma, scraping, public/brand/design, deployment, environment, and secrets files.

## Recommended next lane

User smoke on the exact protected URL. Any observed defect returns to the scoped Autopilot bug-fix loop.

## Commit readiness

Safe to commit

## Suggested next step

Test manual note/interval entry and **Build a score** at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-multi-input-b0944c7-20260711`. If protected imports are desired next, explicitly authorize only the `STEEL_RAG_ENABLE_MELODY_IMPORT=true` protected-environment change; do not change DNS, Access policy, Tunnel, or secrets otherwise.
