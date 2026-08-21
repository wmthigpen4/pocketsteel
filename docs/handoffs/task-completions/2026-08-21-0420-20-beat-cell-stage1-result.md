# Exact runtime beat-cell Stage-1 development result

Date: 2026-08-21

## Outcome

The single preregistered exact-runtime-beat-cell development preflight completed
successfully on its first invocation and passed all 13 frozen Stage-1 gates.
This is a valid structural-observability and oracle-support feasibility pass,
not a fitted-selector, calibration, promotion, or player-playback result.

`stage1Passed=true` and
`selectorStageMayRunInNewSealedDevelopmentCycle=true`. The artifact retains
`selectorFitted=false`, `selectorUseAllowed=false`,
`calibrationMayOpenOnce=false`, `calibrationStatus=closed`,
`promotionEligible=false`, and `operatingThreshold=null`. Calibration, test,
confirmation, production, arbitrary-public-song proof, player playback, and
Travis contact remain closed.

## Frozen candidate and execution

- Source revision:
  `2c22beef021c843d25ff4cac10a0660fdb1d77b1`. The live execution session
  recorded a clean worktree immediately before and after the official run.
- Stage-1 source-contract SHA-256:
  `b4511d521945db84ab827f6c0207452a950322d964df9354274ee57eb3f9cfa4`.
- Candidate: the exact official 246-track development output of the frozen
  seven-member mixed-head ensemble.
- Ensemble SHA-256:
  `da73df511651230a5e8ef827c05aefb117710770ee4f994507354747058baedd`.
- Construction: the exact 11,234 integer-millisecond beat cells copied from
  the independently audited runtime receipt, with no interpolation, rounding,
  alternate meter inference, fallback grid, or track removal.
- Scoring: dedicated exact-cell scoring on
  `[startMilliseconds/1000,endMilliseconds/1000)`, preserving the frozen
  overlap epsilon, tie policy, endpoint reconciliation, and `0.75`
  reference-dominance, prediction-coverage, and prediction-dominance floors.
- Split: exact `development`; development-only and promotion-ineligible.

The live execution receipt records that the command intentionally unset
`PYTHONWARNINGS`. The identical reference extraction path had already shown
that Python 3.12 can surface an irrelevant third-party `aifc` deprecation under
warnings-as-errors. Code and synthetic QA had already passed with warnings as
errors; allowing the known warning to abort would have wasted the single
official attempt without strengthening an integrity gate.
`PYTHONDONTWRITEBYTECODE=1` remained set. The same session recorded exit zero,
one atomic publication, and no failed or retried official beat-cell attempt.
These execution facts are operator/session attestations; the artifact-derived
hash, funnel, gate, and publication facts below were independently recomputed.

Run root:

`/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1`

Official result:

`/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/beat-cell-stage1/report.json`

Official prediction-only summaries:

`/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/beat-cell-stage1/summaries`

## Artifact receipts

- Report file SHA-256:
  `0263746165db4f7388aa8ae2e8d8f39e7583f0719cde01718bce4bd5d498adec`.
- Canonical whole-report SHA-256:
  `50de920799827cee0670faa135ce76d454896511e8e2cc39219049647748281e`.
- Internal artifact SHA-256:
  `c3019c5dfa7dd5466d18ea4e2ec98b08a2ec77ca925a1a033816963e7d22ab89`.
- Decision SHA-256:
  `41c4859f8b5005b824acb222bbdf80bb4baace6c068712bf6d892f5843b52aaa`.
- Gate-set SHA-256:
  `e0b96b0ac56ecf4d4609afa38cf8311084f59e3c58affc413dec39e88d960ad0`.
- Track-set SHA-256:
  `71c4b65785a9a6f4b7303b45b27d7eac605cf1b24ca2a078a3df7baba8e9b611`.
- Dataset-set SHA-256:
  `ba1d6e758682914c9d28c71a92950d4b9ccaeab53cecb3dc27a32f98e3ab26a0`.
- GuitarSet comp/solo-set SHA-256:
  `1f0d5fc71f3c27827269742977b5337719c8b29f37e2ab35e606540d1ef60852`.
