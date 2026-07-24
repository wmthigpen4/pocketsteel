# Steel Guitar 101 Foundation Router Fix

## Task Summary

Requested: add a Steel Guitar 101 / foundation concept answer layer so obvious beginner steel-guitar questions receive direct teacher-first answers instead of falling into the generic fallback or source-fragment path.

Completed:
- Added deterministic source-free foundation answers for steel guitar, pedal steel, lap steel, console steel, E9, C6, universal tuning, extended E9, copedent, changer, pedals/levers, volume pedal, steel bar, picks, grips, pockets, slants, A/B/C pedals, E-lower, F lever, splits, raise/lower, cabinet drop, scale, chord, and tuning.
- Added deterministic comparison answers for lap steel vs pedal steel, E9 vs C6, dobro vs steel guitar, and pedal steel vs regular guitar.
- Preserved existing visual/chord resolvers and off-domain guardrails.
- Added focused API tests proving foundation answers are teacher-first, source-free, warning-free, and do not attach fretboard payloads.

Intentionally not changed:
- No UI files.
- No `/api/answer` schema changes.
- No auth, deployment, DNS, corpus, Chroma/vector stores, embeddings, scraping, source-inbox, private data, or visual assets.
- No broad rename from Steel Guitar RAG to Steel Guitar RAG.

## Files Changed

- `steel_guitar_rag/curated_answers.py`
  - Added `FOUNDATION_CONCEPT_ANSWERS`.
  - Added `FOUNDATION_COMPARISON_ANSWERS`.
  - Added foundation concept normalization and question matching.
  - Wired foundation answers into `sgf_quarantine_teacher_answer` before the broad fallback.
- `tests/test_api_search.py`
  - Added foundation concept source-free answer tests.
  - Added foundation comparison source-free answer tests.
  - Added regression coverage for Cmaj7, A minor/B-flat, string/fret/pedal diagnostics, noisy pedal rods, and JavaScript off-domain guardrail.

Generated artifacts:
- `corpus-private/reports/full-answer-quality-eval.md`
- `corpus-private/reports/full-answer-quality-eval.json`

Those generated private reports must remain unstaged.

## Tests And Checks

Commands run:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_api_search.py -q -k "steel_guitar_101 or quarantine_smoke_concrete_resolvers or off_domain_user_smoke_prompt"
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_api_search.py tests/test_fretboard_examples.py -q
.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py tests/test_api_contract.py -q
.venv/bin/python scripts/run_full_answer_quality_eval.py
.venv/bin/python -m pytest
```

Results:
- Focused 101/API tests: `5 passed, 233 deselected`.
- Classifier/API/fretboard scoped suite: `367 passed`.
- Contract/eval scoped suite: `68 passed`.
- Strict answer eval script: `151 pass / 33 warn / 111 fail`, `Private-source behavior correct: True`.
- Full pytest: `706 passed, 2 failed`.

Known unrelated full-suite failures:
- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

These are the same static/UI caveats already documented in `docs/handoffs/task-completions/integration-status.md`.

## Behavior Before / After

Before:
- Foundation prompts such as `What is a steel guitar?`, `What does E9 mean?`, `What does C6 mean?`, and `What is it called pedal steel?` could reach generic fallback/source-shaped answer paths instead of a plain beginner explanation.

After:
- `What is a steel guitar?` answers directly with bar/sliding context and distinguishes lap steel from pedal steel.
- `What does E9 mean?` explains E9 as the common pedal-steel tuning and names the dominant-ninth flavor.
- `What does C6 mean?` explains C6 as C-E-G-A and points to western swing/jazzier harmony.
- `What is it called pedal steel?` explains the steel bar plus floor-pedal pitch-changing reason.
- Foundational answers use `sources: []`, `warnings: []`, and no fretboard payload.

## Integration Notes

- This is a backend answer-routing addition under Lane 05.
- Source cards remain available for source-backed steel questions.
- Deterministic chord/fretboard paths still attach fretboard payloads where already supported.
- Off-domain prompts such as `Give me a JavaScript sorting algorithm.` still return the existing scope guardrail without retrieval/source cards.
- The generic fallback text remains in place for non-foundation unsupported prompts; this task only reduces false fallback for clear 101 concepts.

## Risk Assessment

Risk: low.

Reason:
- The change is deterministic, source-free, and inserted before the generic fallback only for narrowly recognized foundation question forms.
- It does not alter retrieval, Chroma, schema, UI, auth, deployment, or source-card rendering.
- Focused and broad backend suites passed; only known unrelated static/UI full-suite failures remain.

Rollback:
- Revert the foundation answer block and tests from `steel_guitar_rag/curated_answers.py` and `tests/test_api_search.py`.

## Commit Readiness

Safe to commit.

Safe-to-stage file list:
- `steel_guitar_rag/curated_answers.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/steel-guitar-101-foundation-router-fix.md`

Must remain unstaged:
- `corpus-private/reports/full-answer-quality-eval.md`
- `corpus-private/reports/full-answer-quality-eval.json`
- parked corpus/source/design/deploy/static/private/generated files already present in the dirty worktree.

## Suggested Next Step

Lane 15 QA / Answer Eval:

```text
QA the Steel Guitar 101 foundation router fix. Read docs/handoffs/task-completions/steel-guitar-101-foundation-router-fix.md, then smoke beginner prompts including: What is a steel guitar? What does E9 mean? What does C6 mean? What is it called pedal steel? What is a copedent? What are grips? What is the difference between lap steel and pedal steel? Confirm answers are direct, teacher-first, source-free for foundation concepts, warning-free, and do not attach fretboard unless the prompt asks for positions.
```
