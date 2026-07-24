# Lane 20 — Frozen Split-Grip Action Recovery

## Task summary

Continued the discovery-only challenger loop from HEAD `f8b361fcc629801f49d4eb0e2dcb1eeae7cfba64`. The exact split-middle-grip geometry contract is now frozen and its independently read tablature cells are replayed as complete steel actions before reviewed truth is joined.

The clean-shadow inventory was also audited. Every one of the 194 main discovery pages and all 24 licks discovery pages already appears in conservative human-exposure inventory. There is no honest unseen discovery line remaining in either batch. The workflow therefore does not relabel exposed material as fresh shadow evidence and does not open validation or sealed-test data.

Opened-discovery action replay:

- Development proposals: 2.
- Complete independent tokens: 2 of 2.
- Mechanically valid actions under `source-e9-abc-defg-v1`: 2 of 2.
- Exact actions after the post-inference truth join: 2 of 2.
- Opened-shadow proposals: 1.
- Complete independent tokens: 1 of 1.
- Mechanically valid action: 1 of 1.
- Exact action after the post-inference truth join: 1 of 1.
- Opened-discovery action gate: PASS.
- Fresh-discovery promotion: not available.
- Human rereview requested: 0.

The rule remains a non-promoted challenger. The evidence proves that the narrow recovered cells can be converted into exact, mechanically valid actions on the opened regression cases; it does not establish collection-wide accuracy or an unbiased promotion result.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
  - Adds immutable selection of the one regression-passed row-geometry contract.
  - Adds independent token/action replay pinned to the reader, copedent, geometry selection, archived machine record, and source derivative.
  - Digests action inference before reviewed truth is joined.
  - Adds reusable action metrics and a fail-closed development/opened-shadow gate.
- `scripts/amazing_tablature.py`
  - Adds `freeze-discovery-tab-row-geometry-contract`.
  - Adds `evaluate-discovery-tab-action-recovery-challenger` with explicit reader/model options.
- `tests/test_amazing_tablature_extraction.py`
  - Covers complete-token, mechanical-validity, and exact-action gate requirements.
- `docs/handoffs/task-completions/2026-07-22-1540-20-frozen-tab-action-recovery.md`
  - This handoff.

Ignored private artifacts only:

- Geometry selection digest: `0f12c74a898d636070f90f22f001e3cc75ed0a7235f765eb2a9a5d12a48be694`.
- Geometry contract digest: `8d9c99a35f12f01e2fbccfdc2b0c491bc722b396e7d5d7003d6665b1d1f5c3be`.
- Token-reader contract digest: `bccf36b7aa4c4d10128c0a52f756a3fe21877b43eb0f42200923b20900cd62ac`.
- Action report digest: `a3ba5d4a1e6b9ca089e4083ea35971780ba2789e485099cd2ba0531e091405e8`.
- Action report: `corpus-private/melody-decisions/batches/atb-20260716-training-278-semantic-v2/extraction/discovery/review/automation/anchored-tab-row-geometry-v1/split-grip-action-recovery-v1/report-a3ba5d4a1e6b.json`.

No literal source material is included in this handoff. Private selections, reports, cell crops, cell-reader caches, and actions remain ignored and must not be staged.

## Tests and checks

- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_extraction.py scripts/amazing_tablature.py` — PASS.
- `.venv/bin/ruff check steel_guitar_rag/amazing_tablature_extraction.py scripts/amazing_tablature.py tests/test_amazing_tablature_extraction.py` — PASS.
- Focused geometry/action tests — PASS, 3 tests.
- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_extraction.py` — PASS, 146 tests.
- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_training.py tests/test_amazing_tablature_sealed_test.py tests/test_amazing_tablature_input_parity.py` — PASS, 38 tests using repository fixtures only.
- `git diff --check` — PASS.
- Contract freeze replay — PASS and idempotent.
- Discovery-only action replay — PASS; report digest `a3ba5d4a1e6b9ca089e4083ea35971780ba2789e485099cd2ba0531e091405e8`.

## Integration notes

- The action inference includes the exact source-copedent revision and rejects incomplete, uncertain, multi-state, low-confidence, or mechanically invalid recovered cells.
- Reviewed actions are accessed only after the reader output and normalized action receive an inference digest.
- The frozen contract is explicitly classified as opened-discovery replay only. It cannot be presented as fresh shadow, validation, sealed-test, or promotion evidence.
- The geometry challenger remains outside the default extractor and runtime behavior.
- The independent human-exposure inventory is conservative: prepared review artifacts count as exposure even if their page was not ultimately submitted.
- Current page records, reviewed records, annotation ledgers, challenger models, validation records, and sealed-test artifacts were not modified.

## Risk assessment

**Low to medium.** The code is offline, private, and fail-closed. All three observed proposals are exact, but three is too small for an unbiased promotion claim. A new discovery collection would be required for fresh shadow evidence; otherwise this remains a narrowly supported opened-regression rule.

## Human decision needed

No. Do not request another human audit.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-1540-20-frozen-tab-action-recovery.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`.
- All unrelated untracked historical handoffs.
- Everything beneath `corpus-private/`.
- Raw images, current page records, reviewed records, human decisions, training ledgers, validation artifacts, sealed-test data, selections, reports, cell crops, and reader caches.

## Recommended next lane

Lane 20 Amazing Tablature Training.

Return to the larger blocker: incomplete conventional-score attack grouping and pitch grouping. Use the existing 39 opened discovery systems to develop source-only grouping rules, keep the unified score/tab timeline as the fixed acceptance gate, and require no false reviewable accepts. Do not send another human audit until the score reader and tablature state are simultaneously complete.

## Commit readiness

Safe to commit.

## Suggested next step

`Lane 20: Improve source-only conventional-score attack and chord grouping on the opened discovery benchmark, replay through the unified timeline, and keep validation and sealed-test data closed.`
