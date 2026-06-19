# 2026-06-18 - Lane 18 - Public-Domain Song Tab Architecture

## Task Summary

Requested: design the public-domain song tablature architecture for Pocket Steel / The Turnaround without implementing code.

Completed: created this Lane 18 product/architecture handoff defining provenance, source registries, melody/chord/lyrics schemas, arrangement planning, validation, UI behavior, test strategy, and the next Lane 05 implementation prompt.

Intentionally not changed:

- No app code.
- No backend implementation.
- No UI code.
- No tests.
- No song data.
- No public-domain registry records.
- No `/api/answer`, `/api/tab/render`, SGF retrieval, Chroma/vector stores, embeddings, corpus/source data, scraping, auth, deployment, DNS, or design assets.

Task type: docs-only product/architecture.

Lane: `18 Product / Architecture`.

Task mode: GREEN for this handoff. Future implementation is YELLOW because it will add data contracts, answer routing, tab generation paths, and QA coverage.

Repo guidance read:

- `AGENTS.md`
- `agents.md`
- `README.md`
- `docs/handoffs/task-completions/integration-status.md`

No conflicts found. Local guidance requires exact-path staging, a handoff under `docs/handoffs/task-completions/`, `git diff --check`, and no broad staging.

## 1. Current State

The current tab-engine path supports deterministic examples and has architecture handoffs for answer-triggered tab examples and the next tab feature ladder.

Current known capabilities:

- Structured tab event model.
- Standard E9 assumptions.
- Mechanical validation through the existing `tab_engine`.
- Fixed-width tab rendering.
- Fretboard payload/sync direction where tab and SVG should share the same event/position data.

Current product gap:

- Short generated grips and exercises are useful, but they are not song tablature.
- Users will expect recognizable song melodies, practical steel arrangements, and clear provenance.
- The system currently lacks a public-domain song registry, source-backed melody data, arrangement rules, and song-level citation behavior.

Current safety boundary:

- The app must not generate copyrighted song tab.
- The app must not imply SGF, lesson, or public-domain provenance for rule-generated exercises.
- Public-domain song output requires explicit source and rights records before generation is enabled.

## 2. Product Problem

The tab engine needs to distinguish three different products that can look similar on screen:

1. A deterministic exercise.
2. A source-backed lick or practice idea.
3. A public-domain song arrangement.

If these are blurred, the product becomes misleading:

- A rule-generated I-IV move can be useful, but it is not sourced from a public-domain song.
- SGF or lesson-inspired technique can inform teaching, but it does not authorize copying a melody or arrangement.
- A public-domain song arrangement needs documented song status, cited melody data, and arrangement provenance.

The correct architecture is not "ask the model for tab." It is:

1. Verify song eligibility.
2. Load canonical melody/chord/lyric source records.
3. Plan an arrangement from the song data and user context.
4. Generate structured tab events.
5. Run mechanical and steel-practical validation.
6. Render tab and fretboard from the same events.
7. Show source/provenance clearly in the UI.

## 3. Provenance Model

Every tab payload must carry an explicit provenance type. The model should be visible to QA and available to the UI, even if the learner-facing copy is concise.

### Deterministic Exercise

Use when the app generates a short original drill, grip, chord move, or practice phrase from E9 rules.

Required values:

- `provenance.type`: `deterministic_exercise`
- `rightsStatus`: `original_educational_example`
- `sourcePolicy`: `no_external_song_source`
- `sourceIds`: empty array
- `generatedFrom`: deterministic rule/planner id

Rules:

- Do not cite SGF, lessons, or public-domain song sources for this output.
- Do not present it as a song phrase.
- It may include teaching context or source-backed notes separately, but the tab itself remains original/generated.

### Source-Backed Lick/Practice

Use when a source supports a general idea, technique, or practice concept, but the app still generates a short original example.

Required values:

- `provenance.type`: `source_backed_practice`
- `rightsStatus`: `original_educational_example`
- `sourcePolicy`: `source_supports_concept_not_tab`
- `sourceIds`: source cards or curated registry ids
- `generatedFrom`: deterministic rule/planner id plus source concept id

Rules:

- Source cards support the teaching claim, not the exact tab events.
- Do not copy raw SGF tab scraps or lesson fragments into generated tab.
- UI copy should avoid "from this source" unless the source actually contains the exact public-domain melody data being arranged.

### Public-Domain Song Arrangement

Use when the app arranges a documented public-domain melody/progression into E9 tab.

Required values:

