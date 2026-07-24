# 2026-06-22 13:45 05 E9 Explorer Key-Aware Display Spelling

## Task Summary

Requested a Lane 05 / Lane 06 fix for E9 Fretboard Explorer learner-facing note spelling.

Completed:

- Added display-only note spelling fields to the deterministic E9 Fretboard Explorer payload.
- Preserved canonical pitch-class validation and canonical `notes` values.
- Preserved deterministic row IDs, generation rules, row counts, controls, and validation behavior.
- Added key-aware display spelling for G natural minor so learner-facing Explorer output uses `G A Bb C D Eb F`.
- Added display summaries and display top-voice notes for UI consumption.
- Added tests proving G natural-minor display output uses `Bb` and `Eb` while canonical/internal pitch identity can remain `A#` / `D#`.
- Added tests proving E9 tuning/mechanical labels still use sharp-oriented E9 spellings such as `F#`, `D#`, `G#`, and `Eb/D#`.

Intentionally not changed:

- No `/api/answer` routing.
- No RAG, SGF/forum retrieval, corpus, Chroma, embeddings, scraper, deployment, auth, DNS, private source data, assets, or unrelated UI work.
- No global conversion of E9 notation to flats.

## Files Changed

Files in this scoped commit set:

- `steel_guitar_rag/fretboard_explorer.py`
- `tests/test_fretboard_explorer.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-backend-slice.md`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-qa.md`
- `docs/handoffs/task-completions/2026-06-22-1345-05-e9-explorer-key-aware-display-spelling.md`

Notes:

- The Explorer module and focused test file were untracked when this task began.
- The QA handoff explicitly stated the Explorer backend slice had passed QA but remained working-tree-only.
- This handoff includes the key-aware display-spelling fix on top of that approved untracked Explorer slice.

## Implementation Notes

The implementation separates internal pitch identity from learner-facing display spelling:

- `notes`: canonical pitch names from the existing pitch helpers; unchanged for validation.
- `intervals`: existing interval validation labels; unchanged.
- `display_notes`: learner-facing, key-aware note spelling for UI.
- `display_top_voice`: top voice with display spelling.
- `display_summary`: compact learner-facing row summary with display note names.
- `query.display_scale_notes`: scale spelling for UI filters/headings.

For G natural minor:

- Scale display output is `G A Bb C D Eb F`.
- `Bb` major rows may keep canonical `A#` internally but expose `Bb` in `display_notes`.
- `Eb` major and diminished-context rows may keep canonical `D#` internally but expose `Eb` in `display_notes`.

Mechanical E9 labels remain unchanged:

- Open strings still expose `F#`, `D#`, and `G#`.
- E-lower mechanical change still exposes `Eb/D#`.

## Tests And Checks

Run from repo root:

- `git status --short`
  - Broad unrelated dirty/untracked worktree remains parked.
- `.venv/bin/python -m py_compile steel_guitar_rag/fretboard_explorer.py`
  - Passed.
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
  - Passed: `11 passed`.
- `.venv/bin/python -m pytest -q`
  - Passed: `786 passed`.
- `git diff --check`
  - Passed.
- `git diff --no-index --check -- /dev/null steel_guitar_rag/fretboard_explorer.py`
  - No whitespace errors; exit code `1` is expected for `/dev/null` comparison.
- `git diff --no-index --check -- /dev/null tests/test_fretboard_explorer.py`
  - No whitespace errors; exit code `1` is expected for `/dev/null` comparison.

## Integration Notes

- Branch: `feature/answer-api`
- Starting HEAD: `891bf1e`
- This is an isolated deterministic Explorer payload/display-model change.
- UI should consume `display_notes`, `display_top_voice`, `display_summary`, and `query.display_scale_notes` for learner-facing note spelling instead of rendering canonical `notes` directly.
- Canonical `notes` remains available for validation/debugging and should not be treated as learner-facing copy where enharmonic spelling matters.

## Risk Assessment

Risk: low-to-medium.

Reasons:

- The change is isolated to the uncommitted Explorer module and focused tests.
- Full pytest is green.
- Existing row IDs and canonical validation are preserved.
- The main risk is downstream UI accidentally continuing to display canonical `notes` instead of the new display fields.

Rollback:

- Revert the scoped Explorer commit if needed.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `steel_guitar_rag/fretboard_explorer.py`
- `tests/test_fretboard_explorer.py`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-backend-slice.md`
- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-qa.md`
- `docs/handoffs/task-completions/2026-06-22-1345-05-e9-explorer-key-aware-display-spelling.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked worktree files.
- Corpus/private corpus files.
- Chroma/vector stores.
- Embeddings.
- Scraper output.
- Deployment/auth/DNS files.
- Source-inbox/private source data.
- Assets/design files.
- Unrelated UI files.

## Recommended Next Lane

Lane 06 UX/UI Design for polished Explorer UI consumption of `display_notes` rather than canonical `notes`.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Commit exact paths only with a message such as:

`fix: add key-aware explorer display spelling`
