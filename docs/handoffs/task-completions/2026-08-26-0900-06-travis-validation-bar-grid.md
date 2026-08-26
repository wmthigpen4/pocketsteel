# Travis validation bar grid and structural review controls

## Task summary

This bounded Lane 06 correction stops presenting raw chord-detector intervals as
musical bars. The Travis validation page now uses a provisional, reviewer-
correctable beat grid, renders one numbered box per bar, and permits no more than
one supported half-bar split. Unstable short predictions are collapsed into the
strongest bar-level chord and labeled as unstable rather than displayed as
three- or four-chord arrangements.

The same change adds reversible adjacent-box merges, proper superscript NNS
extensions, frame-level playback tracking, time-signature and tempo controls,
and persistent backend fields for the new review data. Seamoon Funk Machine was
removed from the private pilot bundle and replaced by Cowboy Take Me Away (No
Steel). Private audio and generated proof data remain ignored and are not part
of the commit.

## Behavior changed

- chord boxes are numbered and can be referenced directly in comments;
- adjacent boxes can be selected, merged, commented on, corrected, and unmerged;
- lead-in silence is labeled separately and is not numbered as a chord box;
- `7` extensions use superscript notation in NNS (for example `4⁷`);
- time signature and tempo are visible, editable, and saved per song;
- the pilot grid defaults provisionally to 4/4 because automatic meter rankings
  were too close to present as definitive;
- raw beat-level chord fluctuations are aggregated to one chord per bar;
- a half-bar split is shown only when both halves have at least 60% coverage and
  64% confidence;
- a rendered bar can never contain three or more predicted chords;
- playback highlighting is driven by `requestAnimationFrame` while audio plays;
- the replacement track is Cowboy Take Me Away (No Steel).

## Files changed

- `ui/chord-reader-travis-validation/index.html`
- `ui/chord-reader-travis-validation/validation.css`
- `ui/chord-reader-travis-validation/validation.js`
- `workers/chord-reader-validation/src/validation.ts`
- `workers/chord-reader-validation/tests/index.test.ts`
- `scripts/enrich_travis_validation_rhythm.js`
- `scripts/replace_travis_validation_track.py`
- `tests/test_travis_validation_ui.py`
- this handoff

## Checks

- TypeScript worker check — passed;
- worker unit tests — 5 passed;
- focused Python UI tests — 3 passed;
- JavaScript syntax checks — passed;
- Ruff check — passed;
- `git diff --check` — passed;
- local browser smoke at
  `http://127.0.0.1:8898/ui/chord-reader-travis-validation/?v=6&session=v6-smoke`
  — passed.

The browser smoke verified 15 songs, Cowboy present, Seamoon absent, 4 beat
markers per provisional 4/4 bar, reversible merge/undo, and zero bars with more
than two displayed chord symbols. Overnight Male specifically rendered a
maximum of two chord symbols per bar after the correction.

## Accuracy and risk

This is a review-interface correction, not a chord-model accuracy gain. Meter,
tempo, downbeat phase, bar chord, and split decisions remain machine estimates.
The UI labels the 4/4 meter as provisional and exposes uncertainty instead of
claiming it as ground truth. Travis's edits are required to determine which
recurring errors can later support a measured model improvement.

## Safe-to-stage exact file list

- `ui/chord-reader-travis-validation/index.html`
- `ui/chord-reader-travis-validation/validation.css`
- `ui/chord-reader-travis-validation/validation.js`
- `workers/chord-reader-validation/src/validation.ts`
- `workers/chord-reader-validation/tests/index.test.ts`
- `scripts/enrich_travis_validation_rhythm.js`
- `scripts/replace_travis_validation_track.py`
- `tests/test_travis_validation_ui.py`
- `docs/handoffs/task-completions/2026-08-26-0900-06-travis-validation-bar-grid.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `ui/chord-reader-travis-validation/local-data/`
- audio, generated predictions, credentials, browser data, and course material

## Commit readiness

Safe to commit. The protected production asset upload and Access policy are
separate external-state steps.