- `provenance.type`: `public_domain_song_arrangement`
- `rightsStatus`: `public_domain_verified`
- `songId`
- `sourceIds`: one or more melody/progression source ids
- `arrangementId`: deterministic planner/version id
- `arrangementType`: one of the supported arrangement types
- `publicDomainReview.status`: `verified`

Rules:

- Public-domain status must be explicit and documented per song before generation.
- Melody source must be stored or cited.
- The generated arrangement is new, but its source melody/progression must be traceable.
- If public-domain status is incomplete, the app must not generate song tab.

## 4. Public-Domain Song Registry Schema

The song registry should be small and curated at first. Do not infer eligibility at answer time.

Conceptual registry record:

```json
{
  "songId": "candidate-boil-them-cabbage-down",
  "title": "Boil Them Cabbage Down",
  "alternateTitles": [],
  "status": "candidate | verified | rejected | needs_review",
  "rightsStatus": "public_domain_verified | public_domain_candidate | unknown | restricted",
  "jurisdiction": "US",
  "review": {
    "reviewedBy": "lane-02-or-human-review",
    "reviewedAt": "YYYY-MM-DD",
    "basis": "publication_date | traditional | source_license | expert_review",
    "notes": "Short review note. No broad legal claim without cited basis."
  },
  "sources": [
    {
      "sourceId": "source-001",
      "type": "melody | chord_progression | lyrics | historical_rights_note",
      "title": "Source title",
      "url": "https://example.invalid/source",
      "licenseOrRights": "public_domain | cc0 | permissive | unknown",
      "retrievedAt": "YYYY-MM-DD",
      "citationText": "Short citation for UI/source card"
    }
  ],
  "defaultKey": "G",
  "supportedKeys": ["G", "A", "C", "D"],
  "difficulty": "starter | common | alternate | advanced",
  "enabledArrangementTypes": [
    "melody_only",
    "two_note_harmony",
    "three_note_grip",
    "backup_fill",
    "intro_turnaround"
  ],
  "warnings": []
}
```

Rules:

- `status=verified` and `rightsStatus=public_domain_verified` are required before song-tab generation.
- `candidate` records may exist for review, but they must not produce user-facing generated song tab.
- Registry records should cite source material. Do not rely on memory or unsourced assumptions.
- Keep source text minimal in the registry. Store enough citation/provenance to find and verify the source, not a bulk copy of source material unless the source/license allows it and the repo path is approved.

## 5. Melody Data Schema

Melody data must be structured enough for deterministic arrangement planning.

Conceptual melody record:

```json
{
  "melodyId": "boil-cabbage-melody-g-v1",
  "songId": "boil-them-cabbage-down",
  "sourceId": "source-001",
  "key": "G",
  "meter": "4/4",
  "pickupBeats": 0,
  "phrases": [
    {
      "id": "phrase-a1",
      "label": "A1",
      "events": [
        {
          "id": "m-a1-001",
          "beat": "1",
          "duration": "quarter",
          "pitch": "G4",
          "scaleDegree": "1",
          "lyricSyllableId": "lyr-a1-001",
          "tie": false
        }
      ]
    }
  ],
  "contour": ["same", "up", "down"],
  "range": {
    "lowest": "D4",
    "highest": "B4"
  },
  "checksum": "stable-source-data-checksum"
}
```

Requirements:

- Melody source must be stored or cited.
- Melody pitch and rhythm must be structured. Raw text alone is not enough.
- Arrangement must preserve melody contour.
- For melody-tracking arrangements, the melody note should usually be the top audible note.
- Transposition should occur from structured pitch/scale-degree data, not from rendered tab.
- If source data is incomplete, mark the song or phrase `needs_review`.

## 6. Chord/Lyrics Data Schema

Chord and lyric data should support arrangement context, but chords must not override the melody.

Conceptual progression record:

```json
{
  "progressionId": "boil-cabbage-progression-g-v1",
  "songId": "boil-them-cabbage-down",
  "sourceId": "source-002",
  "key": "G",
  "sections": [
    {
      "id": "section-a",
      "label": "A",
      "measures": [
        {
          "measure": 1,
          "chords": [
            {
              "beat": "1",
              "symbol": "G",
              "function": "I",
              "duration": "measure"
            }
          ]
        }
      ]
    }
  ]
}
```

Conceptual lyric record:

```json
{
  "lyricsId": "boil-cabbage-lyrics-v1",
  "songId": "boil-them-cabbage-down",
  "sourceId": "source-003",
  "rightsStatus": "public_domain_verified",
  "lines": [
    {
      "id": "line-001",
      "text": "Short public-domain line only if source policy allows storage",
      "syllables": [
        {
          "id": "lyr-a1-001",
          "text": "Boil",
          "melodyEventId": "m-a1-001"
        }
      ]
    }
  ]
}
```

