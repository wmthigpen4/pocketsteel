# 2026-06-27 11:41 - Lane 15 - Explorer Musical Red-Team QA

## Pass / Warn / Fail

Warn.

No product blockers were found in the focused automated red-team coverage added in this slice. The warning is that this run did not perform a new browser/protected-preview smoke after adding the QA test file, and the richest chord/voicing finder logic still lives in the frontend Explorer controller rather than a shared backend musical rules module.

## Task Summary

Requested: create and run a focused musical red-team QA matrix for the E9 Fretboard Explorer across pitch math, copedent controls, notation modes, major-7 versus dominant-7 traps, partial/rootless labels, cross-copedent behavior, and Explorer UI behavior before monetization.

Completed:

- Inspected repo guidance, integration status, recent Explorer handoffs, Explorer backend rules, Explorer UI controller, and existing frontend/backend test coverage.
- Added focused backend QA tests for the highest-risk deterministic pitch/control facts that should not depend on browser UI behavior.
- Ran the requested focused checks and existing Explorer/frontend/fretboard tests.

Intentionally not changed:

- No Explorer backend behavior.
- No UI implementation.
- No protected-preview restart/deployment.
- No auth, DNS, scraping, embeddings, Chroma/vector stores, raw corpus, source records, private transcripts, secrets, or private data.

## Branch And HEAD

- Branch: `feature/answer-api`
- Starting HEAD: `ebb7435`
- Final HEAD / commit hash if committed: reported in the final Codex response after the scoped QA commit.
- Latest relevant protected-preview status: integration status records protected-preview Explorer Chord / Voicing Finder browser behavior passed for the cache-busted static Explorer URL, with `/api/version` still reporting older runtime SHA `4040a47`.

## Files Inspected

- `AGENTS.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-27-1110-18-fretboard-musical-product-audit.md`
- `docs/handoffs/task-completions/2026-06-27-1140-12-chord-voicing-finder-protected-smoke.md`
- `pocketsteel/e9_copedents.py`
- `pocketsteel/fretboard_explorer.py`
- `ui/e9-fretboard-explorer.js`
- `tests/test_fretboard_explorer.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`

## Files Changed

- Added `tests/test_explorer_musical_red_team.py`
- Added `docs/handoffs/task-completions/2026-06-27-1141-15-explorer-musical-red-team.md`

## Red-Team Cases Covered

Added backend QA coverage:

- String 3 fret 3 open resolves to `B`.
- String 3 fret 3 with B pedal resolves to `C`.
- String 5 fret 3 open resolves to `D`.
- String 5 fret 3 with A pedal resolves to `E`.
- String 9 fret 3 open resolves to `F`.
- Key F / fret 3 / strings 4-6-10 / A+B resolves to `G-C-E`, the C major pitch set for V in F.
- Key G / fret 3 / strings 5-6-9 / A+B resolves to `E-C-F`, intervaled against F as `7-5-1`, a major-7/no-3 color rather than dominant/V7.
- Key G / fret 3 / strings 5-7-9 / A+B resolves to `E-A-F`, intervaled against F as `7-3-1`, a major-7/no-5 color rather than dominant/V7.
- F-A-Eb/D# resolves against F as `1-3-b7`, a dominant-7/no-5 color rather than Fmaj7.
- A, B, C, E-raise, E-lower, D-lower, and G-lower control impact previews stay string-aware.
- Emmons/Day profiles do not include Custom LKV `B-to-Bb`; Day preserves `C, B, A` pedal order; Custom LKV exposes `B-to-Bb`.

Existing frontend/backend coverage reviewed and rerun:

- `V7 in G` resolves to `D7`.
- `Imaj7 in F` resolves to `Fmaj7`.
- `Fmaj7`, `F major 7`, and `FΔ7` parse as major 7.
- `Cmin9` / `Cm9` parse as minor 9 and show clear no-practical-voicing behavior under default filters.
- Missing 3rd lowers confidence for partial major-7 voicings.
- Missing 5th can remain practical.
- 9th-string color alone does not imply dominant 7.
- NNS, Roman, Numbers, and Notes notation modes are covered by frontend tests.
- Single-note finder pedal effects are covered by frontend tests.
- Grip vocabulary tiers, dyad/pad roles, and mixed string-group path behavior are covered by frontend tests.

