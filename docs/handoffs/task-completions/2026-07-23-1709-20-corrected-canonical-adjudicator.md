# Lane 20 — Corrected canonical adjudicator

## Task summary

Implemented the missing append-only finalizer for corrected canonical
validation. The existing corrected scorer and two compact review packets were
already capable of isolating eight genuinely new preference ambiguities, but
there was no digest-bound command that could consume both cohort submissions
and recompute the fixed promotion gates.

The new
`adjudicate-corrected-canonical-validation` command:

- requires the exact corrected score-report digest;
- requires one unique immutable submission per authoritative cohort;
- proves each submission belongs to the exact model artifact, corrected score,
  disagreement report, packet, cohort, and pending decision set;
- carries prior verdicts only from the scorer's already verified
  byte-equivalent ledger;
- recomputes overall, cohort, evidence-mode, top-three, and mechanical gates
  from strict counts;
- treats reviewer feedback as unresolved and keeps every activation/freeze
  gate closed;
- writes only a private evaluation receipt;
- adds zero validation decisions to discovery or training;
- leaves the sealed test unopened.

The existing one-choice licks packet and seven-choice main packet remain valid.
This slice did not rewrite their score digest, disagreement digest, packet
digest, or source imagery.

## Files changed

- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1709-20-corrected-canonical-adjudicator.md`

No files were deleted. Private generated reports remain ignored beneath
`corpus-private/melody-decisions/`.

## Tests and checks

- Python compilation: PASS.
- Ruff: PASS.
- Focused corrected-adjudication and trainer/runtime parity tests: PASS,
  3 tests.
- Lane 20 extraction, training, runtime-model, and arranger suite: PASS,
  254 tests.
- Full repository test suite: PASS, 1,448 tests.
- `git diff --check`: PASS.

New tests prove:

- accepted alternatives are incorporated into the fixed metrics;
- strict source-top counts remain separately visible;
- all fixed gates pass only when every cohort is complete and thresholds pass;
- a missing cohort submission fails closed;
- reviewer feedback keeps runtime enable, rules freeze, and sealed-test access
  disabled;
- no accepted training ledger is created from validation.

## Integration notes

After the user submits both compact packets, run:

```text
.venv/bin/python scripts/amazing_tablature.py \
  adjudicate-corrected-canonical-validation \
  at-90360274fad075f6 \
  --score-report-digest \
  78ddcd590280d21d9701efa73668b55207a4994c28aa02ebedeef1ea85fc23a4 \
  --submission-id <licks-submission-id> \
  --submission-id <main-submission-id>
```

The exact submission IDs must be discovered from the immutable private
receipts; do not guess them.

Because this implementation changes a rules-code digest, a passing result is
not itself sufficient to freeze the existing challenger. After adjudication,
rebuild the discovery-only challenger from the clean committed HEAD, verify
byte-identical learned weights and exact trainer/runtime parity, transfer
validation verdicts only across byte-equivalent disagreement signatures, and
rerun the corrected evaluation. Validation must not train the rebuild.

## Risk assessment

Medium. The new finalizer is intentionally strict and can block on any stale
packet, incomplete cohort, feedback correction, changed artifact, or changed
digest. This is desirable fail-closed behavior. The remaining risk is that the
eight human choices may not clear the fixed greater-than-95% gate.

## Human decision needed

Yes. Submit the one licks preference choice and seven main-packet preference
choices. No score or tablature capture rereview is requested.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1709-20-corrected-canonical-adjudicator.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/2026-07-23-1700-20-corrected-canonical-ambiguity-review-ready.md`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`
- `docs/handoffs/task-completions/integration-status.md`
- all unrelated historical untracked handoffs

## Recommended next lane

Lane 20 applies the two submissions and recomputes the fixed gate. If it
passes, Lane 20 rebuilds the exact discovery-only challenger from this clean
HEAD and Lane 15 independently verifies lineage and parity before any private
enablement.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the four exact files above. Preserve the existing review packet
digests, wait for both necessary preference submissions, then run the new
adjudicator automatically.
