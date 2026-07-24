# Lane 20 Discovery-Derived Validation Reader Hardening

## Task summary

Used only already-opened discovery corrections to harden tablature event grouping and confidence accounting, then reran both validation cohorts against the same exact canonical challenger. Validation remained evaluation-only and the 63-page sealed test remained closed.

Two general defects were corrected:

- Empty string rows nominated by the high-recall event detector are no longer counted as separate missed symbols. A printed candidate column with no recognized state now produces one column-level blocker.
- Contact-sheet crops stop between neighboring detected event components so adjacent printed states are not presented to the vision reader as one token.

The authoritative extractor is now `lane20-score-tab-v17`. The validation challenger remains `at-1fa9630a173af769`, artifact SHA-256 `092bdd501490425c85732fb80af51f777270205d503b44aa242111a7e955aa50`. No validation decision was used for training.

## Discovery-only evidence

The correction ledger contains 928 unique discovery operations across the two cohorts. The licks corrections are dominated by attack, sustain, control timing, release, and slide semantics; the main packet contains those patterns plus more pitch/string corrections. The repeated corrections support treating event grouping and temporal state changes as first-class problems rather than relaxing mechanical or pitch validation.

A private five-page discovery replay targeted pages with prior neighboring-state merge failures. One eligible correction-heavy page supplied 136 replay cells and had 24 prior space-merged symbol failures. Under bounded crops, the replay produced zero space-merged tokens and zero reader-marked uncertain cells; 95 non-empty cells parsed through the tab grammar. The private replay artifact remains ignored under `corpus-private/melody-decisions/`.

## Validation results

Original `lane20-score-tab-v15` validation:

- Main: 395 blocking items, 721 tab events, 480 alignments.
- Licks: 12 blocking items, 64 tab events, 41 alignments.
- Total: 407 blocking items.

After empty-cell accounting (`lane20-score-tab-v16`):

- Main: 212 blocking items, 765 tab events, 510 alignments.
- Licks: 12 blocking items, 64 tab events, 41 alignments.
- Total: 224 blocking items.

After neighbor-bounded crops (`lane20-score-tab-v17`):

- Main: 192 blocking items, 747 tab events, 483 alignments, 229 derived decisions.
- Licks: 8 blocking items, 64 tab events, 45 alignments, 34 derived decisions.
- Total: 200 blocking items, a 50.9% reduction from the original 407.
- Failed pages: 0/31.
- Affected lines: 44 main plus 2 licks, 46 total.
- Zero-blocker pages: 4/28 main and 1/3 licks.
- Sealed test accessed: false.

The v17 main event/alignment totals are lower than v16. This is consistent with removal of duplicate neighboring reads, but it is not automatically accepted as truth. The 46 affected lines require compact human ground-truth review before arranger accuracy can be scored.

Remaining blocking classes:

- Main: 105 unresolved event columns, 48 uncertain symbols, 24 uncertain modifiers, 10 low-confidence symbols, 2 repeated-state ambiguities, 2 score OMR failures, and 1 tab-cell vision failure.
- Licks: 7 uncertain modifiers and 1 unresolved event column.

## Accuracy interpretation

The fixed `>95%` acceptance contract is for arrangement from normalized exact musical events. Typed note names, intervals, MIDI, and exact MusicXML should normalize to the same event representation and therefore bypass photo/scan recognition. Uploaded score images add a separate score/tab recognition stage that must be measured independently.

The arranger cannot yet receive an honest validation score because machine extraction is not validation truth. The next required evidence is human-approved line-level validation ground truth. No threshold may be relaxed, and no sealed-test cohort may open before validation passes and the exact model/rules/schema/validator freeze is recorded.

## Files changed

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-1108-20-discovery-derived-validation-reader-hardening.md`

Private generated validation and discovery replay artifacts remain ignored and must not be staged.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_extraction.py -k 'empty_high_recall or movement_chain_cell or low_confidence_tab_cell'` — 3 passed.
- `.venv/bin/python -m pytest -q tests/test_amazing_tablature_extraction.py -k 'tab_cell_crop or empty_high_recall or movement_chain_cell'` — 3 passed.
- `.venv/bin/ruff format steel_guitar_rag/amazing_tablature_extraction.py tests/test_amazing_tablature_extraction.py` — 2 files formatted.
- `.venv/bin/ruff check steel_guitar_rag/amazing_tablature_extraction.py tests/test_amazing_tablature_extraction.py` — passed.
- Main validation extraction — 28/28 processed, 0 failures, exact challenger pin retained.
- Licks validation extraction — 3/3 processed, 0 failures, exact challenger pin retained.
- `.venv/bin/python scripts/amazing_tablature.py shadow-test-discovery at-1fa9630a173af769 --max-review-lines 12` — 1,060 decisions, 954 exact source agreements, 956 expert-acceptable, 16 reviewed preferences accounted once, 4 exact lines/7 current disagreements suppressed from rereview, 0 selected review lines, `validationAccessed=false`, `sealedTestAccessed=false`.
- `.venv/bin/python -m pytest -q` — final rerun 1,341 passed in 55.40 seconds.

## Integration notes

The next review surface must be one chronological line at a time: original score and tab together, captured score notes/octaves, captured tab movements, event-count comparison, and one line-level correct/corrected/exclude decision. It must not expose a long per-cell warning list. The 46 affected lines are the correction-priority set; clean lines still need sufficient independent sampling to prevent a rubber-stamp ground truth set.

After validation truth is approved, score the same arranger output through exact MusicXML, MIDI, typed note-name, interval-name, and canonical normalized-event adapters. Equivalent inputs must normalize identically. Only then compute top-choice, top-three, cohort, evidence-mode, and mechanical-validity metrics.

## Risk assessment

Medium. Blocking uncertainty was cut in half without weakening mechanical validation, but image recognition is still not validation truth. The bounded crop can remove accidental neighboring reads and can also expose missed event localization; human line review is required to distinguish those cases. Rollback is the prior extractor contract and private v16 extraction artifacts.

## Human decision needed

No decision is needed for this completed hardening slice. Human line-level validation review will be required after the compact audit is prepared.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/handoffs/task-completions/2026-07-22-1108-20-discovery-derived-validation-reader-hardening.md`

## Files that must not be staged

- `corpus-private/`
- `docs/handoffs/task-completions/integration-status.md`
- Unrelated historical handoffs and parked files
- Any raw source, validation imagery, review data, model artifact, extraction output, or sealed-test artifact

## Recommended next lane

Lane 20 to build the compact 46-line validation audit, followed by Lane 15 to independently approve validation ground truth and score the exact structured-input adapters.

## Commit readiness

Safe to commit.

## Suggested next step

Prepare a digest-pinned compact validation line audit for the 46 affected lines plus a bounded sample of clean lines, with one line-level decision and no cell-by-cell correction burden. Keep validation annotations out of training and keep all sealed-test data closed.
