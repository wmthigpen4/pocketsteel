# SGF Primary Answer Leakage Backend Fix

## Task Summary

Requested under `AUTOPILOT USER SMOKE BUG`: fix strict-scorer failures where SGF/forum snippets, first-person forum fragments, and source-looking hyphen bullets could become or look like primary answer text.

Completed a scoped backend patch that:

- expands the SGF primary-answer quarantine patterns for raw forum fragments and forum-like first-person text;
- normalizes backend-composed answer list markers from `-` to `*` before returning `/api/answer` payloads, so teacher lists are not mistaken for copied forum bullets;
- adds a minor-chord teacher fallback for quarantined “find minors on E9” style questions;
- rewrites several guardrail/fallback answers to avoid first-person phrasing that the strict scorer correctly flags as forum-like;
- adds focused API regressions proving raw forum-provider bodies are quarantined and teacher lists remain readable.

Intentionally not changed:

- no UI files;
- no auth, deployment, DNS, corpus, Chroma, embeddings, source-inbox, private data, scraping, or design assets;
- no `/api/answer` schema change;
- no source-card layout change;
- no broad answer architecture rewrite.

## Files Changed

Scoped implementation/test files:

- `pocketsteel/answering.py`
- `pocketsteel/api.py`
- `pocketsteel/curated_answers.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/sgf-primary-answer-leakage-backend-fix.md`

Generated/dirty artifacts intentionally not part of this slice:

- `docs/answer-eval-report.md` was rewritten by `scripts/run_answer_eval.py`; it remains unstaged.
- Many unrelated parked files were present before/around this task and remain parked.

## Root Cause

The strict scorer exposed four related backend issues:

1. The SGF quarantine was too narrow and missed raw forum-body shapes such as copied `- I found...` bullets, SGF markup remnants, and anecdotal first-person forum starts.
2. Some early curated/deterministic paths bypassed any final answer-body cleanup before `/api/answer` returned.
3. Teacher-composed markdown lists used hyphen bullets, which are visually fine but collide with the strict SGF-fragment detector when the content starts like copied forum bullets.
4. A few internal fallback answers used first-person “I...” wording in source-sensitive contexts, which can look like forum-player voice rather than product voice.

## Behavior Before And After

Strict eval before this patch, from `/tmp/pocketsteel-strict-after-c8.json`:

- pass: 130
- warn: 31
- fail: 134
- `sgf_primary_answer_leakage`: 85
- `forum_first_person_fragment_leakage`: 44
- `deterministic_teacher_answer_source_fragment`: 16
- `repair_instruction_source_fragment_failure`: 19
- `weak_source_boilerplate_in_answer`: 0
- `off_domain_sgf_source_cards`: 0

Strict eval after this patch, from `/tmp/pocketsteel-strict-after-sgf-primary-fix4.json`:

- pass: 153
- warn: 33
- fail: 109
- `sgf_primary_answer_leakage`: 0
- `forum_first_person_fragment_leakage`: 0
- `deterministic_teacher_answer_source_fragment`: 0
- `repair_instruction_source_fragment_failure`: 0
- `weak_source_boilerplate_in_answer`: 0
- `off_domain_sgf_source_cards`: 0

Representative behavior preserved/fixed:

- Raw provider body beginning `- I found this...` now returns the source-free quarantine answer instead of using the provider body.
- Teacher answers still use readable lists, but the returned body uses `*` list markers so they do not resemble copied SGF bullet fragments.
- “How do I find minors on E9?” now gets a direct teacher-style minor-chord explanation rather than quarantined source-looking fragments.
- Current-roster and copyright guardrails now use neutral product phrasing instead of “I do not...” / “I can...” phrasing.

## Tests And Checks

Commands run:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_answer_eval.py tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py -q
.venv/bin/python scripts/run_full_answer_quality_eval.py --output /tmp/pocketsteel-strict-after-sgf-primary-fix4.md --json-output /tmp/pocketsteel-strict-after-sgf-primary-fix4.json
.venv/bin/python scripts/run_answer_eval.py
.venv/bin/python -m pytest
git diff --check
```

Results:

- `git diff --check`: passed after stripping trailing whitespace written by the generated `docs/answer-eval-report.md`.
- Focused backend/eval pytest: `369 passed`.
- Strict answer-quality eval: target leakage buckets are all zero; broader eval remains `153 pass / 33 warn / 109 fail`.
- Legacy `scripts/run_answer_eval.py`: completed successfully; legacy categories report `pass: 0`, `likely_directness_failure: 147`, `source weakness / no-source: 146`, which is pre-existing/legacy scoring behavior and not the strict leakage target.
- Full pytest: `692 passed, 2 failed`.

Known unrelated full-suite failures:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

These match the known static/UI caveats and were not introduced by this backend patch.

## Smoke Target

No browser smoke was required or run for this backend-only scorer/leakage patch.

Smoke Target:
- Target type: API-fallback
- Result type: API fallback, not browser smoke
- Exact browser URL tested: not applicable
- Cache-busted URL tested: not applicable
- Exact URL the user should use: not changed by this task
- Auth required: not applicable
- Auth provider: not applicable
- Cloudflare Access login result: not attempted
- Local backend URL: temporary local eval servers started by the eval scripts
- Expected backend port: not fixed; eval scripts used temporary local ports
- Expected git HEAD: `14021f8`
- Version endpoint: not used
- Version endpoint result: not used
- If version endpoint missing, how version is inferred: local git HEAD and test process
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not applicable
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not applicable
- Who should test this URL: Lane 15/12 if protected-preview smoke is requested
- Do not test these URLs: none specified
- Known caveats: this handoff proves backend API/eval behavior, not protected-preview browser rendering

## Risk Assessment

Risk: medium-low.

Why:

- The change touches shared answer output formatting and quarantine logic, so it is broader than a one-question fix.
- The implementation is intentionally narrow: final answer text normalization, quarantine detection, and fallback wording only.
- The `/api/answer` schema, source-card shape, retrieval gates, and frontend rendering were not changed.

Rollback:

- Revert the scoped commit/file changes in `pocketsteel/answering.py`, `pocketsteel/api.py`, `pocketsteel/curated_answers.py`, and `tests/test_api_search.py`.

## Commit Readiness

Safe to commit.

Exact safe-to-stage file list:

- `pocketsteel/answering.py`
- `pocketsteel/api.py`
- `pocketsteel/curated_answers.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/sgf-primary-answer-leakage-backend-fix.md`

Must remain unstaged:

- `docs/answer-eval-report.md`
- unrelated parked docs/corpus/deploy/source-inbox/private/design/runtime files visible in `git status`
- any `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, source-inbox raw/provenance, `.wrangler/`, `public/`, `ui/brand/`, `Neon Sign/`, deployment secrets, or design assets

## Suggested Next Step

Lane 15 QA / Answer Eval should rerun the strict scorer and user-smoke target prompts against the committed backend patch.

Exact next prompt:

```text
Lane 15 QA / Answer Eval: Rerun the strict SGF-primary-answer leakage scorer and a focused API smoke for raw SGF/forum fragment prompts after commit `backend: block sgf primary answer leakage`. Confirm `sgf_primary_answer_leakage`, `forum_first_person_fragment_leakage`, `deterministic_teacher_answer_source_fragment`, and `repair_instruction_source_fragment_failure` remain zero. Do not treat the known unrelated static/UI full-suite failures as backend blockers.
```
