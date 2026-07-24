# Steel Guitar RAG Tab Engine Product Architecture

## Task Summary

- What was requested: define the product architecture and feature ladder for the Steel Guitar RAG tab engine so future backend, UX, QA, and RAG lanes can build from a structured deterministic plan.
- What was completed: created this Lane 18 product/architecture handoff covering product thesis, feature ladder, tab-producing input types, backend architecture, data model concepts, guardrails, MVP cut, v2/v3 roadmap, RAG integration, SVG fretboard sync, risks, acceptance criteria, and recommended engineering slices.
- What was intentionally not changed: no app code, backend implementation, UI, prompts, `/api/answer`, SGF retrieval, Chroma/vector stores, embeddings, corpus data, source-inbox data, deployment, auth, staging, or commits were changed.

## Product Thesis

Steel Guitar RAG tab should become a teaching and validation engine, not a prompt-only ASCII tab generator.

The product differentiator is not "the model can print lines with fret numbers." The differentiator is that Steel Guitar RAG can reason from a copedent, resolve playable positions, plan a small musical idea, render readable tab, validate that the tab is possible, explain why it works, and synchronize it with the SVG fretboard.

The tab engine should answer like a steel-guitar teacher:

- show the physical move,
- name strings, frets, pedals, and levers,
- explain intervals or chord function,
- warn when the setup is unknown or unsupported,
- keep examples short and original unless the user provides the source material,
- use RAG as context/evidence, not as the tab source of truth.

## Core Architecture Principle

Tab output must be structured first and rendered second.

Required system layers:

1. Copedent profile.
2. Pitch/position resolver.
3. Musical planner.
4. Tab event model.
5. Renderer.
6. Validator.
7. Answer/RAG integration.
8. UI/fretboard sync.

LLM text generation may help explain a tab, choose wording, or summarize source-backed technique context. It must not be the authority for whether a fret/string/pedal combination is playable.

## Feature Ladder

### Level 0: Tab Explanation Without Generation

User pastes short tab or asks what a tiny pattern means.

Product behavior:

- parse or preserve the user-provided tab,
- explain mechanics, intervals, and likely musical function,
- warn when copedent assumptions are unknown,
- avoid claiming exact artist/source intent.

Why first:

- lowest copyright and musical-risk surface,
- useful before the engine generates full examples,
- trains the answer shape for future generated tabs.

### Level 1: Short Original Educational Examples

System generates very short examples for a concept, such as A+B pedal movement, E-lower minor sound, blocking, grips, or a I-IV move.

Limits:

- original educational examples only,
- short phrase length,
- standard E9 only at first,
- no named-song reconstruction,
- no artist solo recreation.

### Level 2: Chord Movement Examples

System generates a small tab example for movements such as I-IV, I-V, I-IV-V-I, open to A+F, or A+B to open equivalents.

Required:

- planner names chord function and destination,
- resolver picks playable positions,
- validator confirms all tab events fit the assumed copedent,
- answer explains the movement before showing tab.

### Level 3: Melody-To-Tab From User-Provided Notes

User provides a short melody as notes, scale degrees, or simple rhythm labels.

Required:

- user-provided musical material,
- engine maps notes to candidate string/fret/control choices,
- user can choose beginner, smooth bar movement, same grip, or low movement,
- output includes caveats about timing and phrasing.

### Level 4: Lyrics/Chord Guided Examples

User supplies lyrics and chord symbols, or a public-domain song context. The engine creates short fills, transitions, or backup ideas around the chords.

Required:

- rights status must be explicit,
- examples must be short and educational,
- copyrighted lyrics/chords cannot be used to reconstruct a song arrangement,
- public-domain or user-owned material gets broader support.

### Level 5: Answer-Enhanced Tabs

Tab becomes part of the normal answer stack when a teaching question benefits from it.

Examples:

- "Show me a simple I-IV-V move in G."
- "Give me a blocking drill for strings 5 and 6."
- "Show a short example using B+C."

Required:

- direct teaching answer first,
- tab block second,
- explanation and caveats,
- optional source cards only below the answer.

### Level 6: Tab Validation

System validates user-provided or generated tab against a copedent.

Validation includes:

- invalid string/fret/control labels,
- unsupported pedal/lever,
- impossible simultaneous raises/lowers,
- large or awkward bar jumps,
- unclear timing,
- missing copedent assumptions,
- copyrighted/full-song guardrail.

### Level 7: SVG Fretboard Sync

Tab events drive synchronized fretboard states.

Behavior:

