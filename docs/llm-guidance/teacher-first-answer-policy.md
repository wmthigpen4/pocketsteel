# Teacher-First Answer Policy

This document extends `docs/llm-guidance/answer-contract.md`, `docs/llm-guidance/eval-rubric.md`, and `docs/llm-guidance/product-memory.md`.

The core product decision is simple: Steel Guitar RAG must answer like a steel-guitar teacher first. Source retrieval is evidence. It is not the user-facing lesson.

## Product Rule

The answer box must contain a synthesized teaching answer, not copied source snippets.

Forum and message-board sources are useful because they capture player experience, vocabulary, disagreements, and real-world setup context. They should support the lesson below the answer. They must not become the lesson.

Source-backed does not mean source-quoted.

## Visual Priority

The answer must be visually and conceptually stronger than the sources.

Required UI hierarchy:

1. Answer card: direct synthesized teaching answer.
2. Optional fretboard card: only when the answer needs a visual position map.
3. Source cards: secondary evidence, collapsed or visually quieter by default where practical.

Source excerpts belong below the answer. The user should be able to learn the practical answer without reading forum excerpts first.

Do not make source cards look like the primary answer. Do not let a stack of source cards visually overpower the answer card or fretboard selector.

## Source-Backed Answers

For source-backed answers, the app should produce this answer shape:

1. Direct answer.
2. Why it works.
3. Practical steel-guitar application.
4. Source-backed notes, if relevant.
5. Caveats or conflicting opinions, if relevant.

The answer body should paraphrase and synthesize:

- what multiple players agree on
- where players disagree
- what the user should try first
- what setup or context changes the answer

The answer body must not copy source excerpts as its main content. If a short quote is ever useful, it should be exceptional, brief, and clearly secondary to the synthesized explanation.

## Copedent And Fretboard Answers

For copedent, chord-position, and fretboard answers, the app should produce this answer shape:

1. Recommended starting position.
2. Strings, frets, pedals, and levers.
3. Intervals or chord tones.
4. Two to four best alternate positions.
5. Optional "show more" for additional grips, inversions, rootless/partial pockets, or advanced positions.

The answer should name what to try first. The fretboard should not dump every possible card by default.

Default fretboard behavior:

- Show starter and common positions first.
- Keep alternate, advanced, partial/rootless, and copedent-dependent cards behind filters or "show more" behavior.
- Use the fretboard to teach a small number of useful choices, not to prove the engine found many possibilities.
- Suppress SGF source cards for deterministic chord-position answers unless a future rule-source card type is explicitly approved.

## General Music Questions

For general music questions that are still relevant to steel guitar, the app should prefer a plain teaching answer before forum evidence.

Example: "What's it mean for a song to be a swing or a waltz?"

Expected behavior:

- First explain the concept plainly.
- Then connect it to steel-guitar playing: time feel, subdivision, comping/fills, volume pedal phrasing, bar movement, and where to leave space.
- Only show forum evidence if it adds meaningful steel-player context.

Do not retrieve and stitch forum fragments when a clean teaching explanation is the right first answer.

## Forbidden Fragment Answers

The app must never answer with:

- raw forum or message-board snippets as the answer body
- raw tab scraps
- partial post excerpts
- unrelated source quotes
- lightly stitched excerpts with no teacher synthesis
- source-card text copied into the answer card
- source cleanup leftovers such as greetings, signatures, edited-post markers, links, or contact/order chatter

Explicitly forbidden fragment examples:

- `Which someone else is probably playing`
- `I MAY BE LEARNING`
- `Top Hi All`
- `Does anyone know`
- `Can some of you possibly post`
- `Useful distilled points`
- `retrieved material`
- `source cards as supporting evidence`
- `[object Object]`

If the available sources are too weak or fragmentary, the answer should say what can be answered safely, ask for narrowing context, or return a deterministic fallback. It should not display random SGF fragments as if they were an answer.

## Screenshot-Derived Failure Cases

These failures should be treated as product regressions:

### G-Minor Chord

Failure: "How do I play a G-minor chord?" produced raw source fragments and an overwhelming fretboard grid.

Expected behavior:

- Start with a recommended playable G minor location or state that deterministic minor support is limited.
- Name strings, fret, pedals/levers, and intervals if known.
- Show no more than the best two to four positions by default.
- Hide additional grips, inversions, or partial/rootless cards behind "show more" or filters.
- Do not use forum fragments to fill a missing deterministic minor answer.

### 1-4-5-1 Turnaround

Failure: "How do I play a 1-4-5-1 turnaround?" produced raw tab/forum snippets instead of teaching the progression.

Expected behavior:

- Explain the progression as I-IV-V-I.
- Give a simple E9 starting example in one key, usually G or the requested key.
- Name frets, pedals/levers, strings/grips, and the movement path.
- Give one short practice step.
- Use source cards only if they add real context; do not show raw tab scraps as the answer.

### Swing Or Waltz

Failure: "What's it mean for a song to be a swing or a waltz?" produced forum fragments instead of a clean music explanation.

Expected behavior:

- Explain swing feel and waltz meter plainly.
- Connect each to steel-guitar phrasing and accompaniment.
- Keep forum evidence secondary or absent unless it adds useful player practice context.

## Ideal Answer Templates

These are product templates, not mandatory exact headings. Runtime code may use different section labels if the same teaching structure is preserved.

### Chord Position Question

Use for: "Where can I play a G chord?", "How do I play a G-minor chord?", "Show me C# positions."

