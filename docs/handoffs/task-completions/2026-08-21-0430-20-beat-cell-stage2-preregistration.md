# Beat-cell Stage-2 development selector preregistration

Date: 2026-08-21

## Purpose and authorization boundary

This document freezes exactly one development-only beat-cell selector cycle
after the independently audited exact-runtime-beat-cell Stage-1 pass. It does
not fit a selector, open calibration/test/confirmation, change the player, run
an arbitrary public song, or authorize Travis contact.

The machine-readable authority for this preregistration is:

`docs/handoffs/task-completions/2026-08-21-0430-20-beat-cell-stage2-preregistration.json`

- file SHA-256:
  `674298f9077d3471e00d296dfe0925e2aa278270721544a6b7391b27cdd7cfb4`;
- canonical-object SHA-256:
  `fc8a8cc0ef0c408a068dc59d28d99726bd379e55d7ce9258d51835054d80dca2`;
- exact feature-math projection SHA-256:
  `65fc42417c1b45201e02fe35f140fee541f20608f08fbe6f2d92c127e4009ef2`;
- exact selector-core projection SHA-256:
  `2c0b541418b6360b2e79945375b4638bcc50eb1733894311dedcb9b566f156cf`;
- exact readiness projection SHA-256:
  `81f58801c789370e06104203117331b8e2d487e3055d14b7a1831e1c22b73b18`;
- exact Stage-A/Stage-B projection SHA-256:
  `814902fac2550294ce8e336a39b01db6c9012e628c0fdaeb3a1bfc31e13f0688`
  and `ebf2cf85c1c854a8a9c30d0100bd27343612607b0c3fb440e9512b272cb5ff32`;
- exact one-shot projection SHA-256:
  `450413b12835c8ffa5117ceb41e896b0f1168589ea2a6f48a2b601fa09f78796`.

Canonical JSON means UTF-8, sorted keys, compact separators,
`ensure_ascii=false`, and `allow_nan=false`. Every materialized implementation
projection must equal the corresponding JSON subobject with no missing or
extra field and reproduce these hashes before any official Stage-A input is
opened. The prose explains the policy; the JSON fixes its mechanical values.

The current runtime-bar examples, selector, and readiness schemas must not be
fed beat cells by renaming fields. Beat-cell prediction-only summaries do not
contain the ordered 48 selector features, and the bar pipeline hard-binds bar
timing, label, denominator, feature, and provenance contracts. Such an adapter
would be a semantic and provenance failure. Stage 2 therefore requires new
beat-cell schemas around an exact projection of the already frozen selector
mathematical core.

## Exact admitted Stage-1 result

Only this result may enter the cycle:

- report path:
  `/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/beat-cell-stage1/report.json`;
- report file SHA-256:
  `0263746165db4f7388aa8ae2e8d8f39e7583f0719cde01718bce4bd5d498adec`;
- report canonical SHA-256:
  `50de920799827cee0670faa135ce76d454896511e8e2cc39219049647748281e`;
- report artifact SHA-256:
  `c3019c5dfa7dd5466d18ea4e2ec98b08a2ec77ca925a1a033816963e7d22ab89`;
- decision SHA-256:
  `41c4859f8b5005b824acb222bbdf80bb4baace6c068712bf6d892f5843b52aaa`;
- gate-set SHA-256:
  `e0b96b0ac56ecf4d4609afa38cf8311084f59e3c58affc413dec39e88d960ad0`;
- source-contract SHA-256:
  `b4511d521945db84ab827f6c0207452a950322d964df9354274ee57eb3f9cfa4`;
- track-set SHA-256:
  `71c4b65785a9a6f4b7303b45b27d7eac605cf1b24ca2a078a3df7baba8e9b611`;
- exact receipt artifact/track/totals SHA-256:
  `4f14ed0a3b3436ea8cdd50ae5fef77d0b086efc96c4ec8ec8e7a9af11814834b`,
  `a2de02b7419753d41a0ad1e6e85ca14ae5877fc93c2dc7847508ccc7ac004602`,
  and `46c68e5de9b2cadbe7f0abc03e9a3faaf036d8b06db93f8998a1c0067c448e4a`;
- exact 246-sidecar artifact/file-set SHA-256:
  `bf379a3bcf1601c92771e07529aa411aca0edca9b36f2bb2587db3c2d886dbff`
  and `a4e247adcd4c4ebfac5da9fc65b6c2c7c578ea9377542f9ec1e94f19af3a1312`;
- exact prediction-identity set SHA-256:
  `aa6471a3de97ce33f4e2d8f7faaea3d6dd0197e49f2318e17a6917b4a5e38e8e`;
- exact group track-set/count:
  `16bea714365fcfe5f1c317dbe69a51f51d47cb2cc3435577dc736a482a0e558c`
  and 169 confidence groups;
