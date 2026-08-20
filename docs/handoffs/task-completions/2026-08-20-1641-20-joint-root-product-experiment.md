# Optional joint root/product factorized experiment

## Task summary

Implemented the bounded v9 matched experiment without training or evaluating a model. The factorized model can now opt into a 49-state auxiliary head ordered as `N`, then twelve chromatic roots for each of major, minor, dominant, and minor-seventh. The legacy seven heads remain the first 90 outputs; the optional head is appended at outputs 90–138.

Training derives the joint target from train-window root and product arrays after pitch-roll transposition, adds configurable joint cross-entropy, and can apply train-only inverse-square-root product-class weights to both direct product CE and the corresponding product blocks in joint CE. Joint models now select checkpoints with an explicit development-only direct/joint product blend, defaulting to `0.5`, after freezing each frame's independent root prediction. The training contract and model config bind that blend and record direct product accuracy, raw 49-way joint accuracy, joint-only conditioned product accuracy, and blended selection product accuracy by epoch and dataset. The 90-output path retains its original direct-product checkpoint metric and output contract.

ONNX export detects the config contract, emits either 90 or 139 outputs, records exact optional-head metadata, and verifies ONNX Runtime parity. At inference, the independent root path is decoded first and frozen. For that fixed root only, the decoder can blend direct product log-probability with the matching four joint-head product logits. Blend zero is the direct-product endpoint; blend one is the joint-only endpoint. For a joint model, pitched-product confidence uses the same four-class conditional product space at every blend, including zero, so confidence is continuous across the decoder sweep. Legacy 90-output confidence remains the original five-way direct-head confidence. The blend is included in prediction decoder metadata and decoder/provenance hashes. Old/new ensemble members cannot be mixed.

CLI wiring was added to train, predict, generic benchmark, and factorized-cache benchmark commands. No production player/UI, data, calibration partition, test partition, model weights, or generated benchmark artifact was changed or opened.

## Files changed

- `steel_guitar_rag/chord_reader/factorized.py`
- `steel_guitar_rag/chord_reader/benchmark.py`
- `steel_guitar_rag/chord_reader/cli.py`
- `tests/test_chord_reader_factorized.py`
- `docs/handoffs/task-completions/2026-08-20-1641-20-joint-root-product-experiment.md`

No files were deleted. No model, cache, prediction, or benchmark artifact was generated in the worktree.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_chord_reader_factorized.py`: 62 passed, 3 skipped. The skips are the optional PyTorch/ONNX tests because the default research venv does not include PyTorch.
- `~/Documents/Pocket Steel/tmp/chord-reader-v4/.venv/bin/python -m pytest -q tests/test_chord_reader_factorized.py`: 65 passed. This ran the real PyTorch model test and a real 139-output ONNX export/ONNX Runtime parity test. Two upstream PyTorch exporter/tracer warnings were emitted.
- `.venv/bin/python -m pytest -q tests/test_chord_reader_benchmark_v2.py tests/test_chord_reader_factorized.py`: 71 passed, 3 skipped.
- `.venv/bin/python -m pytest -q tests/test_chord_reader*.py`: 260 passed, 4 skipped, 7 failed in the concurrent, explicitly excluded harmonic-prior slice. All seven failures stop at `steel_guitar_rag/chord_reader/harmonic_prior.py:1375` because `_validate_duration_model` returns more values than its caller unpacks. The joint-root/product and benchmark-v2 suites remain green; this task did not modify the concurrent file.
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/factorized.py steel_guitar_rag/chord_reader/benchmark.py steel_guitar_rag/chord_reader/cli.py tests/test_chord_reader_factorized.py`: passed.
- `git diff --check`: passed at closeout before this handoff.

Focused coverage proves label mapping and inversion, pitch transposition, train-only weight expansion, unchanged legacy parameter tensors and output slicing, 139-output export metadata, exact decoder blend endpoints, immutable roots, joint checkpoint diagnostics and selection-metric binding, continuous joint-model confidence at blend zero, unchanged legacy confidence, prediction decoder-hash binding, CLI dispatch, and fail-closed legacy/joint ensemble incompatibility.

## Integration notes

New training flags:

