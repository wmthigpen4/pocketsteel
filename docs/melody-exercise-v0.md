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
- `melody`: note names or scale degrees. Longer lists are divided into sections.
- `sectionNumber`: requested section, starting at 1.
- `renderingMode`: `transcription`, `e9_adaptation`, or `teaching_simplification`.
- `accuracy`: requested `exact`, `approximate`, or `interpretive` label. Exact artist-material claims are downgraded when no source is identified.
- `material`: artist, song, recording/version, section, source URL, and source reference.

The answer may add `melody_exercise` with:

- material identity and source reference;
- rendering and accuracy labels;
- section number, total, continuation state, and next section;
- mechanically validated musical events;
- validation results shared by tab and fretboard rendering.

Ready exercises also return `tab_example` and `fretboard` derived from the same validated events. Source-free original exercises return no source cards. Recording-based lessons preserve a supplied source URL as a recording/arrangement source card.

## Frontend Contract

When the backend advertises `features.melodyExercise=true` through `/api/session`, the home header exposes **Melody Studio** beside Explore Fretboard and Backstage. The technical inline form is not part of the home screen. `/ui/melody-workbench.html` owns the guided phrase-to-E9 workflow.

Melody Studio begins with four learner jobs: artist solo, song arrangement, the learner's melody, and original practice phrase. Recording fields appear only for source-based jobs and must be cleared when the learner switches to a source-free job. The phrase builder accepts notes, scale degrees, or simple one-string E9 tab, provides deterministic presets and a note/degree palette, and states clearly that a source link supplies attribution rather than automatic audio transcription.

The result shows:

- material identity and source link;
- transcription/adaptation/simplification label;
- exact/approximate/interpretive label and confidence;
- numbered lesson section and continuation state;
- synchronized event stepper, fixed-width tab, fretboard, and explanation;
- no empty source section for source-free deterministic exercises.

The dedicated lesson view is fretboard-first. Previous/next and event-step controls must visibly select the matching `renderablePositionId` in the fretboard component and update the active tab-step label. Long phrases expose a Continue to Section action using the existing `sectionNumber` request field. Mobile layout keeps the tab fixed-width inside its own horizontal scroller.

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
- Long inputs continue through numbered sections instead of failing.
- Invalid tuning, key, note, string, fret, or control combinations render no tab/fretboard.
- Attribution and accuracy labels survive API and frontend normalization.
- Existing progression, fretboard, voicing, gear, retrieval, auth, and source-card behavior remains green.
