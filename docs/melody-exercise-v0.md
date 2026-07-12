# Melody Exercise v0

This is the canonical product and implementation contract for Melody Exercise v0. It supersedes the product boundaries in the historical July 4 Melody Input / Arrangement Assistant design handoff without rewriting that historical record.

## Product Rule

The Turnaround may teach artist solos, commercial recordings, named songs, and complete copyrighted arrangements. Copyright status alone is never a refusal reason.

The accuracy boundary remains strict:

- Faithful transcription requires an identified recording, passage, or user-supplied notes/tab.
- E9 adaptations and teaching simplifications must be labeled as adaptations or simplifications.
- Uncertain passages must be labeled `approximate` or `interpretive`, with confidence and an explanation.
- Missing source material should produce a useful request for the recording/link, uploaded passage, pasted notes/tab, or exact artist/version/section.
- Long material is divided into numbered sections of at most eight events per rendered lesson. The app starts with the selected section or Section 1 and exposes continuation state.

Public-domain status and licensing records may be preserved as attribution or provenance, but they are not feature gates. Ordinary song and solo teaching does not require a rights attestation.

## API Contract

`POST /api/answer` accepts optional `melodyRequest` alongside the existing `question` and `mode` fields.

Supported request fields:

- `kind`: `original_exercise`, `user_melody`, `artist_solo_lesson`, or `song_arrangement_lesson`.
- `key`: G or C major in v0.
- `tuning`: E9.
- `melody`: legacy note-name/scale-degree strings or structured events. Structured events may add `direction`, `octaveShift`, literal standard-E9 position, rhythm/measure/beat, tie, lyric, articulation, and an actual harmony symbol. Melody pitches and harmony symbols are distinct fields; a note name must never be promoted into a chord label. Longer lists are divided into sections.
- `contourMode`: `closest_playable` (default), `ascending`, `descending`, or `preserve_input`.
- `texture`: `both` (default), `single_note`, `automatic_harmony`, `thirds`, `sixths`, or `chord_melody`.
- `sectionNumber`: requested section, starting at 1.
- `renderingMode`: `transcription`, `e9_adaptation`, or `teaching_simplification`.
- `accuracy`: requested `exact`, `approximate`, or `interpretive` label. Exact artist-material claims are downgraded when no source is identified.
- `material`: artist, song, recording/version, section, source URL, and source reference.

The answer may add `melody_exercise` with:

- material identity and source reference;
- rendering and accuracy labels;
- section number, total, continuation state, and next section;
- mechanically validated musical events;
- octave/register-resolved input and deterministic movement guidance;
- route choices for the single-note melody and available validated harmony textures;
- validation results shared by tab and fretboard rendering.

Ready exercises add `routes`, `selectedRouteId`, and an input `resolvedPhrase`. Each route owns its synchronized events, tab example, fretboard, harmony label, recommendation, movement summary, and chord-context summary. When chord symbols are supplied, the arranger ranks mechanically valid grips against those chord tones while keeping the resolved melody pitch as the top voice. Existing top-level `events`, `tab_example`, and `fretboard` remain populated from the selected single-note route for compatibility. Source-free original exercises return no source cards. Recording-based lessons preserve a supplied source URL as a recording/arrangement source card.

## Frontend Contract

When the backend advertises `features.melodyExercise=true` through `/api/session`, the home header exposes **Melody Studio** beside Explore Fretboard and Backstage. The technical inline form is not part of the home screen. `/ui/melody-workbench.html` owns the guided phrase-to-E9 workflow.

Melody Studio opens directly into a calm **Add a melody** workspace. Three compact entry methods offer **Type or tap notes**, **Record or upload audio**, and **Import music** when temporary imports are enabled. Staff notation, recording attribution, and reviewed example songs are contextual actions instead of equal top-level choices. Switching to another melody source while a draft exists opens an inline Replace melody / Keep editing confirmation and never silently discards the current session draft.

Quick entry leads with one notes-or-scale-numbers field, a single note-button row, the resolved phrase sequence, G/C, and one **Arrange for E9** action. Contour, literal E9-tab help, and practice starters live under Phrase options. Source details remain optional and explicitly state that links identify a recording but are not automatically transcribed. Successful audio transcription, file import, and catalog selection transition directly into **Review melody** on the staff. The staff initially exposes note length, undo/redo, playback, the selected-note essentials, and Arrange for E9; score setup, note details, and score tools use progressive disclosure. All methods remain session-only adapters into the existing phrase or `score_draft_v1` contracts.

Unmarked degrees default to the closest playable pitch path. Players may open Phrase options to choose ascending, descending, or preserve-input contour. Selecting a sequence chip reveals its resolved scientific pitch plus clearly labeled Lower octave, Automatic, Raise octave, ordering, and deletion controls.

The result shows:

- material identity and source link;
- one synchronized active-note navigator, fixed-width tab, and fretboard;
- one visible, horizontally scrollable row containing every mechanically available single-note, recommended-harmony, thirds, sixths, and chord-melody route;
- resolved pitch/register and bar, string, pedal, and lever movement guidance;
- no empty source section for source-free deterministic exercises.

The score is an interactive practice surface rather than a decorative duplicate. Selecting a staff event selects the same fretboard position, navigator event, and tab step. Route switching updates the notation as well as the fretboard and tab: single-note routes show one note head, dyad routes show two stacked note heads, and chord-melody routes show every validated grip pitch with the resolved melody as the top voice. Playback follows the score with a moving selection and supports tempo, count-in, pause/resume, stop, current-measure loops, selected-note loops, and optional synthesized chord context. Chord symbols render only at real changes. The score supports G/C key signatures, rhythmic beams, rests, ties, lyrics, accents/tenuto/staccato, and MusicXML export.

