# Integration Status — Current Snapshot

Updated: 2026-07-11 13:21 America/Chicago

## Repository state

- Branch: `feature/answer-api`
- Current implementation: `74520ca Expand Melody Studio score practice`
- Melody API baseline: `f37201a feat: add Melody Exercise teaching workflow`
- Melody Studio now uses Steel Guitar RAG branding. No broad repository rename is approved.

## Melody Studio

Status: **PASS — score-practice Melody Studio is committed, 934-test green, and verified in the authenticated protected preview. The default-off import/catalog server flag is intentionally not enabled in protected configuration.**

- The home header now exposes feature-gated actions in this order: Explore Fretboard, Melody Studio, Backstage.
- The technical inline Melody form was removed from home.
- `/ui/melody-workbench.html` opens with six equal inputs: Enter notes or intervals, Build a score, Photo or music file, Play or hum it, Use a recording, and Pick a song.
- The original note/degree/literal-E9 phrase editor remains intact and is the default input.
- The lead-sheet builder supports one treble melody voice, G/C, 3/4 and 4/4, pickup, supported note/rest durations, ties, accidentals, chord symbols, lyrics/labels, undo/redo, measure actions, duplicate, transpose, browser playback, and local MusicXML download.
- Melody pitch and chord symbols are separate: melody-only input shows no invented chord labels, while supplied harmony appears only at actual changes.
- The score is an interactive practice surface with synchronized staff/fretboard/navigator/tab selection, adjustable tempo, count-in, pause/resume, stop, measure and selected-note loops, and optional chord sound.
- VexFlow renders G/C key signatures, beams, rests, ties, dots, lyrics, and accent/tenuto/staccato; MusicXML and print output preserve the supported notation.
- Chord symbols guide mechanically validated harmony and chord-melody grip ranking while the resolved melody remains the top voice.
- All input methods normalize into session-only `score_draft_v1`; no uploaded source or draft is persisted.
- A pinned local VexFlow 5.0.0 bundle renders the editable and result staffs, with a local SVG fallback.
- The recording starting point reveals source fields plus faithful-solo versus playable-E9-arrangement treatment; the manual editor keeps practice presets behind its practice-phrase starter.
- Recording fields are cleared when switching to either source-free starting point.
- Phrase entry supports notes, scale degrees, literal one-string E9 tab, note/degree palette buttons, deterministic presets, sequence editing, and section counts.
- After task selection, the task-card grid collapses so the active editor/result is the page focus.
- Phrase notes are clean selectable token/pitch chips. The selected note uses a compact `− / Octave / +` register stepper, a separate Return to automatic action, and separate ordering/removal actions.
- Unmarked degrees use closest-playable octave contour by default; ascending, descending, preserve-input, and per-note octave controls are available.
- Per-note octave controls modify only the selected event; they do not re-anchor later automatic notes.
- Literal tab preserves string, fret, control state, and pitch register.
- YouTube runs only in the official embedded player with loop/tempo companion controls; Ultimate Guitar remains an attributed side reference and is never scraped.
- Public-domain Amazing Grace / NEW BRITAIN is stored as a reviewed, checksummed catalog draft and was locally verified with exact melody, chords, E9 positions, and optional generated F#4→G4 ornament.
- Results are fretboard-first. Every mechanically available single-note, Recommended Harmony, thirds, sixths, and chord-melody route appears in one visible, horizontally scrollable row.
- The lesson header omits the generic Practice the lesson kicker and the non-actionable exactness/confidence/single-section metadata line.
- One compact navigator beneath the fretboard combines Octave colors, legend, note progress, adjacent previous/next arrows, concise steel-player position pills, and one current-note readout.
- Route, arrow, and pill controls visibly synchronize the selected fretboard position, active pill, fixed-width tab route, pedal/lever instructions, and current-note movement cue.
- The duplicated active-tab sentence and verbose event-detail sentence have been removed.
- Melody Studio hides the Explorer-oriented position-card strip, filters, legend, and full technical inspector. A compact Current note readout now states the active note, string(s), fret, controls, and movement cue.
- Melody tab omits artificial `Ly | step N` rows. Event selectors spell out string, fret, and pedal/lever positions, and the primary harmony route is labeled `Recommended harmony` without duplication.
- A default-on, user-toggleable scientific-octave map colors accurate octave zones independently along every E9 string; it does not pretend that one fret-wide band represents one octave across all strings.
- The compact octave 2–6 legend, exact fretboard note markers, and event steps share the same palette. Harmony steps retain the top melody voice's octave label while each displayed harmony marker uses its own exact octave.
- Long phrases continue through the existing `sectionNumber` contract.
- Original exercises suppress recording identity and source UI.
- Deterministic scope remains E9 in G/C major.
- Melody Studio contains no `The Turnaround` copy and now uses the same image-free amber/dark gradient background as E9 Fretboard Explorer.

