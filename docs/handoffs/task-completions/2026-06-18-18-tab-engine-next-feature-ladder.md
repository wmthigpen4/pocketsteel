# 2026-06-18 - Lane 18 - Tab Engine Next Feature Ladder

## Task Summary

Requested: define the next practical feature ladder after the current answer-triggered deterministic tab examples slice.

Completed: created this Lane 18 product/architecture handoff only. It consolidates the prior tab-engine product architecture, answer-triggered tab architecture, Lane 05 implementation plan, Lane 06 UX follow-up, and Lane 15 QA guidance into a next-stage roadmap.

Intentionally not changed:

- No app code.
- No backend code.
- No UI code.
- No tests.
- No `/api/answer` routing.
- No `/api/tab/render` behavior.
- No Chroma/vector stores, embeddings, corpus/source data, scraping, auth, deployment, DNS, or design assets.

Task type: docs-only product/architecture.

Lane: `18 Product / Architecture`.

Task mode: GREEN for this handoff. Future implementation slices are YELLOW because they change answer behavior, response contracts, UI behavior, or eval scope.

## 1. Current State

The tab-engine trajectory is now in three layers:

1. A deterministic tab engine slice has been committed.
   - The engine has structured tab events, validation, default 10-string E9 assumptions, fixed-width rendering, and example rendering.
   - ASCII tab is a renderer output, not the source of truth.
2. Answer-triggered deterministic examples have an architecture contract and Lane 05 implementation plan.
   - The intended response shape is an optional tab example payload attached to normal answer responses only for safe, allowlisted teaching intents.
   - The public field name still needs final consistency between `tab_example` and `tabExample`.
3. Lane 06 and Lane 15 have defined initial UI and QA expectations.
   - UI should show one compact optional tab card only when the backend supplies a valid tab payload.
   - QA should verify validation, safe/unsafe routing, no object-string leaks, no fake frontend tab generation, and no copyrighted song-tab leakage.

Current product boundary:

- v1 answer-triggered tab examples should stay deterministic, short, original, validated, and standard E9.
- RAG can explain or contextualize, but must not generate tab events.
- The UI must not invent tab from answer prose.
- The next step should not jump straight to arbitrary melody or lyrics/chord generation.

## 2. Product Goal

The tab engine should become a practical teaching layer that can:

- give a learner a short playable example at the moment it helps,
- explain why the example works,
- validate that the tab is physically plausible for the assumed copedent,
- sync with the SVG fretboard later,
- grow into user-provided melody and practice workflows without becoming a prompt-only ASCII generator.

The product promise is:

> Steel Guitar RAG can show a small, mechanically valid E9 move and teach the player how to use it.

It should not promise:

- full-song transcription,
- artist-solo reconstruction,
- arbitrary audio-to-tab,
- instant support for every copedent,
- unlimited generated tab dumps.

## 3. Feature Ladder

### v1: Deterministic Examples

Status: current/near-current slice.

Purpose: attach one validated tab example to safe answer intents.

Examples:

- "Show me a G to C move."
- "How do I use A+B pedals?"
- "Give me a beginner lick in G."
- "Show me an E-lower move."

Rules:

- Use fixed registry examples or tightly controlled deterministic builders.
- Validate every event before display.
- Attach at most one compact example by default.
- Feature flag should default off until QA and UI smoke are green.
- No LLM-only tab generation.

### v2: Parameterized Chord Moves

Recommended next MVP slice.

Purpose: generate short chord-movement examples from deterministic E9 position logic rather than a hand-entered example for every key.

Initial scope:

- Standard E9 only.
- Major-key movement only.
- I-IV, I-V, and I-IV-V-I.
- Starter grips such as 4-5-6 and 5-6-8.
- Common position families only: open/no-pedal, A+F, A+B, and validated nearby movement patterns.
- Short 2-4 event examples.

Expected output:

- one selected tab example,
- event model,
- rendered tab,
- validation status,
- direct explanation,
- practice focus,
- optional fretboard position references.

### v3: User-Provided Melody Notes To Tab

Purpose: map a short user-provided note or scale-degree list to playable E9 tab candidates.

Input examples:

- "Tab these notes: G A B D."
- "Show 1 2 3 5 in G on E9."
- "Can I play this short line: B A G E?"

