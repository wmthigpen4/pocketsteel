# Play Along: key-change cues in Now and Next

Completed and published to staging on 2026-08-03.

## Outcome

- The `Next` card shows `Key change ahead · [key] [mode]` when its upcoming chord crosses into a new key region.
- The `Now` card shows `Key change · [key] [mode]` throughout the first bar of the new region.
- Both states receive a green border and high-contrast badge treatment.
- The indicators are derived from the song's key-region data and therefore apply to detected and manually corrected modulations in any song.

## Release

- Feature commit: `92f99393`
- Staging release: `/Users/cory/.steel-rag/releases/92f99393-key-cues-staging`
- Staging version, live, and ready checks passed.
- Production was not changed.

## Browser verification

Verified on the retained `Remember When` project:

- Bar 62 `Next`: `Key change ahead · C major`
- Bar 63 `Now`: `Key change · C major`
- Bar 75 `Next`: `Key change ahead · A major`
- Bar 76 `Now`: `Key change · A major`
- The Song Map was closed and the player was left paused on bar 76.

## Automated verification

- Focused UI tests: `22 passed`
- Full suite: `1579 passed in 82.14s`
- JavaScript, asset-budget, dependency-lock, secret-pattern, and diff checks passed.

## Workspace note

The pre-existing modified `docs/handoffs/task-completions/integration-status.md` and untracked `.venv` were left untouched and are not part of this work.
