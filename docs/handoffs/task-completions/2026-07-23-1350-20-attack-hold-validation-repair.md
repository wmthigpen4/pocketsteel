# Lane 20 Attack/Hold Validation Repair

## Task summary

Continued the approved engineering phase for the exact Amazing Tablature
challenger without opening validation answers or sealed-test data.

Completed:

- extended the discovery-only source transition decoder to emit either
  `attack` or `movement_only`;
- retained exact-signature matching, abstention on unseen signatures, and the
  conservative mechanical gate for movement-only gestures;
- raised the learned-signature precision floor to 99.5%, with at least five
  reviewed examples across at least three independent discovery content
  units;
- added grouped per-label cross-validation and required every emitted label
  to have a true-positive holdout result, zero false positives, and precision
  at or above the declared floor before the decoder may automate validation;
- applied discovery-proven attacks to machine consensus while preserving
  unresolved attack-versus-hold cases;
- reported learned attack and learned movement counts separately;
- clarified that the automatic challenger scorer accepts lines with complete
  tablature cells, not necessarily complete musical execution context;
- added an integration test proving that an accepted attack signature reaches
  the consensus event contract.

Intentionally not changed:

- the exact challenger artifact;
- accepted discovery decisions or review records;
- validation ground truth;
- sealed-test membership or contents;
- runtime enablement or production behavior;
- source images, embeddings, vector stores, auth, or deployment.

The exact scorer implementation was committed immediately before this slice
as `1f267343` and remains evaluation-only.

## Files changed

- `docs/amazing-tablature-training.md`
- `pocketsteel/amazing_tablature_extraction.py`
- `pocketsteel/amazing_tablature_training.py`
- `pocketsteel/amazing_tablature_transition_decoder.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_training.py`
- `tests/test_amazing_tablature_transition_decoder.py`
- `docs/handoffs/task-completions/2026-07-23-1350-20-attack-hold-validation-repair.md`

No files were deleted. Private rebuild artifacts have not yet been generated
from this revision.

## Tests and checks

- Python compilation:
  - `pocketsteel/amazing_tablature_transition_decoder.py`
  - `pocketsteel/amazing_tablature_extraction.py`
  - `pocketsteel/amazing_tablature_training.py`
  - `scripts/amazing_tablature.py`
  - passed.
- Ruff on the touched Python modules and tests:
  - passed.
- Focused transition/contact-consensus tests:
  - 14 passed.
- Transition, extraction, and training modules:
  - 225 passed.
- Full repository test suite:
  - 1,434 passed in 68.55 seconds.
- `git diff --check`:
  - passed.

## Integration notes

The next private artifact build must occur only after this exact source
revision is committed so that each decoder records the correct code revision
and file digests.

After rebuilding each authoritative cohort's discovery transition decoder,
rerun machine-only validation contact consensus and the exact
machine-candidate scorer. Count only decisions whose current and following
execution states are exact. Continue to report tab-only machine evidence
separately from canonical human-reviewed, score-supported validation.

The fixed canonical promotion gate remains unchanged. A machine-only report
cannot authorize private runtime enablement, rules freeze, or sealed-test
access.

## Risk assessment

**Medium.** The change can improve validation execution completeness, but it
may abstain extensively if discovery evidence does not repeat across enough
independent content units. That is the intended failure mode. Rollback is the
single scoped commit for this slice; prior private decoder artifacts remain
digest-pinned and immutable.

## Human decision needed

No. Continue the automatic private rebuild and evaluation. Ask for human
review only if a compact set of complete, genuinely ambiguous cases remains
after the machine-only pass.

## Safe-to-stage exact file list

- `docs/amazing-tablature-training.md`
- `pocketsteel/amazing_tablature_extraction.py`
- `pocketsteel/amazing_tablature_training.py`
- `pocketsteel/amazing_tablature_transition_decoder.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_training.py`
- `tests/test_amazing_tablature_transition_decoder.py`
- `docs/handoffs/task-completions/2026-07-23-1350-20-attack-hold-validation-repair.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- all unrelated pre-existing untracked handoffs
- `corpus-private/**`
- source images and raw collection material
- validation answers and sealed-test artifacts
- embeddings, vector stores, credentials, logs, auth, and deployment files

## Recommended next lane

Lane 20 Amazing Tablature Training, followed by Lane 15 QA only if the
evaluation evidence becomes canonically sufficient.

## Commit readiness

Safe to commit.

## Suggested next step

Commit this exact slice, rebuild both discovery-only transition decoders from
the committed revision, rerun both validation machine-consensus reports, and
evaluate challenger `at-e00734bee5dea6fc` against the fixed gates while
keeping the sealed test closed.
