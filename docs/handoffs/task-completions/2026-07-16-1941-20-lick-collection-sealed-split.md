# Lane 20 — Lick collection sealed split

## Task summary

Registered the second private image batch and split it before training. The batch contains 34 score/tab lick pages plus one separately registered source-copedent evidence image. The evidence image is hashed and verified but excluded from discovery, validation, test, and annotation queues.

Created batch `atb-20260716-licks-34`, pinned source profile `source-e9-abc-defg-d48-e29-v1` revision 1, and sealed an exact 24 discovery / 3 validation / 7 test partition. The partition digest is `2544f04bddd6185ec8b4a9ba6ae96f835823e0bcf2a73788a0184393201e25fc`. Three previously viewed pages were forced into discovery. Each independently complete lick page is an indivisible provisional content unit.

The first batch remains unchanged at 194 discovery / 28 validation / 56 sealed test with partition digest `2ceafe866df5b74b576ebef0dd1299001c0337c2770a1901eb9af85f6b64acec`.

No OCR, transcription, annotations, ground truth, rule refinement, challenger training, embeddings, runtime integration, or source modification was performed.

## Files changed

- `pocketsteel/e9_copedents.py`
  - Added the reviewed source-only copedent profile used by the lick batch.
- `pocketsteel/amazing_tablature_training.py`
  - Added separate source-copedent evidence registration and verification.
  - Added explicit content-unit boundaries and deterministic scalable partition selection.
- `scripts/amazing_tablature.py`
  - Added intake and partition CLI options for those capabilities.
- `tests/test_copedent_transfer.py`
  - Added exact source-profile mechanics coverage.
- `tests/test_amazing_tablature_training.py`
  - Added evidence-exclusion and 24/3/7 sealed-split regression coverage.
- `docs/amazing-tablature-training.md`
  - Documented copedent evidence and explicit content-unit intake.
- This handoff.
- Ignored private Lane 20 manifests and split artifacts were generated and must not be staged.
- Deleted files: none.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_training.py tests/test_copedent_transfer.py` — 27 passed.
- `.venv/bin/python -m ruff check pocketsteel/amazing_tablature_training.py pocketsteel/e9_copedents.py scripts/amazing_tablature.py tests/test_amazing_tablature_training.py tests/test_copedent_transfer.py` — passed.
- `.venv/bin/python -m compileall -q pocketsteel scripts/amazing_tablature.py` — passed.
- Private intake verification — 35/35 assets matched; 34 score/tab inputs and one excluded copedent-evidence asset.
- Idempotent intake verification — both the existing 278-page batch and new 34-page batch resumed with their original immutable digests.
- Private split verification — 34 unique inputs and hashes; exact 24/3/7 counts; three viewed pages in discovery; sealed directory mode `0700`; sealed manifest mode `0600`; test membership absent from normal status.
- Existing batch verification — original 194/28/56 counts, digest, and unopened status unchanged.
- `git diff --check` — passed.

## Integration notes

- Both requested collections now have sealed discovery/validation/test partitions.
- The current registry still names the 278-page batch as the single authoritative training batch. Before combined training, Lane 20 must introduce an explicit multi-batch dataset contract so discovery and validation records from both profiles are included while each sealed test remains isolated.
- Semantic extraction must use the profile pinned to each batch. Printed control letters must not be transferred between the two source profiles by label alone.
- Page-type and musical-content stratification remain pending independent review; no semantic inspection of held-out pages occurred.

## Risk assessment

Medium. Leakage controls, exact counts, source immutability, copedent pinning, and sealed permissions pass. Remaining risks are unknown rights/allowed uses, provisional page-level content-unit review, and the not-yet-implemented multi-batch training contract. Rollback is non-destructive: preserve this unopened batch and create a corrected replacement if independent review identifies a grouping problem.

## Human decision needed

Yes, before training: confirm permitted private training and intended downstream uses for the source material. The training phase should also retain both sealed tests as independent cohorts.

## Safe-to-stage exact file list

- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-16-1941-20-lick-collection-sealed-split.md`
- `pocketsteel/amazing_tablature_training.py`
- `pocketsteel/e9_copedents.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_training.py`
- `tests/test_copedent_transfer.py`

## Files that must not be staged

- Everything under `corpus-private/`.
- Both source image collections.
- Existing modified `docs/handoffs/task-completions/integration-status.md`.
- All unrelated untracked handoffs and parked worktree files.

## Recommended next lane

Lane 15 for an independent private review of both unopened splits, followed by Lane 20 to implement the multi-batch dataset contract and process the complete discovery pools.

## Commit readiness

Safe to commit

## Suggested next step

`Lane 15: Independently review the unopened 278-page and 34-page lick splits for content-unit integrity and category coverage without exposing sealed membership to rule-development work.`
