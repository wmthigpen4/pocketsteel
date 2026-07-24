# Lane 20 — Iterative canonical validation correction

## Task summary

Received the focused canonical-validation correction submission for challenger
`at-90360274fad075f6`. One line was confirmed correct and was carried forward
without rereview. The remaining feedback line was rebuilt as 20 distinct steel
movements, replacing the prior 18-column version that had collapsed separate
attacks and a pedal release.

Implemented an append-only follow-up correction workflow that:

- Verifies the exact prior correction report, packet, submission, corrected
  line, source page, and private correction plan.
- Carries every unchanged or already-confirmed line without rereview.
- Applies new feedback only to the affected corrected line.
- Re-runs copedent and mechanical validation on every replacement event.
- Produces a focused confirmation packet containing only the materially changed
  line.
- Keeps validation truth evaluation-only and leaves sealed-test data unopened.

Across the canonical set, eight lines now require no further review. One
materially reconstructed line requires a final tablature-only confirmation.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- This handoff

Ignored private correction plans, corrected validation records, reports,
packets, and renderings remain beneath `corpus-private/melody-decisions/` and
must not be staged.

## Tests and checks

- Python compilation: PASS.
- Focused canonical-validation tests: PASS, 5 tests.
- Lane 20 test suite: PASS, 274 tests.
- Full repository suite: PASS, 1,446 tests.
- Ruff on changed implementation, CLI, and tests: PASS.
- `git diff --check`: PASS.

## Integration notes

The correction report and one-line packet must be regenerated after this
implementation is committed so their lineage pins the clean repository HEAD.
After that single confirmation is received, Lane 20 must score the exact
challenger predictions against the corrected nine-line human truth. The
original pre-correction metrics are not sufficient because one line's event
sequence materially changed.

Validation ground truth must not train, alter model weights, or enter discovery
preferences. Sealed-test data remains unopened until the exact rules, schemas,
copedents, validators, and scorer are frozen.

## Risk assessment

Risk: medium. The workflow and 20-event reconstruction are mechanically valid
and fully tested, but the materially changed line still needs one final
tablature-only confirmation before becoming canonical validation truth.

## Human decision needed

Yes. Confirm the single rebuilt line after the packet is regenerated from the
committed HEAD.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-23-1649-20-iterative-canonical-correction.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- Modified prior checkpoint handoffs
- Unrelated historical untracked handoffs

## Recommended next lane

Lane 20 Amazing Tablature Training.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the four exact files above, regenerate and smoke-test the one-line
private confirmation packet, then score the corrected nine-line human truth
after its receipt is submitted.
