# Lane 20 — Strict Score/Tab Execution Projection

## Task summary

The validation preflight exposed a structural bottleneck rather than a ranking-model failure: only 4 of 63 validation lines were machine-complete, and the dominant failures came from asking the full-line vision model to reproduce event/cell geometry already established by the deterministic detector.

This slice adds a fail-closed machine-only fallback:

- independent score-reader x positions are matched monotonically to deterministic tablature columns;
- the maximum accepted pair delta is `0.02`;
- unmatched tablature columns are represented as pedal/lever or bar movement without a new score attack;
- equal-quality assignments are rejected unless a same-position candidate has a strictly stronger visible-cell tie-break;
- per-cell token confidence, exact source copedent mechanics, unique row-origin selection, score-pitch containment, and provenance gates remain mandatory;
- validation line preflight now compares score attacks with picked tab attacks while permitting explicitly represented no-pick movement columns.

No validation truth was used. The threshold was checked only against already-opened, human-reviewed discovery evidence. Five discovery movement lines met the strict `0.02` eligibility gate, and all five execution projections were exact. The next looser threshold admitted an error, so it was not adopted.

The previously generated incomplete validation audit remains unpublished. Sealed-test data remains closed.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`
  - bumped validation machine recapture contract to v4;
  - added strict independent score/tab execution projection;
  - retained the full-line localizer only as a count-consistent fallback;
  - corrected validation preflight treatment of no-pick movement columns;
  - expanded machine-only lineage and diagnostic accounting.
- `tests/test_amazing_tablature_extraction.py`
  - added exact movement-column preflight coverage;
  - added strict projection, visible-cell tie-break, and ambiguity rejection coverage.
- This handoff.

Generated private validation reports and derivatives remain under ignored `corpus-private/melody-decisions/` and must not be staged.

## Tests and checks

- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py`
  - **162 passed**
- `.venv/bin/pytest -q tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_input_parity.py tests/test_amazing_tablature_score_sequence.py tests/test_amazing_tablature_sealed_test.py tests/test_amazing_tablature_training.py`
  - **208 passed**
- `git diff --check`
  - **passed**
- Discovery-only movement projection benchmark:
  - strict-gate eligible cases: **5**
  - exact execution classifications: **5/5**
  - validation data used to select threshold: **no**
  - sealed-test data accessed: **no**

## Integration notes

The currently pinned challenger `at-d5c2fbe162bc7d88` predates this code revision. After commit, Lane 20 must rebuild the exact discovery challenger, repin both validation batches, replay extraction, and rerun machine-only remediation before any validation audit may be published.

Validation ground truth may score the frozen challenger but may not become training evidence. The sealed test must remain closed until validation gates pass and the complete rules/model bundle is frozen.

## Risk assessment

Medium.

The projection is deliberately narrow. It should recover only lines whose independently captured score and deterministic tab geometry coincide strongly. Lines outside the discovery-validated threshold, with blank cells, uncertain tokens, ambiguous mappings, invalid copedent actions, or pitch disagreement remain withheld.

Rollback is the single implementation commit for this slice; ignored private artifacts are not part of source history.

## Human decision needed

No.

This is an internal fail-closed validation-readiness improvement within the approved training goal. It does not promote a model, publish an audit, open sealed data, or alter production behavior.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2328-20-strict-score-tab-execution-projection.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- unrelated untracked historical handoffs
- all of `corpus-private/`
- source images, validation reports, review receipts, models, and sealed-test artifacts

## Recommended next lane

Lane 20 Amazing Tablature Training.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact three-file slice, rebuild the discovery-only challenger at that clean HEAD, repin and replay both validation batches, and rerun the private machine-only validation preflight. Publish nothing unless every displayed line is structurally complete.
