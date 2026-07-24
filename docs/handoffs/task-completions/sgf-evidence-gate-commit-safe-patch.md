# SGF Evidence Gate Commit-Safe Patch

## Task Summary

Requested: produce a commit-safe backend patch for the QA-approved “SGF Evidence Is Not Primary Answer Text” slice.

Completed:

- Inspected the current dirty diff and the prior Lane 05 / QA / integration handoffs.
- Identified the exact helper-scope blocker that prevented Repo Steward from committing the approved SGF evidence gate.
- Resolved the helper-scope issue by moving the SGF-approved basic chord/theory and chord-change helpers into a small standalone helper module.
- Repointed `steel_guitar_rag/answering.py` and `steel_guitar_rag/curated_answers.py` to that standalone helper, so the SGF gate no longer depends on dirty `steel_guitar_rag/fretboard_examples.py` helper additions.
- Preserved the QA-approved answer behavior for source-fragment rejection, basic chord/theory fallback, chord-quality fallback, chord-change fallback, private/placeholder identity guardrail, `/api/version`, and eval coverage.

Intentionally not changed:

- No UI files.
- No auth, deployment, DNS, Cloudflare Access policy, corpus, Chroma/vector store, embeddings, scraping, source-inbox, private source data, or design assets.
- No `/api/answer` public schema change.
- No commit.

## Branch And HEAD

- Branch: `feature/answer-api`
- HEAD: `e353848 docs: auto-approve scoped repo steward commits`

## Root Cause Of Commit Blocker

Repo Steward previously stopped because the QA-approved SGF hunks in:

- `steel_guitar_rag/answering.py`
- `steel_guitar_rag/curated_answers.py`

imported and called:

- `basic_chord_theory_answer_for_question`
- `chord_change_answer_for_question`

Those helper definitions existed only inside dirty `steel_guitar_rag/fretboard_examples.py`. But `steel_guitar_rag/fretboard_examples.py` and `tests/test_fretboard_examples.py` also contain broader parked fretboard-engine work and were explicitly marked as not safe for the SGF evidence commit.

That made the approved scope contradictory:

- Stage SGF answer files without `fretboard_examples.py`: broken imports.
- Stage `fretboard_examples.py`: pulls unrelated parked fretboard work into the SGF commit.

## Helper-Scope Resolution

Added:

- `steel_guitar_rag/basic_chord_answers.py`

This module contains only the minimal deterministic helpers required by the SGF evidence gate:

- `basic_chord_theory_answer_for_question`
- `chord_change_answer_for_question`
- small internal spelling/parsing helpers for basic chord names and chord changes

Then repointed:

- `steel_guitar_rag/answering.py`
- `steel_guitar_rag/curated_answers.py`

to import those two helpers from `steel_guitar_rag.basic_chord_answers`.

The parked `steel_guitar_rag/fretboard_examples.py` diff still exists in the working tree, but the SGF commit-safe patch no longer depends on staging it.

## Files Changed

Commit-safe SGF slice files:

- `steel_guitar_rag/basic_chord_answers.py` (new)
- `steel_guitar_rag/answer_contracts.py`
- `steel_guitar_rag/answering.py`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/curated_answers.py`
- `scripts/run_answer_eval.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/sgf-evidence-not-primary-answer-text-implementation.md`
- `docs/handoffs/task-completions/qa-sgf-evidence-not-primary-answer-text.md`
- `docs/handoffs/task-completions/sgf-evidence-gate-commit-safe-patch.md`

Still dirty but parked / not part of the commit-safe SGF slice:

- `steel_guitar_rag/fretboard_examples.py`
- `tests/test_fretboard_examples.py`
- `ui/steel-guitar-rag-mock.html`
- `deploy/landing/index.html`
- `public/`
- `ui/brand/`
- `Neon Sign/`
- corpus metadata/source policy/source-inbox/provenance files
- root RAG/corpus scripts
- broad historical docs/handoffs and generated/private artifacts

## Exact Behavior Preserved

Verified behavior remains:

- `What is a G chord?` returns a teacher-first `G-B-D` style answer, not SGF snippets.
- `What is a sus chord?` explains suspended chords, not SGF snippets.
- `What is a chord change?` explains chord movement/progression, not SGF snippets.
- `How do I play a Fmaj7?` explains `F-A-C-E` and a deterministic E9 mapping caveat, not SGF snippets.
- `How do I play an F major 7th?` behaves like `Fmaj7`.
- `How do I play a B-sus chord/` normalizes to `Bsus4`, explains `B-E-F#`, and avoids SGF fragments.
- `Who is <PRIVATE_PERSON_PLACEHOLDER>?` returns a source-free private/unknown identity guardrail.
- Forum-wisdom questions may keep SGF source cards, but the main answer is synthesized.
- E9 position questions still use deterministic/copedent/fretboard behavior.
- Off-domain retrieval gating still works.

