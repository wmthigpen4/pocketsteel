# Lane 20 Canonical Validation Extraction

## Task summary

Built the clean canonical discovery challenger, independently shadow-checked its discovery lineage/no-rereview accounting, opened only the two validation cohorts under an exact model pin, compared two local tab readers, completed the stronger validation extraction for all 31 pages, and fixed one fail-closed score-crop geometry defect found during that run.

Canonical model: `at-1fa9630a173af769`, parent `at-f1adc00edf1b27db`, 702 examples, four style families, exact 16 reviewed / 6 training / 10 co-valid preferences, complete discovery disposition, printed-score scope reported separately, non-promotable. Model code revision: `3df45029ac0a2dbbc15e59dfa62a21e2a50211d0`. Artifact SHA-256: `092bdd501490425c85732fb80af51f777270205d503b44aa242111a7e955aa50`.

Discovery shadow: 1,060 decisions, 954 exact source agreements (90.0%), 956 expert-acceptable (90.1887%), one known preference failure, four exact lines suppressed from rereview, seven current disagreements suppressed, zero lines selected for review. This remains a noisy extraction shadow and is not the structured-input >95 accuracy claim.

Validation was opened after the canonical model existed and was pinned to that exact artifact. The 63 sealed-test pages remain closed.

## Validation extraction findings

The fast Apple tab reader was not adequate:

- Main 28: 34 tab events, 15 alignments, 1,550 blocking items.
- Licks 3: 4 tab events, 2 alignments, 89 blocking items.

The stronger local `gemma4:12b` reader completed all 31 validation pages:

- Main 28: 964 score events, 721 tab events, 480 alignments, 191 derived decisions, 395 blocking items.
- Licks 3: 78 score events, 64 tab events, 41 alignments, 30 derived decisions, 12 blocking items.
- Failures: 0 after the geometry retry.
- Main pages with zero blockers: 5/28; licks pages with zero blockers: 1/3.
- Dominant unresolved classes: uncertain/low-confidence tab symbols and modifiers. Unverified alignments and mechanically invalid hypotheses remain excluded rather than promoted as facts.

The stronger reader improved main tab-event capture from 34 to 721 and main alignments from 15 to 480. It improved licks tab-event capture from 4 to 64 and alignments from 2 to 41. The remaining blocker count is still too large for a humane review packet; none was handed to the user.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`: ignores a connector-tail suppression rectangle when the tail begins below the crop.
- `tests/test_amazing_tablature_extraction.py`: regression test for the short-crop geometry case.
- `docs/handoffs/task-completions/2026-07-22-1010-20-canonical-validation-extraction.md`: this handoff.

Private generated artifacts beneath `corpus-private/melody-decisions/` include the canonical model, discovery shadow, and validation extraction. They remain ignored and must not be staged. No raw source was modified.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_extraction.py -k 'score_omr_derivative'` — 2 passed, 123 deselected.
- Stronger validation extraction — 31/31 pages processed, 0 failures, exact model pin present, sealed test unopened.
- `.venv/bin/python -m pytest -q` — 1,339 passed in 56.79 seconds.

## Integration notes

The >95 contract concerns exact structured inputs after notation normalization, not image recognition. Validation cannot yet score the arranger because the held-out page facts are not human-approved ground truth. Do not treat machine extraction as validation truth. Do not ask the user to review the current 407 blocking items individually. The next internal slice should use discovery-approved corrections to improve token grouping/confidence and then rebuild validation extraction before constructing a compact, page/line-level ground-truth UI.

No validation decision may enter training. No threshold may be changed after validation results. Do not open sealed-test data until validation passes and the exact rules/model/schema/validator freeze is recorded.

## Risk assessment

Medium. Validation is now opened, so its details may guide rule/extractor refinement but cannot become training evidence. The sealed test remains unbiased. The major risk is confusing image-reader accuracy with arranger accuracy or allowing unresolved validation hypotheses into ground truth; current gates fail closed.

## Human decision needed

No immediate decision and no review request. Machine-side reduction of the validation error surface should continue first.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-1010-20-canonical-validation-extraction.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Unrelated historical handoffs
- `corpus-private/`
- Any source, extraction, review, model, validation, or sealed-test artifact

## Recommended next lane

Lane 20 for discovery-derived validation-reader hardening, followed by Lane 15 for independent validation ground-truth review and scoring.

## Commit readiness

Safe to commit.

## Suggested next step

Replay the dominant validation recognition failures against discovery-approved correction patterns without training on validation, implement only general rules supported by discovery evidence, rerun validation extraction, and create a compact line-level ground-truth review only when the blocker surface is materially smaller. Keep the sealed test closed.
