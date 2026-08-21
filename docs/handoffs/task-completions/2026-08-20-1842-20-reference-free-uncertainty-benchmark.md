# Reference-free uncertainty benchmark wiring

## Task summary

Implemented the development-only benchmark and CLI boundary for factorized
reference-free uncertainty telemetry. `benchmark-factorized-cache` now accepts
`--emit-uncertainty`, passes the opt-in to
`predict_features(..., emit_uncertainty=True)`, validates the emitted hashes and
frozen feature/model/decoder/member bindings, binds the uncertainty payload to
the exact prediction core, shallow-validates its timebase and exact frame-group
shape, writes the complete prediction atomically, and only then opens the
source reference JSON for evaluation.

Emit mode rejects any non-development split and any beat-grid source other
than `none` before model, artifact, cache-manifest, or reference access. Its
report is explicitly `developmentOnlyExperiment: true` and
`promotionEligible: false`. Default-off CLI dispatch, recognizer call shape,
prediction JSON bytes, and certification behavior remain unchanged.

This slice intentionally did not implement a bar-example builder, grouped-OOF
selector, confidence calibrator, corpus change, or any calibration/test run.

## Files changed

- `steel_guitar_rag/chord_reader/benchmark.py`
  - Added early development/no-oracle guards.
  - Added fail-closed uncertainty/core digest and binding validation.
  - Uses the core public `validate_factorized_uncertainty_contract` validator
    to recompute the formula/binding/member contract and `memberOrderSha256`.
  - Retains benchmark-specific cache, decoder, model, and ordered-member
    identity checks after the shared validator passes.
  - Freezes a deep copy of the recognizer's exact member identities, head
    types, common weights, and joint-contributor weights before inference, so
    a coherently resealed or moving member comparator fails closed.
  - Requires the uncertainty payload's `predictionCoreSha256` to match the
    independently validated top-level prediction-core digest.
  - Requires timebase frame count, frame step, and duration to match the
    prediction, and requires exactly the five frozen frame groups.
  - Added atomic emit-mode prediction materialization before reference reads.
  - Added per-track `predictionCoreSha256` and `uncertaintySha256` fields.
  - Added the top-level `uncertaintyExperiment` schema, contract, feature,
    member, binding, and set hashes.
  - Kept the full emitted prediction file SHA as the existing
    `predictionSha256` evaluation identity.
- `steel_guitar_rag/chord_reader/cli.py`
  - Added `benchmark-factorized-cache --emit-uncertainty` and CLI-level early
    rejection before reading the cache manifest.
  - Does not pass a new keyword on the default-off path.
- `tests/test_chord_reader_benchmark_uncertainty.py`
  - Added 20 focused cases covering guards, CLI dispatch, atomic/reference
    ordering, digest/member/timebase/frame-group tamper rejection, shared
    bindings, full-file hashing, report contracts, and byte-stable default
    behavior.
- `docs/handoffs/task-completions/2026-08-20-1842-20-reference-free-uncertainty-benchmark.md`
  - This handoff.

No files were deleted. Ignored smoke outputs were generated beneath
`tmp/chord-reader-v9/experiments/` and must not be staged.

## Tests and checks

- `.venv/bin/pytest -q tests/test_chord_reader_benchmark_uncertainty.py`
  - `20 passed` after the fail-closed binding/timebase/member-identity
    follow-ups.
- `.venv/bin/pytest -q tests/test_chord_reader_uncertainty.py tests/test_chord_reader_bar_uncertainty.py tests/test_chord_reader_benchmark_uncertainty.py tests/test_chord_reader_benchmark_v2.py tests/test_chord_reader_factorized.py`
  - `157 passed, 3 skipped` on the final shared-validator tree.
- `.venv/bin/pytest -q tests/test_chord_reader*.py`
  - `359 passed, 4 skipped`.
- `.venv/bin/ruff check steel_guitar_rag/chord_reader tests/test_chord_reader*.py`
  - Passed.
- `.venv/bin/python -m compileall -q steel_guitar_rag/chord_reader tests/test_chord_reader_benchmark_uncertainty.py`
  - Passed.
- `git diff --check`
  - Passed.

The protected-reference spy passed. At the first attempted
`referencePath.read_bytes()`, the final destination prediction file already
existed, parsed as complete JSON, contained `uncertainty`, declared
`referenceFree: true`, and had a matching canonical `uncertaintySha256`.
Tampered uncertainty is rejected before that reference path is opened. The
tamper matrix covers a valid-looking but false member-order digest, a spliced
prediction-core digest, a coherently resealed false member identity, a
recognizer identity that moves during inference, frame-count/frame-step/duration
drift, and missing or additional top-level frame groups.

## Real sealed-development smoke

Two real ONNX smoke runs used the sealed multiband cache, the five existing
timing manifests, split `development`, `--limit 1`, `--beat-grid-source none`,
and no calibration/test scoring.

- Single joint model pass:
  - `tmp/chord-reader-v9/experiments/uncertainty-single-smoke/report.json`
  - Track: `aam-0001`.
  - One member binding was recorded.
  - `developmentOnlyExperiment: true` and `promotionEligible: false`.
  - Contract SHA-256:
    `645eeedd84f91ef1a37cd355b6e6f9b83a01cd7b8a357e995b0fb898fc8f32e2`.
  - Prediction-core SHA-256, matching both the top level and nested cross-link:
    `e2dbc3621feb77e223e26e5949683ab18bad562c5521c635f8107856bd5b8c58`.
  - Uncertainty SHA-256:
    `eae3f2902e5a853520b4eca997b6411494211b000ac750af65fd24326c00003c`.
  - Full prediction file SHA-256:
    `fce040df558689bf230d9df4f4c5fe999ae8ce68ecd028643a00e2779de14522`.
