# Travis validation key and NNS controls

## Task summary

This Lane 06 adjustment adds a per-song key selector and a Chords/NNS display
toggle to the private Travis validation page. Each song begins with a suggested
major key derived from its duration-weighted chord timeline. Travis can replace
that key when the suggestion is wrong, and all displayed chord labels convert
to Nashville numbers immediately.

The selected key, whether it was suggested or reviewer-selected, and the chosen
display mode persist with the existing browser feedback. The original absolute
chord prediction remains unchanged.

## Behavior changed

- all 12 major keys are available, including enharmonic display for F#/Gb;
- the key control identifies suggestions versus reviewer selections;
- Chords view shows the original absolute chord labels;
- NNS view converts roots chromatically relative to the selected key and
  preserves chord quality and slash-bass relationships;
- `N.C.` remains `N.C.` in both views;
- selected key and display mode survive reloads in the same review session;
- exported tracks include `suggestedKey`, `songKey`, `keySource`, and
  `displayMode`;
- exported segments include both `predictedChord` and `predictedNns`.

## Files changed

- `ui/chord-reader-travis-validation/index.html`
- `ui/chord-reader-travis-validation/validation.css`
- `ui/chord-reader-travis-validation/validation.js`
- `tests/test_travis_validation_ui.py`
- this handoff

No audio, generated predictions, model weights, deployment configuration,
authentication, or production state changed.

## Tests and checks

- `node --check ui/chord-reader-travis-validation/validation.js` — passed;
- `pytest -q tests/test_travis_validation_ui.py tests/test_chord_reader_proof.py`
  — 9 passed;
- Ruff check and format check for the focused Python test — passed;
- Prettier applied to the three page assets;
- `git diff --check` — passed;
- browser smoke — passed.

## Browser smoke

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested:
  `http://127.0.0.1:8898/ui/chord-reader-travis-validation/?v=4&session=automated-smoke-v4`
- Exact URL the user should use:
  `http://127.0.0.1:8898/ui/chord-reader-travis-validation/?v=4`
- Auth required: no
- Local backend URL: `http://127.0.0.1:8898`
- Expected backend port: `8898`
- Who should test this URL: Codex and the user
- Do not test these URLs: production or public URLs; private audio is
  localhost-only

Browser assertions:

- `Nothing's News (No Steel)` initially suggests C;
- its first eight absolute labels are `N.C., C, G, Am, C, F, G, C`;
- NNS in C renders those labels as `N.C., 1, 5, 6m, 1, 4, 5, 1`;
- reviewer-selecting G changes them to `N.C., 4, 1, 2m, 4, b7, 1, 4`;
- the key label changes from `suggested` to `reviewer selected`;
- G and NNS persist after reload in the isolated smoke session;
- all 15 song selectors render a suggested key;
- the document still fits one desktop viewport and the chord rail remains
  horizontal;
- whole-song notes and action buttons remain inside the viewport;
- browser diagnostic log count is zero.

## Risk assessment

Low-to-medium. NNS conversion is deterministic once the selected key is known,
but the initial key is a heuristic suggestion rather than a trained key
estimate. The UI therefore labels it as suggested and gives the reviewer direct
control. Minor-key songs are not offered as a separate tonic mode in this
country-focused pilot; chromatic and minor chords are represented relative to
the selected major tonic.

The current link remains localhost-only. Remote Travis access still requires a
separate protected-hosting and audio-rights decision; deployment/auth was not
attempted.

## Safe-to-stage exact file list

- `ui/chord-reader-travis-validation/index.html`
- `ui/chord-reader-travis-validation/validation.css`
- `ui/chord-reader-travis-validation/validation.js`
- `tests/test_travis_validation_ui.py`
- `docs/handoffs/task-completions/2026-08-25-1840-06-travis-validation-key-nns.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `ui/chord-reader-travis-validation/local-data/`
- all audio, generated predictions, feedback exports, browser/session data,
  credentials, course materials, and unrelated files

## Commit readiness

Safe to commit.

## Suggested next step

Open the clean `?v=4` URL, confirm or correct the suggested key before using NNS,
then complete the normal exception-only chord review.
