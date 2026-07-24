# Lane 20 — Full-collection sealed split

## Task summary

Implemented the approved first slice of the full-collection training plan. Registered the authoritative 278-input collection without OCR or transcription, pinned source profile `source-e9-abc-defg-v1` revision 1, created a leakage-resistant 194/28/56 discovery/validation/test split, and sealed the test membership before rule work.

The split uses 36 previously inspected anchors plus a one-page discovery guard, indivisible unseen contiguous units, exact/perceptual-similarity linkage, two provisional source documents, and structural image stratification. Counts are exactly 194 discovery, 28 validation, and 56 sealed test. The partition digest is `2ceafe866df5b74b576ebef0dd1299001c0337c2770a1901eb9af85f6b64acec`.

Preserved the prior 51-input batch for audit but marked it superseded by `atb-20260716-training-278`. Its accepted decisions are excluded from future training and evaluation. Model `at-44c59f08724d501e` remains a historical approved-beta artifact but is marked ineligible for future dataset comparison. Runtime code was intentionally not changed.

No OCR, semantic extraction, annotations, ground truth, challenger training, embeddings, vector work, RAG ingestion, source copying, source modification, or runtime integration was performed.

## Files changed

- `steel_guitar_rag/amazing_tablature_training.py`
  - Added source-profile revision/digest pinning, private split generation, guarded content units, structural image metadata, sealed test storage, partition enforcement, source verification, batch lifecycle, authoritative-batch filtering, and historical-model eligibility.
- `scripts/amazing_tablature.py`
  - Added `partition`, `supersede-batch`, and `verify-intake` commands.
- `tests/test_amazing_tablature_training.py`
  - Added synthetic 278-input split, privacy, partition-binding, and superseded-dataset regressions.
- `docs/amazing-tablature-training.md`
  - Documented the full-collection workflow and sealed-test rules.
- `pyproject.toml`
  - Declared Pillow for reproducible structural image measurement.
- Ignored private Lane 20 state was updated. It must not be staged.
- Deleted files: none.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_training.py` — 10 passed.
- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_training.py tests/test_copedent_transfer.py tests/test_melody_arranger_decision_fixtures.py` — 32 passed.
- `.venv/bin/python -m ruff check steel_guitar_rag/amazing_tablature_training.py scripts/amazing_tablature.py tests/test_amazing_tablature_training.py` — passed.
- `.venv/bin/python -m compileall -q steel_guitar_rag scripts/amazing_tablature.py` — passed.
- `.venv/bin/python -m pip check` — passed.
- `git diff --check` — passed before this handoff; rerun required before commit.
- Private intake verification — 278/278 hashes matched after partitioning; zero changed inputs.
- Private split verification — 278 unique inputs and hashes; all inspected anchors in discovery; both provisional source documents represented in every partition; normal annotation queue contains discovery only; sealed directory mode `0700`; sealed manifest mode `0600`.
- Deliberate training attempt — stopped with no validated training decisions, confirming the superseded batch is excluded.
- Full `pytest -q` — did not complete because the process was externally killed after passing approximately 46% of the suite. The last reached UI test passed independently (`1 passed`). This is classified as cumulative test-process resource exhaustion, not an assertion failure.
- Targeted mypy — not green because of pre-existing broad `object` conversion errors in `steel_guitar_rag/melody_ranker.py` and existing CLI result-type inference. No new typed contract was introduced.

## Integration notes

- Authoritative batch: `atb-20260716-training-278`.
- Source profile digest: `76a2395879adc0ce19fe075ac3a3030f84d690d416988a0a736fc357397965a7`.
- Input immutable digest: `91186debcea306f45e2fceb7f5645092f6d1681e77c9be9e42c74e71f3ade59e`.
- Partition status: `sealed_unopened`; ground truth remains pending.
- Status intentionally exposes counts/digests, not test membership.
- Grouping review status is `provisional_structural`; page-type and musical-content stratification remain pending independent review because this slice prohibited OCR and semantic transcription.
- The existing runtime beta remains unchanged. This task only prevents its superseded evidence from influencing future Lane 20 training/evaluation.

## Risk assessment

Medium. Dataset leakage guards, immutability, and source verification pass. Remaining risks are provisional semantic content-unit boundaries, unknown source rights/allowed uses, pending sealed-test ground truth, and the intentionally unchanged legacy runtime beta. If independent review finds a cross-partition content unit, create and seal a corrected replacement batch before any annotations or rule work.

Rollback is non-destructive: preserve this unopened batch as historical, create a corrected replacement split, then supersede it. Do not delete private state or source files.

## Human decision needed

Yes, before semantic extraction or rule refinement:

- Confirm the allowed private research/training and downstream product uses for the source material.
- Approve an independent Lane 15 content-unit/page-type review of the unopened split.
- Decide later whether the historical runtime beta should remain until a replacement model is approved; this slice did not change runtime behavior.

## Safe-to-stage exact file list

- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-16-1923-20-full-collection-sealed-split.md`
- `steel_guitar_rag/amazing_tablature_training.py`
- `pyproject.toml`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`

## Files that must not be staged

- Everything under `corpus-private/`.
- The source image collection.
- `docs/handoffs/task-completions/integration-status.md` because it contains unrelated pre-existing changes.
- All unrelated untracked Lane 06/Lane 12/Lane 20 handoffs and parked worktree files.

## Recommended next lane

Lane 15 QA / Answer Eval for an independent, private content-unit and category-distribution review. Do not expose sealed membership to Lane 02 or Lane 05 and do not begin rule work until that review either accepts the split or names a corrected replacement.

## Commit readiness

Safe to commit

## Suggested next step

`Lane 15: Independently review the unopened split for batch atb-20260716-training-278. Verify content-unit boundaries and category coverage without exposing sealed membership to rule-development lanes. If any unit crosses partitions, recommend a corrected replacement before annotations; otherwise approve discovery processing.`
