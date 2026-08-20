# Development-only mixed joint factorized ensemble

## Task summary

Implemented an explicit, development-only experiment that can combine legacy
90-output factorized ONNX members with optional joint-head 139-output members.
The default ensemble remains fail-closed for mixed output contracts. The new
path requires `allow_mixed_joint_members=True` (CLI:
`--allow-mixed-joint-members`), at least one legacy member, at least one joint
member, and positive total global weight on the joint contributors.

Every common head is averaged across all members with the normalized global
member weights. The joint root/product head is averaged only across 139-output
contributors after their global weights are renormalized within that subset.
The result is one 139-wide tensor that uses the existing frozen-root decoder:
the independent root path is decoded first, then the configured direct/joint
product blend is applied only within that root.

The exact member head types, global common-head weights, joint contributor
indices, joint global weight mass, normalized joint-subset weights, output
contract, and policy schema are bound into the ensemble specification hash,
model provenance, decoder contract, decoder hash, and serialized prediction
files. Benchmark v2 therefore also binds them through each prediction SHA-256,
the prediction-set hash, the ensemble model identity, and decoder-config hash.

The cache benchmark rejects this opt-in for `calibration`, `test`, `all`, or
any split other than literal `dev`/`development` before split validation,
recognizer/model loading, inference, or artifact verification. No generic
benchmark, prediction command, player, or production UI flag was added.
Mixed benchmarking also rejects every beat-grid source except `none` at the
same early boundary, so the experiment cannot enter the reference-timing
segmental path and its frozen-root/direct-joint endpoint contract stays exact.
Mixed reports are also explicitly marked `developmentOnlyExperiment: true`,
include the exact aggregation policy and its hash plus the research-only
reason/split/certification policy, and set `promotionEligible: false`. They
retain the complete benchmark-v2 content/source/model/cache/decoder provenance,
but the strict promotion validator intentionally rejects them.

No model was trained, no benchmark was run, and no corpus, feature cache,
calibration row, or test row was read. A synthetic-feature ONNX Runtime smoke
loaded one existing 90-output export and one existing 139-output development
export solely to verify the mixed runtime contract.

## Files changed

- `steel_guitar_rag/chord_reader/factorized.py`
- `steel_guitar_rag/chord_reader/benchmark.py`
- `steel_guitar_rag/chord_reader/cli.py`
- `tests/test_chord_reader_factorized.py`
- `tests/test_chord_reader_benchmark_v2.py`
- `docs/handoffs/task-completions/2026-08-20-1751-20-mixed-joint-factorized-ensemble.md`

No files were deleted and no generated artifact was written into the worktree.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_chord_reader_factorized.py tests/test_chord_reader_benchmark_v2.py`: 96 passed, 3 skipped. The skips are optional ML dependencies absent from the default venv.
- `.venv/bin/python -m pytest -q tests/test_chord_reader*.py`: 298 passed, 4 skipped.
- `~/Documents/Pocket Steel/tmp/chord-reader-v4/.venv/bin/python -m pytest -q tests/test_chord_reader_factorized.py`: 85 passed with two existing PyTorch ONNX exporter/tracer warnings.
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/factorized.py steel_guitar_rag/chord_reader/benchmark.py steel_guitar_rag/chord_reader/cli.py tests/test_chord_reader_factorized.py tests/test_chord_reader_benchmark_v2.py`: passed.
- `git diff --check`: passed.
- Real ONNX Runtime seven-member synthetic-feature smoke: loaded the exact existing four legacy exports (three sealed TCN seeds plus the sealed pitch-roll model) followed by the three existing weighted joint-head seed exports. All seven member calls received one shared feature-array object; the combined output was finite with shape `(8, 139)`; member types were four `legacy-90` then three `joint-139`; joint contributor indices were `[4, 5, 6]` with weights of one third each; one segment decoded; ensemble SHA-256 was `945df7bb6c034a5bd06c2aaf5c538a3b36045d0e0ea49b289b0bcd8b6660832c`; and decoder SHA-256 was `40ecb236263786014e78771b3fc5a51b1e3ba69b968463d96a51ff9ab603c27d`.

