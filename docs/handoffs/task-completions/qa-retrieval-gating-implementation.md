# QA Retrieval-Gating Implementation

## Task Summary

- What was requested: QA the narrow retrieval-gating implementation, verify it blocks off-domain and unsafe/impossible retrieval without changing valid steel-guitar behavior, rerun focused tests plus the 264-row classifier validation, rerun the 12-prompt browser smoke, and report commit readiness.
- What was completed: read the requested guidance, plan/review/implementation handoffs, classifier, `/api/answer`, retrieval/search, source-card, fretboard contract, and answer/API tests; ran the requested focused tests/checks; ran the explicit 264-row question-bank validation; started the documented local loopback v2 rerank preview; attempted Browser-plugin UI smoke; fell back to same-origin `/api/answer` payload smoke when Browser navigation failed.
- What was intentionally not changed: no implementation files, UI files, Chroma/vector stores, embeddings, corpus files, scraping, deployment, DNS, `.wrangler`, source inbox data, provenance/legal files, design assets, staging, or commits were touched by this QA task.

Branch: `feature/answer-api`

HEAD observed: `5844f4e`

## Pass/Fail Decision

Pass for the narrow retrieval-gating implementation.

The implementation correctly prevents retrieval/source-card/fretboard attachment for the tested off-domain and unsafe/impossible prompts, while preserving valid source-backed steel retrieval and existing deterministic fretboard behavior for already-supported phrase shapes.

Product/browser-smoke readiness is still not pass. The 12-prompt smoke still has 6 answer-quality failures that this narrow retrieval-gating slice does not solve.

## Implementation Review Findings

- `steel_guitar_rag/api.py` now calls `classify_answer_request(...)` and gates before deterministic routes and before `_search_for_answer(...)`.
- `_should_gate_answer_intent(...)` gates:
  - `domain == "unsafe_or_impossible"`
  - `domain == "off_domain" and intent == "small_talk"`
- The gate returns existing public `AnswerResponse` shape:
  - `answer`
  - `mode`
  - `sources: []`
  - `warnings: []`
  - `sections`
  - no `fretboard`
- No classifier metadata is exposed in public JSON.
- Steel-guitar prompts are not broadly gated by `retrieval_allowed=false`; source-backed steel prompts still reach retrieval.
- Teacher-first answer composer work was not mixed into this slice.
- Source-card/source-note code was not changed by this QA task.
- Fretboard render contract was not changed by this QA task.
- UI files are dirty in the broader worktree, but they are parked/unrelated; the retrieval-gating implementation handoff does not list UI files in scope.

## Requirement Verification

| Requirement | Result | Evidence |
|---|---:|---|
| Off-domain questions do not run retrieval | Pass | New API tests assert `search_index.calls == []` for `What is the capital of France?`. |
| Unsafe/impossible questions do not run retrieval | Pass | New API tests assert `search_index.calls == []` for `Write me a Python script to scrape Instagram.` and large-output prompts. |
| Off-domain questions do not return source cards/source notes | Pass | Unit/API tests and live payload smoke returned `sources: []`, `warnings: []`. |
| Unsafe/impossible questions do not return source cards/source notes | Pass | Unit/API tests and live payload smoke returned `sources: []`, `warnings: []`. |
| Off-domain questions do not return fretboard payload | Pass | Unit/API tests and live payload smoke returned no top-level `fretboard`. |
| Unsafe/impossible questions do not return fretboard payload | Pass | Unit/API tests and live payload smoke returned no top-level `fretboard`. |
| Valid steel-guitar questions still retrieve sources | Pass | Tests preserve source-backed retrieval; live smoke source-backed prompts returned source cards. |
| Player, brand, vendor, history, and gear questions still retrieve sources | Pass | `test_classifier_gate_preserves_source_backed_steel_retrieval` covers Buddy Emmons, Mullen/MSA, vendors, and E9 9th string. |
| Non-position steel questions do not show fretboard | Pass | Unit/API tests and live payload smoke showed no fretboard for gear/forum/practice prompts. |
| Position/fretboard questions can still show fretboard | Partial | Supported unit prompts such as `Where can I play a G chord?` pass; exact smoke prompts `Where are my G chord positions?` and `Show me C positions on E9.` still fail with sources and no fretboard. |
| `/api/answer` response shape remains stable | Pass | API contract tests passed; public payload shape contains no classifier metadata. |
| Teacher-first answer composer was not mixed into this slice | Pass | Code review and implementation handoff confirm no composer/source-note hierarchy changes. |
| No UI files changed by this slice | Pass with caveat | Implementation scope excludes UI. Current worktree has unrelated parked UI changes; do not stage them with this slice. |

