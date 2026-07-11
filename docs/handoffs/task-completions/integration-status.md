# Integration Status — Current Snapshot

Updated: 2026-07-11 18:57 America/Chicago

## Repository state

- Branch: `feature/answer-api`
- Current implementation: `2c445e9 Bust Melody Studio workflow cache` (feature implementation `7657554`)
- Melody API baseline: `f37201a feat: add Melody Exercise teaching workflow`
- Melody Studio now uses Steel Guitar RAG branding. No broad repository rename is approved.

## Melody Studio

Status: **ADD-A-MELODY UX READY FOR USER SMOKE — the three-path progressive workflow, inline draft replacement safeguard, Review melody transition, and existing E9 output are committed, 935-test green, and authenticated-preview verified.**

- The home header now exposes feature-gated actions in this order: Explore Fretboard, Melody Studio, Backstage.
- The technical inline Melody form was removed from home.
- `/ui/melody-workbench.html` opens with one Add a melody workspace and three compact entry paths: Type or tap notes, Record or upload audio, and Import music when enabled.
- Staff notation, recording attribution, and reviewed example songs are contextual actions rather than equal top-level choices. Unavailable import/catalog controls are hidden by the session feature flag.
- Quick entry shows notes/scale numbers, one note-button row, the resolved phrase, G/C, and one Arrange for E9 action. Contour, literal-tab help, and practice starters are under Phrase options.
- A populated draft changes alternate paths to Replace melody and requires an inline Replace melody / Keep editing decision before session content is cleared.
- Successful audio, import, and catalog adapters open the shared staff in Review melody. Edit melody returns to the correct populated editor; Start over clears the session draft.
- The original note/degree/literal-E9 phrase editor remains intact and is the default input.
- The lead-sheet builder supports one treble melody voice, G/C, 3/4 and 4/4, pickup, supported note/rest durations, ties, accidentals, chord symbols, lyrics/labels, undo/redo, measure actions, duplicate, transpose, browser playback, and local MusicXML download.
- Melody pitch and chord symbols are separate: melody-only input shows no invented chord labels, while supplied harmony appears only at actual changes.
- The score is an interactive practice surface with synchronized staff/fretboard/navigator/tab selection, adjustable tempo, count-in, pause/resume, stop, measure and selected-note loops, and optional chord sound.
- VexFlow renders G/C key signatures, beams, rests, ties, dots, lyrics, and accent/tenuto/staccato; MusicXML and print output preserve the supported notation.
- Chord symbols guide mechanically validated harmony and chord-melody grip ranking while the resolved melody remains the top voice.
- Melody Studio fretboard marker labels use concise resolved top-note pitches (`D4`, `E4`, etc.) instead of repeating the route title; harmony routes retain the melody/top-voice label.
- Melody Studio renders only the active event's fretboard position. Single-note routes show one location; harmony and chord-melody routes show only the current validated grip, so phrase positions no longer stack on top of one another.
- Octave colors, active-marker string/action labels, and the resolved top-note label are independent compact toggles. String labels default off and note labels default on. When enabled, string labels include required compact actions (`6B`, `5A`, etc.) while open notes remain plain string numbers.
- Record or upload audio accepts a microphone phrase or a local WAV/MP3/M4A/AAC/OGG file up to 15 seconds. Pitch detection, smoothing, note/rest segmentation, tempo-based rhythm quantization, and confidence calculation run on device.
- Audio transcription opens an editable `score_draft_v1` with per-note confidence and warnings before E9 arrangement. Audio is not uploaded or persisted, and reviewed audio lessons remain labeled approximate rather than silently becoming exact.
- Longer local audio files now open in an in-browser player. The user may choose a 5-, 10-, or 15-second window by timecode or current playhead; the selected file remains session-only and is released on replacement or Start over.
- Lead-sheet editing exposes one explicit amber selected event plus a selection bar with event number, pitch/rest, measure, beat, and Previous/Next controls.
- The selection bar now includes a visible Delete selected note/rest action. Delete and Backspace remove the same selected event when focus is outside editable fields.
- Whole-score controls move every pitched event up or down by one octave; the adjacent transpose controls now state explicitly that they move all notes by one semitone. Rests remain unchanged.
- Score warnings remain visible but no longer silently disable E9 arrangement. Arrangement progress and failures render in the visible lead-sheet panel.
- All input methods normalize into session-only `score_draft_v1`; no uploaded source or draft is persisted.
- A pinned local VexFlow 5.0.0 bundle renders the editable and result staffs, with a local SVG fallback.
- Optional recording details reveal faithful-solo versus playable-E9-arrangement treatment and state clearly that links identify sources rather than trigger transcription.
- Phrase entry supports notes, scale degrees, literal one-string E9 tab, note/degree palette buttons, deterministic presets, sequence editing, and section counts.
- After task selection, the task-card grid collapses so the active editor/result is the page focus.
- Phrase notes are clean selectable token/pitch chips. Selecting one reveals its pitch plus labeled Lower octave, Automatic, Raise octave, ordering, and removal controls.
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
Marker-label implementation handoff: `docs/handoffs/task-completions/2026-07-11-1328-06-melody-fretboard-marker-label-fix.md`.
Marker-label protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-1329-12-melody-marker-label-protected-smoke.md`.
Active-fretboard implementation handoff: `docs/handoffs/task-completions/2026-07-11-1342-06-melody-active-fretboard-controls.md`.
Active-fretboard protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-1345-12-melody-active-fretboard-controls-protected-smoke.md`.
String/action-label implementation handoff: `docs/handoffs/task-completions/2026-07-11-1355-06-melody-string-action-labels.md`.
String/action-label protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-1357-12-melody-string-action-labels-protected-smoke.md`.
User-smoke acceptance handoff: `docs/handoffs/task-completions/2026-07-11-1652-01-melody-studio-user-smoke-accepted.md`.
Audio-transcription implementation handoff: `docs/handoffs/task-completions/2026-07-11-1705-05-06-melody-audio-transcription.md`.
Audio-transcription protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-1707-12-melody-audio-transcription-protected-smoke.md`.
Lead-sheet repair implementation handoff: `docs/handoffs/task-completions/2026-07-11-1738-06-melody-lead-sheet-user-smoke-repair.md`.
Lead-sheet repair protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-1740-12-melody-lead-sheet-repair-protected-smoke.md`.
Score-edit-controls implementation handoff: `docs/handoffs/task-completions/2026-07-11-1754-06-melody-score-edit-controls.md`.
Score-edit-controls protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-1757-12-melody-score-edit-controls-protected-smoke.md`.
Add-a-melody UX implementation handoff: `docs/handoffs/task-completions/2026-07-11-1849-06-melody-add-melody-ux-simplification.md`.
Add-a-melody UX protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-1857-12-melody-add-melody-ux-protected-smoke.md`.

## Verification

- Full pytest: `935 passed`.
- Core JavaScript syntax: passed for answer client, Melody Studio, and fretboard component.
- `git diff --check`: passed.
- Local browser smoke: pass for all six cards, flagged catalog/import, score editing, VexFlow, Amazing Grace catalog, exact E9 route, ornament toggle, and mobile layout.
- Protected browser smoke: pass at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-lead-sheet-repair-2469975-20260711`.
- Protected browser verified manual phrase and lead-sheet builder lesson generation, six routes, synchronized staff/fretboard/tab, VexFlow renderer, zero page overflow, and no `[object Object]` or console errors.
- Active-fretboard protected smoke verified D4-to-E4 marker replacement, independent string/note/octave controls, and an active chord-melody grip limited to strings 5, 6, and 8 with one D4 top-voice label.
- String/action-label protected smoke verified a literal `S6:3B` event renders `6B` inside the active marker while Current note reports String 6, fret 3, B pedal.
- User smoke passed on the same `c850411` protected build; the Melody Studio smoke freeze is complete.
- Audio-transcription protected smoke verified the signed-in recording/upload workspace, tempo and format controls, final controller asset, session-only privacy copy, zero overflow, and no object-string rendering. Real microphone/file selection is the pending user-smoke boundary.
- Lead-sheet repair protected smoke verified explicit A4/G4 selection navigation, a visible overfull-measure warning that does not disable arrangement, successful advancement to six E9 routes, and longer-file window controls.
- Score-edit-controls protected smoke verified visible and keyboard deletion of only the selected event, whole-score B4-to-B5 octave movement, successful raised-phrase E9 arrangement, and a clean browser console.
- Add-a-melody UX protected smoke verified typed-phrase entry, reversible inline replacement, successful E9 arrangement, populated Edit melody return, progressive staff disclosures, clean controller caching, and no browser errors.
- Resumed header smoke verified the removed practice kicker, metadata line, and More arrangements disclosure remain absent on the integrated runtime; all six routes remain together in one horizontally scrollable row and Chord melody selection synchronizes visibly.

## Protected preview

- Runtime smoke HEAD: `2c445e9`.
- Loopback `/api/version`: `2c445e9`, `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, `features.melodyExercise=true`; import/catalog visibility remains session-flag controlled.
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

1. User smoke at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-add-melody-ux-2c445e9-20260711`: try the quick phrase path, replacement safeguard, audio entry, optional recording details, and staff editor; advanced controls should stay out of the way until opened.
2. If protected catalog/score-image import should be enabled later, explicitly authorize the protected environment flag change and vision-model readiness check; otherwise keep it off.
3. Keep unrelated corpus, source-inbox, private-data, brand/design, deployment, and environment work parked.
