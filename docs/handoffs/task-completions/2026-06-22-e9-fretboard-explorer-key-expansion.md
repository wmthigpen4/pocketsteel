# 2026-06-22 Lane 05 - E9 Fretboard Explorer Key Expansion

## Task Summary

Expanded the deterministic E9 Fretboard Explorer backend from G-only row generation to transposed major and natural minor keys. The implementation keeps musical truth in the pitch validator: every generated row is still resolved against standard 10-string E9 mechanics, checked for intervals/chord quality, and emitted only after validation.

Intentionally not changed: UI, corpus, embeddings, Chroma, scraper output, deployment, auth, DNS, assets, private source data, SGF/RAG behavior, or unvalidated markdown ingestion.

## Files Changed

- `steel_guitar_rag/fretboard_explorer.py`
- `tests/test_fretboard_explorer.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-key-expansion.md`

## Keys Supported

The Explorer now accepts these learner-facing key spellings:

- `C`, `C#`, `Db`, `D`, `D#`, `Eb`, `E`, `F`, `F#`, `Gb`, `G`, `G#`, `Ab`, `A`, `A#`, `Bb`, `B`

The original `build_g_explorer_payload()` and `g_*` row helpers remain available for compatibility. New generalized helpers include `build_explorer_payload(key)` and `explorer_rows(key)`.

## What Changed

- Added key normalization and key slugging for row IDs.
- Added transposed fret generation from the existing G-validated row formulas.
- Added key-aware major and natural minor scale spelling.
- Preserved canonical pitch validation while separating learner-facing `display_notes`.
- Generalized two-string harmonized, three-string major, three-string natural minor, and advanced E-lower pocket row builders.
- Added duplicate-row suppression for transposed octave-equivalent rows that collapse onto the same validated fret.
- Expanded payload filters from `["G"]` to the supported key list.
- Updated payload validation so non-G keys are accepted only if they normalize to the supported key list.
- Added tests for C, D, F, Bb, and C natural minor display spelling while preserving all existing G behavior.

## Generated Row Coverage

- Major three-string diatonic rows for core grips:
  - `3-4-5`
  - `4-5-6`
  - `5-6-8`
  - `6-8-10`
- Natural minor three-string diatonic rows for the same core grips.
- Major two-string harmonized rows.
- Advanced/gated swaps remain present through pitch validation:
  - `5-6-7`
  - `6-7-10`
  - `5-7-8`
- Advanced E-lower `5-7-8` pocket rows remain explicitly labeled as `advanced`.

## Validation Rules Implemented

- A, B, C, E-raise, and E-lower changes remain per-string mechanical changes.
- B+C invalidity for unsupported string groups still fails by actual played strings and notes.
- Rows must stay within frets `0-24` and strings `1-10`.
- Full diminished/partial half-diminished labeling remains unchanged: three-note `1-b3-b5` rows are diminished triads with partial `viiø`/`iiø` wording and omitted `b7`.
- Flat-key display spellings are learner-facing only; pitch identity remains canonical from the pitch engine.
- Generated rows remain independent from RAG, SGF, corpus, transcript guidance, and unvalidated markdown tables.

## Tests And Checks

- `git status --short` - run before implementation; large unrelated dirty/untracked worktree present.
- `git branch --show-current` - `feature/answer-api`.
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - `15 passed`.
- `.venv/bin/python -m pytest` - `795 passed`.
- `git diff --check` - passed.

## Risk Assessment

Risk: medium-low. The change is isolated to the Explorer backend module and tests, but it expands generated output for many keys and therefore affects any future caller that uses `build_explorer_payload(key)`.

Rollback: revert `steel_guitar_rag/fretboard_explorer.py` and `tests/test_fretboard_explorer.py` to the prior G-only helpers. Existing G wrappers were preserved, so current G callers should remain stable.

## Human Decision Needed

No immediate decision required for this backend slice.

Future product/architecture decision: whether UI key selectors should expose all enharmonic aliases or a reduced 12-key display set.

## Safe-To-Stage Exact File List

- `steel_guitar_rag/fretboard_explorer.py`
- `tests/test_fretboard_explorer.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-key-expansion.md`

## Files That Must Not Be Staged

- Unrelated dirty docs, corpus metadata, RAG scripts, source-inbox files, UI brand assets, `public/`, `ui/brand/`, `Neon Sign/`, generated/private/corpus/vector/deployment/auth artifacts, and any other untracked files outside the safe-to-stage list.

## Recommended Next Lane

Lane 15 QA / Answer Eval: run focused Explorer key-expansion QA and, if useful, protected-preview checks once a UI key selector consumes the generalized payload.

## Commit Readiness

Safe to commit if exact-path staging is limited to the safe-to-stage files above.

## Suggested Next Step

Lane 15 prompt:

```text
Lane 15: QA the E9 Fretboard Explorer key expansion. Verify G behavior is unchanged, C/D/F/Bb major rows validate, C natural minor display spelling uses flats, advanced swaps remain gated, and no UI/corpus/deployment/private-source files changed.
```
