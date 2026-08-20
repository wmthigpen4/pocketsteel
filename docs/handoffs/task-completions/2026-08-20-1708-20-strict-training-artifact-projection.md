# Strict training artifact projection

## Task summary

Changed strict factorized training preflight so the complete signed split
protocol and complete artifact-set seal are validated as metadata, while file
inspection is restricted to a derived train-plus-development projection.
Calibration feature and label NPZs are no longer opened, loaded, or rehashed by
training preflight. They remain bound by the immutable calibration-set hash,
the full output-manifest hash, and the full artifact-set hash recorded in model
provenance.

The legacy no-protocol path is unchanged. It continues to verify every file in
the manifest because it has no sealed calibration partition contract.

## Files changed

- `steel_guitar_rag/chord_reader/factorized.py`
- `tests/test_chord_reader_factorized.py`
- `docs/handoffs/task-completions/2026-08-20-1708-20-strict-training-artifact-projection.md`

No generated dataset, feature, label, reference, model, prediction, benchmark,
calibration, or test artifact was changed.

## Tests and checks

- Focused strict-projection and tamper checks: 7 passed.
- Full `tests/test_chord_reader*.py`: 278 passed, 4 dependency-gated skips.
- ML environment `tests/test_chord_reader_factorized.py`, including real 139-output ONNX export/parity: 70 passed.
- Ruff and `git diff --check`: passed.

The focused synthetic fixture makes every calibration feature and label path
unavailable after sealing, then proves strict training provenance still
validates. Separate parameterized checks tamper train/development labels and
features and prove each is rejected before model setup; calibration seal
metadata tampering also fails closed without opening calibration files. The
training contract asserts preservation of the complete artifact-set hash and
records the exact two verified file partitions and count.

## Risks

- Full calibration-file byte revalidation is intentionally deferred until an
  explicitly authorized calibration operation. Strict training still fails on
  any calibration metadata, assignment, set-hash, output-manifest, or full
  artifact-seal mutation.
- The full artifact seal contains the original calibration file digests and
  paths. Training preserves and records that seal but does not assert that
  calibration files are presently readable; that is the desired isolation
  property.

## Human decision needed

None. This is a leakage-hygiene correction required before the matched joint
root/product training runs.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/factorized.py`
- `tests/test_chord_reader_factorized.py`
- `docs/handoffs/task-completions/2026-08-20-1708-20-strict-training-artifact-projection.md`

These source and test files overlap the concurrent optional joint-head slice;
stage their final reviewed versions together, not partial stale copies.

## Files that must not be staged

- Any path under `tmp/`
- Any generated feature, label, reference, model, ONNX, prediction, benchmark,
  calibration, test, or private artifact

## Recommended next lane

Lane 20 may run the matched train/development-only joint-root/product matrix
after the combined source is committed and the complete chord-reader test suite
is green. Lane 15 should then run strict development-only decoding and audit
the frozen reports.

## Commit readiness

Ready for exact-path integration after the combined chord-reader checks and
code review pass. No training, export, benchmark, calibration, or test split
was opened for this task; only synthetic test fixtures were exercised.