Focused coverage proves default mixed rejection; explicit success; exact global
common-head and renormalized joint-subset arithmetic; root-first product decode;
member-order, weight, ensemble, provenance, decoder, canonical-prediction, and
serialized-prediction hash binding; zero joint-mass rejection; all-legacy and
all-joint opt-in rejection; feature/vocabulary mismatch rejection; finite
shape/frame validation continuity; CLI dispatch; and early
calibration/test/all rejection before protected operations. It also proves the
mixed one-hot joint endpoint exactly reproduces the joint member output and
segments; blend one ignores adversarial direct-product logits for both label
and confidence; product blend cannot move decoded frame roots; confidence is
computed from post-aggregation evidence rather than averaged member
confidences; homogeneous 90/139 ensembles remain bit-exact on the default
path, including an adversarial accepted floating-weight case whose normalized
sum is `0.9999999999999999`; mixed-only joint contributors are the only weights
renormalized by the new policy. Dasheng features are extracted once per audio;
the beat-grid oracle is rejected before protected access; and the development cache
is loaded once for the selected track while unavailable held-out paths are
never opened or offered to artifact verification.

## Integration notes

The development-only cache command is:

```text
benchmark-factorized-cache ... \
  --model LEGACY.onnx \
  --ensemble-model JOINT.onnx \
  --ensemble-weight LEGACY_WEIGHT \
  --ensemble-weight JOINT_WEIGHT \
  --allow-mixed-joint-members \
  --joint-product-blend BLEND \
  --split development
```

Weights remain in `--model`, then repeated `--ensemble-model` order and must
sum to one. The opt-in is intentionally invalid with a single model or a
same-head-only ensemble; use the existing strict path for those cases.

This implementation does not authorize opening calibration/test. A later
development run should compare the mixed ensemble to the frozen same-split v8
and v9 controls and report GuitarSet-comp product/dominant recall plus all
named-corpus regression floors before any architecture is frozen.

## Risk assessment

Risk is medium-low for integration and medium for model selection. Default
behavior and same-head ensembles remain strict and regression-tested. The new
path is opt-in and hard-limited to development cache scoring. Logit scale can
still differ across independently trained members, and a favorable blend on
development can overfit; this code makes that experiment reproducible but does
not establish an accuracy gain.

Rollback is to omit `--allow-mixed-joint-members`, which restores the existing
mixed-contract rejection without changing any model or data artifact.

## Human decision needed

No decision is needed to stage this bounded experimental implementation. A
model-selection decision is needed only after development-only ablations are
scored. Calibration and test must remain sealed until the exact member order,
weights, blend, ensemble hash, and decoder hash are frozen.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/factorized.py`
- `steel_guitar_rag/chord_reader/benchmark.py`
- `steel_guitar_rag/chord_reader/cli.py`
- `tests/test_chord_reader_factorized.py`
- `tests/test_chord_reader_benchmark_v2.py`
- `docs/handoffs/task-completions/2026-08-20-1751-20-mixed-joint-factorized-ensemble.md`

## Files that must not be staged

- Any generated ONNX, model checkpoint, feature cache, prediction, benchmark
  report, audio, corpus, calibration/test artifact, or private data.
- Any unrelated dirty file outside the exact list above.

## Recommended next lane

Lane 20 should run a development-only mixed-ensemble weight/blend ablation
against the already frozen controls. Lane 15 should independently verify the
winning development report and exact provenance before calibration is opened.

## Commit readiness

Safe to commit after exact-path review. This task was explicitly instructed not
to commit.

## Suggested next step

`Lane 20: Using only the development cache, compare the explicit mixed 90/139-output ensemble across a small predeclared member-weight and joint-product-blend grid, report per-corpus root/product/detail/boundary metrics and GuitarSet-comp dominant confusion, then stop before calibration/test.`
