# QA: Six Smoke Failures Answer-Quality Fix

Date: 2026-06-13 03:23 CT
Lane: 15 QA / Answer Eval
Branch: `feature/answer-api`
HEAD: `ff5dc6b`

## Decision

Pass.

QA approves a narrowly hunk-staged Repo Steward commit for the six-smoke-failure answer-quality fix.

Commit readiness: Safe to commit, but only with careful hunk staging of the approved files/hunks listed below. The worktree contains many unrelated parked changes, including UI files, generated/private-adjacent artifacts, and other lane work.

## Scope Reviewed

Read and checked:

- `AGENTS.md`
- `docs/llm-guidance/answer-contract.md`
- `docs/llm-guidance/eval-rubric.md`
- `docs/llm-guidance/product-memory.md`
- `docs/llm-guidance/teacher-first-answer-policy.md`
- `tests/answer_eval/question_bank.jsonl`
- `tests/answer_eval/expected_behaviors.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/retrieval-gating-implementation.md`
- `docs/handoffs/task-completions/qa-retrieval-gating-implementation.md`
- `docs/handoffs/task-completions/six-smoke-failures-answer-quality-fix.md`
- `pocketsteel/curated_answers.py`
- `pocketsteel/fretboard_examples.py`
- `pocketsteel/answering.py`
- `pocketsteel/answer_contracts.py`
- `tests/test_api_search.py`

## Verification Summary

- Retrieval gating remains intact.
- Off-domain prompts still suppress retrieval, sources, and fretboard payloads.
- Unsafe/impossible prompts still suppress retrieval, sources, and fretboard payloads.
- Steel source-backed prompts still retrieve supporting sources.
- Non-position steel prompts did not show fretboard payloads in the smoke.
- `Where are my G chord positions?` and `Show me C positions on E9.` returned deterministic fretboard payloads.
- Diminished chord answer is teacher-first practical content, not raw forum fragments.
- Fender Steel King answer is practical teaching/diagnostic content, not raw forum fragments.
- Hum/changer answer is diagnostic troubleshooting with safe guidance.
- B+C pedals answer is useful teaching content.
- No `[object Object]` appeared.
- No weak-source warning appeared as the primary answer.
- No raw SGF/forum fragment appeared as the primary answer.
- Public `/api/answer` response shape remains covered by API contract/search tests.
- No UI file is approved for this fix. The worktree does contain unrelated parked UI changes, so Repo Steward must not stage UI files.
- Teacher-first answer composer changes are limited to the reviewed answer-quality slice.

## 12-Prompt Smoke

Method: same-origin `/api/answer` fallback against the current-worktree loopback server. Browser control was attempted, but the available browser handle did not expose a direct navigation method in this thread (`globalThis.__qaBrowser.navigate is not a function`). The user allowed same-origin `/api/answer` fallback.

Server command:

```bash
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8781 \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2 \
  --candidate-k 20 \
  --min-excerpt-chars 80 \
  --question-only-penalty 0.12 \
  --mention-only-penalty 0.20 \
  --answer-advice-boost 0.04 \
  --quality-boost 0.04 \
  --quality-threshold 0.70 \
  --noise-penalty 0.06 \
  --noise-threshold 0.60
```

Reachability:

- `GET http://127.0.0.1:8781/` returned `200 OK`.
- `GET http://127.0.0.1:8781/api/answer` returned `405 Method Not Allowed`, as expected for GET.

Smoke artifact:

- `/tmp/pocketsteel-qa-six-smoke-12-prompt-api-smoke.json`

Totals:

- Total: 12
- Pass: 12
- Fail: 0

