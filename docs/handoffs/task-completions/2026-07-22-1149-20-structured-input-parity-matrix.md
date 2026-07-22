# Lane 20 — Exact structured-input parity matrix

## Task summary

Strengthened the Amazing Tablature exact-input evidence from one three-note example into a deterministic eight-phrase matrix. The matrix covers G and C, ascending and descending scales, repeated notes, triad motion, varied durations, an explicit octave shift, and every canonical challenger style family.

Each phrase is independently represented as typed note names, scale-degree intervals, MusicXML, MIDI, and normalized score events. The audit requires all five representations to normalize to the same pitch/rhythm events and produce identical complete arranger output.

The validation receipt scorer now embeds this parity receipt and fails the arranger gate if parity fails. Once independently reviewed validation ranking exists, all five equivalent modalities inherit the exact same challenger ranking metrics rather than receiving separate or inflated accuracy claims.

No validation answer was opened or used for this work. No sealed-test path was opened. No runtime model was activated.

## Evidence

- Modalities: 5
- Synthetic phrases: 8
- Events per modality: 42
- Total adapter events: 210
- Exact pitch parity: pass for all phrases
- Exact arranger-output parity: pass for all phrases
- Parity report digest: `41cd52b3faaf6a36268f1542e13f38e66b42da23298a68903bdf82c6fd7a2beb`
- Accuracy claim: none; adapter equivalence only
- Validation accessed by parity audit: false
- Sealed test accessed: false

The current pending validation report is `e1e65361a3633d545a7b9ce2168a90fffbc6a89cc6183405fd9c57c39b618192`. It remains fail-closed because both expert validation submissions are pending, not because adapter parity failed.

## Files changed

- `pocketsteel/amazing_tablature_input_parity.py`
- `pocketsteel/amazing_tablature_training.py`
- `tests/test_amazing_tablature_input_parity.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-22-1149-20-structured-input-parity-matrix.md`

Private ignored artifact created:

- Metrics-only pending validation report beneath `corpus-private/melody-decisions/validation-evaluations/`

Deleted files: none.

## Tests and checks

- `.venv/bin/pytest -q tests/test_amazing_tablature_input_parity.py tests/test_amazing_tablature_training.py` — 36 passed
- `.venv/bin/pytest -q` — 1,346 passed
- `score-validation-line-audits at-1fa9630a173af769` — completed fail-closed; input parity passed, both expert submissions pending, sealed access false
- `git diff --check` — passed

## Integration notes

The matrix is synthetic on purpose: it verifies adapter equivalence without leaking discovery, validation, or test melodies into committed tests. It does not replace held-out arranger scoring. The exact challenger ranking remains the same mathematical operation after all five adapters because their normalized inputs are identical.

The parity module is included in the rules-code digest list, so a future rules freeze will pin it with the model, schemas, validators, and other arranger code.

## Risk assessment

Risk: low.

This is evaluation infrastructure and tests. It changes no runtime feature flag or active model. The main remaining risk is not adapter behavior; it is unresolved image recognition and the unknown held-out arranger score.

Rollback: revert the scoped commit. Private reports are ignored and source data is unchanged.

## Human decision needed

No. The existing main and licks validation audits still need to be completed and submitted.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_input_parity.py`
- `pocketsteel/amazing_tablature_training.py`
- `tests/test_amazing_tablature_input_parity.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-22-1149-20-structured-input-parity-matrix.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All `corpus-private/` content
- All unrelated historical untracked handoffs
- Raw sources, validation submissions, sealed-test material, models, reports, embeddings, or vector artifacts

## Recommended next lane

Lane 20 after both immutable validation submissions arrive. Run the scorer and report image recognition separately from the one shared exact-input arranger accuracy.

## Commit readiness

Safe to commit

## Suggested next step

Complete and submit both validation audits. Then run the immutable validation receipt scorer. Freeze only if the recognition, exact-input ranking, cohort, evidence-mode, top-three, mechanical, and adapter-parity gates all pass.
