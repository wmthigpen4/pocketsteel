# QA Direct Answer First User Smoke Fix

## Task Summary

Lane 15 QA reviewed the Lane 05 direct-answer-first backend patch for predictable practical/theory prompts that should not fall through to raw SGF/forum fragments.

Completed:

- Reviewed the requested guidance, integration status, Lane 05 handoff, answer-contract docs, teacher-first policy, changed backend files, and answer/API tests.
- Verified the current worktree behavior for the cereal-box feasibility prompt, rooted dominant-7 prompts, sus usage/rooted sus prompts, and requested regression prompts.
- Ran focused direct-answer tests, required answer/API/eval suites, `git diff --check`, and full pytest to classify the two reported failures.

Intentionally not changed:

- No implementation files were modified by this QA task.
- No staging or commit was performed.
- No deployment, protected-preview restart, Chroma, corpus, embeddings, scraping, auth, DNS, or UI work was performed.

## Pass/Fail Decision

**Pass for the direct-answer-first backend slice.**

QA approves exact-hunk commit of the direct-answer-first backend/test changes. The patch behaves as intended in the in-process `/api/answer` test path and the focused/broad backend-eval suites pass.

Full pytest still has 2 failures, but they match the Lane 05 report and are unrelated static/UI blockers:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

Classification: **unrelated parked blocker / separate Lane 06 or static asset task**. These failures should not block exact-hunk commit of the backend direct-answer-first slice, but they do remain relevant before a clean full-suite release/restart gate.

## Prompt Results

Prompt verification type: **in-process API fallback, not browser smoke**. This verifies current worktree answer behavior, not protected-preview deployment behavior.

| Prompt | Result | Notes |
| --- | --- | --- |
| `Can I make a pedal steel guitar out of a box of cereal?` | Pass | Starts `No, not as a real functional pedal steel guitar.` Explains rigid body, changer, strings under tension, pedals, rods, levers, tuning stability. No sources, warnings, fretboard, or SGF fragment leakage. |
| `How do I play a G dom 7?` | Pass | Explains `G7 = G-B-D-F`, root/major 3rd/perfect 5th/flat 7th, and does not attach sources or unsupported fretboard. |
| `How do I play a G7?` | Pass | Same clean deterministic dominant-7 answer. No sources, warnings, or raw SGF. |
| `What is a G dominant 7?` | Pass | Same clean deterministic dominant-7 answer. No sources, warnings, or raw SGF. |
| `When would I ever play a sus chord?` | Pass | Directly explains tension/resolution, sus4 replacing the 3rd, held chords, endings, gospel/country phrase use. No sources or fretboard. |
| `When do I use a sus chord?` | Pass | Same clean musical-use answer. No sources or fretboard. |
| `How do I play a G sus chord?` | Pass | Clean rooted sus answer: `Gsus usually means Gsus4`, `G-C-D`, no B/3rd, exact E9 sus mapping limited. No awkward internal wording, sources, or fretboard. |
| `What is a G chord?` | Pass | Direct deterministic chord definition: `G-B-D`, root/major 3rd/perfect 5th. No sources or fretboard. |
| `How do I play a G chord on the E9?` | Pass | Deterministic E9 chord-position answer with fretboard payload. No warnings or raw SGF fragment. |
| `Tell me something about pedal steel I might not already know` | Pass | Direct teacher-first E9 position-family practice answer. No sources, warnings, or raw SGF fragment. |
| `Can I play steel guitar in my kitchen?` | Pass | Direct practical yes answer with safe practice drill. No sources, warnings, or raw SGF fragment. |
| `What is the capital of France?` | Pass | Off-domain guardrail. No sources, warnings, or fretboard. |

## Tests And Checks