## Unit And API Test Results

Commands run:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_search.py -k "classifier_gate or scope_guardrail_for_numbers or position_questions_can_still_return_fretboard_payloads"
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
```

Results:

- `git diff --check`: passed.
- `tests/test_answer_intent_classifier.py`: `62 passed`.
- `tests/test_answer_eval.py`: `9 passed`.
- New/focused retrieval-gating subset: `5 passed, 182 deselected`.
- `tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`: `232 passed`.

Full pytest was not rerun by this QA task because the user requested focused QA and the implementation handoff already reports full pytest `655 passed`.

## 264-Row Validation Results

Command run: an explicit Python validation over `tests/answer_eval/question_bank.jsonl` using `classify_answer_request(...)`.

Rows checked: `264`

Mismatch counts:

- `contract_key_mismatches`: 0
- `invalid_domain_enum`: 0
- `invalid_intent_enum`: 0
- `invalid_shape_enum`: 0
- `offdomain_or_unsafe_domain_mismatches`: 0
- `offdomain_or_unsafe_retrieval_mismatches`: 0
- `offdomain_or_unsafe_sources_mismatches`: 0
- `offdomain_or_unsafe_fretboard_mismatches`: 0
- `impossible_or_large_output_misclassified_as_steel`: 0
- `impossible_or_large_output_retrieval_allowed`: 0
- `nonposition_fretboard_overclassified`: 0
- `steel_source_backed_expected_but_off_domain`: 0
- `steel_source_backed_expected_retrieval_but_classifier_disallows`: 0
- `steel_source_backed_expected_needs_sources_false`: 0

Result: pass.

## Browser Smoke Attempt

Local preview startup command:

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

- `GET /`: `HTTP/1.0 200 OK`
- `GET /api/answer`: `HTTP/1.0 405 Method Not Allowed`

Browser tool status:

- Codex in-app Browser setup succeeded far enough to read Browser documentation.
- Creating a tab succeeded once, but tab navigation to the local URL repeatedly failed with a closed-pipe browser transport error.
- Node Playwright/Puppeteer and Python Playwright/Selenium are not installed in this repo environment.
- Screenshots were therefore not supported for this run.

Fallback smoke used the same-origin API endpoint:

```text
http://127.0.0.1:8781/api/answer
```

Generated fallback artifact:

- `/tmp/steel_guitar_rag-qa-retrieval-gating/12-prompt-api-smoke.json`

## 12-Prompt Smoke Results

Manual rubric result from the same-origin payload smoke: `6 pass`, `6 fail`.

| # | Question | Result | Sources | Fretboard | `[object Object]` | Weak-source wording | Raw/forum fragment issue | Notes |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | What are common uses for the E9 9th string? | Pass | Yes | No | No | No | No | Now gives a useful synthesized 9th-string answer. |
| 2 | Why would a player prefer a wound 6th string? | Pass | Yes | No | No | No | No | Good tradeoff answer. |
| 3 | What do players say about using the 6th string lower? | Pass | Yes | No | No | No | No | Clear G# to F# use-case answer. |
| 4 | How do players approach diminished chords on E9? | Fail | Yes | No | No | No | Yes | Main answer is still source-fragment bullets, not synthesized teaching. |
| 5 | What are common Fender Steel King settings? | Fail | Yes | No | No | No | Yes | Does not provide useful settings; answer is fragment/background text. |
| 6 | How do players diagnose hum that changes when touching the changer? | Fail | Yes | No | No | No | Yes | Returns wrong-topic changer/string fragments, not hum diagnosis. |
| 7 | Where are my G chord positions? | Fail | Yes | No | No | No | Yes | Deterministic position route escaped; no fretboard. |
| 8 | Show me C positions on E9. | Fail | Yes | No | No | No | Yes | Deterministic position route escaped; no fretboard. |
| 9 | What is the capital of France? | Pass | No | No | No | No | No | Retrieval gate works; source-free scoped guardrail. |
| 10 | Write me a Python script to scrape Instagram. | Pass | No | No | No | No | No | Retrieval gate works; source-free unsafe/out-of-scope guardrail. |
| 11 | Explain B+C pedals. | Fail | Yes | No | No | No | Yes | Still returns related-source fragments instead of a direct explanation. |
| 12 | Build a 7-day practice plan for blocking. | Pass | No | No | No | No | No | Useful source-free practice plan. |

Screenshot paths: none. Screenshot capture was blocked by Browser navigation failure.

## Remaining Answer-Quality Failures Not Fixed By Retrieval Gating

1. Source-backed synthesis still allows fragment-style answers:
   - Diminished chords
   - Fender Steel King settings
   - Hum that changes when touching the changer
   - B+C pedals

2. Deterministic position routing still misses natural phrasing:
   - `Where are my G chord positions?`
   - `Show me C positions on E9.`

3. The retrieval gate specifically fixed the old off-domain/unsafe retrieval leak:
   - `What is the capital of France?` now has no sources/fretboard/warnings.
   - `Write me a Python script to scrape Instagram.` now has no sources/fretboard/warnings.

## Commit Approval

QA approves committing the narrow retrieval-gating slice only, with exact-hunk staging.

This approval does not mean the answer stack is product-ready or outside-tester-ready. The 12-prompt smoke still has 6 product-facing answer failures.

Commit readiness: `Needs human review first`.

Reason: the implementation itself is green, but the worktree is broadly dirty, `tests/test_api_search.py` has overlapping parked edits, UI files are dirty from other lanes, and the requested visual browser smoke could not produce screenshots due Browser tooling failure.

## Exact Files Approved For Commit

Approved for the retrieval-gating slice, after exact-path and hunk review:

- `steel_guitar_rag/api.py`
- retrieval-gating hunks only in `tests/test_api_search.py`
- `docs/handoffs/task-completions/retrieval-gating-implementation.md`
- `docs/handoffs/task-completions/qa-retrieval-gating-implementation.md`

Optional docs if Repo Steward wants the full coordination chain in the same docs commit or adjacent docs commit:

- `docs/handoffs/task-completions/retrieval-gating-implementation-plan.md`
- `docs/handoffs/task-completions/qa-retrieval-gating-plan-review.md`

## Exact Files That Should Remain Parked

Do not stage with the retrieval-gating slice:

- UI files:
  - `ui/pedal-steel-fretboard.js`
  - `ui/steel-guitar-rag-landing.html`
  - `ui/steel-guitar-rag-mock.html`
  - `ui/brand/`
  - `public/`
  - `Neon Sign/`
- Source/corpus/provenance/generated data:
  - `corpus-private/`
  - `corpus-v2/`
  - Chroma/vector stores
  - embeddings
  - `source-inbox/`
  - `corpus_metadata/`
  - provenance/legal/source-policy files unless separately approved
- Deployment/DNS/security artifacts:
  - `.wrangler/`
  - deployment docs/config/secrets
  - DNS/Cloudflare changes
- Other parked backend/QA files not directly part of the retrieval gate:
  - `steel_guitar_rag/answer_contracts.py`
  - `steel_guitar_rag/curated_answers.py`
  - `steel_guitar_rag/curated_source_registry.py`
  - `steel_guitar_rag/fretboard_examples.py`
  - `steel_guitar_rag/schema.py`
  - root `rag_*` scripts
  - unrelated smoke/eval scripts and tests

## Exact Next Prompt For 01 Repo Steward If Approved

```text
LANE: 01 Repo Steward
REASONING: HIGH

