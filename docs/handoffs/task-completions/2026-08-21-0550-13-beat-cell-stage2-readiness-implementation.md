# Beat-cell Stage-2 readiness implementation

Date: 2026-08-21

## Outcome

Implemented the distinct, development-only beat-cell selector readiness lane
authorized by the committed Stage-2 preregistration. The evaluator admits the
one exact passed Stage-1 result, the one exact beat-cell examples artifact, and
the one exact selector candidate; validates their per-cell joins; performs one
readiness evaluation; and performs exactly one byte-identical reproduction
refit. It publishes a self-contained readiness artifact only at the exact new
path sealed by the authority.

No official/generated/protected experiment input was opened in this lane. No
official selector was fit, no official readiness result was computed, and no
calibration, test, confirmation, player, public-song, Travis, audio,
prediction, or reference input was accessed. No commit was created.

## Frozen public contract

- Readiness schema:
  `chord_runtime_beat_cell_selector_development_readiness_v1`.
- Public functions:
  - `evaluate_beat_cell_readiness(stage1, examples, selector)` for synthetic,
    file-system-neutral fixtures;
  - `validate_beat_cell_readiness_artifact(artifact)` for standalone exact
    structural and semantic validation;
  - `run_beat_cell_readiness()` for the one exact authority-bound file run.
- Public exception: `BeatCellReadinessError`.
- The descriptive point is fixed at exact target coverage `0.50`. Its cutoff
  is the selector curve's `minimumProbabilityAtDescriptivePoint`; acceptance
  is inclusive and retains the complete exact-equal probability tie block.
- The evaluator emits all five dataset disclosures plus GuitarSet aggregate,
  comp, and solo count-and-canonical-millisecond disclosures. Comp/solo have
  no readiness gate, and solo is never authorized for deployment.
- The artifact remains development-only, promotion-ineligible, and
  player-unauthorized. It has no operating threshold. A passing result may
  only set `calibrationMayOpenOnce: true`; it grants no automatic access and
  stops for independent audit.

## Admissions and exact joins

The evaluator invokes the public validators owned by the Stage-1, examples,
and selector lanes. It additionally verifies every eligible C/I cell across
the three artifacts by `(trackId, cellIndex)`, including outcome hash,
classification/label, canonical duration, source beat cell, dataset, role,
GuitarSet role, confidence group, source group row, prediction identity, and
audio-lineage row. OOF rows are one-to-one, sorted, group-fold isolated, and
have exact unit sample-weight mass per confidence group.

The complete official Stage-1 admission projection is mechanically receipt
bound as:

`9819e8a3c639179a04246c53e59ea85627178e33dd6a51d2e412a63082309be9`.

That projection contains the aggregate funnel, all five dataset funnels,
GuitarSet aggregate and comp/solo funnels, the exact eligible per-cell binding
set, endpoint reconciliation audit, and source receipts. Standalone validation
requires the exact receipt. During an official mapping evaluation, the full
Stage-1 artifact is also run through its strict source validator before this
projection is constructed. A canonical self-hash is an integrity receipt, not
a cryptographic signature; source authenticity still depends on the exact
authority-bound input validation performed by the official runner.

Frozen aggregate Stage-1 admissions are `T/U/R/N/E/C/I =
11234/1445/9789/413/9376/7352/2024`, with corresponding canonical-millisecond
totals `6201472/885368/5316104/241755/5074349/4045887/1028462`. Frozen
GuitarSet admissions are `2392/174/2218/158/2060/921/1139` and
`1133524/99325/1034199/83715/950484/437514/512970` milliseconds. GuitarSet
comp/solo reference-determinate denominators are `954/1264` cells and
`513043/521156` milliseconds.

## Readiness gates and diagnostics

The report contains exactly 15 preregistered gates:

- 11 existing count/Wilson/group-balanced gates: aggregate accepted count,
  end-to-end coverage, precision, one-sided Wilson lower bound,
  group-balanced conditional coverage and precision; and the corresponding
  five GuitarSet gates without a GuitarSet Wilson gate;
- four integer cross-product duration gates: aggregate and GuitarSet
  end-to-end time exposure plus duration-weighted micro precision.

Duration never affects training, group-balanced metrics, Wilson, the
probability curve, cutoff, or selector choice. All gate inputs and disclosures
are recomputed from sealed joined rows and the admitted structural
denominators.

Mandatory diagnostics are exactly recomputed by the standalone validator:
fixed probability-decile micro and group-balanced reliability/ECE; micro and
group-balanced log loss, Brier, and AURC; the exact tie-block
precision/coverage curve; correct/incorrect probability quantiles; all five
outer folds, all datasets, and GuitarSet role slices; accepted-group
concentration; feature missingness/all-missing state and standardized absolute
z drift; and the label-side endpoint reconciliation disclosure. Ordered
feature vectors and their mapping hashes are embedded solely to make drift
diagnostics independently reproducible.

## One-shot reproduction and publication

