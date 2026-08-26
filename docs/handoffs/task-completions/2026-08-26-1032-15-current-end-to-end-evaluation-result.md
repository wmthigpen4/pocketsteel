# Current chord-reader development evaluation result

The bounded evaluation is complete. The corrected report is stored outside git at
`../tmp/chord-reader-v9/experiments/current-end-to-end-development-v1/corrected-report.json`.
Its canonical artifact SHA-256 is
`c3482c07baa130c97eeba7d463df4d23c02739c526d6ea170720ceb9fe48cc7f`.

## Frozen result

- Evaluation population: 623 eligible bars from 55 development tracks.
- Legacy dominant-product reproduction: 498/623, or 79.94%.
- Current displayed dominant-product accuracy: 497/623, or 79.78%.
- Raw engine time-aligned product recall: 83.08% across 982.89 annotated seconds.
- Current bar-display time-aligned product recall: 81.53%.
- Current bar-display time-aligned root recall: 84.71%.
- Current bar-display time-aligned major/minor recall: 83.27%.
- At displayed confidence >= 0.90: 265/270 correct, or 98.15% precision
  at 43.34% coverage.
- At displayed confidence >= 0.95: 161/161 correct, or 100% precision
  at 25.84% coverage.
- At displayed confidence >= 0.98: 32/32 correct, or 100% precision
  at 5.14% coverage.

## Dataset product recall for the current display

- AAM: 98.09%.
- GuitarSet: 51.18%.
- IDMT Guitar: 90.35%.
- NRGCP: 91.02%.
- Winterreise: 79.84%.

## Structural result

- Phase status was accepted on 4/55 evaluation tracks and unresolved on 51/55.
- Two tracks received a nonzero phase shift.
- The display produced 1,102 musical bars, including 185 two-chord bars:
  113 supported and 72 explicitly uncertain.
- The readability cleanup did not improve chord identity on this split. Compared
  with the raw engine, bar aggregation reduced time-aligned product recall by
  1.55 percentage points. The phase-applied display was 0.42 points below the
  unshifted display.

## Claim decision

The result supports describing the system as a promising expert-assist workflow:
its fixed 90% confidence region was 98.15% correct over 43.34% of the evaluated
bars. It does not support describing the generator as world-class today. Overall
accuracy remains about 80%, GuitarSet remains near 51%, and no independent bar-
downbeat annotations were available to certify the new timing logic.

Travis's 15-song review is therefore not ceremonial. It is the independent,
country-specific evidence needed to determine whether the high-confidence behavior
transfers and whether recurring errors can be corrected systematically.
