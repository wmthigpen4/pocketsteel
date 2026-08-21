# Fail-closed reference endpoint reconciliation

## Task summary

Implemented the exact label-side reconciliation needed by the sealed
development join without changing runtime duration identity, selector
features, the OOF estimand, or readiness gates.

When a reference omits `durationSeconds` (or declares it as `null`), the bar
example builder first validates the original segment sequence as finite,
nonnegative, strictly positive-duration, chronologically ordered, and
nonoverlapping. It permits an overhang only when all of these stronger
conditions hold:

- exactly one segment exceeds the full-precision prediction/audio duration;
- that segment is the final segment and has the unique maximum end;
- its start is strictly before the prediction/audio duration;
- its original end and the prediction/audio duration map to the same exact
  integer player-canonical millisecond under `floor(seconds * 1000 + 0.5)`.

Only that terminal `end` is copied and clipped to the full-precision
prediction duration. Starts, labels, other fields, segment order, and the
original reference file remain unchanged. An underhang is never extended.
Any adjacent-millisecond overhang, interior/multiple overhang, non-unique
maximum, terminal start at/after audio end, malformed segment sequence, or
declared-duration reference fails closed. The pre-existing exact runtime join
still requires runtime duration to equal the player-canonical millisecond of
the full-precision prediction duration. The reconciliation row additionally
requires that same integer millisecond to equal the audio-lineage row.

A new self-hashed
`chord_bar_selector_reference_endpoint_reconciliation_audit_v1` is sealed at
the examples root. It retains the exact policy; source/reconciled/unreconciled
track counts; exact five-dataset counts; dataset-count-set hash; per-track
rows; row-set hash; total reconciled seconds; maximum reconciled seconds; and
the audit self hash. Each affected row binds track, dataset, original
reference SHA-256, original end, prediction duration, reconciled end,
reconciled seconds, canonical millisecond, and row SHA-256. Every emitted
example from an affected track carries that exact row hash; examples from
unaffected tracks carry `null`.

Selector training validates the complete audit against the audio-lineage
projection and validates the affected/null association for every example. It
retains both the exact audit and source audit hash in the selector training
artifact. Standalone selector validation recomputes the audit's row, set,
count, sum, maximum, and self hashes. Reconciliation fields are not in
`BAR_FEATURE_NAMES`, the numeric matrix, OOF audit rows, label-count
identities, precision/coverage calculations, or readiness gates.

Readiness independently joins every reconciliation row to the exact group
track, dataset, original reference SHA-256, audio-lineage track, and canonical
millisecond. It also validates every emitted example's row/null association
and the selector's retained audit. Input bindings carry the examples and
selector audit hashes. Output diagnostics disclose exact count, per-dataset
counts, sum, and maximum with explicit `estimatorFeature=false`,
`oofMetricInput=false`, `countIdentityInput=false`, and
`readinessGate=false`. No numeric threshold or pass/fail gate changed.

## Exact real-input shape audit

A read-only audit of the already generated 246-track development inputs found
exactly 40 reference endpoints beyond prediction duration. All 40 omit a
declared reference duration, have one unique terminal maximum/overhanging
segment, start that segment before audio end, and share the exact player
canonical millisecond with prediction/audio duration. Their overhangs range
from `0.00004535147392203953` to `0.00007074829928654935` seconds. No
multi-segment relaxation was needed or implemented.

No examples, selector, readiness, calibration, test, confirmation, model,
audio, reference, browser, player, public-song, or Travis output was created
or overwritten by this task.

## Files changed

