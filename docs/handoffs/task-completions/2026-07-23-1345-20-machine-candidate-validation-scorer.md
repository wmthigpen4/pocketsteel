# Lane 20 Machine-Candidate Validation Scorer

## Task summary

Implemented an evaluation-only scorer for complete, discovery-calibrated
machine-consensus validation lines.

The scorer:

- accepts only authoritative `complete_machine_candidate` lines with
  digest-verified report, candidate, page, exact-model, and mechanical
  lineage;
- ignores every withheld or incomplete line;
- removes machine score hypotheses and event alignments before deriving
  decisions;
- records the resulting evidence only as `alignment:tab_only`;
- withholds movements whose attack-versus-hold state is unresolved;
- computes exact challenger ranking and mechanical metrics without writing
  validation decisions to training ledgers;
- reports score-supported evidence as absent;
- hard-blocks canonical validation, rules freeze, sealed test, and private
  learned-runtime activation regardless of the measured tab-only score.

No validation answer, sealed-test datum, approved discovery record, model
weight, runtime flag, or source image was modified.

## Files changed

- `docs/amazing-tablature-training.md`
- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1345-20-machine-candidate-validation-scorer.md`

## Tests and checks

- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_training.py scripts/amazing_tablature.py`
  - Passed.
- `.venv/bin/ruff check steel_guitar_rag/amazing_tablature_training.py scripts/amazing_tablature.py tests/test_amazing_tablature_training.py`
  - Passed.
- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_training.py::test_machine_validation_scorer_uses_only_complete_tab_consensus`
  - Passed: 1 test.
- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_training.py`
  - Passed: 43 tests.
- `.venv/bin/python -m pytest -q`
  - Passed: 1,433 tests.

## Integration notes

New command:

```bash
.venv/bin/python scripts/amazing_tablature.py \
  score-validation-machine-candidates <exact-model-id>
```

The output schema is
`amazing-tablature-machine-validation-score-v1`. It pins the model artifact,
machine-consensus report and candidate digests, code revision and code-file
digests, structured-input parity report, cohort receipts, evidence-mode
metrics, no-training contract, and unopened sealed-test state.

This is a diagnostic bridge around incomplete image capture, not a substitute
for score-supported human validation. It must not be used to freeze or promote
the challenger.

## Risk assessment

**Medium.** The scorer evaluates only the small complete subset and therefore
can be selection-biased. It reports sample sufficiency and withheld counts,
keeps score-supported evidence empty, and unconditionally blocks every
promotion gate to prevent overclaiming.

## Human decision needed

No. Commit the scoped implementation, rebuild the machine-consensus artifacts
only if exact code-lineage checks require it, and run the scorer against the
exact canonical challenger.

## Safe-to-stage exact file list

- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-23-1345-20-machine-candidate-validation-scorer.md`
- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- other pre-existing untracked handoffs
- `corpus-private/**`
- raw source files, validation answers, sealed-test data, embeddings, vector
  stores, credentials, logs, auth files, and deployment files

## Recommended next lane

Lane 20 Amazing Tablature Training, followed by Lane 15 QA only if the
diagnostic has sufficient evidence.

## Commit readiness

Safe to commit

## Suggested next step

Commit the five exact files above, run
`score-validation-machine-candidates <exact-model-id>`, and report the
tab-only metrics separately from the still-closed canonical validation gate.
