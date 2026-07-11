# Melody audio transcription protected smoke

## Task summary

Refreshed the protected preview to implementation commit `cfe4720` and completed the automatable authenticated browser smoke for Melody Studio short-phrase audio transcription.

The protected workspace now presents one unified **Record or upload audio** entry with microphone capture, 15-second audio-file input, an explicit tempo grid, review-first language, supported audio formats, and a visible session-only/no-upload privacy boundary.

Real microphone permission and host file selection are intentionally reserved for user smoke because browser automation cannot authorize or select those device resources.

## Files changed

- `docs/handoffs/task-completions/2026-07-11-1707-12-melody-audio-transcription-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

No runtime code, auth policy, deployment configuration, corpus, sources, private data, or generated assets were changed in this phase.

## Tests and checks

- Focused Melody/backend/same-origin suite: `38 passed`.
- Full pytest after final implementation changes: `935 passed in 37.78s`.
- Core JavaScript syntax checks: pass.
- Exact-path `git diff --check`: pass.
- Loopback `/api/version`: `cfe4720`, branch `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, and `features.melodyExercise=true`.
- Loopback `/`: `302` to `/ui/steel-guitar-rag-mock.html`.
- Loopback home, versioned Studio, and versioned controller asset: `200`.
- Anonymous loopback `/api/answer`: expected `401`; API fallback is not browser smoke.
- Authenticated protected browser workspace smoke: pass.

Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-audio-transcription-cfe4720-20260711`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-audio-transcription-cfe4720-20260711`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-audio-transcription-cfe4720-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `cfe4720`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `cfe4720`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; redirects to canonical home
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex and the user
- Do not test these URLs: unversioned Studio URL; API fallback as a substitute for browser behavior
- Known caveats: browser automation cannot grant microphone permission or select a host audio file; import/catalog server flag remains intentionally off

Authenticated browser assertions:

- Record or upload audio is visible and selected.
- The workspace exposes approximate tempo, Start listening, Stop and review, audio file selection, and Transcribe file and review.
- The file picker advertises WAV, MP3, M4A, AAC, and OGG support.
- The exact controller asset is `melody-audio-transcription-20260711-2`.
- The page states that audio is decoded in the browser, not uploaded, and released after transcription.
- Horizontal overflow was zero and `[object Object]` was absent.

The deterministic suite separately proves the pitch/rhythm/confidence pipeline and backend approximate-accuracy contract; API fallback is not reported as browser smoke.

## Integration notes

- Runtime refresh terminated only the user-owned port-8770 listener; the installed LaunchDaemon restarted at committed HEAD.
- No privileged file or service configuration changed.
- The user-smoke target is one short monophonic phrase, using either microphone or an audio file, followed by one manual note correction and E9 arrangement.

## Risk assessment

Medium. The protected UI and deterministic logic are verified, but microphone and codec behavior must be tested on the user's actual browser/device.

## Human decision needed

No product decision. User smoke is now required for real audio capture or file selection.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-1707-12-melody-audio-transcription-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All other dirty or untracked paths, especially corpus/source-inbox, private-data, vector/Chroma, scraping, public/brand/design, deployment, environment, secret, and generated-report files.

## Recommended next lane

Lane 06 user smoke; any observed defect returns to the scoped autopilot repair loop.

## Commit readiness

Safe to commit

## Suggested next step

Use the exact protected URL to transcribe one short monophonic phrase, correct one estimated note or duration, and arrange it for E9.
