# QA: Teacher-First Answer Composer

Date: 2026-06-13 03:53 CT
Lane: 15 QA / Answer Eval
Branch: `feature/answer-api`

## Task Summary

Requested: QA the teacher-first answer composer backend slice and decide whether it is safe for Repo Steward hunk-staged commit.

Completed:

- Read the requested repo guidance, answer/eval/product policy docs, teacher-first handoff, current answer engine/composer files, curated answers, retrieval/API/source-card paths, fretboard trigger contract, API tests, and answer-eval tests.
- Verified focused teacher-first regression tests for:
  - `How do I play a G-minor chord?`
  - `How do I play a 1-4-5-1 turnaround?`
  - `What’s it mean for a song to be a swing or a waltz?`
- Verified the previous six-smoke prompts remain clean through tests and browser smoke.
- Verified retrieval gating, public API response shape, deterministic fretboard behavior, and source-card behavior remain intact.
- Ran browser UI smoke for all 15 requested prompts with screenshots.
- Ran 264-row classifier validation and full pytest.

Intentionally not changed:

- No implementation files were modified by QA.
- No UI files were modified by QA.
- No Chroma/vector stores, embeddings, corpus-private, corpus-v2, source-inbox raw/provenance data, scraping, deployment, DNS, secrets, public assets, design assets, staging, or commits.

## Decision

Pass.

QA approves the teacher-first answer composer slice for a narrow Repo Steward hunk-staged commit.

Commit readiness: Safe to commit.

This means safe only for the exact approved hunks listed below. The worktree remains broadly dirty, and several touched files contain unrelated parked changes from other lanes.

## Verification Summary

- Primary answers are synthesized teaching content, not source fragments.
- Source cards/source notes remain evidence below the answer where expected.
- `How do I play a G-minor chord?` gives a useful deterministic G minor answer and fretboard payload.
- `How do I play a 1-4-5-1 turnaround?` explains I-IV-V-I, gives a G-C-D-G example, and applies it to E9.
- `What’s it mean for a song to be a swing or a waltz?` explains meter/feel plainly and connects it to steel phrasing.
- Diminished chords, Fender Steel King settings, hum/changer, and B+C pedals still pass.
- G and C position prompts still give clear E9 positions and visible fretboard cards.
- Non-position prompts do not show visible fretboard cards.
- Position prompts can show visible fretboard cards.
- Off-domain/unsafe retrieval gating remains intact.
- Public `/api/answer` response shape remains covered by API contract/search tests.
- No UI files are approved for this slice.
- No `[object Object]` appeared.
- No weak-source warning appeared as the primary answer.
- No raw SGF/forum fragment appeared as the primary answer.

## Browser Smoke

Method: Browser UI smoke against the current-worktree loopback server.

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

Browser artifact:

- JSON: `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/teacher-first-browser-smoke.json`
- Screenshots: `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/`

Note: an initial browser pass was discarded because it captured loading/placeholder state before final answer/source rendering completed. The reported pass below is the rerun with explicit waits for loaded answer and source-card state.

Totals:

- Total: 15
- Pass: 15
- Fail: 0