- Frozen seven-member mixed winner pass, blend `0.75`:
  - `tmp/chord-reader-v9/experiments/uncertainty-winner-smoke/report.json`
  - Track: `aam-0001`.
  - Seven member bindings were recorded.
  - `developmentOnlyExperiment: true`.
  - `promotionEligible: false`.
  - Contract SHA-256:
    `55dae3ecb81a97e725466b597aa892e031a33f6cbc7285a39bee1316af2d46b7`.
  - Feature-binding SHA-256:
    `59c9db267249a35bd5facee9cc35d6fe55ed3b884bf2108b7649d9fc45c93ead`.
  - Member-binding SHA-256:
    `04abb855199e4b1358349a0ac220683a62a33467cc851f83f937b77a6071a4cc`.
  - Binding SHA-256:
    `d1dbc4d2d67677d1df2f935cb48763ac798ca9c0f953de90f5ac05ffcbcaeabb`.
  - Prediction-core SHA-256, matching both the top level and nested cross-link:
    `4963249b5313c786c0715dc10ad2d842046ccbbea6e8b07bbfa539c41dc00d27`.
  - Uncertainty SHA-256:
    `38a59ed170f8b1c8dcb983cf523d9f26b611959eae7f11b204c825874a9d1931`.
  - Full prediction file SHA-256:
    `8254ab78eca518cbeca528f2cf9cbe0a6d5aa49a44462321f4dc6f0b6edf93bf`.

For both final reruns, an independent SHA-256 of the complete prediction bytes
exactly matched the track's `predictionSha256`, and the nested
`uncertainty.predictionCoreSha256` exactly matched the independently validated
top-level digest.

The first winner smoke attempt exposed an integration error in the separate
core uncertainty slice when reconstructing frame paths from ensemble segments.
That owner fixed the dict-field extraction and product-label cross-check; the
same real winner command then passed. A first single-model attempt using a
development-only timing projection was correctly rejected because strict
protocol validation requires the complete sealed timing manifests; rerunning
with those manifests passed while decoding/scoring only the selected
development row.

## Integration notes

- The emitted uncertainty payload is embedded in the prediction JSON; there is
  no second mutable prediction identity. `predictionCoreSha256` binds the
  prediction without the three uncertainty transport fields,
  `uncertainty.predictionCoreSha256` binds that same core from inside the
  uncertainty payload, `uncertaintySha256` binds the uncertainty payload, and
  `predictionSha256` binds the complete on-disk file used by evaluation
  provenance.
- All emitted tracks must share uncertainty schema, contract, feature binding,
  ordered member binding, and complete binding hashes. Drift fails closed
  before the drifting track's reference is opened.
- The top-level report discloses both the shared binding values and canonical
  binding hashes, plus core/uncertainty track-set hashes.
- Emit mode cannot enter `validate_benchmark_v2_provenance` or promotion.
- Protocol validation may inspect sealed timing metadata, but only the selected
  development feature and reference JSON were decoded/scored in the real
  smoke. No calibration/test reference JSON or result was opened.

## Risk assessment

Risk is medium-low. The change is opt-in, development-only, reference-free
before evaluation, fail-closed on malformed telemetry, and covered by default
byte/behavior regression tests. The primary remaining risk is report size:
frame telemetry is intentionally verbose and should remain an ignored research
artifact until a later example-builder contract selects compact bar features.

Rollback is removal of the CLI flag, emit branch, uncertainty report summary,
and focused test file; the default path is otherwise unchanged.

## Human decision needed

No.

## Safe-to-stage exact file list

These files are safe to stage as the benchmark/CLI portion of the combined
uncertainty integration commit:

- `steel_guitar_rag/chord_reader/benchmark.py`
- `steel_guitar_rag/chord_reader/cli.py`
- `tests/test_chord_reader_benchmark_uncertainty.py`
- `docs/handoffs/task-completions/2026-08-20-1842-20-reference-free-uncertainty-benchmark.md`

The core uncertainty files have a separate owner/handoff and must be included
from that exact reviewed list in the combined integration commit; this handoff
does not authorize staging them by implication.

## Files that must not be staged

- `tmp/chord-reader-v9/experiments/uncertainty-single-smoke/`
- `tmp/chord-reader-v9/experiments/uncertainty-winner-smoke/`
- Any other generated model, feature cache, prediction, report, corpus, or
  private artifact.

## Recommended next lane

Lane 01 Repo Steward should combine this exact list with the separately tested
core uncertainty exact list, review the full staged diff, and commit only after
the core handoff and aggregate QA agree. The next model-development slice may
then build grouped out-of-fold bar examples from train-only predictions; it
must not open calibration or confirmation.

## Commit readiness

Safe to commit as part of the tested combined uncertainty integration.

## Suggested next step

`Lane 01: combine the exact safe-to-stage lists from the core uncertainty and reference-free benchmark handoffs, run staged diff checks, and commit the tested integration without generated smoke artifacts.`
