# QA: Chord/Fretboard Routing Smoke Readiness Fix

## Task summary
- What was requested: QA the chord/fretboard routing smoke-readiness fix before user smoke testing, without modifying implementation files, staging, or committing.
- What was completed: Read the requested repo guidance, answer contract/eval docs, expected behaviors, integration status, protected-preview readiness handoff, Lane 05 fix handoff, current classifier/API/answer/fretboard files, and current tests; ran focused routing tests, classifier/eval/API suites, explicit 264-row classifier validation, full pytest, and a 15-prompt browser smoke against a current-worktree local loopback server.
- What was intentionally not changed: No implementation files, UI files, corpus/private/vector/source-inbox files, deployment/DNS/auth config, Chroma stores, embeddings, generated reports, staging, or commits were changed by this QA task.

## Pass/fail decision
**Safe to commit** for the chord/fretboard routing smoke-readiness slice, after Repo Steward hunk-level review.

All requested regression prompts passed in local browser smoke against the current worktree:
- `How do I play a G chord on the E9?`
- `Where do I play a G chord on the E9?`
- `Where the the G chords?`
- `Show me the fretboard`
- `How do I play an A chord?`
- `How do I play a D chord?`
- `How do I play a D chord across the fretboard of the E9?`
- `What is the capital of France?`

The smoke run was browser-based, not API-only fallback. It used the repo-supported local loopback server at `http://127.0.0.1:8781`, not the authenticated protected-preview hostname. Because no deploy/restart was performed, broad user smoke should wait until Repo Steward commits the slice and Lane 12/protected-preview verification proves the protected preview is running that committed code.

## Test commands and results
Repo state and whitespace:

```bash
git branch --show-current
git rev-parse --short HEAD
git status --short
git diff --check
```

Results:
- Branch: `feature/answer-api`
- HEAD: `e60324f`
- Worktree: broad pre-existing dirty/untracked files remain.
- `git diff --check`: passed.

Focused chord/fretboard routing tests:

```bash
.venv/bin/python -m pytest \
  tests/test_fretboard_examples.py::test_smoke_ready_chord_position_prompt_variants_are_supported \
  tests/test_fretboard_examples.py::test_show_me_the_fretboard_returns_default_e9_reference_payload \
  tests/test_api_search.py::test_smoke_ready_chord_fretboard_prompts_route_deterministically \
  tests/test_api_search.py::test_show_me_the_fretboard_returns_default_visual_without_retrieval_fragments
```

Result: `4 passed`.

Requested focused suites:

```bash
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
```

Results:
- `tests/test_answer_intent_classifier.py`: `62 passed`.
- `tests/test_answer_eval.py`: `9 passed`.
- `tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py`: `238 passed`.

264-row classifier validation:

```json
{
  "contract_key_mismatches": 0,
  "impossible_or_large_output_misclassified_as_steel": 0,
  "impossible_or_large_output_retrieval_allowed": 0,
  "invalid_domain_enum": 0,
  "invalid_intent_enum": 0,
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

Full suite:

```bash
.venv/bin/python -m pytest
```

Result: `668 passed`.

## Browser smoke setup
Local server command:

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
- `GET http://127.0.0.1:8781/`: `200 OK`.
- `GET http://127.0.0.1:8781/api/answer`: `405 Method Not Allowed`, expected for GET.

Browser URL:
- `http://127.0.0.1:8781/ui/steel-guitar-rag-mock.html?access=beta_user&v=qa-chord-fretboard-routing-smoke-readiness-fix`

Smoke artifacts:
- `/tmp/pocketsteel-chord-fretboard-routing-smoke/browser-smoke-results.json`
- `/tmp/pocketsteel-chord-fretboard-routing-smoke/browser-smoke-results-adjusted.json`
- `/tmp/pocketsteel-chord-fretboard-routing-smoke/screenshots/g-chord-on-e9.png`
- `/tmp/pocketsteel-chord-fretboard-routing-smoke/screenshots/show-me-the-fretboard.png`
- `/tmp/pocketsteel-chord-fretboard-routing-smoke/screenshots/d-chord-across-e9.png`

The local smoke server was stopped after testing.

## 15-prompt smoke result
Adjusted primary-answer result: `15 passed / 0 failed`.

Note: the first automated pass reported `14 passed / 1 failed` because the raw-fragment detector scanned the whole rendered page and found source-card text on the `1-4-5-1 turnaround` source-backed answer. The actual primary answer was teacher-first and clean. I reclassified raw-fragment failure against the primary answer text, matching the requested criterion: “raw SGF/forum/source fragment as primary answer.”

