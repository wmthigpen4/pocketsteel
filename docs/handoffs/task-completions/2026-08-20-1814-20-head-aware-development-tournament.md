# Head-aware chord-reader development tournament

## Outcome

The frozen development winner is the explicit mixed-head seven-model ensemble
with uniform global member weights and joint-product blend `0.75`:

- common-head members, in order: legacy multiband TCN seeds 20/21/22,
  legacy multiband pitch-roll TCN seed 20, then weighted joint-root/product
  TCN seeds 20/21/22;
- common-head weights: `1/7` for every member;
- joint-head contributors: member indices `4, 5, 6`, renormalized to `1/3`
  each;
- root is decoded independently and frozen before conditional product evidence;
- no beat or reference-timing oracle.

The winning report is:

`tmp/chord-reader-v9/benchmarks/sealed-v2-development/`
`sealed-v2-mb-mix-l4-jrp-pw-u3-u7-b075/report.json`

Report SHA-256:
`eb2df218ac6255e1b57738519cfafcc3cf688e3bbdc5b865a26f789726127aa0`.

It binds clean source revision
`54703e7ddd23901c3ec40551f3ab6c220f95d01f`, 246 development tracks,
6,083.656829 seconds, the frozen multiband cache and feature specification,
all seven ONNX member hashes in exact order, both weight policies, blend,
decoder hash, track/reference/timing hashes, and 246 prediction hashes.

## Development results

| Metric | Legacy four-way | Winner | Change |
|---|---:|---:|---:|
| Root weighted recall | 82.90% | 83.04% | +0.14 pp |
| Product weighted recall | 73.20% | 76.47% | +3.27 pp |
| Detailed weighted recall | 64.05% | 66.17% | +2.11 pp |
| Boundary F1 | 76.28% | 78.33% | +2.05 pp |
| Sequence edit rate (lower is better) | 31.25% | 24.42% | -6.83 pp |

GuitarSet accompaniment results improved without the root regression seen in
the standalone joint models:

| Metric | Legacy four-way | Winner | Change |
|---|---:|---:|---:|
| Root recall | 90.66% | 90.80% | +0.14 pp |
| Product recall | 59.81% | 66.53% | +6.72 pp |
| Detailed recall | 55.17% | 63.35% | +8.17 pp |
| Exact dominant-quality recall | 17.26% | 56.57% | +39.31 pp |

The winner passed every predeclared architecture gate, including the aggregate,
GuitarSet accompaniment, dominant, sequence, and per-corpus non-regression
guards. The group-balanced and blend-1 alternatives were rejected according to
the frozen ranking and corpus-safety rules; no post-hoc weight or blend search
was added.

## Why this is not a 98% claim

The report is intentionally `developmentOnlyExperiment: true` and
`promotionEligible: false`. At the aggregate bar operating point near 50%
coverage it reaches 1,205/1,207 correct bars (99.83% empirical precision,
99.50% one-sided 95% Wilson lower bound). GuitarSet remains the blocker:

- at the common high-precision threshold, GuitarSet coverage is only 9.55%;
- at least 25% GuitarSet coverage, precision is only 132/150 = 88.0%;
- the current frozen policy requires at least 98% empirical precision and the
  full support requirement.

The reader therefore has a materially stronger architecture, not a certified
98%-accurate product. Calibration and confirmation remain closed, and Travis
must not be asked to review outputs yet.

## Data-access statement

Only the sealed development projection was decoded and scored. The cache
benchmark selected and file-verified development artifacts before inference;
there was zero train/calibration ID overlap, no test rows in the derived
protocol, and no beat/reference oracle. Earlier mechanical GuitarSet parser and
artifact-seal reads are documented in their own handoffs and must not be
described as literally never opened; no calibration outcomes were scored or
used in this tournament.

## Next work

Freeze this architecture while adding reference-free uncertainty telemetry:
separate root/product probabilities and margins, per-member disagreement,
boundary evidence, and acoustic observability. Train any selective-risk model
only from grouped out-of-fold predictions, with composition families kept in a
single fold. Do not open calibration until the feature set, selector,
architecture, and score are frozen and the development support gates pass.

## Files and staging

This handoff is the only tracked file created by the tournament. Models,
predictions, and reports remain ignored under `tmp/chord-reader-v9/` and must
not be staged.