- `train-factorized --joint-root-product`
- `train-factorized --joint-root-product-loss-weight 0.6`
- `train-factorized --joint-root-product-selection-blend 0.5`
- `train-factorized --product-class-weighting`

New inference/evaluation flag:

- `--joint-product-blend FLOAT` on `predict-factorized`, `benchmark`, and `benchmark-factorized-cache`; allowed range is 0–1.

The first matched development experiment should keep the existing TCN feature cache, split protocol, seed, epochs, augmentation, and dataset balancing fixed:

1. Legacy-head control, no new weighting.
2. Direct product weighting only.
3. Joint head with joint loss 0.6, no product weighting.
4. Joint head with joint loss 0.6 and product weighting.

For candidates 3–4, keep checkpoint selection frozen at its contracted default blend `0.5`, then sweep decoder blends `0`, `0.25`, `0.5`, `0.75`, and `1` on development only. Do not multiply the training matrix by decode blend because the post-training sweep is cache-only. If joint loss 0.6 produces no useful product gain, test 0.3 and 1.0 only for the better weighting condition. Any different checkpoint-selection blend is a distinct training configuration and must be named in the model contract rather than changed during decoding.

Suggested falsifiable advancement criteria on development data:

- at least +2.0 percentage points GuitarSet-comp product score or +10 points dominant recall;
- GuitarSet-comp root score no worse than 0.25 points below the matched control;
- no other development dataset loses more than 0.5 points product score without a documented macro gain;
- repeat the winning configuration with additional seeds before freezing the model and decoder hash for calibration.

The optional TCN head adds 4,753 parameters (`96 × 49 + 49`). Feature extraction and encoder compute are unchanged. The output tensor grows from 90 to 139 floats per frame, so browser feasibility should be measured but the incremental model compute is small.

## Risk assessment

Risk is medium. The implementation is opt-in and legacy contracts have direct regression coverage, but the challenger has not been trained or measured. A full 49-way CE can be sparse, product weighting may overcorrect rare dominant examples, and raw joint logits may have a different scale from the direct product head. The default `0.5` checkpoint-selection blend is now explicit and reproducible, but it remains an experimental choice that must be compared by the later multi-seed development runs before calibration.

Beat-aware segment boundaries still originate from the existing root/mode, direct-factor, boundary, and rhythm evidence. Joint evidence selects product within the already frozen root/span; it does not yet create new segmental boundary candidates. That is intentionally deferred until this experiment proves the joint head contains useful product evidence.

Rollback is to omit all new flags and continue exporting/recognizing the unchanged 90-output contract.

## Human decision needed

No decision is needed to integrate this opt-in implementation. A human/model-selection decision is needed only after the four matched development runs and seed replication. Calibration and test must remain sealed until a single model identity and decoder hash are frozen.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/factorized.py`
- `steel_guitar_rag/chord_reader/benchmark.py`
- `steel_guitar_rag/chord_reader/cli.py`
- `tests/test_chord_reader_factorized.py`
- `docs/handoffs/task-completions/2026-08-20-1641-20-joint-root-product-experiment.md`

## Files that must not be staged as part of this slice

- `steel_guitar_rag/chord_reader/datasets.py`
- `tests/test_chord_reader_dataset_timing.py`
- `steel_guitar_rag/chord_reader/harmonic_prior.py`
- `tests/test_chord_reader_harmonic_prior.py`
- Any generated ONNX, safetensors, feature cache, prediction, benchmark report, audio, calibration/test artifact, corpus, or private data.

Those source/test paths were concurrently present in the shared tree and belong to a separate task; this slice did not author or review them.

## Recommended next lane

Lane 20 should run the four matched TCN training candidates against train/development only, then perform the cache-only blend sweep and dataset/quality confusion audit. Lane 15 should independently verify the winning frozen model and decoder provenance before any calibration opening.

## Commit readiness

Safe to commit with exact-path review. Do not stage the unrelated shared-tree files listed above.

## Suggested next step

`Lane 20: Train the four matched train/development-only TCN candidates in the optional joint root/product handoff, sweep decoder blend on development cache only, report per-dataset root/product/detail scores and dominant confusion, and stop before calibration/test.`