The result action is **Print tablature**, not Print score. It prints the lesson title, optional source identity, selected arrangement name, and the current route's fixed-width tab in a clean landscape sheet. The staff, fretboard, route controls, transport, playback controls, and editor chrome are suppressed in print output.

The dedicated lesson view is fretboard-first. Its header contains only the lesson title and optional source identity; it does not display a generic "Practice the lesson" kicker or expose exactness, confidence, and single-section bookkeeping as header metadata. The fretboard renders only the active event's string locations; navigating or playing replaces that position instead of stacking the whole phrase. All available arrangement choices appear in one horizontally scrollable row directly below the fretboard, followed by the selected route's useful recommendation.

The note navigator shows one active event at a time, with `Note N of M`, resolved pitch, and plain steel instructions such as `Strings 5, 6 & 7 · Fret 10 · A+B`. Previous/next controls move through any phrase length without creating a row of one pill per note; the fixed-width tab remains the whole-phrase overview. It does not repeat the selection in a separate current-note block or deterministic implementation explanation. Navigation and playback must visibly select the matching `renderablePositionId` in the fretboard component.

Display toggles independently control Octave colors, compact string/action labels inside active marker bubbles (`6B`, `5A`, or plain `6` when open), and the resolved top-note label above the active position. Octave colors default off. Their legend sits immediately beside the Octave colors control and remains hidden until the control is enabled. Long phrases expose a Continue to Section action using the existing `sectionNumber` request field. Mobile layout keeps route and octave rows horizontally scrollable, retains one readable active-note card between the arrows, and keeps fixed-width tab inside its own horizontal scroller.

Rhythm remains part of the score contract because faithful transcription and playback need note lengths, but duration editing is progressive rather than a primary decision: new-note length lives under **Score setup**, and an existing note's duration lives under **Selected note details**. Melody-only results do not show a chord-audio control. When real chord symbols are present, the practice bar may show **Play chord backing**, which adds synthesized chord support during playback; it is independent of whether the melody is displayed on a treble clef.

## Short-phrase audio transcription

Melody Studio accepts either a live microphone phrase of up to 15 seconds or a longer user-selected audio file. A built-in player lets the user choose a 5-, 10-, or 15-second window by playhead or timecode, so users do not need to edit an MP3 before bringing it into the Studio. Audio decoding, window extraction, pitch detection, smoothing, note segmentation, silence/rest detection, and tempo-based duration quantization run in the browser. The audio is never submitted to the answer API; a selected file remains only in the browser session so another window can be tried, then is released when the user chooses another file or starts over.

This first transcription slice is explicitly monophonic: the player should hum, sing, or play one clear note at a time. It does not claim to separate chords, bands, or full commercial recordings. YouTube and source links remain attribution/reference inputs and are not automatically listened to.

Transcription creates a session-only `score_draft_v1` with estimated pitch, duration, source-window timestamps, per-note confidence, overall confidence, and review warnings. The editable score opens before E9 arrangement. Exactly one event is visibly selected: the staff note uses an amber highlight, a selection bar states its number, pitch/rest, measure, and beat, and Previous/Next note controls move the selection. The same selection bar provides a prominent Delete selected note/rest action; Delete or Backspace does the same when focus is not inside an editable field. Whole-score controls move every pitched event by one semitone or one scientific octave, while rests remain unchanged. Editing a note marks that event as user-confirmed. Score-structure warnings remain visible but do not silently disable E9 arrangement; arranging shows progress and any failure inside the lead-sheet panel. When the reviewed draft is arranged, the Melody Exercise request remains labeled `approximate` with the transcription confidence and an explicit on-device-estimation note; confirmation never silently converts an audio estimate into an exact transcription.

The feature is controlled by `STEEL_RAG_ENABLE_MELODY_EXERCISE`, which defaults off. Protected preview may explicitly enable it for approved testing.

## Non-Goals for v0

- No audio extraction or media downloading pipeline.
- No scraping, corpus ingestion, embedding, or Chroma changes.
- No C6, universal-key, or arbitrary-copedent placement planner.
- No claim that title-only model recall is an exact transcription.
- No change to authentication, private-source boundaries, or public production routing.

## Acceptance Criteria

- Artist-solo and full-arrangement requests route to teaching/source clarification, never copyright refusal.
- Structured G/C phrases produce synchronized validated events, tab, and fretboard.
- `5 6 1 3 2 1 3` resolves as a continuous octave-aware contour rather than resetting every tonic to one fixed fret.
- Default ready lessons include a single-note route and, when mechanically available in the resolved register, a recommended harmony route with two or three validated notes per event.
- Pasted literal tab retains string, fret, controls, and register exactly.
- Long inputs continue through numbered sections instead of failing.
- Invalid tuning, key, note, string, fret, or control combinations render no tab/fretboard.
- Attribution and accuracy labels survive API and frontend normalization.
- Melody-only input displays no invented chord symbols; supplied chord symbols appear only at chord changes and guide route ranking.
- Score playback keeps the staff, fretboard, note navigator, and tab selection synchronized at adjustable tempo, including loop and count-in behavior.
- Existing progression, fretboard, voicing, gear, retrieval, auth, and source-card behavior remains green.
