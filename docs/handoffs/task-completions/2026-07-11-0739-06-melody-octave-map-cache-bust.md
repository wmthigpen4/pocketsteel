# Melody Studio Octave-Map Asset Cache Bust

## Task summary

Protected smoke of implementation commit `35f36bc` found current HTML paired with an earlier cached Melody Studio script. The protected phrase chips rendered, but the new register stepper retained its static fallback labels instead of updating to `Octave 4 · Automatic` and exact per-note raise/lower labels. Loopback inspection confirmed that the installed runtime held the correct JavaScript.

Assigned a fresh cache key to the three Melody Studio script URLs and updated the two exact cache-key assertions. No runtime behavior, API, auth, corpus, source, or deployment policy changed.

## Files changed

- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-0739-06-melody-octave-map-cache-bust.md`

Deleted files: none. Generated artifacts: none.

## Tests and checks

- JavaScript syntax checks for Melody Studio and the shared fretboard — passed.
- Focused Melody Studio, shared-fretboard, and same-origin tests — 54 passed.
- Scoped `git diff --check` — passed.
- The immediately preceding implementation commit passed the full suite: 922 tests.

## Integration notes

The new cache key is `melody-octave-map-35f36bc-20260711`. Protected preview must be refreshed to the follow-up commit and the interaction smoke repeated at a new page URL.

## Risk assessment

Low. This changes only asset query strings. Rollback is the cache-bust follow-up commit.

## Human decision needed

No. This is a protected-smoke blocker inside the approved autopilot adjustment.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-0739-06-melody-octave-map-cache-bust.md`

## Files that must not be staged

Every other dirty or untracked file, especially corpus/source metadata, private/raw data, source-inbox files, brand/design media, public assets, deployment configuration, and unrelated handoffs.

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 protected-preview restart and repeated authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit these four exact files, refresh the supervised runtime, verify `/api/version`, and confirm the protected register stepper, board overlay, toggle, and matching marker colors before user handoff.
