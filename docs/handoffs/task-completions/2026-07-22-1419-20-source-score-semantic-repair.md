# Lane 20 — Source Score Semantic Repair

## Task summary

Continued the discovery-only score-reader improvement loop without opening validation or sealed-test data and without creating another human review packet. The new source-only semantic repair records explicit key signatures and tie endpoints from the Audiveris graph, separates whole-column tie continuations from new attacks, and applies a fail-closed count publication gate based on independent source-image detectors.

Opened discovery regression results across 39 corrected lines:

- Source-notehead baseline: 19 exact lines, 35 total absolute count error.
- Existing projection/component hybrid: 27 exact lines, 25 total absolute count error.
- Semantic repair: 28 exact lines, 24 total absolute count error.
- High-confidence count subset: 13 of 13 exact; 7 of 7 development and 6 of 6 opened shadow.
- Withheld internally: 26 lines whose source-only evidence did not meet the count publication gate.
- Explicit whole-column tie repair: one line, correct.
- Independent key-signature evidence captured: 14 lines.
- On the 15 lines whose source graph had the correct event count, independently captured keys improved exact pitch-group events from 86 to 110 of 146. Only 3 complete lines were pitch exact, so score pitches remain non-publishable and no review packet was created.

The unconstrained vision replay was stopped after one uncached inference remained too slow for a bounded run. It created no review, training, validation, or sealed-test output. The deterministic semantic replay completed and is the authoritative result for this slice.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
  - Captures direct key-signature evidence, explicit tie starts, and tie continuations from the Audiveris source graph.
  - Preserves visible-column counting separately from semantic attack counting.
  - Adds a source-only, fail-closed semantic score repair and confidence gate.
  - Adds a discovery-only regression evaluator that joins reviewed truth only after inference.
  - Keeps source-only pitch candidates non-publishable until independent score/tab containment succeeds.
- `scripts/amazing_tablature.py`
  - Adds `evaluate-discovery-source-score-semantic-repair`.
- `tests/test_amazing_tablature_extraction.py`
  - Covers key and tie graph parsing, key application, source-only corroboration, and non-publication of uncorroborated pitches.
- `docs/handoffs/task-completions/2026-07-22-1419-20-source-score-semantic-repair.md`
  - This handoff.

Private regression reports were written only beneath ignored `corpus-private/melody-decisions/`. No current page record, reviewer decision, training ledger, challenger model, validation record, or sealed-test artifact was modified.

## Tests and checks

- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_extraction.py scripts/amazing_tablature.py` — PASS.
- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py` — PASS, 138 tests.
- `.venv/bin/pytest -q tests/test_amazing_tablature_training.py tests/test_amazing_tablature_sealed_test.py tests/test_amazing_tablature_input_parity.py` — PASS, 38 tests using repository fixtures only; no private sealed cohort was opened.
- Focused semantic/key/tie tests — PASS.
- `git diff --check` — PASS.
- Discovery-only semantic replay — PASS; report digest `423cd361b32eef0d54564803ab17114c731670a6bff02970ee11bc130ed2a510`.

## Integration notes

- The 13/13 result is precision on a fail-closed subset, not 100% collection coverage and not a promotion claim.
- The remaining count problem is coverage: 26 of 39 opened regression lines are correctly withheld rather than presented as valid captures.
- The remaining pitch problem is chord/head grouping and independently corroborated scientific pitch. Capturing the printed key improved event accuracy materially, but 110 of 146 comparable events and 3 exact lines are below the downstream-use gate.
- The next machine-only slice should create a unified event timeline after separately recognizing score attacks, tie continuations, and steel-only movements. It must then require source pitch candidates to agree with independently decoded machine tablature before any line can become reviewable.
- Validation review remains withdrawn. Validation and sealed-test data were not accessed.

## Risk assessment

**Medium.** The repair is fail-closed and discovery-only, but the benchmark is previously opened correction evidence and cannot promote the reader. The confidence subset is small. Pitch candidates remain explicitly non-publishable. Rollback is the scoped source commit; ignored private reports may remain for audit.

## Human decision needed

No. Do not request more review yet.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-1419-20-source-score-semantic-repair.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated untracked historical handoffs.
- Everything beneath `corpus-private/`.
- Raw images, review packets, page records, training ledgers, validation artifacts, and sealed-test data.

## Recommended next lane

Lane 20 Amazing Tablature Training.

Build the discovery-only unified event timeline and independent machine-tab pitch containment gate. Replay it against the same opened benchmark, expanding source-count coverage without reducing the 100% precision of the currently publishable count subset. Do not create a human review packet until count, mechanics, and pitch containment all pass.

## Commit readiness

Safe to commit.

## Suggested next step

`Lane 20: Build a discovery-only unified score/tie/steel event timeline and independent machine-tab pitch containment gate, replay it offline, and keep validation and human review closed until every representation is complete and count-consistent.`
