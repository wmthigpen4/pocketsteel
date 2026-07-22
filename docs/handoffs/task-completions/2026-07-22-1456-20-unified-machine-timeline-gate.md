# Lane 20 — Unified Machine Score/Tab Timeline Gate

## Task summary

Continued the discovery-only machine improvement loop without opening validation or sealed-test data and without creating another human audit. This slice adds one fail-closed timeline shared by the machine score reader and archived pre-correction machine tablature. Picked score attacks, tied continuations, held score states, steel-only movements, mechanical validity, exact scientific pitches, and nonblank event rows are now explicit parts of one reviewability decision.

The evaluator uses the 39 previously opened discovery regression lines. It freezes source-score inference and the archived pre-correction machine-tab snapshot before reviewed truth is joined for scoring. It does not use corrected tablature geometry, reviewed pitches, reviewed counts, or reviewed string rows during inference.

Final discovery regression result:

- Cases evaluated: 39.
- Archived pre-correction machine snapshots available: 33.
- Source score counts exact after truth join: 23.
- Source score pitches exact after truth join: 5.
- Archived machine tablature exact after truth join: 11.
- Structurally complete unified timelines: 6.
- Timelines with exact score-pitch containment in machine tab: 3.
- Lines passing every machine reviewability gate: 1.
- Passing lines exact after the post-inference truth join: 1 of 1.
- Lines withheld from human review: 38.
- Human rereview requested: 0.

The single passing opened-shadow line is `input-0033`, score system `score-system-ec4d63bb3a08098a6210`, with five score attacks and five machine-tab states. Its first printed system supplied a digest-pinned, source-only zero-fifths key contract; all five timeline rows were nonblank, mechanically valid, and pitch-contained. Post-inference scoring confirmed both its complete score pitches and machine tablature were exact. This is a discovery regression result only, not a validation result, sealed-test result, promotion claim, or collection-wide accuracy estimate.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`
  - Adds a unified machine score/tab timeline with explicit attack, tie-continuation, and held-state semantics.
  - Blocks review on mismatched score/tab attacks, blank rows, invalid steel actions, unmatched events, or failed scientific-pitch containment.
  - Treats a printed tie as sustain evidence; a tie does not create an extra picked tablature column unless an actual machine-tab movement exists.
  - Adds first-system-only page key evidence. An explicit key remains direct evidence; a recognized first-system clef with no key candidates and no ambiguity deterministically establishes zero fifths.
  - Adds a discovery-only evaluator using digest-pinned score artifacts and archived pre-correction machine records, with reviewed truth joined only after the inference digest.
- `scripts/amazing_tablature.py`
  - Adds `evaluate-discovery-machine-score-tab-timeline`.
- `tests/test_amazing_tablature_extraction.py`
  - Covers attacks, tied continuations, movement-only held states, bad-pitch rejection, unmatched-event rejection, explicit first-system keys, proven zero-fifths keys, and ambiguous-key rejection.
- `docs/handoffs/task-completions/2026-07-22-1456-20-unified-machine-timeline-gate.md`
  - This handoff.

Ignored private report only:

- `corpus-private/melody-decisions/batches/atb-20260716-training-278-semantic-v2/extraction/discovery/review/automation/discovery-machine-score-tab-timeline-v1/report-71df385cc46e.json`
- Report digest: `71df385cc46e55e00edc9fccbd853607f494f16fbc6301ab15241c85862256c7`.

No current page record, corrected record, review decision, training ledger, challenger model, validation record, or sealed-test artifact was modified.

## Tests and checks

- `.venv/bin/python -m py_compile pocketsteel/amazing_tablature_extraction.py scripts/amazing_tablature.py` — PASS.
- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_extraction.py` — PASS.
- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_training.py tests/test_amazing_tablature_sealed_test.py tests/test_amazing_tablature_input_parity.py` — PASS, 38 tests using repository fixtures only.
- `.venv/bin/ruff check pocketsteel/amazing_tablature_extraction.py scripts/amazing_tablature.py tests/test_amazing_tablature_extraction.py` — PASS.
- `git diff --check` — PASS.
- Discovery-only machine timeline replay — PASS; report digest `71df385cc46e55e00edc9fccbd853607f494f16fbc6301ab15241c85862256c7`.

## Integration notes

- This gate solves the review-integrity problem, not the remaining recognition problem. It prevents blank or count-inconsistent representations from reaching the user.
- The principal coverage blockers are now quantified: independent machine-tab attack counts disagree with source counts on 26 lines; source pitch candidates are incomplete on 34 lines; only 5 lines have exact source pitches and only 11 have exact archived machine tablature after truth is joined.
- Blocker counts are non-exclusive and include downstream cascades; they must not be added together as unique cases.
- The first-system zero-fifths rule is limited to a digest-pinned first printed system with a recognized clef, no key candidates, and no ambiguity. It is never inferred from a continuation system.
- The 1/1 reviewable precision result is useful lineage evidence but statistically too small for promotion. It comes from previously opened discovery material.
- The no-rereview contract is enforced here as `humanRereviewRequested: false` and `reviewPacketCreated: false`. The one exact machine-reviewable regression line is accounted for internally and is not sent back to the user.
- Validation review remains withdrawn. Validation and sealed-test data were not accessed.

## Risk assessment

**Medium.** The behavior is discovery-only and fail-closed, but the benchmark is previously opened correction evidence. The one passing line is not enough to estimate general accuracy. First-system zero-fifths inference depends on correct clef/key-symbol recognition and therefore remains protected by independent machine-tab pitch containment. Rollback is the scoped source commit; ignored private reports may remain for lineage audit.

## Human decision needed

No. Do not request another human audit yet.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-1456-20-unified-machine-timeline-gate.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated untracked historical handoffs.
- Everything beneath `corpus-private/`.
- Raw images, current page records, review packets, reviewer decisions, training ledgers, validation artifacts, and sealed-test data.

## Recommended next lane

Lane 20 Amazing Tablature Training.

Improve independent machine tablature localization before asking for review again. Reuse the new unified timeline as the fixed acceptance gate, learn system-level string-row origin from source geometry and mechanical validity only, and reject any reread whose cell count differs from the visual candidate count. In parallel, improve source-score pitch grouping while preserving first-system key provenance. Replay only on opened discovery and require a materially larger exact reviewable subset with no false accepts before producing another audit.

## Commit readiness

Safe to commit.

## Suggested next step

`Lane 20: Improve independent source-only tablature row/cell localization and score-pitch grouping against the fixed unified timeline gate. Replay on opened discovery only; create no human review packet until a materially larger machine-reviewable subset remains exact after the post-inference truth join.`
