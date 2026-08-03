# Silent-intro tonic correction

Completed and published to staging on 2026-08-03.

## Reported failure

`Cowboy Take Me Away (No Steel)` should remain in F# major, but a long silent intro and frequent C# dominant chords caused the analyzer to report `C# major → F# major`.

## Generalized correction

- Silent opening bars are excluded from the tonal pitch profile.
- Repeated dominant-to-tonic resolutions now inform the initial tonic estimate.
- Silence still breaks cadence adjacency rather than joining distant chords.
- No song title, artist, or project ID is hard-coded.
- Existing projects on the prior calibration automatically run a fresh on-device analysis.

## Release and verification

- Feature commit: `093e5939`
- Staging release: `/Users/cory/.steel-rag/releases/093e5939-tonic-cadence-staging`
- Staging live, ready, and version checks passed; production was not changed.
- Regression reproducing the leading silence and F#/C#/B/D#m vocabulary reports one F#-major region.
- Prior G major → C major → A major and borrowed-flat-seven regressions still pass.
- Focused tests: `36 passed`.
- Full suite: `1584 passed in 92.34s`.

## Browser note

The exact project showed the original `C# major → F# major` failure before deployment. Its browser-local project became unavailable during the staging restart, so the post-deployment exact-project reload could not be completed.

## Workspace note

The pre-existing modified `docs/handoffs/task-completions/integration-status.md` and untracked `.venv` were left untouched and are not part of this work.
