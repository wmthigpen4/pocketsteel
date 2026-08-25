# Bounded consensus preflight stop

## Task summary

The user authorized the preregistered three-candidate bounded development run.
The harness and preregistration were implemented, tested, and committed at
`6800cd92` before any new inference or fit.

The feature command then stopped during its input-binding preflight. No audio
was opened, BTC was not instantiated by the command, no NNLS feature was
created, and no candidate was fit. In accordance with the zero-automatic-retry
rule, the command was not rerun.

## Exact blocker

The bar-example surface has 185 unique tracks across 246 runtime rows and all
185 bind to the development runtime-audio manifest. Those same track IDs exist
in the sealed multiband cache, but their cache entries carry the historical
source-cache role `train`, not `development`. The harness incorrectly filtered
the feature lookup to entries whose source-cache role was `development`, so it
reported all 185 unique tracks as missing.

This is a manifest-role mismatch, not missing data and not a model result. The
safe correction is to bind feature rows by exact track ID across the sealed
manifest while continuing to derive the experiment role exclusively from the
development-only examples and runtime-audio manifests. No label or held-out
partition needs to be opened.

## Files changed

- `scripts/run_bounded_consensus_development.py`
- `tests/test_bounded_consensus_development.py`
- `docs/handoffs/task-completions/2026-08-25-1600-15-bounded-consensus-development-preregistration.md`
- this stop handoff

The first three paths are committed in `6800cd92`. No correction has been
applied yet. No generated experiment file exists below the intended bounded
output directory.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_bounded_consensus_development.py`
  — 4 passed.
- `.venv/bin/ruff check scripts/run_bounded_consensus_development.py tests/test_bounded_consensus_development.py`
  — passed.
- `.venv/bin/ruff format --check scripts/run_bounded_consensus_development.py tests/test_bounded_consensus_development.py`
  — passed after formatting.
- `git diff --check` — passed before the scoped preregistration commit.
- Local dependency readiness — BTC snapshot, Torch, librosa, NumPy, and
  scikit-learn available.
- One feature command — stopped in binding preflight before inference.

## Risk assessment

Low. No model work occurred. The primary risk is silently treating a second
command as an automatic retry, which is why execution stopped. The proposed
correction does not expand candidates, fits, thresholds, data roles, or output
surfaces.

## Human decision needed

Yes. Approve one corrected feature command after the exact track-ID binding fix.
The original cap remains unchanged: one actual BTC pass, one NNLS pass, exactly
three candidate fits, zero searches, and a mandatory terminal stop.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-25-1610-15-bounded-consensus-preflight-stop.md`

After approval and correction, the exact safe implementation paths would be:

- `scripts/run_bounded_consensus_development.py`
- `tests/test_bounded_consensus_development.py`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `~/Documents/Pocket Steel/tmp/`
- all source audio, model caches, credentials, and unrelated files

## Recommended next lane

Lane 15: apply the exact track-ID binding correction, add a regression test,
run one corrected feature command and the single three-fit evaluation, then
stop at the terminal report.

## Commit readiness

Safe to commit

## Suggested next step

Approve the one corrected feature command under the unchanged hard cap.
