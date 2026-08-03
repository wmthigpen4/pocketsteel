# Functional-cadence key-region correction

Completed and published to staging on 2026-08-03.

## Reported failure

A freshly imported `Remember When` recording correctly started in G major and ended in A major, but its short C-major middle section was absorbed into G as borrowed ♭VII harmony.

## Generalized correction

- Key-region scoring now recognizes repeated dominant-to-tonic and subdominant-to-tonic resolutions inside a candidate region.
- Cadences at a region boundary are excluded so an adjacent section cannot receive credit for the prior section's transition.
- The rule is based on harmonic function, with no song title, artist, or project ID hard-coded.
- Existing projects on the prior calibration automatically run a fresh on-device analysis.
- A control regression confirms that occasional borrowed ♭VII chords do not create a false modulation.

## Release and verification

- Feature commit: `a74ab3fa`
- Staging release: `/Users/cory/.steel-rag/releases/a74ab3fa-functional-cadence-staging`
- Staging live, ready, and version checks passed; production was not changed.
- The exact fresh project now reports `G major → C major → A major` in both Review Song and Play Along.
- Review Song marks C major at bar 62 and A major at bar 76.
- Focused tests: `35 passed`.
- Full suite: `1583 passed in 85.76s`.

## Workspace note

The pre-existing modified `docs/handoffs/task-completions/integration-status.md` and untracked `.venv` were left untouched and are not part of this work.
