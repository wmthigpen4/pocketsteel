# Play-Along Key Regions And Seventh Calibration

## Task Summary

- Made seventh-chord quality audio-led so harmonic key context can no longer
  manufacture a dominant seventh when the flattened seventh is not present in
  the retained chroma evidence.
- Added stable section-level key-region detection and independent chord
  decoding inside each detected region.
- Added Review controls to set a section key or add/remove a key-change marker
  at any bar while preserving manual chord corrections.
- Made Review and Play Along Nashville numbers use the active section key.
- Added key-journey labels, Song Map modulation markers, and a live Current key
  badge in Play Along.
- Added the Alan Jackson shape as a deterministic regression: G major, then C
  major, then A major, with no false dominant sevenths on plain triads.

## Source And Release Identity

- Branch: `feature/enhanced-play-along-staging`
- Feature commit: `be68e6859d6e76f01114ef0f2fd04bf226e12da5`
- Prepared detached release:
  `/Users/cory/.steel-rag/releases/be68e685-key-regions-staging`
- Current live staging commit during this handoff: `d3a0d1a`
- Production was not changed.

## Tests And Checks

- `npm run check:js` — passed.
- `npm run check:assets` — passed.
- `npm run check:locks` — passed.
- `scripts/check_secret_patterns.py` — passed.
- Full Python suite — `1577 passed`.
- Focused Play-Along suite — `34 passed`.
- `git diff --check` — passed before commit.

## Exact-Release Smoke

- Started the detached commit temporarily on isolated loopback port `8791`
  with the staging runtime configuration, without changing the LaunchAgent,
  tunnel, DNS, auth, or live staging listener.
- `/health/live` — 200.
- `/health/ready` — 200.
- `/api/version` — 200 with `git_sha: be68e68`.
- `/setup/local-smoke?v=key-regions-be68e685` — 200 and browser-verified:
  `Starting key`, the key-journey element, and all cache-busted Review assets.
- `/play/local-smoke?v=key-regions-be68e685` — 200 and browser-verified:
  `Current key`, the key-journey element, and all cache-busted Play Along
  assets.
- The user's original authenticated Remember When staging tab was restored to
  `https://test.steelguitarrag.com/play/local-c8742572-fd8b-4171-b0ff-6bc09ec30c27`
  after the isolated smoke.

## Deployment Status

The exact release is prepared and verified, but it was not activated on
`test.steelguitarrag.com`. The staging service is a custom user LaunchAgent,
`com.steelguitarrag.staging`, while the repository runbook documents only the
production LaunchDaemon activation/restart helper. `AGENTS.md` requires a stop
when the restart command is missing or ambiguous, so no plist edit, direct
`launchctl` command, listener termination, or improvised cutover was used.

The safe next step is to document or provide the approved exact staging
activation command for `com.steelguitarrag.staging`, point it at the prepared
release above, verify `/api/version` reports `be68e68`, and then repeat the
authenticated browser smoke on the user's retained local project.

## Known Repository Baseline

- `docs/handoffs/task-completions/integration-status.md` contains unrelated
  pre-existing user work and was not staged or edited by this task.
- `.venv` remains intentionally untracked and was not staged.

## Risk Assessment

Medium. The change deliberately shifts authority from key priors to audio
evidence for seventh quality and introduces section-level modulation state.
The deterministic G → C → A regression, full suite, and exact-release browser
smoke are green. Final risk remains the real-recording result for the user's
on-device project after the staging cutover.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-08-03-1626-play-along-key-regions.md`

## Files That Must Not Be Staged

- `docs/handoffs/task-completions/integration-status.md`
- `.venv`
- LaunchAgent plists, environment files, logs, credentials, audio, local
  browser storage, and detached release contents.

## Recommended Next Lane

- Lane 12 Self-Hosted Deployment after an approved staging restart procedure
  is available, followed by authenticated smoke on the retained Remember When
  project.

## Commit Readiness

- The handoff file is safe for an exact-path documentation commit.
