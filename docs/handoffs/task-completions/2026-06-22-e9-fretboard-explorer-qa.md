# E9 Fretboard Explorer Backend QA

Pass/warn/fail: **warn**

## Task summary

Independently QA-reviewed the Lane 05 deterministic E9 Fretboard Explorer backend slice before UI work.

Completed:

- Read `AGENTS.md`.
- Read `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-backend-slice.md`.
- Inspected the new backend row generator and tests.
- Ran focused and full test suites.
- Ran an independent row-summary and invariant script against generated rows.
- Verified no production/UI/API/RAG/corpus wiring was introduced by the Explorer module.

Intentionally not changed:

- No backend implementation edits.
- No UI edits.
- No corpus, Chroma, embeddings, scraper output, deployment, auth, DNS, assets, or private source data touched.
- No staging or commit.

## Tested state

- Branch: `feature/answer-api`
- Current committed HEAD during QA: `891bf1e`
- QA tested working-tree Lane 05 files:
  - `pocketsteel/fretboard_explorer.py`
  - `tests/test_fretboard_explorer.py`
  - `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-backend-slice.md`
- Note: the Explorer slice files were untracked during QA, so this was a working-tree validation, not a committed-HEAD validation.

## Files inspected

- `AGENTS.md`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-backend-slice.md`
- `pocketsteel/fretboard_explorer.py`
- `tests/test_fretboard_explorer.py`
- `pocketsteel/fretboard_examples.py` helper functions for note, interval, and pitch resolution
- `git status --short`
- Recent git log / HEAD

## Files changed

- Created `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-qa.md`

No tests or fixtures were added. Existing focused tests plus independent QA scripting covered the requested hard validation rules without needing code edits.

## QA coverage

Validated:

1. G major 2-string harmonized rows.
2. G major 3-string diatonic harmony rows.
3. G natural minor 3-string diatonic harmony rows.
4. Core grips:
   - `3-4-5`
   - `4-5-6`
   - `5-6-8`
   - `6-8-10`
5. Advanced swaps:
   - `5-6-7`
   - `6-7-10`
   - `5-7-8`
6. Per-string pedal/lever mechanics.
7. Diminished vs partial m7b5 labeling.
8. Scale-degree ordering.
9. No RAG/corpus dependency for deterministic rows.
10. Full payload validation and duplicate-id checks.

## Validated rows

Generated row counts:

- Total Explorer payload rows: `106`
- G major 2-string harmonized rows: `40`
- G major 3-string diatonic rows: `32`
- G natural minor 3-string diatonic rows: `32`
- Advanced `5-7-8` E-lower pocket rows: `2`

Harmony counts:

- `two_string_harmonized`: `40`
- `three_string_diatonic`: `64`
- `advanced_pocket`: `2`

Scale counts:

- `major`: `74`
- `natural_minor`: `32`

String groups observed:

- `3-4`
- `3-4-5`
- `3-5`
- `4-5-6`
- `4-6`
- `5-6`
- `5-6-7`
- `5-6-8`
- `5-7-8`
- `6-10`
- `6-7-10`
- `6-8-10`

Core-grip and advanced-swap observations:

- `3-4-5` and `4-5-6` cover full major and natural-minor diatonic rows.
- `5-6-8` and `6-8-10` cover no-pedals/no-levers major rows and diminished/E-raise rows; minor rows correctly move to advanced swap grips where needed.
- `5-6-7` and `6-7-10` carry the A+B minor rows that would not validate on `5-6-8` / `6-8-10`.
- `5-7-8` appears only as an advanced E-lower pocket grip at frets `8` and `20`.

## Hard-rule validation

Passed:

- A pedal affected strings `5` and `10` only.
- B pedal affected strings `3` and `6` only.
- C pedal affected strings `4` and `5` only.
- E-raise affected strings `4` and `8` only.
- E-lower affected strings `4` and `8` only.
- A+B did not imply every string in a grip changed.
- B+C is rejected on `6-8-10` because C does not affect the played strings.
- B+C is rejected on `5-6-8` when resulting pitches do not validate.
- Full major/minor rows contain required triad intervals.
- Diminished rows contain `1-b3-b5/#11`, are marked `partial`, and disclose omitted `b7`.
- No generated row used ambiguous `open` in row IDs or `position_family`; generated labels use `no_pedals_no_levers`.
- `5-7-8` remains `difficulty_tier: advanced`, `position_family: e_lower_pocket`.
- Explorer module imports pitch helpers only; no RAG, SGF/forum retrieval, corpus, Chroma, scraper, API route, or UI dependency was found.

## Issues found

No hard QA blockers found.

Warnings:

1. **Natural-minor note spelling is pitch-correct but not key-spelled.**
   - Example: natural-minor rows may expose `A#` where learner-facing theory would usually prefer `Bb`, and `D#` where `Eb` would be clearer in G natural minor / flat-key rows.
   - This is not a pitch-validation failure because pitch classes are correct.
   - Before polished UI, Lane 05 or Lane 06 should decide whether UI displays canonical pitch names as-is or receives/display-normalizes key-aware note spellings.

2. **Explorer slice is not committed at tested HEAD.**
   - QA validated untracked working-tree files. Repo Steward should exact-path stage/commit the Lane 05 slice before any downstream UI work assumes it is in HEAD.

## Fixes applied

None.

## Tests and checks run

Run from `/Users/cory/Documents/Pocket Steel`:

- `git status --short`
  - Broad unrelated dirty/untracked worktree remains parked.
- `git branch --show-current`
  - `feature/answer-api`
- `git rev-parse --short HEAD`
  - `891bf1e`
- `.venv/bin/python -m py_compile pocketsteel/fretboard_explorer.py`
  - Passed.
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
  - Passed: `9 passed`.
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py -q`
  - Passed: `52 passed`.
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q`
  - Passed: `25 passed`.
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
  - Passed: `5 passed`.
- `.venv/bin/python -m pytest -q`
  - Passed: `784 passed`.
- `git diff --check`
  - Passed.
- Independent generated-row QA script
  - Passed hard-rule checks with `hard_rule_failures []`.

## Risks

Risk level: low-to-medium.

Reasons:

- Backend row generation is deterministic, pitch-validated, and isolated.
- UI has not consumed the payload yet, so display expectations remain unproven.
- Natural-minor enharmonic spelling could confuse users if rendered directly.
- The slice is working-tree-only at the time of this QA handoff.

Rollback:

- If committed, revert the exact Explorer slice files:
  - `pocketsteel/fretboard_explorer.py`
  - `tests/test_fretboard_explorer.py`
  - `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-backend-slice.md`

## Human decision needed

No for backend QA approval.

Optional product/UI decision:

- Decide whether learner-facing Explorer notes should be key-aware spellings (`Bb`, `Eb`) instead of canonical sharp spellings (`A#`, `D#`) before or during UI work.

## Safe-to-stage exact file list

For this QA task only:

- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-qa.md`

For the Lane 05 backend slice, based on this QA:

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

Lane 01 Repo Steward for exact-path commit of the Lane 05 backend slice plus this QA handoff, if desired.

After commit, Lane 06 may begin UI work against the Explorer payload with the note-spelling warning called out.

Suggested Lane 01 prompt:

```text
Lane 01: Run ExactPathCommit for the E9 Fretboard Explorer backend slice and QA handoff. Stage only pocketsteel/fretboard_explorer.py, tests/test_fretboard_explorer.py, docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-backend-slice.md, and docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-qa.md. Run cached diff checks and commit if clean. Leave unrelated dirty files parked.
```

## Commit readiness

Safe to commit the scoped backend slice and QA handoff with exact-path staging.