- selecting a tab beat/event highlights the matching strings/frets/controls,
- selecting a fretboard position can reveal the corresponding tab event,
- UI geometry remains SVG-owned,
- backend sends musical intent only.

### Level 8: Practice Exercises

Tab examples become drills with repetition counts, tempo targets, focus notes, and progression through difficulty.

Examples:

- blocking drill,
- A+B squeeze drill,
- E-lower minor drill,
- I-IV-V-I movement drill,
- call-and-response fill exercise.

## User Input Types That Can Produce Tab

| Input type | MVP support | Product behavior |
| --- | --- | --- |
| Concept request | Yes | Generate a short original educational example for a technique or movement. |
| Chord movement | Yes | Generate a tiny transition using deterministic positions. |
| Chord progression | Limited MVP | Support I-IV, I-V, and I-IV-V-I in common keys; expand later. |
| Pasted user tab | Yes for explanation | Explain and validate; regenerate only as original variation if requested. |
| User-provided notes | V2 | Convert short note list or scale degrees to candidate tab. |
| User-provided rhythm | V2/V3 | Preserve simple beat labels first; real rhythmic notation later. |
| Lyrics/chords supplied by user | V3 | Generate short fills only when rights and scope are safe. |
| Public-domain song | V3 | Allow short educational excerpts with explicit rights status. |
| Copyrighted song title only | No | Refuse full tab; offer original exercise in the style or explain chord movement. |
| Named artist solo | No | Refuse reconstruction; offer technique analysis or original exercise. |

## Backend Architecture

### 1. Copedent Profile

Purpose: define tuning, strings, pedals, levers, and string-specific pitch changes.

MVP:

- standard 10-string E9,
- strings 1-10 high to low,
- canonical pedals `A`, `B`, `C`,
- canonical levers `F`, `E`, `G+`, `G-`, `D-`, `D--`, `V`,
- profile id such as `mvp-e9-standard`.

Future:

- saved user copedent,
- profile-backed caveats,
- copedent comparison,
- unsupported-change diagnostics.

### 2. Pitch/Position Resolver

Purpose: resolve notes, intervals, and playable locations from fret/string/control choices.

Responsibilities:

- calculate pitch by string, fret, pedal, and lever,
- normalize enharmonics while preserving user-facing spelling where useful,
- find candidate positions for chords, scale tones, and melody notes,
- return confidence and caveats.

This layer should reuse or align with the E9 fretboard position engine contract. It must not call SGF retrieval to decide pitch facts.

### 3. Musical Planner

Purpose: turn a user goal into a small playable plan.

Planner inputs:

- goal type: drill, chord movement, melody mapping, tab explanation, validation,
- key/root/quality/progression,
- difficulty: beginner, practical, advanced,
- constraints: strings, grips, fret range, pedals/levers, bar movement preference,
- rights status and source of musical material.

Planner outputs:

- ordered musical steps,
- selected positions,
- intended chord functions or intervals,
- practice focus,
- constraints and caveats.

The planner should be deterministic for MVP templates. It can later use LLM assistance only to select among validated plans or phrase explanations.

### 4. Tab Event Model

Purpose: represent tab as structured events before rendering.

Conceptual event fields:

```json
{
  "id": "event-001",
  "beat": "1",
  "duration": "quarter",
  "fret": 3,
  "strings": [4, 5, 6],
  "pedals": [],
  "levers": [],
  "notes": {"4": "G", "5": "D", "6": "B"},
  "intervals": {"4": "1", "5": "5", "6": "3"},
  "technique": ["pick", "block"],
  "positionId": "g-open-3",
  "label": "G major open position"
}
```

MVP can omit exact rhythmic durations if unsupported, but it should still preserve event order and optional beat labels.

### 5. Renderer

Purpose: render structured events into output formats.

MVP renderers:

- plain monospace tab block,
- compact event list for UI,
- answer text summary.

Future renderers:

- editable tab UI,
- printable lesson snapshot,
- MusicXML-like export if useful,
- fretboard animation timeline.

Renderer rule: ASCII tab is an output format, not the source of truth.

### 6. Validator

Purpose: prevent bad or impossible tab from reaching the user unmarked.

Validation should check:

- string numbers 1-10,
- fret range,
- known pedal/lever labels,
- copedent-supported changes,
- conflicts such as simultaneous incompatible raises/lowers,
- tab event positions resolve to expected notes when target notes exist,
- bar movement and grips are plausible for the requested difficulty,
- generated content stays within copyright/product guardrails.

If validation fails, the system should either repair deterministically, downgrade confidence, ask for more context, or refuse/redirect when rights are unsafe.

