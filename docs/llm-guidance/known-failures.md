# Known Failures And Regression Memory

This document captures failure classes seen in handoffs and tests. Some are fixed, some are suspected, and all should remain in the mental model for future answer, UI, and QA work.

## Recently Fixed Or Covered

- Invalid chord prompts such as `how do I play a GF chord?` and `how do I play an H chord?` must clarify rather than retrieve.
- Slash-chord prompt `G/F` must explain slash-chord behavior and not show source cards or fretboard payload unless future slash visualization is implemented.
- B9/E-lower prompts must show the appropriate fretboard payload when visualizable.
- Home-prompt smoke hard failures were reduced from `18 -> 0`.
- Product red-team hard failures were reduced from `28 -> 4 -> 0`.
- Stale protected-preview fretboard UI cache was fixed previously with asset cache-bust work.

## Real Steel Questions That Have Failed

Keep regression pressure on these categories:

- `Why does A+B make a chord?`
  - Former failure: misrouted to maker/entity/background fallback.
  - Expected: explain A+B as a pedal combination that changes B to C# and G# to A, forming chord tones in context.
- `Where is a G chord on E9?`
  - Former failure: returned source cards/fragments instead of deterministic visual routing.
  - Expected: fret 3 open, fret 6 A+F, fret 10 A+B, with fretboard payload.
- `What interval is string 5 with the A pedal?`
  - Former failure: raw/source-fragment answer.
  - Expected: string 5 is B open; A pedal raises it to C#; interval depends on key/chord context.
- `Is this a full chord or partial voicing?`
  - Former failure: unrelated C6/source fragments.
  - Expected: ask for fret, strings/grip, pedals/levers, and chord/key before classifying.

## Wrong Routing

Common routing failures:

- Off-domain prompts reaching SGF retrieval.
- Missing-context prompts reaching retrieval instead of asking for details.
- Practical advice prompts returning background/forum fragments instead of drills.
- Beginner concept prompts routed as source-backed facts.
- Valid chord-position prompts missing deterministic fretboard payload.
- Invalid chord-symbol prompts receiving fretboard/source-backed answers.

Regression prompts to keep:

- `Show me all numbers from 1 to 1 million.`
- `Give me a pancake recipe.`
- `Where is a Zm chord?`
- `What is Cmajorish?`
- `What's a better grip for this chord?`
- `Where should I go after A+B in G?`
- `Help me clean up my blocking.`
- `Give me a practice rut breaker.`

## Stale Protected Preview UI

Known class:

- Production/protected preview can serve stale JS/HTML even when backend payload is correct.
- Symptoms:
  - fretboard payload visible in API response but card hidden in UI
  - stale cache-bust key
  - root HTML points to wrong static path
  - UI still expects legacy `highlights`

Required response:

- Verify current static asset path/cache-bust string.
- Browser-smoke the protected preview after cache-bust/static-serving changes.
- Do not assume local tests prove production asset freshness.

## Fretboard Not Showing Or Showing Incorrectly

Failing classes:

- Missing `response.fretboard` for concrete chord/position questions.
- Fretboard card present for non-position questions.
- A+F and A+B swapped.
- Wrong key or borrowed examples in answer body.
- Source cards shown for deterministic fretboard answers.
- Raw UI geometry emitted by backend.
- Selector text exposes implementation metadata such as `full_chord_position`.

Required checks:

- G open: fret 3.
- G A+F: fret 6.
- G A+B: fret 10.
- Positions should use stable musical payloads, not SVG coordinates.

## UI Rendering Failures

Known/suspected regressions:

- `[object Object]` visible in answers or fretboard controls.
- Markdown tables rendering as raw pipes.
- `Common grips` displayed under `Levers`.
- duplicate or orphan `Practical answer` headings.
- vendor/source sections not rendering under expected headings.
- source-card and answer-card text overlapping on mobile.

## Weak-Source And Raw Fragment Failures

Fail when answer body contains:

- `Top`
- `Does anyone know`
- `If I may`
- first-person forum anecdote as the main answer
- unrelated jokes/gore/chatter
- `Useful distilled points`
- `source cards as supporting evidence`
- `source support was weak`
- PayPal/order/contact/email snippets
- raw SGF fragments instead of synthesis

Source cards may contain short excerpts, but the answer body must remain composed by the assistant.

## Missing Source Links

Fail when:

- Source-backed forum wisdom has no source cards.
- Player/history/product/current-ish claims have no source or curated citation when evidence matters.
- Source card URLs are missing when a URL exists in metadata.
- Generated/curated vendor links are injected into unrelated answers.

Pass when:

- Deterministic/source-free answers suppress source cards.
- Source-backed answers show useful cards with meaningful excerpts.

## Non-Position Questions Showing Fretboard

Do not show fretboard for:

- off-domain guardrail
- invalid chord-symbol clarification
- missing-context clarifier
- broad practice/technique answer without concrete position
- gear diagnosis
- player/history
- forum wisdom unless the user asks for a position or the answer includes a concrete visual map

## Position Questions Failing To Show Fretboard

Show fretboard for:

- `Where is a G chord on E9?`
- `Where can I play a G chord?`
- `How do I play G on E9?`
- `Where should I go after A+B in G?`
- concrete B9/E-lower/pocket prompts when visualizable

Use deterministic rules first. Do not retrieve forum fragments to decide these answers.
