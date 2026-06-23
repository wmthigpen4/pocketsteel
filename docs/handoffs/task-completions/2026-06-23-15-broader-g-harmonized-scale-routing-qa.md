# Broader G Harmonized-Scale Routing QA

Pass/warn/fail: **pass**

Branch: `feature/answer-api`

HEAD tested: `0a4e8a0`

Dirty implementation status: expected Lane 05 dirty work is present and scoped to the reported implementation/test files, plus the Lane 05 handoff.

## Task Summary

Lane 15 QA reviewed the uncommitted Lane 05 broader deterministic G harmonized-scale routing slice. The slice was tested through the in-process answer helper, focused backend/eval tests, and full `tests/test_api_search.py`.

Completed:
- Confirmed broad G major harmonized-scale prompts route to deterministic source-free fretboard answers.
- Confirmed G natural minor harmonized-scale prompts route to deterministic source-free fretboard answers.
- Confirmed F# diminished in G and A diminished in G minor route deterministically without full m7b5 overclaiming.
- Confirmed the existing 5&8 branch correction remains intact.
- Confirmed static harmonized-scale prompts remain tab-free.
- Confirmed movement/copyright/gear regression prompts remain behaviorally sane.

Intentionally not changed:
- No implementation files were modified by QA.
- No UI, deployment, auth, DNS, corpus, Chroma, embeddings, scraping, private data, or protected-preview runtime work was touched.
- No staging or commit was performed in Lane 15.

## Files Inspected

- `AGENTS.md`
- `agents.md`
- `README.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-05-broader-g-harmonized-scale-routing.md`
- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `tests/test_api_search.py`

Notes:
- `PLAN.md` and `plan.md` were requested but are not present in the repo root.

## Files Changed

- `docs/handoffs/task-completions/2026-06-23-15-broader-g-harmonized-scale-routing-qa.md`

No implementation files were changed by QA.

## Dirty Files Reviewed

Expected active Lane 05 slice:
- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-23-05-broader-g-harmonized-scale-routing.md`

Unrelated dirty and untracked files remain parked. They include existing docs/corpus metadata/source-inbox/design/static asset work shown by `git status --short`.

## Prompt Matrix Results

All prompts were tested through the same in-process answer helper used by the API search tests.

| # | Prompt | Result |
|---|---|---|
| 1 | `Show me a G harmonized scale.` | Pass: deterministic G major harmonized-scale answer, fretboard payload, no sources, no warnings, no `tab_example`. |
| 2 | `Show me G major harmonized scale on E9.` | Pass: same deterministic G major route. |
| 3 | `Show me a G major harmonized scale.` | Pass: same deterministic G major route. |
| 4 | `Show me a G harmonized scale on E9.` | Pass: same deterministic G major route. |
| 5 | `Show me a G harmonized scale on strings 5 and 8.` | Pass: preserves 5&8 branch behavior, no sources, no warnings, no `tab_example`. |
| 6 | `Show me a G natural minor harmonized scale.` | Pass: deterministic G natural minor route, fretboard payload, no sources, no warnings, no `tab_example`. |
| 7 | `Show me G natural minor harmonized scale on E9.` | Pass: same deterministic G natural minor route. |
| 8 | `Show me the F# diminished position in G.` | Pass: F#-A-C diminished triad, no false full F#m7b5 claim, fretboard payload, no sources, no warnings. |
| 9 | `Show me the A diminished position in G minor.` | Pass: A-C-Eb diminished triad, no false full Am7b5 claim, fretboard payload, no sources, no warnings. |
| 10 | `Show me a G major grip.` | Pass for regression scope: fretboard-first static grip answer, no `tab_example`, no warnings. Existing behavior still includes one source card; this is outside the new harmonized-scale source-free route. |
| 11 | `Show me a 4-5-6 grip.` | Pass for regression scope: fretboard-first static grip answer, no `tab_example`, no warnings. Existing behavior still includes one source card; this is outside the new harmonized-scale source-free route. |
| 12 | `Show me a G to C move.` | Pass: movement prompt still includes deterministic tab and fretboard payload. |
| 13 | `Give me a beginner lick in G.` | Pass: lick prompt still includes deterministic tab and fretboard payload. |
| 14 | `Give me the full tab for a modern copyrighted song.` | Pass: refuses/redirects safely, no fretboard, no `tab_example`, no sources, no warnings. |
| 15 | `What are good Fender Steel King settings?` | Pass: gear answer has no stale fretboard or `tab_example`. |

## Expected vs Actual Behavior

Broad G major routing: **passed**
- Prompts 1-4 return deterministic G major harmonized-scale guidance.
- Payload title: `G major harmonized scale on E9`
- Position count: 12
- Includes the 4-5-6 harmonized scale family and hidden 5&8 branch options.
- No sources, warnings, or `tab_example`.

G natural minor routing: **passed**
- Prompts 6-7 return deterministic G natural minor harmonized-scale guidance.
- Payload title: `G natural minor harmonized scale on E9`
- Position count: 8
- Includes G minor, A diminished, Bb major, C minor, D minor, Eb major, F major, and octave G minor.
- No sources, warnings, or `tab_example`.