Rules:

- Chords should be derived from melody plus known progression, not invented first.
- If no trusted chord source exists, derive simple functional harmony from melody and key and label it `derived_harmony`.
- Lyrics are optional for tab generation.
- Do not store lyrics for a song unless rights status and source policy allow it.
- If lyric storage is not needed, store phrase labels and melody ids instead.

## 7. E9 Arrangement Planner

The arrangement planner turns source-backed song data into playable E9 tab events.

Planner inputs:

- `songId`
- `melodyId`
- optional `progressionId`
- optional `lyricsId`
- `key`
- `arrangementType`
- `playerContext`
- `difficulty`
- `fretRange`
- `preferredGrip`
- `profileId`

Supported arrangement types:

- `melody_only`
- `two_note_harmony`
- `three_note_grip`
- `backup_fill`
- `intro_turnaround`

Player context:

```json
{
  "role": "lead | backup",
  "bassPlayerPresent": true,
  "bandContext": "solo | duo | full_band | unknown",
  "skillLevel": "starter | common | alternate | advanced",
  "melodyTracking": true
}
```

Planner rules:

- Preserve melody contour.
- Keep melody on top when `melodyTracking=true`.
- Prefer mechanically simple grips for starter arrangements.
- Use chord tones derived from melody/progression context.
- Avoid muddy low grips for beginner arrangements.
- Prefer nearby bar movement over large jumps when multiple valid positions exist.
- Use pedals/levers only when they improve playability or sustain.
- Do not create arbitrary pedal/lever combinations.
- Do not use SGF fragments as event source.

Output should be payload-ready structured tab events plus provenance and validation data. Rendered ASCII tab and fretboard payloads must be derived from these events.

## 8. Mechanical Validation Layer

Mechanical validation should reuse the existing `tab_engine` validation path.

Required checks:

- string numbers are valid for 10-string E9,
- frets are valid for the supported range,
- pedal/lever labels are known,
- requested changes affect the target strings,
- no duplicate or impossible notes inside an event,
- event note count fits renderer limits or an explicitly expanded renderer mode,
- mixed-fret events are rejected unless future slant support exists,
- generated events render successfully,
- rendered tab is produced from the structured events.

Failure behavior:

- Do not display invalid generated song tab.
- Return answer-only fallback or "needs review" copy.
- Log/test validation issues in QA paths.
- Do not silently repair melody mistakes in a way that changes the tune.

## 9. Steel-Practical Validation Layer

Mechanical validation proves a tab can be rendered. Steel-practical validation asks whether it is worth giving to a learner.

Checks:

- melody contour preserved,
- melody note is on top when required,
- chord tones support the current chord/function,
- bar jumps are reasonable for the declared difficulty,
- grips are physically and musically common enough for the difficulty,
- pedal/lever moves are practical in sequence,
- low-register grips do not muddy the arrangement,
- root/bass notes are omitted when context calls for it,
- output length is not excessive,
- arrangement type matches user request.

Suggested result shape:

```json
{
  "status": "pass | warning | fail",
  "score": 0.92,
  "checks": [
    {
      "code": "melody_contour_preserved",
      "status": "pass",
      "message": "Melody contour matches source phrase."
    }
  ],
  "warnings": []
}
```

Rule:

- A `fail` result blocks song-tab display.
- A `warning` result can display only with clear caveats and QA coverage.

## 10. Bass/Root Omission Rules

Pedal steel often should not carry the bass role in a full band. The arrangement planner needs explicit context.

Rules:

- If `bassPlayerPresent=true`, avoid low root-heavy grips unless requested.
- For backup arrangements, prefer upper harmony, fills, passing tones, and voice-leading over full low triads.
- For melody tracking, keep melody on top and drop lower root/bass notes when they muddy the sound.
- For solo steel context, allow more root support but still avoid low clutter in starter arrangements.
- For three-note grips, root can be omitted if the melody and harmony context make the chord clear.
- For dominant or color tones later, prioritize function and voice-leading over spelling every chord tone.

Starter defaults:

- Lead melody: melody-only or two-note harmony first.
- Backup with bass present: two-note harmony or backup fill.
- Solo practice: melody-only plus occasional three-note grip.
- Avoid low 6-8-10 style grips for beginner melody arrangements unless validated as clean in context.

## 11. Source/Citation Requirements

Public-domain song tab needs source cards that describe the song data, not SGF evidence masquerading as song provenance.

Required per generated song tab:

