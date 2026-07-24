# Answer-Triggered Tab Examples Architecture

## Task Summary

- What was requested: define the next backend architecture slice for safely attaching deterministic `tab_example` payloads to normal answer responses in Steel Guitar RAG.
- What was completed: created this Lane 18 architecture handoff for answer-triggered tab examples, including current state, product goal, proposed response contract, intent routing strategy, deterministic example registry, safe generation ladder, backend integration points, test plan, risks, and the next Lane 05 implementation prompt.
- What was intentionally not changed: no app code, frontend files, UI implementation, tests, `/api/answer`, `/api/tab/render`, SGF retrieval, Chroma/vector stores, embeddings, corpus data, source-inbox data, auth, deployment, staging, or commits were changed.

## Current State

Committed backend slice:

- Commit: `686fd3c feat: add deterministic tab engine slice`
- Module: `steel_guitar_rag/tab_engine.py`
- Route: `POST /api/tab/render` in `steel_guitar_rag/api.py`
- Tests: `tests/test_tab_engine.py`

The committed tab engine provides:

- deterministic structured `TabEvent` / `TabNote` data,
- default 10-string E9 profile,
- validation for strings, frets, duplicate strings, mixed frets, note count, unknown changes, and changes placed on unaffected strings,
- fixed-width monospace rendering with ten string rows,
- examples for `g_major_open`, `g_to_c`, `ab_major`, `e_lower_color`, and `beginner_lick`,
- a standalone `/api/tab/render` route,
- no answer-route integration yet.

Important current boundary:

- `/api/tab/render` can render/validate structured events.
- `/api/answer` does not yet attach `tab_example`.
- Existing answer routing already has deterministic fretboard branches, guardrails, curated answers, curated guidance checks, RAG fallback, answer contract enforcement, and optional fretboard payloads.
- Current answer contract tests only allow extra `fretboard` in answer payloads, so `tab_example` will need a deliberate contract update.

Lane 06 dependency:

- Lane 06 is working on answer-page tab rendering.
- This architecture intentionally does not touch `ui/answer-client.js`, `ui/steel-guitar-rag-mock.html`, or other frontend files.
- Backend should define a stable payload that Lane 06 can render without guessing.

## Product Goal

Normal answers should be able to include one compact deterministic `tab_example` payload when the user asks for a safe, supported tab-adjacent teaching example.

The tab should be supporting content, not the dominant answer:

1. Teaching answer first.
2. Optional `tab_example` as a compact demonstration.
3. Optional fretboard payload or future sync data.
4. Sources last, if relevant.

The product promise is "here is a mechanically valid example you can try," not "the LLM invented a tab."

## Proposed Data Contract

Recommended top-level answer addition:

```json
{
  "answer": "Try a simple G to C move at fret 3. Pick strings 4-5-6 for G, then use the A+B color on the same fret for the C sound.",
  "mode": "search",
  "sources": [],
  "warnings": [],
  "sections": [],
  "tab_example": {
    "id": "g-to-c-beginner-456",
    "title": "G to C beginner move",
    "kind": "deterministic_example",
    "context": {
      "key": "G",
      "tuning": "E9",
      "profile": "default_e9",
      "difficulty": "beginner",
      "grip": "4-5-6",
      "rightsStatus": "original_educational_example",
      "source": "deterministic_tab_registry"
    },
    "events": [
      {
        "id": "g-to-c-1",
        "label": "G",
        "chord": "G",
        "notes": [
          {"string": 4, "fret": 3, "changes": []},
          {"string": 5, "fret": 3, "changes": []},
          {"string": 6, "fret": 3, "changes": []}
        ]
      },
      {
        "id": "g-to-c-2",
        "label": "C lift",
        "chord": "C",
        "notes": [
          {"string": 5, "fret": 3, "changes": ["A"]},
          {"string": 6, "fret": 3, "changes": ["B"]},
          {"string": 8, "fret": 3, "changes": []}
        ]
      }
    ],
    "rendered_tab": "Ch |G     C\n 1 |\n ...",
    "validation": {
      "ok": true,
      "issues": [],
      "profile": "default_e9",
      "eventCount": 2
    },
    "explanation": "This keeps the bar at fret 3 and uses the A+B pedal color to move from the G home sound toward C.",
    "intervals": [
      {
        "eventId": "g-to-c-1",
        "chord": "G",
        "byString": {"4": "1", "5": "5", "6": "3"}
      },
      {
        "eventId": "g-to-c-2",
        "chord": "C",
        "byString": {"5": "1", "6": "5", "8": "3"}
      }
    ],
    "warnings": []
  }
}
```

