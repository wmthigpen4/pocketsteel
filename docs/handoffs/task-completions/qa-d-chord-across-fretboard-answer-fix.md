# QA: D Chord Across-Fretboard Answer Fix

## Task summary
- What was requested: QA the D chord across-the-fretboard answer fix without modifying implementation files; verify teacher-first answer quality, practical E9 positions, fretboard payload, source hygiene, retrieval gating, G/C position regressions, and smoke behavior.
- What was completed: Read the requested guidance/handoffs and current answer/fretboard/test files, inspected the D-fix diff, ran focused and broad tests, ran explicit 264-row classifier validation, started the repo-supported local current-worktree smoke server, performed direct `/api/answer` and Browser UI smoke against the current worktree.
- What was intentionally not changed: No runtime implementation files, UI files, Chroma/vector stores, embeddings, corpus data, deployment, DNS, Cloudflare config, or source/corpus files were modified by this QA task. No files were staged or committed.

## Pass/fail decision
**Needs human review first**

The D-chord fix itself passed all focused checks:
- “How do I play a D chord across the fretboard of the E9?” now returns a teacher-first deterministic D major answer.
- The answer includes practical E9 D positions: 10th fret open/no pedals, 13th fret A+F, 17th fret A+B, plus across-fretboard alternates at 5th fret A+B and 3rd fret E-lower.
- Top-level `response.fretboard` is present with `D major positions on E9`.
- Direct POST returned 40 fretboard positions and no source cards/warnings.
- Browser UI rendered the fretboard and did not show `[object Object]`, weak-source warning, or raw SGF/forum fragments.

However, the optional 15-prompt smoke exposed an adjacent non-D product issue:
- `Build a 7-day practice plan for blocking.` returns a focused 25-minute routine, not a 7-day plan.
- This does not regress the D-fix behavior, but it means the full 15-prompt smoke is not clean.

## D chord prompt result
Direct POST command:

```bash
curl -sS -X POST http://127.0.0.1:8781/api/answer \
  -H 'Content-Type: application/json' \
  -H 'X-Steel-Rag-Dev-Access-Role: beta_user' \
  --data '{"question":"How do I play a D chord across the fretboard of the E9?"}' \
  | .venv/bin/python -c '...summary parser...'
```

Result:

```json
{
  "answer_contains_d_major": true,
  "answer_contains_10": true,
  "answer_contains_13": true,
  "answer_contains_17": true,
  "answer_contains_5_ab": true,
  "answer_contains_3_e_lower": true,
  "source_count": 0,
  "warning_count": 0,
  "has_fretboard": true,
  "fretboard_title": "D major positions on E9",
  "position_count": 40,
  "position_ids_sample": [
    "d-open-grip-3-4-5-10",
    "d-open-10",
    "d-open-grip-5-6-8-10",
    "d-open-grip-5-7-8-10",
    "d-e-lower-5-7-8-3",
    "d-e-lower-7-8-10-3",
    "d-e-lower-4-5-7-3",
    "d-e-lower-1-4-5-3"
  ]
}
```

Browser screenshot:
- `/tmp/steel_guitar_rag-d-chord-fix-browser-smoke/screenshots/d-chord-across-fretboard.png`

## Smoke result
Local current-worktree server:

```bash
STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first \
STEEL_RAG_ENABLE_PRIVATE_SOURCES=true \
STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma \
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 \
STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma \
STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 \
STEEL_RAG_ANSWER_AUTH_MODE=local_dev \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8781 \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2 \
  --answer-auth-mode local_dev \
  --auth-provider scaffold
```

Reachability:
- `GET http://127.0.0.1:8781/` returned `200 OK`.
- `GET http://127.0.0.1:8781/api/answer` returned `405 Method Not Allowed`, as expected for GET.

Browser URL:
- `http://127.0.0.1:8781/ui/steel-guitar-rag-mock.html?access=beta_user&v=qa-d-chord-across-fretboard-answer-fix`