- song title,
- public-domain review status,
- jurisdiction or scope of review,
- melody source id and citation,
- chord/progression source id or derived-harmony label,
- lyrics source id if lyrics are used or shown,
- arrangement planner id/version,
- generated arrangement provenance.

Citation UI copy should distinguish:

- "Melody source"
- "Chord source"
- "Lyrics source"
- "Arrangement generated by The Turnaround"
- "Technique note" for SGF/lesson-inspired supporting evidence

Rules:

- Do not cite SGF as the melody source unless the SGF source actually provides a verified public-domain melody and usage policy allows it.
- Do not cite public-domain sources for deterministic exercises.
- Do not show source cards stronger than the answer/tab explanation.
- If source status is uncertain, block generated song tab.

## 12. UI Behavior

UI should make provenance and learning state clear without overwhelming the answer.

Recommended default layout:

1. Direct teaching answer.
2. Song/arrangement summary.
3. Compact tab card.
4. Optional SVG fretboard sync.
5. Source/provenance cards.

Tab card should show:

- song title,
- arrangement type,
- key,
- E9/profile assumption,
- role/context: lead or backup,
- validation badge,
- short provenance label,
- rendered tab,
- "why this works" explanation,
- caveats if present.

Provenance labels:

- `Original exercise`
- `Source-backed practice idea`
- `Public-domain song arrangement`

Fretboard behavior:

- Fretboard events must come from the same event list as tab.
- Selecting a tab event should highlight the matching fret/string/control state.
- UI computes SVG geometry.
- Backend sends event ids, strings, frets, pedals/levers, notes, intervals, and optional phrase ids.
- No backend raw x/y coordinates.

Default display limits:

- Do not dump a whole song by default.
- Show one phrase or short section first.
- Provide "show next phrase" or "show more arrangement" later only after pagination/rights/QA behavior exists.

## 13. First MVP Song Recommendation

Recommended first MVP candidate: `Boil Them Cabbage Down`.

This is a candidate recommendation, not a public-domain claim. It must not be enabled until Lane 02 or human provenance review creates a verified song registry record with cited source data.

Why this candidate is practical:

- Common beginner fiddle/folk tune.
- Short repeated phrases.
- Works as melody-only, two-note harmony, simple backup fill, and intro/turnaround material.
- Useful for testing I-IV-V movement, melody-on-top rules, and bass/root omission.
- Familiar enough for user validation without requiring copyrighted modern-song handling.

Acceptance condition before enabling:

- verified public-domain registry status,
- cited melody source,
- cited or derived chord progression,
- structured melody events for one short phrase,
- standard E9 arrangement generated from structured data,
- mechanical validation pass,
- steel-practical validation pass,
- UI source/provenance distinction visible.

Fallback candidate if provenance review rejects or blocks it:

- Choose another short, well-documented public-domain/traditional melody only after the same source review process.

## 14. Test Plan

### Registry Tests

- candidate songs do not generate tab,
- verified songs can generate tab,
- unknown/restricted songs are blocked,
- every enabled song has at least one melody source citation,
- every enabled song has public-domain review metadata,
- missing review metadata blocks generation.

### Melody/Progression Tests

- melody events parse into stable phrase/event ids,
- transposition preserves scale-degree contour,
- derived harmony is labeled as derived,
- incomplete source records return `needs_review`,
- lyric storage is absent unless rights/source policy allows it.

### Arrangement Planner Tests

- melody-only preserves melody contour,
- melody-tracking keeps melody on top,
- two-note harmony uses valid chord tones,
- three-note grip does not add muddy low roots in starter mode,
- backup fill avoids stepping on bass role when `bassPlayerPresent=true`,
- intro/turnaround output is short and source/provenance-labeled.

### Mechanical Validation Tests

- all generated events pass `tab_engine` validation,
- invalid pedal/string changes block display,
- mixed-fret/slant-like events block display until slants are supported,
- rendered tab is generated from events,
- fretboard payload uses the same event ids.

### Steel-Practical Validation Tests

- excessive bar jumps fail starter arrangements,
- low muddy grips warn or fail in beginner mode,
- root omission rules apply with `bassPlayerPresent=true`,
- no output exceeds default phrase length limits,
- unsupported copedent/profile blocks or caveats correctly.

### Answer/UI Contract Tests

- provenance labels are present,
- source cards are separated from arrangement provenance,
- deterministic exercises do not cite public-domain song sources,
- source-backed practice ideas do not claim exact song/source arrangement,
- public-domain song arrangement shows melody/chord source context,
- no `[object Object]` rendering,
- no full copyrighted song tab generation.

## 15. Next Implementation Prompt For Lane 05

