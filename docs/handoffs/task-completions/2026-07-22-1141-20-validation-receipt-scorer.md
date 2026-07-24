# Lane 20 — Validation receipt scorer and expert-override fix

## Task summary

Continued the approved Amazing Tablature validation workflow from clean HEAD `ae80a3082a9cf164a8569a0bd1f6c076972b9b5a`.

Completed:

- Fixed the validation console so an expert may mark a line correct even when the machine had flagged it. Machine warnings remain visible but no longer veto expert ground truth.
- Regenerated both private validation consoles without changing either packet digest.
- Added `score-validation-line-audits`, which verifies exact model, packet, page-record, and submission lineage before scoring.
- Separated score/image recognition metrics from normalized-input arranger ranking metrics.
- Enforced the predeclared `>95%` top-choice gate, top-three, cohort, evidence-mode, and mechanical-safety gates.
- Made validation scoring in-memory only. It cannot import validation reviews into accepted decisions or training data.
- Produced a metrics-only pending receipt while both expert submissions are absent.

Intentionally not changed:

- No validation answer was used for training or rule refinement.
- No sealed-test file was opened.
- No rules freeze, sealed evaluation, promotion, runtime integration, embeddings, source files, or raw assets were changed.

## Current evidence

- Exact challenger: `at-1fa9630a173af769`
- Artifact SHA-256: `092bdd501490425c85732fb80af51f777270205d503b44aa242111a7e955aa50`
- Main validation packet: `4663b12e863dde290790622fdfb62a3f07ca95412814fc766bc933c40c066803`
- Licks validation packet: `aafa20b92a9628e0dd695496f5588ccff841a0c75e96244cc71515a0f315e8cf`
- Combined validation pages: 31
- Pages with paired score/tab lines: 28
- Pages with no paired line: 3
- Current page/system detection: `28 / 31 = 90.32%`, below the fixed 95% floor
- Reviewable lines: 63
- Pre-review automated blockers: 200 (192 main, 8 licks)
- Expert submissions received: 0 of 2 at scoring time
- Arranger top-choice accuracy: not yet established; no unreviewed machine output was treated as ground truth
- Pending report digest: `d31223454396cd2ffcb45dc0934a851f16c2822211b34c4e9b51cb68a98e3fb3`
- Rules freeze allowed: no
- Sealed test allowed: no

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-22-1141-20-validation-receipt-scorer.md`

Private ignored artifacts regenerated or created:

- Both current validation line-audit HTML consoles
- `corpus-private/melody-decisions/validation-evaluations/at-1fa9630a173af769/validation-line-score-d31223454396cd2ffcb45dc0934a851f16c2822211b34c4e9b51cb68a98e3fb3.json`

Deleted files: none.

## Tests and checks

- `.venv/bin/pytest -q tests/test_amazing_tablature_training.py tests/test_amazing_tablature_extraction.py` — 164 passed
- `.venv/bin/pytest -q` — 1,345 passed
- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_training.py scripts/amazing_tablature.py` — passed
- `git diff --check` — passed
- Local HTTP checks for both regenerated validation consoles — passed; both served the expert-override code
- `score-validation-line-audits at-1fa9630a173af769` — completed with a pending/fail-closed receipt; both submissions pending and sealed access false

## Integration notes

The scorer reports two independent gates:

1. Recognition: page/system detection, score-reader correctness, explicit tab confirmation, and resolved-line rate.
2. Arranger ranking: exact normalized score events to expert-selected tablature, with strict top-choice, top-three, cohort, evidence-mode, and mechanical-safety thresholds.

Typed notes, intervals, MusicXML, MIDI, and normalized event input bypass image recognition. Uploaded sheet music must pass both recognition and arranger gates.

The compact validation review is not the complete atomic OCR/OMR acceptance suite; its report says so explicitly.

## Risk assessment

Risk: medium.

- The page/system detector is objectively below 95% on the opened validation pages.
- The arranger accuracy is unknown until both immutable expert submissions arrive.
- Validation feedback may diagnose a failure, but must not train the challenger.
- Once a passing model is frozen and the sealed test is run, that test is a one-shot unbiased evaluation.

Rollback: revert the scoped commit. Private reports and consoles are generated and ignored; source assets are unchanged.

## Human decision needed

No product decision is needed now. The two current validation audits must be completed and submitted before a real accuracy result exists.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-22-1141-20-validation-receipt-scorer.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing parked change)
- All `corpus-private/` content
- All unrelated historical untracked handoffs
- Any raw source page, validation submission, sealed-test material, report, model, embedding, or vector artifact

## Recommended next lane

Lane 20 after both expert validation submissions are received. Run the immutable scorer once, report the recognition and arranger gates separately, and stop fail-closed if either is below threshold. Lane 15 receives a freeze candidate only after all fixed validation gates pass.

## Commit readiness

Safe to commit

## Suggested next step

Complete and submit both current validation line audits. Then run:

`Lane 20: Score both immutable validation line-audit submissions for exact model at-1fa9630a173af769. Do not train on validation, do not open sealed test, and report recognition and arranger accuracy separately.`