Canonical contract: `docs/melody-exercise-v0.md`.
Implementation handoff: `docs/handoffs/task-completions/2026-07-10-1341-06-melody-studio-ux-rescue.md`.
Protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1354-12-melody-studio-protected-smoke.md`.
Adjustment handoff: `docs/handoffs/task-completions/2026-07-10-1404-12-melody-studio-background-protected-smoke.md`.
Arranger implementation handoff: `docs/handoffs/task-completions/2026-07-10-1432-05-06-melody-studio-arranger-upgrade.md`.
Arranger protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1435-12-melody-arranger-protected-smoke.md`.
Calm-controls protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1552-12-melody-studio-calm-controls-protected-smoke.md`.
Independent-octave protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1559-12-independent-octave-protected-smoke.md`.
Fretboard-clarity implementation handoff: `docs/handoffs/task-completions/2026-07-10-1609-06-melody-fretboard-card-cleanup.md`.
Fretboard-clarity protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1611-12-melody-fretboard-cleanup-protected-smoke.md`.
Lesson-label implementation handoff: `docs/handoffs/task-completions/2026-07-10-1631-06-melody-lesson-label-cleanup.md`.
Lesson-label protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1632-12-melody-lesson-labels-protected-smoke.md`.
Scientific-octave implementation handoff: `docs/handoffs/task-completions/2026-07-10-1901-06-melody-scientific-octave-guide.md`.
Scientific-octave protected-smoke handoff: `docs/handoffs/task-completions/2026-07-10-1903-12-melody-octave-guide-protected-smoke.md`.
Octave-map adjustment handoff: `docs/handoffs/task-completions/2026-07-11-0736-06-melody-scientific-octave-map-adjustment.md`.
Octave-map cache-bust handoff: `docs/handoffs/task-completions/2026-07-11-0739-06-melody-octave-map-cache-bust.md`.
Octave-map protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-0742-12-melody-octave-map-protected-smoke.md`.
Compact-flow implementation handoff: `docs/handoffs/task-completions/2026-07-11-0801-06-melody-compact-flow-navigator.md`.
Compact-flow protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-0804-12-melody-compact-flow-protected-smoke.md`.
Lesson-header implementation handoff: `docs/handoffs/task-completions/2026-07-11-0812-06-melody-lesson-header-cleanup.md`.
Lesson-header protected blocker: `docs/handoffs/task-completions/2026-07-11-0815-12-melody-header-protected-smoke-blocker.md`.
Multi-input implementation handoff: `docs/handoffs/task-completions/2026-07-11-0837-18-melody-studio-multi-input-builder.md`.
Multi-input protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-0841-12-melody-multi-input-protected-smoke.md`.
Resumed lesson-header protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-1246-12-melody-header-protected-smoke-resumed.md`.
Score-practice implementation handoff: `docs/handoffs/task-completions/2026-07-11-1317-05-06-melody-score-practice-arranger.md`.
Score-practice protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-1321-12-melody-score-practice-protected-smoke.md`.

## Verification

- Full pytest: `934 passed`.
- Core JavaScript syntax: passed for answer client, Melody Studio, and fretboard component.
- `git diff --check`: passed.
- Local browser smoke: pass for all six cards, flagged catalog/import, score editing, VexFlow, Amazing Grace catalog, exact E9 route, ornament toggle, and mobile layout.
- Protected browser smoke: pass at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-score-practice-74520ca-20260711`.
- Protected browser verified manual phrase and lead-sheet builder lesson generation, six routes, synchronized staff/fretboard/tab, VexFlow renderer, zero page overflow, and no `[object Object]` or console errors.
- Resumed header smoke verified the removed practice kicker, metadata line, and More arrangements disclosure remain absent on the integrated runtime; all six routes remain together in one horizontally scrollable row and Chord melody selection synchronizes visibly.

## Protected preview

- Runtime smoke HEAD: `74520ca`.
- Loopback `/api/version`: `74520ca`, `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, `features.melodyExercise=true`; `melodyImport` remains default off.
- Preview refresh succeeded without `sudo` by terminating only the user-owned port-8770 listener and allowing the installed LaunchDaemon to restart it.
- Installed wrapper matches the committed wrapper.
- Cloudflare Access login and protected manual/score lesson generation succeeded; the prior arranger blocker is closed.
- Loopback root redirects to `/ui/steel-guitar-rag-mock.html`; home and Melody Studio routes return 200; anonymous answer calls remain 401.
- The authenticated protected root redirects to the canonical home route; use the exact direct cache-busted Melody Studio URL for user smoke.
- API fallback is not browser smoke; authenticated browser behavior was verified at the direct Studio URL.

## Dirty worktree

- Unrelated tracked and untracked corpus/source/pipeline/landing-asset work remains parked.
- Protected/generated groups, corpus/vector stores, source-inbox raw/provenance, private material, and unrelated assets were not staged, deleted, reset, or cleaned.

## Next action

1. Continue user smoke at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-score-practice-74520ca-20260711`.
2. If protected catalog/upload import should be enabled, explicitly authorize the protected environment flag change and vision-model readiness check; otherwise keep it off.
3. Keep unrelated corpus, source-inbox, private-data, brand/design, deployment, and environment work parked.
