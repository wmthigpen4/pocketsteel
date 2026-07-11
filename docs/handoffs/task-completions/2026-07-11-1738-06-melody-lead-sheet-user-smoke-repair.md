# Melody Studio lead-sheet user-smoke repair

## Task summary

Repaired the three issues reported during real-device audio-transcription smoke:

1. Users no longer need to find or create an MP3 shorter than 15 seconds. Melody Studio accepts a longer local audio file, provides an in-browser player, and lets the user analyze a 5-, 10-, or 15-second window chosen by `m:ss`, total seconds, or the current playhead.
2. Lead-sheet editing now has an unmistakable active event. The selected staff event uses the amber selected style and `aria-current`; a prominent selection bar states note/rest number, pitch, measure, and beat; Previous note and Next note move the selection; the existing editor always applies to that named event.
3. **Confirm and arrange for E9** no longer appears inert. Score-structure warnings remain visible but no longer silently disable arrangement. The button shows progress, submission failures render inside the visible lead-sheet panel, and successful arrangement advances to the lesson result.

Long audio remains session-only and is never uploaded. The selected file is retained only in the browser session so the user can try another window, then released when another file is selected or Start over is used.

No backend/API contract, dependency, auth, DNS, deployment policy, corpus, Chroma, scraping, source-inbox, private data, or brand assets were changed.

## Files changed

- `docs/melody-exercise-v0.md`
- `ui/melody-score.js`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-1738-06-melody-lead-sheet-user-smoke-repair.md`

Deleted files: none. Generated repository artifacts: none.

## Tests and checks

- Focused Melody/backend/same-origin suite: `38 passed`.
- Full pytest after final changes: `935 passed in 39.08s`.
- `node --check ui/answer-client.js` — pass.
- `node --check ui/melody-workbench.js` — pass.
- `node --check ui/melody-score.js` — pass.
- `node --check ui/pedal-steel-fretboard.js` — pass.
- Exact-path `git diff --check` — pass.
- Local browser end-to-end smoke — pass.

Deterministic tests cover:

- `m:ss`, seconds, and invalid timecode parsing;
- 5/10/15-second window bounds and end-of-file clipping;
- source-window offset preservation in score events;
- all new selection, navigation, progress, audio-preview, timecode, playhead, and cache-key controls;
- warnings no longer participating in the arrange-button disabled condition.

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-lead-sheet-repair-20260711-1`
- Cache-busted URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-lead-sheet-repair-20260711-1`
- Exact URL the user should use: protected-preview URL to be recorded after commit/restart
- Auth required: yes
- Auth provider: local dev scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: `fdf2011` before implementation commit
- Version endpoint: not used for the temporary local server
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: local server ran from the tested worktree
- Whether app root `/` works: not repeated; direct Studio URL was the smoke target
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: covered by same-origin tests
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: production; unversioned Studio route
- Known caveats: browser automation cannot grant microphone permission or select a host audio file; real-file window selection remains a user-smoke action

Local browser proof:

- Created an intentionally overfull 5-beat 4/4 score.
- The warning remained visible while Arrange for E9 remained enabled.
- Note 2 displayed `Selected note 2 of 2 · A4 · measure 1, beat 2` and `aria-current` identified A4.
- Previous note changed both the selection bar and `aria-current` to G4 note 1.
- Arrange for E9 advanced to the result with all six routes, visible fretboard, and tab.
- The audio workspace showed a longer-file helper, player, 5/10/15-second window, timecode start, Use current playhead, and Transcribe selected window.
- Horizontal overflow was zero and `[object Object]` was absent.

## Integration notes

- Audio source timestamps are offset to the selected window's absolute file time.
- Score warnings remain advisory for E9 arranging; MusicXML/lead-sheet correction guidance remains visible.
- `submitLesson` now returns success/failure and can report into a caller-provided visible status element.
- Controller asset key: `melody-lead-sheet-repair-20260711-1`.

## Risk assessment

Low to medium. The arrange dead-end and selection ambiguity are directly reproduced and fixed. Long-file decoding remains device/codec dependent, but only a bounded 5–15-second PCM window is analyzed and the file stays local.

Rollback is the implementation commit created from this exact file list.

## Human decision needed

No before commit/protected automated smoke. After protected verification, the user should retry the same longer MP3 workflow.

## Safe-to-stage exact file list

- `docs/melody-exercise-v0.md`
- `ui/melody-score.js`
- `ui/melody-workbench.js`
- `ui/melody-workbench.html`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-11-1738-06-melody-lead-sheet-user-smoke-repair.md`

## Files that must not be staged

All other dirty or untracked paths, especially corpus/source-inbox, private-data, vector/Chroma, scraping, public/brand/design, deployment, environment, secret, and generated-report files.

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 protected-preview refresh and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the exact files above, verify protected note selection and warning-bearing arrangement, and return the longer-MP3 user-smoke URL.