| # | Prompt | Result | Sources | Fretboard positions | `[object Object]` | Weak warning | Raw fragment | Answer summary |
|---:|---|---|---:|---:|---|---|---|---|
| 1 | What are common uses for the E9 9th string? | PASS | 6 | 0 | No | No | No | Explains the 9th string D note as dominant-7th color, passing/scale tone, and practical E9 usage. |
| 2 | Why would a player prefer a wound 6th string? | PASS | 6 | 0 | No | No | No | Explains tone/feel tradeoff and changer-travel caution for G# to F# lower. |
| 3 | What do players say about using the 6th string lower? | PASS | 6 | 0 | No | No | No | Explains the G# to F# lower and practical uses in passing notes and chord color. |
| 4 | How do players approach diminished chords on E9? | PASS | 6 | 0 | No | No | No | Teacher-first diminished explanation: spell the sound, use it as movable passing tension, resolve cleanly. |
| 5 | What are common Fender Steel King settings? | PASS | 6 | 0 | No | No | No | Practical Steel King settings guidance: moderate EQ, set volume at gig level, adjust by room/pickup. |
| 6 | How do players diagnose hum that changes when touching the changer? | PASS | 6 | 0 | No | No | No | Diagnostic flow for isolating amp vs signal chain, grounding/cable/guitar causes, and safe checks. |
| 7 | Where are my G chord positions? | PASS | 0 | 44 | No | No | No | Deterministic G positions: 3rd fret open, 6th fret A+F, 10th fret A+B, with visual payload. |
| 8 | Show me C positions on E9. | PASS | 0 | 44 | No | No | No | Deterministic C positions: 8th fret open, 11th fret A+F, 15th fret A+B, with visual payload. |
| 9 | What is the capital of France? | PASS | 0 | 0 | No | No | No | Scope guardrail redirects to steel-guitar topics; no retrieval or fretboard payload. |
| 10 | Write me a Python script to scrape Instagram. | PASS | 0 | 0 | No | No | No | Scope/safety guardrail redirects to steel-guitar topics; no retrieval or fretboard payload. |
| 11 | Explain B+C pedals. | PASS | 6 | 0 | No | No | No | Teacher-first B+C explanation as melodic/position-shift tool with practical strings 3-4-5 work. |
| 12 | Build a 7-day practice plan for blocking. | PASS | 0 | 0 | No | No | No | Structured 7-day blocking practice plan with timed work and measurable practice goals. |

Screenshots: none. Browser control was not available enough for navigation, so this was an API fallback smoke.

## Test Commands And Results

```bash
git status --short
```

Result: dirty worktree with many unrelated parked files. Relevant reviewed changes are in backend answer files and `tests/test_api_search.py`.

```bash
git diff --check
```

Result: passed.

```bash
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
```

Result: `62 passed in 0.07s`.

```bash
.venv/bin/python -m pytest tests/test_answer_eval.py
```

Result: `9 passed in 0.02s`.

```bash
.venv/bin/python -m pytest tests/test_api_search.py -k "classifier_gate or scope_guardrail_for_numbers or position_questions_can_still_return_fretboard_payloads"
```

Result: `5 passed, 183 deselected in 0.07s`.

```bash
.venv/bin/python -m pytest tests/test_api_search.py -k "remaining_retrieval_gating_smoke_failures or amp_hum_advice_stays_diagnostic"
```

Result: `2 passed, 186 deselected in 0.08s`.

```bash
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
```

Result: `233 passed in 0.77s`.

264-row classifier validation:

```text
rows: 264
contract_key_mismatches: 0
invalid_domain_enum: 0
invalid_intent_enum: 0
invalid_shape_enum: 0
offdomain_or_unsafe_domain_mismatches: 0
offdomain_or_unsafe_retrieval_mismatches: 0
offdomain_or_unsafe_sources_mismatches: 0
offdomain_or_unsafe_fretboard_mismatches: 0
impossible_or_large_output_misclassified_as_steel: 0
impossible_or_large_output_retrieval_allowed: 0
nonposition_fretboard_overclassified: 0
steel_source_backed_expected_but_off_domain: 0
steel_source_backed_expected_retrieval_but_classifier_disallows: 0
steel_source_backed_expected_needs_sources_false: 0
```

## Remaining Failures

None found in the requested tests or 12-prompt smoke.

Residual risk: the smoke used API fallback rather than browser DOM screenshots. It still verified the answer payload, source suppression/presence, fretboard payload presence/suppression, weak-warning absence, raw-fragment absence, and `[object Object]` absence.

## Files Approved For Commit

Approved only as narrowly staged hunks:

- `pocketsteel/curated_answers.py`
  - teacher-first diminished chord route
  - teacher-first Fender Steel King settings route/recognizer
  - teacher-first B+C pedals route/recognizer
  - symmetric hum/changer diagnostic matcher, if present in this file's relevant hunk
- `pocketsteel/fretboard_examples.py`
  - deterministic parser expansion for `Where are my <root> chord positions?`
  - deterministic parser expansion for `Show me <root> positions on E9.`
- `pocketsteel/answering.py`
  - symmetric hum/changer diagnostic matcher
- `pocketsteel/answer_contracts.py`
  - symmetric hum/changer diagnostic matcher
- `tests/test_api_search.py`
  - `test_remaining_retrieval_gating_smoke_failures_get_teacher_first_answers`
  - `test_amp_hum_advice_stays_diagnostic_and_non_visual`
  - any direct fixture/helper hunks required only by those two tests
- `docs/handoffs/task-completions/six-smoke-failures-answer-quality-fix.md`
- `docs/handoffs/task-completions/qa-six-smoke-failures-answer-quality-fix.md`

## Hunks Requiring Careful Staging

`tests/test_api_search.py` is heavily touched by many lanes. Repo Steward should hunk-stage only:

- the focused regression test that checks the six former 12-prompt smoke failures
- the focused hum/changer diagnostic non-visual regression test
- minimal test helper adjustments required by those tests, if any

Do not stage unrelated API/search test changes from other lanes.

## Files That Should Remain Parked

Do not stage for this commit:

- `ui/pedal-steel-fretboard.js`
- `ui/steel-guitar-rag-landing.html`
- `ui/steel-guitar-rag-mock.html`
- `public/`
- `ui/brand/`
- `Neon Sign/`
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector store files
- embeddings
- source-inbox changes
- provenance/legal metadata dumps
- deployment/DNS/Cloudflare or `.wrangler` changes
- unrelated docs, scripts, ingestion, or corpus tooling changes
- generated smoke outputs under `/tmp`

## Risks

- Browser DOM screenshots were not captured because browser navigation was unavailable in this thread. API fallback was explicitly allowed and passed.
- The worktree is broad and dirty. Commit safety depends on precise hunk staging.
- Source-backed teacher-first answers still return source cards as supporting evidence. This matches retrieval-gating policy for source-backed steel questions.

## Human Decision Needed

No for QA approval of the narrow six-failure fix.

Yes for Repo Steward hunk-staging discipline: use the approved hunk list above and avoid unrelated parked files.

## Recommended Next Step

Repo Steward should hunk-stage only the approved six-failure fix hunks, run the focused tests plus `git diff --check`, and commit the narrow fix.

## Exact Next Prompt For 01 Repo Steward

```text
Read:
- AGENTS.md
- docs/handoffs/task-completions/six-smoke-failures-answer-quality-fix.md
- docs/handoffs/task-completions/qa-six-smoke-failures-answer-quality-fix.md

Branch: feature/answer-api

Do not deploy, change DNS, touch Chroma, regenerate embeddings, run scraping, or stage unrelated parked work.

Hunk-stage only the approved six-smoke-failure answer-quality fix:
- pocketsteel/curated_answers.py: teacher-first diminished, Fender Steel King, B+C pedals, and related recognizer hunks
- pocketsteel/fretboard_examples.py: parser expansion for "Where are my <root> chord positions?" and "Show me <root> positions on E9."
- pocketsteel/answering.py: hum/changer diagnostic matcher hunk
- pocketsteel/answer_contracts.py: hum/changer diagnostic matcher hunk
- tests/test_api_search.py: focused six-smoke-failure regression tests and minimal required helpers only
- docs/handoffs/task-completions/six-smoke-failures-answer-quality-fix.md
- docs/handoffs/task-completions/qa-six-smoke-failures-answer-quality-fix.md

Do not stage UI files, public assets, corpus/private/vector/source-inbox/provenance/deployment files, generated reports, or unrelated docs/scripts/tests.

Run:
git diff --cached --check
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py

If clean, commit with a narrow message for the six smoke failure answer-quality fix.
```

## Exact Next Prompt For Lane 05 If Not Approved

Not needed. QA found no remaining blocker in this slice.