Rules:

- The user supplies the musical notes.
- The engine resolves candidate string/fret/control choices.
- The answer offers one beginner-friendly path by default and maybe one alternate.
- Rhythm support starts simple: ordered notes, optional beat labels, no complex notation in the first slice.
- The system must not infer full copyrighted melodies from titles or lyric fragments.

### v4: User-Provided Lyrics/Chords To Short Fills

Purpose: help users build short fills or movement ideas around material they provide or around public-domain/user-owned material.

Input examples:

- "Here are my chords: G C D G. Give me a short fill between C and D."
- "For this public-domain verse, show a simple steel fill."
- "I wrote this chorus. Give me a two-beat fill over the V chord."

Rules:

- Rights status must be explicit.
- Output should be short fills, transitions, or practice examples, not full arrangements.
- Copyrighted title-only prompts should redirect to original exercises or conceptual explanation.
- The answer should state when it is using user-provided material.

### v5: Tab Explanation And Validation

Purpose: explain and validate tab that the user provides.

Input examples:

- "What does this tab mean?"
- "Is this A pedal tab possible?"
- "Why does this lick work over G?"

Behavior:

- Parse or preserve the user-provided tab.
- Validate string/fret/control labels where possible.
- Explain mechanics, chord tones, intervals, and likely practice use.
- Warn when timing, copedent, or notation is ambiguous.
- Do not claim provenance or exact artist intent unless supplied by a valid source.

### v6: SVG Event Sync

Purpose: connect tab events to the existing SVG fretboard so the tab becomes a visual teaching instrument.

Behavior:

- Selecting a tab event highlights the relevant fret/string/control state.
- Selecting a fretboard highlight can reveal the matching tab event.
- The backend sends event ids, string numbers, fret numbers, pedals/levers, and optional position ids.
- The UI owns all fret/string geometry and animation.
- No backend raw x/y coordinates.

### v7: Practice Exercise Generator

Purpose: turn tab examples into guided practice.

Examples:

- A+B squeeze drill.
- I-IV-V-I movement drill.
- Blocking drill on strings 4-5-6.
- E-lower minor color drill.

Payload concepts:

- drill steps,
- repetition count,
- tempo suggestion,
- focus note,
- success criteria,
- "what to listen for",
- optional tab/fretboard event sync.

### v8: User Copedent Profiles

Purpose: adapt tab generation and validation to the player's saved setup.

Behavior:

- Load user profile only behind the correct auth/profile controls.
- Revalidate every generated event against the selected profile.
- If a control is missing or different, omit the generated tab or show a clear caveat.
- Do not silently translate standard E9 examples into a custom copedent without deterministic validation.

Profile status values should be made explicit before implementation:

- `default_e9`
- `assumed_default_e9`
- `user_profile_e9`
- `unsupported_user_profile`
- `profile_required`

## 4. Recommended Next MVP Slice

Recommended next slice: v2 parameterized chord moves.

Reason:

- It builds directly on the deterministic tab engine and answer-triggered examples.
- It gives clear product value without the copyright and ambiguity risks of melody/lyrics workflows.
- It exercises the pitch/position resolver and validator in a bounded way.
- It prepares the data shape needed for SVG sync and practice drills.

Suggested first v2 behavior:

- Support "show a simple I-IV move in G" and related direct chord-move prompts.
- Generate a short standard-E9 event sequence for I-IV and I-V in a small set of validated keys first, then expand to all 12 major roots only after fixtures pass.
- Prefer one starter grip and one easy bar/pedal movement.
- Include a `difficulty` or `tier` value of `starter`.
- Include `rightsStatus: original_educational_example`.
- Include profile assumption: `default_e9` or `assumed_default_e9`.
- Omit tab rather than guess when the requested key, quality, or move is unsupported.

Recommended first acceptance examples:

- G I-IV: G to C.
- A I-IV: A to D.
- G I-V: G to D.
- G I-IV-V-I: G to C to D to G.

If all-12-key support is attempted, it must be driven by deterministic pitch/position fixtures, not manual spreadsheet rows.

## 5. Inputs That Should Produce Tab

MVP/v2 eligible:

- "Show me a simple G to C move."
- "Give me a beginner I-IV move in G."
- "Show a simple I-V move on E9."
- "Give me a short A+B practice example."
- "Show me an E-lower color move."
- "Give me a beginner lick in G."
- "Show a 4-5-6 grip example."
- "Make a two-measure original practice example for I-IV-V-I in G."

Later eligible:

- "Tab these notes: G A B D."
- "Turn this note list into E9 tab."
- "Here are my chords; give me a short fill."
- "Here is my own lyric line and chords; make a short transition."
- "Explain this tab."
- "Validate this tab."

Requirement:

- The request must either map to a known deterministic example/generator or provide the musical material to be transformed.

## 6. Inputs That Should Not Produce Tab

Do not produce generated tab for:

- "Tab the whole song..."
- "Give me the exact solo from..."
- "Play it like [named artist] on [recording]."
- "Transcribe this YouTube/audio/video."
- "Generate all positions for every chord."
- "Use this commercial lesson transcript to make tab."
- Copyrighted title-only prompts.
- Long pasted copyrighted lyrics or arrangements.
- Unsupported copedents unless profile support is implemented and validated.
- Non-steel/off-domain questions.
- Gear, vendor, player bio, maintenance, or troubleshooting questions unless the user also asks for a safe practice example.

Safe redirect:

- Explain why full tab is not available.
- Offer a short original exercise in the same general skill area.
- Offer to tab a short user-provided note list or chord movement.

## 7. Melody-To-Tab Roadmap

Phase 1:

- Accept short note lists and scale degrees only.
- No rhythm beyond ordering and optional beat labels.
- Standard E9 only.
- Return one beginner path and one optional alternate if confidence is high.

Phase 2:

- Add constraints: fret range, string set, grip, "stay near fret 3", "avoid levers", "use A+B".
- Add simple rhythm labels: quarter, half, hold, pickup.
- Add interval display against key/root.

Phase 3:

- Add phrase planner preferences: smooth bar movement, same position, higher register, lower register, beginner.
- Add user-copedent validation after profile architecture is ready.

Guardrail:

- Melody-to-tab requires user-provided notes, public-domain material, or user-owned material. A song title alone is not enough.

## 8. User-Provided Lyrics/Chords Roadmap

Phase 1:

- Accept chord-only progressions for short original fills.
- Ignore lyrics for generation except as user-visible context.
- Generate transitions and fills, not arrangements.

Phase 2:

- Accept user-owned lyric/chord snippets with explicit user-provided rights status.
- Produce a very short fill or turnaround around one chord change.
- Include timing caveats if the lyric meter is ambiguous.

Phase 3:

- Add public-domain support with explicit source/right status.
- Add stronger form awareness: intro, turnaround, tag, fill between vocal lines.

Guardrail:

- Do not reconstruct copyrighted songs from title, lyric fragments, or chord charts scraped from elsewhere.

## 9. Tab Explanation Roadmap

Phase 1:

- Preserve user-provided tab and explain mechanics.
- Validate obvious string/fret/control errors.
- Explain likely chord tones when key/root is provided.

Phase 2:

- Normalize simple tab into structured events.
- Identify grip, position family, pedals/levers, intervals, and likely chord function.
- Suggest one practice variation.

Phase 3:

- Offer correction suggestions for invalid events.
- Let user choose "explain", "validate", "simplify", or "make a short original variation."

Guardrail:

- Explanation can discuss pasted material, but generated replacement tab should remain short and original unless the user owns/provides the material and scope is safe.

## 10. SVG Fretboard Sync Roadmap

Phase 1:

- Add optional `fretboardSync` payload for tab events.
- Map event ids to fret/string/control data and optional position ids.
- UI displays one selected event at a time.

Phase 2:

- Add next/previous event controls.
- Highlight current tab event on the SVG fretboard.
- Keep the tab card and fretboard detail panel in sync.

Phase 3:

- Add compare mode for two events or positions.
- Add practice-step progression through tab events.
- Add animation only after static sync is reliable.

Contract rule:

- Backend sends musical intent only.
- UI/SVG remains the source of truth for geometry.
- Decorative guitar imagery remains decorative.

## 11. Practice-Plan Integration Roadmap

Phase 1:

- Attach a "one thing to practice" note to each generated tab example.
- Add suggested repetition count and slow-tempo instruction in answer prose.

Phase 2:

- Add structured `practiceSteps` to tab payloads.
- Each step can reference tab event ids and fretboard position ids.
- Include focus area: blocking, pedal timing, intonation, bar movement, grip accuracy.

Phase 3:

- Generate multi-day practice plans from validated drills.
- Track user preference/profile only after auth/profile architecture is approved.
- Add difficulty progression from starter to common to alternate to advanced.

Guardrail:

- Practice plans should use validated examples and short drills, not long generated solos.

## 12. Risks And Guardrails

### Fake-Tab Risk

Risk: plausible ASCII tab can be mechanically wrong.

Guardrails:

- Structured events first.
- Renderer second.
- Validator before display.
- No LLM-only tab events.
- No SGF-fragment-derived tab events.

### Copyright Risk

Risk: tab requests can drift into full-song transcription.

Guardrails:

- Require `rightsStatus`.
- Block full copyrighted song/solo requests.
- Redirect to original short exercises.
- Do not reconstruct commercial lesson content.

### Intent-Routing Risk

Risk: too many answer types get tab cards.

Guardrails:

- Narrow allowlist.
- Feature flag default off for new generators.
- Omit tab when confidence is low.
- QA safe/unsafe near-miss tests.

### UI-Clutter Risk

Risk: tab and fretboard cards overwhelm the teaching answer.

Guardrails:

- One compact example by default.
- Hide alternates behind "show more" later.
- Keep source cards secondary.
- Do not dump every possible position or tab option.

### Copedent-Mismatch Risk

Risk: default E9 tab is wrong for the user's guitar.

Guardrails:

- State profile assumption.
- Revalidate against saved user profile before profile-backed display.
- Do not silently adapt unsupported setups.

### Contract-Drift Risk

Risk: backend, UI, and QA disagree on field names or validation shape.

Guardrails:

- Choose `tabExample` vs `tab_example` before the answer-route implementation stabilizes.
- Keep API contract tests and frontend fixture tests aligned.
- Add fixture payloads for each new generator stage.

## 13. Recommended Next Implementation Prompts

### Lane 05 Backend / RAG Integration

```text
Lane: 05 Backend / RAG Integration
Reasoning level: HIGH

Task: Implement v2 parameterized E9 chord-move tab examples behind a default-off feature flag.

Read:
- AGENTS.md
- docs/handoffs/task-completions/2026-06-18-18-tab-engine-next-feature-ladder.md
- docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md
- docs/handoffs/task-completions/2026-06-18-05-answer-triggered-tab-examples-implementation-plan.md
- steel_guitar_rag/tab_engine.py
- steel_guitar_rag/api.py
- steel_guitar_rag/answer_intent_classifier.py
- tests/test_tab_engine.py
- tests/test_api_contract.py
- tests/test_api_search.py

Goal:
Generate one validated short standard-E9 tab example for safe I-IV, I-V, and I-IV-V-I chord-move prompts using deterministic position logic, not manual spreadsheet rows and not LLM/RAG-generated events.

Scope:
- Standard 10-string E9 only.
- Major-key starter examples only.
- Short 2-4 event examples.
- Feature flag default off.
- Optional answer payload only after validation passes.
- RAG may support explanation only; it must not generate tab events.

Do not:
- touch UI files,
- generate copyrighted song tab,
- use SGF fragments as tab source,
- touch Chroma, embeddings, corpus/source-inbox data, scraping, deployment, auth, or DNS.

Required tests:
- safe prompt attaches valid tab when flag is on,
- flag off preserves existing answer behavior,
- unsupported prompt omits tab,
- copyrighted song/artist-solo requests omit tab or refuse,
- rendered tab validates,
- payload shape matches final `tabExample`/`tab_example` contract.
```

### Lane 15 QA / Answer Eval

