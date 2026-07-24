# Lane 20 — Score-supported validation accounting

## Task summary

Continued the approved Amazing Tablature engineering goal and completed the
validation evidence-accounting slice for exact challenger
`at-90360274fad075f6`.

Completed:

- Added a stable execution digest that ignores candidate-wrapper identifiers
  while retaining ordered strings, frets, controls, attack state, execution
  type, and sounding pitch.
- Pinned that digest into machine score-recapture receipts and reports.
- Required complete source-contact, recapture-report, archived-page, model,
  candidate, execution, and no-training lineage before any validation decision
  can be classified as `alignment:score_supported`.
- Kept every other complete machine candidate in the separate
  `alignment:tab_only` evidence class.
- Rescored the exact challenger with both evidence modes reported separately.
- Preserved the fixed preference thresholds and preserved the raw strict
  numerator and denominator.

Exact private result:

- 68 decisions from 9 complete lines.
- Raw strict top choice: 64/68, or 94.1176%.
- Top-three coverage: 68/68, or 100%.
- Main cohort: 22/22, or 100%.
- Licks cohort: 42/46, or 91.3043%.
- Score-supported: 23/23, or 100%; evidence sufficient.
- Tab-only: 41/45, or 91.1111%; evidence sufficient.
- Source mechanics valid: 68/68.
- Predicted mechanics valid: 68/68.
- Machine-consensus score report digest:
  `70526c304d2967fc81afb9c3437d15b8856edd2490877db949554e838ac7201e`.
- Machine-consensus disagreement report digest:
  `7ba187d8e0d7ce1553508c12b883cf7e560431f8a4f48ef2283f7d4f5da5a151`.

Intentionally not completed:

- Machine consensus was not presented as human validation ground truth.
- No validation evidence entered training.
- No model was promoted or enabled.
- No sealed-test data was opened.
- No runtime, UI, deployment, auth, embedding, vector, or source file was
  changed.

## Files changed

- `steel_guitar_rag/amazing_tablature_validation.py`
- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `tests/test_amazing_tablature_validation.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_training.py`
- This handoff.

Private ignored validation reports and recapture receipts remain beneath
`corpus-private/melody-decisions/` and must not be staged.

## Tests and checks

- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_validation.py steel_guitar_rag/amazing_tablature_extraction.py steel_guitar_rag/amazing_tablature_training.py tests/test_amazing_tablature_validation.py tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_training.py`
  - PASS.
- `.venv/bin/ruff check steel_guitar_rag/amazing_tablature_validation.py steel_guitar_rag/amazing_tablature_extraction.py steel_guitar_rag/amazing_tablature_training.py tests/test_amazing_tablature_validation.py tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_training.py`
  - PASS.
- `.venv/bin/pytest -q tests/test_amazing_tablature_validation.py tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_training.py`
  - PASS: 228 passed.
- `.venv/bin/pytest -q`
  - PASS: 1,441 passed in 76.13 seconds.
- `git diff --check`
  - PASS.
- Exact machine-consensus scorer
  - Human truth used: false.
  - Validation may train: false.
  - Sealed test accessed: false.

## Integration notes

The exact challenger now has sufficient evidence in both predeclared evidence
modes, and the score-supported subset is perfect. The remaining raw overall
misses are the same four licks decisions already adjudicated on the prior
weight-identical challenger. They must not be silently copied. The next Lane
20 slice must issue an exact decision-equivalence certificate proving the
model weights, feature/config contract, decision IDs, source events, candidate
sets, rankings, and scores are identical before reusing those four immutable
expert judgments.

Even after such a certificate, the report must preserve machine consensus and
human adjudication as distinct evidence classes. The fixed canonical gate
remains closed until its full evidence contract passes.

## Risk assessment

Risk: medium.

The new lineage contract is intentionally fail closed and substantially
reduces the risk of assigning score support to a rebuilt candidate whose
musical execution changed. The remaining risk is overstating machine
consensus as canonical human validation. The scorer explicitly prevents that.

Rollback is the scoped implementation commit. Private artifacts can be
regenerated from immutable source and digest-pinned reports.

## Human decision needed

No.

The prior four decisions may be reused only if the automatic exact-equivalence
certificate passes. Otherwise the system must withhold them rather than ask
for rereview or infer equivalence.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_validation.py`
- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `tests/test_amazing_tablature_validation.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1531-20-score-supported-validation-accounting.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- All unrelated historical untracked handoffs.
- Raw images, private review submissions, model artifacts, reports,
  embeddings, indexes, auth, or deployment artifacts.

## Recommended next lane

Lane 01 exact-path commit, then Lane 20 exact decision-equivalence
certification and no-rereview adjudication transfer.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact seven-file slice, compare the old and clean challenger
disagreement evidence field by field, and reuse the four prior expert
judgments only if a digest-pinned exact-equivalence certificate passes.