### 7. Answer/RAG Integration

Purpose: integrate tab with teacher-first answers and source evidence.

Rules:

- deterministic tab generation comes before SGF retrieval for supported tab tasks,
- SGF/forum content may explain technique context or caveats,
- SGF/forum fragments must not generate tab events,
- private guidance must not produce public tab without auth/private-review controls,
- source-backed does not mean source-quoted,
- answer text must explain what the tab does and how to practice it.

### 8. UI/Fretboard Sync

Purpose: connect tab events to the SVG fretboard and answer UI.

Rules:

- backend sends string/fret/control/event ids,
- UI computes all geometry,
- tab event ids and fretboard position ids must be stable,
- selected event highlights the fretboard,
- selected fretboard marker can reveal tab event(s),
- no raw x/y coordinates in backend tab payloads.

## Data Model Concepts

### Tab Payload

Conceptual response shape:

```json
{
  "type": "pedal_steel_tab",
  "instrument": "E9",
  "copedent": "mvp-e9-standard",
  "rightsStatus": "original_educational_example",
  "purpose": "practice_drill",
  "title": "G to C A+B movement",
  "difficulty": "starter",
  "events": [],
  "renderings": {
    "ascii": ""
  },
  "fretboardSync": {
    "mode": "tab-events",
    "eventPositionMap": {}
  },
  "validation": {
    "status": "valid",
    "warnings": []
  },
  "explanation": {
    "directAnswer": "",
    "whyItWorks": "",
    "practiceStep": ""
  }
}
```

### Position Reference

Tab events should be able to reference existing fretboard positions:

```json
{
  "positionId": "g-open-3",
  "fret": 3,
  "strings": [4, 5, 6],
  "pedals": [],
  "levers": []
}
```

### Validation Result

```json
{
  "status": "valid | warning | invalid",
  "confidence": "deterministic | assumed-copedent | inferred | unsupported",
  "warnings": [
    {
      "code": "assumed_standard_e9",
      "message": "This assumes standard 10-string E9."
    }
  ]
}
```

### Rights Status

Required values should be explicit:

- `original_educational_example`
- `user_provided_material`
- `public_domain`
- `source_backed_explanation_only`
- `restricted_copyrighted_material`
- `unknown`

`restricted_copyrighted_material` and `unknown` should not allow generated full tab.

## Guardrails

### Copyright And Source Guardrails

- Do not generate full note-for-note tab for copyrighted songs.
- Do not reconstruct commercial lesson material.
- Do not recreate a named artist's complete recorded solo.
- Do not use private lesson transcripts to output public tab.
- Do not claim exactness when source material is uncertain.
- User-provided short material can be explained or transformed within safe limits.
- For copyrighted-title-only prompts, redirect to a short original exercise, chord-movement explanation, or technique discussion.

### Musical Guardrails

- No unsupported copedent claims.
- No arbitrary pedal/lever combinations in generated tab.
- No slants until the position engine and UI explicitly support them.
- No live audio promise in MVP.
- No melody-to-tab claim until note input and resolver tests exist.
- No "all possible tabs" dumps.

### Product Guardrails

- The answer should teach first; tab is a structured teaching artifact.
- Fretboard sync should clarify, not overwhelm.
- Default examples should be short enough to practice immediately.
- Hide alternate/advanced versions behind explicit user action.
- Do not expose private-review guidance publicly.

## MVP Cut

MVP should support:

- standard 10-string E9 only,
- assumed standard copedent,
- short original educational examples,
- chord movement examples for simple deterministic families,
- pasted short tab explanation,
- structured tab event model,
- ASCII rendering from structured events,
- validation for basic string/fret/control correctness,
- answer text sections: direct answer, mechanics, why it works, practice step, caveats,
- optional static fretboard sync using event ids and position ids.

MVP should not support:

- full-song tab,
- melody-to-tab from arbitrary audio,
- lyrics/chord arrangement generation for copyrighted songs,
- custom copedent editing,
- C6/universal tunings,
- bar slants,
- live audio/playback,
- arbitrary pedal/lever stacks,
- SGF-fragment-generated tab.

## V2 Roadmap

V2 should add:

- melody-to-tab from user-provided notes or scale degrees,
- difficulty and movement preferences,
- stronger validator with pitch target checks,
- saved user copedent support if auth/profile architecture is ready,
- UI event selection synced with fretboard highlights,
- alternate position suggestions,
- practice drill payloads with repetition/tempo targets,
- eval fixtures for generated examples.