Commands run:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_api_search.py -k "direct_yes_no_practical or rooted_dominant_seventh or suspended_usage or rooted_suspended"
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
.venv/bin/python -m pytest
git diff --check
```

Results:

- `git diff --check`: passed.
- Focused direct-answer tests: `4 passed, 210 deselected`.
- `tests/test_answer_intent_classifier.py`: `66 passed`.
- `tests/test_answer_eval.py`: `9 passed`.
- Required answer/API/eval suite: `259 passed`.
- Full pytest: `645 passed, 2 failed`.

Full-suite failure classification:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`: unrelated static landing source/deploy mismatch. Separate Lane 06/static task.
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`: unrelated missing public fretboard background route/static asset. Separate Lane 06/static task.

## Files Changed

Changed by Lane 05 direct-answer-first patch, approved for exact-hunk commit:

- `pocketsteel/answer_contracts.py`
  - Approve only the added contract entries for `direct_yes_no_practical`, `chord_quality_theory`, `unsupported_exact_mapping`, `forum_context_secondary`, and `when_to_use_musical_context`.
- `pocketsteel/basic_chord_answers.py`
  - Approve only dominant-7 normalization/parsing, `dominant_seventh_spelling_for_answer`, updated dominant-7 direct answer, rooted sus wording cleanup, and `sus_chord_usage_answer_for_question`.
- `pocketsteel/curated_answers.py`
  - Approve only the `sus_chord_usage_answer_for_question` import, early routing for direct practical/sus usage answers, and `direct_yes_no_practical_answer`.
- `tests/test_api_search.py`
  - Approve only the four direct-answer-first regression tests:
    - `test_direct_yes_no_practical_answers_start_directly_without_sgf_fragments`
    - `test_rooted_dominant_seventh_answers_are_direct_and_source_free`
    - `test_suspended_usage_answers_directly_without_fretboard_or_sources`
    - `test_rooted_suspended_answers_are_clean_direct_theory`

Handoff artifacts approved to include with the slice if Repo Steward policy includes task handoffs:

- `docs/handoffs/task-completions/direct-answer-first-user-smoke-fix.md`
- `docs/handoffs/task-completions/qa-direct-answer-first-user-smoke-fix.md`

Files/hunks that must remain parked:

- All corpus/source/legal/provenance/source-inbox changes.
- All root RAG script changes.
- `README.md`, broad docs, and integration-status refreshes not part of this direct-answer slice.
- `deploy/landing/index.html`, `public/`, `ui/brand/`, `Neon Sign/`, static assets, generated reports, private/corpus/vector data, and any unrelated untracked handoffs/assets.

## Integration Notes

- The protected preview remains on a committed/stale runtime until Repo Steward commits this exact backend slice and Lane 12 restarts/verifies it.
- Lane 05 handoff reported protected-preview browser smoke against `/api/version` result `28ae8f4`, which did not include this patch. The live protected preview failure for the cereal-box prompt should be treated as stale-runtime evidence, not a backend patch failure.
- The direct-answer patch does not touch UI files, auth policy, deployment config, Chroma, embeddings, scraping, corpus, or private source data.
- Retrieval gating remains intact in focused tests and prompt checks.

## Risk Assessment

Risk: **low for exact-hunk backend commit**.

Why:

- The changes are narrow deterministic/curated answer routes plus contract/test coverage.
- No retrieval, Chroma, corpus, deployment, auth, or UI code was touched by the approved backend slice.
- Focused and required answer/API/eval suites pass.

Rollback notes:

- Revert the approved hunks in the four implementation/test files if a regression appears.
- Do not revert unrelated parked files as part of this slice.

## Commit Readiness

**Safe to commit** for exact-hunk staging of the approved backend/test slice.

Protected-preview restart remains blocked until:

1. Repo Steward commits the approved exact hunks.
2. Lane 12 restarts/verifies the protected preview against the new commit.

The two full-suite static/UI failures require separate Lane 06/static work or a separate Repo Steward/static cleanup before the repo can claim a fully clean test suite.

## Suggested Next Step

Recommended lane: **01 Repo Steward**.

Exact next prompt:

```text
Repo Steward: QA approved the direct-answer-first backend slice in docs/handoffs/task-completions/qa-direct-answer-first-user-smoke-fix.md. Proceed under auto-approval. Stage only the approved exact hunks in pocketsteel/answer_contracts.py, pocketsteel/basic_chord_answers.py, pocketsteel/curated_answers.py, tests/test_api_search.py, plus the direct-answer-first and QA handoff files if handoff policy requires them. Keep all unrelated parked corpus/source/static/UI/root-script/docs files unstaged. Run git diff --check and the focused/required backend tests named in the QA handoff, then commit with a scoped message. If exact-hunk staging cannot isolate the approved slice, write a blocker handoff instead of committing.
```

If Repo Steward blocks because of static/UI full-suite failures, recommended Lane 06/static prompt:

```text
Lane 06/static: Fix the two unrelated full-suite blockers reported in docs/handoffs/task-completions/qa-direct-answer-first-user-smoke-fix.md: landing source vs deploy static HTML mismatch and missing public fretboard background route in same-origin smoke server. Do not touch backend answer behavior, Chroma, corpus, embeddings, scraping, auth, DNS, or deployment secrets. Add or update focused static tests, run the failing tests and full pytest if practical, and write a handoff.
```
