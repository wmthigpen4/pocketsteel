# Soft-router student integration

## Task summary

Integrated the development-only calibrated soft router with the heterogeneous student recognizer. The recognizer now supports a `soft_router` artifact that is mutually exclusive with the legacy hard `domain_gate`, derives the documented 24 named router features from a multiband texture profile plus normalized expanded/conservative evidence, and applies the calibrated weight to root, per-root conditional quality, and boundary evidence. Root mass is reconstructed separately from quality conditionals so quality evidence cannot move the root.

Invalid artifacts and weights of exactly zero fail closed to the existing expanded path without changing the prediction object. Exact factor endpoints return the original expanded logits at zero and conservative logits at one.

Added `predict_counterfactuals(audio, *, prediction_id=None, router_context=None)`, which runs every expert once and returns `expanded`, `conservative`, and `routerFeatures` without accepting references or labels. Optional `router_context` values are `beatConfidence`, `downbeatConfidence`, and `oodDistance`; omitted values are zero.

## Files changed

- `steel_guitar_rag/chord_reader/student.py`
- `tests/test_chord_reader.py`
- `docs/handoffs/task-completions/2026-08-20-1456-05-soft-router-integration.md`

## Tests/checks run

- `.venv/bin/pytest -q tests/test_chord_reader.py tests/test_chord_reader_routing.py` — 78 passed.
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/student.py tests/test_chord_reader.py` — passed.
- `git diff --check -- steel_guitar_rag/chord_reader/student.py tests/test_chord_reader.py` — passed.

## Risks

- The runtime router has no beat/downbeat estimator wired in this slice, so those two features default to zero unless the caller supplies label-free confidences.
- The 49-state student model has no independent bass output. Its normalized root marginal is used as a neutral bass placeholder for the common router evidence contract; bass is not blended into student decoding.
- A calibrated router artifact still needs development-only counterfactual rows before this path can be enabled in a benchmark or product configuration.

## Human decision needed

None for this isolated implementation. Promotion remains gated on development calibration and sealed evaluation.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/student.py`
- `tests/test_chord_reader.py`
- `docs/handoffs/task-completions/2026-08-20-1456-05-soft-router-integration.md`

## Files that must not be staged

- Generated router artifacts, feature caches, audio, benchmark outputs, private corpora, and unrelated dirty files.

## Recommended next lane

Lane 15 should generate composition-grouped development counterfactual rows with the new API, score both predictions, fit the router from development only, and run one sealed comparison without training on test labels.

## Commit readiness

The focused implementation and tests are ready for exact-path integration after the parent task resolves shared edits in `tests/test_chord_reader.py`. Nothing was staged or committed.