```text
Lane: 15 QA / Answer Eval
Reasoning level: HIGH

Task: Design and run QA for v2 parameterized chord-move tab examples.

Read:
- AGENTS.md
- docs/handoffs/task-completions/2026-06-18-18-tab-engine-next-feature-ladder.md
- the Lane 05 implementation handoff for v2 chord moves
- tests/test_tab_engine.py
- tests/test_api_contract.py
- tests/test_api_search.py

Verify:
- safe chord-move prompts attach tab only when feature flag is on,
- unsafe/copyrighted prompts do not attach generated tab,
- rendered tab validates and has no object-string leaks,
- answer text and tab example do not contradict each other,
- non-tab answer shapes remain backward-compatible,
- no UI/browser behavior is claimed without browser smoke.

Write a QA handoff with exact pass/fail buckets and safe-to-stage paths.
```

### Lane 06 UX/UI Design

```text
Lane: 06 UX/UI Design
Reasoning level: HIGH

Task: Define or implement the UI behavior for multiple future tab states without changing backend generation.

Read:
- AGENTS.md
- docs/handoffs/task-completions/2026-06-18-18-tab-engine-next-feature-ladder.md
- docs/handoffs/task-completions/2026-06-18-06-answer-triggered-tab-example-ux-followup.md
- the final backend tab payload contract

Goal:
Keep one compact tab card readable while preparing for future event selection, fretboard sync, validation notes, and show-more behavior.

Guardrails:
- no fake frontend tab generation,
- no raw object rendering,
- no page-level horizontal overflow,
- no empty tab shell,
- source cards remain visually secondary to the teaching answer.
```

### Lane 18 Product / Architecture

```text
Lane: 18 Product / Architecture
Reasoning level: HIGH

Task: Define the `fretboardSync` contract for tab event sync.

Use:
- docs/handoffs/task-completions/2026-06-18-18-tab-engine-next-feature-ladder.md
- current fretboard payload contract
- current tab payload contract

Deliver:
- event-to-position mapping contract,
- selected-event behavior,
- fallback behavior when sync data is absent,
- no raw geometry rule,
- backend/frontend/QA implementation prompts.
```

## Files Changed

- Created:
  - `docs/handoffs/task-completions/2026-06-18-18-tab-engine-next-feature-ladder.md`
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
- `git diff --no-index --check -- /dev/null docs/handoffs/task-completions/2026-06-18-18-tab-engine-next-feature-ladder.md`
  - Passed. Used because this handoff is new and untracked, so normal `git diff --check` does not inspect its contents.
- `git status --short`
  - Passed before and after file creation. The broader worktree has many unrelated dirty and untracked files; this task created only the target handoff.
- `git status --short -- docs/handoffs/task-completions/2026-06-18-18-tab-engine-next-feature-ladder.md`
  - Passed. Shows the new handoff as untracked before staging.

Skipped:

- Unit, API, UI, browser, and eval tests. This task intentionally changed no executable files.

## Integration Notes

- Recommended next implementation lane: Lane 05.
- Recommended next implementation slice: v2 parameterized chord moves.
- Lane 06 should not build SVG sync until the event-to-position contract is written and v1/v2 tab card behavior is stable.
- Lane 15 should add safe/unsafe intent buckets before any broader protected-preview rollout.
- Lane 01 should treat this handoff as a product/architecture artifact and stage/commit only by exact path if committing.

## Risk Assessment

Risk level: low for this handoff, medium for future implementation.

Why:

- This task is docs-only and does not alter runtime behavior.
- Future v2 chord-move generation touches answer routing and response contracts, so it needs focused backend tests and QA review.

Rollback notes:

- Remove this handoff if superseded by a later product architecture decision.

## Human Decision Needed

No for this handoff.

Future human decisions:

- Choose the canonical public response field name: `tabExample` or `tab_example`.
- Decide whether v2 should start with a small validated key set or all 12 major roots.
- Decide when user-copedent profiles are safe to use in generated tab.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-18-tab-engine-next-feature-ladder.md`

## Files That Must Not Be Staged

- Any pre-existing dirty files outside the safe-to-stage path above.
- App code.
- Backend implementation files.
- Frontend/UI files.
- Tests.
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

Suggested next task: implement the v2 parameterized chord-move tab example slice behind a default-off feature flag after the current answer-triggered deterministic tab examples slice is reconciled and QA-cleared.

## Commit Readiness

Safe to commit.

Reason: this handoff is docs-only, checks passed, and the staged diff is limited to this exact file. The broader worktree contains many unrelated dirty and untracked files that must remain parked.