10-prompt D-focused smoke:
- Result: `10 passed / 0 failed`.
- D across-fretboard and D positions prompts both showed fretboard payloads, no sources, no weak-source warning, no raw fragments, no `[object Object]`.
- G and C position prompts still passed with fretboard payloads and no sources.
- Off-domain/unsafe prompts suppressed sources and fretboard.

15-prompt smoke:
- Result: `14 passed / 1 failed`.
- Failure: `Build a 7-day practice plan for blocking.`
  - Actual: begins `Use a focused 25-minute E9 routine with one measurable result.`
  - Source count: `0`
  - Fretboard: `false`
  - No `[object Object]`, weak-source warning, or raw fragment.
  - Classification: adjacent answer-quality specificity issue, not a D-fix regression.

Raw smoke artifacts:
- `/tmp/steel_guitar_rag-d-chord-fix-browser-smoke/browser-smoke-results-stable.json`
- `/tmp/steel_guitar_rag-d-chord-fix-browser-smoke/screenshots/d-chord-across-fretboard.png`

## Tests and checks
Commands run:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_fretboard_examples.py::test_d_major_across_fretboard_position_prompts_are_supported tests/test_api_search.py::test_remaining_retrieval_gating_smoke_failures_get_teacher_first_answers
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
```

Results:
- `git diff --check`: passed.
- Focused D/fix tests: `2 passed`.
- `tests/test_answer_intent_classifier.py`: `62 passed`.
- `tests/test_answer_eval.py`: `9 passed`.
- `tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`: `234 passed`.

264-row classifier validation:

```json
{
  "contract_key_mismatches": 0,
  "impossible_or_large_output_misclassified_as_steel": 0,
  "impossible_or_large_output_retrieval_allowed": 0,
  "invalid_domain_enum": 0,
  "invalid_shape_enum": 0,
  "nonposition_fretboard_overclassified": 0,
  "offdomain_or_unsafe_domain_mismatches": 0,
  "offdomain_or_unsafe_fretboard_mismatches": 0,
  "offdomain_or_unsafe_retrieval_mismatches": 0,
  "offdomain_or_unsafe_sources_mismatches": 0,
  "rows": 264,
  "steel_source_backed_expected_but_off_domain": 0,
  "steel_source_backed_expected_needs_sources_false": 0,
  "steel_source_backed_expected_retrieval_but_classifier_disallows": 0
}
```

Note: an initial ad hoc validation command used an outdated local `allowed_answer_shape` enum list and produced false `invalid_shape_enum` mismatches. It was corrected and rerun with the current classifier shape values.

Skipped:
- Full pytest was not rerun because this QA task did not change implementation or test files other than this handoff, and the requested focused/broad suites passed. The optional 15-prompt smoke found one adjacent product issue.

## Files changed
Changed by this QA task:
- `docs/handoffs/task-completions/qa-d-chord-across-fretboard-answer-fix.md`

Generated artifacts:
- `/tmp/steel_guitar_rag-d-chord-fix-browser-smoke/browser-smoke-results.json`
- `/tmp/steel_guitar_rag-d-chord-fix-browser-smoke/browser-smoke-results-stable.json`
- `/tmp/steel_guitar_rag-d-chord-fix-browser-smoke/screenshots/d-chord-across-fretboard.png`

Implementation/test files inspected as the D-fix scope:
- `steel_guitar_rag/fretboard_examples.py`
- `steel_guitar_rag/curated_answers.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `steel_guitar_rag/api.py`

Pre-existing/parked dirty files observed in the shared worktree include broad backend, UI, corpus/provenance, docs, source-inbox, and design-asset paths. This QA task did not touch them.

## Commit recommendation
QA does not recommend a broad commit until the human/Repo Steward decides how to handle the adjacent 7-day practice-plan smoke failure.

