# Fixed half-bar-cell Stage-1 development preflight

Date: 2026-08-21

## Task summary

Implemented the isolated, sealed Stage-1 feasibility preflight for one exact
official 246-track development candidate. This stage constructs exactly two
fixed canonical-millisecond cells per attested runtime bar and measures only
structural label observability, prediction eligibility, and oracle correct
support. It does not fit a selector, choose a cutoff, open calibration/test,
promote an artifact, inspect a confirmation split, contact Travis, or change
runtime/player behavior.

The CLI is:

```text
.venv/bin/python scripts/chord_half_bar_stage1.py \
  --benchmark <exact-official-development-report.json> \
  --benchmark-root <exact-prediction-root> \
  --audio-lineage <exact-full-development-audio-lineage.json> \
  --runtime-manifest <exact-runtime-manifest.json> \
  --runtime-root <exact-runtime-root> \
  --group-manifest <exact-group-manifest.json> \
  --group-root <exact-reference-root> \
  --summary-output-root <NEW-summary-directory> \
  --output <NEW-stage1.json>
```

No real Stage-1 run was performed while implementing or testing this slice.

## Frozen construction and source scope

- The preflight accepts only the exact official winner-seven development run:
  246 tracks and 169 reviewed confidence groups across AAM, GuitarSet, IDMT
  Guitar, NRGCP, and Winterreise.
- Exact report file/canonical/track and prediction artifact/core/uncertainty
  set hashes, ensemble, runtime manifest/analyzer, group manifest, audio
  lineage/projection, reviewed dataset shape, and full shared
  prediction/runtime binding are sealed in `STAGE1_SOURCE_CONTRACT`.
- The fixed structural denominators are derived again from the exact runtime
  `barCount` rows joined to exact group dataset/role rows. They are source-shape
  invariants, not performance expectations: aggregate `2919/5838` parent
  bars/cells; AAM `136/272`; GuitarSet `618/1236`; IDMT Guitar `535/1070`;
  NRGCP `1009/2018`; Winterreise `621/1242`; GuitarSet comp `253/506`; and
  GuitarSet solo `365/730`.
- Every parent bar must be at least 2 ms. Its two cells are
  `[startMs, midpointMs)` and `[midpointMs, endMs)`, where
  `midpointMs=(startMs+endMs+1)//2`. Duration, starts, and excluded prefixes
  must already be exact decimal integer-millisecond values; values such as
  `1.0004` fail.
- Boundaries depend only on attested runtime parent starts and ends. Labels,
  prediction segments, uncertainty, correctness, and selector outputs cannot
  affect them.
- The target worker source is independently rehashed before nested prediction
  or reference access and again before publication. The frozen worker receipt
  is `ea148fd2355d493a94ec4253fadc2cacd198637b19d81bd7e5cf3576cf0407da`.
  The claim is deliberately narrow: the midpoint matches one possible player
  half-split output-event boundary. The current worker emits two events only
  when its split condition passes, and odd-meter evidence assignment is not an
  equal-duration half split. This challenger does not claim unchanged current
  UI topology or current worker half-evidence equivalence.

## Scoring, funnel, and decision

The implementation uses a dedicated canonical-ms cell summarizer/scorer; it
never adapts derived cells into the runtime analyzer schema or calls the
parent-bar summarizer/scorer. Each cell is scored on exactly
`[startMs/1000,endMs/1000)`. Prediction and reference evidence is clipped at
the prediction duration and exact cell end. A rounded-up runtime tail is
uncovered; excess evidence after a rounded-down runtime end is clipped.

Reference dominance, prediction coverage, and prediction dominance remain
fixed at `0.75`. The existing bar helper's `1e-9` comparison and overlap
semantics are versioned explicitly: an overlap at or below epsilon is ignored,
and eligibility fails only when `observed + epsilon < required`. Covered and
dominant durations and ratios are clamped identically in producer and
validator. Dominant-product exact ties choose the lexicographically smallest
canonical product.

