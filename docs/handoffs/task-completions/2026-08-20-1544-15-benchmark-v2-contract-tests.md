# Benchmark v2 contract tests

## Task summary

Added a focused, corpus-free QA suite for the strict factorized-cache benchmark v2 contract. The tests exercise the public benchmark path with tiny NPZ/reference fixtures and an isolated recognizer. They verify exact frozen calibration bar-set selection, forwarding all timing manifests into split validation, artifact-seal validation before inference, source/cache dataset identity, single-read raw reference hashing, semantic timing hashing, shared evaluation-hash recomputation, strict v2 report merging, and fail-closed feature-spec/split/artifact requirements.

No implementation files were changed. No model training, corpus access, calibration, promotion, runtime wiring, UI work, or deployment was performed.

## Files changed

- `tests/test_chord_reader_benchmark_v2.py`
- `docs/handoffs/task-completions/2026-08-20-1544-15-benchmark-v2-contract-tests.md`

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_chord_reader_benchmark_v2.py` — 9 passed.
- `.venv/bin/python -m ruff check tests/test_chord_reader_benchmark_v2.py` — passed.
- `git diff --check -- tests/test_chord_reader_benchmark_v2.py` — passed.
- `git status --short` — reviewed before and after; the worktree contains substantial pre-existing concurrent chord-reader changes, all left untouched.

## Integration notes

- Calibration scoring is asserted to select only the descriptors sealed under `splitProtocol.calibration.barEligibility.tracks`, and their shared `trackSetSha256` must equal the frozen bar-eligible set hash.
- The artifact validator is asserted to run before the first `predict_features` call and again after inference.
- Raw reference bytes are asserted to be read once, parsed from those same bytes, and hashed without JSON normalization.
- Every current semantic timing identity field is asserted to change `timingSha256`; `referencePath` is intentionally excluded from that semantic identity.
- Merge tests first validate each v2 source report, reject a dirty or different source identity, recompute the merged evaluation hashes, and retain `promotionEligible=True` plus `oracleTimingUsed=False`.
- Missing `featureSpecSha256`, `splitProtocol`, or `artifactIntegrity` fails before any inference call.
- No implementation failure was found by this focused suite.

## Risk assessment

Low. The new file is tests only. Split-protocol and artifact-integrity validators are isolated in most benchmark-path tests so the tests can assert call ordering and exact arguments; their internal behavior remains covered by their dedicated suites. The missing-artifact case deliberately uses the real artifact validator.

## Human decision needed

No.

## Safe-to-stage exact file list

- `tests/test_chord_reader_benchmark_v2.py`
- `docs/handoffs/task-completions/2026-08-20-1544-15-benchmark-v2-contract-tests.md`

## Files that must not be staged

- Every other modified or untracked file in the shared worktree unless separately approved by its owning handoff.
- Generated model weights, feature caches, label caches, benchmark outputs, audio, and corpus artifacts.

## Recommended next lane

Lane 15 should run this suite together with the dedicated split-protocol, artifact-integrity, factorized, bar-product, bar-promotion, and promotion-v9 suites after the concurrent implementation files settle.

## Commit readiness

Safe to commit

## Suggested next step

Lane 15: run the integrated strict chord-reader QA set, then report any implementation failures without weakening the frozen v2 contract.
