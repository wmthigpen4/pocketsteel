# Teaching Intent Specificity Revision QA

## Task Summary

Lane: 15 QA / Answer Eval

Requested: QA the revised Lane 05 teaching-intent specificity fix and verify it resolves the prior Lane 15 blockers while preserving the screenshot/user-smoke teaching prompt fixes.

Completed:
- Read `AGENTS.md` guidance from the active prompt context.
- Reviewed the revised Lane 05 handoff and the prior failed Lane 15 QA handoff.
- Reviewed the scoped routing and test changes in `pocketsteel/answer_intent_classifier.py`, `pocketsteel/curated_answers.py`, `tests/test_answer_intent_classifier.py`, and `tests/test_api_search.py`.
- Ran the requested focused checks.
- Re-ran the prior QA-blocking regression tests.
- Ran API-fallback smoke for all 12 requested prompts with answer snippets capped to 500 characters in this report.

Intentionally not changed:
- No implementation code.
- No tests or fixtures.
- No `/api/answer` runtime behavior.
- No UI, Chroma/vector stores, embeddings, SGF scraper, deployment, DNS, auth policy, `corpus-private/`, or generated/private corpus outputs.
- No staging or commit.

## Pass/Fail Decision

Pass.

The revised fix resolves the two prior Lane 15 blockers and preserves the original 12 smoke-prompt fixes. QA approves this revised teaching-intent specificity slice for exact-path Repo Steward staging.

## Prior QA Failures Resolved

Previously failing command:

```bash
.venv/bin/python -m pytest tests/test_api_search.py::test_default_teaching_mode_prompts_do_not_fall_into_forum_fragments tests/test_api_search.py::test_song_tab_policy_allows_teaching_without_full_copyrighted_tab -q
```

Current focused blocker check:

```bash
.venv/bin/python -m pytest tests/test_api_search.py::test_default_teaching_mode_prompts_do_not_fall_into_forum_fragments tests/test_api_search.py::test_song_tab_policy_allows_teaching_without_full_copyrighted_tab tests/test_api_search.py::test_original_style_lick_route_precedes_generic_lick_route -q
```

Result:
- Passed: `3 passed`.

Resolved findings:
- `Give me an example of just one steel guitar lick` now satisfies the existing `grip 4-5-6` regression.
- `Can you write me an original E9 lick in the style of a slow country ballad?` now uses the original-style/copyright-safe route and does not get swallowed by the generic country lick answer.

## Prompt-By-Prompt Result Table

Direct API-fallback smoke was run through `tests.test_api_search.answer_for_question(...)` with noisy practical source fixtures. This is API fallback, not browser smoke.

| # | Prompt | Result | Answer snippet / QA notes |
| --- | --- | --- | --- |
| 1 | `Teach me some B&C pedal skills.` | Pass | Starts: `On E9, B+C pedal work is a pedal-timing and melodic-position skill...` Includes standard 10-string E9, strings 3-4-5, B+C mechanics, phrase steps, and practice instruction. |
| 2 | `Show me another lick.` | Pass | Starts: `With no previous lick context available...` Includes fret 3, `grip 4-5-6`, A+B, and practice instruction. |
| 3 | `Show me a lick in C minor.` | Pass | Starts: `Here is a simple E9 lick in C minor.` Includes fret 6, strings 3-4-5, B+C, and C-Eb-G. |
| 4 | `Show me a lick.` | Pass | Starts: `Here is one simple original E9 lick in G.` Includes fret 3, `grip 4-5-6`, A+B, and blocking/practice instruction. |
| 5 | `Show me a steel guitar lick.` | Pass | Direct E9 lick in G with fret 3, `grip 4-5-6`, A+B, and no source fallback. |
| 6 | `Show me a country lick in G.` | Pass | Direct country E9 lick in G with fret 3, `grip 4-5-6`, A+B, and no `available matches are too thin` wording. |
| 7 | `Teach me a lick in D-sharp.` | Pass | Starts by treating D-sharp as Eb/D# for fretboard thinking. Includes fret 11, strings 4-5-6, and A+B. |
| 8 | `Teach me about turnarounds.` | Pass | Defines a turnaround and gives G-C-D-G E9 path with frets, grips, and practice instruction. |
| 9 | `What is a turnaround?` | Pass | Same direct music/steel teaching route; no generic retrieval failure. |
| 10 | `Teach me about minor chords.` | Pass | Explains root/minor 3rd/5th, C-Eb-G, fret 6, B+C, and practice steps. |
| 11 | `Teach me about major chords.` | Pass | Explains root/major 3rd/5th, G-B-D, and G major E9 position families. |
| 12 | `Give me a JavaScript sorting algorithm.` | Pass | Off-domain guarded: says the app is focused on pedal steel guitar. No sources, warnings, or fretboard. |

For prompts 1-11, QA observed:
- No `I need a more specific steel-guitar question`.
- No `available matches are too thin`.
- No generic retrieval-failure wording such as `retrieved material`, `source support was weak`, or `limited source support`.
- No source cards.
- No warnings.
- No fretboard payload for these non-position teaching prompts.
- Steel mechanics are present where expected: E9, frets, strings/grips, pedals/levers, phrase, blocking, or practice instruction.

