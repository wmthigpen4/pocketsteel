# Tab Engine Answer UX Plan

## Task Summary

Lane: 06 UX/UI Design.

Requested a UX plan for deterministic pedal steel tab output on the answer page while Lane 05 builds the backend tab engine. This is a parallel planning task only. No backend logic, answer routing, tab generation, Chroma, corpus, scraping, auth, deployment, or production runtime behavior was changed.

The user prompt refers to "Pocket Steel" tab output. Repo guidance says current user-facing app naming is still in transition and not to perform broad renames. This plan therefore focuses on the answer-page UX and uses neutral component names; final user-facing copy should follow the product naming decision active at implementation time.

## Files And Components Inspected

- `AGENTS.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/llm-guidance/answer-contract.md`
- `docs/llm-guidance/eval-rubric.md`
- `docs/llm-guidance/teacher-first-answer-policy.md`
- `tests/answer_eval/expected_behaviors.md`
- `ui/steel-guitar-rag-mock.html`
  - answer workspace shell
  - `.answer-card`
  - `.answer-detail-grid`
  - `.answer-section`
  - `.answer-table`
  - `.answer-fretboard`
  - `.source-section`
  - `renderResponse()`
  - `appendAnswerSectionContent()`
  - `renderFretboardVisualization()`
- `ui/answer-client.js`
  - `normalizeAnswerResponse()`
  - `normalizeSections()`
  - markdown table parsing
  - fretboard payload preservation
  - source normalization
- `ui/pedal-steel-fretboard.js`
  - position controls
  - selector cards
  - detail panel
  - technical details collapse
  - SVG stage and mobile scroll behavior
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`

## Current Answer Page Shape

The answer page currently renders this hierarchy:

1. Question card.
2. Main `.answer-card` with a lead section and detail sections.
3. Optional `.answer-fretboard` card, hidden unless `response.fretboard` exists.
4. Source notes.
5. Follow-up chips.
6. Ask-another-question input.

This is a good foundation for tab output. The first tab UI slice should fit between the main answer card and source cards, near the fretboard section, while keeping the teaching answer primary.

## Recommended Answer-Page Layout

### Primary Teaching Flow

The answer card should still lead with synthesized teaching prose:

1. Direct answer.
2. Why it works.
3. Try this.
4. Optional tab example.

Tab should never replace the teaching answer. It should illustrate the answer.

Recommended order when an answer includes tab:

```text
Question

Answer card
- Direct answer
- Why it works
- Try this

Tab card / tab examples

Optional fretboard card

Source notes

Follow-ups
```

If tab and fretboard are both present, the tab should usually appear before the fretboard when the tab is the primary demonstration. The fretboard can then become the visual explanation of the selected event later.

## Proposed UI Components

### `answer-tab-section`

New answer-page section, sibling to `answer-fretboard`.

Recommended placement in `ui/steel-guitar-rag-mock.html`:

```html
<section class="answer-tab" id="answer-tab" hidden>
  <div class="tab-card">
    <div class="tab-card-header">
      <p class="answer-section-title">Tab example</p>
      <span class="tab-validation-badge">Validated</span>
    </div>
    <p class="tab-context"></p>
    <pre class="tab-block"><code></code></pre>
    <div class="tab-explanation"></div>
  </div>
