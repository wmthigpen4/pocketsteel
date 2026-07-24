# Answer Generation Contract

This contract defines how Steel Guitar RAG decides whether an answer may be generated from deterministic music logic, private profile data, curated rules, or SGF retrieval. It exists to prevent deterministic music questions from falling through to forum fragments.

The key product rule is simple:

Plain chord-location questions are deterministic music-logic questions. They must not use SGF fragments to generate the answer.

## Current Flow Diagnosis

The current `/api/answer` path in `steel_guitar_rag/api.py` retrieves SGF/private sources before most answer-route decisions:

1. Parse the answer request.
2. Run `_search_for_answer(...)` using the configured retrieval mode.
3. Sanitize retrieved sources.
4. Infer the contract intent.
5. Try special-case answer helpers such as B+C exercises, private profile answers, curated answers, prompt-injection handling, no-source fallback, or the configured answer provider.
6. Apply final wording/quality contracts.
7. Attach `fretboard_payload_for_question(...)`; when present, clear top-level source cards.

This means deterministic cases can still be exposed to retrieval side effects before the deterministic route wins. The later source-card cleanup helps presentation, but it does not fully guarantee that answer text, answer provider selection, warnings, or fallback behavior remain deterministic.

The intended architecture is intent-first:

1. Normalize and classify the question.
2. Decide retrieval policy from intent.
3. Run deterministic/private/curated answer authority first when the intent requires it.
4. Run retrieval only when allowed by the intent policy.
5. Validate the final answer and payload against the intent.
6. If deterministic validation fails, return a safe deterministic fallback instead of SGF fragments.

Current branch inspection notes:

- `steel_guitar_rag/api.py` still calls `_search_for_answer(...)` before `infer_contract_intent(...)`, `lookup_curated_answer(...)`, and `fretboard_payload_for_question(...)`.
- `steel_guitar_rag/curated_answers.py` can build deterministic chord-position prose through `visual_fretboard_curated_answer(...)`, but that route is reached after retrieval has already run.
- `steel_guitar_rag/fretboard_examples.py` now has a contract-shaped fretboard payload and deterministic major-position helpers, but `major_chord_location_request_for_question(...)` does not yet cover every mandatory phrase shape in this contract, including `where all can I play`, `where can I find`, `how do I make`, and `where is A major on E9`.
- `steel_guitar_rag/answer_contracts.py` still uses broad `copedent_fretboard` inference for chord/fret/E9 terms; it does not yet express a separate pre-retrieval `deterministic_chord_position` authority.
- `scripts/run_full_answer_quality_eval.py` already checks wrong-key leakage and source-fragment chord answers, but the next QA pass needs response-payload assertions for `response.fretboard`, source suppression, and retrieval-not-called behavior.

## Retrieval Policy Terms

- `forbidden`: retrieval must not run for answer generation, and retrieved excerpts must not influence the answer body.
- `supporting-only`: retrieval may provide source cards or background evidence, but it may not decide the core answer.
- `required`: retrieval or an approved source registry is required because the question asks about a source-backed fact, product, player, current-ish claim, or lived forum wisdom.
- `allowed`: retrieval may generate the answer when no higher-authority deterministic, private, or curated route applies.

## Intent Classes

