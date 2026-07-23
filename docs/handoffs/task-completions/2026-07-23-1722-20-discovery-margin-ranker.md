# Lane 20 — Discovery margin ranker

## Task summary

After corrected canonical validation finished below the fixed greater-than-95%
preference gate, investigated a bounded discovery-only improvement without
training on validation decisions or opening sealed-test data.

Page-grouped five-fold discovery checks rejected an unstable per-style
hyperparameter shortcut and a nonlinear expansion. The retained change adds a
non-negative pairwise separation margin to the existing averaged perceptron.
It still consumes the exact same 21 ordered runtime features and produces the
same linear `weightsByStyle` artifact contract.

The predeclared retained discovery configuration uses 16 epochs, learning rate
0.03, averaged weights, and update margin 0.10. On the deterministic
page-grouped discovery folds it produced 660 strict top choices from 702
decisions (94.0171%), compared with 655 of 702 (93.3048%) for the prior
unshuffled 32-epoch averaged configuration. It did not regress any runtime
feature, pitch, register, harmony, or mechanical constraint.

No new challenger was created in this code slice. The implementation is ready
to be committed first so a successor artifact can pin a clean exact HEAD.

## Files changed

- `pocketsteel/melody_ranker.py`
- `pocketsteel/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1722-20-discovery-margin-ranker.md`

No files were deleted. No raw source, extraction, validation, sealed-test,
runtime, UI, auth, deployment, embedding, or vector-store files were changed.

## Tests and checks

- Python compilation — PASS.
- Ruff on the four implementation/test paths — PASS.
- Focused margin and complete-discovery tests — PASS, 3 tests.
- Lane 20 extraction/training/model/validation suite — PASS, 277 tests.
- Full repository suite — PASS, 1,449 tests.
- `git diff --check` — PASS.
- Validation decisions used for training — 0.
- Sealed-test data accessed — no.

## Integration notes

The update margin is trainer-only. It is recorded in immutable training
configuration and model identity, but the resulting artifact remains a
21-feature linear scorer compatible with the exact existing runtime adapter.

The next run should create a small fixed set of complete-discovery candidates
from the clean committed HEAD, compare them only on discovery diagnostics,
select one exact model, verify trainer/runtime parity, and then rerun canonical
validation. Corrected validation verdicts remain evaluation-only.

## Risk assessment

Medium. Discovery grouped checks show a modest and consistent aggregate gain,
but discovery development is not held-out accuracy. The change may or may not
provide the two additional accepted validation choices needed to exceed 95%.
The fixed validation threshold must not be relaxed.

Rollback is to train with the default update margin of `0.0`, which preserves
the prior behavior and artifact contract.

## Human decision needed

No. The active approved goal authorizes the bounded discovery-only refinement
and exact validation rerun. Exact runtime activation and sealed-test access
remain blocked unless all fixed gates pass.

## Safe-to-stage exact file list

- `pocketsteel/melody_ranker.py`
- `pocketsteel/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-1722-20-discovery-margin-ranker.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`
- `docs/handoffs/task-completions/2026-07-23-1700-20-corrected-canonical-ambiguity-review-ready.md`
- `docs/handoffs/task-completions/integration-status.md`
- all unrelated historical untracked handoffs

## Recommended next lane

Lane 01 exact-path commit, immediately followed by Lane 20 clean-HEAD
challenger construction and discovery-only selection.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the five exact paths above, build the fixed margin candidates from
that clean HEAD, and keep validation and sealed-test data closed until one
candidate has been selected by discovery-only evidence.
