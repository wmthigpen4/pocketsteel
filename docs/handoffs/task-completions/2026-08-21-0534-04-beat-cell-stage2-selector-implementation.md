# Beat-cell Stage-2 selector implementation

Date: 2026-08-21

## Outcome

Implemented the distinct development-only beat-cell selector lane authorized
by the committed Stage-2 preregistration. The implementation consumes only the
exact `chord_runtime_beat_cell_selector_examples_v1` artifact validated by the
Lane-A owner, projects its 48-key `featureValues` object into the separately
sealed feature-name order, and reuses the exact byte-pinned bar-selector
mathematical core. It does not open official/generated/protected experiment
inputs in tests and does not access calibration, test, confirmation, player,
public-song, Travis, audio, prediction, or reference leaves.

No existing bar-selector source was changed. No selector was fit on official
examples, no readiness decision was made, and no commit was created.

## Frozen public contract

- Selector schema:
  `chord_runtime_beat_cell_correctness_selector_v1`.
- Application schema:
  `chord_runtime_beat_cell_correctness_probability_v1`.
- Public functions:
  - `train_beat_cell_selector(examples)`;
  - `validate_beat_cell_selector_artifact(selector, examples=None)`;
  - `apply_beat_cell_selector(feature_row, selector)`.
- Public exception: `BeatCellSelectorError`.
- The validator returns numeric estimator state, matching the existing bar
  selector's application contract. Supplying `examples` additionally proves
  the exact source artifact, row metadata, label audits, and source-set hashes.
- OOF audit rows have exactly:
  `exampleKey`, `trackId`, `cellIndex`, `durationMilliseconds`, `datasetId`,
  `role`, `guitarsetRole`, `confidenceGroupId`, `outerFold`, `probability`,
  `correct`, and `sampleWeight`.
- Every confidence group is assigned to exactly one outer fold and has exact
  unit OOF mass within `1e-12`. Inner folds exclude the corresponding outer
  holdout and use the frozen salts.
- The selector reports exact count and integer-millisecond duration
  denominators, propagates the complete label-audit object, retains the frozen
  five-row elastic-net grid, and selects no threshold.
- The probability application boundary is split-neutral. It validates one
  exact prediction-only feature row, gates only product non-null plus
  coverage/dominance at `0.75`, and does not use a development track allowlist
  or Stage-1 projection equality. Its output remains development-only,
  promotion-ineligible, player-unauthorized, calibration/test closed, and has
  `operatingThreshold: null` with no acceptance field.

## Provenance and mathematical binding

- Authority canonical SHA-256:
  `fc8a8cc0ef0c408a068dc59d28d99726bd379e55d7ce9258d51835054d80dca2`.
- Feature-math projection SHA-256:
  `65fc42417c1b45201e02fe35f140fee541f20608f08fbe6f2d92c127e4009ef2`.
- Stage-B projection SHA-256:
  `ebf2cf85c1c854a8a9c30d0100bd27343612607b0c3fb440e9512b272cb5ff32`.
- Selector-core projection SHA-256:
  `2c0b541418b6360b2e79945375b4638bcc50eb1733894311dedcb9b566f156cf`.
- Reused `bar_selector.py` file SHA-256:
  `c9d7efcec0ee85d0ee0697a1fe551bb270702bb730b25da3765a72acb475637b`.

Every train, validate, and apply call reloads the committed authority and
rechecks the projection hashes and source-module byte hash before using the
pinned private core helpers. Training uses the frozen nested grouped OOF
folds, group weights, weighted preprocessing, deterministic restarted FISTA,
stable exact logistic link, convergence certificate, probability tie blocks,
`math.fsum` curve accumulation, grid, and tie-breaking behavior.

Canonical JSON feature-object ordering is not treated as estimator order.
The validator requires the exact feature key set and explicitly projects in
the authority's feature-name array order. A canonical render/parse/unmocked
training regression covers this boundary.

## One-shot CLI and publication integrity

`scripts/chord_beat_cell_selector.py` exposes only `train` and `validate` and
accepts no caller-supplied paths, grid, cutoff, fold, feature, weight, selector,
or retry controls. Paths come only from the authority.

The train action rejects an existing canonical selector path before reading
examples or invoking the trainer. Before any fit, the CLI also runs the full
standalone examples validator and requires the examples' Stage-1 file,
canonical-object, artifact, decision, gate-set, track-set, and source-contract
hashes to equal the authority, with exactly 9,376 examples and 5,074,349
canonical integer milliseconds.

