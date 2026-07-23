# Amazing Tablature runtime ranker adapter and parity

## Task summary

Implemented the production inference adapter for the canonical 21-feature Amazing Tablature ranker contract and replaced the runtime's partial eight-field approximation.

- Added one shared action-to-feature-record implementation used by trainer decision derivation and runtime position triples.
- Projected runtime `PositionCandidate` objects into the trainer's mechanical-action shape with exact pitch, stable controls, attack/sustain state, and previous/current/following context.
- Added second-order pair-state path search so outgoing movement, sustain continuity, and direction continuation/reversal can affect runtime ranking without approximating the following event.
- Preserved deterministic behavior when the ranker is disabled.
- Added the adapter to the exact rules-code digest contract.
- Added trainer-versus-runtime parity tests across all 21 ordered features and a path-search following-context regression.

No challenger was promoted and no validation or sealed-test data was opened in this slice.

## Files changed

- `pocketsteel/melody_ranker_adapter.py`
- `pocketsteel/amazing_tablature_decisions.py`
- `pocketsteel/amazing_tablature_training.py`
- `pocketsteel/melody_arranger.py`
- `tests/test_amazing_tablature_training.py`
- `tests/test_melody_arranger_decision_fixtures.py`
- `docs/handoffs/task-completions/2026-07-22-2012-20-runtime-ranker-adapter-parity.md`

## Tests and checks

- Python compilation for all touched runtime/training modules: PASS.
- Five focused adapter, fallback, and path tests: `5 passed`.
- Training, arranger-decision, copedent-transfer, and Melody Assistant suites: `97 passed`.
- Full test suite: `1378 passed in 63.32s`.
- `git diff --check`: PASS before this handoff; rerun after handoff creation.

## Integration notes

The selected challenger `at-ca3af91682513311` was trained against the same feature semantics, but its artifact pins the previous rules-code digest. It must not be evaluated or promoted against this changed runtime as though the lineage were unchanged. The next step is an exact-configuration challenger rebuild from this committed revision. Feature parity should make the new artifact reproduce the selected weights; any difference is a stop signal.

The first event receives no learned score because discovery training creates transition-scoped examples beginning at event two. All later events receive the complete canonical vector. Best Fit maps sustained-note learned scoring to the canonical `harmonized` family rather than the untrained `vocal_steel` label.

## Risk assessment

Medium until the exact challenger is rebuilt and validation passes. The active runtime remains deterministic because ranker channels and runtime weights are still disabled, so this commit does not change current protected-preview arrangement selection.

## Human decision needed

No. The active goal authorizes the clean challenger rebuild and validation phase. Exact promotion remains conditional on the fixed gates.

## Safe-to-stage exact file list

- `pocketsteel/melody_ranker_adapter.py`
- `pocketsteel/amazing_tablature_decisions.py`
- `pocketsteel/amazing_tablature_training.py`
- `pocketsteel/melody_arranger.py`
- `tests/test_amazing_tablature_training.py`
- `tests/test_melody_arranger_decision_fixtures.py`
- `docs/handoffs/task-completions/2026-07-22-2012-20-runtime-ranker-adapter-parity.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing unrelated untracked handoffs, including the two preceding status-only audits
- `corpus-private/**`
- Raw images, annotations, validation data, sealed-test data, model artifacts, and generated reports

## Recommended next lane

Lane 20: rebuild the exact selected challenger configuration from this committed HEAD, verify weight-level parity and lineage, then automatically prepare complete validation comparisons.

## Commit readiness

Safe to commit.

## Suggested next step

Commit the exact adapter slice, rebuild the selected configuration (`32` epochs, `0.03` learning rate, averaged weights, `0.35` base ratio) from its pinned parent lineage, and stop if the rebuilt weights differ from `at-ca3af91682513311`.