Field rules:

- `tab_example` is optional.
- If present, it must be fully validated before display.
- `rendered_tab` must be produced by `steel_guitar_rag.tab_engine`, not hand-authored by the answer composer.
- `events` are the source of truth; `rendered_tab` is a renderer output.
- `validation.ok=false` should not be attached to normal user answers except in explicit validation/explanation flows.
- `rightsStatus` is required and should be `original_educational_example` for generated examples in the next slice.
- The answer payload should not include raw x/y fretboard geometry.

Compatibility note:

- Existing answer payload contract tests will need to allow `tab_example` as an optional top-level key, similar to `fretboard`.

## Intent Routing Strategy

### Safe Intent Categories

Attach `tab_example` only when the question maps to a known deterministic example or a safe structured generator.

Safe categories for the next slice:

- `chord_move`
  - "Show me a G to C move."
  - "Give me a simple I to IV movement in G."
- `grip_example`
  - "Show me a 4-5-6 grip example."
  - "Give me a beginner grip on strings 5-6-8."
- `pedal_lever_usage`
  - "How do I use A+B pedals?"
  - "Show me an E-lower move."
- `beginner_lick`
  - "Give me a beginner lick in G."
  - "Show a simple country lick."
- `scale_fragment`
  - Later in v1 only if backed by a fixed registry example.
  - Otherwise v2+.
- `tab_validation_explanation`
  - User pasted short tab or structured events.
  - Should validate/explain, not silently replace with generated material.
- `public_domain_melody`
  - Later only. Not part of the next backend slice.

### Unsafe Or Blocked Categories

Do not attach generated tab examples for:

- full copyrighted song tab,
- named modern song arrangements,
- "tab the whole solo",
- "play the exact Lloyd/Paul/Buddy solo" style requests,
- arbitrary melody extraction from recording/audio/video,
- requests to reproduce commercial lesson material,
- unknown long pasted copyrighted material,
- any prompt asking for exhaustive/all-possible tabs.

Blocked requests should use an answer-only guardrail or a safe redirect:

- explain the chord movement,
- offer a short original exercise,
- ask the user to provide a short phrase they own or have rights to use.

## Example Registry Strategy

Add a deterministic answer-tab registry before adding generative planners.

Recommended module:

- `steel_guitar_rag/tab_examples.py` or `steel_guitar_rag/answer_tab_examples.py`

Registry entry shape:

```python
{
    "example_id": "g-to-c-beginner-456",
    "trigger_intents": ("chord_move", "pedal_lever_usage"),
    "trigger_patterns": (...),
    "key_support": ("G",),
    "default_key": "G",
    "grip": "4-5-6",
    "difficulty": "beginner",
    "event_builder": build_g_to_c_beginner_events,
    "explanation_builder": explain_g_to_c_beginner,
    "rights_status": "original_educational_example",
}
```

Registry rules:

- Registry returns structured `TabEvent` objects, not ASCII.
- Every registry result must pass `render_tab()` or `render_tab_from_payload()` before being attached.
- Registry should return `None` for unsupported keys rather than forcing a bad transposition.
- Registry should include a reason/caveat for safe fallback when useful.
- Registry examples must be short and practice-oriented.
- Registry should not call SGF retrieval, Chroma, or the answer provider.

Recommended first entries:

- `g_to_c`: existing engine example, maps to chord move / A+B usage.
- `beginner_lick`: existing engine example, maps to beginner lick in G.
- `e_lower_color`: existing engine example, maps to E-lower move.
- `g_major_open`: maps to grip example / G major grip.
- `ab_major`: rename or relabel carefully if it means A+B major family rather than Ab major; avoid confusing user-facing title.