| # | Prompt | Result | Sources | Fretboard | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | `How do I play a G chord on the E9?` | Pass | Suppressed | Shown | G major answer: 3rd fret open, 6th fret A+F, 10th fret A+B. |
| 2 | `Where do I play a G chord on the E9?` | Pass | Suppressed | Shown | Same deterministic G route. |
| 3 | `Where the the G chords?` | Pass | Suppressed | Shown | Typo phrase understood as G chord position request. |
| 4 | `Show me the fretboard` | Pass | Suppressed | Shown | Default starter standard E9/G major reference view. |
| 5 | `How do I play an A chord?` | Pass | Suppressed | Shown | A major: 5th fret open, 8th fret A+F, 12th fret A+B. |
| 6 | `How do I play a D chord?` | Pass | Suppressed | Shown | D major: 10th fret open, 13th fret A+F, 17th fret A+B. |
| 7 | `How do I play a D chord across the fretboard of the E9?` | Pass | Suppressed | Shown | D major plus across-fretboard alternates including 5th fret A+B and 3rd fret E-lower. |
| 8 | `What is the capital of France?` | Pass | Suppressed | Suppressed | Retrieval-gated off-domain guardrail. |
| 9 | `Write me a Python script to scrape Instagram.` | Pass | Suppressed | Suppressed | Unsafe/off-domain guardrail. |
| 10 | `What are common uses for the E9 9th string?` | Pass | Shown | Suppressed | Source-backed steel answer; evidence secondary. |
| 11 | `Explain B+C pedals.` | Pass | Shown | Suppressed | Source-backed/teacher-first B+C answer; no fretboard. |
| 12 | `How do players diagnose hum that changes when touching the changer?` | Pass | Shown | Suppressed | Diagnostic answer; no fretboard. |
| 13 | `What are common Fender Steel King settings?` | Pass | Shown | Suppressed | Gear answer; no fretboard. |
| 14 | `How do I play a 1-4-5-1 turnaround?` | Pass | Shown | Suppressed | Teacher-first progression answer; source cards secondary. |
| 15 | `What’s it mean for a song to be a swing or a waltz?` | Pass | Shown | Suppressed | Plain teaching answer; no fretboard. |

Across all 15 prompts:
- `[object Object]`: not observed.
- Weak-source warning as primary answer: not observed.
- Raw SGF/forum/source fragment as primary answer: not observed.
- Non-position steel questions: did not show fretboard.
- Position/chord-location/default-fretboard questions: showed fretboard.
- Deterministic chord/fretboard prompts: top-level sources suppressed.
- Source-backed prompts: source cards appeared as secondary evidence.

## Individual routing failure verification
1. `How do I play a G chord on the E9?`
   - Fixed. Teacher-first G major answer with fretboard.
   - Sources suppressed.
   - No raw fragments, weak warning, or `[object Object]`.

2. `Where do I play a G chord on the E9?`
   - Fixed. Same deterministic G major route and fretboard.

3. `Where the the G chords?`
   - Fixed. Reasonably understood as G chord position request.

4. `Show me the fretboard`
   - Fixed. Returns starter standard E9/G-major reference view with fretboard.
   - No retrieval/source fallback.

5. `How do I play an A chord?`
   - Preserved. Teacher-first A major answer with fretboard.

6. `How do I play a D chord?`
   - Preserved. Teacher-first D major answer with fretboard.

7. `How do I play a D chord across the fretboard of the E9?`
   - Preserved. Teacher-first D answer with starter positions and across-fretboard alternates; fretboard shown.

8. `What is the capital of France?`
   - Preserved. Retrieval gating blocks it; no sources or fretboard.

## Files changed
Changed by this QA task:
- `docs/handoffs/task-completions/qa-chord-fretboard-routing-smoke-readiness-fix.md`

Generated artifacts:
- `/tmp/pocketsteel-chord-fretboard-routing-smoke/browser-smoke-results.json`
- `/tmp/pocketsteel-chord-fretboard-routing-smoke/browser-smoke-results-adjusted.json`
- `/tmp/pocketsteel-chord-fretboard-routing-smoke/screenshots/g-chord-on-e9.png`
- `/tmp/pocketsteel-chord-fretboard-routing-smoke/screenshots/show-me-the-fretboard.png`
- `/tmp/pocketsteel-chord-fretboard-routing-smoke/screenshots/d-chord-across-e9.png`

Implementation/test files inspected:
- `pocketsteel/answer_intent_classifier.py`
- `pocketsteel/api.py`
- `pocketsteel/curated_answers.py`
- `pocketsteel/fretboard_examples.py`
- `pocketsteel/answering.py`
- `pocketsteel/answer_contracts.py`
- `tests/test_api_search.py`
- answer-eval tests and question bank docs

