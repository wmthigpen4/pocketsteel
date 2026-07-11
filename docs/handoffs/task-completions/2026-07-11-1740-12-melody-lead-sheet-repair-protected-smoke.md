# Melody lead-sheet repair protected smoke

## Task summary

Refreshed the protected preview to implementation commit `2469975` and completed authenticated browser smoke for the user-reported lead-sheet/audio-window repair.

Protected smoke reproduced the previously inert case with an intentionally overfull 4/4 score. The warning remained visible, note selection was explicit and navigable, Arrange for E9 remained enabled, and the workflow advanced to all six E9 routes with fretboard and tab.

The protected audio workspace also exposes playback and 5/10/15-second window selection for longer files, eliminating the need to locate or pre-edit a 15-second MP3.

## Files changed

- `docs/handoffs/task-completions/2026-07-11-1740-12-melody-lead-sheet-repair-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

No runtime code, auth policy, deployment configuration, corpus, sources, private data, or generated assets were changed in this phase.

## Tests and checks

- Focused Melody/backend/same-origin suite: `38 passed`.
- Full pytest: `935 passed in 39.08s`.
- Core JavaScript syntax checks: pass.
- Exact-path `git diff --check`: pass.
- Loopback `/api/version`: `2469975`, branch `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, and `features.melodyExercise=true`.
- Loopback `/`: `302` to `/ui/steel-guitar-rag-mock.html`.
- Loopback home, versioned Studio, and versioned controller asset: `200`.
- Anonymous loopback `/api/answer`: expected `401`; API fallback is not browser smoke.
- Authenticated protected browser smoke: pass.

Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-lead-sheet-repair-2469975-20260711`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-lead-sheet-repair-2469975-20260711`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-lead-sheet-repair-2469975-20260711`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: `2469975`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `2469975`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; redirects to canonical home
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex and the user
- Do not test these URLs: unversioned Studio URL; API fallback as a substitute for browser behavior
- Known caveats: automated browser smoke cannot select the user's local MP3; real-file window selection remains the user-smoke boundary

Authenticated browser assertions:

- An overfull 5-beat 4/4 score displayed its warning while Arrange for E9 remained enabled.
- A4 showed as `Selected note 2 of 2 · A4 · measure 1, beat 2` and was the sole `aria-current` staff event.
- Previous note changed the selection bar and `aria-current` to G4 note 1.
- Arrange for E9 advanced to a visible result with Faithful melody, Vocal steel, Recommended harmony, thirds, sixths, and Chord melody.
- Fretboard and tab were present after arrangement.
- The audio panel showed longer-file guidance, 5/10/15-second choices, timecode start, Use current playhead, and Transcribe selected window.
- The final controller asset was loaded; horizontal overflow was zero and `[object Object]` was absent.

## Integration notes

- Runtime refresh terminated only the user-owned port-8770 listener; the installed LaunchDaemon restarted at committed HEAD.
- No privileged file or service configuration changed.
- API fallback remained unauthenticated by design and is not counted as browser smoke.

## Risk assessment

Low to medium. The selection and arrangement defects are directly verified as closed. Real long-file decoding and playhead selection still depend on the user's browser/codec and require user smoke.

## Human decision needed

No. The user should retry the longer MP3 workflow at the exact URL.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-11-1740-12-melody-lead-sheet-repair-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files that must not be staged

All other dirty or untracked paths, especially corpus/source-inbox, private-data, vector/Chroma, scraping, public/brand/design, deployment, environment, secret, and generated-report files.

## Recommended next lane

Lane 06 user smoke; any observed defect returns to the scoped autopilot repair loop.

## Commit readiness

Safe to commit

## Suggested next step

Retry the original longer MP3, select the desired window, edit notes with the selection bar, and confirm arrangement advances.
