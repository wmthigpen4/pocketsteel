# Fixed half-bar-cell Stage-1 development result

Date: 2026-08-21

## Outcome

The fixed half-bar-cell development preflight completed successfully as an
experiment and failed its predeclared Stage-1 rubric. The failure is a valid
performance result, not an integrity, execution, or publication failure.

`stage1Passed=false`,
`selectorStageMayRunInNewSealedDevelopmentCycle=false`, and
`calibrationMayOpenOnce=false`. No selector was fitted. Calibration, test,
confirmation, production, public-song proof, and Travis contact remain closed.

The preflight passed 11 of 13 gates. Only the aggregate and GuitarSet
duration-weighted reference-determinacy gates failed. All count gates,
count- and duration-weighted prediction-eligibility gates, count- and
duration-weighted oracle correct-support gates, and the GuitarSet support-count
gate passed.

## Frozen candidate and execution

- Source revision:
  `2e1ba0a8bd0a58afdcd4ace40a66fe92741b712b`, clean.
- Candidate: exact official 246-track development run of the frozen
  seven-member mixed-head ensemble.
- Ensemble SHA-256:
  `da73df511651230a5e8ef827c05aefb117710770ee4f994507354747058baedd`.
- Construction: exactly two canonical-millisecond cells per each of 2,919
  attested runtime bars, using the frozen upper midpoint.
- Scoring: dedicated exact-cell scorer on `[startMs/1000,endMs/1000)`, with
  unchanged `0.75` reference-dominance, prediction-coverage, and
  prediction-dominance floors.
- Split: exact `development`; development-only and promotion-ineligible.

The first invocation used `PYTHONWARNINGS=error` and stopped safely before the
first reference read or any publication when Python 3.12 surfaced the
third-party `aifc` deprecation warning during audio extraction. The identical
frozen command was rerun without promoting third-party deprecations to errors;
no source, construction, score, gate, or label policy changed. Publication then
completed atomically. The failed attempt left neither the report nor summary
directory behind.

Run root:

`/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1`

Official result:

`/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/half-bar-stage1/report.json`

## Artifact receipts

- Report file SHA-256:
  `365d5c538d499c0607eba973e407326d282b3de69346cffc39ddf661fb294e80`.
- Internal artifact SHA-256:
  `ebbd64b0fc14b781a42b93e1295080e5e2d25b00894da47e73bde486233cbaeb`.
- Decision SHA-256:
  `106bb3b8e7a9ed0c3fa37d3ab589aa19495875328829e7687c0aff340d28a5ea`.
- Gate-set SHA-256:
  `fbe8e1a04efa7c8ad4fd03eae5e6aea75f4b26461743c51816c8863892a1fa24`.
- Track-set SHA-256:
  `1d3fc471605f31d2d1dd48730e8217bed7dee99311446e22876e51a9162f6aa7`.
- Source-group track-set SHA-256:
  `16bea714365fcfe5f1c317dbe69a51f51d47cb2cc3435577dc736a482a0e558c`.
- Endpoint-reconciliation audit SHA-256:
  `39cc78e10ba581b06299f506bd8ca027c1fbb3ac2cdbdac23c427dfda7700af7`.
- Prediction-sidecar inventory SHA-256:
  `0c25a8a74df7c8ce96259cb46de63ab58bb317b7a862e95cc4d69ee0ed8af422`.

The inventory contains exactly 246 canonical, regular, non-symlink JSON
sidecars, totaling 6,815,735 bytes, with no missing, extra, or nested entries.
The committed validator returned the official artifact unchanged. An
independent audit reproduced all sidecar hashes, all 5,838 midpoint
partitions, outcome classifications, funnels, source bindings, and gates.

## Exact Stage-1 result

Aggregate funnel:

| Unit | T | U | R | N | E | C | I |
|---|---:|---:|---:|---:|---:|---:|---:|
| cells | 5,838 | 1,374 | 4,464 | 310 | 4,154 | 3,341 | 813 |
| duration ms | 6,201,472 | 1,868,103 | 4,333,369 | 335,776 | 3,997,593 | 3,304,722 | 692,871 |

GuitarSet funnel:

| Unit | T | U | R | N | E | C | I |
|---|---:|---:|---:|---:|---:|---:|---:|
| cells | 1,236 | 214 | 1,022 | 132 | 890 | 408 | 482 |
| duration ms | 1,133,524 | 303,342 | 830,182 | 135,209 | 694,973 | 328,274 | 366,699 |

The two failed gates are exact integer comparisons:

1. Aggregate duration reference determinacy:
   `4 * 4,333,369 = 17,333,476 < 3 * 6,201,472 = 18,604,416`.
   Observed `69.876%`; required `75%`; short by `317,735 ms` of
   determinate duration.
