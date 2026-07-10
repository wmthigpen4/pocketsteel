# Melody Studio UX Rescue

## Task summary

Implemented the approved user-smoke adjustment that replaces the exposed technical Melody form with a dedicated, guided Melody Studio. The home header now has a feature-gated Melody Studio action between Explore Fretboard and Backstage. The new workspace guides the player through a task, optional recording identity, phrase construction, and a fretboard-first E9 lesson.

The existing `POST /api/answer`, `melodyRequest`, and `melody_exercise` contracts remain unchanged. Audio uploads, YouTube extraction, automatic transcription, all-key support, corpus work, scraping, embeddings, Chroma, auth policy, DNS, private sources, and unrelated assets were intentionally not changed.

## Lane classification

- Primary lane: 06 UX/UI Design.
- Supporting lanes: 15 QA, 01 Repo Steward, then 12 Self-Hosted Deployment.
- Mode: approved Autopilot user-smoke adjustment.

## Files changed

- `ui/melody-workbench.html` — new guided, responsive Melody Studio workspace.
- `ui/melody-workbench.js` — task state, phrase parsing/palette/presets, payload construction, section continuation, result rendering, and visible synchronization.
- `ui/steel-guitar-rag-mock.html` — feature-gated top header entry, responsive labels, removed inline form, and natural-answer handoff.
- `ui/pedal-steel-fretboard.js` — exported position-selection method for visible event synchronization.
- `docs/melody-exercise-v0.md` — canonical dedicated-workspace frontend contract.
- `tests/test_melody_workbench_ui.py`, `tests/test_frontend_answer_ui.py`, `tests/test_same_origin_smoke_server.py` — focused regression coverage.
- Deleted: none.
- Generated artifacts: none.

## Tests and checks

- `PYTHONPATH=.:scripts .venv/bin/pytest -q` — 913 passed.
- Initial expanded focused run — 383 passed, 1 stale static header assertion failed; assertion updated to the new desktop/mobile labels.
- Intermediate focused run — 76 passed, 1 second stale header-span assertion failed; corrected before the full green run.
- `node --check ui/answer-client.js` — passed.
- `node --check ui/melody-workbench.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `git diff --check` — passed.

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8898/ui/melody-workbench.html?access=beta_user&v=melody-studio-local-20260710`
- Cache-busted URL tested: same as above
- Exact URL the user should use: protected-preview URL only after Lane 12 passes
- Auth required: yes
- Auth provider: local scaffold development role
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8898`
- Expected backend port: 8898
- Expected git HEAD: pre-commit working tree based on `5aa4e18`
- Version endpoint: `http://127.0.0.1:8898/api/version`
- Version endpoint result: feature-enabled local runtime from the working tree
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not used as the canonical local target
- Whether app root `/` is expected to work: redirects to the main UI
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: no user smoke against local `127.0.0.1`
- Known caveats: API fallback is not browser smoke; browser viewport control bottoms out near 487–541 CSS pixels in this environment.

Browser results:

- Home header showed Explore Fretboard, Melody Studio, and Go Backstage in the approved order; local-dev navigation preserved the explicit beta role.
- Melody Studio showed four plain-language learner jobs and hid the editor until a job was chosen.
- Switching from Artist Solo to Original Exercise cleared artist, song, recording/source data and hid recording fields.
- Phrase presets built removable/reorderable sequence chips and reported the correct section count.
- Original `1 2 3 5` rendered a fretboard-first lesson with tab and four events.
- Next Note visibly changed the fretboard selected position to `melody-g-section-1-event-2`, the event strip to A/S4/F5, and the active tab-step label.
- A ten-note phrase rendered Section 1 of 2 with eight events; Continue to Section 2 rendered the remaining two events and hid continuation.
- Source-needed artist flow kept fretboard/tab hidden, preserved attribution, and contained no copyright refusal.
- Narrow-header labels switched to Fretboard, Melody, and Backstage with no material page-level overflow.
- Tab computed `white-space: pre` and `overflow-x: auto`.
- No `[object Object]` or relevant browser console errors appeared.

## Integration notes

- New static route: `/ui/melody-workbench.html`.
- New client asset: `/ui/melody-workbench.js`.
- Home header action is hidden until `/api/session` returns `features.melodyExercise=true`.
- Local-dev header navigation preserves `?access=<role>`; production/protected navigation uses the clean route.
- The new fretboard API is `selectPedalSteelFretboardPosition(container, positionId)` and returns whether the selection succeeded.
- A recording link is explicitly described as attribution only; this slice does not imply media analysis.

## Risk assessment

- Risk: medium because the main header, home markup, shared fretboard component, and a new user-facing route changed.
- Mitigations: unchanged backend contract, feature gating, 913-test suite, focused helper/static tests, and live local browser verification.
- Rollback: revert the scoped implementation commit; the backend Melody API remains compatible.

## Human decision needed

No before commit/protected smoke. User smoke begins only after the protected loop passes.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-10-1341-06-melody-studio-ux-rescue.md`
- `docs/melody-exercise-v0.md`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `ui/pedal-steel-fretboard.js`
- `ui/steel-guitar-rag-mock.html`

## Files that must not be staged

All paths not listed above, especially corpus/source metadata, source-inbox, pipeline scripts, private/vector data, `public/`, `ui/brand/`, `Neon Sign/`, deployment assets, and unrelated handoffs.

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 12 protected-preview update and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval: stage only the exact files above, commit the UX rescue, restart the protected preview, and run the protected header/workspace smoke before issuing a user URL.