| # | Prompt | Result | Sources | Fretboard | `[object Object]` | Weak warning | Raw fragment | Screenshot |
|---:|---|---|---|---|---|---|---|---|
| 1 | What are common uses for the E9 9th string? | PASS | shown | suppressed | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/01-what-are-common-uses-for-the-e9-9th-string.png` |
| 2 | Why would a player prefer a wound 6th string? | PASS | shown | suppressed | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/02-why-would-a-player-prefer-a-wound-6th-string.png` |
| 3 | What do players say about using the 6th string lower? | PASS | shown | suppressed | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/03-what-do-players-say-about-using-the-6th-string-lower.png` |
| 4 | How do players approach diminished chords on E9? | PASS | shown | suppressed | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/04-how-do-players-approach-diminished-chords-on-e9.png` |
| 5 | What are common Fender Steel King settings? | PASS | shown | suppressed | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/05-what-are-common-fender-steel-king-settings.png` |
| 6 | How do players diagnose hum that changes when touching the changer? | PASS | shown | suppressed | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/06-how-do-players-diagnose-hum-that-changes-when-touching-the-changer.png` |
| 7 | Where are my G chord positions? | PASS | suppressed | shown: `G MAJOR POSITIONS ON E9` | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/07-where-are-my-g-chord-positions.png` |
| 8 | Show me C positions on E9. | PASS | suppressed | shown: `C MAJOR POSITIONS ON E9` | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/08-show-me-c-positions-on-e9.png` |
| 9 | What is the capital of France? | PASS | suppressed | suppressed | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/09-what-is-the-capital-of-france.png` |
| 10 | Write me a Python script to scrape Instagram. | PASS | suppressed | suppressed | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/10-write-me-a-python-script-to-scrape-instagram.png` |
| 11 | Explain B+C pedals. | PASS | shown | suppressed | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/11-explain-b-c-pedals.png` |
| 12 | Build a 7-day practice plan for blocking. | PASS | suppressed | suppressed | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/12-build-a-7-day-practice-plan-for-blocking.png` |
| 13 | How do I play a G-minor chord? | PASS | suppressed | shown: `G MINOR POSITIONS ON E9` | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/13-how-do-i-play-a-g-minor-chord.png` |
| 14 | How do I play a 1-4-5-1 turnaround? | PASS | shown | suppressed | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/14-how-do-i-play-a-1-4-5-1-turnaround.png` |
| 15 | What’s it mean for a song to be a swing or a waltz? | PASS | shown | suppressed | no | no | no | `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/15-what-s-it-mean-for-a-song-to-be-a-swing-or-a-waltz.png` |

## Test Commands And Results

```bash
git status --short
```

Result: broad dirty worktree. Relevant teacher-first slice files are modified/untracked among many unrelated parked files.

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
.venv/bin/python -m pytest tests/test_fretboard_examples.py::test_hyphenated_minor_chord_questions_route_to_minor_positions tests/test_api_search.py::test_teacher_first_screenshot_prompt_regressions_are_synthesized
```

Result: `2 passed in 0.08s`.

```bash
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
```

Result: `234 passed in 0.81s`.

264-row classifier validation:

```text
rows: 264
contract_key_mismatches: 0
invalid_domain_enum: 0
invalid_shape_enum: 0
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

```bash
.venv/bin/python -m pytest
```

Result: `659 passed in 4.35s`.

## Remaining Answer-Quality Issues

None found in the requested tests or 15-prompt browser smoke.

Residual note: source cards for source-backed teacher-first answers can still contain raw-looking historical forum/tab excerpts in the source-card area. The answer body remained synthesized and clean, which matches the current policy that source cards are secondary evidence.

## Files Changed

Changed by Lane 05 teacher-first slice:

- `steel_guitar_rag/fretboard_examples.py`
- `steel_guitar_rag/curated_answers.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`

Created by Lane 05 teacher-first slice:

- `docs/handoffs/task-completions/teacher-first-answer-composer.md`

Created by this QA task:

- `docs/handoffs/task-completions/qa-teacher-first-answer-composer.md`

Deleted files: none.

Generated artifacts:

- `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/teacher-first-browser-smoke.json`
- `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/screenshots/*.png`

## Exact Files Approved For Commit

Approved only as narrowly hunk-staged changes:

- `steel_guitar_rag/fretboard_examples.py`
- `steel_guitar_rag/curated_answers.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/teacher-first-answer-composer.md`
- `docs/handoffs/task-completions/qa-teacher-first-answer-composer.md`

## Exact Hunks Needing Careful Staging

`steel_guitar_rag/fretboard_examples.py`:

- Stage only the hyphenated minor-chord parsing/routing support needed for `How do I play a G-minor chord?`.
- Do not stage unrelated fretboard engine/catalog/UI-support hunks from other lanes.

`steel_guitar_rag/curated_answers.py`:

- Stage only the `lookup_curated_answer(...)` calls for:
  - `teacher_first_turnaround_answer(...)`
  - `teacher_first_swing_waltz_answer(...)`
- Stage only the definitions of:
  - `teacher_first_turnaround_answer(...)`
  - `teacher_first_swing_waltz_answer(...)`
- Do not stage unrelated home-prompt, red-team, missing-context, broad intent-mode, or technique-coach hunks from other lanes unless Repo Steward separately confirms they are already part of a committed/approved slice.

