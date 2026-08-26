# Travis validation timing alignment correction

## Summary

This bounded Lane 06 correction addresses a reviewer-visible mismatch between
beat-aligned bars and chord changes. Highway 40 Blues exposed that a low-
confidence first-half chord was being discarded, causing the second-half chord
to be stretched across the entire bar and displayed almost a second early.

The UI now preserves a possible half-bar split when coverage supports the timing
but confidence is insufficient to call the harmony correct. It labels that
split for verification. During playback, each half is independently highlighted
and the Current chord readout changes at the half-bar boundary without waiting
for the next box.

An independent opening beat analysis placed the Highway grid 0.093 seconds later
than the original grid. That bounded calibration is stored in the private proof
bundle. Per-song Earlier, Later, and Reset controls permit 0.05-second reviewer
nudges; the chosen offset autosaves through the protected backend.

## Verification

- Highway Bar 2 renders `E / F#m`, labeled `possible half-bar split — verify`;
- Highway defaults to a measured `+0.09s` grid offset;
- Later changes the offset to `+0.14s`; Reset restores `+0.09s`;
- all 15 opening audits retained four beat markers per bar;
- no opening rendered more than two chord parts;
- TypeScript check passed;
- worker tests: 6 passed;
- focused UI tests: 3 passed;
- JavaScript syntax, Ruff, and `git diff --check` passed.

This remains a human-validation interface. The timing correction improves
alignment and exposes ambiguity; it does not establish the correct chord names.

## Safe-to-stage files

- `ui/chord-reader-travis-validation/index.html`
- `ui/chord-reader-travis-validation/validation.css`
- `ui/chord-reader-travis-validation/validation.js`
- `workers/chord-reader-validation/src/validation.ts`
- `workers/chord-reader-validation/tests/index.test.ts`
- `tests/test_travis_validation_ui.py`
- `scripts/apply_travis_validation_timing_calibration.py`
- this handoff

## Never stage

- `docs/handoffs/task-completions/integration-status.md`
- `ui/chord-reader-travis-validation/local-data/`
- private audio, generated proof data, credentials, or browser state
