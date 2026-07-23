# Lane 20 — Canonical validation corrections

## Task summary

Received and scored the exact nine-line canonical validation submission for
challenger `at-90360274fad075f6`. The submission confirmed two lines and
identified seven lines requiring correction, so the canonical gate correctly
remained closed.

Implemented an append-only validation-correction workflow that:

- Pins the original score report, packet, submission, source candidate, source
  page digest, correction plan, and exact correction operations.
- Leaves machine page records and machine-consensus candidates immutable.
- Applies all seven feedback lines to separate validation-ground-truth
  artifacts.
- Re-runs deterministic copedent and mechanical validation.
- Carries the two already-confirmed lines without rereview.
- Sends back only two corrected lines that genuinely require another human
  confirmation.
- Prohibits validation evidence from entering discovery training.
- Leaves both sealed-test cohorts unopened.

The private correction application produced:

- 9 total lineage-covered lines.
- 7 corrected lines.
- 2 carried human-confirmed lines.
- 2 lines requiring focused confirmation.
- 100% mechanical validity across the corrected lines.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- This handoff.

Ignored private correction plans, corrected validation records, reports,
packets, and renderings were generated beneath
`corpus-private/melody-decisions/`. They must not be staged.

## Tests and checks

- Python compilation: PASS.
- Focused canonical-validation tests: PASS, 4 tests.
- Focused extraction and training tests: PASS, 230 tests.
- Full Lane 20 suite: PASS, 261 tests.
- Full repository suite: PASS, 1,445 tests.
- Ruff on changed implementation, CLI, and tests: PASS.
- `git diff --check`: PASS.

## Integration notes

The correction report and focused packet must be regenerated after the
implementation commit so their lineage records the final repository HEAD. The
user should then confirm only the two shown lines. Once that receipt is
received, Lane 20 can score the exact human-corrected validation truth and
continue to the private learned-versus-deterministic comparison if the fixed
thresholds pass.

The original validation submission remains a failed canonical gate and is not
overwritten. Validation ground truth is evaluation-only and cannot train the
challenger.

## Risk assessment

Risk: medium. The workflow is mechanically validated and digest-pinned, but two
changed lines still need focused human confirmation before they can become
canonical validation truth. No runtime behavior changed.

## Human decision needed

Yes. Confirm the two corrected validation lines after the packet is regenerated
from the committed HEAD.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-23-1632-20-canonical-validation-corrections.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- Modified prior checkpoint handoffs
- Unrelated historical untracked handoffs

## Recommended next lane

Lane 20 Amazing Tablature Training for focused correction confirmation and
human-corrected validation scoring. Independent Lane 15 remains required before
the final rules freeze.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the four exact files above, regenerate the two-line private packet
from that HEAD, run local browser smoke, and give the user the exact
cache-busted URL.
