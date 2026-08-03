# Play-Along Key Regions Staging Completion

## Task Summary

- Completed and deployed audio-led seventh detection, stable same-mode key
  regions, section-aware NNS, Review key-boundary editing, Play Along current-key
  display, and modulation markers.
- Prevented sequence and key context from selecting a seventh chord when the
  flattened-seventh candidate lacks direct audio support.
- Added Review teaching that reports the detected flattened-seventh evidence
  for retained seventh labels.
- Published new immutable asset names because the staging cache does not honor
  query-string-only cache busting for the existing aliases.
- Corrected the retained Remember When project to the confirmed key journey:
  G major at bar 1, C major at bar 63, and A major at bar 76.

## Source And Runtime Identity

- Branch: `feature/enhanced-play-along-staging`
- Active commit: `e8fb923a358a78ab964602c503d2b7f12ec1b406`
- Detached release:
  `/Users/cory/.steel-rag/releases/e8fb923a-major-modulations-staging`
- Staging LaunchAgent: `com.steelguitarrag.staging`
- Staging `/api/version`: `e8fb923`
- Production was not changed.

## Verification

- Full Python suite: `1577 passed`.
- JavaScript syntax checks: passed.
- Asset budget: passed for 1276 tracked files and 51 Explorer chunks.
- Dependency-lock check: passed for five environments.
- Secret-pattern scan: passed.
- Live and ready health endpoints: passed during the health-gated cutover.
- Authenticated in-app browser smoke on the retained local project:
  - title loaded correctly;
  - starting/current key is G;
  - key journey is `G major → C major → A major`;
  - Review markers show C major and A major changes;
  - Play Along shows the same journey and current key;
  - Play Along Song Map contains both key-change markers;
  - dominant-seventh bars dropped from 59 to 4 after the immutable worker asset
    and unsupported-extension guard were active.

## Deployment Note

The first attempt used modern `launchctl bootout/bootstrap`; macOS rejected the
user LaunchAgent with error 5. The prior plist was restored and the service was
successfully recovered with its existing legacy user-agent mechanism,
`launchctl load -w`. Subsequent cutovers used `launchctl unload` followed by
`launchctl load -w`, with a plist snapshot, health/version gate, and automatic
rollback function. This is the known-working staging activation mechanism and
should be documented in the staging runbook before the next release.

## Known Repository Baseline

- `docs/handoffs/task-completions/integration-status.md` contains unrelated
  pre-existing user work and was not staged or edited by this task.
- `.venv` remains intentionally untracked and was not staged.

## Risk Assessment

Low to medium. The live retained project and full suite are green. Chord
recognition remains an estimate and the four retained dominant sevenths should
still be reviewed by ear, but context can no longer manufacture unsupported
sevenths. Manual key boundaries remain editable in Review.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-08-03-1700-play-along-key-regions-staging-complete.md`

## Files That Must Not Be Staged

- `docs/handoffs/task-completions/integration-status.md`
- `.venv`
- LaunchAgent plists, environment files, logs, credentials, audio, browser
  storage, detached releases, and temporary rollback snapshots.

## Recommended Next Lane

- Product review on the live staging project. Production promotion remains a
  separate decision.

## Commit Readiness

- This handoff is safe for an exact-path documentation commit.
