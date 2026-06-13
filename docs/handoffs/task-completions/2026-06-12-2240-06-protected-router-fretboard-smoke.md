## Task summary
- What was requested: Run a protected-preview browser smoke after the latest fretboard/router commits against `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=router-fretboard-smoke-2`.
- What was completed: Browser-smoked all requested chord, position, pocket, copedent, and general-learning prompts in an authenticated protected-preview session. Verified fretboard routing, direct diagnostic behavior, absence of `[object Object]`, absence of weak-source warnings, and correct suppression/appearance of the fretboard card by question type.
- What was intentionally not changed: No UI, backend, routing, corpus, Chroma, embeddings, deployment, DNS, auth, or scraping changes were made. No files were staged or committed.

## Files changed
- Changed files: none.
- Created files: `docs/handoffs/task-completions/2026-06-12-2240-06-protected-router-fretboard-smoke.md`.
- Deleted files: none.
- Generated artifacts: none.

## Browser smoke
- Exact URL tested: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=router-fretboard-smoke-2`.
- Browser entry method: authenticated protected-preview in-app browser session.
- Note: The browser connector text-entry path could not use the virtual clipboard, so prompts were entered with per-key input. This did not affect the app behavior being tested.

| Prompt | Result | Notes |
| --- | --- | --- |
| Where are some places to play C chords? | Pass | Fretboard appeared. Routed to C positions: `8 open`, `11 A+F`, `15 A+B`. No SGF fragments, weak-source warning, or `[object Object]`. |
| I am in the key of G. Where can I play a 6m chord? | Pass | Fretboard appeared. Routed to E minor / 6m in G: `3 A`, `8 E`, `10 B+C`. Deterministic answer. |
| How do I plan an F chord? | Pass | Fretboard appeared. Typo/intent routed to play F. Starter positions included `1 open`, `4 A+F`, `8 A+B`. |
| Where all can I play a G chord? | Pass | Fretboard appeared. Starter positions: `3 open`, `6 A+F`, `10 A+B`. |
| Where all can I play a B chord? | Pass | Fretboard appeared. Starter positions: `7 open`, `10 A+F`, `14 A+B`. |
| What does 5-7-8 with E lowered give me at the 3rd fret? | Pass | Focused diagnostic payload appeared with one selector and no full browser tabs. Answer identified D major with rootless B minor 7 color context. |
| Is 5-7-8 with E lowered a B9 pocket? | Pass | No fretboard card. Direct validation answer said it is not a full B9 pocket and explained the D major / rootless color relationship. |
| Show me V chord pockets in A. | Pass | Fretboard appeared. Routed to E as V in A, with starter positions `0 open`, `3 A+F`, `7 A+B`. |
| What is my copedent? | Pass | No fretboard card. Copedent rendered correctly and included string 9 as `D`. Private source card shown. |
| Teach me about pockets. | Pass | No fretboard card. Direct learning answer with appropriate source card; no raw SGF fragment behavior observed. |

## Pass-condition checklist
- No SGF fragment answers: pass.
- No weak-source warning visible: pass.
- No `[object Object]`: pass.
- Fretboard appears for chord/position/pocket questions: pass.
- Direct diagnostic questions do not show full browser tabs: pass.
- C chords route to C positions: pass.
- G 6m routes to E minor / deterministic limited minor answer: pass.
- `plan F` routes to play F: pass.
- Copedent shows string 9 as D: pass.
- Non-position questions do not show fretboard: pass.

## Tests and checks
- `node --check ui/pedal-steel-fretboard.js`: passed.
- `node --check ui/answer-client.js`: passed.
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py tests/test_frontend_answer_ui.py tests/test_same_origin_smoke_server.py`: passed, 53 passed.
- `.venv/bin/python -m pytest`: passed, 512 passed.
- `git diff --check`: passed.
- Tests skipped and why: none.

## Integration notes
- Lane 06 can treat the protected-preview router/fretboard smoke as green for the tested prompts.
- The current UI no longer shows the removed `Include lever positions` control in this smoke path.
- Direct diagnostic payloads use focused display without full multi-position tabs.
- Selector cards include short reason copy such as `starter:`, `dominant pocket:`, and `advanced:`.
- Source cards are suppressed for deterministic chord-position answers where expected.
- No schema/API/component/data contract changes were made.
- Assumptions: The authenticated protected-preview session reflects the current app runtime for `v=router-fretboard-smoke-2`.
- Blockers: none found.
- Human decisions needed: none for this smoke.

## Risk assessment
- Low.
- Why: This was a read-only browser smoke plus test verification. The only repo change is this handoff report.
- Rollback notes: Delete this handoff report if it needs to be replaced; no runtime code was changed.

## Commit readiness
Safe to commit

## Suggested next step
- Lane 15 QA / Answer Eval should run the next exploratory smoke pass.
- Recommended prompt: `Run QA exploratory smoke against the protected preview for the current fretboard/router behavior, expanding beyond the Lane 06 fixed prompt list into edge-case chord spellings, pocket diagnostics, direct lesson questions, and non-position forum/source questions. Confirm no SGF fragments, no weak-source warnings, no [object Object], and correct fretboard visibility.`