| Intent | SGF Retrieval Allowed | SGF Can Generate Answer | Retrieval Role | Private Profile Allowed | Source Cards | Visual Payload | Final-Answer Lint Rules |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `deterministic_chord_position` | No | No | Forbidden | No for MVP; future user-copedent variant must be explicit | Suppressed; use deterministic `fretboard.sourceContext` | Required | Must name requested root/canonical enharmonic, include open/A+F/A+B frets, include `response.fretboard`, and contain no unrelated keys, dominant detours, raw SGF fragments, or source-card language |
| `deterministic_progression_position` | No for generation | No | Forbidden or deterministic-rule context only | No for MVP unless question says "my setup" | Suppressed or deterministic rule context only | Required when the user asks to show/map positions; optional for prose-only progression explanation | Must keep I/IV/V or requested progression in the requested key and avoid unrelated borrowed examples |
| `deterministic_grips` | No for basic grip facts | No for basic grip facts | Forbidden for core answer; supporting-only only if user asks what players commonly prefer | Yes only when question asks "my grips" or "my setup" | Suppressed for deterministic generic grips; private cards only for authorized personal setup | Optional | Must use supported strings/grips only, avoid invented copedent-specific changes, and avoid raw geometry |
| `user_private_profile` | No | No | Forbidden for SGF; private source is authoritative | Required when answering personal setup facts | Private source cards may show only to authorized roles | Optional | Must answer from the saved private profile only, must not leak private facts into non-personal answers, and must not mix SGF copedent chatter as if it were the user's setup |
| `practical_concept` | Yes | Not as the first authority when a rules/curated answer exists | Supporting-only unless no deterministic/curated route exists | Only if explicitly personal | Usually yes for source-backed concepts; no for purely curated rules | Optional only when a diagram materially helps | Must define the concept directly, give practical steps, and avoid "retrieved material" framing |
| `right_hand_technique` | Yes | Yes, after cleanup/distillation | Required or supporting depending on topic | No unless explicitly personal | Yes when source-backed | Forbidden | Must provide actionable hand/attack/blocking guidance and avoid gear-only or raw forum fragment answers |
| `gear_product` | Yes | Yes, with curated/source registry preference for known products | Required for product identity, value, specs, and owner-impression claims | No | Yes, preferably curated/current URLs for current product claims | Forbidden | Must avoid stale certainty, contact/order junk, and unapproved URL claims |
| `vendor_buying` | Limited | No for vendor list generation from stale forum fragments | Curated/current registry first; SGF may be background only | No | Yes, curated/current vendor cards preferred | Forbidden | Must include current availability caveat and must not surface PayPal/email/order-link fragments |
| `player_teacher_bio` | Yes | Yes when curated/source evidence is adequate | Required or curated registry | No | Yes unless curated no-source fallback is intentional | Forbidden | Must identify the requested person directly, mention role/contribution, and avoid ranking templates |
| `troubleshooting_diagnostic` | Yes | Yes, after diagnostic template/rules layer shapes the answer | Required/supporting | No unless explicitly personal rig data exists | Yes | Forbidden | Must include likely causes, isolation steps, and safety boundaries where applicable |
| `maintenance_how_to` | Yes | Yes, after safety/rules layer shapes the answer | Required/supporting | No unless explicitly personal setup data exists | Yes | Forbidden | Must include concrete steps and cautions; no unsafe exact mechanics without support |
| `song_tab_guardrail` | Yes | No for full copyrighted tab/lyrics | Supporting-only for style/source context | No unless user supplies private/licensed material and authorization is explicit | Optional | Optional only for original/public-domain short exercises | Must enforce copyright guardrails and offer safe alternatives |
| `generic_rag_answer` | Yes | Yes | Allowed/required | No unless explicitly personal and authorized | Yes | Forbidden unless a separate deterministic visual intent is also detected | Must avoid raw forum fragments, internal source language, weak source cards, and unsupported exact claims |

## Mandatory Deterministic Chord-Position Rule

The following plain chord-location questions must route to `deterministic_chord_position` before retrieval:

- `Where can I play a B chord?`
- `Where all can I play a B chord?`
- `How do I play a C#?`
- `How do I make a Bb chord?`
- `Where is A major on E9?`
- `Show me F# positions.`
- `What frets give me C major?`
- `Where can I find B#?`

Equivalent variants with punctuation, "major chord", "places to play", "all can I play", "find", "make", "show me", and upper/lower case must classify the same way.

These questions must not:

- retrieve SGF to decide the answer;
- send retrieved excerpts to the LLM;
- use SGF source cards as support;
- borrow examples from another key;
- mention unrelated dominant material such as `B7` unless the user asked for I-IV-V, key-of-E, dominant, V-chord, or turnaround context;
- return a text-only answer when a fretboard payload is supported.

## Deterministic Chord-Position Behavior

### Parse

