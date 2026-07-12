# Integration Status — Current Snapshot

Updated: 2026-07-12 09:03 America/Chicago

## Repository state

- Branch: `feature/answer-api`
- Current implementation: `03a372e fix: simplify Melody Studio lesson layout`
- Melody API baseline: `f37201a feat: add Melody Exercise teaching workflow`
- Melody Studio now uses Steel Guitar RAG branding. No broad repository rename is approved.

## Melody Studio

Status: **SIMPLIFIED LESSON RESULT READY FOR USER SMOKE — Melody Studio is 936-test green and authenticated-preview verified with the 12-song book plus a compact, fretboard-first result layout.**

- The home header now exposes feature-gated actions in this order: Explore Fretboard, Melody Studio, Backstage.
- The technical inline Melody form was removed from home.
- `/ui/melody-workbench.html` opens with one Add a melody workspace and three compact entry paths: Type or tap notes, Record or upload audio, and Import music when enabled.
- Staff notation, recording attribution, and the built-in songbook are contextual actions rather than equal top-level choices. User file/image/MusicXML/MIDI import remains hidden unless its separate session feature is enabled.
- Quick entry shows notes/scale numbers, one note-button row, the resolved phrase, G/C, and one Arrange for E9 action. Contour, literal-tab help, and practice starters are under Phrase options.
- A populated draft changes alternate paths to Replace melody and requires an inline Replace melody / Keep editing decision before session content is cleared.
- Successful audio, import, and catalog adapters open the shared staff in Review melody. Edit melody returns to the correct populated editor; Start over clears the session draft.
- The original note/degree/literal-E9 phrase editor remains intact and is the default input.
- The lead-sheet builder supports one treble melody voice, G/C, 3/4 and 4/4, pickup, supported note/rest durations, ties, accidentals, chord symbols, lyrics/labels, undo/redo, measure actions, duplicate, transpose, browser playback, and local MusicXML download.
- Melody pitch and chord symbols are separate: melody-only input shows no invented chord labels, while supplied harmony appears only at actual changes.
- The score is an interactive practice surface with synchronized staff/fretboard/navigator/tab selection, adjustable tempo, count-in, pause/resume, stop, measure and selected-note loops, and conditional chord backing when real chord symbols are present.
- Arrangement route switching now changes the musical score as well as the fretboard and tab: Faithful melody shows one note head, harmonized routes show two stacked note heads, and Chord melody shows every validated grip pitch while retaining the melody as the top voice.
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
- The built-in songbook now contains 12 reviewed public-domain teaching phrases: Amazing Grace, Oh! Susanna, Aura Lee, Buffalo Gals, Skip to My Lou, She’ll Be Coming ’Round the Mountain, When the Saints Go Marching In, Red River Valley, Shenandoah, My Bonnie Lies over the Ocean, Yankee Doodle, and Camptown Races.
- `Browse songbook (12)` opens title/attribution search plus difficulty, meter, and feel filters. Cards show tune/version, G/C key, meter, difficulty, feel, note/section count, and attribution before opening the shared Review melody staff.
- Built-in songs are advertised through `features.melodyCatalog=true` whenever Melody Exercise is enabled. Catalog listing/opening no longer requires the broader `melodyImport` flag; uploads and file imports remain gated and disabled on the protected preview.
- Catalog teaching phrases are labeled interpretive and sourced for provenance; they do not claim note-for-note fidelity to a particular commercial or historical performance.
- Results are fretboard-first. Every mechanically available single-note, Recommended Harmony, thirds, sixths, and chord-melody route appears in one visible, horizontally scrollable row directly below the fretboard.
- The lesson header omits the generic Practice the lesson kicker and the non-actionable exactness/confidence/single-section metadata line.
- One scalable navigator shows a single active note between Previous/Next arrows with `Note N of M`, resolved pitch, and readable steel position text such as `Strings 5, 6 & 7 · Fret 10 · A+B`; it does not create one technical pill per phrase event.
- Route and arrow controls visibly synchronize the selected fretboard position, fixed-width tab route, pedal/lever instructions, and movement cue.
- The duplicated active-tab sentence and verbose event-detail sentence have been removed.
- Melody Studio hides the Explorer-oriented position-card strip, filters, legend, and full technical inspector. The single active-note navigator now states the note, string(s), fret, controls, and movement cue without a duplicate Current note block.
- Melody tab omits artificial `Ly | step N` rows. Event selectors spell out string, fret, and pedal/lever positions, and the primary harmony route is labeled `Recommended harmony` without duplication.
- A default-off, user-toggleable scientific-octave map colors accurate octave zones independently along every E9 string; it does not pretend that one fret-wide band represents one octave across all strings.
- The compact octave 2–6 legend sits directly beside the Octave colors control and remains hidden until enabled. Exact fretboard note markers and the active event share the same palette; harmony retains the top melody voice's octave label while each displayed harmony marker uses its own exact octave.
- Melody-only results hide chord playback. When real chord symbols are supplied, the practice bar labels the option `Play chord backing`; it is unrelated to the treble-clef display.
- Note-duration editing remains available for faithful rhythm and playback but is progressive: new-note length is under Score setup and selected-note length is under Selected note details.
- The redundant deterministic implementation explanation has been removed from the result.
- Print score has been removed. A compact **Print** action now sits beside Start over directly below the tablature and produces a landscape sheet with title, optional source, selected arrangement, and fixed-width current-route tab while hiding the staff, fretboard, controls, and editor.
- The introductory phrase-to-E9 hero is hidden after a lesson is generated; the compact Melody Studio header remains. Edit melody is prominent beside the lesson title and remains available after the tablature.
- Octave colors, String labels, and Note labels sit immediately below the fretboard, before arrangement choices. Non-actionable route-recommendation prose is no longer rendered.
- Loop controls are grouped into one closed, horizontally contained Loop options disclosure for eight-event sections and are omitted for shorter sections.
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
Lesson-focus implementation handoff: `docs/handoffs/task-completions/2026-07-11-2314-06-melody-lesson-focus-adjustment.md`.
Lesson-focus protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-2318-12-melody-lesson-focus-protected-smoke.md`.
Route-score synchronization implementation handoff: `docs/handoffs/task-completions/2026-07-11-2325-06-melody-route-score-sync-fix.md`.
Route-score synchronization protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-2329-12-melody-route-score-sync-protected-smoke.md`.
Print-tablature implementation handoff: `docs/handoffs/task-completions/2026-07-11-2334-06-melody-print-tablature-adjustment.md`.
Print-tablature protected-smoke handoff: `docs/handoffs/task-completions/2026-07-11-2336-12-melody-print-tablature-protected-smoke.md`.
Songbook implementation handoff: `docs/handoffs/task-completions/2026-07-12-0847-01-public-domain-songbook-implementation.md`.
Songbook protected-smoke handoff: `docs/handoffs/task-completions/2026-07-12-0852-12-public-domain-songbook-protected-smoke.md`.
Result-layout adjustment handoff: `docs/handoffs/task-completions/2026-07-12-0900-06-melody-result-layout-user-smoke-adjustment.md`.
Result-layout protected-smoke handoff: `docs/handoffs/task-completions/2026-07-12-0903-12-melody-result-layout-protected-smoke.md`.

