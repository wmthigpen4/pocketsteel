# Task Summary

- What was requested: define the MVP `response.fretboard` payload contract so the Steel Guitar RAG backend/answer layer and UI can stop guessing about fretboard diagrams.
- What was completed: created a product/architecture contract document for `response.fretboard`, including top-level fields, position object fields, required vs optional behavior, validation rules, canonical pedal/lever labels, legacy mapping, JSON schema proposal, sample payloads, non-goals, and implementation sequence.
- What was intentionally not changed: no backend generation, no API type edits, no UI rendering changes, no visual design changes, no SGF scraping, no manifest or corpus data changes, no embeddings/Chroma/vector DB work, no deployment changes, and no auth/security changes.

# Files Changed

- Changed files:
  - None
- Created files:
  - `docs/fretboard-payload-contract.md`
  - `docs/handoffs/task-completions/2026-06-11-1615-18-fretboard-payload-contract.md`
- Deleted files:
  - None
- Generated artifacts:
  - None

# Tests And Checks

- `rg -n "response\\.fretboard|fretboard|positions|pedal-steel-fretboard|VirtualFretboard|Fretboard" . -g '!data/**' -g '!sgf-output/**' -g '!*.sqlite' -g '!node_modules/**'`
  - Passed for inspection. Found existing conventions in `steel_guitar_rag/fretboard_examples.py`, `steel_guitar_rag/api_contract.py`, `ui/answer-client.js`, `tests/test_fretboard_examples.py`, and `tests/test_frontend_answer_ui.py`.
- `find docs -maxdepth 3 -type d | sort`
  - Passed for inspection. Confirmed `docs/handoffs/task-completions/` exists and `docs/architecture/` does not exist because `docs/architecture.md` is a file.
- `git status --short`
  - Passed for inspection. Confirmed the worktree already contained many unrelated dirty and untracked files; this task only added the two docs listed above.
- `sed -n '1,220p' steel_guitar_rag/fretboard_examples.py`
  - Passed for inspection.
- `sed -n '220,380p' steel_guitar_rag/fretboard_examples.py`
  - Passed for inspection.
- `sed -n '1,130p' steel_guitar_rag/api_contract.py`
  - Passed for inspection.
- `sed -n '250,360p' ui/answer-client.js`
  - Passed for inspection.
- `sed -n '240,310p' tests/test_frontend_answer_ui.py && sed -n '740,850p' tests/test_frontend_answer_ui.py`
  - Passed for inspection.
- `sed -n '1,190p' tests/test_fretboard_examples.py`
  - Passed for inspection.
- `rg -n "E-raise/F|E-lower|6-lower|2/9-lower|vertical/Bb|A\\+F|A\\+B|G\\+|G-|D--|D-|copedent" docs steel_guitar_rag tests ui -g '!data/**'`
  - Passed for inspection.
- `sed -n '1,120p' docs/api-contract.md`
  - Passed for inspection.
- `git diff --check -- docs/fretboard-payload-contract.md`
  - Passed.
- `git diff --check -- docs/fretboard-payload-contract.md docs/handoffs/task-completions/2026-06-11-1615-18-fretboard-payload-contract.md`
  - Passed.
- `git status --short -- docs/fretboard-payload-contract.md docs/handoffs/task-completions/2026-06-11-1615-18-fretboard-payload-contract.md`
  - Passed. Both task files are untracked and not committed.
- Tests skipped:
  - No unit or browser tests were run because this was a docs-only contract definition and did not modify executable code.

# Integration Notes

- Contract doc path: `docs/fretboard-payload-contract.md`.
- Required top-level MVP fields: `type`, `title`, `tuning`, `strings`, and `positions`.
- Optional top-level fields: `subtitle`, `copedent`, `key`, `legend`, `notes`, `warnings`, and `sourceContext`.
- Required position fields: `id`, `label`, `fret`, `strings`, `grip`, `pedals`, `levers`, and `color`.
- Optional position fields: `role`, `notes`, `intervals`, `bar`, `warnings`, `explanation`, and `sourceContext`.
- Sample payloads included:
  - G major positions: fret 3 no pedals, fret 6 A+F, fret 10 A+B.
  - C major positions: repo-pattern example using fret 8 no pedals, fret 11 A+F, fret 3 A+B.
  - Single-position answer: G major A+B at fret 10 on strings 4-5-6.
- Canonical MVP pedal names: `A`, `B`, `C`.
- Canonical MVP lever names: `F`, `E`, `G+`, `G-`, `D-`, `D--`, `V`.
- Existing repo seed labels differ from the new canonical contract. The doc recommends this mapping:
  - `E-raise/F` -> `F`
  - `E-lower` -> `E`
  - `6-lower` -> `G-`
  - `2/9-lower` -> `D-`
  - `vertical/Bb` -> `V`
- Schema/API/component/data contract changes:
  - Documentation only. No code contract has been changed yet.
  - Proposed migration is `highlights` -> `positions`, with a temporary compatibility period if needed.
- Assumptions:
  - `docs/fretboard-payload-contract.md` is the right location because `docs/architecture.md` already exists as a file, so `docs/architecture/fretboard-payload-contract.md` cannot be created without a docs restructure.
  - The UI remains the owner of fret math, string geometry, marker placement, colors, and SVG coordinates.
  - Backend payloads own musical intent only.
- Blockers:
  - None for the docs contract.
- Human decisions needed:
  - Decide whether `description` remains a legacy alias for `subtitle`.
  - Decide whether implementation should emit both `positions` and legacy `highlights` during migration.
  - Decide whether C major sample positions are ready for QA gold fixtures or should get a musician review first.
  - Decide whether canonical lever names should be displayed directly or translated by the UI into longer teaching labels.

# Risk Assessment

- Risk: Low
- Why: docs-only architecture work. It does not affect rendering, backend response generation, RAG behavior, corpus data, scraping, embeddings, auth, deployment, or live endpoints.
- Rollback notes: remove `docs/fretboard-payload-contract.md` and this handoff file.

# Commit Readiness

Needs human review first

# Suggested Next Step

- Lane: 05 Backend / RAG Integration
- Recommended prompt: "Implement the MVP `response.fretboard` contract from `docs/fretboard-payload-contract.md` for deterministic known E9 cases only. Do not touch scraping, corpus data, Chroma, embeddings, deployment, auth, or UI rendering. Add fixture-based tests for G major positions and preserve a compatibility path for the current UI if needed."