## Exact files approved for commit
Approved for this chord/fretboard routing smoke-readiness slice only:
- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/chord-fretboard-routing-smoke-readiness-fix.md`
- `docs/handoffs/task-completions/qa-chord-fretboard-routing-smoke-readiness-fix.md`

## Hunks needing careful staging
- `pocketsteel/fretboard_examples.py`
  - parser patterns for `where do I play`, `on the E9`, and `Where the the <root> chords`
  - default payload route for `Show me the fretboard`
- `pocketsteel/curated_answers.py`
  - source-free default teacher-first answer for `Show me the fretboard`
- `tests/test_fretboard_examples.py`
  - smoke-ready prompt variant payload tests
  - default E9 reference payload test
- `tests/test_api_search.py`
  - API-level deterministic routing tests for G/A/D/default-fretboard prompts
  - source-free/fretboard-backed assertions for deterministic prompts

## Files that should remain parked
Do not stage these for this slice unless separately approved:
- `pocketsteel/api.py` version endpoint work from another lane.
- UI files currently dirty in the shared worktree, including `ui/pedal-steel-fretboard.js`, `ui/steel-guitar-rag-mock.html`, and `ui/steel-guitar-rag-landing.html`.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated reports/data.
- `source-inbox/`, `source-inbox/provenance.json`, provenance/legal/source-policy artifacts.
- Deployment/DNS/Cloudflare/auth/security files and secrets.
- Unrelated root RAG/build scripts and parked dirty files from other lanes.

## Integration notes
- This QA used a local current-worktree browser smoke, not the authenticated protected-preview hostname.
- The protected preview should still be restarted/version-verified after this slice is committed before inviting user smoke.
- `integration-status.md` should be refreshed after Repo Steward commit and protected-preview verification.
- No public `/api/answer` response shape change was observed in tests.
- Retrieval gating remains intact for off-domain and unsafe/impossible prompts.
- The local smoke server reads configured vector stores for source-backed prompts; it did not modify Chroma, embeddings, app config, DNS, or deployment state.

## Risk assessment
Risk: low to medium.

Why:
- Runtime behavior is a narrow deterministic parser/default-route fix and all requested tests plus full pytest passed.
- Browser smoke passed the current 15-prompt matrix.
- Git hygiene risk remains medium because the worktree is broadly dirty and shared files contain unrelated lane work.

Rollback notes:
- Remove the parser/default-fretboard route hunks and related tests listed above. No data-store rollback is involved.

## Commit readiness
Safe to commit

## User smoke readiness
Current-worktree QA is clean for the requested smoke-readiness matrix.

User smoke testing is allowed only after:
1. Repo Steward hunk-stages and commits the approved slice.
2. Protected preview is restarted or otherwise proven to be running the committed fix.
3. `/api/version` or equivalent protected-preview verification confirms the deployed/runtime SHA.

Until those integration steps happen, external user smoke remains blocked by runtime/version readiness, not by this QA result.

## Suggested next step
Recommended next lane: `01 Repo Steward`

Exact prompt:

```text
LANE: 01 Repo Steward
REASONING: MEDIUM
Branch: feature/answer-api

Hunk-stage and commit only the chord/fretboard routing smoke-readiness fix approved by QA.

Use:
- docs/handoffs/task-completions/chord-fretboard-routing-smoke-readiness-fix.md
- docs/handoffs/task-completions/qa-chord-fretboard-routing-smoke-readiness-fix.md

Approved files:
- pocketsteel/fretboard_examples.py
- pocketsteel/curated_answers.py
- tests/test_fretboard_examples.py
- tests/test_api_search.py
- docs/handoffs/task-completions/chord-fretboard-routing-smoke-readiness-fix.md
- docs/handoffs/task-completions/qa-chord-fretboard-routing-smoke-readiness-fix.md

Carefully hunk-stage only:
- parser/default-fretboard route hunks for G-on-E9, where-do-I-play, typo G chords, and Show me the fretboard
- associated deterministic answer block and focused tests

Do not stage pocketsteel/api.py version endpoint work, UI files, corpus/private/vector/source-inbox/provenance/legal/deploy/design assets, generated reports, or unrelated dirty files.

After commit, request Lane 12 protected-preview restart/version verification before outside user smoke.
```

If blocked later in protected preview, recommended Lane 05 revision prompt:

```text
LANE: 05 Backend / RAG Integration
REASONING: HIGH

Protected-preview smoke still fails chord/fretboard routing despite local QA passing.

Compare the protected-preview runtime SHA/version and current worktree behavior for:
- How do I play a G chord on the E9?
- Where do I play a G chord on the E9?
- Where the the G chords?
- Show me the fretboard

Expected:
- deterministic teacher-first answer
- fretboard payload for chord/default-fretboard prompts
- sources []
- warnings []
- no raw source fragments
- no [object Object]

Do not touch deployment, DNS, Chroma, embeddings, scraping, corpus-private, corpus-v2, source-inbox, UI, or unrelated answer behavior. Add focused tests only if the failure is a real backend route gap rather than stale runtime.
```
