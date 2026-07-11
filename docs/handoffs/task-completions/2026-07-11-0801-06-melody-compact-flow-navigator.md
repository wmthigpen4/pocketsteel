# Melody Studio Compact Entry Flow and Note Navigator

## Task summary

Implemented both approved Melody Studio user-smoke recommendations:

1. Removed the four-card Step 1 gate and opened directly into the phrase builder with three compact starting points: **Enter my phrase**, **A song or recording**, and **Give me an exercise**.
2. Replaced the scattered octave legend, navigation buttons, event cards, current-note card, event explanation, and active-tab sentence with one compact note navigator beneath the fretboard.

The recording starting point reveals source fields plus a meaningful treatment choice between **Faithful solo passage** (`artist_solo_lesson`) and **Playable E9 arrangement** (`song_arrangement_lesson`). The exercise starting point reveals practice presets. Source fields clear when switching back to either source-free path. Existing API request kinds, arranger behavior, source attribution, route switching, exactness labels, section continuation, and feature gating remain intact.

The note navigator now contains the Octave colors toggle and legend, note progress, adjacent previous/next arrows, concise steel-player position pills such as `G5 · S3+5 · F10 · B+A`, and one current-note readout. The redundant visible active-tab line and verbose event-detail sentence were removed.

No backend, API, auth, corpus, source, private-data, scraper, vector, deployment-policy, brand-asset, or shared-fretboard behavior changed.

## Lane classification

- Primary lane: 06 UX/UI Design.
- Supporting lanes: 15 QA, 01 Repo Steward, and 12 Self-Hosted Deployment.
- Mode: explicitly approved Autopilot user-smoke adjustment.

## Files changed

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-11-0801-06-melody-compact-flow-navigator.md`

Deleted files: none. Generated artifacts: none.

## Tests and checks

- `node --check ui/melody-workbench.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- Focused Melody Studio, shared-fretboard, frontend, and same-origin suite — 80 passed.
- Full `PYTHONPATH=.:scripts .venv/bin/pytest -q` — 922 passed.
- Scoped `git diff --check` — passed.
- Local Melody Studio request — HTTP 200.
- Local `/api/version` — `b516204`, branch `feature/answer-api`, feature flag enabled.

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8898/ui/melody-workbench.html?access=beta_user&v=compact-flow-local-20260711`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending protected-preview commit/restart/smoke
- Auth required: no
- Auth provider: local scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8898`
- Expected backend port: 8898
- Expected git HEAD: pre-commit working tree based on `b516204`
- Version endpoint: `http://127.0.0.1:8898/api/version`
- Version endpoint result: HTTP 200, `git_sha=b516204`, `features.melodyExercise=true`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not exercised in this focused local smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not retested in this focused local smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: do not use the local URL for user smoke after the local server stops
- Known caveats: protected-preview auth and cache delivery still require Lane 12 verification; API fallback is not browser smoke.

Browser results:

- Initial load opened directly on **Enter my phrase** with no Step 1 gate.
- **A song or recording** revealed source fields and the faithful/adapted treatment selector.
- Selecting faithful treatment, adding artist/song metadata, then switching to **Give me an exercise** cleared source state and revealed only the practice presets.
- **Start over** returned to a blank direct phrase-entry state.
- A faithful-solo phrase produced the source-backed lesson title, approximate label, and source identity expected from the unchanged request contract.
- The compact navigator rendered no active-tab sentence or verbose event-detail sentence.
- Previous/next, pill selection, and route switching updated note progress, current-note text, and the selected `renderablePositionId` in the fretboard.
- Recommended harmony displayed concise multi-string pills and preserved the exact harmony marker octaves.
- Octave colors hid/restored the overlay and legend without changing note selection.
- The navigator kept the Next arrow nine pixels after the last pill for a three-note phrase instead of pushing it to the far edge.
- Page-level horizontal overflow was zero.
- No browser console errors or `[object Object]` text appeared.

## Integration notes

The four backend request kinds remain canonical. The three frontend starting points are a simpler view over them: phrase maps to `user_melody`, exercise maps to `original_exercise`, and recording exposes the two source-based kinds as a treatment selector. `createInitialState()` now defaults to `user_melody`, so the enabled workspace can render the editor immediately.

## Risk assessment

Medium because the primary Melody Studio entry flow and lesson navigation changed. Risk is bounded to the dedicated feature-gated workspace; API contracts and shared components are unchanged. Rollback is the scoped implementation commit.

## Human decision needed

No. The user explicitly approved both recommendations for implementation and protected-preview delivery.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-11-0801-06-melody-compact-flow-navigator.md`

## Files that must not be staged

Every other dirty or untracked file, especially corpus/source metadata, raw or private data, source-inbox files, brand/design media, `public/`, `Neon Sign/`, deployment assets/configuration, and unrelated handoffs.

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 12 protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval: stage only the six exact paths above, review the cached diff, commit the compact flow, refresh the supervised preview, verify `/api/version`, and exercise all three starting points plus note navigation at one cache-busted protected URL.