</section>
```

Use `pre > code` with a monospaced font and horizontal overflow inside the card.

### `tab-card`

Use for one compact tab example. This is the default component for small examples inside a normal answer.

Fields:

- Title: what the tab demonstrates.
- Context line: key, tuning, grip, difficulty.
- Validation badge/status.
- Monospaced tab block.
- Why this works.
- Intervals/chord tones.
- Optional controls.

### `tab-card-list`

Use for "Show me 3 ways" style answers.

Default behavior:

- Show 3 cards maximum without extra expansion.
- Each card has a short title and compact tab.
- A selected/expanded card shows "Why this works" and intervals.
- Avoid dumping several tall tab blocks at once on mobile.

### `tab-validation-card`

Use for pasted-tab explanation or validation results.

Good states:

- `Valid`
- `Playable with caveats`
- `Needs context`
- `Impossible on this copedent`
- `Copyright-limited`

The validation state should be friendly and actionable. Example:

```text
Playable with caveats
This grip works if your E-lower is on strings 4 and 8. The tab does not specify blocking, so start slowly and check sustain.
```

### `practice-tab-exercise`

Use for practice exercise output.

Recommended structure:

- Goal.
- Time box.
- Tab block.
- What to listen for.
- One variation.
- Stop condition.

## Output Type Designs

### 1. Small Example Tab Inside A Normal Answer

Use when tab supports a larger teaching answer.

Visual hierarchy:

- Compact card.
- Short title.
- One tab block.
- Explanation below.
- Controls minimized.

Example copy:

```text
Simple A+B move in G
Key: G · Tuning: E9 · Grip: 4-5-6 · Difficulty: beginner

Validated for standard 10-string E9

[monospaced tab]

Why this works:
At fret 10 with A+B down, strings 4-5-6 outline a G major pocket. Keep the bar still and listen for the change against the pedals.
```

UX rule:

- If the tab is shorter than 6 lines, show it inline.
- If longer, collapse after the first tab block with a "Show full tab" disclosure.

### 2. "Show Me 3 Ways" Tab Cards

Use a small grid/list of cards, not one huge block.

Recommended layout:

```text
3 ways to play that phrase

[Card 1: Beginner] [Card 2: More color] [Card 3: Higher position]
```

Each card:

- Title.
- Context line.
- Tab preview.
- "Why this works."
- "Show on fretboard" button prepared but disabled/hidden until event sync exists.

Desktop:

- 2 or 3 cards per row only if tab remains readable.
- Prefer one-column vertical cards for longer tab.

Mobile:

- Single column.
- Only the selected card's full tab open by default.

### 3. Tab Explanation / Validation Result

Use when the user pastes tab or asks "does this work?"

Recommended layout:

```text
Tab check
Playable with caveats

What it says:
- Fret 3, strings 5-7-8, E-lower
- Notes: ...
- Intervals: ...

What to fix:
- ...

[monospaced original/sanitized tab]
```

Important:

- Do not shame the user.
- Avoid "invalid" as the only message. Say what is missing or what assumption is needed.
- Do not display raw parser internals.

### 4. Practice Exercise Output

Use for "give me something to practice" answers.

Recommended sections:

- Goal.
- Tab exercise.
- What to listen for.
- Variation.
- Practice plan.

Example copy:

```text
Goal
Cleanly block strings 4-5-6 while moving from no-pedals to A+B.

Tab exercise
[monospaced tab]