`tests/test_fretboard_examples.py`:

- Stage only `test_hyphenated_minor_chord_questions_route_to_minor_positions`.

`tests/test_api_search.py`:

- Stage only `test_teacher_first_screenshot_prompt_regressions_are_synthesized`.
- Do not stage unrelated parked API/search test hunks.

The two handoff docs above can be staged as whole files.

## Files That Should Remain Parked

Do not stage for this teacher-first commit:

- `ui/pedal-steel-fretboard.js`
- `ui/steel-guitar-rag-landing.html`
- `ui/steel-guitar-rag-mock.html`
- `public/`
- `ui/brand/`
- `Neon Sign/`
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox` raw/provenance/generated files
- provenance/legal metadata dumps
- deployment/DNS/Cloudflare/`.wrangler` files
- generated reports
- `/tmp/steel_guitar_rag-teacher-first-browser-smoke-rerun/`
- unrelated docs, scripts, tests, API files, corpus tooling, and root RAG/build scripts
- `docs/handoffs/task-completions/integration-status.md` unless a separate docs-only coordination task explicitly approves it

## Integration Notes

- No public API response shape change.
- No classifier contract change.
- No retrieval-gating widening.
- No UI rendering code change.
- Deterministic G-minor visual answer suppresses source cards and shows a fretboard.
- Source-backed teacher-first answers keep source cards below the synthesized answer.

## Risk Assessment

Risk: medium.

Why:

- Test and browser smoke coverage is green.
- The implementation slice is conceptually narrow, but the relevant files are heavily overlapped with unrelated parked work. Commit safety depends on precise hunk staging.
- Source-backed prompts still rely on current retrieval results for source cards; this is expected, but source-card excerpts may look raw because they are evidence rather than the answer.

Rollback:

- Revert the narrowly staged teacher-first hunks and tests.
- No data/vector/UI/deployment rollback needed.

## Human Decision Needed

No for QA approval.

Yes for Repo Steward staging discipline: stage only the exact approved hunks because the worktree is broad and dirty.

## Commit Readiness

Safe to commit.

This means safe only for the exact approved teacher-first hunks above.

## Suggested Next Step

Lane 01 Repo Steward should hunk-stage the approved teacher-first composer slice, run the focused checks and broad answer/API/eval tests, then commit the narrow slice.

## Exact Next Prompt For 01 Repo Steward

```text
LANE: 01 Repo Steward
REASONING: MEDIUM
Branch: feature/answer-api

Read:
- AGENTS.md
- docs/handoffs/task-completions/teacher-first-answer-composer.md
- docs/handoffs/task-completions/qa-teacher-first-answer-composer.md

Do not deploy, change DNS, touch Chroma/vector stores, regenerate embeddings, run scraping, stage generated/private/corpus/source-inbox/provenance/design/deploy files, or use git add .

Hunk-stage only the teacher-first answer composer slice:
- steel_guitar_rag/fretboard_examples.py: hyphenated minor-chord parsing/routing support for "How do I play a G-minor chord?"
- steel_guitar_rag/curated_answers.py: lookup_curated_answer calls and definitions for teacher_first_turnaround_answer and teacher_first_swing_waltz_answer
- tests/test_fretboard_examples.py: test_hyphenated_minor_chord_questions_route_to_minor_positions
- tests/test_api_search.py: test_teacher_first_screenshot_prompt_regressions_are_synthesized
- docs/handoffs/task-completions/teacher-first-answer-composer.md
- docs/handoffs/task-completions/qa-teacher-first-answer-composer.md

Do not stage UI files, integration-status.md, source-inbox files, corpus/private/vector/generated data, deployment files, or unrelated docs/scripts/tests.

Run:
git diff --cached --check
.venv/bin/python -m pytest tests/test_fretboard_examples.py::test_hyphenated_minor_chord_questions_route_to_minor_positions tests/test_api_search.py::test_teacher_first_screenshot_prompt_regressions_are_synthesized
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_answer_eval.py
.venv/bin/python -m pytest tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py

If clean, commit with a narrow message such as:
backend: add teacher-first answer composer cases
```

## Exact Next Prompt For Lane 05 If Blocked

Not needed. QA found no blocker in this slice.
