# Teaching Intent Specificity Revision

## Task Summary

Lane: 05 Backend / RAG Integration

Requested: revise the uncommitted teaching-intent specificity slice after Lane 15 QA failed it. The original target prompts worked, but QA found route-precedence regressions in nearby lick/song-learning behavior.

Completed:
- Read the failed Lane 15 QA handoff, Repo Steward blocker handoff, and Lane 12 protected-preview blocker handoff.
- Identified the exact route-precedence failure: generic lick routing ran before more-specific original-style/copyright-safe song-learning routing.
- Revised the route precedence so original-style lick prompts yield to the existing song-learning/copyright-safe answer before generic lick handling.
- Restored the legacy `grip 4-5-6` phrase in the generic E9 lick answer.
- Added a regression test proving original-style lick routing beats generic lick routing.
- Preserved the implicit teaching prompt fixes from the earlier slice.

Intentionally not changed:
- No curated_guidance public exposure.
- No curated_guidance answer-body usage or source-card wiring.
- No protected-preview restart.
- No staging or commit.
- No UI, Chroma, embeddings, SGF scraper, deployment, DNS, auth policy, or corpus-private changes.

## Why Lane 15 Failed The Previous Slice

Lane 15 marked the previous slice as failed even though the 12 smoke prompts passed.

Blocking QA failures:

1. `tests/test_api_search.py::test_default_teaching_mode_prompts_do_not_fall_into_forum_fragments`
   - Prompt: `Give me an example of just one steel guitar lick`
   - Failure: the answer no longer included the expected exact phrase `grip 4-5-6`.

2. `tests/test_api_search.py::test_song_tab_policy_allows_teaching_without_full_copyrighted_tab`
   - Prompt: `Can you write me an original E9 lick in the style of a slow country ballad?`
   - Failure: the widened generic country lick route intercepted the more-specific original-style/copyright-safe route.

## Exact Root Cause

The earlier implementation widened `_mentions_lick_request(...)` correctly for user-smoke prompts, but it also changed route precedence:

- `/api/answer` calls `intent_mode_curated_answer(...)` before the full source-aware `lookup_curated_answer(...)` path.
- The generic lick branch in `intent_mode_curated_answer(...)` matched `original E9 lick in the style of a slow country ballad`.
- That prevented the existing `mentions_original_style_lick(...)` song-learning answer from running.

The fix was not to narrow all implicit lick routing again; the fix was to make more-specific original-style lick handling win before generic lick handling.

## What Changed

Implementation:
- Added `original_style_lick_curated_answer(...)` helper so the existing original-style answer has one source of truth.
- `lookup_curated_answer(...)` now checks `original_style_lick_curated_answer(...)` before `intent_mode_curated_answer(...)`.
- The generic `teacher_first_general_lick_answer(...)` returns `None` for original-style prompts.
- The later `mode == "lick_request"` fallback also skips original-style prompts.
- The generic E9 lick wording now says `grip 4-5-6`, satisfying the existing regression.

Tests:
- Added `test_original_style_lick_route_precedes_generic_lick_route`.
- Kept the earlier smoke regression for all listed teaching prompts and JavaScript off-domain guardrail.

## Prompt-By-Prompt Before/After

| Prompt | Before revision | After revision |
| --- | --- | --- |
| `Teach me some B&C pedal skills.` | Fixed by previous slice; direct E9 B+C practice answer. | Still direct E9 B+C practice answer with strings 3-4-5, pedal mechanics, phrase steps, and practice instruction. |
| `Show me another lick.` | Fixed by previous slice. | Still default E9 lick in G with no previous-context requirement. |
| `Show me a lick in C minor.` | Fixed by previous slice. | Still C minor E9 lick using fret 6, strings 3-4-5, B+C. |
| `Show me a lick.` | Fixed by previous slice. | Still default original E9 lick in G. |
| `Show me a steel guitar lick.` | Already decent; previous slice changed wording. | Still direct E9 lick, now includes `grip 4-5-6`. |
| `Show me a country lick in G.` | Fixed by previous slice. | Still direct country E9 lick in G; no weak-match wording. |
| `Teach me a lick in D-sharp.` | Fixed by previous slice. | Still treats D-sharp as Eb/D# and gives fret 11 E9 lick. |
| `Teach me about turnarounds.` | Fixed by previous slice. | Still steel-oriented turnaround explanation and G-C-D-G example. |
| `What is a turnaround?` | Fixed by previous slice. | Still steel/music teaching answer with E9 examples. |
| `Teach me about minor chords.` | Fixed by previous slice. | Still minor-chord teaching answer with C-Eb-G and B+C position. |
| `Teach me about major chords.` | Fixed by previous slice. | Still major-chord teaching answer with G-B-D and E9 position families. |
| `Give me a JavaScript sorting algorithm.` | Off-domain guardrail passed. | Still off-domain guarded, source-free, warning-free, no fretboard. |
| `Give me an example of just one steel guitar lick` | Failed QA because expected `grip 4-5-6` phrase was missing. | Passes; generic E9 lick includes `grip 4-5-6`. |
| `Can you write me an original E9 lick in the style of a slow country ballad?` | Failed QA because generic country lick intercepted song-learning route. | Passes; original-style/copyright-safe route returns `original slow-country E9 exercise` and `Original mini-exercise in G`. |

