# E9 Fretboard Explorer Backend Slice

Pass/warn/fail: pass

## Task summary

Implemented the first deterministic E9 Fretboard Explorer backend slice: a G-only, standard 10-string E9 row generator and pitch validator for the MVP Explorer.

Completed:

- Added a structured Explorer row model.
- Added deterministic standard E9 pitch/control resolution.
- Added pitch validation for generated rows.
- Added G major 2-string harmonized rows.
- Added G major 3-string diatonic harmony rows.
- Added G natural minor 3-string diatonic harmony rows.
- Added explicit advanced swap rows for `5-6-7`, `6-7-10`, and `5-7-8`.
- Added focused tests for row shape, row coverage, validation behavior, diminished labeling, and per-string mechanics.

Intentionally not changed:

- No UI changes.
- No API routing changes.
- No answer routing changes.
- No RAG, SGF/forum, transcript-guidance, corpus, embeddings, Chroma, scraper, deployment, auth, DNS, assets, or private-source changes.
- No commit or staging.

## Files changed

- `pocketsteel/fretboard_explorer.py`
- `tests/test_fretboard_explorer.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-backend-slice.md`

## What changed

### New backend module

`pocketsteel/fretboard_explorer.py` adds:

- `ExplorerRow`
- `ExplorerCandidate`
- `validate_explorer_candidate(...)`
- `validate_explorer_payload(...)`
- `g_major_two_string_rows()`
- `g_major_three_string_rows()`
- `g_natural_minor_three_string_rows()`
- `g_advanced_e_lower_pocket_rows()`
- `g_explorer_rows()`
- `build_g_explorer_payload()`

The module uses deterministic pitch math and standard E9 mechanics. It does not import retrieval, corpus, SGF, transcript, or RAG paths.

### New tests

`tests/test_fretboard_explorer.py` covers:

- Explorer row model shape.
- Explorer payload shape.
- G major 3-string diatonic harmony.
- G natural minor 3-string diatonic harmony.
- G major 2-string harmonized rows.
- Advanced swaps.
- `5-7-8` E-lower pocket rows.
- B+C invalidity on unvalidated string groups.
- Diminished triad vs partial m7b5 labeling.
- Per-string pedal/lever effects.
- No RAG/corpus/source dependency in generated rows.

## Generated row coverage

- G major 2-string harmonized rows: 40 rows.
- G major 3-string diatonic rows: 32 rows.
- G natural minor 3-string diatonic rows: 32 rows.
- Advanced G major `5-7-8` E-lower pocket rows: 2 rows at frets 8 and 20.
- Total G Explorer payload rows: 106.

Core grips:

- `3-4-5`
- `4-5-6`
- `5-6-8`
- `6-8-10`

Advanced swaps:

- `5-6-7`
- `6-7-10`
- `5-7-8`

## Validation rules implemented

- Key is limited to `G` for MVP.
- Frets must be `0-24`.
- Strings must be `1-10`.
- String groups must match generated string lists.
- Rows must be pitch validated before payload use.
- A pedal changes strings 5 and 10 only.
- B pedal changes strings 3 and 6 only.
- C pedal changes strings 4 and 5 only.
- E-raise changes strings 4 and 8 only.
- E-lower changes strings 4 and 8 only.
- Controls must affect at least one played string.
- A+B and B+C are tracked per affected string, not as whole-grip changes.
- B+C is rejected when C does not affect the played strings or when the resulting notes do not validate against the target chord.
- Major, minor, and diminished triads require pitch-class validation against the target root.
- Three-note `1-b3-b5` rows are labeled `diminished` and marked partial when they imply half-diminished function without b7.
- Generated labels use `no_pedals_no_levers` and mechanical `E-raise` / `E-lower` names.

## Tests and checks run

- `git status --short`
- `git branch --show-current`
- `.venv/bin/python -m py_compile pocketsteel/fretboard_explorer.py`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
  - Result: `9 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py -q`
  - Result: `52 passed`
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q`
  - Result: `25 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
  - Result: `5 passed`
- `.venv/bin/python -m pytest`
  - Result: `784 passed`
- `git diff --check`
  - Result: passed
- `git diff --no-index --check -- /dev/null pocketsteel/fretboard_explorer.py`
  - Result: no whitespace errors; exit 1 expected for `/dev/null` comparison.
- `git diff --no-index --check -- /dev/null tests/test_fretboard_explorer.py`
  - Result: no whitespace errors; exit 1 expected for `/dev/null` comparison.
- `git diff --no-index --check -- /dev/null docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-backend-slice.md`
  - Result: no whitespace errors; exit 1 expected for `/dev/null` comparison.

Note: after a final unused-import cleanup, `py_compile`, `tests/test_fretboard_explorer.py -q`, `git diff --check`, no-index whitespace checks, and full `pytest` were rerun and passed.

## Risks

- Scope is intentionally G-only; all-key transposition is not implemented.
- The Explorer payload is not wired into `/api/answer` or UI.
- The new rows depend on deterministic candidate formulas plus pitch validation; future expansion still needs table-wide validation before adding more keys or harmony types.
- Existing worktree contains broad unrelated dirty/untracked files. This slice did not touch them.

## Human decision needed

No for this backend slice. Future decisions are needed before:

- wiring this Explorer payload to API/UI;
- adding all-key transposition;
- using source-guidance explanations alongside deterministic rows.

## Safe-to-stage exact file list

- `pocketsteel/fretboard_explorer.py`
- `tests/test_fretboard_explorer.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-backend-slice.md`

## Files that must not be staged

- Any unrelated dirty or untracked worktree files.
- UI files.
- Corpus/private corpus files.
- Embeddings, Chroma/vector stores, scraper output.
- Deployment/auth/DNS files.
- Source-inbox/private source data.
- Assets/design files.

## Recommended next lane

Lane 15 QA / Answer Eval.

Suggested next prompt:

```text
Lane 15: QA the G-only deterministic E9 Fretboard Explorer backend slice in pocketsteel/fretboard_explorer.py and tests/test_fretboard_explorer.py. Verify row model shape, pitch validation, G major/minor coverage, advanced swap labeling, no RAG/corpus dependency, and readiness for a later UI/API wiring slice.
```

## Commit readiness

Safe to commit after human/Repo Steward exact-path review.
