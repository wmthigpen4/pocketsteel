# Lane 20 — Discovery Glyph Decoder and Validation Consensus Hardening

## Task summary

Implemented the next private Amazing Tablature engineering slice without opening sealed-test data:

- made malformed local-reader responses retry and fail closed;
- limited full-sheet multimodal reading to two pinned first-pass artifacts, with the third artifact reserved for focused disagreements;
- removed only unresolved high-recall candidates whose horizontal position exactly equals a detected barline from musical event accounting;
- added a discovery-only HOG/k-nearest-neighbor tab-glyph decoder with grouped content-unit cross-validation and abstention;
- registered the private glyph artifact separately from the arrangement challenger and source-transition decoder;
- added the eligible glyph decoder as an independent semantic vote in validation contact-sheet consensus.

No model was promoted, enabled in runtime, or exposed in the app. Validation remains evaluation-only and sealed test remains unopened.

## Private diagnostic result

The main discovery glyph artifact built during development was:

- decoder ID: `atg-c0fe5b851780f9e9`
- discovery examples: 1,245
- discovery content units: 17
- selected confidence threshold: 0.80
- grouped content-unit CV precision at that threshold: 95.2542%
- grouped content-unit CV coverage at that threshold: 23.6948%
- validation data used: false
- sealed-test data used: false

The main validation consensus was intentionally not reported as a pass. In the first 15 systems processed with the decoder, zero lines met the strict complete two-reader agreement gate. The decoder recovered additional cells, but remaining cells were withheld. This is a recognition blocker, not evidence that the arrangement ranker failed.

The exact glyph decoder and challenger must be rebuilt after this code is committed so their code revision and artifact lineage match the clean HEAD.

## Files changed

- `steel_guitar_rag/amazing_tablature_glyph_decoder.py`
- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_training.py`
- this handoff

Generated private artifacts beneath `corpus-private/melody-decisions/` were not staged and must remain ignored.

## Tests and checks

- `.venv/bin/pytest -q tests/test_amazing_tablature_training.py -k 'glyph' tests/test_amazing_tablature_extraction.py -k 'contact_sheet_consensus or page_furniture or glyph'`
  - 7 passed
- `.venv/bin/pytest -q`
  - 1,400 passed
- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_glyph_decoder.py steel_guitar_rag/amazing_tablature_training.py steel_guitar_rag/amazing_tablature_extraction.py scripts/amazing_tablature.py`
  - passed
- `git diff --check`
  - passed

## Integration notes

- The glyph decoder is a source-recognition aid, not a melody arrangement model.
- Its output cannot validate a cell by itself; validation consensus still requires at least two semantic readers to agree.
- Its training examples are derived visual features and semantic fret/control labels from approved discovery records only.
- Exact barline exclusion requires both `recognitionState=unresolved` and a position equal to a detected barline within `1e-7`; nearby attacks are retained.
- Conventional score recognition remains a separate validation component and cannot be masked by tab-cell agreement.

## Risk assessment

Medium. The new decoder is deliberately precision-first and abstains, but its current discovery-only coverage is limited. Validation cannot pass until complete independent score/tab ground truth or substantially stronger automatic recognition is available. Rollback is the scoped commit containing the seven files listed above; private generated artifacts are disposable and remain uncommitted.

## Human decision needed

No for this engineering slice. Human validation is required later only if automatic comparison reaches complete, compact ambiguous cases. Model promotion still requires explicit exact-model approval.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_glyph_decoder.py`
- `steel_guitar_rag/amazing_tablature_extraction.py`
- `steel_guitar_rag/amazing_tablature_training.py`
- `scripts/amazing_tablature.py`
- `tests/test_amazing_tablature_extraction.py`
- `tests/test_amazing_tablature_training.py`
- `docs/handoffs/task-completions/2026-07-23-0517-20-discovery-glyph-validation-consensus.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- unrelated historical untracked handoffs
- private reader caches, crops, candidates, reports, models, and registries

## Recommended next lane

Lane 20:

1. exact-path commit this green slice;
2. rebuild the main and licks discovery decoders and exact arrangement challenger from the resulting clean HEAD;
3. rerun discovery shadow/no-rereview accounting;
4. rerun validation consensus from caches;
5. prepare human review only for complete, compact ambiguities;
6. keep sealed test closed until all fixed validation gates pass and the engine is frozen.

## Commit readiness

Safe to commit

## Suggested next step

`Lane 20: Rebuild all discovery-only decoder and challenger artifacts from the clean commit, verify exact lineage and no-rereview accounting, and continue automatic validation comparison without opening sealed test.`
