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
- `melody`: legacy note-name/scale-degree strings or structured events. Structured events may add `direction`, `octaveShift`, or a literal standard-E9 `string`, `fret`, and `changes` position. Longer lists are divided into sections.
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

Ready exercises add `routes`, `selectedRouteId`, and an input `resolvedPhrase`. Each route owns its synchronized events, tab example, fretboard, harmony label, recommendation, and movement summary. Existing top-level `events`, `tab_example`, and `fretboard` remain populated from the selected single-note route for compatibility. Source-free original exercises return no source cards. Recording-based lessons preserve a supplied source URL as a recording/arrangement source card.

## Frontend Contract

When the backend advertises `features.melodyExercise=true` through `/api/session`, the home header exposes **Melody Studio** beside Explore Fretboard and Backstage. The technical inline form is not part of the home screen. `/ui/melody-workbench.html` owns the guided phrase-to-E9 workflow.

Melody Studio opens directly into the phrase builder. A compact starting-point control offers **Enter my phrase**, **A song or recording**, and **Give me an exercise**. The song/recording path reveals source fields plus a treatment choice between a faithful solo passage and a playable E9 arrangement; these continue to map to the existing artist-solo and song-arrangement request kinds. Recording fields are cleared when the learner switches to a source-free starting point. Practice presets appear for the exercise starting point. The phrase builder accepts notes, scale degrees, or literal one-string E9 tab and states clearly that a source link supplies attribution rather than automatic audio transcription. Literal tab retains its string, fret, controls, and register.

Unmarked degrees default to the closest playable pitch path. Players may choose ascending, descending, or preserve-input contour and adjust individual notes up or down by an octave. Sequence chips show the resolved scientific pitch before submission.

The result shows:

- material identity and source link;
- transcription/adaptation/simplification label;
- exact/approximate/interpretive label and confidence;
- numbered lesson section and continuation state;
- compact synchronized note navigator, fixed-width tab, fretboard, and explanation;
- switchable single-note, recommended harmony, thirds, sixths, and chord-melody routes when mechanically available;
- resolved pitch/register and bar, string, pedal, and lever movement guidance;
- no empty source section for source-free deterministic exercises.

The dedicated lesson view is fretboard-first. One compact navigator beneath the board combines the Octave colors toggle and legend, note progress, previous/next arrows, concise pitch/position pills, and one current-note readout. It does not repeat the selected note in a separate active-tab sentence or long explanatory event sentence. Previous/next and note-pill controls must visibly select the matching `renderablePositionId` in the fretboard component. Long phrases expose a Continue to Section action using the existing `sectionNumber` request field. Mobile layout keeps the arrows beside a horizontally scrollable pill row and keeps the fixed-width tab inside its own horizontal scroller.

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
- Existing progression, fretboard, voicing, gear, retrieval, auth, and source-card behavior remains green.