The classifier must extract:

- requested root spelling: for example `A`, `Bb`, `C#`, `B#`;
- chord quality: MVP supports plain major only when the user says `chord`, `major`, or omits quality in a location question;
- position request shape: `where`, `where all`, `how do I play`, `make`, `find`, `show`, or `what frets`.

If the root is valid but the quality is unsupported, the answer should say the MVP supports major-position diagrams first and offer a safe next step. It must not invent arbitrary frets or strings.

### Normalize Enharmonics

The route must support all 12 major roots and common enharmonic spellings:

| Requested | Canonical |
| --- | --- |
| C | C |
| C# / Db | C# |
| D | D |
| D# / Eb | D# |
| E / Fb | E |
| F / E# | F |
| F# / Gb | F# |
| G | G |
| G# / Ab | G# |
| A | A |
| A# / Bb | A# |
| B / Cb | B |
| B# | C |

When the requested spelling differs from canonical spelling, the first sentence must explain the enharmonic relationship. Example: `B# is the same pitch as C. On E9, think of it as a C major chord.`

### Calculate Positions

For MVP standard 10-string E9:

- open/no pedals: `(requested_root - E) mod 12`
- A+F position: `open_fret + 3`
- A+B position: `open_fret + 7`
- common strings: `[4, 5, 6]`
- common optional grips: `4-5-6`, `3-4-5`, `5-6-8`, `6-8-10`

Reference table:

| Canonical Root | Open | A+F | A+B |
| --- | ---: | ---: | ---: |
| C | 8 | 11 | 15 |
| C# | 9 | 12 | 16 |
| D | 10 | 13 | 17 |
| D# | 11 | 14 | 18 |
| E | 0 | 3 | 7 |
| F | 1 | 4 | 8 |
| F# | 2 | 5 | 9 |
| G | 3 | 6 | 10 |
| G# | 4 | 7 | 11 |
| A | 5 | 8 | 12 |
| A# | 6 | 9 | 13 |
| B | 7 | 10 | 14 |

Required A major answer facts:

- fret 5, no pedals;
- fret 8, A pedal + F lever;
- fret 12, A+B pedals;
- no `G major`;
- no `B7` unless explicitly requested by progression/dominant context.

Required B major answer facts:

- fret 7, no pedals;
- fret 10, A pedal + F lever;
- fret 14, A+B pedals;
- no RKL/B7/B9 fragment answer;
- must include a fretboard payload.

Required C# major answer facts:

- fret 9, no pedals;
- fret 12, A pedal + F lever;
- fret 16, A+B pedals;
- no tuning-fragment answer.

### Return Shape

The answer body should be short, direct, and deterministic:

```text
On standard E9, useful A major positions are 5th fret no pedals, 8th fret with A pedal + F lever, and 12th fret with A+B pedals.

Try them first on strings 4-5-6. Common related grips are 3-4-5, 5-6-8, and 6-8-10.
```

The response must include:

- `answer`;
- `sections`;
- `sources: []` for top-level source cards, unless a future deterministic-rule source-card type is explicitly added;
- `fretboard` with the committed `response.fretboard.positions` contract;
- `fretboard.sourceContext` identifying the deterministic rule, not SGF fragments.

The payload must not include raw UI/SVG geometry such as `x`, `y`, `cx`, `cy`, or coordinate fields.

## Answer Gate

Before returning any response, the stack must validate the response against the classified intent.

For `deterministic_chord_position`, the gate must verify:

- the parsed requested root is valid;
- the answer names the requested or canonical root;
- all three deterministic frets are present;
- `response.fretboard` exists;
- the fretboard positions contain stable IDs, frets 0-24, strings 1-10, strings `[4, 5, 6]` for MVP major positions, and no raw geometry;
- A+F and A+B are not swapped;
- unrelated major keys are absent;
- unrelated dominant chords are absent unless progression/dominant context allows them;
- raw SGF/source fragments are absent;
- internal language such as `retrieved material`, `source cards`, or `Useful distilled points` is absent;
- top-level SGF source cards are suppressed.

