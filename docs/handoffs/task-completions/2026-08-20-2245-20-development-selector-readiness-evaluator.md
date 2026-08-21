# Development-only chord selector readiness evaluator

## Task summary

Implemented a new, additive development-only evaluator for the frozen chord-bar
selector. The exact CLI is:

```text
.venv/bin/python scripts/chord_bar_selector_readiness.py \
  --examples <exact-development-examples.json> \
  --selector <exact-development-selector.json> \
  --group-manifest <exact-development-groups.json> \
  --output <NEW-development-readiness.json>
```

The evaluator does not accept a threshold, gate override, dataset-count
override, or promotion option. It accepts only canonical JSON files whose
envelopes are sealed as development-only and promotion-ineligible. All three
envelopes are checked before nested artifact access; selector
`training.split` must also be exactly `development`.

Before this module reads OOF rows directly, it calls the complete
`validate_bar_selector_artifact` validator. It then calls
`train_bar_selector` again on the exact examples artifact and requires object,
canonical, and canonical-rendered byte equality with the supplied selector.
The examples/selector source hashes are joined exactly, including both
`sourceGroupManifestSha256` bindings. The confidence-group manifest's track,
track-set, and manifest hashes are independently recomputed.

Readiness also independently requires the reviewed real-run group shape rather
than trusting an upstream command invocation: 246 tracks and 169 confidence
groups, with AAM `2 x 1`, GuitarSet `3 x 12`, IDMT Guitar `6 x 8`, NRGCP
`156 x 1`, and Winterreise `2 x 2`. Cross-dataset confidence groups are
forbidden for this explicit-empty derivative-registry run. The exact shape is
part of the frozen rubric and has its own canonical SHA-256.

Every OOF `exampleKey` must join exactly once to one source example, the exact
audio-lineage projection dataset, and the exact group-manifest track role and
confidence group. Keys are unique; probability and weight are finite; labels
and missing-confidence flags are boolean; weights are positive; every group
stays in one outer fold and sums to OOF weight one. All five folds and both
emitted GuitarSet roles (`comp`, `solo`) are mandatory diagnostics.

The evaluator validates the exact certification-only dataset determinacy audit
for `aam`, `guitarset`, `idmt_guitar`, `nrgcp`, and `winterreise`, including all
row/self/set hashes and aggregate sums. It proves `R = T - U`, `E = R - N =`
joined OOF count, and missing legacy confidence remains an audit-only subset
inside `E`. GuitarSet end-to-end coverage uses only
`selector.training.datasetLabelDeterminacyAudit[guitarset].referenceDeterminateBarCount`;
it never substitutes emitted examples.

The sole descriptive cutoff is the existing selector precision-coverage point
whose `targetCoverage` is exactly `0.50`. Its
`minimumProbabilityAtDescriptivePoint` is used with the inclusive rule
`probability >= cutoff`, preserving the entire tie block. The evaluator
recomputes and requires exact canonical agreement for the stored grouped log
loss, Brier score, AURC, and every frozen tie-block curve point at
`[.05, .10, .20, .30, .40, .50, .60, .75, .90, 1.0]`.

The immutable development gates are:

- `R/T >= 0.75`;
- aggregate accepted count `>= 150`;
- aggregate end-to-end micro coverage `A/R >= 0.50`;
- aggregate micro precision `>= 0.98`;
- aggregate one-sided 95% Wilson lower bound `>= 0.98`, with
  `z = 1.6448536269514722`;
- aggregate group-balanced conditional coverage/precision `>= 0.50/0.98`;
- GuitarSet accepted count `>= 30` at the same cutoff;
- GuitarSet end-to-end micro coverage `A_G/R_G >= 0.25`;
- GuitarSet micro precision `>= 0.98`;
- GuitarSet group-balanced conditional coverage/precision `>= 0.25/0.98`.

The GuitarSet Wilson bound is disclosed but is not a gate. AAM and IDMT Guitar
same-cutoff disclosures are mandatory. The artifact also contains fixed-decile
micro and group-weighted reliability/ECE; micro and grouped OOF metrics;
correct/incorrect probability quantiles; accepted metrics by fold, dataset,
and GuitarSet comp/solo; accepted-group concentration; feature missingness and
all-missing audit; final-refit standardized absolute-z quantiles and fractions
above 3 and 5; and missing-legacy-confidence subset performance. Numeric drift
diagnostics are disclosure-only and have no invented cutoff.

Exact end-to-end denominators exist only for the aggregate and dataset strata.
Fold and GuitarSet comp/solo diagnostics report their emitted conditional
denominators and explicitly declare end-to-end coverage unavailable because
the sealed inputs do not stratify excluded reference-determinate bars by fold
or role. No denominator is inferred, and this known unavailability is not a
readiness failure; absent emitted folds or either GuitarSet role is.

Only valid inputs and joins plus every numeric gate and complete mandatory
diagnostic produce `developmentReadinessPassed=true` and
`calibrationMayOpenOnce=true`. Every other evaluated result keeps calibration
closed with stable exact reason codes. The output always remains
`developmentOnly=true`, `promotionEligible=false`, and
`operatingThreshold=null`; the descriptive cutoff is explicitly not a
calibration or production threshold.

All input paths, file bytes, canonical objects, claimed artifacts, the rubric,
every joined OOF row, diagnostics, decision, output path, and complete output
are hash-bound. Input inode/content bindings are rechecked inside the output
publication commit. Output publication walks/creates the absolute parent using
retained no-follow directory descriptors, writes and fsyncs a private inode,
links only to a new name, verifies exact round-trip bytes plus the visible
parent inode/path, and performs inode-owned rollback on every failure.