Naming caution:

- Current example id `ab_major` can be read as "A-flat major." In product-facing registry labels, prefer `a_b_pedal_major` or `ab_pedal_major_family` if that is the musical intent.

## Safe Generation Ladder

### v1: Fixed Examples Only

- Attach only deterministic registry examples.
- No transposition except cases already explicitly validated.
- No LLM-created events.
- No SGF-created events.
- All examples validate before display.

### v2: Parameterized Chord Moves

- Allow key-parameterized I-IV, I-V, and I-IV-V-I moves.
- Use pitch/position engine and tab validator.
- Reject unsupported keys or return answer-only fallback.

### v3: Melody-Note Input To Tab

- User provides a short note list or scale-degree list.
- Resolver maps to candidate tab events.
- User chooses beginner/smooth/same-grip preferences.

### v4: Lyrics/Chords User-Provided Short Phrase

- User provides owned or safe short phrase context.
- Engine creates fills or transitions, not full arrangements.
- Rights status remains explicit.

### v5: SVG Event Sync

- Add event ids and position ids that let the SVG fretboard highlight selected tab events.
- UI still owns all geometry.

### v6: Practice-Plan Integration

- Tab examples become drill steps with repetition targets, tempo notes, and "what to listen for."

## Backend Integration Points

Likely files for the next Lane 05 slice:

- `steel_guitar_rag/tab_engine.py`
  - Reuse `TabEvent`, `TabNote`, `render_tab`, `render_example`, `tab_examples`, validation issues, and default profile.
  - Avoid broad changes unless small metadata/event-id additions are needed.
- `steel_guitar_rag/api.py`
  - Attach optional `tab_example` in `/api/answer` payload after deterministic/curated answer selection and before response serialization.
  - Keep `/api/tab/render` unchanged unless the contract needs shared serializer helpers.
- `steel_guitar_rag/answer_intent_classifier.py`
  - Add or extend internal routing attributes for tab-example eligibility.
  - Do not expose classifier internals in public payloads.
- `steel_guitar_rag/curated_answers.py`
  - Existing teacher-first answers already cover lick requests, B+C pedal practice, song-learning guardrails, and tab/notation requests.
  - Next slice may map selected curated intents to deterministic tab examples, but curated prose must not generate events.
- `steel_guitar_rag/answer_contracts.py`
  - Add optional `tab_example` response contract allowance if contract validation covers response shape.
- `tests/test_tab_engine.py`
  - Add registry/serializer tests if the registry lives near the tab engine.
- `tests/test_api_contract.py`
  - Update response schema allowance for optional `tab_example`.
- `tests/test_api_search.py`
  - Add answer-route tests that prove safe intents attach tab and unsafe intents do not.

Suggested new module:

- `steel_guitar_rag/answer_tab_examples.py`

Suggested responsibilities:

- classify tab example request subtype,
- select deterministic example id,
- build payload-ready `tab_example`,
- call renderer/validator,
- return `None` when unsupported or blocked.

Do not integrate by asking the LLM to produce ASCII tab inside the answer text.

## Answer Flow Placement

Recommended sequence inside `/api/answer`:

1. Parse and authorize answer request.
2. Run answer intent classifier.
3. Apply unsafe/off-domain guardrails.
4. Produce deterministic fretboard or curated answer as today.
5. Ask `answer_tab_examples` whether this question and answer intent allow a tab example.
6. If yes, build events from registry.
7. Validate/render with `tab_engine`.
8. Attach `tab_example` only when validation passes.
9. Return answer response.

Rules:

- Tab attachment must not require RAG retrieval.
- Tab attachment must not trigger RAG retrieval.
- RAG can still provide answer/source context when the chosen answer route already uses it.
- If answer and tab disagree, omit the tab and add an internal/test-visible warning rather than showing contradictory teaching.

## Test Plan For Next Slice

Minimum test cases:

1. "Show me a G to C move" attaches `tab_example`.
2. "Give me a simple G major fill" attaches beginner G example.
3. "How do I use A+B pedals?" attaches a string-aware A/B example.
4. "Show me an E-lower move" attaches `e_lower_color`.
5. "Give me a beginner lick in G" attaches `beginner_lick`.
6. "Show me a 4-5-6 grip example" attaches a grip example.
7. "Where can I buy a slide bar?" does not attach `tab_example`.
8. "Who is Lloyd Green?" does not attach `tab_example`.
9. "What do players say about wound 6th strings?" does not attach `tab_example`.
10. "Give me full tab for [modern copyrighted song]" is blocked from tab generation.
11. "Tab the whole solo from [artist/song]" is blocked from tab generation.
12. Arbitrary audio/recording extraction request is blocked from tab generation.
13. Registry event with A pedal on string 4 is rejected and not attached.
14. Every attached `rendered_tab` is generated from events and validates.
15. Non-tab answers are byte/shape-equivalent except for existing expected fields.
16. Tab example attachment works when search/RAG returns no sources.
17. Default key is explicit in `tab_example.context.key`.
18. Unsupported key returns no `tab_example` or a safe answer-only fallback.
19. `tab_example.validation.ok` is never false in normal answer generation.
20. Optional response contract allows `tab_example` but rejects unexpected arbitrary keys.
21. Source-backed answer text cannot override deterministic tab events.
22. UI-facing payload contains no Python objects or raw dataclass representations.
23. `ab_major` naming cannot surface as ambiguous "A-flat major" if the example means A+B pedal family.
24. Feature flag off keeps `/api/answer` unchanged.
25. Feature flag on enables only allowlisted safe intents.

Recommended regression buckets:

- `tab_example_missing_for_safe_intent`
- `tab_example_attached_to_unsafe_intent`
- `copyrighted_song_tab_leak`
- `fake_tab_unvalidated_event`
- `tab_answer_mismatch`
- `tab_example_requires_rag`
- `tab_payload_schema_drift`
- `tab_object_string_leak`

## Risks And Mitigations

### Fake Tab Risk

Risk: plausible-looking tab can be mechanically wrong.

Mitigation:

- registry events only in v1,
- validate before attach,
- no LLM-created events,
- renderer output only from structured events.

### Copyright/Product Guardrail Risk

Risk: user asks for full song or named-solo tab and system produces too much.

Mitigation:

- block unsafe categories before registry lookup,
- require `rightsStatus=original_educational_example`,
- redirect to short original exercise or conceptual explanation.

### UI Clutter Risk

Risk: answer page becomes dominated by tab blocks.

Mitigation:

- one compact `tab_example` by default,
- tab appears after teaching answer,
- future multi-example results require Lane 06 design and explicit expansion behavior.

### Copedent Mismatch Risk

Risk: default E9 example may be wrong for a user setup.

Mitigation:

- context must state `profile=default_e9`,
- answer text should say "assuming standard E9" when needed,
- later saved-copedent support must revalidate.

### Brittle Intent Routing Risk

Risk: keyword matching attaches tab to too many prompts.

Mitigation:

- start with narrow allowlist,
- feature flag default off,
- tests for safe and unsafe near-misses,
- omit tab when intent confidence is low.

### Source-Backed Answer vs Deterministic Tab Mismatch

Risk: RAG or curated answer text describes one move while tab shows another.

Mitigation:

- use curated/deterministic answer intent metadata to select tab,
- omit tab on mismatch,
- keep RAG supporting-only for technique context.

## Feature Flag Recommendation

Add a flag for the next backend slice:

- `ENABLE_ANSWER_TAB_EXAMPLES`

Default:

- off.

Recommended rollout:

1. Local tests only.
2. Protected preview.
3. Lane 06 render smoke after UI slice is ready.
4. Broader beta only after Lane 15 approves safe/unsafe intent coverage.

## Recommended Next Codex Implementation Prompt

Use this after Lane 06 finishes answer-page tab rendering or confirms the payload contract is acceptable:

```text
Lane: 05 Backend / RAG Integration
Reasoning level: HIGH

Task: Implement the first answer-triggered deterministic tab example slice.

Read:
- AGENTS.md
- docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md
- docs/handoffs/task-completions/2026-06-18-05-tab-engine-first-slice.md
- docs/handoffs/task-completions/2026-06-18-1516-06-tab-engine-answer-ux.md
- steel_guitar_rag/tab_engine.py
- steel_guitar_rag/api.py
- steel_guitar_rag/answer_intent_classifier.py
- steel_guitar_rag/curated_answers.py
- tests/test_tab_engine.py
- tests/test_api_contract.py
- tests/test_api_search.py

Goal:
Attach an optional `tab_example` payload to `/api/answer` only for safe, allowlisted teaching intents that map to deterministic tab examples.

Scope:
- Create a small deterministic registry/helper, likely `steel_guitar_rag/answer_tab_examples.py`.
- Reuse `steel_guitar_rag.tab_engine` events, renderer, and validator.
- Add feature flag `ENABLE_ANSWER_TAB_EXAMPLES`, default off.
- Attach one compact validated `tab_example` for supported prompts:
  - "Show me a G to C move"
  - "Give me a simple G major fill"
  - "How do I use A+B pedals?"
  - "Show me an E-lower move"
  - "Give me a beginner lick in G"
  - "Show me a 4-5-6 grip example"
- Do not attach tab examples for gear, player bio, vendor, forum-wisdom, off-domain, unsafe, full-song, named-song arrangement, or whole-solo requests.
- Do not let LLM/RAG generate tab events.
- Do not touch frontend files.

Tests:
- Add focused registry tests.
- Update answer API contract tests for optional `tab_example`.
- Add `/api/answer` tests for safe attachment and unsafe non-attachment.
- Prove rendered tabs always validate.
- Prove feature flag off preserves existing answer behavior.

Do not:
- modify UI files,
- modify Chroma/vector stores,
- modify corpus/source-inbox data,
- run scraping,
- deploy,
- stage or commit unless explicitly instructed.

Required handoff:
Write `docs/handoffs/task-completions/<timestamp>-05-answer-triggered-tab-examples.md` with files changed, tests run, risks, safe-to-stage paths, and next lane.
```

## Files Changed

- Created:
  - `docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md`
- Changed:
  - None
- Deleted:
  - None
- Generated artifacts:
  - None

## Tests And Checks

Commands run:

- `sed -n '1,260p' /Users/cory/.codex/attachments/af3f8bff-ce35-415f-b7d2-696eef502f02/pasted-text.txt`
  - Passed. Initial task attachment read.
- `sed -n '1,520p' AGENTS.md`
  - Passed. Read repo protocol and lane workflow rules.
- `git status --short`
  - Passed before editing. Showed broad unrelated dirty worktree, including current Lane 06 UI/test files and other parked work.
- `sed -n '1,280p' /Users/cory/.codex/attachments/52b5ec79-d43b-402e-a73a-c9c4de1f8053/pasted-text.txt`
  - Passed. Second attachment matched the task.
- `test -f docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md; printf '%s\n' $?`
  - Passed. Returned `1`, confirming this handoff did not already exist.
- `git show --stat --oneline 686fd3c --`
  - Passed. Confirmed committed deterministic tab engine slice.
- `git status --short -- docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md steel_guitar_rag/tab_engine.py steel_guitar_rag/api.py tests/test_tab_engine.py ui/answer-client.js ui/steel-guitar-rag-mock.html`
  - Passed. Showed unrelated dirty UI/test files; target handoff did not exist.
- `sed -n '1,280p' /Users/cory/.codex/attachments/3dc5437e-9397-40aa-8feb-b4819d8463e0/pasted-text.txt`
  - Passed. Latest attachment matched the task and steered the final scope.
- `rg -n "tab|tab_example|/api/tab|answer|intent|curated" steel_guitar_rag tests -g '*.py'`
  - Passed, though output was large/truncated. Used to identify relevant modules.
