# Lane 20 — Validation Remediation and Discovery Replay

## Task summary

The validation audit remains withdrawn. The known licks canary was processed only through a fail-closed machine remediation path. Its deterministic tab geometry found 14 candidate columns, while the legacy count-only reader found 12. Guided state recognition produced 14 candidate states, but the independent score-pitch gate accepted 0 of 14 correspondences, so no candidate was applied and no review packet was created.

The remediation work then moved back to already opened, corrected discovery evidence. A new supervised-geometry regression measures tab fret/control recognition and score-pitch recognition after inference, without creating training evidence or another human-review queue.

Discovery regression result for three corrected main-packet lines:

- 33 total reviewed events across three cases.
- Two cases were measurable; one was withheld because the state reader did not return one token for every reviewed row.
- Guided tab recognition was exact on 21 of 21 measurable events and exact on both measurable lines.
- The ordinary score vision reader was exact on 1 of 21 measurable events and on no complete line.
- The source-only Audiveris head graph recovered 14 of 15 pitches on its count-complete natural-staff-position case. It was not promoted because the other cases had incorrect attack counts and key-signature provenance remains unreliable.

The licks validation canary remains at revision 1 with zero validation-machine recaptures. Its existing 12 score events, 5 decoded tab events, and 14 visual candidates were not replaced.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`
  - Added structural capture-issue classification so pitch disagreements are not mislabeled as blank reader output.
  - Added fail-closed validation machine remediation with visual event geometry, guided tab-state reading, string-origin calibration, copedent validation, score-pitch containment, immutable private revisions, and no-review publication behavior.
  - Added numbered guided tab-state crops and guide-aware local vision parsing.
  - Added deterministic key-signature application as a diagnostic, without enabling automatic use of unverified key metadata.
  - Added an opened-discovery guided capture regression with aggregate tab, score-vision, and head-graph metrics.
- `scripts/amazing_tablature.py`
  - Added `remediate-validation-machine-capture`.
  - Added `evaluate-discovery-guided-capture-regression`.
- `tests/test_amazing_tablature_extraction.py`
  - Added regression coverage for capture-issue classification, machine count consensus, guided event ordering, nonblank/mechanically valid states, score/tab pitch containment, and key-signature handling.
- `docs/handoffs/task-completions/2026-07-22-1343-20-validation-remediation-discovery-replay.md`
  - This handoff.

Generated private artifacts were written only beneath ignored `corpus-private/melody-decisions/` automation paths. No raw image, reviewed record, training ledger, challenger, validation page record, or sealed-test artifact was modified.

## Tests and checks

- `.venv/bin/python -m py_compile pocketsteel/amazing_tablature_extraction.py scripts/amazing_tablature.py` — PASS.
- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py` — PASS, 137 tests.
- `.venv/bin/pytest -q tests/test_amazing_tablature_training.py` — PASS, 35 tests.
- `.venv/bin/pytest -q tests/test_amazing_tablature_sealed_test.py tests/test_amazing_tablature_input_parity.py` — PASS, 3 tests using test fixtures only; no private sealed cohort was opened.
- `git diff --check` — PASS.
- Validation canary dry runs — correctly withheld; zero applied lines.
- Discovery guided capture regression — completed with no validation or sealed-test access in that regression run.

## Integration notes

- Validation remains evaluation-only and may not create training evidence.
- The validation remediation command writes a page revision only with `--apply`, and the tested canary never reached that gate.
- No validation review page should be served until every representation is nonblank, mechanically complete, and count-consistent.
- Tab glyph recognition is no longer the leading error when event and string geometry are known. Score attack recovery, pitch/scientific octave, and independently verified key signatures are the current bottlenecks.
- Natural staff-position head-graph pitches and key-adjusted pitches must remain separate until key-signature capture is independently reliable.

## Risk assessment

**Medium.** The new commands are fail-closed and did not change private truth, but they are experimental Lane 20 automation. The score reader remains well below the publication gate. Row-origin calibration and mechanical row overrides are diagnostics until discovery regression coverage is expanded. Rollback is the scoped source commit; private generated reports may remain ignored and need not be deleted.

## Human decision needed

No. Do not request more human review yet.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-1343-20-validation-remediation-discovery-replay.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated untracked historical handoffs.
- Everything beneath `corpus-private/`.
- Raw images, source crops, review packets, validation records, training ledgers, challenger artifacts, and sealed-test data.

## Recommended next lane

Lane 20 Amazing Tablature Training.

Expand the guided discovery regression across a page-grouped development slice, add source-only attack-count repair around the head graph, and require separately validated key-signature evidence. Do not prepare another human review packet until the combined nonblank/count/mechanics/pitch gate passes offline.

## Commit readiness

Safe to commit.

## Suggested next step

`Lane 20: Expand the discovery-only guided score/tab regression, improve source-only head-graph attack recovery and key-signature capture, and keep validation review withdrawn until the offline structural and pitch gates pass.`