- exact Stage-1 aggregate count funnel `T/U/R/N/E/C/I`:
  `11234/1445/9789/413/9376/7352/2024`;
- exact Stage-1 aggregate duration-ms funnel:
  `6201472/885368/5316104/241755/5074349/4045887/1028462`;
- exact GuitarSet count funnel:
  `2392/174/2218/158/2060/921/1139`;
- exact GuitarSet duration-ms funnel:
  `1133524/99325/1034199/83715/950484/437514/512970`.

The two independently reproducible sidecar-set formulas use canonical JSON
(`ensure_ascii=false`, `allow_nan=false`, sorted keys, compact separators,
UTF-8) and are frozen as follows:

```text
artifactSet = canonical_sha256(sorted([
  {"trackId": sidecar.trackId,
   "artifactSha256": sidecar.artifactSha256}
  for sidecar in flat regular prediction-only sidecars
], key=trackId))

fileSet = canonical_sha256(sorted([
  {"name": basename,
   "fileSha256": sha256(raw_file_bytes)}
  for each flat regular summary file
], key=name))
```

Stage A must treat the report itself as opaque: it may rehash and stat the exact
path but must not parse it, return it, receive a group/reference/outcome path,
or call the full Stage-1 validator. It independently validates only the exact
reference-free receipt, prediction identities/artifacts, and 246
prediction-only sidecars. Stage B, after the complete feature set commits,
must reproduce the full Stage-1 artifact, all source bindings, outcome rows,
and all 13 passed gates. A missing, extra, relocated, resealed-alternate, stale,
or partially valid input blocks whichever phase first encounters it.

## Fixed output topology

All destinations are new, mutually disjoint, and disjoint from every source
root:

- reference-free feature-set manifest:
  `/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/beat-cell-stage2/feature-set/manifest.json`;
- complete feature-summary directory:
  `/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/beat-cell-stage2/feature-set/summaries`;
- sealed examples artifact:
  `/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/beat-cell-stage2/examples/artifact.json`;
- selector artifact:
  `/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/beat-cell-stage2/selector/artifact.json`;
- readiness result:
  `/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/beat-cell-stage2/readiness/report.json`.

Every publication is new-path-only, canonical, retained-directory-fd based,
and failure-atomic. Input bytes/inodes and exact source roots must be rechecked
immediately before commit. Partial feature sets, orphaned summaries, and a JSON
artifact that references a not-yet-complete set are forbidden.

## Stage A: reference-free beat-cell feature set

Before any Stage-1 outcome row is consulted, build and seal all 11,234 feature
rows for all 246 tracks from only:

- the exact frozen prediction artifacts and uncertainty evidence;
- the exact frozen runtime beat receipt cells;
- the exact 246 prediction-only Stage-1 sidecars;
- exact audio-lineage and prediction-identity bindings.

Stage A does not parse the benchmark report. Each prediction leaf is located
only from the exact full prediction identity embedded in a validated Stage-1
prediction-only sidecar, resolved beneath the pinned benchmark root. The
benchmark report remains an opaque raw-file-hash binding until Stage B.

For each receipt interval `[startMs/1000,endMs/1000)`, compute the same ordered
48 uncertainty statistics named by the frozen bar feature contract, using the
same frame-overlap, boundary-edge, missing-value, product-family, transition,
epsilon, and tie semantics. The interval contract is new and explicitly
beat-cell semantic: no call to the bar summarizer, no full-precision final-end
substitution, no seconds-to-ms reconstruction, and no relabeling as a bar.

The implementation must bind a new beat-cell feature contract. The existing
full bar feature-contract SHA-256
`09e43a50baa00398b16878c381a36335cbe5f217c28e428a5f248e4643ecc8ad`
is source-lineage evidence only: it also binds runtime-bar timing and the
full-precision bar-end rule and therefore cannot attest beat semantics. The
new contract must contain and self-hash an explicit shared-feature-math
projection comprising the ordered 48 names, frame weighting and clipping,
winner-product overlap/tie rule, transition count, product-family encoding,
weighted summary statistics, boundary-frame rounding, edge missingness,
observability summaries, finite/missing policy, and epsilon. A separate
interval projection must bind exact receipt integer-ms half-open cells and
forbid full-precision final-end substitution.
For every cell it must exactly cross-check prediction product, coverage, and
dominance against the frozen prediction-only Stage-1 summary, and bind the
receipt cell hash, prediction/core/uncertainty identity, canonical duration,
construction hash, and feature-row hash. Feature summaries contain no outcome,
reference, dataset, role, group, or correctness field.

