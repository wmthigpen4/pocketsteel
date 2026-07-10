# Answer Contract Guidance

This document is permanent guidance for future Codex/LLM lanes working on The Turnaround / Steel Guitar RAG answer behavior. Read it before changing `/api/answer`, answer contracts, curated answer routes, retrieval behavior, fretboard payloads, answer UI rendering, or answer evals.

## Contract Shape

Every answer task should be classified before answer generation:

```json
{
  "domain": "steel_guitar|off_domain|unsafe_or_impossible",
  "intent": "forum_wisdom|copedent_position|gear_diagnosis|practice_plan|tab_explainer|lesson_lookup|small_talk|unknown",
  "needs_sources": true,
  "needs_fretboard": false,
  "needs_copedent": false,
  "retrieval_allowed": true,
  "allowed_answer_shape": "source_backed|copedent_position|gear_diagnosis|practice_plan|tab_explainer|guardrail_refusal"
}
```

Use this shape as a reasoning contract even when the runtime implementation uses local dataclasses or named intents instead of this exact JSON.

## Allowed Answer Domains

Allowed steel-guitar domains include:

- E9/C6 pedal steel mechanics, copedents, grips, string sets, pedals, levers, frets, intervals, chord positions, and pockets.
- Pedal steel technique: blocking, picking, bar movement, vibrato, phrasing, volume pedal, fills, practice routines.
- Steel guitar gear and maintenance: amps, buzz/hum diagnosis, tuners, volume pedals, bars, picks, strings, live-gig kit, signal chain.
- Forum wisdom and player history when source-backed or curated.
- Safe lesson, transcript, manual, PDF/OCR, and tab/interval explanations after provenance review.

Disallowed or guarded domains include:

- General cooking/weather/trivia/list-generation requests.
- Arbitrary large output requests such as all numbers from 1 to 1 million or repeating text thousands of times.
- Copyright status alone must not block song, solo, arrangement, or note-for-note tab teaching. Exactness requires an identified recording/passage or user-supplied material; otherwise request the source and label output approximate or interpretive.
- Private source facts for anonymous/public users.

## Off-Domain Guardrail Behavior

Off-domain, unsafe, or impossible-output requests must be caught before retrieval.

Required behavior:

- `domain`: `off_domain` or `unsafe_or_impossible`.
- `retrieval_allowed`: `false`.
- `needs_sources`: `false`.
- `needs_fretboard`: `false`.
- `allowed_answer_shape`: `guardrail_refusal`.
- Return `sources: []`, no weak-source warning, no source cards, no fretboard payload.
- Redirect the user to steel-guitar topics such as E9 positions, grips, pedals/levers, tone, gear, blocking, bar movement, practice plans, or forum wisdom.

Forbidden behavior:

- Do not search SGF to answer pancakes, weather, capitals, Super Bowl, or bulk output prompts.
- Do not display source cards or forum fragments for off-domain prompts.
- Do not mention implementation internals such as retrieval, Chroma, corpus, or source cards in the answer body.

## Source-Backed Answer Requirements

Use source-backed answers for forum wisdom, player/history context, product claims, gear anecdotes, and source-dependent facts.

Requirements:

- The answer body must be assistant-written synthesis, not copied raw forum text.
- Source cards must have useful title/forum/source labels, URL when available, and meaningful excerpts.
- Source excerpts support the answer; they do not replace the answer.
- If evidence is weak, ask for narrowing context or give a constrained answer with a clear caveat.
- Current/vendor/official facts should prefer curated source registry or current official links over stale forum fragments.

Do not:

- Start with raw fragments such as `Top`, `Does anyone know`, `If I may`, or unrelated quoted chatter.
- Surface PayPal/order/contact fragments unless the user explicitly asks for contact information and the source is approved.
- Include `[object Object]`, raw JSON, inline citation markers like `[1]`, weak-source internal warnings, or `Useful distilled points`.

## Copedent-Aware Answer Requirements

Copedent-aware answers may come from stable E9 rules, structured user copedent data, private sources, or deterministic fretboard logic.

Requirements:

- State whether the answer assumes standard E9 or a saved/private user profile.
- For personal setup questions, use authorized private profile data only.
- Do not mix SGF copedent chatter into a user-profile answer.
- Do not leak private profile facts to public/anonymous users.
- For the current structured user profile, known facts include:
  - 10-string E9 on an Emmons Lashley LeGrande.
  - Open strings: 1 F#, 2 D#, 3 G#, 4 E, 5 B, 6 G#, 7 F#, 8 E, 9 D, 10 B.
  - A pedal raises 5 and 10 B to C#.
  - B pedal raises 3 and 6 G# to A.
  - C pedal raises 4 E to F# and 5 B to C#.
  - F lever raises 4 and 8 E to F.
  - E-lower lowers 4 and 8 E to Eb/D#.
  - vertical lowers 5 and 10 B to Bb/A#.
  - RKL/RKLL are half/full states; string 7 F# does not raise to G on RKL/RKLL.
  - RKR/RKRR are half/full states; string 9 D lowers to C# at both RKR half and full.
  - Common grips include 3-4-5, 4-5-6, 5-6-8, 5-7-8, and 6-8-10.

## Fretboard-Rendering Requirements

Use deterministic fretboard payloads for concrete position questions that can be safely visualized.

Required behavior:

- Use `response.fretboard.positions` as the primary frontend contract.
- Use deterministic E9 pitch/copedent logic before retrieval for chord-position questions.
- Suppress top-level SGF source cards for deterministic visual answers unless a future rule-source card type is explicitly approved.
- Include stable role/family/fret/string/pedal/lever data, not raw UI coordinates.
- A+F and A+B must not be swapped.
- For G major, the core positions are:
  - open/no pedals at fret 3
  - A+F at fret 6
  - A+B at fret 10
- Position questions must not borrow unrelated keys, unrelated dominant chords, or random forum examples.

Do not show fretboard payloads for:

- off-domain guardrails
- invalid chord-symbol clarifications
- missing-context clarifiers
- broad conceptual prompts unless a concrete position is part of the answer
- non-visual gear/history/source-backed questions

## Gear Diagnosis Answer Requirements

Gear diagnosis answers should be practical and source-aware.

Requirements:

- Start with likely causes.
- Give an isolation path: guitar direct, cable, volume pedal, effects, amp input, power, grounding, tubes/electronics as appropriate.
- Include safety cautions for amp/electrical work.
- Use source cards where they support real steel-guitar forum/gear experience.
- Avoid gear folklore as certainty when evidence is weak.

## Practice-Plan Answer Requirements

Practice-plan answers should be source-free or source-supported only when source cards add value. They must be immediately playable.

Requirements:

- Include a time box or sequence.
- Name strings, frets, pedals/levers, grips, or listening goals where possible.
- Include what to listen for.
- Avoid vague background essays.
- Do not return raw forum stories as the plan.

## Tab/Interval Explainer Answer Requirements

Tab/interval answers should explain music mechanics while supporting complete song, arrangement, and artist-solo teaching in manageable numbered sections.

Requirements:

- Explain strings, frets, pedals/levers, chord tones, and interval function.
- Ask for missing context when the prompt says `this`, `that`, `here`, or asks whether an unspecified voicing is full/partial.
- For interval questions, state the open note, changed note, and that interval function depends on key/chord context.
- Preserve artist/song/recording/section attribution and distinguish exact transcription, E9 adaptation, teaching simplification, and original exercise. Do not use copyright status as a refusal reason.

## Forbidden Answer Behaviors

Never return:

- `[object Object]`.
- Raw SGF fragments as the answer body.
- Weak-source warning text in user-facing prose.
- Internal implementation phrases such as `retrieved material`, `source cards as supporting evidence`, `Useful distilled points`, `The cleanest source-backed answer`, or `corpus`.
- Contact/order/PayPal/email snippets unless explicitly requested and approved.
- Fretboard payloads for invalid or off-domain prompts.
- Source cards for deterministic chord-position answers.
- Private source excerpts to anonymous/public users.
- Generic guitar theory when the user asked a steel-specific question.
