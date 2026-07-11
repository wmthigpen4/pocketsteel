# Melody Studio Add-a-Melody UX Simplification

## Task summary

Implemented the approved Melody Studio workflow simplification. The six equal entry cards are replaced by one calm **Add a melody** workspace with three compact entry paths: Type or tap notes, Record or upload audio, and Import music when temporary imports are enabled. Staff notation, recording attribution, and reviewed examples are contextual actions. Phrase, score, audio, import, catalog, arranger, and result contracts remain unchanged.

The quick path now shows notes/scale numbers, one note-button row, the live sequence, G/C, and one Arrange for E9 action. Contour, literal-tab help, and practice starters are progressively disclosed. Staff setup, selected-note details, score tools, and audio rhythm/window controls are collapsed until relevant. Audio/import/catalog results transition into Review melody.

Changing melody sources with a non-empty draft now opens an inline Replace melody / Keep editing decision; no session draft is silently discarded. Recording attribution remains optional, survives a source change when populated, and explicitly states that links identify sources but are not automatically transcribed.

Intentionally unchanged: `/api/answer`, `melodyRequest`, `score_draft_v1`, `melody_exercise`, arranger mechanics, audio analysis, import endpoints, feature-flag defaults, persistence, auth, deployment configuration, corpus, Chroma, scraping, private data, and unrelated app UI.

## Lane classification

- Primary lane: 06 UX/UI Design
- Supporting lanes: 18 Product / Architecture, 15 QA / Answer Eval, 01 Repo Steward, 12 Self-Hosted Deployment
- Mode: approved YELLOW UI-flow implementation / Autopilot

## Files changed

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- This handoff

No files were deleted or generated.

## Tests and checks

- `node --check ui/answer-client.js` — pass
- `node --check ui/melody-score.js` — pass
- `node --check ui/melody-workbench.js` — pass
- `node --check ui/pedal-steel-fretboard.js` — pass
- Focused Melody/API/UI/import slice — 41 passed, 300 deselected
- Full pytest — 935 passed
- `git diff --check -- <scoped files>` — pass

### Local browser smoke

- Initial desktop viewport showed three compact entry methods, G/C, one visible Arrange for E9 action, and no console warnings/errors.
- Typing `1 2 3 5` rendered G4, A4, B4, D5 sequence chips and changed alternate entry controls to Replace melody.
- Requesting audio replacement showed the inline confirmation while preserving the phrase; Keep editing closed it without losing the phrase.
- Confirming replacement cleared the phrase and opened the audio path.
- Audio player/window controls were hidden before file selection; Rhythm options stayed collapsed.
- Optional recording details opened contextually and stated that links are not automatically transcribed.
- Staff editor initially showed note length, undo/redo, Play, staff, and Arrange; Score setup and Score tools were closed.
- Adding G4 changed the phase to Review melody. Pitch/duration remained visible while chord, lyric, tie, and articulation stayed collapsed.
- The Amazing Grace example opened directly into Review melody with sourced score metadata.
- Typed `1 2 3 5` arranged successfully into `Your melody exercise in G`; Edit melody returned to the populated editor.
- Mobile containment check reported equal document client and scroll widths, three wrapping entry choices, and one visible primary Arrange action.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8765/ui/melody-workbench.html?access=beta_user&v=melody-add-melody-ux-local-20260711-3`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending committed protected-preview refresh
- Auth required: yes
- Auth provider: local development scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8765`
- Expected backend port: 8765
- Expected git HEAD: working tree based on `62eeeed`
- Version endpoint: not used for the working-tree browser smoke
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: cache-busted working-tree assets
- Whether app root `/` works: yes, redirects to the home UI
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: unversioned or prior protected Studio URLs
- Known caveats: real microphone permission and host-file selection remain user-smoke boundaries

## Integration notes

- `features.melodyImport=false` hides the Import music entry and Try an example song action instead of presenting unavailable controls. The Type and Audio paths remain available under `melodyExercise`.
- Entry methods are adapters to the existing in-memory phrase or score draft. No storage was added.
- Populated recording details preserve the artist/song teaching kind across audio/import-to-review transitions.
- The inline replacement decision avoids disruptive native browser dialogs and keeps keyboard focus inside the application.

## Risk assessment

Medium-low. The change reorganizes a broad but feature-contained UI and state flow while leaving server contracts untouched. The focused, full-suite, and local-browser checks are green. Rollback is the scoped implementation commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-11-1849-06-melody-add-melody-ux-simplification.md`

## Files that must not be staged

All unrelated dirty corpus, source-inbox, private-data, deployment, public/brand, Neon Sign, RAG pipeline, README, environment, and pre-existing documentation files.

## Recommended next lane

01 Repo Steward exact-path commit, then 12 Self-Hosted Deployment protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval with the exact safe-to-stage list, restart the protected preview, verify the committed version, run authenticated phrase/replacement/staff/arrangement smoke, and refresh `integration-status.md` separately.