The complete Stage-1 prediction summary is separately recomputed with the
frozen `summarize_prediction_cells` implementation and must equal the
sidecar's canonical object exactly, including floats. The 48-feature path
retains the bar feature contract's own `math.fsum` overlap and
`math.isclose(rel_tol=0,abs_tol=1e-9)` tie semantics. Its product must equal
the Stage-1 product exactly; coverage and dominance must match with
`math.isclose(rel_tol=0,abs_tol=1e-9)`. Any mismatch ends the one shot.

A label-mutation test must prove that changing every Stage-1 outcome for any
track cannot change any feature byte, path, row hash, or feature-set hash.

## Stage B: sealed examples join

Only after the complete feature set is committed may the examples join open
the already sealed Stage-1 outcome rows. It must never reopen raw references or
rescore labels. Outcome classes are copied exactly:

- `C` becomes `correct=true`;
- `I` becomes `correct=false`;
- `U` and `N` are excluded.

The examples artifact must emit exactly 9,376 examples and reconcile exactly
to the Stage-1 `E` count and `5,074,349 ms` eligible duration. Each example
binds track ID, cell index, full canonical cell duration, receipt cell hash,
feature-row/summary/set hashes, Stage-1 outcome-row/report hashes, audio-lineage
row, prediction identity, dataset/role disclosure, and exactly one confidence
group. Only the 48 ordered feature values enter the estimator matrix; every
other field is metadata or audit evidence.

The artifact must carry exact aggregate, five-dataset, and GuitarSet comp/solo
count-and-duration label audits. Logical `(trackId,cellIndex)` keys are unique;
every track maps to one group; duplicate audio maps to one group; and no group
may cross a fold. Cell replication is never treated as independent evidence.

`exampleKey` is the canonical SHA-256 of an exact no-extra/no-missing,
label-free Stage-A payload with schema, track ID, cell index, duration
milliseconds, source beat-cell, prediction-identity, feature-row,
feature-summary artifact, feature-set artifact, and audio-lineage-row SHA-256
fields. Outcome, Stage-1 artifact, group, dataset, and role hashes remain
separately validated metadata and cannot affect row order, estimator input, or
probability tie order. The machine-readable authority fixes exact field names
and value sources.

## Stage C: one frozen selector candidate

Train exactly one candidate. The beat-cell selector receives a new semantic
schema and config hash. The current full bar selector config SHA-256
`9691afc0464c90a369e042a8fed3a23fbe53fe0285987c2aa5ba544947b00f67`
is source-lineage evidence only; it cannot attest equality of an unstated
subset. The implementation must construct and self-hash a new exact
selector-core projection containing all of the following:

- exact 48-feature order;
- target `correct:boolean`;
- each confidence group has total weight one, with equal eligible-cell mass
  within that group;
- five outer folds with salt `bar-selector-outer-v1`;
- four inner folds per outer fold with salt
  `bar-selector-inner-v1-outer-{outerFold}`;
- final-refit hyperparameter-selection salt `bar-selector-inner-v1-final`;
- fold-local group-weighted median imputation, weighted mean centering,
  weighted population-standard-deviation scaling, scale floor `1e-8`;
- all-missing training-fold features impute zero and use scale one;
- the exact ordered five-point elastic-net grid:
  `(.01,.25)`, `(.01,.50)`, `(.05,.25)`, `(.05,.50)`, `(.05,.75)`;
- minimum inner group-balanced log loss, with grid order breaking ties;
- exact group-weighted log-loss probability floor `1e-12`, lexicographic
  example-key ordering within equal-probability blocks, and complete-tie-block
  precision/coverage accumulation;
- deterministic trace-majorized gradient-restarted FISTA v2;
- branch-stable exact float64 logistic sigmoid;
- proximal-gradient-mapping L-infinity convergence certificate;
- maximum 3,000 iterations and tolerance `1e-6`;
- precision/coverage targets
  `.05,.10,.20,.30,.40,.50,.60,.75,.90,1.0`;
- no operating-threshold selection.

The new config changes only the interval/outcome/provenance schemas required by
beat cells. Dataset, role, track ID, group ID, duration, outcome audits, and
hashes never enter the estimator matrix. Nested OOF evaluation remains
group-disjoint and deterministic. Nonconvergence or any integrity failure ends
the cycle without another candidate.

## Stage D: frozen beat-cell readiness profile

The evaluator must reproduce the selector byte-for-byte, rejoin every OOF row,
and admit only the exact passed Stage-1 and examples artifacts. It receives a
new beat-cell readiness schema and rubric hash. The full bar readiness rubric
SHA-256
`b55cd06588ed4578bd31dcdb4eee6bdf894cac76ed98fab34ca5e4a516fce850`
is source provenance for the unchanged cutoff and count policies only. The new
rubric uses only the group-balanced precision/coverage point whose target
coverage is exactly `0.50`, takes its
`minimumProbabilityAtDescriptivePoint`, and accepts `probability >= cutoff`
including the complete tie block. The cutoff is a development diagnostic,
never a calibration or production threshold.