Review and commit only the narrow retrieval-gating slice.

Read:
- AGENTS.md
- docs/handoffs/task-completions/retrieval-gating-implementation.md
- docs/handoffs/task-completions/qa-retrieval-gating-implementation.md

Approved scope:
- steel_guitar_rag/api.py
- retrieval-gating hunks only in tests/test_api_search.py
- docs/handoffs/task-completions/retrieval-gating-implementation.md
- docs/handoffs/task-completions/qa-retrieval-gating-implementation.md

Optional coordination docs, if you choose to include the plan/review chain in the same commit or a neighboring docs commit:
- docs/handoffs/task-completions/retrieval-gating-implementation-plan.md
- docs/handoffs/task-completions/qa-retrieval-gating-plan-review.md

Do not use git add .
Do not stage UI files, Chroma/vector stores, embeddings, corpus-private, corpus-v2, source-inbox, provenance/legal/source-policy files, deployment/DNS/.wrangler files, public/, ui/brand/, Neon Sign/, generated reports, or unrelated parked backend/eval changes.

Before commit, run:
- git diff --check
- .venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_answer_eval.py
- .venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py

Commit only if exact-path/hunk review confirms no unrelated parked work is included.
```

## Exact Next Prompt For 05 Backend / RAG Integration If Not Approved Or For Next Product Fix

```text
LANE: 05 Backend / RAG Integration
REASONING: HIGH

