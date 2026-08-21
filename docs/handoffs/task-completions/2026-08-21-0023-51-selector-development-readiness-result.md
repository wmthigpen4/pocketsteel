# Seven-member selector development-readiness result

Date: 2026-08-21

## Outcome

The fixed development-only confidence-selector cycle completed successfully as
an experiment and failed its predeclared readiness rubric. The failure is a
valid performance result, not an integrity or execution failure.

`developmentReadinessPassed=false` and
`calibrationMayOpenOnce=false`. Calibration, test, confirmation, production,
public-song proof, and Travis contact remain closed.

## Frozen candidate

- Architecture: mixed head-aware seven-member multiband ensemble.
- Common-head member weights: uniform `1/7`.
- Joint contributors: members 4, 5, and 6, renormalized to `1/3` each.
- Joint-product blend: `0.75`.
- Ensemble SHA-256:
  `da73df511651230a5e8ef827c05aefb117710770ee4f994507354747058baedd`.
- Benchmark split: exact `development`, 246 unique tracks, no limit.
- Timing: `beatGridSource=none`, `oracleTimingUsed=false`.
- Benchmark source revision:
  `00e2d008903f604fc2164c927fd1c0c135dffd07`, clean.
- Selector/readiness source revision:
  `04b10ffed8a7c3ad7880e3c1963561ad1417745d`, clean.

## Artifact receipts

Run root:

`/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1`

- Development audio-lineage artifact:
  `0359c8eba22f62e7d3318b4bc677f4c6a3d87619dd053c1eeba737cfcfc70072`.
- Development audio-lineage projection:
  `d1f480348a13e358f66c6ce035eb004724c6ae1fb356afcbfe601753b5bb33d7`.
- Runtime-bar manifest:
  `e717f8b2c44f41fc7cd9557796b701225e82d3e2f5e40b66365a21b406f65ab1`;
  file SHA-256
  `9c7c171227610a6364f37888f33b3a98d5f8c16d95fe193416e5e4aee18a37f8`.
- Group manifest:
  `92ae8ad59468c46d469fd0040ccfda12ef6404aa20578715465fb812890f86a4`.
- Final benchmark report file SHA-256:
  `fd9dcf2d36214816fe86282a5dc1f0511b05e32a6eecb419fd710d45bba1ed31`.
- Benchmark prediction-core set:
  `92c92e1ec13e2e3edf88fcb5ed41f9e92741a64654478665c049b535438750ae`.
- Benchmark uncertainty set:
  `9d199449763d2206c404b753f8b4961388fd24400d4cc3cfb4dbf0d149342e5a`.
- Examples artifact:
  `cb9d887f189a1902a85dac0641365f372cd7d8063ef660c0051368b54341a943`;
  file SHA-256
  `69f3a2b240efa4a213c442ce6371375d035753ffaa652b42f2d1daf6f91782ce`.
- Selector artifact:
  `ca4d1e5839a311e2a67b6fe3ae756a6272c6f91992d57a688074e299672aab16`;
  file SHA-256
  `588604e45cd3f112e69cb295a270a22daf484c367a63399c5f00bab52b4dae31`.
- Readiness artifact:
  `2a9bad99e7ef2c767eaa6b567fe8d64af322fe98999bf5a7806a2849626dc5dc`;
  file SHA-256
  `114905344d2879f5652506e0a0fcf76cbf4fc3abe95107b3b4c2313ec3a5e657`.
- Readiness rubric:
  `b55cd06588ed4578bd31dcdb4eee6bdf894cac76ed98fab34ca5e4a516fce850`.
- Readiness decision:
  `6d54041e2262b54c76b900bd241ec651c09ea98a5286ccb2e2c89c3027d275c3`.

All listed receipts were independently recomputed during the final audit.

## Endpoint reconciliation

The examples join initially failed closed because 40 undeclared reference
segments ended 45-71 microseconds beyond exact audio duration while remaining
inside the same player-canonical millisecond. Commit `00e2d008` added a narrow,
asymmetric rule that clips only one unique terminal overhang. It cannot extend
an endpoint, cross a millisecond cell, alter a declared-duration reference, or
change any label inside scored audio.

The sealed audit contains 40 tracks: 36 GuitarSet and four IDMT. Its maximum
clip is `0.00007074829928654935` seconds and audit SHA-256 is
`39cc78e10ba581b06299f506bd8ca027c1fbb3ac2cdbdac23c427dfda7700af7`.
The metadata is label-side provenance only and never enters selector features,
OOF rows, metrics, or gates.

## Selector execution