What to listen for
The previous chord should stop before the next one blooms. If the notes smear together, slow down and isolate the right hand.
```

### 5. Future Event-By-Event Fretboard Sync

Do not build this in the first slice. Prepare the model and DOM for it.

Future behavior:

- Each tab event has an `eventId`.
- Each rendered tab token can carry `data-tab-event-id`.
- The fretboard position/highlight can carry the same event id.
- Selecting a tab event highlights:
  - the tab position,
  - the matching fret/string group,
  - the detail explanation.

Future controls:

- Previous event.
- Next event.
- Play slowly.
- Show picking events.
- Show intervals.
- Show bar movement.

Do not add audio/playback in the first UI slice.

## Suggested Future Payload Shape

This is a UX-consumption suggestion only. Lane 05 owns backend contract decisions.

```json
{
  "tab": {
    "title": "Simple A+B move in G",
    "context": {
      "key": "G",
      "tuning": "E9",
      "grip": "4-5-6",
      "difficulty": "beginner"
    },
    "validation": {
      "status": "validated",
      "label": "Validated for standard 10-string E9",
      "caveats": []
    },
    "tabText": "4---------10B--\\n5---------10A--\\n6---------10B--",
    "whyItWorks": "At fret 10 with A+B down, strings 4-5-6 outline a G major pocket.",
    "intervals": ["root", "3rd", "5th"],
    "chordTones": ["G", "B", "D"],
    "sourceNote": "Optional source-backed note when this follows a forum or lesson answer.",
    "events": [
      {
        "id": "event-1",
        "fret": 10,
        "strings": [4, 5, 6],
        "pedals": ["A", "B"],
        "levers": [],
        "notes": ["G", "B", "D"],
        "intervals": ["root", "3rd", "5th"]
      }
    ]
  }
}
```

For multiple examples:

```json
{
  "tabs": [
    { "id": "way-1", "title": "Beginner grip", "...": "..." },
    { "id": "way-2", "title": "More color", "...": "..." },
    { "id": "way-3", "title": "Higher position", "...": "..." }
  ]
}
```

The frontend should support either one `tab` or a short `tabs[]` list, but should not generate tab itself.

## Visual Hierarchy

1. Answer prose stays largest and visually dominant.
2. Tab card is dark, quiet, and readable.
3. Monospaced tab block is strong but bounded.
4. Validation badge is visible but not alarm-like.
5. Controls are small and secondary.
6. Source notes remain evidence below.

Recommended styling:

- Use existing warm amber/dark card treatment.
- Use `font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` for tab.
- Use large enough tab text for older users: desktop `16px-18px`, mobile `15px-16px`.
- Use `overflow-x: auto` inside the tab block.
- Keep line height around `1.55` to prevent string lines from blending.
- Avoid decorative animation inside the tab block.

## Mobile Considerations

- Tab block must scroll horizontally inside the card, not widen the page.
- Long tab examples should use `<details>` or a "Show full tab" expansion.
- "Show me 3 ways" should default to one open card and two compact summaries.
- Controls should wrap into two rows max when possible.
- Copy button should be large enough to tap.
- The tab/fretboard sync concept should use next/previous controls on mobile rather than requiring precise tapping on tiny tab characters.

## Accessibility And Readability

- Preserve whitespace using `<pre><code>`.
- Add an accessible label to the tab block, such as `aria-label="Pedal steel tab example"`.
- Validation badge should have text, not color alone.
- Do not use color alone to encode beginner/more-color states.
- Copy button should announce success with a polite live region.
- Avoid tiny interval badges; prefer readable inline text.
- Respect reduced motion; future event sync should not auto-animate for reduced-motion users.

## Optional Controls

Recommended first-slice controls:

- `Copy tab`
- `Show intervals`
- `Show picking events` only if backend returns picking events
- `Show on fretboard` present only when event/fretboard mapping exists

Mode controls:

- `Beginner`
- `More color`

These should filter or simplify the explanatory display, not mutate generated tab.

Do not add:

- Playback/audio.
- Tempo controls.
- Editable tab.
- Export/download.
- Full song/tab builder.
- Copyrighted-song tab prompts or affordances.

## Copyright And Safety Guardrails

The tab UI should reinforce that the first version is for:

- short educational examples,
- public-domain material,
- user-provided phrases,
- technique demonstrations,
- validation/explanation of user-provided tab.

Do not make the UI look like a copyrighted-song tab machine. Avoid prompts like "Generate full tab for [song]."

If backend returns a copyright-limited or missing-rights status, the UI should show a quiet guardrail:

```text
I can explain the move or create a short educational example, but I cannot provide a full copyrighted arrangement.
```

## What Not To Show Yet

- No fake generated tab.
- No placeholder "coming soon" tab block in real answers.
- No raw event JSON.
- No parser debug data.
- No `[object Object]`.
- No backend validation internals such as raw enum names.
- No source cards as tab content.
- No giant grid of every possible tab variation.

## Recommended First UI Implementation Slice

Smallest useful frontend slice after Lane 05 has a real payload:

1. Add `normalizeTabPayload()` in `ui/answer-client.js`.
2. Preserve `payload.tab` and `payload.tabs` if present.
3. Add an `answer-tab` section in `ui/steel-guitar-rag-mock.html` between `.answer-card` and `.answer-fretboard`.
4. Add `renderTabExamples()` that:
   - hides/clears when no tab payload exists,
   - renders one compact tab card,
   - renders up to three tab cards,
   - uses monospaced `<pre><code>`,
   - displays validation status text,
   - displays `Why this works`,
   - optionally displays intervals/chord tones.
5. Add CSS for `.tab-card`, `.tab-block`, `.tab-validation-badge`, `.tab-controls`.
6. Add tests in `tests/test_frontend_answer_ui.py` for:
   - tab payload preserved by normalization,
   - tab block renders as monospaced/pre/code,
   - no tab section for non-tab answers,
   - no `[object Object]`,
   - three tab cards render without page-level source/fretboard displacement.

Do not implement fretboard sync until event ids and backend event payloads are stable.

## Acceptance Criteria For First UI Slice

- A valid backend tab payload displays below the primary answer.
- Non-tab answers show no tab area.
- Tab text appears in a monospaced scroll-safe block.
- Validation status is visible and text-based.
- Title/context are readable.
- "Why this works" appears under the tab.
- Intervals/chord tones render as readable text.
- Source notes stay below and secondary.
- The answer card remains the visual lead.
- Mobile has no page-level horizontal overflow.
- Copy tab works if implemented.
- No fake tab is generated on the frontend.
- No raw JSON or `[object Object]` appears.

## Browser Smoke Plan

After Lane 05 returns real tab payloads, smoke:

```text
Smoke Target:
- Target type: local/protected-preview as appropriate
- Result type: browser smoke
- Exact browser URL tested:
- Cache-busted URL tested:
- Auth required:
- Auth provider:
- Local backend URL:
- Expected backend port:
- Expected git HEAD:
- Version endpoint:
- Version endpoint result:
- Whether app root `/` works:
- Whether `/ui/steel-guitar-rag-mock.html` works:
- Who should test this URL: Codex and the user
- Known caveats:
```

Suggested prompts:

- "Show me a short E9 tab example for A+B in G."
- "Give me 3 ways to practice a simple G to C move."
- "Explain this tab: [user-provided short phrase]."
- "Give me a 5-minute blocking exercise with tab."
- A non-tab gear question, to verify no tab UI appears.

Visual checks:

- Tab block readable at desktop and narrow widths.
- Source cards do not crowd the tab.
- Fretboard card remains hidden unless payload includes visual positions.
- Copy tab does not alter layout.
- Long tab scrolls inside the card.

## Risks And Dependencies On Lane 05

- Backend must provide validated tab text; frontend should not generate it.
- Event-by-event sync depends on stable event ids and position metadata.
- Copyright/rights status should be explicit enough for frontend guardrail copy.
- If backend sends multiple tabs, it should identify recommended/default examples so UI does not overwhelm the user.
- If backend sends picking events, the shape needs to distinguish pick direction/finger from musical notes and intervals.

## Human Decision Needed

Yes, before implementation:

- Confirm final user-facing product naming for tab UI copy.
- Confirm whether first UI slice should accept `tab`, `tabs`, or both.
- Confirm whether "Show on fretboard" should be hidden until sync exists or shown disabled as a future affordance.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-1516-06-tab-engine-answer-ux.md`

## Files That Must Not Be Staged

- Current unrelated dirty files shown by `git status --short`
- Backend files
- corpus, Chroma, embeddings, source-inbox raw data, scraping outputs
- deployment/DNS/secrets
- raw design assets
- `public/` and `ui/brand/` unless a separate asset task explicitly approves them

## Recommended Next Lane

Lane 18 Product / Architecture or Lane 05 Backend / RAG Integration should confirm the tab payload contract. After that, Lane 06 UX/UI Design can implement the first UI slice.

## Commit Readiness

Safe to commit as a docs-only planning artifact.

## Suggested Next Prompt For Lane 06

```text
Lane: 06 UX/UI Design
Implement the first tab-output answer UI slice from docs/handoffs/task-completions/2026-06-18-1516-06-tab-engine-answer-ux.md after Lane 05 confirms the tab payload shape. Do not generate tab on the frontend. Preserve answer-first hierarchy, render tab in pre/code, hide tab UI for non-tab answers, add focused frontend tests, and write a handoff.
```
