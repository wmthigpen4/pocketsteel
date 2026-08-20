# Same-feature factorized logit ensemble

## Task summary

Added `FactorizedEnsembleRecognizer`, a content-addressed ONNX ensemble runtime for two or more compatible factorized models. It extracts one shared feature array, runs every member on that array, averages root, conditional-quality, bass, and boundary logits independently, and invokes the existing hierarchical or beat-aware decoder exactly once. Decoded segments are never averaged or voted.

Optional weights must be finite, non-negative, match the member count, and sum to one. Exact one-hot weights return a byte-identical copy of the selected member's logits and reproduce that member's decoded segments.

Every member is validated against its ONNX input/output contract, factorized schema, feature kind/count, 0.1-second frame grid, sample rate, feature-spec identity, complete vocabulary, head order, and output widths. The runtime rejects model mutation during load, incompatible members, non-finite inputs or logits, frame-count drift, malformed weights, and invalid durations. Dasheng audio inference remains offline and extracts its verified snapshot-backed feature array only once for the whole ensemble.

Predictions expose each member's SHA-256, byte count, runtime-contract hash, architecture, window contract, normalized weight, the content-addressed ensemble SHA-256, and a deterministic decoder-contract SHA-256. New ONNX exports also write the explicit frame duration metadata; existing v2 exports remain compatible because their schema already fixes the frame duration to 0.1 seconds.

## Files changed

- `steel_guitar_rag/chord_reader/factorized.py`
- `tests/test_chord_reader_factorized.py`
- `docs/handoffs/task-completions/2026-08-20-1537-20-factorized-logit-ensemble.md`

## Tests/checks run

- Focused factorized suite: 48 passed, 1 skipped.
- Factorized, Dasheng, Dasheng-cache, artifact-integrity, and split-protocol suites: 95 passed, 2 skipped.
- Actual ONNX Runtime smoke with the 30-epoch multiband control and pitch-roll challenger on one synthetic zero-feature array: passed; one ensemble segment emitted with the expected feature contract.
- Actual mixed TCN/transformer one-hot endpoint smoke: passed; decoded segments exactly equaled the selected TCN member.
- Ruff on factorized implementation and focused tests: passed.
- Python compile check using the workspace Python with a temporary pycache: passed.
- Exact-path `git diff --check`: passed.

## Risks

- This is an inference/runtime primitive only. No ensemble weights were tuned, no models were trained, and no accuracy claim follows from the implementation.
- Raw-logit averaging assumes members have reasonably comparable logit scales. Uniform and candidate weights must be selected on development data only; calibration and confirmation data must stay sealed.
- The research worktree's default `.venv` does not currently contain the optional `onnxruntime` package. The actual-model smoke passed under the existing play-along virtual environment with ONNX Runtime 1.28.0; dependency installation was outside this slice.
- The factorized implementation and test files already contain earlier uncommitted v9 work from other approved slices. Parent integration must review them as cumulative files rather than treating this handoff as an isolated historical diff.
- CLI and benchmark wiring were intentionally excluded. Direct Python callers can use the runtime now; a later owned integration slice should add any command-line or benchmark entry point.

## Human decision needed

None for integration. Model/weight selection remains an evaluation decision after same-seed development comparisons.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/factorized.py`
- `tests/test_chord_reader_factorized.py`
- `docs/handoffs/task-completions/2026-08-20-1537-20-factorized-logit-ensemble.md`

## Files that must not be staged

- Generated ONNX models, weights, feature caches, sealed manifests, benchmark outputs, audio, corpus artifacts, and unrelated dirty files.

## Recommended next lane

Lane 20 can train additional seeds of the selected same-feature architecture on the sealed train protocol, select uniform versus development-tuned non-negative weights on development only, and hand the frozen ensemble identity to Lane 15 for strict evaluation. CLI/benchmark integration belongs to its owning implementation slice.

## Commit readiness

The runtime and focused tests are ready for parent-task integration. Nothing was staged or committed.