If any deterministic validation fails, the system must not fall back to retrieval-generated text. It should return a safe deterministic fallback:

```text
On standard E9, I can map plain major-chord positions deterministically, but I could not safely build that diagram for this request. Try asking "Where can I play an A major chord?" or provide the exact root and tuning.
```

For deterministic parse success but response-generation failure, prefer a more specific fallback:

```text
On standard E9, A major is available at the 5th fret no pedals, 8th fret with A pedal + F lever, and 12th fret with A+B pedals. I am omitting source cards because this is a deterministic E9 position rule, not a forum-source answer.
```

## Recommended Backend Implementation

Smallest safe backend sequence:

1. Add an `answer_intents` module or extend `answer_contracts.py` with a strict pre-retrieval intent classifier.
2. In `steel_guitar_rag/api.py`, classify immediately after `parse_answer_request(...)` and before `_search_for_answer(...)`.
3. If intent is `deterministic_chord_position`, call the deterministic chord-position route immediately and skip SGF/private retrieval.
4. Expand `steel_guitar_rag/fretboard_examples.major_chord_location_request_for_question(...)` or move it behind the new classifier so it covers all mandatory phrase variants.
5. Build answer text and `response.fretboard` from `steel_guitar_rag.fretboard_examples` or a narrow successor music-logic module.
6. Clear top-level `sources` for deterministic chord answers and preserve rule provenance in `fretboard.sourceContext`.
7. Add an intent-aware final gate after answer assembly; deterministic failures return deterministic fallback, not RAG fallback.
8. Keep current v2/private retrieval config unchanged for non-deterministic intents.
9. Do not change answer quality logic for unrelated intents in the first implementation pass.

Suggested implementation shape:

```python
intent = classify_answer_intent(answer_request.question, answer_request.mode)

if intent.name == "deterministic_chord_position":
    response = build_deterministic_chord_position_response(answer_request.question)
    return validate_or_fallback(response, intent)

search_response = run_retrieval_if_allowed(intent, answer_request, access)
response = build_answer_from_intent(intent, answer_request, search_response)
return validate_or_fallback(response, intent)
```

The classifier should return a structured object, not only a string:

```python
AnswerIntent(
    name="deterministic_chord_position",
    retrieval_policy="forbidden",
    source_card_policy="suppress",
    visual_payload="required",
    requested_root="B",
    normalized_root="B",
    chord_quality="major",
)
```

## Recommended QA And Eval Coverage

Add route-level unit tests that use fake search indexes proving deterministic questions do not call SGF retrieval:

- `Where can I play a B chord?`
- `Where all can I play a B chord?`
- `How do I play a C#?`
- `How do I make a Bb chord?`
- `Where is A major on E9?`
- `Show me F# positions.`
- `What frets give me C major?`
- `Where can I find B#?`

Add answer payload tests:

- deterministic chord answers include `response.fretboard`;
- `response.fretboard.positions` contains the requested open, A+F, and A+B positions;
- top-level `sources` is empty;
- `fretboard.sourceContext` identifies deterministic rules;
- requested root positions match the reference table;
- A+F and A+B are not swapped;
- unsupported chord qualities fail safely without invented fret/string maps.
- fake SGF and private search indexes are not called for `deterministic_chord_position`.

Add fuzzed phrase variants:

- `where all can i play {root} chord`;
- `where can i find {root}`;
- `how do i make {root} major`;
- `show me {root} positions`;
- `what frets are {root} major`;
- `where is {root} on E9`;
- punctuation, casing, `a/an`, `major chord`, and bare root variants.

Add or keep eval failure buckets:

- `wrong_key_chord_position_leakage`: answer borrows another requested key, such as `G major` in an A question, or unrequested dominant material such as `B7`.
- `missing_visual_payload`: deterministic chord-position answer lacks `response.fretboard`.
- `source_fragment_chord_answer_failure`: deterministic chord-position answer includes raw SGF/tuning/source fragments.
- `missing_deterministic_route`: deterministic chord-position question called SGF retrieval or returned source-backed fallback.
- `deterministic_source_card_leakage`: deterministic chord-position response returned top-level SGF/private source cards.
- `fretboard_position_contract_failure`: deterministic chord-position visual payload lacks `positions`, uses out-of-range frets/strings, swaps A+F/A+B, or contains raw geometry.