## V3 Roadmap

V3 should add:

- public-domain song excerpts,
- user-supplied lyrics/chord guided fill generation,
- richer rhythmic notation,
- editable tab input,
- printable/exportable lesson snapshots,
- deeper RAG-assisted technique context,
- user-specific practice progression,
- optional playback only after deterministic event timing exists.

## RAG Integration Strategy

RAG should support tab answers in three ways:

1. Intent classification: determine whether the user wants generation, explanation, validation, or a rights-restricted request.
2. Teaching context: add source-backed technique notes, caveats, or player-practice wisdom below the deterministic tab.
3. Answer composition: synthesize a teacher-first explanation around the validated tab.

RAG must not:

- invent playable tab events,
- copy raw SGF tab scraps into the answer,
- use private guidance for public tab,
- bypass the validator,
- fill gaps when the deterministic engine cannot support the request.

Recommended routing:

1. Guardrail/right-status check.
2. Tab intent classification.
3. Copedent/profile selection.
4. Deterministic planner/resolver/validator.
5. Optional RAG for technique context only.
6. Renderer and answer composition.
7. UI/fretboard payload assembly.

## SVG Fretboard Sync Strategy

The SVG fretboard should be a synchronized teaching view, not a separate generator.

Backend sends:

- tab event ids,
- string numbers,
- fret numbers,
- pedals/levers,
- optional position ids,
- optional notes/intervals,
- event order and labels.

UI owns:

- string/fret geometry,
- marker placement,
- animation timing,
- selected state,
- responsive rendering,
- decorative imagery.

MVP sync:

- tab block event rows map to highlighted locations,
- selected event highlights one fret/string group,
- fretboard detail panel shows event mechanics.

Later sync:

- step-through controls,
- compare events,
- practice drill progress,
- simple animation across tab events.

## Risks

Risk level: medium.

Key risks:

- Prompt-only tab generation would create plausible but wrong steel guitar tab.
- Copyright requests can pressure the system into full-song or artist-solo reconstruction.
- SGF fragments may include tab scraps that should not become generated output.
- Custom copedent assumptions can make otherwise valid tab wrong for the user.
- Fretboard sync can overwhelm the answer if every event/position is shown at once.
- Private-review guidance could leak into public tab answers if routing is not gated.

Mitigations:

- Structured event model before rendering.
- Validator before display.
- Short original examples only for MVP.
- Explicit rights status on every tab payload.
- Feature flags for tab generation and fretboard sync.
- Lane 15 evals for copyright, impossible tab, and object-string/rendering regressions.
- Auth/private-review gates before any private material can influence tab output.

## Acceptance Criteria

MVP product acceptance:

- A user can ask for a short original E9 exercise and receive a compact, playable tab example with explanation.
- The tab is generated from structured events, not hand-written prompt text.
- The output names strings, frets, pedals/levers, and practice purpose.
- The validator catches invalid string/fret/control values.
- The answer refuses or redirects full copyrighted song/artist-solo tab requests.
- The ASCII rendering can be regenerated from the event model.
- If fretboard sync is present, each tab event maps to string/fret/control values and no raw geometry.
- Source cards, if any, support technique context and do not become the tab.

Backend acceptance:

- `TabEvent`-like objects exist before any ASCII renderer.
- Pitch/position resolver is deterministic for MVP E9.
- Rights status and validation status are included in the response.
- Feature flags default off for generated tab in public/protected-preview rollout.

UX acceptance:

- Tab block is readable on desktop and mobile.
- Explanation appears before or beside the tab clearly enough to teach the move.
- Fretboard sync highlights one selected event or a small group by default.
- UI never renders raw objects such as `[object Object]`.

QA acceptance:

- Fixtures cover at least one generated exercise, one chord movement, one pasted-tab explanation, one invalid copedent/control case, and one copyrighted-song refusal.
- Eval buckets include copyright guardrail, impossible tab, unsupported copedent, missing validation, source-fragment tab leakage, and fretboard sync mismatch.

## Key Architectural Decisions

- Tab is a structured deterministic system, not an ASCII prompt format.
- ASCII tab is a renderer output.
- MVP uses standard 10-string E9 only.
- The pitch/position resolver is the musical authority.
- RAG can explain and contextualize but cannot invent tab events.
- Every tab payload needs rights status and validation status.
- SVG fretboard sync uses string/fret/control/event ids, never backend geometry.
- Generated examples start short, original, and educational.

## Recommended Next Engineering Slices

### Lane 05 Slice 1: Tab Payload Contract

Define backend dataclasses or schema for:

- tab request intent,
- tab event,
- tab payload,
- validation result,
- rights status,
- fretboard sync map.

No generation yet.

### Lane 05 Slice 2: E9 Resolver Adapter

Connect tab event validation to the existing or planned E9 pitch/position engine.

Scope:

- standard E9 only,
- validate strings/frets/pedals/levers,
- calculate notes/intervals for known events.

### Lane 05 Slice 3: Deterministic Short Example Generator

Generate two or three hardcoded-template but resolver-backed examples:

- A+B squeeze drill,
- G to C I-IV movement,
- simple E-lower minor color example if validated.

### Lane 15 Slice 1: Tab Contract Review And Fixtures

Review this architecture and create fixture expectations before runtime generation ships.

Required fixture buckets:

- valid short original example,
- invalid string/fret/control,
- copyrighted-song refusal,
- user-pasted tab explanation,
- fretboard sync map integrity.

### Lane 06 Slice 1: Tab Rendering Design

Design the answer UI shape for:

- monospace tab block,
- event detail,
- pedals/levers badges,
- validation warnings,
- fretboard sync affordance.

No broad UI redesign.

## Files Changed

- Created:
  - `docs/handoffs/task-completions/2026-06-18-18-tab-engine-product-architecture.md`
- Changed:
  - None
- Deleted:
  - None
- Generated artifacts:
  - None

## Tests And Checks

Commands run:

- `sed -n '1,520p' AGENTS.md`
  - Passed. Read repo protocol and workflow requirements.
- `git status --short`
  - Passed before editing. Showed broad pre-existing dirty worktree unrelated to this task.
- `ls docs/handoffs/task-completions | tail -40`
  - Passed. Reviewed recent handoff names for current coordination context.
- `test -f docs/handoffs/task-completions/2026-06-18-18-tab-engine-product-architecture.md; printf '%s\n' $?`
  - Passed. Returned `1`, confirming this file did not already exist.
- `sed -n '1,260p' docs/tab-feature-guardrails.md`
  - Passed. Used for tab-specific rights and product guardrails.
- `sed -n '1,260p' docs/e9-fretboard-position-engine.md`
  - Passed. Used for deterministic pitch/position architecture alignment.
- `sed -n '1,260p' docs/steel-guitar-rag-fretboard-product-concept.md`
  - Passed. Used for fretboard sync/product mode alignment.
- `sed -n '1,260p' docs/llm-guidance/teacher-first-answer-policy.md`
  - Passed. Used for answer-shape and source-fragment guardrails.

- `git status --short`
  - Passed after editing. Broad dirty worktree remains and includes unrelated parked/runtime files; this task's scoped status shows only this new handoff.
- `git diff --check`
  - Passed.
- `git diff --no-index --check -- /dev/null docs/handoffs/task-completions/2026-06-18-18-tab-engine-product-architecture.md`
  - Passed. Used because this handoff is new and untracked, so normal `git diff --check` does not inspect its contents.
- `git status --short -- docs/handoffs/task-completions/2026-06-18-18-tab-engine-product-architecture.md`
  - Passed. Shows `?? docs/handoffs/task-completions/2026-06-18-18-tab-engine-product-architecture.md`.

Skipped tests:

- Unit, API, browser, and eval tests were skipped because this was a docs-only architecture task with no executable behavior changed.

## Integration Notes

- Future implementation should start with a tab payload/data contract, not generation.
- Lane 05 should not wire tab into `/api/answer` until Lane 15 has reviewed fixtures and guardrails.
- Lane 06 should design rendering from structured events, not from raw ASCII-only strings.
- Lane 15 should create explicit refusal and impossible-tab buckets before public rollout.
- RAG integration should remain supporting-only for tab generation until deterministic tab validation exists.

## Human Decision Needed

No for this architecture handoff.

Future product decision needed before implementation: choose whether the first runtime tab slice is protected-preview only or hidden behind an internal feature flag with no UI exposure.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-18-tab-engine-product-architecture.md`

## Files That Must Not Be Staged

- Any pre-existing dirty files outside the safe-to-stage path above.
- App code, backend implementation files, UI files, tests, deployment files, auth files, Chroma/vector data, embeddings, corpus-private, source-inbox data, generated reports, raw design assets, and secrets.

## Commit Readiness

Safe to commit

## Recommended Next Lane

Recommended lane: `15 QA / Answer Eval`.

Suggested next step: Lane 15 should run a design review of this tab engine architecture and create tab-specific QA fixture buckets before Lane 05 defines runtime schemas.