## Off-Domain Guardrail Finding

Pass.

`Give me a JavaScript sorting algorithm.` remains off-domain guarded, source-free, warning-free, and without fretboard payload.

## Curated Guidance Leakage Finding

Pass.

The API-fallback smoke payloads did not expose:
- `private_review`
- `curated_guidance`
- `corpus-private`
- private-guidance labels
- private filenames or excerpts

No curated-guidance source cards or visible answer-body usage were added by this slice.

## Tests And Checks

Commands run:

```bash
git status --short
```

Result:
- Passed. Worktree is broadly dirty with many unrelated files; scoped files remain identifiable.

```bash
git diff --check
```

Result:
- Passed.

```bash
.venv/bin/python -m pytest tests/test_api_search.py -k 'lick or turnaround or chord or curated_guidance' -q
```

Result:
- Passed: `39 passed, 207 deselected`.

```bash
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_api_contract.py -q
```

Result:
- Passed: `81 passed`.

```bash
.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q
```

Result:
- Passed: `64 passed`.

```bash
.venv/bin/python -m py_compile pocketsteel/api.py pocketsteel/answer_intent_classifier.py pocketsteel/curated_answers.py pocketsteel/curated_guidance_retriever.py
```

Result:
- Passed.

```bash
.venv/bin/python -m pytest tests/test_api_search.py::test_default_teaching_mode_prompts_do_not_fall_into_forum_fragments tests/test_api_search.py::test_song_tab_policy_allows_teaching_without_full_copyrighted_tab tests/test_api_search.py::test_original_style_lick_route_precedes_generic_lick_route -q
```

Result:
- Passed: `3 passed`.

Optional API-fallback smoke:
- Ran all 12 requested prompts through `answer_for_question(...)`.
- Result: all passed the requested criteria.

Full pytest:
- Not run. The user requested focused suites; current blocker findings are resolved by focused tests. Existing broad dirty-worktree caveats should remain under Repo Steward control.

## Files Changed

Changed by this QA task:
- `docs/handoffs/task-completions/2026-06-14-15-teaching-intent-specificity-revision-qa.md`

Reviewed but not modified by this QA task:
- `pocketsteel/answer_intent_classifier.py`
- `pocketsteel/curated_answers.py`
- `pocketsteel/api.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `tests/test_answer_eval.py`
- `tests/test_full_answer_quality_eval.py`

Deleted:
- None

Generated artifacts:
- None

## Files Safe To Stage

QA approves exact-path staging for this revised slice:

- `pocketsteel/answer_intent_classifier.py`
- `pocketsteel/curated_answers.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-14-05-teaching-intent-specificity-fixes.md`
- `docs/handoffs/task-completions/2026-06-14-05-teaching-intent-specificity-revision.md`
- `docs/handoffs/task-completions/2026-06-14-15-teaching-intent-specificity-revision-qa.md`

Optional coordination file, if Repo Steward wants to include Lane 05's queued next-lane prompt with this slice:
- `docs/codex-queue/next-lane-15-teaching-intent-specificity-revision-qa.md`

Do not use `git add .`.

## Files That Must Not Be Staged

Do not stage:
- `docs/handoffs/task-completions/2026-06-14-15-teaching-intent-specificity-qa.md` unless Repo Steward explicitly wants to commit the superseded failed QA handoff.
- `docs/handoffs/task-completions/2026-06-14-12-teaching-intent-protected-preview-smoke.md` unless Lane 12 explicitly approves that blocker handoff.
- unrelated dirty/parked files in the broad worktree.
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- SGF scraper outputs
- `source-inbox/` raw data or provenance
- `.wrangler/`
- DNS/deployment secrets
- `public/`
- `ui/brand/`
- `Neon Sign/`
- generated/private reports or raw design assets.

## Risks

Risk level: low-medium.

Why:
- Shared answer routing is touched, but this revision preserves the new implicit teaching behavior while restoring the more specific original-style lick route.
- The worktree is broadly dirty, so exact-path staging is essential.

Rollback notes:
- Revert scoped changes in `pocketsteel/answer_intent_classifier.py`, `pocketsteel/curated_answers.py`, `tests/test_answer_intent_classifier.py`, and `tests/test_api_search.py`.
- No corpus, Chroma, UI, auth, deployment, scraper, or private-data rollback is involved.

## Human Decision Needed

No.

## Commit Readiness

Safe to commit with exact-path staging.

## Recommended Next Lane

Recommended lane: `01 Repo Steward`.

Suggested next prompt:

```text
Lane 01: Run ExactPathCommit for the teaching-intent specificity revision approved by docs/handoffs/task-completions/2026-06-14-15-teaching-intent-specificity-revision-qa.md. Stage only the approved exact paths/hunks, keep the superseded failed QA handoff and unrelated dirty files parked, run staged-diff checks, and commit the scoped revised teaching-intent specificity slice. Do not use git add . and do not stage corpus-private, corpus-v2, source-inbox, public, ui/brand, Neon Sign, deployment secrets, generated reports, or unrelated docs/corpus/runtime files.
```
