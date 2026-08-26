# Current chord-reader end-to-end evaluation preregistration

This is a development-only, one-run comparison. It is frozen before current-system
results are calculated. It does not authorize tuning, threshold search, training,
or opening calibration/test material.

## Frozen system

- Product revision: `7336f5dc`
- UI aggregation implementation SHA-256: `452f57fef5996e189d80059da042fddf71d6c1dd5024e171be422e40a8e0c536`
- Phase-anchor implementation SHA-256: `c8c7100dae961e969ffdc6aaa1f873d2d0ac98a117d685ff851ac92ca967852d`
- Current behavior: runtime beat-grid completion, sustained-harmonic phase
  backsolve, count-in/pickup handling, musical-bar aggregation, and no more than
  two displayed chord decisions per bar.
- Phase thresholds and split thresholds are copied exactly from the frozen UI.
  They may not be changed after results are seen.

## Frozen development evidence

- Bar examples SHA-256: `69f3a2b240efa4a213c442ce6371375d035753ffaa652b42f2d1daf6f91782ce`
- Engine benchmark report SHA-256: `059418fd796133e70d3148fdccf978b28214d670dd15da5f6fae355e3ab9bc74`
- Runtime beat receipt SHA-256: `be09f0973aa2ad12c626890f3c7015a50faf7ee24fefe4297ee44f14c79b2053`
- Prior bounded-selector report SHA-256: `bb2a53d00413a8ec036e946adb86f4f483bc40b7f35f67aa55ab314304b68d2e`
- Frozen split: `bounded-consensus-development-holdout-v1`
- Evaluation population: 623 eligible bars from 55 held-out development tracks.
- Expected legacy reproduction: 498/623 chord-product-correct bars (79.936%).
- No BTC or NNLS chord replacement is permitted. Those signals remain
  confidence evidence only.

## Predeclared measurements

The current displayed chord timeline is constructed from the existing engine
segments and the current predicted-grid/phase/aggregation rules. It is compared
only within the same 623 frozen reference-bar windows.

1. **Chord identity (duration weighted):** root, major/minor, and product recall
   of the displayed timeline against the reference timeline.
2. **Bar timing:** percentage of reference bar starts and ends within 250 ms of
   the nearest current displayed bar boundary, plus median absolute boundary error.
3. **Joint bar accuracy:** a bar is correct only when both boundaries are within
   250 ms and the current displayed dominant product equals the reference dominant
   product.
4. **Current UI confidence:** precision and coverage for joint correctness at the
   fixed displayed-confidence thresholds 0.50, 0.64, 0.80, 0.90, 0.95, and 0.98.
   This is not the same confidence estimator as the legacy 99.6% selector and will
   not be presented as a direct replacement for it.
5. **Dataset strata:** AAM, GuitarSet, IDMT Guitar, NRGCP, and Winterreise.
6. **Structural impact:** phase status/count, bars shifted by phase backsolve, and
   split-versus-single display counts.

The implementation must first reproduce the frozen 498/623 legacy count and verify
audio, prediction, timing, and reference hashes. A mismatch is an evaluator defect,
not a model result. One corrected rerun is allowed only for such a defect.

## Claim boundary

This development split has informed prior work, so it cannot certify a
state-of-the-art or "world-class" claim. A strong result may support language such
as "promising" or "possibly world class, pending independent validation." A factual
world-class claim requires an untouched independent evaluation and comparison with
current published systems under the same metric and dataset protocol.
