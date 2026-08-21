# Reference-free factorized uncertainty core

## Task summary

Implemented opt-in, reference-free uncertainty telemetry for single and
ensemble factorized chord inference. The default path remains unchanged:
omitting `emit_uncertainty` (or passing `False`) produces the same prediction
mapping and canonical bytes as before.

Emit mode performs one normal inference traversal per member, combines the
member logits once, decodes the prediction, adds all final model/ensemble
metadata, and attaches uncertainty last. Dynamic members therefore call their
session once; fixed-window members call it once per ordinary window, never a
second time for telemetry. Audio feature extraction is also shared with the
prediction and occurs once per track.

The emitted payload is schema
`chord_factorized_uncertainty_v1`. It reports frame-level root and
decoder-effective product probability, margin, normalized entropy, direct vs
joint agreement/Jensen-Shannon divergence, weighted member votes and
disagreement, selected-class probability spread, mutual information, boundary
probability/spread, and four representation-only observability measurements.
It makes no physical bass or polyphony claim.

The implementation is fail-closed. Emit mode rejects reference boundaries and
all beat grids before feature extraction or model inference. It rejects
non-finite or malformed logits, inconsistent frame counts/shapes, missing
joint evidence when a nonzero blend requires it, invalid hashes/contracts, and
all malformed uncertainty schemas, ranges, null rules, member layouts, or
timebases.

No model was trained, no corpus was read, and no calibration or held-out test
artifact was opened in this core task.

## Files changed

- `steel_guitar_rag/chord_reader/factorized.py`
  - Added the immutable inference-bundle container and shared inference path.
  - Added `emit_uncertainty=False` to feature and audio prediction APIs.
  - Added deterministic decoder/runtime/model identity for legacy single
    models without changing default prediction metadata.
  - Added final-root/product path reconstruction for ensemble telemetry.
  - Ensured ensemble metadata is complete before uncertainty hashes attach.
- `steel_guitar_rag/chord_reader/uncertainty.py`
  - Added the frozen schema, formula contract, builders, canonical hashes,
    frame metrics, observability profile, and full public validator.
- `tests/test_chord_reader_uncertainty.py`
  - Added focused coverage for the schema, formulas, endpoints, hash binding,
    traversal behavior, fail-closed contracts, and default compatibility.
- `docs/handoffs/task-completions/2026-08-20-1907-20-reference-free-factorized-uncertainty-core.md`
  - This handoff.

No files were deleted. Other modified/untracked benchmark, CLI, bar-summary,
test, and handoff files in the shared worktree belong to their separate task
owners and are not implicitly included by this handoff.

## Frozen payload and hash contract

The top-level prediction gains these fields only in emit mode:

- `uncertainty`
- `predictionCoreSha256`
- `uncertaintySha256`

`predictionCoreSha256` hashes the canonical prediction after excluding those
three transport fields. The same digest is embedded at
`uncertainty.predictionCoreSha256`; this prevents telemetry from being spliced
onto a different prediction. `uncertaintySha256` then hashes the complete
uncertainty payload, including that cross-link. Canonical JSON uses sorted
keys, compact separators, `ensure_ascii=False`, and `allow_nan=False`.

The model-specific `uncertainty.contractSha256` binds the exact formula/class
contract, shared binding, and ordered member identities. The shared binding
contains the feature kind/count/spec hash, sample rate, decoder contract hash,
model-or-ensemble hash, product blend, ordered common weights, joint member
indices, and normalized joint-contributor weights. It intentionally excludes
track-specific data.

The public `validate_factorized_uncertainty_contract(uncertainty)` recomputes
and validates the full payload, including the contract and member-order hashes,
member provenance and weight derivation, exact timebase, exact frame section
and leaf sets, every frame-array length/range/null invariant, member vote
layout, boundary statistics, observability rules, and the optional prediction
core cross-link. It returns a copy of the validated shared binding for
benchmark/bar consumers.

## Mathematical semantics

- Root and direct product probabilities are softmax probabilities.
- Every member's product evidence is conditioned on the same final ensemble
  root. A legacy 90-output member uses only its own direct product head; a
  139-output member uses its own direct/joint evidence at the configured blend.
- Combined product evidence uses aggregated direct logits plus the aggregated
  joint-contributor head. Mixed ensembles renormalize only the joint subset;
  homogeneous joint ensembles preserve their existing global weights exactly.
- Product blend endpoints are exact: at blend one, direct logits cannot alter
  the product label or confidence, and changing blend cannot move the frozen
  root path.
- Weighted pairwise disagreement is `1 - sum(vote_mass**2)`. Votes are stored
  member-major as `M x T`; spread and mutual information use the common member
  weights.
- Entropy and Jensen-Shannon divergence use natural logarithms, float64-tiny
  probability floors, and explicit normalization recorded in the hashed
  formula contract.
- Boundary model probability is the stable sigmoid of the combined boundary
  logit; member mean/std are computed after each member's sigmoid.
