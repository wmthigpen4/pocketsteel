# Melody Studio Scientific-Octave Map Adjustment

## Task summary

During Melody Studio user smoke, the user reported that the scientific-octave guide had no visibility toggle, did not color the fretboard itself, and left the per-note octave controls feeling clunky. This adjustment:

- adds a default-on **Show/Hide octave map** control;
- renders scientifically accurate octave zones independently along every E9 string rather than implying that one vertical fret band represents one octave;
- color-matches exact note markers and lesson-step cards to the legend;
- replaces the three long register buttons with a compact per-note `− / Octave / +` stepper and a separate **Return to automatic** action;
- preserves top-melody octave labeling for harmony lesson steps while coloring every displayed harmony voice by its actual register;
- keeps the shared fretboard overlay opt-in, so Fretboard Explorer and other consumers are unchanged;
- adds a narrow-screen register layout that stays inside the phrase editor.

No API, arranger, tab, auth, corpus, source, deployment-policy, or shared default-fretboard behavior changed.

## Files changed

- `ui/pedal-steel-fretboard.js`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-0736-06-melody-scientific-octave-map-adjustment.md`

Created: this handoff only. Deleted files: none. Generated artifacts: none.

## Tests and checks

- `node --check ui/melody-workbench.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `PYTHONPATH=.:scripts .venv/bin/pytest -q tests/test_melody_workbench_ui.py tests/test_pedal_steel_fretboard_ui.py tests/test_frontend_answer_ui.py tests/test_same_origin_smoke_server.py` — 80 passed after the final mobile adjustment.
- `PYTHONPATH=.:scripts .venv/bin/pytest -q` — 922 passed after the final narrow-screen refinement.
- Scoped `git diff --check` — passed.
- Local UI request — HTTP 200.
- Local `/api/version` — `35447a2`, feature flag `melodyExercise=true`.
- Local interactive browser smoke — passed:
  - a `5 6 1` phrase resolved as `D4 E4 G4`;
  - raising only the third note produced `D4 E4 G5` and changed the register readout to `Octave 5 · +1 octave`;
  - the generated single-note route rendered 30 per-string octave zones and exact marker octave metadata;
  - the octave-map toggle hid/restored the overlay, guide, and event accents;
  - the active G5 marker and card used the octave-5 amber color;
  - on the recommended harmony route, the G5 top voice remained octave 5 while its supporting string was correctly tagged octave 4;
  - no `[object Object]` text was present.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8898/ui/melody-workbench.html?access=beta_user&v=octave-map-local-20260711`
- Cache-busted URL tested: `http://127.0.0.1:8898/ui/melody-workbench.html?access=beta_user&v=octave-map-local-20260711`
- Exact URL the user should use: pending protected-preview commit/restart/smoke
- Auth required: no
- Auth provider: local scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8898`
- Expected backend port: 8898
- Expected git HEAD: `35447a2` before the scoped implementation commit
- Version endpoint: `http://127.0.0.1:8898/api/version`
- Version endpoint result: HTTP 200, `git_sha=35447a2`, `features.melodyExercise=true`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not tested in local feature smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not retested in local feature smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: do not use the local URL for user smoke after the local server stops
- Known caveats: the color lanes model the unpedaled open-string fret path; pedal/lever event markers use the exact mechanically adjusted pitch and therefore remain accurate at octave boundaries.

## Integration notes

`showScientificOctaveOverlay` is a new optional shared-fretboard rendering option and defaults to `false`. Melody Studio supplies standard E9 open pitches and per-position `scientificOctavesByString`; no existing consumer is opted in implicitly. The overlay is string-aware because a single fret contains multiple registers.

## Risk assessment

Low to medium. The shared component gained optional rendering code, but its default output is unchanged and focused shared-component tests prove the overlay is absent unless requested. Rollback is the scoped implementation commit.

## Human decision needed

No. This is a user-smoke adjustment already authorized for the autopilot repair loop.

## Safe-to-stage exact file list

- `ui/pedal-steel-fretboard.js`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-0736-06-melody-scientific-octave-map-adjustment.md`

## Files that must not be staged

All other dirty or untracked files, especially corpus/source metadata, raw or private data, `source-inbox`, brand/design media, `public/`, `Neon Sign/`, deployment assets/configuration, and unrelated handoffs.

## Recommended next lane

Lane 01 Repo Steward for exact-path staging and the scoped implementation commit, followed by Lane 12 protected-preview restart and authenticated smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval: stage only the seven exact files above, review the cached diff, commit the adjustment, restart the documented protected preview, verify the new HEAD through `/api/version`, run authenticated browser smoke at one cache-busted Melody Studio URL, and refresh `integration-status.md` separately.
