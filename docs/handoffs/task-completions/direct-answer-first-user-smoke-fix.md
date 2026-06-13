# Direct Answer First User Smoke Fix

## Task Summary

Requested: handle an autopilot user smoke bug where the app returned SGF/forum fragments as the primary answer instead of directly answering the user’s actual question.

Completed:

- Added direct-answer-first deterministic handling for:
  - DIY feasibility / practical yes-no prompts.
  - Rooted dominant-7 chord questions such as `G dom 7` and `G7`.
  - Sus chord usage questions.
  - Rooted sus chord questions with cleaner wording.
- Added explicit answer-contract categories for the new direct-answer-first modes.
- Added focused API regressions for the observed failures.
- Ran focused and broad backend/eval tests.
- Ran protected-preview browser smoke against the requested root URL and recorded that the live preview is still serving old committed behavior.
- Ran API fallback against the patched working tree and verified the target prompts pass there.

Intentionally not changed:

- No UI files.
- No `/api/answer` schema changes.
- No auth, deployment, DNS, corpus, Chroma/vector store, embeddings, scraping, source-inbox, private source data, or visual assets.
- No commit.

## Root Cause

The existing answer pipeline already had retrieval gating and several deterministic answer routes, but these prompt shapes were not caught before retrieval/fallback:

- “Can I make a pedal steel guitar out of a box of cereal?”
- “How do I play a G dom 7?”
- “When would I ever play a sus chord?”

When the deterministic route missed, the answer provider could turn SGF snippets into the primary answer. The final source-fragment gate could reject some bad text, but it did not yet replace these specific question types with a direct practical answer.

## Files Changed

- `pocketsteel/basic_chord_answers.py`
- `pocketsteel/curated_answers.py`
- `pocketsteel/answer_contracts.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/direct-answer-first-user-smoke-fix.md`

No files were deleted.

## Categories Added / Fixed

- `direct_yes_no_practical`
- `chord_quality_theory`
- `unsupported_exact_mapping`
- `forum_context_secondary`
- `when_to_use_musical_context`
- `diy_feasibility_question` behavior is implemented under `direct_yes_no_practical`.

## Behavior Before / After

### Cereal Box Pedal Steel

Prompt:

`Can I make a pedal steel guitar out of a box of cereal?`

Before:

- Protected-preview browser returned SGF fragments about fabricated parts, buying a pedal steel, and inherited pedal steels.

After in patched working tree:

- First sentence: `No, not as a real functional pedal steel guitar.`
- Explains rigid body, changer, roller/nut system, strings under tension, pedals, rods, levers, and tuning hardware.
- `sources: []`
- no fretboard
- no weak-source warnings

### G Dominant 7

Prompts:

- `How do I play a G dom 7?`
- `How do I play a G7?`
- `What is a G dominant 7?`

Before:

- Could fall to weak source fallback or unrelated SGF fragments.

After in patched working tree:

- First sentence: `G7, or G dominant 7, is G-B-D-F: root, major 3rd, perfect 5th, and flat 7th.`
- Explains thinking G major first, then adding or implying F.
- `sources: []`
- no fretboard because exact dominant-7 position mapping is not claimed here.

### Sus Chord Usage

Prompts:

- `When would I ever play a sus chord?`
- `When do I use a sus chord?`

Before:

- Could fall to SGF fragments about bars, pedals, and unrelated forum chatter.

After in patched working tree:

- First sentence: `Use a sus chord when you want tension that wants to resolve.`
- Explains sus4 replacing the 3rd with the 4th.
- Gives steel/music use cases: held chord, intro ending, gospel-style lift, country phrase.
- `sources: []`
- no fretboard.

### Rooted Sus Chord

Prompt:

`How do I play a G sus chord?`

Before:

- Closer than the others, but included awkward internal-ish wording about deterministic map support.

After in patched working tree:

- First sentence: `Gsus usually means Gsus4. Gsus4 is a G suspended chord (G sus4): G-C-D, built from root, 4th, and perfect 5th.`
- Explains there is no B, so it is neither plain major nor minor until it resolves.
- States exact E9 sus-position mapping is still limited without SGF fragments.

## Tests Added / Updated

Added focused regressions in `tests/test_api_search.py`:

- `test_direct_yes_no_practical_answers_start_directly_without_sgf_fragments`
- `test_rooted_dominant_seventh_answers_are_direct_and_source_free`
- `test_suspended_usage_answers_directly_without_fretboard_or_sources`
- `test_rooted_suspended_answers_are_clean_direct_theory`

## Tests And Checks

Commands run:

```bash
git status --short
git diff --check
.venv/bin/python -m pytest tests/test_api_search.py -k "direct_yes_no_practical or dominant_seventh_answers or suspended_usage or rooted_suspended or rootless_chord_quality or suspended_chord_punctuation or major_seventh or chord_change or basic_chord_definition or smoke_ready_chord_fretboard"
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_answer_eval.py tests/test_api_contract.py tests/test_api_search.py tests/test_full_answer_quality_eval.py
.venv/bin/python -m pytest
```

Results:

- `git diff --check`: passed.
- Focused direct-answer-first tests: `10 passed`.
- Required backend/eval suite: `334 passed`.
- Full pytest: `645 passed, 2 failed`.

Full-suite failures are unrelated static/UI blockers:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

These failures pre-existed this backend answer-composition patch and are not in the answer-routing path.

## Smoke Target

- Target type: protected-preview root
- Result type: browser smoke failed on stale live preview; API fallback against patched working tree passed
- Exact browser URL tested: `https://app.steelguitarrag.com/`
- Cache-busted URL tested: not applicable; root URL redirects to `/ui/steel-guitar-rag-mock.html`
- Exact URL the user should use: not ready yet; protected preview needs a committed patch and restart first
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded / existing browser session was able to load the protected preview
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: patched working tree after this task
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `git_sha=28ae8f4`, `git_branch=feature/answer-api`, `retrieval_mode=hybrid_private_first`, `auth_provider=cloudflare_access`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes; returned `302 Found`
- Whether app root `/` is expected to work: yes; it redirects to the UI path
- Whether `/ui/steel-guitar-rag-mock.html` works: yes, browser loaded it
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Lane 12 / QA after commit and restart, then the user
- Do not test these URLs: do not treat API fallback as protected-preview browser proof
- Known caveats: protected preview is serving committed `28ae8f4`; this patch is uncommitted, so the browser still shows the old bad cereal-box answer

## Browser Smoke Result

Protected-preview browser smoke against `https://app.steelguitarrag.com/`:

| Prompt | Result | Answer category | First sentence / direct answer | Source fragments primary? | Source cards appropriate? | Fretboard appropriate? |
| --- | --- | --- | --- | --- | --- | --- |
| `Can I make a pedal steel guitar out of a box of cereal?` | FAIL on live preview | expected `direct_yes_no_practical` | Live preview started with SGF fragment: `I can tell you though that I have fabricated...` | yes | no | no fretboard expected |

I stopped protected-preview UI smoke after this first failure because it proved the live server has not been updated with the patch. Continuing the browser prompts would retest stale code rather than this fix.

## API Fallback Result

API fallback, not browser smoke. In-process `/api/answer` against the patched working tree:

| Prompt | Result | Answer category | First sentence / direct answer | Source fragments primary? | Sources | Fretboard |
| --- | --- | --- | --- | --- | ---: | --- |
| `Can I make a pedal steel guitar out of a box of cereal?` | PASS | `direct_yes_no_practical` | `No, not as a real functional pedal steel guitar.` | no | 0 | no |
| `How do I play a G dom 7?` | PASS | `chord_quality_theory` | `G7, or G dominant 7, is G-B-D-F...` | no | 0 | no |
| `How do I play a G7?` | PASS | `chord_quality_theory` | `G7, or G dominant 7, is G-B-D-F...` | no | 0 | no |
| `When would I ever play a sus chord?` | PASS | `when_to_use_musical_context` | `Use a sus chord when you want tension that wants to resolve.` | no | 0 | no |
| `How do I play a G sus chord?` | PASS | `chord_quality_theory` | `Gsus usually means Gsus4...` | no | 0 | no |
| `What is a G chord?` | PASS | `chord_quality_theory` | `A G major chord is G-B-D...` | no | 0 | no |
| `How do I play a G chord on the E9?` | PASS | `copedent_fretboard` | `On standard E9, several useful G major starter positions are:` | no | 0 | yes |
| `What is the capital of France?` | PASS | `scope_guardrail` | `That request is outside Steel Guitar RAG’s scope...` | no | 0 | no |

## Commit / Autopilot Status

Commit hash: none.

I did not commit because autopilot stop conditions apply:

- Full pytest is still red due unrelated static/UI failures.
- The protected-preview browser smoke failed on stale live code.
- The worktree remains heavily dirty with unrelated parked files.

## User Smoke May Continue?

No. User smoke should wait until:

1. This backend patch is QA-reviewed if needed.
2. Repo Steward exact-hunk stages and commits only the scoped backend/test/handoff changes.
3. The protected-preview server is restarted from the committed HEAD.
4. Lane 12/QA verifies the root URL again.

## Remaining Caveats

- The patch is verified in-process, not in protected-preview browser runtime.
- Protected-preview runtime is currently serving `28ae8f4`, which does not include these uncommitted changes.
- Full pytest still has unrelated static/UI failures.
- The dirty worktree includes many unrelated parked files; exact-hunk staging is required.

## Risk Assessment

Risk: medium.

Why:

- The backend change is narrow and focused tests are green.
- The repo state is dirty and protected-preview has stale code, so commit/restart needs Repo Steward and Lane 12 discipline.

Rollback:

- Revert the exact hunks in `pocketsteel/basic_chord_answers.py`, `pocketsteel/curated_answers.py`, `pocketsteel/answer_contracts.py`, and `tests/test_api_search.py` if this slice needs to be parked.
- Do not use destructive git cleanup against unrelated dirty files.

## Commit Readiness

Not ready to commit under autopilot.

Reason: full pytest red due unrelated failures, protected-preview browser smoke failed on stale code, and the worktree is heavily dirty.

## Suggested Next Step

Recommended lane: `15 QA / Answer Eval`, then `01 Repo Steward`.

Exact next QA prompt:

```text
Lane 15 QA / Answer Eval

Review docs/handoffs/task-completions/direct-answer-first-user-smoke-fix.md and the diff for:
- pocketsteel/basic_chord_answers.py
- pocketsteel/curated_answers.py
- pocketsteel/answer_contracts.py
- tests/test_api_search.py

Verify the direct-answer-first behavior for:
- Can I make a pedal steel guitar out of a box of cereal?
- How do I play a G dom 7?
- How do I play a G7?
- When would I ever play a sus chord?
- How do I play a G sus chord?
- What is a G chord?
- How do I play a G chord on the E9?
- What is the capital of France?

Confirm source fragments are not the primary answer, source cards are suppressed for deterministic answers, and fretboard appears only for the E9 position prompt. If approved, authorize Repo Steward exact-hunk staging.
```

Exact next Repo Steward prompt after QA:

```text
Lane 01 Repo Steward

QA approved the direct-answer-first user smoke fix. Stage only the approved hunks in:
- pocketsteel/basic_chord_answers.py
- pocketsteel/curated_answers.py
- pocketsteel/answer_contracts.py
- tests/test_api_search.py
- docs/handoffs/task-completions/direct-answer-first-user-smoke-fix.md

Do not stage unrelated UI/static/corpus/source-inbox/deploy/design/private/generated files. Run focused backend tests and git diff --check on the staged diff. Commit only if the scoped staged diff is clean and unrelated failures remain parked.
```
