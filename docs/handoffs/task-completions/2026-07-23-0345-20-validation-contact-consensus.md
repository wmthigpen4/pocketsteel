# Lane 20 — Validation contact-sheet semantic consensus

## Task summary

Replaced the validation tab localizer as the sole authority for event columns
with a source-only, three-reader semantic consensus preflight. Reader outputs
are compared after parsing through the exact source copedent, so typography
differences do not create false disagreements.

The preflight:

- Pins three distinct local vision-model artifact digests.
- Caches each read by image, labels, prompt, and reader contract.
- Reconstructs event columns directly from the labeled source contact sheets.
- Tries one global string-origin correction per line and requires mechanical
  consistency.
- Uses focused 3× card rereads only for disputed cells.
- Applies the discovery-only source transition decoder only to proven movement
  signatures.
- Abstains on all other attack-versus-hold decisions.
- Writes validation-only private candidates and a digest-pinned report.
- Never creates validation training evidence and never opens sealed-test data.

## Licks validation result

- Validation pages: 3.
- Systems: 6.
- Reconstructed event columns: 85 of 85.
- Reconstructed ordered events: 85.
- Complete machine candidates: 5 systems.
- Withheld incomplete: 1 system.
- Remaining unresolved cells: 1 starting-grip voice.
- Safely classified movement-only events: 17.
- `input-0008` system 1 is restored to 14 of 14 event columns.
- Validation may train: false.
- Sealed test accessed: false.

The sixth line retains all 21 event columns but remains withheld because one
voice in its initial grip lacks two-model semantic agreement.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`
- `pocketsteel/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-23-0345-20-validation-contact-consensus.md`

Generated candidates, caches, focused crops, and reports remain under ignored
`corpus-private/melody-decisions/`.

## Tests and checks

- Focused contact-consensus tests: 3 passed.
- Transition decoder and training tests: 40 passed.
- Full suite: 1397 passed.
- `git diff --check`: passed.
- Real licks validation consensus: 85/85 columns reconstructed, one cell
  withheld.

## Integration notes

This validates tablature state capture, not conventional score OCR and not the
arrangement ranker. Those scorecards must remain separate:

1. source-image recognition,
2. structured note-to-tab ranking,
3. source-specific movement decoding.

The exact challenger must be rebuilt after this commit because the extraction
and rules-code digests changed.

## Risk assessment

Medium. The pass reads validation imagery, but never trains from it. It is
fail-closed and preserves the fixed human validation gate. The main residual
risk is source-grid string-origin ambiguity; the implementation prefers a
mechanically complete detected origin and otherwise requires a unique global
offset.

## Human decision needed

No decision is needed now. One licks validation grip voice will eventually need
a tightly scoped human check unless another independent reader resolves it.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_extraction.py`
- `pocketsteel/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-23-0345-20-validation-contact-consensus.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- All unrelated untracked historical handoffs.

## Recommended next lane

Lane 20: exact-path commit, rebuild the discovery challenger and source decoder
from the clean HEAD, then run the same semantic contact-sheet preflight on the
main validation cohort. Keep sealed-test data closed.

## Commit readiness

Safe to commit.

## Suggested next step

Rebuild all private artifacts from the clean code revision, verify the exact
21-feature challenger lineage, and run main-cohort recognition preflight before
publishing any human audit.