- `sed -n '1,260p' docs/handoffs/task-completions/2026-06-18-18-tab-engine-product-architecture.md`
  - Passed. Used for prior Lane 18 architecture context.
- `sed -n '1,220p' docs/handoffs/task-completions/2026-06-18-1516-06-tab-engine-answer-ux.md`
  - Passed. Used for Lane 06 parallel UI context.
- `sed -n '1,280p' steel_guitar_rag/tab_engine.py`
  - Passed. Read-only inspection.
- `sed -n '280,620p' steel_guitar_rag/tab_engine.py`
  - Passed. Read-only inspection.
- `rg -n "tab|answer|api/tab|answerResponse|fretboard|curated|intent" steel_guitar_rag/api.py`
  - Passed. Used to locate answer/tab integration points.
- `sed -n '1,320p' tests/test_tab_engine.py`
  - Passed. Read-only inspection.
- `sed -n '240,530p' steel_guitar_rag/api.py`
  - Passed. Read-only inspection of `/api/tab/render` and `/api/answer` flow.
- `sed -n '1,240p' steel_guitar_rag/answer_intent_classifier.py`
  - Passed. Read-only inspection of current intent classifier.
- `sed -n '3000,3148p' steel_guitar_rag/curated_answers.py`
  - Passed. Read-only inspection of existing lick/practice curated answers.
- `sed -n '1,220p' docs/handoffs/task-completions/2026-06-18-05-tab-engine-first-slice.md`
  - Passed. Used for committed backend slice context.

- `git status --short`
  - Passed after editing. Broad unrelated dirty worktree remains; this task's scoped change is only this new handoff.
- `git diff --check`
  - Passed.
- `git diff --no-index --check -- /dev/null docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md`
  - Passed. Used because this handoff is new and untracked, so normal `git diff --check` does not inspect its contents.
- `git status --short -- docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md`
  - Passed. Shows `?? docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md`.

Skipped tests:

- Unit, API, browser, and eval tests were skipped because this was a docs-only architecture task with no executable behavior changed.

## Integration Notes

- Next slice should be Lane 05, not Lane 06.
- Lane 06 can continue tab rendering work in parallel because this handoff only defines the backend answer payload contract.
- The next backend implementation should be feature-flagged and default off.
- The next backend implementation should attach `tab_example` only when events validate.
- `/api/tab/render` remains useful as a standalone validation/rendering endpoint; normal answer integration should reuse the same validator/renderer.
- Current dirty frontend/test files were not touched.

## Risk Assessment

Risk level: medium for future implementation, low for this docs-only handoff.

Why:

- Answer-triggered tabs can create high product value, but also carry fake-tab, copyright, and UI-clutter risks.
- Deterministic registry and validation keep the first slice bounded.
- This handoff does not alter runtime behavior.

Rollback notes:

- Remove this handoff if the architecture direction changes.

## Human Decision Needed

No for this architecture handoff.

Future decision before broader rollout:

- Whether `ENABLE_ANSWER_TAB_EXAMPLES` should be protected-preview only at first or available in local dev only until Lane 06 UI smoke is green.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md`

## Files That Must Not Be Staged

- Any pre-existing dirty files outside the safe-to-stage path above.
- `tests/test_tab_engine.py`
- `ui/answer-client.js`
- `ui/steel-guitar-rag-mock.html`
- App code, backend implementation files, frontend files, tests, deployment files, auth files, Chroma/vector data, embeddings, corpus-private, source-inbox data, generated reports, raw design assets, and secrets.

## Commit Readiness

Safe to commit if only the exact handoff path above is staged.

No commit was made because the task did not explicitly require committing and the worktree is not clean.

## Recommended Next Lane

Recommended lane: `05 Backend / RAG Integration`, after Lane 06 confirms the answer-page tab rendering contract is compatible or after Lane 15 reviews this design.

Suggested immediate next step:

```text
Lane 15: Run Lane15DesignReview for docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md. Verify safe/unsafe routing, payload shape, feature flag default-off behavior, copyright guardrails, and the proposed test plan before Lane 05 implements answer-triggered tab examples.
```