```text
Direct answer:
Start with [chord] at [fret] on strings [strings], using [pedals/levers or open]. That gives you [intervals/chord tones].

Why it works:
[Explain the E9 family: open/no-pedals, A+F, A+B, E-lower, minor family, etc.]

Try these positions:
- [Best starter position]: fret, strings, pedals/levers, intervals.
- [Alternate 1]: fret, strings, pedals/levers, why useful.
- [Alternate 2]: fret, strings, pedals/levers, why useful.

Practice it:
Pick one grip, say the intervals out loud, and move between the starter and one alternate slowly.

Caveat:
[Only if needed: standard E9 assumption, minor support limitation, user copedent dependency, no slants yet.]
```

Fretboard default: show starter/common positions only. Extra grips and inversions belong behind filters or "show more."

### Turnaround Or Progression Question

Use for: "How do I play a 1-4-5-1 turnaround?", "Show me a smoother turnaround."

```text
Direct answer:
A 1-4-5-1 turnaround means moving from the home chord to the IV chord, then V, then back home. In [key], that is [I]-[IV]-[V]-[I].

One E9 path:
- I: [fret, grip, pedals/levers]
- IV: [fret, grip, pedals/levers]
- V: [fret, grip, pedals/levers]
- I: return to [position]

Why it works:
[Explain the pedal/lever or fret movement and the chord functions.]

Practice it:
Use one grip, play each chord once, block cleanly between changes, then add one simple fill only after the movement is smooth.

Caveat:
[Mention assumed tuning/key or ask for key if missing.]
```

Source cards are optional. Raw tab scraps are forbidden.

### General Music Theory Question

Use for: "What's it mean for a song to be a swing or a waltz?", "What is a ii-V-I?"

```text
Direct answer:
[Plain-language concept explanation.]

How it affects steel guitar:
[Explain feel, rhythm, chord movement, phrasing, or accompaniment in steel terms.]

What to try:
[One concrete exercise or listening target.]

Source-backed note:
[Only if forum evidence adds a useful player-specific observation.]
```

The first answer should be a clean explanation, not a forum digest.

### Gear Diagnosis Question

Use for: "Why does my hum change when I touch the changer?", "Why does my tone sound thin?"

```text
Direct answer:
The most likely causes are [short list].

Diagnostic path:
1. Test [guitar/cable/volume pedal/amp] in isolation.
2. Add one part of the signal chain at a time.
3. Compare what changes.
4. Stop before unsafe amp/electrical work.

Practical steel-guitar application:
[Tie the diagnosis to pickup, changer ground, volume pedal, amp input, bar/pick attack, or stage setup.]

Safety:
[Amp/electrical caution if relevant.]

Source-backed notes:
[Summarize player reports only when they support the diagnosis.]
```

Do not answer a diagnostic prompt with unrelated gear anecdotes or source fragments.

### Practice Plan Question

Use for: "Build a 7-day practice plan for blocking.", "What should I practice tonight?"

```text
Direct answer:
Use this [time box] plan focused on [skill].

Plan:
- [Step with minutes or repetitions]
- [Step with strings/grip/fret/pedals/levers]
- [Step with listening goal]
- [Step with musical application]

What to listen for:
[Timing, intonation, blocking, sustain, space, or feel.]

Make it harder:
[One progression or tempo variation.]
```

Practice plans should usually be source-free unless source evidence adds a specific, useful player-tested drill.

### Tab Or Interval Explanation Question

Use for: "What does this tab mean?", "What intervals are in this grip?", "Is this a full chord?"

```text
Direct answer:
[Explain the tab/interval/function in plain terms.]

String-by-string:
- String [n]: [open note] -> [changed note], interval [x] in [key/chord context]
- String [n]: [open note] -> [changed note], interval [x]

What it gives you:
[Full chord, partial voicing, rootless color, inversion, passing sound, etc.]

How to use it:
[One practical playing context.]

Need more context:
[Ask for key, fret, strings, pedals/levers, or target chord if missing.]
```

Teach full songs, artist solos, and copyrighted arrangements when requested. Copyright status alone is not a refusal reason. Require an identified recording/passage or user-supplied material before claiming exact transcription; otherwise label the result as an E9 adaptation, teaching simplification, approximate, or interpretive. Divide long material into numbered sections.

## Answer Gate Requirements

Before a response reaches the UI, answer generation should reject or repair answers that:

- begin with raw source text
- use source excerpts as the main answer body
- contain unrelated chord/key/source fragments
- expose internal retrieval language
- include `[object Object]`
- include weak-source warnings as user-facing prose
- show source cards for deterministic fretboard answers
- show a fretboard payload for non-visual conceptual answers
- dump many fretboard cards by default when a smaller starter set is enough

If repair fails, return a safe teacher-first fallback, a deterministic answer, or a missing-context clarification.

## Eval Implications

Add or preserve regression buckets for:

- raw source fragment in answer body
- source cards visually stronger than answer
- source-backed answer without synthesis
- deterministic position answer using SGF fragments
- fretboard over-dump by default
- general music theory routed to forum fragments
- raw tab scraps in answer body
- unrelated source quote leakage
- missing caveat for weak/conflicting source evidence

Browser smoke should inspect both content and visual hierarchy:

- Does the answer card teach the user before sources appear?
- Are source excerpts below or collapsed/secondary?
- Are fretboard cards limited to starter/common positions by default?
- Does the source area feel like evidence rather than the answer?

## Implementation Direction

Backend answer generation should compose a teacher-first answer object before source cards are attached. Retrieval may provide evidence, but the answer body should be synthesized from the selected intent template.

Frontend rendering should keep the answer card dominant, make source cards secondary, and avoid default-expanded source stacks that compete with the lesson.

QA should fail any answer where source-backed means source-quoted.