## Tests And Checks

Commands run:

```bash
git status --short
```

Result:
- Ran. Broad dirty worktree remains; scoped files are identifiable.

```bash
git diff --check
```

Result:
- Passed.

```bash
.venv/bin/python -m pytest tests/test_api_search.py::test_default_teaching_mode_prompts_do_not_fall_into_forum_fragments tests/test_api_search.py::test_song_tab_policy_allows_teaching_without_full_copyrighted_tab tests/test_api_search.py::test_original_style_lick_route_precedes_generic_lick_route -q
```

Result:
- `3 passed`

```bash
.venv/bin/python -m pytest tests/test_api_search.py -k 'lick or turnaround or chord or curated_guidance' -q
```

Result:
- `39 passed, 207 deselected`

```bash
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_api_contract.py -q
```

Result:
- `81 passed`

```bash
.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q
```

Result:
- `64 passed`

```bash
.venv/bin/python -m py_compile steel_guitar_rag/api.py steel_guitar_rag/answer_intent_classifier.py steel_guitar_rag/curated_answers.py steel_guitar_rag/curated_guidance_retriever.py
```

Result:
- Passed.

Full pytest:
- Not run. The task requested focused suites; known unrelated static/UI full-suite caveats remain from earlier handoffs.

## Integration Notes

- The original-style answer remains source-aware through `lookup_curated_answer(...)`; it is no longer swallowed by source-free generic intent-mode handling.
- The user-smoke teaching prompts remain deterministic/source-free.
- Curated guidance remains unavailable to public/beta/unauthenticated users by this slice; no private-review content is surfaced.
- Missing-context prompts such as `this lick` remain excluded from the generic lick route.

## Remaining Risks

Risk level: low-medium.

Why:
- Shared answer routing is touched, but route precedence is now narrower and covered by the specific QA blockers.
- The broader worktree remains dirty, so exact-path staging is still required.

Rollback:
- Revert scoped changes in `steel_guitar_rag/answer_intent_classifier.py`, `steel_guitar_rag/curated_answers.py`, `tests/test_answer_intent_classifier.py`, and `tests/test_api_search.py`.
- No UI, auth, deployment, Chroma, embeddings, scraper, or private data rollback is needed.

## Human Decision Needed

No for this revision implementation.

Yes before:
- protected-preview restart,
- curated_guidance public/beta exposure,
- source-card/answer-body usage for curated_guidance,
- broad answer-routing refactors.

## Safe-To-Stage Exact File List

For this revised slice, pending Lane 15 approval:
- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/curated_answers.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-14-05-teaching-intent-specificity-fixes.md`
- `docs/handoffs/task-completions/2026-06-14-05-teaching-intent-specificity-revision.md`
- `docs/codex-queue/next-lane-15-teaching-intent-specificity-revision-qa.md`

Do not use `git add .`.

## Files That Must Not Be Staged

Do not stage:
- `docs/handoffs/task-completions/2026-06-14-15-teaching-intent-specificity-qa.md` unless Lane 15 explicitly wants to commit its failed QA handoff.
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

## Commit Readiness

Needs human review first.

Reason:
- The QA-blocking regressions are fixed locally and checks are green.
- Lane 15 needs to re-review and supersede the failed QA handoff before Repo Steward can exact-path stage.

## Recommended Next Lane

Recommended lane: 15 QA / Answer Eval.

Suggested next prompt:

```text
Lane 15: QA the revised teaching-intent specificity slice using docs/handoffs/task-completions/2026-06-14-05-teaching-intent-specificity-revision.md. Confirm the original 12 smoke prompts still pass, `Give me an example of just one steel guitar lick` includes `grip 4-5-6`, and `Can you write me an original E9 lick in the style of a slow country ballad?` uses the original-style/copyright-safe route rather than the generic country lick route. Run the focused tests listed in the handoff, verify curated_guidance/private-review content is not exposed, and if green, write a superseding QA handoff with exact safe-to-stage files for Repo Steward.
```
