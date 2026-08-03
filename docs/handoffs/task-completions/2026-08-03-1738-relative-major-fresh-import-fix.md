# Relative-major fresh-import correction

Completed and published to staging on 2026-08-03.

## Reported failure

A deleted and freshly re-added `Remember When` recording was analyzed as `E minor → F# minor`, missing the middle section. The detected chords showed the systematic cause: G/G6 sonorities were being labeled Em/Em7, C/C6 as Am/Am7, and A/A6 as F#m/F#m7.

## Generalized correction

- Major-sixth versus relative-minor ambiguity now uses audible root strength before choosing the chord label.
- Starting-key estimation now includes primary I/IV/V harmonic-function evidence.
- The starting key is estimated from the opening section rather than allowing a long final modulation to dominate the whole-song average.
- Automatic key-region detection keeps the selected mode stable, while manual section-mode changes remain available.
- Existing v2 projects on an older calibration automatically run a fresh on-device analysis without preserving a possibly incorrect old key hint.
- No song title, artist, or project ID is hard-coded.

## Release and verification

- Feature commit: `b9119642`
- Staging release: `/Users/cory/.steel-rag/releases/b9119642-relative-major-staging`
- Staging live, ready, and version checks passed; production was not changed.
- New regression covers a fresh, sixth-colored G major → C major → A major form and recovers all three regions.
- True Em7 remains Em7 in the root-evidence regression.
- Focused tests: `33 passed`.
- Full suite: `1581 passed in 89.84s`.
- JavaScript, asset-budget, dependency-lock, secret-pattern, and diff checks passed.

## Browser note

The exact fresh project was inspected before deployment and confirmed the `E minor → F# minor` failure. A staging sign-in renewal prevented the post-deployment page reload, so exact-project browser confirmation remains pending; the new calibration will automatically rerun when the authenticated Review page reloads.

## Workspace note

The pre-existing modified `docs/handoffs/task-completions/integration-status.md` and untracked `.venv` were left untouched and are not part of this work.