No real/generated development artifact, model, audio, reference, calibration,
test, confirmation, private source, browser, player, or Travis input was opened
or run while implementing or testing this evaluator.

## Files changed

- `steel_guitar_rag/chord_reader/selector_readiness.py` (new)
- `scripts/chord_bar_selector_readiness.py` (new)
- `tests/test_chord_reader_selector_readiness.py` (new)
- `docs/handoffs/task-completions/2026-08-20-2245-20-development-selector-readiness-evaluator.md` (new)

No active bar-example, bar-selector, experiment-driver, benchmark, runtime,
model, corpus, player, UI, deployment, auth, or production file was edited by
this task.

Frozen SHA-256 values:

- `steel_guitar_rag/chord_reader/selector_readiness.py`:
  `adc6d4ede545d37653e6a1a96ac897fff5feea08a06edc802279b3e02b76bb73`
- `scripts/chord_bar_selector_readiness.py`:
  `753653634ceb364e8043a6034ac258a51c9dd65761fc0b03941b50ee801f6a11`
- `tests/test_chord_reader_selector_readiness.py`:
  `f76a33c13ba5276499ebc02880ed08b3dbae8b65e848fee88b1e770a51e84478`
- frozen readiness rubric canonical SHA-256:
  `ba6ac408facf8687f70bfd97f182dd90f7dd04d3f58d70ae9fc98e17a6b06016`
- reviewed 246/169 group-shape canonical SHA-256:
  `41efe198522b17708835ffb67c7dde0ace316506808104884db2c2c6673c6436`

The handoff's own final file hash is reported outside this self-referential
document.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_chord_reader_selector_readiness.py`
  - `11 passed`
- `.venv/bin/python -m pytest -q tests/test_chord_reader_selector_readiness.py tests/test_chord_reader_bar_selector.py tests/test_chord_reader_bar_examples.py tests/test_chord_reader_selector_development.py`
  - `183 passed`
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/selector_readiness.py scripts/chord_bar_selector_readiness.py tests/test_chord_reader_selector_readiness.py`
  - passed
- `.venv/bin/ruff format --check steel_guitar_rag/chord_reader/selector_readiness.py scripts/chord_bar_selector_readiness.py tests/test_chord_reader_selector_readiness.py`
  - passed
- `.venv/bin/python -m py_compile steel_guitar_rag/chord_reader/selector_readiness.py scripts/chord_bar_selector_readiness.py tests/test_chord_reader_selector_readiness.py`
  - passed
- `git diff --check`
  - passed
- Independent final re-audit:
  - no remaining P0/P1;
  - direct unmocked canonical write/read followed by
    `_validate_reproduction` passed.

Focused adversarial coverage includes the exact passing decision; fixed
same-cutoff GuitarSet closure; exact GuitarSet `R_G` distinct from emitted
examples; canonical sort-keys feature mapping projection; protected-split
preflight before validation/training/nested access; mismatched source group
hash; resealed smaller five-dataset run; non-unit group weight; missing and
unclassifiable GuitarSet role closure; selector reproduction mismatch; existing
output collision; in-place input mutation before commit; retained-dirfd output
parent rename/recreate after link with owned rollback; and CLI receipt after
successful atomic publication.

The integrated selector/driver tests also exercise canonical `sort_keys=True`
JSON write/read followed by the real unmocked selector trainer. This prevents
JSON object-key ordering from changing the estimator's explicit
`BAR_FEATURE_NAMES` projection.

## Risks

Risk is medium-low. The implementation is additive, development-only, and
cannot open calibration/test/confirmation or promote a selector. Its decision
is meaningful only for the exact sealed input family and frozen 246/169 run
shape. Canonical hashes are integrity commitments, not signatures or external
authentication.

The evaluator intentionally retrains the selector, so the command can take as
long as deterministic nested grouped training. Any reproduction, validation,
join, metric, shape, file-stability, or publication mismatch fails without a
readiness artifact.

The fold/role end-to-end denominator limitation is explicit and non-gating
because the predeclared numeric gates use only exact aggregate/dataset
denominators. Adding exact excluded-bar fold/role strata later would require a
new reviewed artifact schema and rubric version, not a silent reinterpretation.

## Human decision needed

No decision is needed to exact-path stage this isolated evaluator. Running it
on the real sealed development outputs is the next authorized development-only
step. Calibration must remain sealed unless the resulting exact artifact says
both `developmentReadinessPassed=true` and `calibrationMayOpenOnce=true`.

This readiness artifact is not itself promotion approval, an operating
threshold, calibration evidence, held-out confirmation, public-song proof, or
authorization to contact Travis.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/selector_readiness.py`
- `scripts/chord_bar_selector_readiness.py`
- `tests/test_chord_reader_selector_readiness.py`
- `docs/handoffs/task-completions/2026-08-20-2245-20-development-selector-readiness-evaluator.md`

## Files that must not be staged under this handoff

- Concurrent edits to `bar_examples.py`, `bar_selector.py`,
  `selector_development.py`, their tests, and their earlier handoffs; those
  belong to their own exact-path integration slices.
- Generated examples, selector, group, readiness, benchmark, prediction,
  timing, summary, model, feature, audio, reference, calibration, test,
  confirmation, private, browser, player, or Travis artifacts.

## Recommended next lane

Lane 01 should exact-path review and commit these four files after the final
independent evaluator audit. The development experiment lane may then run this
CLI only after the exact 246-track examples, selector, and group artifacts have
successfully published. The next action must follow the emitted readiness
decision exactly; no gate or cutoff may be changed after viewing results.

## Commit readiness

Ready for exact-path staging after final independent audit. This task was
explicitly instructed not to edit active bar/driver files and did not do so.
