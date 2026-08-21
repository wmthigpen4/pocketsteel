# Beat-cell Stage-1 preflight implementation

Date: 2026-08-21

## Outcome

Implemented the separately frozen development-only exact runtime beat-cell
Stage-1 feasibility preflight, its CLI, fail-closed standalone validator, and
synthetic/adversarial QA. The implementation was not run against the real
benchmark, receipt, prediction, reference, label, calibration, test,
confirmation, or player artifacts.

The implementation copies each exact official receipt `beatCells` row
unchanged, preserves the exact prefix-to-canonical-duration partition, seals
all prediction-only summaries before the first reference read, scores the
same frozen T/U/R/N/E/C/I count and duration partitions, evaluates the same
13 integer gates, and keeps selector fitting and calibration unauthorized.

## Frozen official inputs and denominators

- Receipt file SHA-256:
  `be09f0973aa2ad12c626890f3c7015a50faf7ee24fefe4297ee44f14c79b2053`.
- Internal receipt SHA-256:
  `4f14ed0a3b3436ea8cdd50ae5fef77d0b086efc96c4ec8ec8e7a9af11814834b`.
- Beat track-set SHA-256:
  `a2de02b7419753d41a0ad1e6e85ca14ae5877fc93c2dc7847508ccc7ac004602`.
- Receipt totals SHA-256:
  `46c68e5de9b2cadbe7f0abc03e9a3faaf036d8b06db93f8998a1c0067c448e4a`.
- Exact totals: 246 tracks, 11,234 beat cells, 6,443,258 ms source,
  6,201,472 ms covered, and 241,786 ms excluded prefix.
- Exact independently projected 246-row prediction-identity-set SHA-256:
  `aa6471a3de97ce33f4e2d8f7faaea3d6dd0197e49f2318e17a6917b4a5e38e8e`.
- Dataset beat-cell count/duration denominators: AAM 545/295,509 ms;
  GuitarSet 2,392/1,133,524 ms; IDMT Guitar 2,231/1,293,968 ms; NRGCP
  4,203/2,368,023 ms; Winterreise 1,863/1,110,448 ms.
- GuitarSet disclosures: comp 18 tracks, 1,039 cells, 566,668 ms; solo
  18 tracks, 1,353 cells, 566,856 ms.

## Files

- `steel_guitar_rag/chord_reader/beat_cell_stage1.py`
  - SHA-256 `ed4b7d4dfa64afa7f07f193567e6c26d7e3d594e3b5f50e5ce03658838cc3a96`.
- `scripts/chord_beat_cell_stage1.py`
  - SHA-256 `badc3d2e50c8318676bebbee68e723f05d59a35890ecddd30b4bd3bf8d1f61b9`.
- `tests/test_chord_reader_beat_cell_stage1.py`
  - SHA-256 `ff1751b75cf85d8a03142d9a081f14b635f0336845989ab2edf1100b23c55646`.
- This handoff.

## Security and publication properties

- The official receipt is a required path-backed canonical input and is
  validated with the public strict validator using its exact receipt path,
  parent runtime root, and `verify_sources=True` before any candidate
  prediction or reference leaf access.
- The five top-level input file/stat bindings and the strict receipt are
  revalidated at the atomic publication commit point.
- The output JSON and complete prediction-only summary directory set publish
  atomically to new paths disjoint from all source roots.
- The artifact embeds enough exact reference-free receipt material for its
  standalone validator to recompute receipt, track, topology, totals,
  construction, derived timing, prediction identity, dataset, audit, funnel,
  gate, and decision bindings.
- The validator rejects coherent outer reseals of cells, lineage, derived
  timing, top paths/shapes, nested roots, dataset disclosures, reconciliation
  bindings, candidate identities, and GuitarSet disclosures.
- `selectorUseAllowed=false`, `selectorFitted=false`,
  `calibrationMayOpenOnce=false`, and `calibrationStatus=closed` remain exact
  across their rubric, artifact, and decision envelopes.

## QA

- Focused synthetic/adversarial suite with warnings as errors:
  `40 passed`.
- Adjacent beat-receipt, half-bar, and group/scoring nonbrowser suite:
  `172 passed, 1 deselected`.
- Full chord-reader nonbrowser suite:
  `736 passed, 4 skipped, 3 deselected`.
- Ruff check, Ruff format check, Python compilation, and CLI help all pass.

One initial adjacent command unintentionally collected an installed-Chrome
`test_real_browser_*` case. Its fixture-only Chrome subprocess exited with
`SIGABRT`; no protected benchmark input was involved. The command was
immediately replaced by the explicit nonbrowser run above. No real Stage-1 or
real receipt/reference/prediction run occurred.

## Repository and staging boundary

- Branch: `feature/chord-reader-ssl-v9`.
- Starting HEAD: `b3dce7d35055c698e2ca812a57b5f7df224bebfc`.
- No commit was created.
- Safe-to-stage set is exactly the three implementation/test files above plus
  this handoff.
- Do not stage unrelated worktree content or anything under ignored
  experiment storage.

## Human decision and next lane

The implementation is ready for independent P0/P1 freeze review. If that
review is clean, commit only the exact safe-to-stage set and preregister a
separate official Stage-1 execution lane. That later lane must use new output
paths and the exact frozen sources.

This handoff does not authorize running Stage-1 now, fitting a selector,
opening calibration/test/confirmation, promoting a model, changing player
code, attempting playback parity, or contacting Travis.