The first selector invocation failed safely without publishing because the
original plain proximal-gradient solver had not converged after 3,000
iterations. The sealed matrix was finite and valid; Apple Accelerate emitted
spurious matmul status warnings while producing finite, repeatable values.

Commit `04b10ffe` replaced the slow solver with a trace-majorized,
gradient-restarted FISTA implementation and a proximal-gradient stationarity
certificate. It preserved the exact objective, grid, preprocessing, weights,
folds, and maximum iterations. The exact link function is separately bound as
`branch-stable-exact-logistic-sigmoid-float64-v1`.

All 126 fits converged; the maximum was 625 iterations and the final refit used
538. Repeated real runs produced byte-identical selector artifacts. The chosen
grid point remained the first predeclared point: `alpha=0.01`,
`l1Ratio=0.25`.

## Fixed readiness result

Count funnel:

| Scope | T | U | R | N | E |
|---|---:|---:|---:|---:|---:|
| Aggregate | 2,919 | 1,176 | 1,743 | 158 | 1,585 |
| GuitarSet | 618 | 212 | 406 | 71 | 335 |

The fixed descriptive point is the inclusive-tie, group-balanced 50% coverage
point at probability `0.9927280522834526`. It is not an operating or
calibration threshold.

Aggregate at that point:

- accepted: 464;
- correct: 461;
- empirical precision: `0.9935344827586207`;
- one-sided 95% Wilson lower bound: `0.9839336224324062`;
- group-balanced conditional coverage: `0.5004510123362965`;
- group-balanced precision: `0.9995622719069728`;
- end-to-end coverage: `0.2662076878944349`.

GuitarSet at the same point:

- accepted: 39;
- correct: 37;
- empirical precision: `0.9487179487179487`;
- group-balanced conditional coverage: `0.11502105211622726`;
- group-balanced precision: `0.949624632214058`;
- end-to-end coverage: `0.0960591133004926`.

Exact failed gates:

1. reference-determinacy rate: `0.5971223021582733 < 0.75`;
2. aggregate end-to-end coverage: `0.2662076878944349 < 0.50`;
3. GuitarSet end-to-end coverage: `0.0960591133004926 < 0.25`;
4. GuitarSet micro precision: `0.9487179487179487 < 0.98`;
5. GuitarSet group-balanced conditional coverage:
   `0.11502105211622726 < 0.25`;
6. GuitarSet group-balanced precision: `0.949624632214058 < 0.98`.

## Diagnostic interpretation

- The runtime grid is structurally insufficient: 1,051 cells are
  reference-mixed and 125 are reference-uncovered.
- Group-balanced selection is dominated by 112 NRGCP groups out of 125
  emitted groups; NRGCP provides 349/464 accepted bars.
- All 39 accepted GuitarSet bars are comp recordings. GuitarSet solo accepts
  zero bars.
- Fold 3 contains 274/279 correct emitted examples but accepts none at the
  global fixed point, showing extreme-tail scale instability.
- Overall/Guitar/comp/solo diagnostic AUROC is approximately
  `0.916/0.792/0.719/0.577`.
- No threshold on the frozen score can rescue GuitarSet. At the required
  102 accepted bars, the best diagnostic threshold prefix is only 86/102
  correct (`84.31%`). At at least 98% Guitar precision, only nine bars can be
  accepted. These are post-hoc diagnostics and authorize no threshold change.

## Independent verification

The final read-only audit performed 12,169 assertions over canonical files,
self-hashes, source bindings, all 1,585 OOF joins, group/fold weights, stored
metric recomputation, the complete tie block, every gate, diagnostics, and the
decision. Fresh selector training reproduced the supplied object and canonical
bytes exactly. No data-integrity issue was found.

## Next sealed cycle

The next cycle is a one-change, stage-gated development experiment:

1. Split each deployable runtime bar at the exact player midpoint into two
   player-visible chord cells. The boundary is independent of labels and model
   predictions.
2. Before any selector fit, require count- and duration-weighted reference
   determinacy, prediction eligibility, and oracle-correct support floors.
3. Only if Stage 1 passes, build one sealed examples artifact and train once
   with the already frozen selector/rubric. No alternate midpoint, grid,
   cutoff, or hyperparameter search is allowed in the same cycle.
4. Any failure keeps calibration/test/confirmation closed.
5. A future passing candidate must still prove itself on a preregistered
   arbitrary licensed/public-domain song through the exact real-player path
   before Travis may be contacted.

## Repository state

The result artifacts are generated beneath `tmp/` and remain ignored. No
generated artifact is staged or committed. The tracked source tree was clean
at each official benchmark/selector/readiness invocation.