```text
Lane: 05 Backend / RAG Integration
Reasoning level: HIGH

Task: Implement the first public-domain song tab architecture slice without adding user-facing generated song tab yet.

Read:
- AGENTS.md
- docs/handoffs/task-completions/2026-06-18-18-public-domain-song-tab-architecture.md
- docs/handoffs/task-completions/2026-06-18-18-tab-engine-next-feature-ladder.md
- pocketsteel/tab_engine.py
- current answer/tab contract files
- tests/test_tab_engine.py
- tests/test_api_contract.py

Goal:
Add the backend contract scaffolding for public-domain song tab generation, but do not enable song tab output until verified song data exists.

Scope:
- Define provenance types:
  - deterministic_exercise
  - source_backed_practice
  - public_domain_song_arrangement
- Define registry schema/types for public-domain song records.
- Define melody/progression/arrangement data structures.
- Add validation helpers that require verified public-domain metadata before generation.
- Add tests proving candidate/unverified songs cannot generate tab.
- Reuse existing tab_engine mechanical validation for any generated events.
- Keep feature flag default off.

Do not:
- add real song data yet,
- make public-domain claims without cited records,
- generate copyrighted song tab,
- use SGF fragments as melody data,
- touch UI files,
- touch Chroma, embeddings, corpus/source-inbox raw data, scraping, auth, deployment, DNS, or secrets.

Required handoff:
Write docs/handoffs/task-completions/<timestamp>-05-public-domain-song-tab-scaffold.md with files changed, tests run, risks, safe-to-stage exact paths, and next lane.
```

## Files Changed

- Created:
  - `docs/handoffs/task-completions/2026-06-18-18-public-domain-song-tab-architecture.md`
- Changed:
  - None
- Deleted:
  - None
- Generated artifacts:
  - None

## Tests And Checks

Commands run:

- `git diff --check`
  - Passed.
- `git diff --no-index --check -- /dev/null docs/handoffs/task-completions/2026-06-18-18-public-domain-song-tab-architecture.md`
  - Passed. Used because this file is new and untracked, so normal `git diff --check` does not inspect it.
- `git status --short`
  - Passed before and after file creation. The broader worktree has many unrelated dirty/untracked files; this task created only the target handoff.
- `git status --short -- docs/handoffs/task-completions/2026-06-18-18-public-domain-song-tab-architecture.md`
  - Passed. Shows the new handoff as untracked before staging.

Skipped:

- Unit, API, UI, browser, and eval tests. This task intentionally changes only a documentation handoff.

## Integration Notes

- This handoff does not authorize song data ingestion.
- This handoff does not make any public-domain claim for a specific song.
- The first implementation should scaffold contracts and blocking validation before any user-facing song arrangement is enabled.
- Lane 02 or human provenance review should own verified song/source records.
- Lane 05 should own backend contract scaffolding and validation.
- Lane 06 should own UI rendering only after backend payload shape is stable.
- Lane 15 should own registry/provenance/rights and generation guardrail tests.

## Risk Assessment

Risk level: low for this docs-only handoff, medium/high for future implementation.

Why:

- Public-domain song tab is product-valuable but rights-sensitive.
- Incorrect provenance would mislead users and create legal/product risk.
- Generated arrangements can be mechanically valid but musically poor without steel-practical validation.

Rollback notes:

- Remove this handoff if superseded by later product/legal architecture.

## Human Decision Needed

No for this handoff.

Future decisions:

- Approve the first verified public-domain song candidate after source review.
- Decide where verified melody/progression source data should live.
- Decide whether source data records are repo-tracked fixtures, generated artifacts, or externally managed content.
- Choose final public response field naming for tab payloads if not already settled.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-18-public-domain-song-tab-architecture.md`

## Files That Must Not Be Staged

- Any pre-existing dirty files outside the safe-to-stage path above.
- App code.
- Backend implementation files.
- Frontend/UI files.
- Tests.
- Song data.
- `docs/handoffs/task-completions/integration-status.md`
- Chroma/vector data.
- Embeddings.
- `corpus-private/`
- `corpus-v2/`
- Source-inbox raw data.
- Scraping outputs.
- Deployment/auth/DNS/secrets files.
- Raw design assets.
- Generated reports.

## Recommended Next Lane

Lane 05 Backend / RAG Integration.

Recommended first implementation slice:

- Add public-domain song-tab contract scaffolding and blocking validation only.
- Do not add real song data yet.
- Prove candidate/unverified songs cannot generate tab.

## Commit Readiness

Safe to commit if the cached diff is limited to the safe-to-stage file above.