If Repo Steward chooses to split the D-fix despite the adjacent smoke issue, the exact likely D-fix files are:
- `steel_guitar_rag/fretboard_examples.py`
- `steel_guitar_rag/curated_answers.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/d-chord-across-fretboard-answer-fix.md`
- `docs/handoffs/task-completions/qa-d-chord-across-fretboard-answer-fix.md`

Hunks needing careful staging:
- `steel_guitar_rag/fretboard_examples.py`: major-chord prompt patterns supporting D/across-fretboard/position phrasing and generated D major alternate positions.
- `steel_guitar_rag/curated_answers.py`: deterministic major-position answer enrichment for across-the-fretboard alternates.
- `tests/test_fretboard_examples.py`: D major across-fretboard payload facts.
- `tests/test_api_search.py`: D across-fretboard answer/source/fretboard regression assertions.

Files that should remain parked unless separately approved:
- `ui/pedal-steel-fretboard.js`
- `ui/steel-guitar-rag-mock.html`
- `public/`
- `ui/brand/`
- `Neon Sign/`
- `source-inbox/`
- `corpus-private/`
- `corpus-v2/`
- corpus/provenance/legal/deploy/design asset changes unrelated to this D-fix QA.

## Integration notes
- Retrieval gating remained intact in smoke: off-domain and unsafe prompts suppressed sources and fretboard.
- G and C deterministic position prompts still rendered fretboard payloads and source-free answers.
- Non-position prompts in the smoke did not attach fretboard.
- Source-backed steel prompts displayed source cards as secondary support and did not show raw SGF/forum fragments as the primary answer.
- No UI files were changed by this QA task. The current shared worktree already contains parked UI changes from other lanes.
- The local smoke server read configured Chroma stores but did not modify Chroma, embeddings, app config, DNS, deployment, or tunnel routing.

## Risk assessment
Risk: Medium.

Why:
- The D-fix itself is low risk based on focused tests and browser smoke.
- The shared worktree is very broad and dirty, so Repo Steward must use exact-path and possibly hunk-level staging.
- The optional 15-prompt smoke found an adjacent answer-quality issue for a 7-day practice-plan prompt, which should be triaged before calling the whole answer-quality gate clean.

Rollback notes:
- If the D fix needs backing out, revert only the D-related prompt/parser/answer/test hunks listed above. No data-store rollback is involved.

## Commit readiness
Needs human review first

## Suggested next step
Recommended next lane: `05 Backend / RAG Integration`

Exact Lane 05 revision prompt if the adjacent smoke issue blocks commit:

```text
Fix the practice-plan specificity regression found during D-chord QA.

Prompt: Build a 7-day practice plan for blocking.

Current behavior: returns a 25-minute routine, not a 7-day plan.

Goal: Return a teacher-first 7-day blocking plan with daily focus, short drills, measurable goals, no fretboard payload unless explicitly requested, no source cards unless needed as secondary evidence, no weak-source warning, no raw SGF fragments, and no [object Object].

Do not modify Chroma, embeddings, deployment, DNS, scraping, corpus-private, corpus-v2, or UI files. Add focused tests in the existing answer/API/eval coverage. Run the focused tests plus the existing 15-prompt smoke if available, then write a handoff.
```

Exact 01 Repo Steward prompt if human decides the D fix can be split now:

```text
Review and hunk-stage only the D chord across-fretboard answer fix.

Use the QA handoff docs/handoffs/task-completions/qa-d-chord-across-fretboard-answer-fix.md.

Candidate files:
- steel_guitar_rag/fretboard_examples.py
- steel_guitar_rag/curated_answers.py
- tests/test_fretboard_examples.py
- tests/test_api_search.py
- docs/handoffs/task-completions/d-chord-across-fretboard-answer-fix.md
- docs/handoffs/task-completions/qa-d-chord-across-fretboard-answer-fix.md

Do not stage unrelated UI, corpus, source-inbox, deploy, design asset, provenance, generated report, or parked worktree changes. Note that optional 15-prompt smoke found an adjacent 7-day practice-plan specificity issue, so decide whether to commit D fix now or wait for Lane 05 follow-up.
```
