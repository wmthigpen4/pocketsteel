# 2026-06-19 - Lane 18 - Parameterized Chord Movement Contract

## Task Summary

Requested: define the product/API contract for deterministic parameterized E9 chord-movement examples before backend implementation.

Completed: created this Lane 18 product/architecture handoff for a narrow v2 tab feature that supports beginner-safe standard E9 movement examples for `I-IV`, `I-V`, and `I-IV-V-I`.

Intentionally not changed:

- No backend implementation.
- No UI implementation.
- No tests.
- No deployment, auth, DNS, corpus, scraping, embeddings, Chroma/vector stores, secrets, private transcripts, or assets.
- No public-domain song tab, melody-to-tab, user song arrangement, arbitrary fake tab, or SGF-derived exact tab behavior.

Task type: docs-only product/API contract.

Lane: `18 Product / Architecture`.

Task mode: GREEN for this docs handoff. Future backend implementation is YELLOW because it will change answer routing, helper behavior, contract tests, and API/tab test coverage.

Repo guidance read:

- `AGENTS.md`
- `agents.md`
- `README.md`
- `docs/handoffs/task-completions/integration-status.md`

Local guidance conflicts: none.

## Current State

The landing-page slice is complete and integration status records the private-preview landing refresh through:

- `0bbdef0 refresh private preview landing page`
- `3f1b3dc docs: record private preview landing smoke`
- `d10fb85 docs: refresh integration status after landing smoke`

The tab path currently has:

- `steel_guitar_rag/tab_engine.py`
  - `TabEvent` and `TabNote` structured events.
  - Default 10-string E9 profile.
  - String-aware A/B/C/E/F/V/G/D control validation.
  - 0-24 fret validation.
  - One to three notes per event.
  - One fret per multi-note event until slants exist.
  - Fixed-width rendered tab generated from events.
- `steel_guitar_rag/answer_tab_examples.py`
  - deterministic answer-tab selection for safe prompts,
  - static fretboard-first examples for static grips,
  - `tab_example` payloads for movement/lick/control examples,
  - derived fretboard payloads from the same validated tab events.
- Existing API contract:
  - top-level response key is `tab_example`;
  - `tab_example.events` are source of truth;
  - `tab_example.rendered_tab` is renderer output;
  - `tab_example.validation.ok` must be `true` for normal display;
  - optional `fretboard` payload can be generated from tab events.

Current product rule:

- SVG fretboard owns static positions.
- Tab engine owns movement over time.
- Static grip/chord answers should remain fretboard-first.
- Movement, licks, fills, transitions, pedal/lever choreography, and phrase sequences may use tab plus fretboard.

## Product Goal

Add a deterministic parameterized chord-movement feature that can answer common beginner movement prompts without requiring a hand-entered tab example for every key.

The first version should support:

- standard 10-string E9 only,
- major keys only,
- compact original educational examples,
- `I-IV`,
- `I-V`,
- `I-IV-V-I`,
- practical beginner-safe positions and controls,
- one short tab example plus a derived fretboard payload.

This is not:

- SGF-derived tab,
- public-domain song tab,
- copyrighted song tab,
- melody-to-tab,
- a full arrangement engine,
- LLM-generated ASCII tab.

## Supported Movement Request Shapes

The selector should treat these as eligible only when the request is clearly asking for a movement, transition, lick-like example, or short practice phrase:

- "Show me a G to C move."
- "Give me a simple I-IV move in G."
- "Show a I to V move in A."
- "Give me a simple 1-4-5-1 movement on E9."
- "Show a beginner G-C-D-G movement."
- "Give me a short A to D to E to A example."
- "Show a simple pedal steel transition from I to IV in C."
- "Give me a beginner-safe I-IV-V-I phrase."

Eligible terms:

- `move`
- `movement`
- `transition`
- `phrase`
- `short example`
- `beginner example`
- `pedal move`
- `walk from`
- `go from`
- `I-IV`
- `I-V`
- `I-IV-V-I`
- `1-4`
- `1-5`
- `1-4-5-1`

Static requests remain fretboard-first and should not attach tab by default:

- "Where is G major?"
- "Show me G major positions."
- "What fret is C?"
- "Show a 4-5-6 grip."
- "Where can I play an A chord?"

## Accepted Key And Progression Inputs

### Keys

Initial implementation should support major roots only:

- C
- C# / Db
- D
- D# / Eb
- E
- F
- F# / Gb
- G
- G# / Ab
- A
- A# / Bb
- B

Enharmonic handling:

- Normalize internally to pitch class.
- Preserve the user-facing spelling where practical in titles and answer copy.
- Do not support minor keys in this slice.

### Progressions

Accepted progression forms:

- Roman numerals: `I-IV`, `I-V`, `I-IV-V-I`
- Arabic Nashville-like numbers: `1-4`, `1-5`, `1-4-5-1`
- Direct chord pairs/triples when they match a major-key relationship:
  - `G to C`
  - `G to D`
  - `G C D G`
  - `A to D`
  - `A to E`
  - `A D E A`

Rejected or deferred:

- minor progressions,
- dominant 7ths,
- jazz changes,
- modal changes,
- chromatic progressions,
- arbitrary chord strings,
- named song progressions,
- slash chords,
- substitutions,
- all-positions enumeration.

## Movement Families

The backend should start with a limited set of deterministic movement families. Each family needs fixtures and tab-engine validation.

### I-IV: Same-Fret A+B Partial

Starter example:

- Key: G
- Event 1: G at fret 3, strings 4-5-6, no pedals.
- Event 2: C partial at fret 3, strings 5-6 with A+B.

Reason:

- Keeps the bar still.
- Demonstrates A+B movement.
- Uses existing validated `g_to_c` semantics.
- Works as a starter movement even when the IV event is a partial grip.

### I-V: Nearby Major Position

Recommended starter strategy:

- Use a short two-event move from I to a nearby validated V position.
- Prefer a common major family already supported by the pitch/position engine.
- Keep one grip and short bar movement where possible.
- If no beginner-safe deterministic V path is validated for a key, omit tab.

Implementation must not invent pedal/lever stacks to force a V movement.

### I-IV-V-I: Short Phrase Sequence

Recommended starter strategy:

- Build from validated `I-IV` and `I-V` movement families.
- Keep total event count between 3 and 4.
- Prefer repeated simple grips over richer voicings.
- Title and explanation must say this is a short educational movement, not a song phrase.

Example target:

- G to C partial to D position to G return.

Only implement after the individual `I-IV` and `I-V` families pass fixtures.

## Expected Backend Payload Shape

Use the existing top-level `tab_example` key.

Conceptual shape:

```json
{
  "tab_example": {
    "id": "movement-g-i-iv-456-v1",
    "title": "G I-IV beginner move",
    "kind": "parameterized_chord_movement",
    "display_tab": true,
    "preferred_display": "tab_and_fretboard",
    "context": {
      "key": "G",
      "root": "G",
      "quality": "major",
      "progression": "I-IV",
      "chords": ["G", "C"],
      "movementType": "I-IV",
      "tuning": "E9",
      "profile": "default_e9",
      "difficulty": "beginner",
      "tier": "starter",
      "grip": "4-5-6",
      "rightsStatus": "original_educational_example",
      "provenanceType": "deterministic_exercise",
      "sourcePolicy": "no_external_song_source",
      "generator": "parameterized_e9_chord_movement_v1"
    },
    "rendered_tab": "Ch |G     C partial\n 1 |\n ...",
    "validation": {
      "ok": true,
      "issues": [],
      "profile": "default_e9",
      "eventCount": 2
    },
    "explanation": "A short original G-to-C movement. Keep the bar at fret 3, then press A+B on strings 5 and 6 for a compact IV sound.",
    "intervals": [
      {
        "eventId": "movement-g-i-iv-456-v1-event-1",
        "chord": "G",
        "byString": {"4": "1", "5": "5", "6": "3"}
      },
      {
        "eventId": "movement-g-i-iv-456-v1-event-2",
        "chord": "C partial",
        "byString": {"5": "3", "6": "1"}
      }
    ],
    "events": [
      {
        "id": "movement-g-i-iv-456-v1-event-1",
        "label": "I",
        "chord": "G",
        "function": "I",
        "notes": [
          {"string": 4, "fret": 3, "changes": []},
          {"string": 5, "fret": 3, "changes": []},
          {"string": 6, "fret": 3, "changes": []}
        ]
      },
      {
        "id": "movement-g-i-iv-456-v1-event-2",
        "label": "IV",
        "chord": "C partial",
        "function": "IV",
        "notes": [
          {"string": 5, "fret": 3, "changes": ["A"]},
          {"string": 6, "fret": 3, "changes": ["B"]}
        ]
      }
    ]
  }
}
```

