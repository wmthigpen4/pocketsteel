# Lane 20 — Source-only count-hypothesis consensus

## Task summary

Validation readiness was discarding complete score crops whenever two independent
source-only readers located the same printed notehead columns but disagreed about
whether one of those columns was a tied continuation.

This slice advances the approved automated validation-repair loop without using
validation answers:

- exact agreement on visible columns, attacks, and continuations remains the
  preferred path;
- when those signatures differ, a count must receive at least two votes across
  the two readers' independently observed visible-column and attack counts;
- each surviving count is passed to two independently seeded score-only
  pitch/key readers;
- the readers must agree exactly on key signature and every ordered scientific
  pitch group, and their source geometry must remain within the existing `0.06`
  gate;
- zero surviving pitch hypotheses fail closed;
- multiple surviving pitch hypotheses fail closed;
- lineage now records count votes, candidate counts, consensus mode, and rejected
  pitch candidates;
- the private validation machine-recapture contract is bumped from v4 to v5.

The change does not use tablature pitches, validation truth, reviewer answers, or
sealed-test data to choose a score count. No audit was published and no model was
promoted or enabled.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- this handoff

Private generated reports remain under ignored
`corpus-private/melody-decisions/` and must not be staged.

## Tests and checks

- Focused source-only consensus tests: **2 passed**.
- Full Lane 20 focused suite:
  - `tests/test_amazing_tablature_extraction.py`
  - `tests/test_amazing_tablature_input_parity.py`
  - `tests/test_amazing_tablature_score_sequence.py`
  - `tests/test_amazing_tablature_sealed_test.py`
  - `tests/test_amazing_tablature_training.py`
  - result: **208 passed**.
- `git diff --check`: **passed**.
- Validation truth accessed: **no**.
- Sealed-test data accessed: **no**.

## Integration notes

The currently pinned discovery challenger predates the v5 code revision. After
this exact slice is committed, Lane 20 must rebuild the challenger at the clean
HEAD, repin both validation batches, replay validation extraction, and rerun the
unpublished machine-only remediation/readiness report.

Any line with zero or multiple source-only count/pitch hypotheses remains
withheld. This slice does not relax score/tab pitch containment, source-copedent
mechanics, independent tab-cell lineage, row-origin uniqueness, or structural
preflight.

## Risk assessment

Medium.

The fallback is deliberately conservative, but it permits a repeated
source-only count hypothesis when exact tie classification differs. Exact
two-reader pitch/key agreement and unique-hypothesis selection limit the risk.
Rollback is the single implementation commit; ignored private artifacts are not
part of source history.

## Human decision needed

No.

This is an internal, fail-closed validation-readiness repair within the approved
goal. It does not publish a human packet, activate a model, open sealed data, or
change production behavior.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-23-0104-20-source-only-count-hypothesis-consensus.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- unrelated untracked historical handoffs
- all of `corpus-private/`
- source images, validation reports, review receipts, models, and sealed-test
  artifacts

## Recommended next lane

Lane 20 Amazing Tablature Training.

## Commit readiness

Safe to commit

## Suggested next step

Exact-path commit this three-file slice, rebuild the discovery-only challenger,
repin both validation batches, rerun v5 machine-only remediation, and calculate
unpublished structural readiness. Do not send another human audit unless every
displayed line is complete.