## Verification

- Full pytest: `936 passed`.
- Core JavaScript syntax: passed for answer client, Melody Studio, and fretboard component.
- `git diff --check`: passed.
- Local browser smoke: pass for a twelve-note sectioned phrase, six arrangement routes, one active-note navigator, octave toggle/legend, melody-only chord-backing suppression, mobile containment, and clean browser logs.
- Protected browser smoke: pass at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-print-tab-5007011-20260711`.
- Protected browser verified manual phrase and lead-sheet builder lesson generation, six routes, synchronized staff/fretboard/tab, VexFlow renderer, zero page overflow, and no `[object Object]` or console errors.
- Active-fretboard protected smoke verified D4-to-E4 marker replacement, independent string/note/octave controls, and an active chord-melody grip limited to strings 5, 6, and 8 with one D4 top-voice label.
- String/action-label protected smoke verified a literal `S6:3B` event renders `6B` inside the active marker while Current note reports String 6, fret 3, B pedal.
- User smoke passed on the same `c850411` protected build; the Melody Studio smoke freeze is complete.
- Audio-transcription protected smoke verified the signed-in recording/upload workspace, tempo and format controls, final controller asset, session-only privacy copy, zero overflow, and no object-string rendering. Real microphone/file selection is the pending user-smoke boundary.
- Lead-sheet repair protected smoke verified explicit A4/G4 selection navigation, a visible overfull-measure warning that does not disable arrangement, successful advancement to six E9 routes, and longer-file window controls.
- Score-edit-controls protected smoke verified visible and keyboard deletion of only the selected event, whole-score B4-to-B5 octave movement, successful raised-phrase E9 arrangement, and a clean browser console.
- Add-a-melody UX protected smoke verified typed-phrase entry, reversible inline replacement, successful E9 arrangement, populated Edit melody return, progressive staff disclosures, clean controller caching, and no browser errors.
- Lesson-focus protected smoke verified a twelve-note sectioned phrase, one readable active-note card, six routes below the fretboard, default-off adjacent octave legend, conditional chord-backing suppression, removed deterministic copy, and clean navigation/browser logs.
- Route-score synchronization protected smoke verified one, two, and three stacked note heads for Faithful melody, Recommended harmony, and Chord melody respectively, with exact pitch labels, preserved top melody voice, synchronized fretboard/tab, and clean browser logs.
- Print-tablature protected smoke verified the unique Print tablature action, absence of Print score, current Recommended harmony route label/tab, parsed landscape print CSS, score/control suppression, and clean browser logs. Native print preview remains the user-smoke boundary.
- Resumed header smoke verified the removed practice kicker, metadata line, and More arrangements disclosure remain absent on the integrated runtime; all six routes remain together in one horizontally scrollable row and Chord melody selection synchronizes visibly.
- Songbook protected smoke verified all 12 cards, search/filter metadata, a one-result Shenandoah search, 16-event staff review, authenticated catalog opening, Section 1 E9 arrangement, six routes, source attribution, Print tablature, Continue to Section 2, and zero browser errors.
- Result-layout protected smoke verified the hidden result hero, top and bottom Edit melody actions, fretboard-adjacent display controls, closed eight-event Loop options, removed route prose, bottom-row Print/Start over placement, synchronized lesson surfaces, and zero browser errors. Local smoke separately verified that a seven-note section omits Loop options entirely.

## Protected preview

- Runtime smoke HEAD: `03a372e`.
- Loopback `/api/version`: `03a372e`, `feature/answer-api`, `hybrid_private_first`, `cloudflare_access`, `features.melodyExercise=true`, `features.melodyCatalog=true`; user uploads/imports remain separately disabled.
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

1. User smoke at `https://app.steelguitarrag.com/ui/melody-workbench.html?v=melody-result-layout-03a372e-20260712`: confirm the simplified lesson hierarchy, Edit melody placement, fretboard display controls, loop disclosure behavior, and bottom-row Print action.
2. If protected score-image/file import should be enabled later, explicitly authorize the protected environment flag change and vision-model readiness check; otherwise keep it off.
3. Keep unrelated corpus, source-inbox, private-data, brand/design, deployment, and environment work parked.