Every self-hashed outcome embeds enough evidence for the standalone validator
to rederive `U`, `N`, `C`, or `I`. Count- and canonical-duration funnels satisfy
`T=U+R`, `R=N+E`, `E=C+I`, and `T=U+N+C+I`, and disclose `C/E`. `C/R` is named
only as the oracle end-to-end correct-support upper bound; it is not precision
or deployable accuracy.

The 13 fixed gates use integer cross-products with zero denominators failing:

- aggregate count and duration: `R/T >= 3/4`, `E/R >= 3/4`, `C/R >= 1/2`;
- GuitarSet overall count and duration: `R/T >= 3/4`, `E/R >= 3/4`,
  `C/R >= 1/4`;
- GuitarSet correct cell count: `C >= 30`.

GuitarSet comp/solo count-and-duration strata are mandatory disclosures with
exact official 18/18 track support. They are intentionally not role-specific
gates. Calibration remains closed regardless of the Stage-1 result. A pass
only permits proposing Stage 2 in a new sealed development cycle.

## Integrity and ordering

- All four top-level envelopes are rejected before caller roots are resolved.
- The official source contract is verified before nested prediction, timing,
  or reference leaves are opened.
- Benchmark rows are projected onto an exact prediction-identity allowlist.
  Full report/reference validation and group/reference metadata enter only
  after every prediction-only summary has materialized in private staging.
- Prediction duration, runtime construction duration, and report identity
  canonical milliseconds must agree before a summary is written or any
  reference opens.
- Source group metadata rows are embedded and revalidated exactly, including
  track, split, dataset, role, derived GuitarSet role, confidence group, and
  reference hash. The exact source group track-set hash and 18 comp/18 solo
  support are recomputed.
- Reference endpoint reconciliation rows are clipped in returned evidence and
  exactly cross-bound to their track, dataset, reference, and row hash.
- The standalone validator rederives construction, evidence classifications,
  exclusions, funnels, structural denominators, strata, gates, decision,
  source bindings, exact shared runtime identity, publication paths, and every
  expected sidecar filename.
- Prediction summaries remain private in a temporary directory until all
  prediction and label phases, artifact validation, and input-stability checks
  succeed. The new summary directory and its only referencing JSON are then
  published as one retained-dirfd atomic set. Prediction-, reference-, and
  publication-fault tests prove no partial visible outputs remain.

## Frozen hashes

- `steel_guitar_rag/chord_reader/half_bar_stage1.py`:
  `5704074b7f8fe899271511fafd3766b7d1ac25e81b5927690989d6b8c1b84af5`
- `scripts/chord_half_bar_stage1.py`:
  `8703611045660b4f2060ae1a7e6ab7e57a5cdceabe4507f69f6563c65a082432`
- `tests/test_chord_reader_half_bar_stage1.py`:
  `0e557aba381d4311a18784767da76f480a84a383e2dad28039d1e648cc26b1a2`
- target-player half-split contract:
  `cd2a6342c1efd3b53a54b6555ed6901a60a0b051ff9f0cf9f7ab139c96c0d00d`
- construction policy:
  `e45e4f799403c2d583cc980c38010c9bcac2da2b7b3e8e89158eeefa6a5c3a96`
- scoring policy:
  `b7c1ac8c3cc110692e346092e3bfcd154481a720973d7849655cc56f1cbde6c0`
- Stage-1 rubric:
  `4b69630b99993cff225d3302a7eb8ce5367d4e46959f19226e2d6ee51d5fd634`
- official Stage-1 source contract:
  `3e7b265e141d1303257499fe39e0bbfc2d65b87440ebb8daae9363cc28cdbac1`

The handoff's final file hash is intentionally reported outside this
self-referential document.

## Tests and checks

- `.venv/bin/python -m pytest -q -W error tests/test_chord_reader_half_bar_stage1.py`
  - `39 passed`
- `.venv/bin/python -m pytest -q -W error -k 'not real_browser' tests/test_chord_reader*.py`
  - `663 passed, 4 skipped, 2 deselected`