2. GuitarSet duration reference determinacy:
   `4 * 830,182 = 3,320,728 < 3 * 1,133,524 = 3,400,572`.
   Observed `73.239%`; required `75%`; short by `19,961 ms`.

The corresponding count gates pass: aggregate `R/T=76.465%` and GuitarSet
`R/T=82.686%`. Longer cells are disproportionately indeterminate, so the
duration safeguard correctly caught a weakness hidden by cell counts.

Prediction observability is not the structural bottleneck. Aggregate
duration `E/R=92.251%`, and GuitarSet duration `E/R=83.713%`, both pass.
The oracle correct-support upper bounds also pass: aggregate duration
`C/R=76.262%` and GuitarSet duration `C/R=39.542%`. These values are
feasibility ceilings, not deployable precision or selector accuracy.

## Dataset attribution

The diagnostic margins below compare each dataset with the analogous 75%
duration-determinacy line. They are disclosures, not additional official
gates.

| Dataset | Tracks | T cells | R/T count | R/T duration | Duration margin |
|---|---:|---:|---:|---:|---:|
| AAM | 2 | 272 | 95.22% | 95.79% | +61,429.25 ms |
| GuitarSet | 36 | 1,236 | 82.69% | 73.24% | -19,961 ms |
| IDMT Guitar | 48 | 1,070 | 66.26% | 60.35% | -189,558 ms |
| NRGCP | 156 | 2,018 | 79.98% | 70.33% | -110,518.25 ms |
| Winterreise | 4 | 1,242 | 69.24% | 69.68% | -59,127 ms |

The five margins sum exactly to the aggregate `-317,735 ms` deficit. IDMT is
the largest contributor, followed by NRGCP and Winterreise.

## GuitarSet role disclosure

GuitarSet comp and solo remain mandatory sealed disclosures, not separate
authorization gates.

- Comp, 18 tracks: duration `R/T=65.57%`, `E/R=87.29%`, oracle
  `C/R=65.13%`, and `C/E=74.61%`. Comp is 53,413 ms below its analogous
  75% determinacy line and causes the formal GuitarSet duration deficit.
- Solo, 18 tracks: duration `R/T=80.90%`, `E/R=80.81%`, oracle
  `C/R=18.81%`, and `C/E=23.27%`. Solo offsets 33,452 ms of determinacy
  deficit but has very weak correct support.

The solo result is a hallucination/abstention warning, not a reason to compel
coverage. Solo remains an abstention/disclosure domain unless a later,
separately frozen proof establishes safe emissions.

## Interpretation and next sealed cycle

The half-bar hypothesis produced a meaningful structural improvement over the
full-bar development result: count determinacy now clears the fixed floors.
It nevertheless fails because long indeterminate cells still dominate total
duration. A selector or threshold cannot repair `R/T`, so fitting Stage 2 on
this artifact is forbidden.

The recommended next experiment is exactly one new beat-cell Stage-1 cycle,
not a quarter-bar fallback or grid search. Before any label access, it must
freeze and hash a reference-free runtime beat grid, exact player-replayable
rounding, meter and compound-meter semantics, endpoint handling, invalid-grid
failure behavior, and one-cell-per-beat display topology. It must preserve the
same candidate, five datasets, all 13 count-and-duration gates, exact integer
arithmetic, GuitarSet overall authorization, and comp/solo disclosures.

Predeclared abort conditions:

- if an exact reference-free beat grid cannot be replayed by the player for
  every scoped track without labels or prediction outputs, abort before
  labels;
- if any frozen count or duration gate fails, reject the challenger and do not
  fit a selector;
- do not substitute fixed quarter-bars, sub-beat cells, adaptive grids,
  dataset removal, threshold tuning, or a same-cycle retry after seeing the
  result;
- a beat-cell Stage-1 pass may authorize only a new sealed Stage-2 development
  cycle. It does not open calibration or authorize raw beat predictions in the
  player;
- calibration, test, confirmation, arbitrary public-song proof, and Travis
  remain closed until their own previously frozen gates are reached.

## Repository and split safety

Generated artifacts remain beneath ignored `tmp/` paths and were not staged.
The tracked source tree remained clean during the official run and audit. All
opened source, prediction, timing, reference, and sidecar rows were exact
development rows. No calibration, test, confirmation, protected-split, or
additional reference-label artifact was opened.

## Human decision needed

No judgment call can convert this result into a pass. Stage 2 must not run.
The only safe continuation is a separately implemented, reviewed, committed,
and preregistered beat-cell Stage-1 cycle satisfying the abort conditions
above. Travis must not be contacted.
