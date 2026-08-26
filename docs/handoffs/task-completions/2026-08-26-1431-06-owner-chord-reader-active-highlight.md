# Lane 06 — Owner chord-reader active highlight

## Task summary

Made the currently playing chord card unmistakable from mobile/tablet guitar
distance. The timeline updater was already moving the active class at each exact
transition, but the old active treatment was only a one-pixel blue border and a
10% blue tint; the gold confidence edge visually competed with it. The active
card now uses a solid light-blue fill, dark chord text, a bright multi-ring edge,
a small scale lift, and an explicit `NOW` marker. It also exposes
`aria-current="true"` for assistive-state verification.

No model, prediction, timing, rhythm, or audio behavior changed.

## Files changed

- `ui/chord-reader-owner-test/index.html`
- `ui/chord-reader-owner-test/owner-test.css`
- `ui/chord-reader-owner-test/owner-test.js`
- `tests/test_owner_chord_reader_ui.py`
- this handoff

## Tests and checks

- `node --check ui/chord-reader-owner-test/owner-test.js` — PASS
- `node --test tests/owner_chord_reader_timing.test.js` — PASS, 2 tests
- `.venv/bin/python -m pytest -q tests/test_owner_chord_reader_ui.py` — PASS, 3 tests
- `git diff --check` — PASS
- Browser transition smoke — PASS: active Change 3 at 18.023 seconds changed
  to active Change 4 after the 19.400-second boundary
- Active computed style — PASS: solid `rgb(145, 207, 255)` background,
  high-contrast border, and `aria-current="true"`

## Risks

- The first modeled chord still legitimately spans 0:00.4–0:18.0, so it remains
  highlighted for almost eighteen seconds before the first predicted change.
- Stronger highlighting improves visibility but does not change model accuracy.

## Human decision needed

None for the local fix. The owner should confirm visibility at normal guitar
distance before the separate publishing scope.

## Safe-to-stage exact file list

- `ui/chord-reader-owner-test/index.html`
- `ui/chord-reader-owner-test/owner-test.css`
- `ui/chord-reader-owner-test/owner-test.js`
- `tests/test_owner_chord_reader_ui.py`
- `docs/handoffs/task-completions/2026-08-26-1431-06-owner-chord-reader-active-highlight.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `ui/chord-reader-owner-test/local-data/`
- all unrelated, generated, audio, model, private, cache, and corpus files

## Recommended next lane

Lane 06 owner listening smoke, followed by the previously described private
deployment design only after the user approves that separate scope.

## Commit readiness

Ready for an exact-path commit of the five listed files.
