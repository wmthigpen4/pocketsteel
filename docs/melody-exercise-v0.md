# Melody Exercise v0

This is the canonical product and implementation contract for Melody Exercise v0. It supersedes the product boundaries in the historical July 4 Melody Input / Arrangement Assistant design handoff without rewriting that historical record.

## Product Rule

The Turnaround may teach artist solos, commercial recordings, named songs, and complete copyrighted arrangements. Copyright status alone is never a refusal reason.

The accuracy boundary remains strict:

- Faithful transcription requires an identified recording, passage, or user-supplied notes/tab.
- E9 adaptations and teaching simplifications must be labeled as adaptations or simplifications.
- Uncertain passages must be labeled `approximate` or `interpretive`, with confidence and an explanation.
- Missing source material should produce a useful request for the recording/link, uploaded passage, pasted notes/tab, or exact artist/version/section.
- Reviewed songbook material is rendered as one continuous complete-song lesson so the full score, tablature, playback, and loop controls share the same timeline. Manual note lists and non-catalog requests may still use labeled sections, with a 16-event fallback when no measure data exists.

Public-domain status and licensing records may be preserved as attribution or provenance, but they are not feature gates. Ordinary song and solo teaching does not require a rights attestation.

## API Contract

`POST /api/answer` accepts optional `melodyRequest` alongside the existing `question` and `mode` fields.

Supported request fields:

- `kind`: `original_exercise`, `user_melody`, `artist_solo_lesson`, or `song_arrangement_lesson`.
- `key`: G or C major in v0.
- `tuning`: E9.
- `melody`: legacy note-name/scale-degree strings or structured events. Structured events may add `direction`, `octaveShift`, literal standard-E9 position, rhythm/measure/beat, tie, lyric, articulation, and an actual harmony symbol. Melody pitches and harmony symbols are distinct fields; a note name must never be promoted into a chord label. Longer lists are divided into sections.
- `meter` and `pickupBeats`: optional score context used to distinguish pickups, passing tones, arrivals, and cadences. They do not change the entered pitches or source rhythm.
- `contourMode`: `closest_playable` (default), `ascending`, `descending`, or `preserve_input`.
- `texture`: `both` (default), `single_note`, `mixed_arrangement`, `automatic_harmony`, `thirds`, `sixths`, or `chord_melody`. The legacy `automatic_harmony` request remains supported, while the default route set uses the mixed arrangement.
- `sectionNumber`: requested section, starting at 1.
- `sections`: optional reviewed phrase labels with `startMeasure` and `endMeasure`, retained as internal form metadata.
- `wholeSong`: optional boolean. When true, every supplied melody event is arranged in one continuous lesson and the response has one `Complete song` section.
- `renderingMode`: `transcription`, `e9_adaptation`, or `teaching_simplification`.
- `accuracy`: requested `exact`, `approximate`, or `interpretive` label. Exact artist-material claims are downgraded when no source is identified.
- `material`: artist, song, recording/version, section, source URL, and source reference.

The answer may add `melody_exercise` with:

- material identity and source reference;
- rendering and accuracy labels;
- phrase label, section number, total, previous/next continuation state, event range, and measure range;
- mechanically validated musical events;
- octave/register-resolved input and deterministic movement guidance;
- route choices for the faithful melody, recommended mixed performance arrangement, and available validated fixed harmony textures;
- pocket-first mixed-route events with arrangement role, performance-control posture, harmonic-pattern family, canonical grip, and an optional concise selection reason;
- route-level path summaries for bar travel, harmonic-family changes, string-group changes, and pedal-family changes;
- mixed-route texture counts and sparse mechanically validated bar/pedal/lever transitions that do not alter source notes or rhythm;
- validation results shared by tab and fretboard rendering.

Ready exercises add `routes`, `selectedRouteId`, and an input `resolvedPhrase`. Each route owns its synchronized events, tab example, fretboard, harmony label, recommendation, movement summary, path summary, and chord-context summary. When chord symbols are supplied, the arranger keeps the resolved melody pitch and register as the top voice, requires supporting voices to fit the active chord, and prefers one familiar harmonized-scale pocket over isolated locally convenient grips. `performanceControls` describes the pedals and levers the player holds; individual note `changes` continue to name only controls that affect that string. Existing top-level `events`, `tab_example`, and `fretboard` remain populated from the selected single-note route for compatibility. Source-free original exercises return no source cards. Recording-based lessons preserve a supplied source URL as a recording/arrangement source card.

