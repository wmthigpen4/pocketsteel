# Melody Studio lesson-focus user-smoke adjustment

## Task summary

Implemented the current Melody Studio user-smoke feedback without changing arranger or API contracts:

- moved every available arrangement route into one row directly below the fretboard;
- replaced the phrase-length row of technical pills with one active-note navigator that reads in steel-player language;
- made Octave colors opt-in and kept its hidden-until-enabled legend beside the control;
- renamed `Hear chords` to `Play chord backing` and hid it unless the arranged events contain real chord symbols;
- removed the deterministic implementation explanation from the lesson;
- moved new-note and selected-note duration controls into progressive score disclosures while preserving rhythm editing for transcription and playback.

The existing eight-event section boundary remains intact. A twelve-note local smoke phrase rendered eight notes in section one and offered `Continue to Section 2`.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lanes: `15 QA / Answer Eval`, `01 Repo Steward`, then `12 Self-Hosted Deployment`
- Mode: approved user-smoke adjustment / Autopilot

## Files changed

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- this handoff

No files were deleted. No generated assets were created.

## Tests and checks

- `node --check ui/melody-workbench.js` — pass
- `node --check ui/melody-score.js` — pass
- `node --check ui/pedal-steel-fretboard.js` — pass
- `PYTHONPATH=.:scripts .venv/bin/pytest -q tests/test_melody_workbench_ui.py tests/test_pedal_steel_fretboard_ui.py tests/test_frontend_answer_ui.py tests/test_same_origin_smoke_server.py` — 81 passed
- `PYTHONPATH=.:scripts .venv/bin/pytest -q` — 935 passed
- `git diff --check -- ui/melody-workbench.html ui/melody-workbench.js tests/test_melody_workbench_ui.py tests/test_same_origin_smoke_server.py docs/melody-exercise-v0.md` — pass

## Local browser smoke

- Typed `1 2 3 4 5 6 7 1 2 3 4 5` and arranged it successfully.
- Verified exactly one active event card: `Note 1 of 8 · G4 · String 8 · Fret 15 · Open`.
- Verified event navigation changed the card and active fretboard state to note two.
- Verified no `S6+7+10`-style shorthand appears in the navigator.
- Verified six route buttons render between the fretboard and tab.
- Verified Octave colors defaults off, its legend is hidden, and enabling it reveals the adjacent legend and overlay.
- Verified melody-only results hide Play chord backing.
- Verified the removed deterministic explanation is absent.
- Verified viewport containment and internal route scrolling at the narrow browser breakpoint.
- Verified zero browser console warnings or errors.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-lesson-focus-local-20260711-1`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending protected-preview refresh after commit
- Auth required: yes
- Auth provider: local development scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: `8765`
- Expected git HEAD: working tree based on `9062bef`
- Version endpoint: not used for working-tree browser smoke
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: cache-busted working-tree assets
- Whether app root `/` works: yes, redirects to the home UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: unversioned or prior protected Melody Studio URLs
- Known caveats: the narrow in-app browser honored a minimum 487px layout viewport; document and viewport widths matched with no page-level overflow

## Integration notes

- No API, melody request, score draft, arranger, tab, or fretboard component contract changed.
- Rhythm values are retained because score playback and faithful transcription require timing, but the controls are no longer part of the default score surface.
- Chord backing is tied to actual chord metadata, not to harmony-route voicings and not to treble-clef display.

## Risk assessment

Low. The change is client-only hierarchy, presentation, and conditional visibility with focused regression coverage. Rollback is the scoped implementation commit.

## Human decision needed

No. The adjustment is approved and ready for exact-path commit and protected-preview verification.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-11-2314-06-melody-lesson-focus-adjustment.md`

## Files that must not be staged

Every other modified or untracked path, especially corpus, source-inbox, private-data, deployment, public/brand, `ui/brand/`, `Neon Sign/`, generated reports, and unrelated docs/runtime files.

## Recommended next lane

`01 Repo Steward` for exact-path commit, then `12 Self-Hosted Deployment` for protected-preview restart and authenticated smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval, stage only the six safe files above, commit the user-smoke adjustment, restart protected preview, verify `/api/version`, run authenticated protected browser smoke, and refresh `integration-status.md` separately.