- `steel_guitar_rag/chord_reader/bar_examples.py`
- `steel_guitar_rag/chord_reader/bar_selector.py`
- `steel_guitar_rag/chord_reader/selector_readiness.py`
- `tests/test_chord_reader_bar_examples.py`
- `tests/test_chord_reader_bar_selector.py`
- `tests/test_chord_reader_selector_readiness.py`
- `docs/handoffs/task-completions/2026-08-20-2334-20-reference-endpoint-reconciliation.md`

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_chord_reader_bar_examples.py`
  - `60 passed`
- `.venv/bin/python -m pytest -q tests/test_chord_reader_bar_selector.py`
  - `70 passed`
- `.venv/bin/python -m pytest -q tests/test_chord_reader_selector_readiness.py`
  - `12 passed`
- Integrated examples/selector/driver/readiness suite:
  - `200 passed`
- Full non-browser chord-reader suite:
  - `617 passed, 4 skipped, 2 deselected`
- Ruff check, Ruff format check, Python compilation, and `git diff --check`:
  - passed

Frozen file SHA-256 values:

- `steel_guitar_rag/chord_reader/bar_examples.py`:
  `1da0c38e74b504edfaebc85d85fb597375ee35507637ec02cacdd128f152906e`
- `steel_guitar_rag/chord_reader/bar_selector.py`:
  `fb16bf87a8a8b9582880051d4dc2cab6db0a1e23a909803b7f71daf3ef333127`
- `steel_guitar_rag/chord_reader/selector_readiness.py`:
  `efe6c72070ab59613a48ce14827ec766b3d9e85b43c7a6c13982faead5837174`
- `tests/test_chord_reader_bar_examples.py`:
  `699a4c24d17af0ff9e1cdd5da27330d089dcc25ba0536b14553d9f9d0fcd5f73`
- `tests/test_chord_reader_bar_selector.py`:
  `8e38d9e6f02373976e4e5f7e00be1092737e8436656a33990bf5e753bc09e9ec`
- `tests/test_chord_reader_selector_readiness.py`:
  `44029f4a5209b3cf053c30c8854eb04ba2c8600dc016bef97b11a80f6c533e15`
- outcome/eligibility contract canonical SHA-256:
  `ff3b65b70ef6782c09e40633d855321e52d5508172d4b15cf765049c12d98d6a`
- selector config canonical SHA-256:
  `3c8bca543e18e0bce17435beb184afae005d4b69733a3f7cb60e3522e3e3aee8`
- readiness rubric canonical SHA-256:
  `b55cd06588ed4578bd31dcdb4eee6bdf894cac76ed98fab34ca5e4a516fce850`

Adversarial coverage includes same-canonical-millisecond clipping, immutable
original reference bytes, adjacent-millisecond rejection, declared-duration
rejection, interior/multiple overhang rejection, exact underhang preservation,
malformed/overlapping reference rejection, audit JSON round-trip, per-dataset
count reconciliation, fully resealed source-audit tampering, per-example row
splicing, fully resealed standalone selector-audit tampering, readiness
reference-SHA source-join tampering, and readiness count/sum/maximum disclosure.

## Risks

Risk is low-to-medium and isolated to the development label join. The rule is
deliberately narrower than a tolerance: it recognizes only the exact observed
unique-terminal shape inside one already frozen player millisecond. A future
different reference shape fails and requires a separately reviewed policy;
this code does not widen itself.

Canonical hashes are integrity commitments, not signatures. Trusted
provenance still depends on the existing exact benchmark, audio-lineage,
runtime, group-manifest, and local builder/validator boundaries.

## Human decision needed

No decision is needed to exact-path stage this isolated fix. The authorized
next action is to rerun only the failed development examples stage at a new
output path or after the parent workflow's exact recoverable cleanup. The
already frozen readiness gates must be applied without alteration.
Calibration, test, confirmation, production promotion, public-song proof, and
contacting Travis remain out of scope.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/bar_examples.py`
- `steel_guitar_rag/chord_reader/bar_selector.py`
- `steel_guitar_rag/chord_reader/selector_readiness.py`
- `tests/test_chord_reader_bar_examples.py`
- `tests/test_chord_reader_bar_selector.py`
- `tests/test_chord_reader_selector_readiness.py`
- `docs/handoffs/task-completions/2026-08-20-2334-20-reference-endpoint-reconciliation.md`

## Files that must not be staged

- Anything beneath `tmp/`, including the generated development experiment.
- Generated summaries, examples, selectors, readiness reports, predictions,
  timing grids, lineage artifacts, audio, references, models, calibration,
  test, confirmation, player, or public-song artifacts.
- Unrelated worktree files.

## Recommended next lane

Lane 01 should exact-path review and commit this fix after the independent
P0/P1 audit. The development experiment lane may then resume at
`build-examples`; selector training and readiness remain contingent on that
stage's exact successful output.

## Commit readiness

No commit was made, as instructed. The listed paths are ready for exact-path
staging after final checks and independent audit complete.