Compatibility rules:

- Existing UI/API consumers currently require `id`, `title`, `context`, `rendered_tab`, `validation`, `explanation`, `intervals`, and `events`.
- Additional fields like `kind`, `display_tab`, `preferred_display`, `context.provenanceType`, and `events[].function` may be added only if contract tests allow them.
- If strict API contract tests require exact key sets, update tests intentionally in Lane 05.
- Do not switch to `tabExample` in this slice unless the API contract is deliberately migrated. Current code/tests use `tab_example`.

## Expected Tab-Event Semantics

Each tab event is a musical state in time.

Required event semantics:

- Event order is phrase order.
- Each event has one chord/function target.
- Each event has one to three notes.
- Multi-note events stay on one fret.
- `notes[].string` uses string numbers 1-10.
- `notes[].fret` uses frets 0-24.
- `notes[].changes` uses tab-engine control labels, currently `A`, `B`, `C`, `E`, `F`, `V`, `G`, `D`.
- Chord labels should be learner-facing: `G`, `C partial`, `D`, etc.
- Function labels should be progression-facing: `I`, `IV`, `V`.

Recommended additions for this slice:

- `events[].id`
- `events[].label`
- `events[].function`
- `context.movementType`
- `context.progression`
- `context.chords`
- `context.provenanceType`
- `context.sourcePolicy`
- `context.generator`

Tab event ids should be stable for a given generator version, key, movement type, and event index.

## Expected Fretboard Relationship

The tab event list is the source of truth for movement examples.

Rules:

- For movement examples, backend may attach both `tab_example` and `fretboard`.
- The `fretboard` payload must be derived from the same validated tab events.
- Fretboard position count should match tab event count unless future UI deliberately collapses duplicate states.
- Position ids should follow the existing convention:
  - `{tab_example.id}-event-{index}`
- Position `positionKind` should remain `tab_example_event`.
- Position `family` should remain `tab_example`.
- Fretboard `sourceContext` should be a deterministic rule context, not SGF.
- No raw x/y geometry is allowed.

Product rule:

- Static grip/chord answers remain fretboard-first.
- Movement answers use tab as the time sequence and fretboard as the state visualization.

## Validation Requirements

### Mechanical Validation

Every generated movement must pass existing `tab_engine` validation before being attached to `/api/answer`.

Required checks:

- valid `default_e9` profile,
- strings 1-10,
- frets 0-24,
- known controls,
- controls only on affected strings,
- one to three notes per event,
- no duplicate strings inside an event,
- no mixed-fret multi-note event,
- renderer output non-empty,
- `validation.eventCount == len(events)`.

If validation fails:

- do not attach `tab_example`,
- do not attach derived movement fretboard payload,
- return answer-only fallback or static fretboard answer if appropriate.

### Musical Validation

The generator must also validate the movement intent:

- requested key parses as a major root,
- requested progression is one of `I-IV`, `I-V`, `I-IV-V-I`,
- generated chords match the requested progression,
- event labels/functions match event order,
- generated notes/intervals match the intended chord or documented partial,
- movement is beginner-safe for `difficulty=beginner`,
- no unsupported arbitrary pedal/lever combinations.

If musical validation fails:

- omit the tab example,
- do not fall through to SGF fragments as generated tab evidence,
- answer with a safe explanation or ask for a narrower request.

## Source And Provenance Labeling

Parameterized chord movements are deterministic/original educational examples.

Required labeling:

- `rightsStatus`: `original_educational_example`
- `provenanceType`: `deterministic_exercise`
- `sourcePolicy`: `no_external_song_source`
- `generator`: `parameterized_e9_chord_movement_v1`
- fretboard `sourceContext.kind`: `rule`
- fretboard `sourceContext.sourceId`: implementation module id, likely `steel_guitar_rag.answer_tab_examples`

Required behavior:

- Do not cite SGF as supporting the exact generated tab.
- Do not cite public-domain song sources.
- Do not imply this is a song arrangement.
- Do not use retrieved SGF tab fragments to generate events.
- Source cards may still appear for answer context if the answer route is source-backed, but the tab payload itself remains deterministic.

## Supported Prompt Examples

Should attach `tab_example` when implemented and validated:

- "Show me a G to C move."
- "Give me a simple I-IV move in G."
- "Show a beginner I to IV movement in A."
- "Give me a simple 1-4 move on E9 in C."
- "Show a I-V move in G."
- "Give me a beginner 1-5 move in D."
- "Show G to D as a short E9 movement."
- "Show a simple I-IV-V-I in G."
- "Give me a beginner 1-4-5-1 pedal steel example in A."
- "Show G-C-D-G as a short movement, not a song."

Should remain fretboard-first without `tab_example`:

- "Where can I play G major?"
- "Show me C chord positions."
- "What frets give me A major?"
- "Show a 4-5-6 G grip."

## Intentionally Unsupported Prompts

Do not attach generated movement tab for:

- "Tab the whole song."
- "Give me tab for Together Again."
- "Show the solo from Panhandle Rag."
- "Transcribe this recording."
- "Make a public-domain arrangement of [title]" in this slice.
- "Turn this melody into tab."
- "Here are my lyrics and chords, arrange them."
- "Give me a minor I-IV-V."
- "Show a blues I7-IV7-V7 turnaround."
- "Give me all possible I-IV positions."
- "Use SGF posts to generate tab."
- "Generate a Lloyd Green-style solo."
- "Use my custom copedent."

Safe fallback:

- Explain the supported scope.
- Offer a short original E9 movement exercise.
- For static chord questions, return deterministic fretboard-first content.

## Recommended Backend Implementation Slice

Recommended Lane 05 target:

- Extend `steel_guitar_rag.answer_tab_examples` or add a small helper module for parameterized movement generation.
- Keep output behind existing answer-tab routing behavior and current `tab_example` key.
- Generate structured `TabEvent` objects, then render/validate through `steel_guitar_rag.tab_engine`.
- Add deterministic parsing for major key plus `I-IV`, `I-V`, `I-IV-V-I`.
- Start with a small fixture-backed key set if necessary. Expand to all 12 major roots only after pitch/position fixtures prove correctness.
- Keep static grip/chord requests fretboard-first.
- Attach a derived fretboard payload from the same event list.
- Add focused tests before any protected-preview smoke.

Suggested implementation order:

1. Add parser tests for supported/unsupported movement request shapes.
2. Add event-builder tests for G `I-IV`, G `I-V`, and G `I-IV-V-I`.
3. Add transposition/normalization tests for at least A and C if all-key support is attempted.
4. Add payload-shape tests for `tab_example`.
5. Add answer API tests that supported movement prompts attach tab and static chord prompts remain fretboard-first.
6. Add guardrail tests for song/copyright/melody/user-copedent prompts.

## Exact Lane 05 Prompt Target