Compatibility detail:

- The standalone helper includes both compact and written-out chord labels where tests require them, for example `Fmaj7 is F-A-C-E` and `F major 7`.
- Suspended-chord answers include both fuller interval language and compact formula labels such as `sus4 = root, 4th, 5th`.

## Tests And Checks

Commands run:

```bash
git status --short
git diff --name-only
git diff --stat
git diff --check
.venv/bin/python -m py_compile steel_guitar_rag/basic_chord_answers.py steel_guitar_rag/answering.py steel_guitar_rag/curated_answers.py
.venv/bin/python -m pytest tests/test_api_search.py -k "unknown_person_identity or primary_answer_gate or rootless_chord_quality or major_seventh or chord_change or suspended_chord or basic_chord_definition or smoke_ready_chord_fretboard"
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_answer_eval.py tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
.venv/bin/python scripts/run_answer_eval.py --help
.venv/bin/python -m pytest
git diff --check
```

Results:

- `git diff --check`: passed.
- `py_compile`: passed.
- Focused SGF/API selection: `8 passed, 200 deselected`.
- Combined backend/eval gate: `327 passed`.
- `scripts/run_answer_eval.py --help`: passed.
- Full pytest: `639 passed, 2 failed`.

Full pytest failures are unchanged unrelated static/UI blockers:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

I did not run the live `scripts/run_answer_eval.py` evaluator against an HTTP server because it requires a live `/api/answer` server and writes report artifacts by default. The commit-safety signal for this backend slice is the focused pytest/eval suite above.

## QA Re-Review

Recommended: Lane 15 quick re-check is prudent because code changed materially from the QA-approved dirty implementation by moving helper scope into a new module.

Expected QA scope:

- Confirm the same SGF-focused prompts still pass.
- Confirm `steel_guitar_rag/fretboard_examples.py` is no longer required for the SGF commit.
- Confirm full pytest still has only the two unrelated static/UI failures.

## Exact Files / Hunks Repo Steward Can Stage If Approved

Repo Steward can stage exact SGF hunks in:

- `steel_guitar_rag/basic_chord_answers.py`
- `steel_guitar_rag/answer_contracts.py`
- `steel_guitar_rag/answering.py`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/curated_answers.py`
- `scripts/run_answer_eval.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/sgf-evidence-not-primary-answer-text-implementation.md`
- `docs/handoffs/task-completions/qa-sgf-evidence-not-primary-answer-text.md`
- `docs/handoffs/task-completions/sgf-evidence-gate-commit-safe-patch.md`

Important hunk guidance:

- In `steel_guitar_rag/answering.py`, stage the import from `steel_guitar_rag.basic_chord_answers`, the rootless/generic fretboard import already present in clean HEAD scope, SGF chatter filtering, and deterministic fallback loop.
- In `steel_guitar_rag/curated_answers.py`, stage the import from `steel_guitar_rag.basic_chord_answers`, calls to `basic_chord_theory_answer_for_question` and `chord_change_answer_for_question`, and the private/placeholder identity guardrail.
- Do not stage the unrelated dirty `steel_guitar_rag/fretboard_examples.py` helper additions. They are no longer required by the SGF patch.
- Do not stage `tests/test_fretboard_examples.py`; the matching SGF behavior is covered in `tests/test_api_search.py`.

## Files / Hunks That Must Remain Parked

Do not stage unless a separate lane approves them:

- `steel_guitar_rag/fretboard_examples.py`
- `tests/test_fretboard_examples.py`
- `ui/steel-guitar-rag-mock.html`
- `deploy/landing/index.html`
- `public/`
- `ui/brand/`
- `Neon Sign/`
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, DBs, logs, generated reports
- raw `source-inbox` content and provenance files
- source-inbox inventory/report outputs
- corpus metadata/source policy registry changes
- root RAG/corpus build scripts
- deployment secrets, `.wrangler/`, DNS config, private env files
- broad docs/provenance/deploy changes unrelated to the SGF evidence gate

## Protected Preview Restart

Protected-preview restart remains blocked.

Reason:

- The SGF backend slice is now commit-safe after QA re-check/Repo Steward exact-hunk staging, but the worktree still has unrelated dirty runtime/user-facing files.
- Full pytest still has two unrelated static/UI failures.
- The protected preview should not certify a dirty working tree.

## Risk Assessment

Risk: low-to-medium.

Why:

- The helper-scope change is narrow and moves SGF-specific deterministic theory helpers into a standalone module.
- Focused backend/eval tests are green.
- The main risk is commit-scope contamination from the large dirty worktree, not the backend behavior.

Rollback notes:

- If needed, revert the exact SGF commit containing `steel_guitar_rag/basic_chord_answers.py` and the import/call-site changes.
- Do not use destructive cleanup commands against the dirty worktree.

## Commit Readiness

Needs human review first.

Reason:

- Behavior is preserved and the helper-scope blocker is resolved.
- Because the code changed materially from the prior QA-approved dirty implementation by introducing `steel_guitar_rag/basic_chord_answers.py`, Lane 15 should do a quick re-check before Repo Steward commits.

## Exact Next Prompt

Lane 15 QA re-check:

```text
Lane 15 QA / Answer Eval

Re-check the commit-safe SGF Evidence Is Not Primary Answer Text patch.

Read:
- docs/handoffs/task-completions/sgf-evidence-gate-commit-safe-patch.md
- docs/handoffs/task-completions/qa-sgf-evidence-not-primary-answer-text.md
- git diff -- steel_guitar_rag/basic_chord_answers.py steel_guitar_rag/answer_contracts.py steel_guitar_rag/answering.py steel_guitar_rag/api.py steel_guitar_rag/curated_answers.py scripts/run_answer_eval.py tests/test_api_search.py

Verify:
- The SGF evidence gate behavior is unchanged.
- The new `steel_guitar_rag/basic_chord_answers.py` resolves the helper-scope blocker.
- `steel_guitar_rag/fretboard_examples.py` and `tests/test_fretboard_examples.py` are no longer required for this SGF commit.
- Focused SGF/API/eval tests pass.
- Full pytest still has only the unrelated static/UI failures, if rerun.

If approved, write a handoff that explicitly authorizes Repo Steward exact-hunk staging of only the files listed in the commit-safe handoff.
```

If QA approves, Lane 01 Repo Steward prompt:

```text
Lane 01 Repo Steward

QA approved the commit-safe SGF Evidence Is Not Primary Answer Text patch. Proceed under Repo Steward auto-approval with exact-hunk staging only.

Stage only:
- steel_guitar_rag/basic_chord_answers.py
- approved SGF hunks in steel_guitar_rag/answer_contracts.py
- approved SGF hunks in steel_guitar_rag/answering.py
- approved /api/version hunks in steel_guitar_rag/api.py
- approved SGF/private-identity hunks in steel_guitar_rag/curated_answers.py
- approved eval-pattern hunks in scripts/run_answer_eval.py
- approved tests in tests/test_api_search.py
- docs/handoffs/task-completions/sgf-evidence-not-primary-answer-text-implementation.md
- docs/handoffs/task-completions/qa-sgf-evidence-not-primary-answer-text.md
- docs/handoffs/task-completions/sgf-evidence-gate-commit-safe-patch.md

Do not stage steel_guitar_rag/fretboard_examples.py, tests/test_fretboard_examples.py, UI/static/corpus/source-inbox/deploy/design/private/generated files, or unrelated docs.

Run staged diff checks and focused backend/eval tests before committing. Stop with a blocker handoff if any unrelated hunk cannot be isolated.
```
