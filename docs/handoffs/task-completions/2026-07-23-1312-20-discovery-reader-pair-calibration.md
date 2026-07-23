# Lane 20 Discovery Reader-Pair Calibration

## Task summary

Implemented a discovery-only, precision-gated calibration layer for the exact
ordered outcomes of the two pinned tablature readers.

The previous reader contract could qualify an individual reader state, but it
still treated any two-reader semantic agreement as strong evidence. Discovery
replay showed that both readers can share the same systematic source-font
misread. The new contract therefore:

- learns exact reader-pair outcomes only from digest-verified,
  human-approved discovery records;
- uses leave-one-content-unit-out evaluation and fixed support, content-unit,
  and 99.5% precision gates;
- permits an accepted pair rule to approve an exact agreement or correct a
  repeatable confusion such as blank-versus-symbol;
- gives an accepted exact pair correction precedence over ordinary agreement
  while preserving ordinary two-reader semantic agreement when no correction
  applies;
- keeps single-reader conflicts and reader failures unresolved;
- reconstructs every accepted pair state through the pinned copedent and
  mechanical validator before publication.

Validation labels and sealed-test data were not used. Learned runtime behavior
remains disabled.

## Files changed

- `docs/amazing-tablature-training.md`
- `pocketsteel/amazing_tablature_extraction.py`
- `pocketsteel/amazing_tablature_reader_calibration.py`
- `pocketsteel/amazing_tablature_training.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_reader_calibration.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1312-20-discovery-reader-pair-calibration.md`

No source images, approved discovery records, validation answers, sealed-test
records, embeddings, vector stores, runtime flags, or deployment files were
changed.

## Tests and checks

- `./.venv/bin/python -m py_compile pocketsteel/amazing_tablature_extraction.py pocketsteel/amazing_tablature_reader_calibration.py pocketsteel/amazing_tablature_training.py`
  - Passed.
- `./.venv/bin/ruff check pocketsteel/amazing_tablature_extraction.py pocketsteel/amazing_tablature_reader_calibration.py pocketsteel/amazing_tablature_training.py tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_reader_calibration.py tests/test_amazing_tablature_training.py`
  - Passed.
- `./.venv/bin/pytest -q tests/test_amazing_tablature_reader_calibration.py tests/test_amazing_tablature_training.py tests/test_amazing_tablature_extraction.py -k 'reader_calibration or contact_sheet_consensus'`
  - Superseded by the broader focused run below.
- `./.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py::test_contact_sheet_consensus_rejects_uncalibrated_shared_reader_misread tests/test_amazing_tablature_extraction.py::test_contact_sheet_consensus_applies_discovery_pair_confusion_correction tests/test_amazing_tablature_reader_calibration.py tests/test_amazing_tablature_training.py`
  - Superseded by the corrected precedence contract below.
- `./.venv/bin/python -m pytest -q tests/test_amazing_tablature_extraction.py -k 'contact_sheet_consensus'`
  - Passed: 9 tests.
- `./.venv/bin/python -m pytest -q tests/test_amazing_tablature_reader_calibration.py tests/test_amazing_tablature_training.py tests/test_amazing_tablature_extraction.py -k 'reader_calibration or contact_sheet_consensus or focused_contact_sheet'`
  - Passed: 18 tests.
- `./.venv/bin/pytest -q`
  - Passed: 1,431 tests.

## Integration notes

The reader-calibration artifact schema is now
`amazing-tablature-reader-calibration-v4`. Existing v3 private artifacts are
intentionally ineligible and must be rebuilt from discovery before another
machine-only validation comparison.

Commit preparation briefly stopped because another active Codex task modified
`pocketsteel/amazing_tablature_extraction.py` and
`tests/test_amazing_tablature_extraction.py` after the full suite passed and
while this task was staging. The staging created by this task was removed, the
other task stopped changing the files, and the policy was reconciled: an exact
accepted pair correction is evidence tier 3, ordinary independent agreement
is tier 2, and an accepted singleton is tier 1. No mixed commit was created.

The next Lane 20 action is to rerun the final suite, commit the coherent
snapshot, rebuild both private discovery artifacts against that exact HEAD,
and rerun the machine-only validation shadow. The shadow should report
accepted pair-rule counts, grouped false positives, resolved cells, withheld
cells, complete lines, and lineage hashes.

## Risk assessment

**Medium.** Exact discovery-qualified pair corrections can override ordinary
reader agreement, so their grouped holdout precision and lineage are critical.
Pair corrections remain exact-state and source-cohort specific and cannot
cross input modes. Ordinary agreement remains available when no correction
rule applies.

Rollback is the scoped implementation commit; private generated artifacts are
ignored and can be rebuilt from the preceding code revision if needed.

## Human decision needed

No. Continue the approved discovery-only challenger loop. Human musical review
is not requested unless a genuinely ambiguous residue remains after automatic
discovery calibration and deterministic validation.

## Safe-to-stage exact file list

- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-23-1312-20-discovery-reader-pair-calibration.md`
- `pocketsteel/amazing_tablature_extraction.py`
- `pocketsteel/amazing_tablature_reader_calibration.py`
- `pocketsteel/amazing_tablature_training.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_reader_calibration.py`
- `tests/test_amazing_tablature_training.py`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Other pre-existing untracked handoffs
- `corpus-private/**`
- Raw source images, validation artifacts, sealed-test artifacts, embeddings,
  vector stores, credentials, logs, and deployment files

## Recommended next lane

Lane 20 Amazing Tablature Training, followed by Lane 15 only if the
machine-only shadow satisfies the fixed validation gate.

## Commit readiness

Safe to commit

## Suggested next step

Rerun the full suite and commit the coherent exact file set. Then rebuild both
discovery reader-calibration artifacts from the committed HEAD and run one
machine-only validation shadow without opening validation answers or
sealed-test data.