```text
Lane: 05 Backend / RAG Integration
Reasoning level: HIGH

Task: Implement deterministic parameterized E9 chord-movement examples.

Read:
- AGENTS.md
- docs/handoffs/task-completions/2026-06-19-18-parameterized-chord-movement-contract.md
- steel_guitar_rag/tab_engine.py
- steel_guitar_rag/answer_tab_examples.py
- steel_guitar_rag/api.py
- steel_guitar_rag/api_contract.py
- tests/test_tab_engine.py
- tests/test_api_contract.py
- tests/test_api_search.py

Goal:
Implement a narrow deterministic v2 movement generator for standard 10-string E9 major-key `I-IV`, `I-V`, and `I-IV-V-I` examples.

Requirements:
- Use current `tab_example` response key.
- Generate structured `TabEvent`/`TabNote` data first.
- Render and validate via `steel_guitar_rag.tab_engine`.
- Attach derived fretboard payload from the same event list.
- Keep static chord/grip answers fretboard-first.
- Label outputs as deterministic/original educational examples.
- Do not cite SGF or public-domain sources for exact generated tab.
- Do not generate song tab, melody-to-tab, user song arrangements, public-domain arrangements, or custom-copedent examples.

Tests:
- focused parser/generator tests,
- tab validation tests,
- API contract tests,
- answer API tests for supported movement prompts,
- negative tests for static chord prompts, copyrighted song tab, public-domain arrangement prompts, melody-to-tab prompts, and custom copedent prompts.

Do not:
- touch UI files,
- touch deployment/auth/DNS,
- touch corpus, scraping, embeddings, Chroma/vector stores, private transcripts, secrets, or assets.

Write a completion handoff under docs/handoffs/task-completions/.
```

## Checks Run

Commands run:

- `git status --short`
  - Passed before and after handoff creation. The worktree has broad unrelated dirty/untracked files; this task created only the new handoff.
- `git diff --check`
  - Passed.
- `git diff --no-index --check -- /dev/null docs/handoffs/task-completions/2026-06-19-18-parameterized-chord-movement-contract.md`
  - Passed. Used because the handoff is new and untracked, so normal `git diff --check` does not inspect its contents.
- `rg -n "markdownlint|markdown lint|mdformat|prettier|remark" README.md AGENTS.md docs/current-commands.md pyproject.toml package.json Makefile 2>/dev/null || true`
  - Passed. No documented lightweight markdown lint/check command was found.
- lightweight markdown lint/check if documented
  - Skipped because no documented lightweight markdown lint/check command was found.
- `git diff --cached --name-only`
  - Passed before staging. No cached files were present.
- `git diff --cached`
  - Passed after exact staging. Cached diff contains only this new handoff.
- `git diff --cached --check`
  - Passed after exact staging.

Skipped:

- Unit/API/UI/browser tests. This task is docs-only.

## Risks

Risk level: medium for future implementation, low for this handoff.

Future implementation risks:

- Incorrect transposition can generate plausible but wrong tab.
- I-V movement may be less obvious than I-IV and needs fixture-backed validation.
- Partial IV events can be musically useful but must be labeled clearly as partial.
- Broad keyword matching could attach tab to static chord-location answers.
- Source/provenance ambiguity could make deterministic exercises look SGF-derived.

Mitigations:

- Start with fixture-backed movement families.
- Validate mechanically through `tab_engine`.
- Validate musically against requested progression.
- Keep static chord answers fretboard-first.
- Add negative routing tests.
- Keep provenance labels explicit.

## Blockers

No blocker for this architecture handoff.

Potential future implementation blocker:

- If the current pitch/position helper cannot safely produce I-V examples for enough keys, Lane 05 should implement only fixture-backed G/A/C examples first or return no tab for unsupported keys.

## Files Touched

- Created:
  - `docs/handoffs/task-completions/2026-06-19-18-parameterized-chord-movement-contract.md`
- Changed:
  - None
- Deleted:
  - None
- Generated artifacts:
  - None

## Safe-To-Stage Files

- `docs/handoffs/task-completions/2026-06-19-18-parameterized-chord-movement-contract.md`

## Files That Must Remain Unstaged

- Any pre-existing dirty or untracked files outside the safe-to-stage path above.
- Backend implementation files.
- UI implementation files.
- Tests.
- Deployment/auth/DNS files.
- Corpus, scraping, embeddings, Chroma/vector stores, secrets, private transcripts, generated reports, and assets.
- `docs/handoffs/task-completions/integration-status.md`

## Recommended Next Lane

Lane 05 Backend / RAG Integration.

Next action:

- Implement deterministic parameterized movement examples using the prompt target above.

## Commit Readiness

Safe to commit if exact staging and cached checks remain limited to:

- `docs/handoffs/task-completions/2026-06-19-18-parameterized-chord-movement-contract.md`