- Honest representation-only observability reports
  `representationRms`, `temporalDeltaRms`,
  `absoluteActivationConcentration`, and `cosineChange` from the already
  extracted feature matrix. Silence-to-silence cosine change is zero.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_chord_reader*.py`
  - `359 passed, 4 skipped` on the final shared tree.
- `~/Documents/Pocket Steel/tmp/chord-reader-v4/.venv/bin/python -m pytest -q tests/test_chord_reader_factorized.py tests/test_chord_reader_uncertainty.py`
  - `105 passed`; this exercised the optional PyTorch export and real ONNX
    Runtime tests. Two existing upstream exporter/tracer warnings were emitted.
- `.venv/bin/ruff check steel_guitar_rag/chord_reader tests/test_chord_reader*.py`
  - Passed.
- `.venv/bin/ruff format --check steel_guitar_rag/chord_reader/uncertainty.py tests/test_chord_reader_uncertainty.py`
  - Passed. `factorized.py` deliberately retains the repository's existing
    formatting to avoid a 900-line formatter-only diff.
- `.venv/bin/python -m compileall -q steel_guitar_rag/chord_reader/factorized.py steel_guitar_rag/chord_reader/uncertainty.py tests/test_chord_reader_uncertainty.py`
  - Passed.
- `git diff --check`
  - Passed.

Focused tests prove exact schema/leaves and N-frame nulls; known entropy,
margin, confidence, Jensen-Shannon, vote, disagreement, MI, standard-deviation,
and boundary math; blend-zero/blend-one and frozen-root behavior; mixed member
head isolation; Unicode-safe canonical hashing; member order and weight
binding; prediction-core cross-link and splice rejection; hash-last ensemble
metadata; one shared feature extraction; one normal dynamic/fixed-window
traversal; silence observability; and NaN, shape, duration, timebase, member,
joint-head, beat-grid, and reference-boundary rejection.

A full repository `pytest -q` was also attempted. Its collection is blocked in
the base research environment by unrelated missing optional dependencies:
OpenCV (`cv2`) and PyYAML (`yaml`) across seven non-chord-reader test modules.
The complete chord-reader and optional ML suites above are green.

## Final real development smoke

The benchmark owner reran both real ONNX smokes after the final full-payload
validator and recognizer-identity contract landed. Both used sealed track
`aam-0001`, split `development`, limit one, and beat-grid source `none`; both
reported `developmentOnlyExperiment: true` and `promotionEligible: false`.
No calibration or held-out test row was opened.

- Single joint model:
  - Prediction core and nested cross-link SHA-256:
    `e2dbc3621feb77e223e26e5949683ab18bad562c5521c635f8107856bd5b8c58`.
  - Uncertainty SHA-256:
    `eae3f2902e5a853520b4eca997b6411494211b000ac750af65fd24326c00003c`.
  - Full prediction/actual file SHA-256:
    `fce040df558689bf230d9df4f4c5fe999ae8ce68ecd028643a00e2779de14522`.
  - Model-specific uncertainty contract SHA-256:
    `645eeedd84f91ef1a37cd355b6e6f9b83a01cd7b8a357e995b0fb898fc8f32e2`.
- Frozen seven-member mixed winner:
  - Prediction core and nested cross-link SHA-256:
    `4963249b5313c786c0715dc10ad2d842046ccbbea6e8b07bbfa539c41dc00d27`.
  - Uncertainty SHA-256:
    `38a59ed170f8b1c8dcb983cf523d9f26b611959eae7f11b204c825874a9d1931`.
  - Full prediction/actual file SHA-256:
    `8254ab78eca518cbeca528f2cf9cbe0a6d5aa49a44462321f4dc6f0b6edf93bf`.
  - Model-specific uncertainty contract SHA-256:
    `55dae3ecb81a97e725466b597aa892e031a33f6cbc7285a39bee1316af2d46b7`.

For both runs the outer core digest equaled the nested cross-link, and the
recorded full prediction digest equaled the actual serialized file digest.

## Risk assessment

Risk is medium-low. The feature is explicit opt-in, hashes bind telemetry to
the exact prediction/model/decoder/member contract, validation is fail-closed,
and default behavior is byte-regression-tested. Telemetry is intentionally
verbose and development-facing; it is not an accuracy certificate, confidence
calibration, or promotion decision.

Rollback is removal of the emit flag, bundle/attach paths, uncertainty module,
and focused tests. The default prediction path remains independently covered.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/factorized.py`
- `steel_guitar_rag/chord_reader/uncertainty.py`
- `tests/test_chord_reader_uncertainty.py`
- `docs/handoffs/task-completions/2026-08-20-1907-20-reference-free-factorized-uncertainty-core.md`

## Files that must not be staged

- Generated ONNX exports, checkpoints, feature caches, predictions, reports,
  audio, corpus files, or private/reference artifacts.
- Any unrelated dirty file outside the exact combined safe-to-stage lists from
  the independently owned core, benchmark, and bar handoffs.

## Commit readiness

Safe to commit as part of the tested combined uncertainty integration after
the real current-tree development smoke and combined staged-diff review agree.
This task was explicitly instructed not to commit.

## Suggested next step

Lane 01 should combine the exact safe-to-stage lists from the core, benchmark,
and bar handoffs, verify the final real development-only smoke and staged diff,
then commit without any generated prediction/model/cache artifacts. The next
model-development lane may use this reference-free telemetry to construct
train/development confidence examples; calibration/test must remain sealed.