Publication uses a retained no-follow directory descriptor, a private fsynced
temporary inode, link-only creation, exact byte round-trip, owned-inode checks,
directory fsync, and absolute-parent inode verification. The initial examples
read captures both bytes and device/inode identity. The same idempotent
snapshot check runs immediately before `link(2)` and immediately after it;
failure before link has zero output visibility and failure after link removes
only owned inodes. After the final parent verification, the canonical output
name must still resolve to the exact linked regular-file inode. Failure scans
the retained parent and removes every discoverable name for that owned inode
while preserving foreign replacements. On success, the private temporary alias
is unlinked inside the guarded transaction, the parent is fsynced again, and
the absolute parent plus canonical name-to-owned-inode binding are reverified
before return; `finally` is failure cleanup only. Validate captures and finally
rechecks bytes and inode for both examples and selector inputs before reporting
success. Byte-identical inode replacement, input mutation, post-link faults,
parent replacement, a final-parent-check destination swap, and a swap during
successful temporary-alias cleanup all fail closed.

## Tests run

- `.venv/bin/pytest -q tests/test_chord_reader_beat_cell_selector.py`
  - 17 passed.
- `.venv/bin/pytest -q tests/test_chord_reader_beat_cell_examples.py tests/test_chord_reader_beat_cell_selector.py tests/test_chord_reader_beat_cell_readiness.py`
  - 113 passed.
- `.venv/bin/pytest -q tests/test_chord_reader_*.py` with the three real-browser
  runtime tests deselected
  - 779 passed, 4 skipped, 3 deselected.
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/beat_cell_selector.py scripts/chord_beat_cell_selector.py tests/test_chord_reader_beat_cell_selector.py`
  - passed.
- `.venv/bin/python -m py_compile ...`
  - passed for all three owned Python files.
- `.venv/bin/python scripts/chord_beat_cell_selector.py --help`
  - exposed only `train` and `validate`.
- `git diff --check`
  - passed at the implementation checkpoint.

Synthetic coverage includes canonical feature-object key sorting, exact
Lane-A examples validation, deterministic object-identical reproduction,
group-disjoint nested folds, unit group weights, count/duration propagation,
OOF metadata, artifact/envelope tampering, non-finite application inputs,
split-neutral application, pre-fit retry refusal, post-link fault rollback,
parent-swap rollback, pre-link zero-visibility rejection, mutation between the
two commit checks, a final-parent-check name swap with foreign preservation and
owned-alias cleanup, a final-temporary-cleanup name swap, byte-identical inode
replacement, final validation-input identity checks, and a fully coherent
examples reseal with the wrong Stage-1 binding rejected before the trainer can
run.

## Estimator authenticity boundary and residual risk

The standalone artifact validator intentionally performs no refit. A canonical
self-hash detects accidental mutation but is not a signature or authenticity
proof; a party able to replace and reseal the whole estimator can construct a
structurally valid development artifact. Performing a coefficient refit inside
validation would spend an unregistered additional fit. The sole
preregistered readiness reproduction therefore owns semantic estimator
identity: it trains once from the exact sealed examples and requires object,
canonical, and rendered-byte identity. An adversarial estimator-only reseal
test confirms that structural/source validation does not refit and that the
readiness reproduction rejects the reseal as non-identical.

The remaining operational risk is the real one-shot optimizer run itself:
convergence and readiness results are unknown until the exact official
examples exist and the already-authorized root execution occurs after review
and clean commit. This implementation does not predict or weaken that result.

## Files touched

- `steel_guitar_rag/chord_reader/beat_cell_selector.py`
- `scripts/chord_beat_cell_selector.py`
- `tests/test_chord_reader_beat_cell_selector.py`
- `docs/handoffs/task-completions/2026-08-21-0534-04-beat-cell-stage2-selector-implementation.md`

Implementation file SHA-256 values before this handoff was added:

- core module:
  `689a31d0eac1f07ec870333fb2994b47eb005ac907c23d14ce7e6a822fb16576`;
- CLI:
  `37bdf4c156495eb6d4d8293fd1201f23db1299c6d397c8e347c00e242f007048`;
- tests:
  `dd6dca6488ffbef946d231d0ca5f372e58fa3e0b85cd3bc885b7c851d38d43dc`.

These hashes must be refreshed after any review patch.

## Human decision needed

No new lane-local decision is needed. The root task already grants autopilot
for the exact scoped commit and one-shot Stage-2 development sequence. Root
must still independently review this frozen implementation and create the
clean commit before exercising that existing authorization. Calibration, test,
confirmation, player changes, promotion, and deployment remain unauthorized.

## Recommended next step

Root should independently review and commit the frozen Stage-2 implementation
as one clean scoped change, then run the already-authorized exact official
one-shot development sequence. That execution must stop after the readiness
artifact for independent audit.
