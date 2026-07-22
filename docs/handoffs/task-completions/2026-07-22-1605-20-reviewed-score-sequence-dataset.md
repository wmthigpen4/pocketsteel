# Lane 20 — Reviewed score-sequence training dataset

## Task summary

Converted the frozen, already-opened discovery score corrections into one immutable private image-to-sequence training manifest. Each target is an ordered sequence of human-approved pitch groups. The target deliberately excludes unreviewed duration, rhythm, ties, and horizontal localization, and includes no tablature or source text.

Also tested and rejected four dependency-free visual/correction formulations before integrating any model:

- balanced ridge patch classifier: zero exact held-out development lines and zero exact shadow lines;
- nearest-shape patch matcher: no development cross-validation improvement and no shadow-line improvement;
- HOG/linear-SVM union: no development or shadow-line improvement and one shadow regression;
- small NumPy MLP: no calibration improvement, no shadow improvement, and three shadow regressions;
- learned pitch-set correction table: no stable correction rule survived grouped development cross-validation.

None of those candidates was committed, frozen, promoted, or exposed for human review.

Intentionally not changed:

- no validation or sealed-test data was opened;
- no raw image was copied or modified;
- no current reviewed record was modified;
- no training run or model promotion was started;
- no review packet, embeddings, runtime wiring, or public artifact was created.

## Files changed

- `pocketsteel/amazing_tablature_extraction.py`
  - added strict construction of human-approved pitch/chord sequence targets;
  - added immutable private dataset creation from the frozen score benchmark;
  - enforces reviewed-record digests and model-training authorization;
  - excludes rhythm, ties, horizontal boxes, tablature, and source text.
- `scripts/amazing_tablature.py`
  - added `build-discovery-score-sequence-dataset`.
- `tests/test_amazing_tablature_extraction.py`
  - verifies pitch/chord labels and rejection of partially reviewed targets;
  - verifies unapproved rhythm, ties, and coordinates cannot enter a target.
- `docs/amazing-tablature-training.md`
  - documents the private dataset command and its privacy/lineage contract.
- This handoff.

Private ignored artifact, never to be staged:

- `review/automation/reviewed-score-sequence-dataset-v1/manifest-a5a58c4c3d47.json`

## Dataset result

Manifest digest: `a5a58c4c3d471476e0d83d3e5153eade95099529d6362ea198c2f8882f974371`

| Subset | Cases | Pages | Content units | Attack groups | Notehead labels |
|---|---:|---:|---:|---:|---:|
| Development | 27 | 21 | 19 | 271 | 541 |
| Opened shadow | 12 | 9 | 8 | 105 | 225 |
| Total | 39 | 30 | 23 | 376 | 766 |

The shadow subset is already-opened discovery regression evidence, not an unbiased holdout. The manifest preserves that classification and cannot claim promotion eligibility.

Manifest safety flags:

- `sourceTextIncluded: false`
- `tablatureIncluded: false`
- `rawImagesCopied: false`
- `reviewPacketCreated: false`
- `currentPageRecordsModified: false`
- `trainingStarted: false`
- `promotionEligible: false`
- `validationAccessed: false`
- `sealedTestAccessed: false`

## Tests and checks

- `.venv/bin/python -m pytest tests/test_amazing_tablature_extraction.py -k 'reviewed_score_sequence_target or source_head_grouping or source_score_semantic_repair' -q`
  - PASS: 6 passed, 145 deselected.
- `.venv/bin/python scripts/amazing_tablature.py build-discovery-score-sequence-dataset --help`
  - PASS.
- `.venv/bin/python scripts/amazing_tablature.py build-discovery-score-sequence-dataset atb-20260716-training-278-semantic-v2`
  - PASS; manifest digest above.
- `.venv/bin/python -m pytest tests/test_amazing_tablature_extraction.py -q`
  - PASS: 151 passed.
- `git diff --check`
  - PASS.

## Integration notes

The corrections now have a model-ready contract that does not invent pixel boxes. A proper trainer should consume the full conventional-score line and emit an ordered sequence of simultaneous pitch groups. It should use a CTC or equivalent sequence loss, train only on development, choose thresholds/hyperparameters with page-grouped development folds, and score the opened shadow once per frozen candidate. The current sample is small, so scan-style augmentation and/or a reviewed pretrained OMR backbone will likely be necessary.

Any new training dependency must stay in an isolated private trainer environment and must not become an application runtime dependency. Exact model weights, optimizer state, and training logs must remain ignored under `corpus-private/`.

## Risk assessment

Risk: low to medium.

The committed code only creates a private manifest and does not train or promote a model. The main risk is future overfitting: 39 lines and 766 noteheads are useful supervision but insufficient evidence for production accuracy without page-grouped evaluation and later governed validation.

## Human decision needed

No.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_extraction.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `docs/amazing-tablature-training.md`
- `docs/handoffs/task-completions/2026-07-22-1605-20-reviewed-score-sequence-dataset.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- all unrelated untracked historical handoffs
- everything beneath `corpus-private/`
- source images, reviewed records, private manifests, model weights, logs, embeddings, and indexes

## Recommended next lane

Lane 20 Amazing Tablature Training.

## Commit readiness

Safe to commit.

## Suggested next step

Build an isolated private full-line sequence trainer around `reviewed-score-sequence-dataset-v1`. Train on development only, use page-grouped development folds, freeze the exact candidate before opened-shadow scoring, and preserve the unified no-review gate. Do not open validation or sealed-test data.
