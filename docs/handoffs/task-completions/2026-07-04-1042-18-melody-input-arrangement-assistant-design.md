# 2026-07-04 10:42 - Lane 18 - Melody Input / Arrangement Assistant v0 Design

## Task Summary

Requested: design Melody Input / Arrangement Assistant v0 as a future deterministic teaching feature without implementing runtime behavior.

Completed: created this implementation-ready product and technical contract for a future feature that turns short original or user-provided melody fragments into E9 learning exercises with validated fretboard, tab, and movement guidance.

Intentionally not changed:

- No backend implementation.
- No UI implementation.
- No tests.
- No app runtime behavior.
- No corpus, scraping, embeddings, Chroma/vector stores, source-inbox, auth, DNS, deployment config, private transcripts, licensing metadata, secrets, or assets.
- No public-domain song support was added.
- No song tab, recording transcription, YouTube transcription, artist solo reconstruction, or arbitrary LLM tab generation was added.

Task type: docs-only architecture/design.

Lane: `18 Product / Architecture`.

Task mode: GREEN for this handoff. Future implementation is YELLOW because it will add answer/API contracts, validation rules, UI flows, and test coverage.

## User Value

The feature should help a beginner turn a tiny musical idea into a playable E9 learning exercise:

- enter a short melody fragment or scale-degree line,
- choose a key and approximate pocket,
- see one practical place to play it,
- optionally add one slide-in, one pedal-squeeze, one harmonized interval, or one practice route,
- understand why the placement works,
- practice it through synchronized fretboard, tab, and step-by-step explanation.

The product promise is "I will help you turn a small idea into a mechanically valid original exercise," not "I will transcribe a song."

## Product Boundary

Melody Input / Arrangement Assistant v0 should produce deterministic teaching exercises only. It must not become:

- arbitrary song tab generation,
- full copyrighted arrangement generation,
- YouTube/audio/recording transcription,
- artist solo reconstruction,
- commercial lesson reconstruction,
- public-domain arrangement generation without a reviewed registry,
- LLM-only fake tab,
- SGF/forum fragment copying.

The app should clearly distinguish:

- `original_deterministic_exercise`: app-created short exercise from rules.
- `user_provided_melody`: short fragment the user supplies or claims as theirs.
- `source_backed_lesson_idea`: source supports a concept, not exact generated notes.
- `public_domain_registry_arrangement`: future only; requires verified registry/provenance.
- `blocked_copyright_or_transcription`: refusal/redirect path.

## Supported v0 Inputs

Safe v0 input should be narrow and structured.

Required:

- `key`: major key first; minor deferred unless explicitly validated.
- `tuning`: `E9`.
- `melody`: short sequence of note names or scale degrees.
- `input_kind`: `original_prompt` or `user_provided_melody`.
- `rights_attestation`: user confirms this is original, user-provided, or otherwise theirs to use.

Recommended limits:

- 2 to 8 melody events.
- Single-note melody only.
- Optional simple durations: `short`, `long`, `quarter`, `half`, or omitted.
- Optional octave/register hints, but no requirement for exact staff notation.
- Optional pocket preference: open, low, mid, high, or "near fret N".
- Optional difficulty: beginner, intermediate.
- Optional transformations:
  - `plain_placement`
  - `slide_in`
  - `pedal_squeeze`
  - `harmonized_interval`
  - `practice_route`

Allowed prompt examples:

- "Here is my own little line: 1 2 3 5 in G. Show me a beginner E9 exercise."
- "Turn G A B D into a simple E9 practice phrase."
- "Make a short original G major scale-degree exercise: 1 3 4 5."
- "Show one way to play 3 2 1 in C on E9."
- "Give this tiny melody a slide-in option: G A B."
- "Harmonize my short line 1 2 3 in G with simple thirds."

## Blocked Or Redirected Inputs

The feature should block or redirect when the user asks for protected or unverifiable material.

Hard block:

- "Tab the whole song."
- "Transcribe this YouTube recording."
- "Give me the full tab for [modern copyrighted song]."
- "Write the exact solo from [artist/recording]."
- "Arrange the full modern copyrighted song for E9."
- "Turn this commercial lesson into tab."
- "Generate the complete Steel Guitar Rag arrangement" unless a separate verified rights/source path exists and is explicitly enabled.

Redirect:

- "Tab [song title]" -> explain that full-song tab requires rights/provenance and offer a short original exercise in the same key or progression type.
- "This is public domain, arrange it" -> require a reviewed public-domain registry entry before generation; offer an original exercise instead.
- Long pasted melodies -> ask the user to shorten to a 2-8 note fragment and confirm they have rights to use it.
- Audio/video links -> state that v0 does not transcribe recordings; offer a manual short-fragment input form.

## Backend Contract

Recommended request shape for a future endpoint or answer-route helper:

```json
{
  "schema_version": "melody_assistant_v0",
  "input_kind": "user_provided_melody",
  "rights_attestation": "user_supplied_or_original",
  "key": "G",
  "tuning": "E9",
  "copedent_id": "emmons_e9",
  "melody": [
    {"token": "1", "token_kind": "scale_degree", "duration": "quarter"},
    {"token": "2", "token_kind": "scale_degree", "duration": "quarter"},
    {"token": "3", "token_kind": "scale_degree", "duration": "quarter"},
    {"token": "5", "token_kind": "scale_degree", "duration": "half"}
  ],
  "options": {
    "difficulty": "beginner",
    "position_preference": "mid",
    "preferred_strings": [],
    "include": ["plain_placement", "slide_in", "pedal_squeeze", "harmonized_interval"],
    "max_events": 8
  }
}
```

Recommended answer payload addition:

```json
{
  "answer": "Here is a short original G exercise from your 1-2-3-5 line. Start by learning the plain placement, then try the slide-in option slowly.",
  "sources": [],
  "warnings": [],
  "melody_exercise": {
    "schema_version": "melody_assistant_v0",
    "id": "melody-g-1235-v1",
    "title": "Original G 1-2-3-5 exercise",
    "kind": "deterministic_melody_exercise",
    "provenance": {
      "type": "user_provided_melody",
      "rights_status": "user_supplied_or_original",
      "source_policy": "no_external_song_source",
      "source_ids": [],
      "generator": "e9_melody_assistant_v0"
    },
    "input": {
      "key": "G",
      "tokens": ["1", "2", "3", "5"],
      "token_kind": "scale_degree"
    },
    "events": [
      {
        "id": "melody-step-1",
        "step": 1,
        "input_token": "1",
        "resolved_note": "G",
        "scale_degree": "1",
        "string": 6,
        "fret": 3,
        "changes": [],
        "duration": "quarter",
        "technique": "pick",
        "explanation": "Start on the root in the G pocket."
      }
    ],
    "variations": [
      {
        "id": "plain",
        "label": "Plain placement",
        "events": []
      },
      {
        "id": "slide_in",
        "label": "Slide-in option",
        "events": []
      }
    ],
    "validation": {
      "ok": true,
      "mechanical": [],
      "musical": [],
      "steel_practical": [],
      "copyright": []
    },
    "fretboard": {},
    "tab_example": {},
    "lesson_card": {}
  }
}
```

Contract rules:

- `melody_exercise` is optional and must not replace existing `fretboard`, `tab_example`, `progression_guide`, or source-card contracts.
- Structured events are the source of truth.
- Rendered tab is derived from validated events, never hand-authored by the answer composer.
- Fretboard markers are derived from the same validated events as tab.
- `sources` should be `[]` for deterministic original/user-provided exercises.
- Source cards may appear only when supporting a general lesson concept, not as provenance for generated exact notes.
- `provenance.type` and `rights_status` are required.
- Invalid or blocked requests should not attach `melody_exercise`, `tab_example`, or `fretboard`.

## Validation Layers

The implementation needs five validation layers before any rendered output appears.

Input validation:

- Parse note names and scale degrees deterministically.
- Reject ambiguous, long, or song-like requests.
- Require key and rights/provenance classification.
- Cap event count and reject bulk text.

