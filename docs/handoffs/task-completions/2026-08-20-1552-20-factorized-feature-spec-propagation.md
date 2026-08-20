# Factorized browser feature-spec propagation fix

## Task summary

The first post-seal training run exposed that browser-feature model configs did
not retain the top-level sealed `featureSpecSha256`; they wrote `null` even
though the protocol and artifact seal contained the hash. Strict v2 benchmarking
correctly refuses such a model because it cannot prove that model and cache use
the same feature extractor contract.

Updated the browser feature-contract validation to require the sealed hash for
split-protocol training and carry it through model config and ONNX metadata.
Legacy unsigned research caches may still omit it. The four affected first-run
model directories are diagnostic only and must not be exported or certified;
they will be retrained after this clean commit.

## Files changed

- `steel_guitar_rag/chord_reader/factorized.py`
- `tests/test_chord_reader_factorized.py`
- `docs/handoffs/task-completions/2026-08-20-1552-20-factorized-feature-spec-propagation.md`

## Tests/checks run

- Factorized plus benchmark-v2 focused suites: 59 passed, 1 optional test
  skipped.
- Ruff: passed.
- `git diff --check`: passed.

## Risks

The completed pre-fix model artifacts remain ignored but are not valid v2
challengers. No calibration or confirmation data was opened.

## Human decision needed

None.

## Safe-to-stage exact files

- `steel_guitar_rag/chord_reader/factorized.py`
- `tests/test_chord_reader_factorized.py`
- `docs/handoffs/task-completions/2026-08-20-1552-20-factorized-feature-spec-propagation.md`

## Files that must not be staged

- all `tmp/` models, caches, protocols, reports, predictions, and audio.

## Recommended next lane

Lane 20 should retrain the matched seeds from the unchanged sealed protocol,
verify the config hash equals the cache feature-spec hash, and only then export
ONNX candidates.

## Commit readiness

Ready for an exact-path research-branch fix commit.