- Source-group track-set SHA-256:
  `16bea714365fcfe5f1c317dbe69a51f51d47cb2cc3435577dc736a482a0e558c`.
- Source beat-receipt SHA-256:
  `4f14ed0a3b3436ea8cdd50ae5fef77d0b086efc96c4ec8ec8e7a9af11814834b`.
- Endpoint-reconciliation audit SHA-256:
  `39cc78e10ba581b06299f506bd8ca027c1fbb3ac2cdbdac23c427dfda7700af7`.
- Input-bindings SHA-256:
  `8f8c01df18afac33bce7363da6d00aa6a8df507b10f71c7dd48cac075e4f096c`.
- Independent prediction-sidecar artifact-set SHA-256:
  `bf379a3bcf1601c92771e07529aa411aca0edca9b36f2bb2587db3c2d886dbff`.
- Independent prediction-sidecar file-set SHA-256:
  `a4e247adcd4c4ebfac5da9fc65b6c2c7c578ea9377542f9ec1e94f19af3a1312`.
- Independent exact-cell topology SHA-256:
  `8c2137f050580a8cf0a4ad52a06b833673da4b773565e99924a92f55ee93dbfe`.

The atomic publication contains exactly one report and 246 declared canonical
prediction-only JSON sidecars. The sidecars total 15,265,629 bytes. The report
and sidecars are 247 unique same-device regular inodes, all mode `0600` with
link count one; the output directories are mode `0755`. There are no missing,
extra, nested, aliased-input, or temporary entries. The committed validator
returned the report unchanged. An independent read-only audit reproduced all
255 funnels, every sidecar and nested self-hash, all report cross-bindings, and
all 13 exact integer gates. It reported P0 none and P1 none.

## Exact Stage-1 result

Aggregate funnel:

| Unit | T | U | R | N | E | C | I |
|---|---:|---:|---:|---:|---:|---:|---:|
| cells | 11,234 | 1,445 | 9,789 | 413 | 9,376 | 7,352 | 2,024 |
| duration ms | 6,201,472 | 885,368 | 5,316,104 | 241,755 | 5,074,349 | 4,045,887 | 1,028,462 |

GuitarSet funnel:

| Unit | T | U | R | N | E | C | I |
|---|---:|---:|---:|---:|---:|---:|---:|
| cells | 2,392 | 174 | 2,218 | 158 | 2,060 | 921 | 1,139 |
| duration ms | 1,133,524 | 99,325 | 1,034,199 | 83,715 | 950,484 | 437,514 | 512,970 |

Every count and duration identity satisfies
`T=U+R`, `R=N+E`, `E=C+I`, and `T=U+N+C+I` exactly.

## All 13 frozen gates

| Scope | Gate | Observed | Floor | Minimum-unit surplus |
|---|---|---:|---:|---:|
| Aggregate count | R/T | 9,789/11,234 = 87.137% | 75% | +1,363 cells |
| Aggregate duration | R/T | 5,316,104/6,201,472 = 85.723% | 75% | +665,000 ms |
| Aggregate count | E/R | 9,376/9,789 = 95.781% | 75% | +2,034 cells |
| Aggregate duration | E/R | 5,074,349/5,316,104 = 95.452% | 75% | +1,087,271 ms |
| Aggregate count | C/R | 7,352/9,789 = 75.105% | 50% | +2,457 cells |
| Aggregate duration | C/R | 4,045,887/5,316,104 = 76.106% | 50% | +1,387,835 ms |
| GuitarSet count | R/T | 2,218/2,392 = 92.726% | 75% | +424 cells |
| GuitarSet duration | R/T | 1,034,199/1,133,524 = 91.238% | 75% | +184,056 ms |
| GuitarSet count | E/R | 2,060/2,218 = 92.876% | 75% | +396 cells |
| GuitarSet duration | E/R | 950,484/1,034,199 = 91.905% | 75% | +174,834 ms |
| GuitarSet count | C/R | 921/2,218 = 41.524% | 25% | +366 cells |
| GuitarSet duration | C/R | 437,514/1,034,199 = 42.305% | 25% | +178,964 ms |
| GuitarSet support | C | 921 | 30 | +891 cells |

