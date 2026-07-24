# Lane 20 — Corrected validation truth repin

## Task summary

Added a fail-closed way to score a new exact challenger against previously
confirmed canonical validation truth without asking the user to repeat score
or tablature correction work.

The scorer now accepts an optional exact source-model ID. It verifies that
model's artifact, corrected truth report, source packet, original preference
adjudication, disagreement report, and submission bytes before deriving the
new challenger's decisions. Only byte-equivalent prior preference verdicts
carry. New alternatives remain unresolved and require explicit expert
judgment; validation never becomes training evidence.

The clean discovery-only candidate selection retained
`at-59964492d19e1894`. Its opened discovery diagnostic contains 971 acceptable
choices from 1,060 decisions, five more than the prior challenger, with zero
selected rereview lines. The exact candidate still uses the same 21 ordered
runtime features.

An integration replay against the confirmed 124-decision validation truth
succeeded. It found 10 genuinely new alternative preferences. No old
corrected score or tablature line needs rereview. The result remains
fail-closed pending only those compact preference judgments.

## Files changed

- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1730-20-corrected-truth-repin.md`

Private model, discovery-shadow, and evaluation artifacts were appended under
ignored `corpus-private/melody-decisions/`. No source image, accepted
discovery record, validation truth, sealed-test datum, runtime behavior, UI,
auth, deployment, embedding, or vector store was modified.

## Tests and checks

- Python compilation — PASS.
- Ruff — PASS.
- Corrected-canonical focused tests — PASS, 3 tests.
- Lane 20 extraction/training/model/validation suite — PASS, 278 tests.
- Full repository suite — PASS, 1,450 tests.
- `git diff --check` — PASS.
- Private cross-model corrected-truth integration replay — PASS, 124
  decisions.
- Validation decisions added to training — 0.
- Sealed-test data accessed — no.

## Integration notes

The selected model is `at-59964492d19e1894`, artifact SHA-256
`2ddf2ac0c9093665bdef6938d4dcb365b64e7950ed554c61a5b83e7caae83d01`.
It pins clean HEAD `6a9731138d74b37250963f25e9f7974809a50951`,
discovery seed `ats-b21da77c0869f91e`, 702 discovery examples, 21 ordered
features, and `16/6/10` reviewed/training/co-valid preference accounting.

After committing this evaluator slice, rerun the exact corrected score so its
evaluation lineage pins the clean evaluator HEAD. Prepare one compact packet
covering only the 10 new preferences. Do not request score/tab correction,
open sealed test, or enable runtime weights.

## Risk assessment

Medium. Reusing confirmed source truth removes unnecessary human work, but the
new model still creates 10 genuinely different alternatives. Mechanical and
pitch equivalence cannot substitute for expert preference. The fixed
greater-than-95% gate remains unchanged.

Rollback is to omit `--source-model-id`, which preserves the original
same-model scorer behavior.

## Human decision needed

No decision is needed for this implementation or exact commit. A compact
preference-only review will be necessary after the clean scorer replay because
the 10 new disagreement signatures have not previously been judged.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1730-20-corrected-truth-repin.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`
- `docs/handoffs/task-completions/2026-07-23-1700-20-corrected-canonical-ambiguity-review-ready.md`
- `docs/handoffs/task-completions/integration-status.md`
- all unrelated historical untracked handoffs

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 20 clean evaluator replay and
compact preference-only packet preparation.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the four exact paths above, rerun the selected challenger against
the already-confirmed validation truth, and expose only the genuinely new
preference decisions.
