# Router-aware tonal-sequence outcome

## Task summary

The user approved exactly one corrected run of the previously frozen tonal-transition decoder. The correction changed only the evidence seam: `expanded-mixture` songs used expanded logits/boundaries, while the `conservative-sparse` song used conservative logits/boundaries. Decoder penalties, songs, Chordify comparison, and success criteria were unchanged. No training, fitting, parameter search, or retry occurred.

The sole corrected invocation exited `0` and wrote one private report. The preregistered combined decision was **NO-GO** because the central Together Again D-versus-G criterion did not improve.

## Results

| Song | Baseline product agreement | Candidate | Change | Segments before/after |
| --- | ---: | ---: | ---: | ---: |
| Cowboy Take Me Away (No Steel) | 86.636895% | 86.532524% | -0.104371 points | 185 / 184 |
| String By | 94.103997% | 94.155553% | +0.051556 points | 67 / 67 |
| Together Again backing track | 68.838301% | 69.050570% | +0.212269 points | 130 / 129 |

Together Again's complete D-versus-Chordify-G inventory remained **9 windows** at the same starts. Total affected time decreased only from `12.497970778645815` to `12.297970778645812` seconds. Therefore:

- Together overall agreement improved: **pass**;
- String By stayed within the allowed half-point loss: **pass**;
- recurring Together D-versus-G count decreased: **fail**;
- combined decision: **fail / do not implement**.

This fixed tonal transition matrix is not a useful promotion candidate. It mostly preserved the current behavior and made only boundary-scale changes. The evidence supports moving any future work to an explicitly beat/downbeat-aligned segment model or human adjudication rather than tuning these transition penalties.

## Exact receipts

- Private run script SHA-256: `8892326738cb39ef6730b5b447769893b9e5e9ce24f1faafcacc4beae19d6c94`.
- Decoder object canonical SHA-256: `43009cf0187af7cbf23cc4806e19922c7fc84e7d6aab9c5ecd3d58145bbefee0`.
- Private report raw SHA-256: `fe4800df46d079278eec03300ea18e97bde0b37567699b8e65726b8a4f666d87`.
- Scope: 3 songs, 1 decoder, 0 fits, 0 parameter searches, 1 corrected invocation.

The report's optional `baselineDWindowTopCandidates` display list has a presentation-only defect: its label helper omits the `m` suffix from minor-class names, so duplicate root names can appear. That diagnostic was not used by decoding, agreement computation, D/G counting, or the pass/fail decision. It must not be used as a chord-candidate receipt. No rerun was performed to repair this non-decision diagnostic.

## Files changed

- Added this factual outcome handoff only.

Private and untracked:

- `~/Documents/Pocket Steel/tmp/chordify-upload/run_limited_tonal_sequence_check.py`
- `~/Documents/Pocket Steel/tmp/chordify-upload/limited-tonal-sequence-report.json`

No production code, UI, model, threshold, local proof bundle, source audio, or MIDI changed.

## Tests and checks

- Corrected harness compilation under the frozen v4 Python environment — passed.
- Pre-run result-path absence check — passed.
- Sole corrected router-aware invocation — passed, exit `0`.
- Strict JSON load and exact scope assertions — passed.
- Finite baseline/candidate metric assertions for all three songs — passed.
- Decision assertion `passedAll is False` — passed.
- Report raw SHA-256 and decoder canonical SHA-256 captured above.
- Post-run `git status --short` before this receipt — clean.
- No browser smoke was run because no UI artifact changed.

No test was skipped and no second model invocation occurred.

## Integration notes

Chordify remained an automated second opinion used only after decoding. No Chordify chord label entered the router, emissions, boundaries, transition matrix, or path selection. These numbers are cross-system agreement rather than ground-truth accuracy.

The result narrows the failure: simply favoring common fourth/fifth and relative-major/minor transitions is too weak and non-specific to correct the repeated Together pattern. Parameter tuning against these three Chordify outputs would overfit an unverified machine reference and is explicitly out of scope.

## Risk assessment

**Low.** The run was private, bounded, deterministic, and non-promoting. The primary risk is misreading the small +0.212-point Together change as meaningful improvement; the central targeted error count was unchanged and the combined decision failed.

## Human decision needed

**No** for this run. The correct action is to reject this decoder and stop. Any future beat/downbeat or adjudication cycle is a distinct scope and should not inherit an assumption that Chordify is ground truth.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-08-23-1928-15-router-aware-tonal-sequence-outcome.md`

## Files that must not be staged

- `~/Documents/Pocket Steel/tmp/chordify-upload/`
- `ui/chord-reader-proof/local-tests/`
- all private audio, MIDI, generated reports, and experiment source

## Recommended next lane

Stop at the user checkpoint. If work resumes later, Lane 06/15 should add human adjudication controls before Lane 18 proposes any new beat/downbeat-aligned model experiment.

## Commit readiness

Safe to commit

## Suggested next step

Report the NO-GO plainly, retain the current localhost comparison unchanged, and perform no further model runs in this task.
