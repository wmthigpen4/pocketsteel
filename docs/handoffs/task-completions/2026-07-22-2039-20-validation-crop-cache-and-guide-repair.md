# Validation crop, OMR cache, and guided-order repair

## Task summary

Repaired three discovery/validation extraction defects that were preventing structurally complete independent comparisons before exact-challenger evaluation.

1. The OMR derivative no longer trims the already bounded score-system crop horizontally. The previous staff-run boundary could remove the clef/key at the left and terminal noteheads at the right.
2. Audiveris output is now cached beneath an immutable source-crop SHA-256 directory. A changed derivative can no longer reuse MusicXML produced from stale crop bytes.
3. In a numbered guided tablature capture, guide order is authoritative. Noisy model-reported x coordinates are retained for diagnostics but cannot reject a complete guide-indexed state transcription; callers still replace ordinal positions with exact detector geometry before validation.

No raw image, reviewed annotation, validation truth, sealed-test asset, runtime model policy, or production UI was changed.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2039-20-validation-crop-cache-and-guide-repair.md`

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_extraction.py` — 152 passed.
- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_extraction.py tests/test_amazing_tablature_training.py tests/test_amazing_tablature_input_parity.py tests/test_amazing_tablature_score_sequence.py tests/test_melody_arranger_decision_fixtures.py tests/test_copedent_transfer.py tests/test_amazing_tablature_sealed_test.py` — 223 passed.
- `.venv/bin/python -m py_compile pocketsteel/amazing_tablature_extraction.py tests/test_amazing_tablature_extraction.py` — passed.
- `git diff --check` — passed before handoff creation; rerun required before commit.

The sealed-test test module uses synthetic unit fixtures only. No private sealed-test mapping, imagery, extraction, or ground truth was opened.

## Integration notes

Because extraction code participates in Amazing Tablature lineage, the exact complete-discovery challenger must be rebuilt from the committed HEAD before validation is scored. The rebuilt model should retain the same 702-example dataset, 21-feature schema, and numerical weights if lineage is the only changed input. Validation extraction and machine-only remediation should then be replayed using that exact model ID.

Audiveris cache directories are append-only by crop digest. Older unkeyed output is preserved but is not selected for a different crop.

## Risk assessment

Low-to-medium. The fixes are fail-closed and covered by focused tests. Preserving full horizontal width can include more page furniture, but the parent system crop is already horizontally bounded and the derivative still tightens vertically. Validation replay will measure whether the repair improves completeness without weakening pitch, mechanics, or provenance gates.

## Human decision needed

No.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-2039-20-validation-crop-cache-and-guide-repair.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Existing unrelated untracked historical handoffs
- `corpus-private/**`
- Raw images, private annotations, validation ground truth, sealed-test data, and generated model artifacts

## Recommended next lane

Lane 20: commit this exact repair, rebuild the complete-discovery challenger from the clean HEAD, replay validation extraction/remediation, and evaluate only structurally complete validation records.

## Commit readiness

Safe to commit.

## Suggested next step

Rebuild the canonical complete-discovery challenger after the scoped commit, verify lineage/no-rereview accounting, then run automated validation replay. Do not present another human audit unless a small complete ambiguity set remains after machine gates.