## Failures / Warnings

Failures: none in the focused checks run.

Warnings:

- Chord/voicing finder musical inference is still primarily frontend-side. That is acceptable for the current Explorer UI, but monetization-critical musical truth should eventually move into or be mirrored by shared deterministic rules so backend answers, tab, and Explorer cannot drift.
- Protected-preview browser behavior is current for the existing Chord / Voicing Finder smoke handoff, but this new red-team QA test commit itself has not been protected-smoked.
- `/api/version` caveat remains in integration status: protected-preview static UI can be cache-busted independently of the Python runtime version endpoint.

## Musical Risks

- Rootless and partial voicings remain interpretation-heavy. UI must keep omitted tones, confidence, and alternate readings visible.
- Copedent naming needs continued discipline: selected chart/preview behavior, generated row behavior, and future custom-copedent behavior should not be conflated.
- Major-7 versus dominant-7 traps are now explicitly covered, but they should stay in the regression set as chord finder grows.
- Minor 9 and dominant 9 requests are handled through frontend chord-finder filtering today; future answer integration should add backend/API-level assertions before exposing them outside the Explorer UI.

## Product Risks

- Monetization should not claim exact custom-copedent generation until generated rows actually vary by user copedent, not just chart/preview selection.
- Browser smoke remains necessary for visual validation; the automated tests prove logic and markup behavior, not usability or visual clarity.
- If Explorer answers start using these results, Lane 05 needs answer-level contract tests so RAG/corpus never invents fret/string/pedal rows.

## Tests And Checks

Passed:

- `git diff --check`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `.venv/bin/python -m py_compile tests/test_explorer_musical_red_team.py`
- `.venv/bin/python -m pytest tests/test_explorer_musical_red_team.py -q` -> 4 passed
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` -> 38 passed
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` -> 23 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` -> 34 passed

Not run:

- Protected-preview smoke. This task did not request deployment/restart and explicitly forbids protected-preview restart.
- Full pytest. The requested focused checks were run; the worktree also contains extensive unrelated dirty/untracked material.

## Protected-Preview Smoke Currency

Current with caveat for existing Explorer Chord / Voicing Finder behavior: integration status records protected-preview browser smoke passed for the cache-busted Explorer static page, while `/api/version` still reports an older runtime SHA.

Stale relative to this QA slice: no protected-preview smoke has run after adding the new red-team QA test file.

## Files Intentionally Left Unstaged

All unrelated dirty and untracked files remain untouched, including corpus/source/public/brand/private/generated/deployment-adjacent material already present in the worktree.

## Safe-To-Stage Exact File List

- `tests/test_explorer_musical_red_team.py`
- `docs/handoffs/task-completions/2026-06-27-1141-15-explorer-musical-red-team.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked worktree files.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, `source-inbox` raw/provenance files, `.wrangler/`, DNS/deploy secrets, `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated private reports, and corpus/source data.

## Human Decision Needed

No for committing this scoped QA/test slice if the staged diff remains limited to the two exact files above.

Yes before monetization: decide whether chord/voicing finder musical inference should be promoted from frontend-only UI logic into a shared deterministic backend rules module.

## Commit Readiness

Safe to commit if exact-path staging includes only the two files listed above and `git diff --cached --check` passes.

## Recommended Next Lane

Lane 12 should run protected-preview smoke only after this QA commit is included in the intended build and a cache-busted Explorer URL is available.

Lane 05 should own any future move of chord/voicing finder identity logic into shared deterministic backend rules.

Suggested next prompt:

```text
Lane 12: run protected-preview Explorer browser smoke for the current feature/answer-api HEAD after the musical red-team QA commit. Verify the Chord / Voicing Finder, Voicing Identifier, Single Note Finder, and core Explorer modes still pass at a cache-busted URL, with /api/version noted separately from static asset behavior.
```