Mechanical validation:

- Use existing E9 pitch/copedent logic.
- Validate strings, frets, controls, affected strings, and no inert pedals/levers.
- Keep tab and fretboard payloads synchronized.

Musical validation:

- Resolve scale degrees in key.
- Label accidentals with clear spelling.
- Keep top note and harmony claims honest.
- Do not label partial voicings as complete chords.

Steel-practical validation:

- Prefer playable pockets over exhaustive possibilities.
- Avoid large bar jumps in beginner output.
- Prefer common grips and simple control movement.
- Warn when an option is mechanically valid but awkward.

Source/provenance/copyright validation:

- Block copyrighted/full-song/solo/transcription requests before planning.
- Do not accept public-domain claims without a registry record.
- Do not use SGF/forum snippets as generated tab material.
- Do not cite sources for deterministic event choices unless the exact source/provenance category supports it.

## Frontend UX Contract

Recommended v0 UI flow:

1. Entry point labeled as a small learning tool, not song arrangement.
2. Melody input accepts note chips or scale-degree chips.
3. Key selector and optional pocket selector.
4. Difficulty control: beginner/intermediate.
5. Transformation buttons:
   - Plain
   - Slide
   - Pedal squeeze
   - Harmony
   - Route
6. A visible rights/provenance confirmation:
   - "This is my short original/user-provided phrase."
7. Result view:
   - concise answer summary,
   - event stepper,
   - synced fretboard,
   - fixed-width tab,
   - explanation panel,
   - warnings/provenance label.

UI requirements:

- The fretboard should remain the visual center.
- The event stepper should sync selected step, tab highlight, fretboard marker, and explanation.
- Color buttons should represent variation types, not arbitrary decorative colors.
- The UI should not display source cards for deterministic exercises with `sources: []`.
- The UI should show provenance as concise learner-facing copy: "Original exercise from your short phrase."
- Mobile layout must preserve tab spacing through horizontal scroll.
- No `[object Object]` fallback rendering.

## Public-Domain Boundary

Public-domain song support is not part of v0.

Future public-domain arrangement support requires:

- a curated song registry,
- reviewed rights status,
- source IDs for melody/progression data,
- structured melody records,
- an arrangement planner,
- separate UI/source copy,
- tests proving blocked and enabled states.

Until that exists, public-domain claims should route to:

"I can help with a short original exercise in that style or key, but I need a reviewed public-domain source record before generating a song arrangement."

## Test Plan

Lane 05 backend tests:

- parser accepts note-name fragments and scale-degree fragments.
- parser rejects long song-like requests.
- copyright guardrails block named songs, YouTube, recordings, full arrangements, and solos.
- event planner emits validated E9 events.
- tab and fretboard are generated from the same events.
- provenance fields are required.
- deterministic exercises return `sources: []`.
- blocked prompts return no `melody_exercise`, no `tab_example`, no `fretboard`.
- API contract allows optional `melody_exercise`.

Lane 06 frontend tests:

- melody exercise normalizes into UI state.
- event stepper renders.
- tab spacing is preserved.
- fretboard markers sync with events.
- variation buttons switch visible event sets.
- source section is hidden for source-free deterministic exercises.
- blocked responses clear stale melody/tab/fretboard UI.
- mobile/narrow viewport preserves tab alignment.

Lane 15 QA smoke:

- allowed original fragments produce exercises.
- blocked song/transcription prompts refuse cleanly.
- public-domain claims remain blocked without registry.
- no source-card substitution.
- no raw internal provenance objects.
- no `[object Object]`.

## Likely Future Files

Lane 05:

- `pocketsteel/melody_assistant.py`
- `pocketsteel/api.py`
- `pocketsteel/api_contract.py`
- `pocketsteel/tab_engine.py` only if event rendering needs a small extension.
- `tests/test_melody_assistant.py`
- `tests/test_api_contract.py`
- `tests/test_api_search.py`

Lane 06:

- `ui/answer-client.js`
- `ui/steel-guitar-rag-mock.html`
- `ui/pedal-steel-fretboard.js` only if step sync needs renderer support.
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`

Lane 15:

- exploratory smoke script coverage only after the backend/UI contracts exist.

## Smallest Safe Implementation Slice

The smallest safe implementation slice is backend contract and validation only, behind a disabled or narrow explicit route:

1. Add `pocketsteel/melody_assistant.py` with parser, rights classifier, blocker, and event contract.
2. Support only 2-8 note/degree fragments in major keys.
3. Generate only `plain_placement` for G and C first, or even fixtures only if broader planning is not ready.
4. Return structured `melody_exercise` without exposing it in the main UI by default.
5. Add API contract tests and guardrail tests.

Do not start with UI or public-domain arrangements. The backend needs to prove the safety boundary first.

## Recommended Next Implementation Prompt

Lane 05 Backend / RAG Integration:

```text
Use AGENTS.md autopilot mode.

Primary lane: Lane 05 Backend / RAG Integration
Reasoning level: High

Implement Melody Input / Arrangement Assistant v0 backend contract only, behind the narrow deterministic contract in docs/handoffs/task-completions/2026-07-04-1042-18-melody-input-arrangement-assistant-design.md.

Scope:
- Add a parser/validator module for 2-8 note or scale-degree fragments.
- Support E9, major keys, and original/user-provided melody exercises only.
- Add provenance/rights classification.
- Block song titles, full arrangements, artist solos, YouTube/recording transcription, and public-domain claims without registry records.
- Produce a structured `melody_exercise` payload from deterministic validated events.
- Do not expose a broad UI yet.
- Do not add public-domain song support.
- Do not touch corpus, scraping, embeddings, Chroma/vector stores, auth, DNS, deployment, secrets, private transcripts, licensing metadata, or assets.

Tests:
- parser/unit tests
- API contract tests
- API guardrail tests for blocked prompts
- source suppression tests for deterministic exercises
- `git diff --check`

Write a Lane 05 handoff and exact-path commit if green.
```

## Tests And Checks Run

Run for this docs-only slice:

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log --oneline -5`
- `sed` inspections of answer contract, product memory, known failures, tab guardrails, copyright/provenance docs, and related movement/progression handoffs.
- `git diff --check` pending after this handoff is written.

Skipped:

- Runtime tests, browser smoke, protected-preview smoke, and pytest were not run because this task intentionally changed docs only.

## Integration Notes

- This handoff is a future contract only.
- It should not be treated as approval to implement melody input, song arrangements, public-domain registry support, or UI runtime behavior.
- Future work should keep deterministic exercise generation, source-backed concepts, user-provided melody, and public-domain arrangements as separate provenance categories.

## Risk Assessment

Risk: low.

Why:

- Docs-only architecture handoff.
- No runtime behavior changed.
- The design explicitly keeps copyrighted song/tab/transcription and public-domain arrangement support out of v0.

Rollback:

- Revert this handoff and any matching integration-status note.

## Human Decision Needed

No for this design handoff.

Yes before future implementation if the product wants public-domain song arrangement support; that needs a separate registry/provenance design and reviewed source records.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-07-04-1042-18-melody-input-arrangement-assistant-design.md`
- `docs/handoffs/task-completions/integration-status.md` if refreshed for this docs-only contract.

## Files That Must Not Be Staged

All unrelated parked files shown by `git status --short`, especially:

- `README.md`
- `corpus_metadata/**`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- `rag_*.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- `corpus-private/**`
- `corpus-v2/**`
- Chroma/vector stores
- private/generated/source/license artifacts
- unrelated untracked handoffs/assets

## Recommended Next Lane

Lane 05 Backend / RAG Integration for the smallest backend-only parser/contract slice, after the user approves moving from design into implementation.

## Commit Readiness

Safe to commit after `git diff --check`, exact-path staging, staged diff review, and `git diff --cached --check`.

## Suggested Next Step

Use the recommended Lane 05 prompt above only when ready to start implementation. Do not combine it with Melody Input UI, public-domain song arrangements, or Voicing Identifier follow-on work.