## Frontend Contract

When the backend advertises `features.melodyExercise=true` through `/api/session`, the home header exposes **Melody Studio** beside Explore Fretboard and Backstage. The technical inline form is not part of the home screen. `/ui/melody-workbench.html` owns the guided phrase-to-E9 workflow.

Melody Studio opens directly into a calm **Add a melody** workspace. Three compact entry methods offer **Type or tap notes**, **Record or upload audio**, and **Import music** when temporary imports are enabled. Staff notation, recording attribution, and reviewed example songs are contextual actions instead of equal top-level choices. Switching to another melody source while a draft exists opens an inline Replace melody / Keep editing confirmation and never silently discards the current session draft.

Quick entry leads with one notes-or-scale-numbers field, a single note-button row, the resolved phrase sequence, G/C, and one **Arrange for E9** action. Contour, literal E9-tab help, and practice starters live under Phrase options. Source details remain optional and explicitly state that links identify a recording but are not automatically transcribed. Successful audio transcription, file import, and catalog selection transition directly into **Review melody** on the staff. The staff initially exposes note length, undo/redo, playback, the selected-note essentials, and Arrange for E9; score setup, note details, and score tools use progressive disclosure. All methods remain session-only adapters into the existing phrase or `score_draft_v1` contracts.

Unmarked degrees default to the closest playable pitch path. Players may open Phrase options to choose ascending, descending, or preserve-input contour. Selecting a sequence chip reveals its resolved scientific pitch plus clearly labeled Lower octave, Automatic, Raise octave, ordering, and deletion controls.

The result shows:

- material identity and source link;
- one synchronized active-note navigator, fixed-width tab, and fretboard;
- one visible, horizontally scrollable row containing Faithful melody, Recommended arrangement, thirds, sixths, and chord melody when mechanically and harmonically available;
- resolved pitch/register and bar, string, pedal, and lever movement guidance;
- no empty source section for source-free deterministic exercises.

The score is an interactive practice surface rather than a decorative duplicate. Selecting a staff event selects the same fretboard position, navigator event, and tab step. Route switching updates the notation as well as the fretboard and tab: single-note routes show one note head, dyad routes show two stacked note heads, and chord-melody routes show every validated grip pitch with the resolved melody as the top voice. Playback follows the score with a moving selection and supports tempo, count-in, pause/resume, stop, current-measure loops, selected-note loops, and optional synthesized chord context. Loop controls stay collapsed by default and are omitted for sections shorter than eight events. Chord symbols render only at real changes. The score supports G/C key signatures, rhythmic beams, rests, ties, lyrics, accents/tenuto/staccato, and MusicXML export.

The Recommended arrangement may change texture event by event, but texture is a soft preference rather than the path's first priority. Pickups, passing tones, and non-chord tensions favor a single voice or dyad; sustained chord tones, resolutions, chord arrivals, and cadences may use validated pairs or three-note grips. Without real chord symbols it never generates triads. The path stays in one compatible harmonic-pattern family through a phrase when possible, preserves common voices and string groups, and gives familiar control postures explicit priority: open, A, B, and A+B are the common working positions; F-lever and E-lower positions are secondary; C and B+C are specialized choices. The Recommended arrangement uses C or B+C only when the supplied harmony and validated mechanics justify it, such as a matching minor-chord grip, when preserving literal entered tab, or when no mechanically valid common-posture alternative can preserve the requested pitch and register. It does not make a temporary C-pedal or A+B-to-B+C excursion merely to save bar travel or add one harmony note.

Sparse integrated transitions primarily connect one validated two- or three-string attack to another validated two- or three-string grip, with the sounding grip sustaining through the bar movement whenever the copedent permits it. Validated open-to-A+B and A+B-to-open slides may span as many as seven frets so familiar same-chord and V-to-I moves such as fret 10 A+B to fret 3 open are not rejected by the shorter ornamental-slide limit. Melody-only slides and blocked slides, in which harmony is released and added or repicked at the destination, remain occasional exceptions rather than the default. A transition carries semantic source, destination, sustained, repicked, released, and per-string voice-action data. Tab keeps complete source and destination grip columns and inserts `~~~~~` for an audible bar slide or pedal/lever movement, `-----` for a voice held unchanged through the transition, and a blank connector for released, added, or repicked strings. Generated transition data never overwrites a destination note token. The score draws connectors only for voices that actually sustain or move, the fretboard animates only those voices, and printed tab keeps each source-connector-destination unit together. Transitions remain generated performance guidance, preserve source event count and rhythm, and are omitted when the mechanics or musical context are uncertain. The former one-ornament Vocal steel route is not part of the default route set.