The rubric recomputes each ratio gate as an exact integer cross-product; no
floating tolerance or post-result threshold was used.

## Dataset disclosure

| Dataset | Tracks | T cells | R/T count | R/T duration | E/R count | E/R duration | C/R count | C/R duration |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| AAM | 2 | 545 | 95.41% | 96.00% | 96.54% | 96.73% | 91.35% | 91.54% |
| GuitarSet | 36 | 2,392 | 92.73% | 91.24% | 92.88% | 91.91% | 41.52% | 42.30% |
| IDMT Guitar | 48 | 2,231 | 77.19% | 76.78% | 96.69% | 96.27% | 83.04% | 81.40% |
| NRGCP | 156 | 4,203 | 87.79% | 85.63% | 97.78% | 97.44% | 94.42% | 94.84% |
| Winterreise | 4 | 1,863 | 87.98% | 87.99% | 94.02% | 93.88% | 63.58% | 63.13% |

Dataset rows are mandatory disclosures rather than additional authorization
gates. IDMT duration `R/T=76.78%` is the narrowest analogous dataset margin,
only 1.78 percentage points above the 75% line.

## GuitarSet role disclosure

GuitarSet comp and solo remain mandatory sealed disclosures, not separate
authorization gates.

- Comp, 18 tracks: count/duration `R/T=91.82%/90.54%`,
  `E/R=93.92%/93.29%`, and oracle `C/R=68.97%/66.42%`.
- Solo, 18 tracks: count/duration `R/T=93.42%/91.94%`,
  `E/R=92.09%/90.54%`, and oracle `C/R=20.81%/18.57%`.

Solo is still the central abstention risk. Its high structural determinacy and
prediction eligibility coexist with low correct support. The formal product
estimand intentionally authorizes only GuitarSet-overall Stage-1 gates, so this
does not reverse the pass or compel solo coverage. It does prohibit treating
the feasibility result as a deployable solo-performance claim.

## Improvement over fixed half-bars

The beat-cell pass is structural rather than an apparent correctness gain:

- Aggregate duration `R/T` rose from `69.876%` to `85.723%`, converting a
  `317,735 ms` deficit into a `665,000 ms` surplus. Determinate duration
  increased by `982,735 ms`.
- GuitarSet duration `R/T` rose from `73.239%` to `91.238%`, converting a
  `19,961 ms` deficit into a `184,056 ms` surplus. Determinate duration
  increased by `204,017 ms`.
- Aggregate duration oracle `C/R` changed from `76.262%` to `76.106%`.

Finer beat boundaries isolated reference transitions and repaired the two
half-bar determinacy failures. They did not increase the aggregate oracle
correctness ceiling.

## Interpretation and authorized next lane

The formal prerequisite for a new sealed beat-cell Stage-2 development cycle
is met. That later cycle must be separately implemented, reviewed, committed,
and preregistered before opening any label-bearing Stage-2 input. It must use
this exact cell topology and candidate once, retain track/confidence-group
fold isolation and group-balanced evaluation, and make no alternate grid,
threshold, feature, hyperparameter, dataset, or same-cycle retry after seeing
the result.

The existing runtime-bar examples, trainer, and readiness artifacts do not
accept beat-cell summaries. Renaming schemas or treating repeated cells as
independent bars would be a semantic and provenance error. A dedicated sealed
beat-cell Stage-2 adapter/contract is required before fitting anything.

This result does not open calibration. It does not authorize raw beat-cell
predictions in the player. The runtime receipt's disclosed setup-client cache
token mismatch still blocks browser-cache/player parity and the later
arbitrary-public-song proof. Travis must not be contacted.

## Repository and split safety

Generated artifacts remain beneath ignored `tmp/` paths and were not staged.
The tracked source tree was clean immediately before and after the official
run. The independent artifact audit at that point observed only this newly
created untracked result handoff; the Stage-2 preregistration was written
later. The run was confined to the exact sealed development candidate and
development references. No calibration, test, confirmation, public-song, or
Travis artifact was opened.