- Adjacent focused nonbrowser set across Stage 1, bar product, bar uncertainty,
  runtime grid, examples, selector development, and readiness:
  - `238 passed, 2 deselected`
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/half_bar_stage1.py scripts/chord_half_bar_stage1.py tests/test_chord_reader_half_bar_stage1.py`
  - passed
- `.venv/bin/ruff format --check steel_guitar_rag/chord_reader/half_bar_stage1.py scripts/chord_half_bar_stage1.py tests/test_chord_reader_half_bar_stage1.py`
  - passed
- `.venv/bin/python -m py_compile steel_guitar_rag/chord_reader/half_bar_stage1.py scripts/chord_half_bar_stage1.py`
  - passed
- CLI `--help` smoke:
  - passed

Focused adversarial coverage includes protected-split ordering; prediction,
runtime, and identity duration mismatch before reference access; midpoint and
minimum-width behavior; exact-ms rejection; construction and evidence tamper;
fragmentation; float-overlap clamping on `[2810,4099)`; rounded terminal tails;
epsilon neighborhoods; exact boundary and sub-epsilon overlap behavior; zero
denominators and integer gates; source role/group/reference splices; exact
18/18 support; fixed structural denominators; resealed shared decoder/member/
uncertainty/feature substitutions; publication and sidecar-path substitutions;
and prediction-, reference-, and publication-fault cleanup.

An attempted adjacent run without excluding browser tests produced only two
environmental failures: the pinned Chrome process exited with `SIGABRT` before
the WAV and MP3 runtime-analyzer tests could execute. The complete nonbrowser
chord-reader suite above passed; no browser result is claimed.

## Files changed

- `steel_guitar_rag/chord_reader/half_bar_stage1.py` (new)
- `scripts/chord_half_bar_stage1.py` (new)
- `tests/test_chord_reader_half_bar_stage1.py` (new)
- `docs/handoffs/task-completions/2026-08-21-0132-20-fixed-half-bar-stage1-preflight.md` (new)

No active player, worker, model, benchmark, bar scorer, selector, readiness,
calibration, test, confirmation, production, deployment, auth, corpus, private
source, or Travis file was edited.

## Risks

Risk is medium-low. The implementation is additive, exact-run-specific,
development-only, and promotion-ineligible. It intentionally uses private
validation/publication helpers from the existing sealed development pipeline;
their behavior is covered by focused and adjacent tests but remains an
internal coupling.

The midpoint is a hypothetical fixed-two-cell challenger, not a declaration
that the current worker always emits two halves. Stage-1 success would establish
structural feasibility only. It would not establish selector discrimination,
precision, calibration readiness, generalization, unchanged UI behavior, or
public-song deployability.

Canonical hashes provide tamper evidence and reproducibility, not signatures
or external authentication. The real Stage-1 command is intentionally bound to
one exact development receipt set and will fail after any source or target
worker drift until a new reviewed source contract is created.

## Human decision needed

No decision is needed to exact-path stage this isolated preflight. The real
Stage-1 development run remains a separate authorized action and was not
performed here. Its 13-gate result must be followed exactly: any failure keeps
Stage 2, calibration, test, confirmation, public-song proof, and Travis closed.

If all Stage-1 gates pass, the next cycle should preregister one Stage-2
selector fit with no alternate threshold, grid, or hyperparameter search. A
later passing candidate must still be exercised on a preregistered arbitrary
licensed/public-domain song through the exact real-player path before any
Travis contact. That public-song proof is not part of this implementation.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/half_bar_stage1.py`
- `scripts/chord_half_bar_stage1.py`
- `tests/test_chord_reader_half_bar_stage1.py`
- `docs/handoffs/task-completions/2026-08-21-0132-20-fixed-half-bar-stage1-preflight.md`

## Files that must not be staged

- Any generated benchmark, prediction, timing, summary, reference, Stage-1,
  selector, readiness, calibration, test, confirmation, public-song, model,
  audio, browser, player, private-source, deployment, or Travis artifact.
- Concurrent or unrelated worktree changes outside the four exact paths above.

## Recommended next lane

Lane 01 should exact-path review and commit only the four files listed above.
After that integration decision, Lane 20 may run the exact real development
Stage-1 command as a separate sealed action. Lane 15 should independently audit
any real artifact before a Stage-2 proposal.

## Commit readiness

Ready for exact-path staging after final independent static audit. No file is
staged or committed by this handoff.