Fix the remaining answer-quality failures from docs/handoffs/task-completions/qa-retrieval-gating-implementation.md.

Do not modify Chroma, embeddings, scraping, deployment, DNS, UI files, corpus-private, corpus-v2, source-inbox, provenance/legal files, or design assets.

Remaining smoke failures:
- How do players approach diminished chords on E9?
- What are common Fender Steel King settings?
- How do players diagnose hum that changes when touching the changer?
- Explain B+C pedals.
- Where are my G chord positions?
- Show me C positions on E9.

Goals:
- Source-backed steel answers must be synthesized teaching/advice, not raw forum fragments.
- Steel King settings and hum/changer prompts must answer the asked diagnostic/settings question directly.
- B+C pedals must get a direct steel-specific concept explanation, not related-source fragments.
- Natural position prompts such as "Where are my G chord positions?" and "Show me C positions on E9." must route to deterministic source-free fretboard-backed answers.

Preserve the newly implemented retrieval gate:
- off-domain and unsafe/impossible prompts must not run retrieval
- sources/warnings/fretboard must stay empty for guardrail answers
- public /api/answer shape must not expose classifier metadata

Add focused tests and rerun the 12-prompt smoke after implementation.
```

## Risk Assessment

Risk: medium.

The retrieval-gating code path itself is small and well-covered, but commit staging is risky because the worktree is broadly dirty and `tests/test_api_search.py` has overlapping edits from prior lanes. Product readiness risk remains high enough to keep outside testers paused until the 6 remaining smoke failures are fixed and resmoked.

Rollback notes: remove the `_should_gate_answer_intent(...)` branch/helper from `steel_guitar_rag/api.py` and the new retrieval-gating test hunks if the gate needs to be backed out. No data-store rollback is involved.

## Suggested Next Step

Recommended lane: `01 Repo Steward` for exact-hunk commit review of the narrow retrieval-gating slice, then `05 Backend / RAG Integration` for the remaining six answer-quality failures.