The full answer-quality eval should treat any of these buckets as failures, not warnings.

## Implementation Readiness

Implementation should proceed in Lane 05 as a small routing/gating change. The architecture is ready, but the app should not be switched, deployed, or reconfigured as part of the contract implementation. No Chroma, embeddings, scraping, corpus data, generated reports, auth, DNS, or deployment changes are needed.

## Contract Summary

Steel Guitar RAG needs an answer-authority contract, not just answer cleanup. The contract is:

- classify the question before retrieval;
- route deterministic music facts to deterministic music logic;
- allow retrieval only where the intent permits it;
- treat SGF retrieval as supporting-only or forbidden for deterministic E9 positions;
- validate the final response against the chosen intent before returning it.

Plain major chord-location questions are `deterministic_chord_position`. They must return deterministic open/no-pedal, A+F, and A+B positions plus a fretboard payload. They must not use SGF snippets to generate the answer.

## Exact Backend Implementation Recommendations

- In `steel_guitar_rag/api.py`, insert pre-retrieval classification immediately after request parsing.
- Add a structured intent result with at least: `name`, `retrieval_policy`, `source_card_policy`, `visual_payload`, `requested_root`, `normalized_root`, and `chord_quality`.
- Implement `deterministic_chord_position` as a terminal pre-retrieval route.
- Reuse `steel_guitar_rag.fretboard_examples` for E9 major-position math, but expand phrase parsing for the mandatory examples.
- Keep deterministic top-level `sources` empty.
- Put deterministic provenance in `response.fretboard.sourceContext`.
- Add a deterministic answer gate that checks answer text, source cards, and `response.fretboard.positions`.
- If the gate fails, return a deterministic fallback with the computed positions when possible; never fall through to SGF-generated fragments.
- Leave generic RAG, hybrid private retrieval, current Chroma configuration, answer provider configuration, and unrelated contracts unchanged in the first pass.

## Exact QA And Eval Recommendations

- Add unit tests proving `_search_for_answer(...)`, SGF search, and private search are not called for plain chord-location questions.
- Add payload tests for `response.fretboard.positions`, `sourceContext`, no raw geometry, and empty top-level `sources`.
- Add fuzz tests for all 12 roots plus `B#`, `Cb`, `E#`, and `Fb`.
- Add phrase variants for `where all can I play`, `where can I find`, `how do I make`, `show me`, `what frets give me`, `where is ... on E9`, bare `How do I play a C#?`, and punctuation/case changes.
- Promote `missing_visual_payload`, `missing_deterministic_route`, `deterministic_source_card_leakage`, and `fretboard_position_contract_failure` to hard failures.
- Keep the existing wrong-key and source-fragment buckets, and add response-payload validation rather than relying on answer text alone.

## Files Read

- `steel_guitar_rag/api.py`
- `steel_guitar_rag/answering.py`
- `steel_guitar_rag/curated_answers.py`
- `steel_guitar_rag/fretboard_examples.py`
- `steel_guitar_rag/answer_contracts.py`
- `scripts/run_full_answer_quality_eval.py`
- `tests/fixtures/user_question_bank.json`
- `tests/test_full_answer_quality_eval.py`
- `docs/process/codex-completion-protocol.md`
- `docs/answer-generation-contract.md`
- `docs/handoffs/task-completions/2026-06-12-1613-18-answer-generation-contract.md`

## Should Implementation Proceed?

Yes. Implementation should proceed as a separate Lane 05 Backend / RAG Integration task. It should be narrow: add pre-retrieval deterministic intent gating, deterministic chord-position response assembly, response validation, and tests. It should not include deployment, DNS, Chroma, embeddings, scraping, corpus changes, source-inbox changes, auth/security changes, or unrelated answer-quality refactors.