Let `A` be accepted eligible cells, `CA` accepted-and-correct cells, and use
the exact Stage-1 end-to-end denominators `R=9,789` and `R_G=2,218`. Retain all
existing count gates:

- aggregate `A>=150`, exact `2*A>=R`, exact `50*CA>=49*A`, and one-sided 95%
  Wilson lower bound `>=.98` with `z=1.6448536269514722`;
- aggregate group-balanced conditional coverage `>=.50` and precision
  `>=.98`;
- GuitarSet overall `A_G>=30`, exact `4*A_G>=R_G`, and exact
  `50*CA_G>=49*A_G`;
- GuitarSet overall group-balanced conditional coverage `>=.25` and precision
  `>=.98`; GuitarSet Wilson remains disclosure-only;
- Stage-1 aggregate and GuitarSet count-and-duration admission gates remain
  passed and exactly reproduced.

These four duration gates are being committed in this preregistration after
the Stage-1 pass and its outcome aggregates were known, but before any Stage-2
feature build, examples join, fit, probability, or cutoff exists. No claim of
unseen Stage-1 labels is made. Their `.50/.98/.25/.98` floors copy the existing
count floors, can only make readiness stricter, and were not selected from
Stage-2 performance. They implement the earlier design concern that a finer
cell topology must not game coverage through short intervals.

At the same fixed cutoff, define `A_ms` as the sum of each accepted cell's full
canonical duration and `CA_ms` as the sum for accepted-and-correct cells. Use
exact Stage-1 reference-determinate denominators
`R_ms=5,316,104` and `R_G_ms=1,034,199`. Add exactly four integer gates:

- aggregate `2*A_ms >= R_ms`;
- aggregate `50*CA_ms >= 49*A_ms`;
- GuitarSet overall `4*A_G_ms >= R_G_ms`;
- GuitarSet overall `50*CA_G_ms >= 49*A_G_ms`.

Zero or invalid denominators fail closed. Duration never changes training
weights, group-balanced metrics, Wilson statistics, probability curves, the
cutoff, or model selection. There is no duration Wilson bound.

Mandatory diagnostics remain fixed probability deciles/ECE; micro and
group-balanced log loss, Brier, and AURC; exact tie-block precision curves;
correct/incorrect probability quantiles; fold/dataset/Guitar role slices;
accepted-group concentration; feature missingness and standardized absolute-z
drift disclosures; and endpoint reconciliation. AAM and IDMT Guitar remain
mandatory dataset disclosures. Guitar comp/solo must additionally disclose
accepted count/duration, conditional coverage, count/duration precision, and
exact end-to-end count/duration coverage at the same cutoff. Role denominators
are fixed by Stage 1: comp `R=954`, `R_ms=513,043`; solo `R=1,264`,
`R_ms=521,156`. There is no comp or solo gate and no solo deployment
authorization.

## One-shot decision and stop conditions

Only one feature set, one examples artifact, one selector candidate, and one
readiness evaluation are allowed. Exactly one deterministic readiness refit
may occur only to prove reproduction; it is not another candidate. There is no
alternate grid, cutoff, fold, feature set, weighting, cell topology, dataset
subset, or same-cycle retry.

Any integrity error, count/duration mismatch, group leakage, nonconvergence,
missing diagnostic, or failed readiness gate closes the cycle. No threshold or
gate may be relaxed after probabilities are observed.

If and only if every gate and diagnostic passes, the readiness artifact may
set `developmentReadinessPassed=true` and `calibrationMayOpenOnce=true`.
Execution must then stop for independent audit and a tracked result handoff;
calibration is not opened automatically. If any gate fails, both remain false
and calibration stays closed.

Regardless of the readiness outcome, test, confirmation, promotion, player
playback, arbitrary-public-song proof, and Travis remain unauthorized. The
known setup-client cache-token mismatch must be repaired and independently
proved in the real player before any later playback claim.

## Implementation and run sequence

1. Implement only synthetic/offline contracts, tests, CLI stages, and handoffs;
   do not open the official Stage-1 labels or prediction leaves during coding.
2. Obtain an independent P0/P1 audit and green focused/full nonbrowser QA.
3. Commit the exact reviewed implementation on a clean tree.
4. Perform a separate metadata-only official run preflight; require all new
   destinations absent and every frozen input hash unchanged.
5. Build and independently audit the complete reference-free feature set.
6. Build and independently audit the single examples artifact without raw
   reference access.
7. Train the single selector candidate once.
8. Run the frozen readiness evaluator once, audit the result, write a tracked
   handoff, and stop.