Diminished-position routing: **passed**
- F# diminished in G returns the F#-A-C diminished triad and explicitly does not claim full F#m7b5.
- A diminished in G natural minor returns the A-C-Eb diminished triad and explicitly does not claim full Am7b5.
- Both routes return one deterministic fretboard position, no sources, no warnings, and no `tab_example`.

5&8 branch correction: **passed**
- A+F branch present:
  - `g-five-eight-af-branch-4-6`, fret 6, strings 5-8, pedals `["A"]`, levers `["F"]`, notes G/B.
  - `c-five-eight-af-branch-7-11`, fret 11, strings 5-8, pedals `["A"]`, levers `["F"]`, notes C/E.
- E-lower branch present:
  - `g-five-eight-e-lower-branch-4-8`, fret 8, strings 5-8, levers `["E"]`, notes G/B.
  - `c-five-eight-e-lower-branch-7-13`, fret 13, strings 5-8, levers `["E"]`, notes C/E.
- Corrected fret 13 E-lower C/E branch is present.
- Fret 11 is not used as the E-lower C/E branch.

Regression behavior: **passed**
- Static grip answers remain fretboard-first.
- Movement prompts still behave as movement prompts and may include deterministic tab.
- Copyright prompt still refuses/redirects safely.
- Gear prompt does not retain stale tab or fretboard payload.

## Tests And Checks Run

- `git status --short`
  - Result: existing dirty worktree confirmed; expected Lane 05 slice present; unrelated dirty work remains parked.
- `git branch --show-current`
  - Result: `feature/answer-api`
- `git rev-parse --short HEAD`
  - Result: `0a4e8a0`
- `git log -3 --oneline`
  - Result: `0a4e8a0`, `f15ef6c`, `3a07c8f`
- `git diff --name-only`
  - Result: expected Lane 05 files plus unrelated parked files.
- `git diff --cached --name-only`
  - Result: no staged files.
- `git diff --check`
  - Result: passed.
- `.venv/bin/python -m py_compile pocketsteel/fretboard_explorer.py pocketsteel/fretboard_examples.py pocketsteel/curated_answers.py pocketsteel/api.py`
  - Result: passed.
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q`
  - Result: `30 passed`.
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'harmonized or diminished or static_g or tab_example' -q`
  - Result: `19 passed, 254 deselected`.
- `.venv/bin/python -m pytest tests/test_api_search.py -q`
  - Result: `273 passed`.
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q`
  - Result: `25 passed`.
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
  - Result: `5 passed`.
- In-process 15-prompt matrix check
  - Result: passed for this slice, with the noted pre-existing source-card behavior on static grip prompts.

Skipped:
- Protected-preview/browser smoke was not requested for this Lane 15 backend QA and must not be inferred from local helper checks.
- Local `/api/answer` smoke was optional and not needed because the in-process helper and focused tests covered the backend route.

## Risks

Risk: low to medium.

Reasons:
- The implementation adds deterministic answer payloads and tests in the expected files only.
- It extends chord-quality validation with `diminished`; that is broader than one route but is covered by focused API and Explorer tests.
- Existing static grip prompts still include one source card. This appears pre-existing and is not part of the new harmonized-scale source-free route, but it should be kept in mind if the product standard expands to all static fretboard answers.

Rollback notes:
- Revert the Lane 05 exact files listed below if the slice causes later protected-preview issues.

## Blockers

None for the broader G harmonized-scale routing slice.

## Defect Routing

No Lane 05 defect found for this slice.

If the team decides that all static grip answers, not only static harmonized-scale prompts, must be source-free, route that as a separate Lane 05 cleanup because prompts 10-11 still include one source card under pre-existing behavior.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

If Repo Steward proceeds, stage only:

- `pocketsteel/fretboard_examples.py`
- `pocketsteel/curated_answers.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-23-05-broader-g-harmonized-scale-routing.md`
- `docs/handoffs/task-completions/2026-06-23-15-broader-g-harmonized-scale-routing-qa.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked file shown by `git status --short`.
- Protected/private/generated/corpus/deploy/design paths, including:
  - `corpus-private/`
  - `corpus-v2/`
  - Chroma/vector stores
  - embeddings
  - `source-inbox/` raw/provenance files
  - `.wrangler/`
  - DNS/deployment secrets
  - `public/`
  - `ui/brand/`
  - `Neon Sign/`
  - generated reports or private source data unless separately approved.

## Recommended Next Lane

Lane 01 Repo Steward.

Suggested prompt:

```text
Lane 01: Run ExactPathCommit for docs/handoffs/task-completions/2026-06-23-15-broader-g-harmonized-scale-routing-qa.md. Stage only the safe-to-stage files listed there, preserve unrelated dirty work, run staged diff checks, and commit the broader deterministic G harmonized-scale routing slice.
```

## Commit Readiness

Safe to commit.