Selector validation is followed by exactly one call to
`train_beat_cell_selector(examples)`. The reproduced selector must be equal as
an object, canonical object hash, canonical rendered bytes, and selector
artifact receipt. Caller-injected reproduction results and retry controls do
not exist.

`scripts/chord_beat_cell_readiness.py` accepts no input/output/cutoff/gate/fold/
feature/dataset/retry option. All paths come from the committed authority.
Publication requires a disjoint new JSON path and uses retained no-follow
directory descriptors, an fsynced private temporary inode, link-only creation,
exact byte/inode round-trip, owned-inode rollback, directory fsync, and parent
inode verification. Exact source bytes and inodes are checked immediately
before the final link and immediately after it; a mutation at either barrier
fails closed and removes the owned output link.

The destination name is re-bound to the owned inode before and after the byte
round-trip, after directory fsync, and immediately before success. A hostile
name swap fails closed, preserves the foreign replacement, and uses retained-
dirfd inode discovery to remove only links to the private inode created by this
publisher, including an attacker-relocated link. Rollback catches
`BaseException` and keys cleanup from the private temporary inode even when
`link(2)` created the canonical hardlink before Python assigned its linked
state, so post-link cancellation cannot strand an owned canonical output. On
success, the temporary alias is removed inside the guarded transaction,
followed by another parent fsync and final absolute-parent plus canonical
name-to-owned-inode verification; `finally` is only the failure fallback.

## Validation and tamper coverage

Synthetic tests cover the exact 0.50 target point and inclusive tie block,
independent duration-gate failures, one-and-only-one reproduction, canonical
JSON feature-key order versus sealed model order, protected-split ordering,
exact Stage-1 per-cell outcome binding, complete Stage-1 admission receipt,
atomic new-path publication, both input-publication barriers, and CLI policy
closure. A destination-name swap regression proves the publisher cannot return
success on foreign visible bytes and does not delete the foreign replacement.
Separate `KeyboardInterrupt` regressions cover the second source callback and
the link-created-before-assignment boundary. A final-temporary-cleanup swap
regression proves that success cannot be returned with a foreign canonical
replacement or stranded owned alias.

Coherently resealed adversarial cases cover fold/dataset/role slice metrics,
feature missingness and standardized-z diagnostics, stored metric
recomputation, Stage-1 stratum metadata, fixed cutoff policy, publication mode,
count/duration audits, reproduction proof, one-shot policy, and final decision.
They also prove that the reliability diagnostic rejects extra policy fields and
that endpoint reconciliation cannot be relabeled as a duration-gate input even
when every enclosing integrity receipt is coherently resealed.

Tests run on the final pre-handoff snapshot:

- `PYTHONWARNINGS=error .venv/bin/pytest -q tests/test_chord_reader_beat_cell_readiness.py`
  - 30 passed.
- `PYTHONWARNINGS=error .venv/bin/pytest -q tests/test_chord_reader_beat_cell_examples.py tests/test_chord_reader_beat_cell_selector.py tests/test_chord_reader_beat_cell_readiness.py`
  - 113 passed.
- `PYTHONWARNINGS=error .venv/bin/python -m pytest -q tests/test_chord_reader_*.py` with the three named real-browser runtime tests deselected
  - 779 passed, 4 skipped, 3 deselected.
- `.venv/bin/ruff check ...` and `.venv/bin/ruff format --check ...`
  - passed for all three owned Python files.
- `.venv/bin/python -m py_compile ...`
  - passed for all three owned Python files.
- `.venv/bin/python scripts/chord_beat_cell_readiness.py --help`
  - exposed only help; no path or policy override exists.
- `git diff --check`
  - passed.

## Files touched

- `steel_guitar_rag/chord_reader/beat_cell_readiness.py`
- `scripts/chord_beat_cell_readiness.py`
- `tests/test_chord_reader_beat_cell_readiness.py`
- `docs/handoffs/task-completions/2026-08-21-0550-13-beat-cell-stage2-readiness-implementation.md`

Implementation SHA-256 values are refreshed after independent coherent-reseal
review patches and listed below.

- core module:
  `8052330874113502d5af3e20209935ed7f56e3e77695019cdc06cf887432fb6a`;
- CLI:
  `cc0c68ff11b654f8e17f4dc9c8a746c88e543be14d8188e2cf1189304e9b77dd`;
- tests:
  `0731dc8e5f982db2a2300b07e6e7256a22e55279fbf716c2cd3947edb63e348f`.

Refresh these hashes after any review patch.

## Human decision needed

No new lane-local decision is needed. The root task already grants autopilot
for the exact scoped commit and one-shot Stage-2 development sequence. Root
must still independently review this frozen implementation and create the
clean commit before exercising that existing authorization. Calibration, test,
confirmation, player changes, public-song evaluation, Travis contact,
promotion, and deployment remain unauthorized.

## Recommended next step

Root should independently review and commit the frozen Lane-A/Lane-B/Lane-C
implementation as one clean scoped change, then run the already-authorized
exact official one-shot development sequence. That execution must stop after
the readiness artifact is published so its admissions, reproduction,
diagnostics, and 15-gate decision can be independently audited.