The result action is **Print**, positioned beside Start over immediately below the tablature. For a multi-phrase song it prepares every section of the selected arrangement and prints one fixed-width tablature sheet with phrase headings only when multiple sections are present. The print sheet uses letter-size portrait orientation, a compact one-page layout, a clean song title, the selected arrangement, Melody Studio branding, and `www.steelguitarrag.com`. Attribution links, staff notation, fretboard, route controls, display toggles, transport, playback controls, edit actions, and editor chrome are suppressed in print output.

Once an E9 lesson is rendered, the introductory hero is hidden so the lesson begins directly beneath the compact Melody Studio header. **Edit melody** is available at the lesson heading and again after the tablature. Fretboard display controls sit immediately below the fretboard, before arrangement choices and note navigation. Route recommendation prose is not displayed.

The dedicated lesson view is fretboard-first. Its header contains only the lesson title and optional source identity; it does not display a generic "Practice the lesson" kicker or expose exactness, confidence, and single-section bookkeeping as header metadata. The fretboard renders only the active event's string locations; navigating or playing replaces that position instead of stacking the whole phrase. All available arrangement choices appear in one horizontally scrollable row directly below the fretboard, followed by the selected route's useful recommendation.

The note navigator shows one active event at a time, with `Note N of M`, resolved pitch, and plain steel instructions such as `Strings 5, 6 & 7 · Fret 10 · A+B`. Previous/next controls move through any phrase length without creating a row of one pill per note; the fixed-width tab remains the whole-phrase overview. It does not repeat the selection in a separate current-note block or deterministic implementation explanation. Navigation and playback must visibly select the matching `renderablePositionId` in the fretboard component.

Recommended-arrangement events may expose a collapsed **Why this grip?** disclosure beside the active-note instruction. It names the chosen pocket and gives one concise harmonic or ergonomic reason without adding always-visible explanatory prose. It may also explain why an apparently familiar pedal move is not correct for the active grip—for example, A+B on the opening fret-3 strings 4-5-6 G grip produces C harmony rather than preserving G.

Display toggles independently control Octave colors, compact string/action labels inside active marker bubbles (`6B`, `5A`, or plain `6` when open), and the resolved top-note label above the active position. Octave colors default off. Their legend sits immediately beside the Octave colors control and remains hidden until the control is enabled. Reviewed complete songs show the whole lead sheet and whole selected-route tablature at once; note navigation and playback move through that single continuous timeline. Mobile layout keeps route and octave rows horizontally scrollable, retains one readable active-note card between the arrows, and keeps fixed-width tab inside its own horizontal scroller.

The reviewed public-domain songbook stores one complete melodic cycle per title: a verse plus a distinct chorus or refrain when the music changes, or one complete melody when additional lyrical verses reuse the same tune. Catalog cards disclose the form, note count, measure count, and phrase count. Phrase metadata describes the form but does not split the player-facing lesson. Eight-note excerpts are not catalog deliverables.

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
- Default ready lessons include Faithful melody and, when materially different, a Recommended arrangement that can mix one-, two-, and chord-backed three-note events while keeping the resolved melody on top.
- Pasted literal tab retains string, fret, controls, and register exactly.
- Reviewed songbook examples render every event of their complete melodic form in one continuous score and tab; other long inputs may continue through labeled sections instead of failing.
- Complete-song printing includes all phrase sections of the selected arrangement route.
- Invalid tuning, key, note, string, fret, or control combinations render no tab/fretboard.
- Attribution and accuracy labels survive API and frontend normalization.
- Melody-only input displays no invented chord symbols; supplied chord symbols appear only at chord changes and guide route ranking.
- Score playback keeps the staff, fretboard, note navigator, and tab selection synchronized at adjustable tempo, including loop and count-in behavior.
- Existing progression, fretboard, voicing, gear, retrieval, auth, and source-card behavior remains green.
