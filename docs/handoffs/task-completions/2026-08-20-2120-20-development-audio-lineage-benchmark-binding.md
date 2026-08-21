# Development audio-lineage benchmark binding

## Outcome

The frozen factorized-cache uncertainty benchmark now requires the exact full
development audio-lineage artifact. Before inference or reference access it
revalidates every bound source file, re-extracts every selected audio file with
the production multiband extractor, and proves that the float16 feature bytes
used for inference equal both the frozen cache array and the fresh extraction.

This closes the historical gap between source audio identity and the legacy
multiband feature cache. The change is development-only and does not make an
uncertainty report promotion evidence.

## Contract

`benchmark-factorized-cache --emit-uncertainty` now requires
`--audio-lineage-manifest`. The Python API accepts `audio_lineage=` and defaults
to full file/re-extraction verification. The CLI does not expose the synthetic
metadata-only verification mode.

For the exact selected development rows, the benchmark requires:

- the lineage artifact's production
  `steel_guitar_rag.chord_reader.student.extract_student_features` entrypoint;
- the exact canonical winner-cache manifest and feature-spec hash;
- an exact lineage projection over the benchmark track IDs and dataset IDs;
- the loaded inference array's contiguous little-endian float16 SHA-256 to
  equal both the cached and freshly extracted lineage array hashes;
- the cache duration's player-canonical milliseconds to equal the lineage row;
- a valid source-audio, row, projection, and artifact SHA chain.

Each report track now carries `sourceAudioSha256`, cached/fresh feature-array
hashes, canonical milliseconds, and `audioLineageRowSha256`. The top-level
`uncertaintyExperiment.audioLineage` records the full-verification mode, exact
source artifact, sealed projection, feature-array verification formula, and a
canonical binding hash. The report remains
`developmentOnlyExperiment=true`, `promotionEligible=false`, and
`beatGridSource=none`.

Prediction materialization remains reference-first safe: validation and the
complete prediction/uncertainty file are finished before the source reference
JSON is opened. Lineage mismatches fail before reference access.

## Files changed

- `steel_guitar_rag/chord_reader/benchmark.py`
- `steel_guitar_rag/chord_reader/cli.py`
- `tests/test_chord_reader_benchmark_uncertainty.py`
- this handoff

No runtime-grid, model, training, UI, production, calibration, confirmation,
test-corpus, or deployment file is part of this slice.

## Verification

- Benchmark uncertainty, strict benchmark-v2, and factorized suites:
  `119 passed, 3 skipped`.
- Full lineage/runtime/bar integration before the final selector-only follow-up:
  `204 passed, 2 target-Chrome tests deselected`.
- Ruff lint, `py_compile`, and `git diff --check` passed.

Tests cover mandatory CLI lineage input, exact report bindings, loaded cache
array equality, canonical duration equality, cache-manifest identity, and
fail-before-reference rejection for coherent lineage splices. Synthetic tests
may explicitly patch the full verifier and are labeled
`metadata-only-test-fixture-v1`; downstream bar-example consumers reject that
mode.

No real 246-track extraction or benchmark was run by this implementation
slice. Calibration, confirmation, and test remained sealed.

## Operational next step

Run the full lineage attestation in the pinned chord-reader ML environment from
a clean committed source tree. Then pass that exact artifact to the frozen
seven-member development benchmark with `--split development`,
`--beat-grid-source none`, and `--emit-uncertainty`. Any row mismatch is a batch
failure; do not waive it or substitute an older cache/report.

## Safe-to-stage exact paths

- `steel_guitar_rag/chord_reader/benchmark.py`
- `steel_guitar_rag/chord_reader/cli.py`
- `tests/test_chord_reader_benchmark_uncertainty.py`
- `docs/handoffs/task-completions/2026-08-20-2120-20-development-audio-lineage-benchmark-binding.md`

Generated lineage artifacts, predictions, reports, model files, caches, audio,
references, and anything under `tmp/` must not be staged.
