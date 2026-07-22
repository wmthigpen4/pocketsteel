# Lane 20 — Source-head count-constrained grouping

## Task summary

Implemented a discovery-only, fail-closed score-notehead regrouping rule for cases where Audiveris recognizes the individual noteheads but its chord relations split or merge printed attacks incorrectly.

The rule accepts only an independently publishable, source-image-only attack count from the frozen projection/component detector. It then partitions the recognized noteheads at the largest horizontal gaps, verifies the result through the normal score-attack grouping contract, and otherwise preserves the original events. Reviewer counts, reviewer pitches, and tablature are never inference inputs.

Intentionally not changed:

- no validation or sealed-test assets, annotations, or metrics were opened;
- no human rereview packet was created;
- no current reviewed page record was modified;
- no training evidence, model promotion, runtime integration, embeddings, or product behavior was created;
- pitch-wrong candidates continue to be withheld by the unified score/tab gate.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`
  - added `source-head-count-constrained-grouping-v1`;
  - advanced the source semantic repair lineage to `source-score-semantic-repair-v2`;
  - records before/after attack counts and complete source-only diagnostics;
  - applies regrouping only after source-only count publication and rejects any result that does not reproduce the target count.
- `tests/test_amazing_tablature_extraction.py`
  - added integration, geometry-only, immutability, and fail-closed regression coverage.
- This handoff.

Private ignored reports generated, never to be staged:

- `review/automation/source-score-notehead-challenger/semantic-repair-2032b9cae8b4.json`
- `review/automation/discovery-machine-score-tab-timeline-v1/report-b41aeaf99da8.json`

## Discovery-only replay results

Compared with frozen semantic-repair v1 report `d8db35e15dcf`:

| Metric | v1 | v2 |
|---|---:|---:|
| Source pitch candidates complete | 5/39 | 10/39 |
| Source/machine event-count agreement | 8/39 | 13/39 |
| Structurally complete timelines | 8/39 | 13/39 |
| Mechanically valid timelines | 12/39 | 16/39 |
| Source event-count mismatch blockers | 18 | 11 |
| Score-attack-count mismatch blockers | 18 | 11 |
| Machine-reviewable lines | 1 | 1 |
| Reviewable truth-exact lines | 1 | 1 |
| Reviewable precision | 100% | 100% |
| Withheld lines | 38 | 38 |

The grouping change therefore removes seven source event-count mismatches without creating a false-reviewable line. It exposes more pitch candidates to the independent containment check; incorrect candidates remain blocked, which is why the pitch-containment blocker count increases rather than being hidden.

Lineage and privacy flags in both generated reports are explicit:

- `currentPageRecordsModified: false`
- `reviewPacketCreated: false`
- `trainingEvidenceCreated: false`
- `validationAccessed: false`
- `sealedTestAccessed: false`

## Tests and checks

- `.venv/bin/python -m pytest tests/test_amazing_tablature_extraction.py -k 'source_head_grouping or source_score_semantic_repair' -q`
  - PASS: 4 passed, 145 deselected.
- `.venv/bin/python -m pytest tests/test_amazing_tablature_extraction.py -q`
  - PASS: 149 passed.
- `.venv/bin/python scripts/amazing_tablature.py evaluate-discovery-source-score-semantic-repair atb-20260716-training-278-semantic-v2`
  - PASS; report digest `2032b9cae8b4da4dbc92241a9c900f0caff8b743f9bec3a30a029970cf0077fc`.
- `.venv/bin/python scripts/amazing_tablature.py evaluate-discovery-machine-score-tab-timeline atb-20260716-training-278-semantic-v2`
  - PASS; report digest `b41aeaf99da808f94e7215260d0c5dfdc2498f4f0170b84727ee7b7b998c1d85`.
- `.venv/bin/python -m pytest -q`
  - Incomplete repo-wide signal: the process exited zero twice without a pytest summary after reaching 53%, at the unrelated `tests/test_e9_explorer_controls_ui.py::test_e9_fretboard_explorer_controls_are_mode_aware`. The complete focused Lane 20 file passed.
- `git diff --check`
  - PASS.

## Integration notes

The exact inference lineage is now:

1. `score-projection-component-hybrid-v1` publishes a count only under its existing source-only corroboration/bounded-repair rule.
2. `source-head-count-constrained-grouping-v1` may regroup digest-pinned Audiveris heads to that published count.
3. `source-score-semantic-repair-v2` emits the resulting candidate plus diagnostics.
4. `discovery-machine-score-tab-timeline-v1` independently blocks count, structure, mechanics, and pitch-containment failures.

This does not improve staff-pitch recognition itself. The next bottleneck is source-only pitch correctness in the 38 withheld discovery cases, especially missing/spurious noteheads and staff-position/key interpretation.

## Risk assessment

Risk: low to medium.

The change is fail-closed, tested, and demonstrated no discovery reviewable-precision regression. It changes internal source-score candidate grouping and therefore advances the semantic-repair lineage version. It is not promoted and has not been exposed to validation or sealed test.

Rollback: revert the scoped commit; private reports are ignored immutable evaluation artifacts.

## Human decision needed

No.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-1551-20-source-head-count-constrained-grouping.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- all unrelated untracked historical handoffs
- all files beneath `corpus-private/`
- raw images, annotations, reports, embeddings, indexes, and source material

## Recommended next lane

Lane 20 Amazing Tablature Training.

## Commit readiness

Safe to commit.

## Suggested next step

Build a source-only pitch challenger on the now-count-complete discovery cases. Score staff-position pitch, accidental/key application, missing heads, and spurious heads separately; preserve the unified containment gate and no-rereview rule; do not open validation or sealed-test data.
