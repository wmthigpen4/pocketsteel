# Chord Reader ML v3 Development

## Task Summary

Branch: `feature/chord-reader-ml-v3`

Built a reproducible challenger to the current Play Along v2 chord reader on an isolated development branch. The work includes public-data adapters, leakage-safe splits, frozen v2 and pretrained BTC baselines, a trained browser-sized ONNX student model, benchmark/promotion gates, an off-by-default browser integration with v2 fallback, reviewed-chart tooling for local Steel Guitar Forum pairs, and a sealed ten-song Travis A/B review workflow.

Production remains unchanged. The ML reader is enabled only through `pocketSteel.chordReaderEngine=ml-v3`, and any model/runtime failure immediately returns v2 output.

## Result

Frozen GuitarSet test split: 36 recordings, with every player and comp/solo rendition of the same progression kept in the same split group.

| Metric | Play Along v2 | Student | Gain |
| --- | ---: | ---: | ---: |
| Major/minor WCSR | 0.3928 | 0.5214 | +0.1286 |
| Root WCSR | 0.4062 | 0.5835 | +0.1774 |
| Detailed WCSR | 0.3304 | 0.4726 | +0.1421 |
| Boundary F1 | 0.3558 | 0.5013 | +0.1455 |

The tracked public promotion report passes all applicable public, regression, runtime, and memory gates. Projected four-minute inference is 0.25 seconds; measured peak resident memory is about 340 MB.

The first local forum chart/audio exercise, “City Lights,” showed a provisional +0.058 major/minor WCSR gain over v2. It intentionally failed weak-training admission because independent-reader agreement with the arrangement chart was below 80%. The local audio, PDF, transcription, reference, and output reports remain outside the repository. This one-song result is not used as a promotion claim.

## Implementation

- Added normalization for detailed evaluation labels and conservative learner-facing chord symbols.
- Added GuitarSet and AAM importers; audited and excluded Lo-Fi Chords from supervised training because its metadata archive has no chord progression labels.
- Added deterministic composition-level splits and manifest validation that prevents weak labels or held-out data from leaking into training.
- Pinned the historical BTC Hugging Face revision and SHA-256 of every imported file.
- Trained an 80-epoch, 49-class temporal-convolution student on 264 GuitarSet train recordings and selected it on 60 development recordings.
- Exported a 359,340-byte ONNX model with maximum PyTorch/ONNX error below `0.0001`.
- Added a same-origin ONNX Web Worker and vendored the pinned MIT-licensed runtime assets.
- Added exact v2, BTC, and student prediction/benchmark commands.
- Added reviewed-chart conversion that never derives labels from a challenger.
- Added a deterministic blinded packet and separate answer key for Travis's later ten-song review.

## Files Changed

Source and tests:

- `steel_guitar_rag/chord_reader/__init__.py`
- `steel_guitar_rag/chord_reader/benchmark.py`
- `steel_guitar_rag/chord_reader/btc.py`
- `steel_guitar_rag/chord_reader/chart_reference.py`
- `steel_guitar_rag/chord_reader/cli.py`
- `steel_guitar_rag/chord_reader/datasets.py`
- `steel_guitar_rag/chord_reader/labels.py`
- `steel_guitar_rag/chord_reader/manifests.py`
- `steel_guitar_rag/chord_reader/metrics.py`
- `steel_guitar_rag/chord_reader/promotion.py`
- `steel_guitar_rag/chord_reader/review.py`
- `steel_guitar_rag/chord_reader/student.py`
- `scripts/chord_reader.py`
- `scripts/chord_reader_v2.js`
- `tests/test_chord_reader.py`

Browser/runtime:

- `ui/practice-analysis-client.js`
- `ui/chord-reader-ml-worker.js`
- `ui/models/chord-student-v1.onnx`
- `ui/vendor/onnxruntime-web/LICENSE`
- `ui/vendor/onnxruntime-web/PROVENANCE.json`
- `ui/vendor/onnxruntime-web/ort.wasm.min.js`
- `ui/vendor/onnxruntime-web/ort-wasm-simd-threaded.wasm`
- `package.json`
- `package-lock.json`
- `scripts/check_asset_size_budget.py`

Data/model contracts and reports:

- `chord_reader/datasets/catalog.json`
- `chord_reader/datasets/downloads.json`
- `chord_reader/models/btc-ismir19.json`
- `chord_reader/models/chord-student-v1.json`
- `chord_reader/models/chord-student-v1-export.json`
- `chord_reader/benchmarks/guitarset-v1/v2.json`
- `chord_reader/benchmarks/guitarset-v1/btc.json`
- `chord_reader/benchmarks/guitarset-v1/student.json`
- `chord_reader/benchmarks/guitarset-v1/promotion.json`

Dependencies/docs:

- `pyproject.toml`
- `requirements/chord-reader.in`
- `requirements/chord-reader.lock`
- `requirements/README.md`
- `scripts/check_dependency_locks.py`
- `docs/chord-reader-ml-v3.md`
- `docs/handoffs/task-completions/chord-reader-ml-v3-development.md`

## Tests and Checks

- Focused Python tests: `29 passed`.
- Browser ONNX smoke: synthetic C-major audio executed the tracked ONNX model and returned C.
- Browser client smoke: ML segments snap to v2 timing and preserve the v2 fallback contract.
- Ruff: passed for the new Python package, CLI, and focused tests.
- JavaScript syntax checks: passed.
- Vitest worker suite: `4 passed`.
- Dependency lock check: passed.
- Node audit: zero vulnerabilities at the configured threshold.
- Asset budget: passed, including the explicit 12 MiB ceiling for the ONNX WebAssembly runtime.
- Full Python suite: recorded in the final branch validation after exact-path staging.
- `git diff --check`: passed.

## Risks

- GuitarSet is guitar-only. The student needs broader labeled instrumentation before claiming “any song” robustness.
- The 49-class output vocabulary simplifies chord extensions beyond major, minor, dominant seventh, and minor seventh.
- One provisional SGF pair is not an adequate steel benchmark. Its failed weak-label admission means it contributed no training weight.
- Timing alignment from v2 can favor v2 boundary metrics; the steel promotion gate therefore uses chord-duration recall and requires a broader set plus Travis's blind test.
- The vendored ONNX runtime adds roughly 11.2 MB to browser assets, within its dedicated budget but material for caching.

## Human Decision Needed

No decision is needed to keep developing and evaluating this branch. Before production enablement, provide ten Pocket Steel songs for the sealed Travis packet and approve promotion only if all steel and Travis gates pass.

## Safe-to-Stage Exact Files

Every file listed under “Files Changed” is part of this feature and safe to stage by exact path.

## Files That Must Not Be Staged

- `.venv`
- `tmp/`
- The ignored local chord-reader workspace and all downloaded audio, charts, extracted data, training caches, checkpoints, predictions, and private review material
- `__pycache__/`
- Any unrelated file in the original dirty worktree

## Recommended Next Lane

Lane 15 should curate and freeze the remaining steel-reference set, then generate the Travis packet only after the automated steel gate passes. Lane 01 owns any later merge. Lane 12 must not deploy or enable the feature without explicit authorization.

## Commit Readiness

Ready for an exact-path feature-branch commit after the final full-suite and staged-asset checks pass. Not ready for production enablement, merge, or deployment.
