# 2026-08-12 17:38 Lane 06 Complete Major-7 Grip

## Task Summary

Added the standard transposable E9 major-7 grip that uses A+B and strings 9-7-6-5 in low-to-high picking order. The Explorer stores the canonical string group as `5-6-7-9`, validates all four chord tones, and presents it as a complete core major-7 voicing rather than a rootless partial.

The implementation is generic across all keys. With A+B down, the grip spells root, 3rd, 5th, and major 7th from fret 0 (Dmaj7) through fret 11 (C#maj7), repeating at the octave.

Intentionally not changed:

- No backend pitch engine or generated Explorer payload changes.
- No corpus, Chroma, embeddings, scraping, auth, DNS, deployment, or private-source changes.
- No protected-preview restart in this handoff.

## Files Changed

- `ui/e9-music-rules.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `tests/test_e9_explorer_controls_ui.py`
- `docs/handoffs/task-completions/2026-08-12-1738-06-complete-major7-grip.md`

No files were deleted and no generated assets were changed.

## Tests And Checks

Passed:

- `node --check ui/e9-music-rules.js`
- `node --check ui/e9-fretboard-explorer.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py tests/test_e9_explorer_controls_ui.py -q`
  - `52 passed`
- `git diff --check`

Regression coverage verifies:

- Amaj7 at fret 7, A+B, strings `5-6-7-9` contains G#, E, C#, A and omits no target interval.
- The same grip produces a complete major-7 chord for all 12 chromatic roots at the expected fret.
- The complete four-note grip becomes the selected Fmaj7 card in the rendered DOM test.
- The grip explanation gives the player-facing low-to-high order `9-7-6-5`.

## Local Smoke Result

Smoke Target:

- Target type: local
- Result type: executable DOM/UI smoke; final in-app browser smoke blocked by local-port policy
- Exact browser URL attempted: `http://127.0.0.1:8785/ui/e9-fretboard-explorer.html?v=complete-major7-grip-20260812-smoke`
- Cache-busted URL attempted: same as above
- Auth required: no
- Auth provider: none
- Local backend URL: `http://127.0.0.1:8785`
- Expected backend port: `8785`
- Expected git HEAD: current HEAD plus scoped uncommitted changes
- Version endpoint result: not applicable to local smoke
- Root URL status: not checked
- API fallback status: not applicable
- Exact URL the user should test: protected-preview URL after Lane 12 restart

The first browser check against the existing port 8770 loaded the old rules asset and exposed a stale cache-buster. `ui/e9-fretboard-explorer.html` was updated to request `e9-music-rules.js?v=complete-major7-grip-20260812`. A clean local same-origin server was then started on port 8785, but the in-app browser blocked navigation to that port. The focused DOM/UI test exercises the same rendered chord-finder path and passes.

## Integration Notes

- `CORE_GROUPS` and `GRIP_REGISTRY` now contain `5-6-7-9`.
- Chord Finder already computes candidates from the selected copedent, fret, and control state, so no key-specific rows were hardcoded.
- The common control scope already includes A+B.
- Canonical group order remains ascending by E9 string number (`5-6-7-9`); player-facing copy documents the low-to-high picking order (`9-7-6-5`).

## Risk Assessment

Risk: low to medium.

The pitch rule and rendered behavior have focused all-key coverage. Remaining risk is protected-preview cache/runtime propagation because final authenticated browser smoke has not run.

Rollback: revert the scoped registry entry, HTML asset version, and focused tests.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/e9-music-rules.js`
- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `tests/test_e9_explorer_controls_ui.py`
- `docs/handoffs/task-completions/2026-08-12-1738-06-complete-major7-grip.md`

## Files That Must Not Be Staged

- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- All unrelated dirty, generated, private, corpus, Chroma, deployment, and auth files.

## Recommended Next Lane

Lane 01 exact-path commit, followed by Lane 12 protected-preview restart and authenticated browser smoke.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Exact-path commit the five files listed above with commit message `feat: add complete transposable major 7 grip`, then run protected-preview smoke for Amaj7 at fret 7 with A+B on strings 5-6-7-9.
