# 2026-06-18 - Lane 06 - Answer-Triggered Tab Example UX Follow-Up

## Task Summary

Requested: define the UI acceptance behavior for `tab_example` payloads attached to normal answer responses while Lane 05 implements answer-triggered deterministic tab examples.

Completed: created this UX follow-up handoff only.

Intentionally not changed:

- No implementation files were edited.
- No frontend fake tab generation was added.
- No answer UI redesign was attempted.
- No backend, answer routing, Chroma, embeddings, corpus, scraping, auth, deployment, or DNS files were touched.

Branch: `feature/answer-api`

Relevant commits noted by the task:

- `686fd3c feat: add deterministic tab engine slice`
- `54a28c7 fix: clear tab examples on stage return`
- `7834c67 docs: plan tab engine follow-on slices`

## 1. Expected Answer-Page Behavior

When a normal `/api/answer` response includes a supported `tab_example`, the answer page should show one compact tab card after the main teaching answer. The tab card is supporting material, not the main answer.

Expected default flow:

1. Primary answer content.
2. Optional `tab_example` card.
3. Optional fretboard visualization, if present.
4. Source cards / evidence, if present.

If no `tab_example` exists, the existing answer layout must remain unchanged. There should be no empty tab shell, placeholder, loading slot, or "no tab returned" message.

If `tab_example.validation.ok` is `false`, do not show the tab in normal user-facing answers. Invalid examples may be shown only in an explicit debug/dev validation context.

## 2. Tab Card Placement In Normal Answers

Place the tab card directly below the main answer card and before any fretboard/source sections. This keeps the tab visually connected to the explanation while preventing it from swallowing the answer page.

The card should be visually calm and compact:

- small title,
- one context line,
- validation badge,
- monospace tab block,
- optional short explanation and intervals.

Avoid making every answer feel like a tab page. A single answer should normally show zero or one tab card. If Lane 05 later returns multiple tab examples, the UI should cap visible cards or collapse extras behind a clear "Show more tab examples" affordance.

## 3. When Tab Should Be Collapsed Vs Expanded

Default expanded:

- beginner examples,
- one short example,
- tab text that fits within a modest card height,
- answers where the user explicitly asked for a tab/example phrase.

Default collapsed or compact:

- tab is supporting evidence rather than the requested object,
- more than one example exists,
- the tab is long enough to push the answer or source cards far down the page,
- the response is primarily conceptual and the tab is optional practice material.

First implementation slice can keep one short validated tab expanded. Add collapse behavior only when payload length or multiple examples make the page feel crowded.

## 4. Context Line Requirements

For beginner-friendly examples, show a simple context line above the tab block. Preferred fields:

- key,
- tuning,
- grip,
- difficulty,
- profile if useful and not noisy.

Example copy:

`Key: G | Tuning: E9 | Grip: 4-5-6 | Difficulty: beginner`

Do not expose internal implementation fields in the learner-facing context line. Avoid raw IDs, registry names, Python enum names, or contract-only values.

## 5. Validation Status Display

Show a compact validation badge when a validated tab is rendered.

Recommended labels:

- `Validated` for `validation.ok === true`.
- `Needs review` only in debug/dev views.

Normal answer page rule:

- If `validation.ok === false`, hide the tab card entirely unless the page is in a deliberate debug/dev validation mode.

If validation issues exist on a valid warning-style payload, show them as a subdued "Validation notes" line below the tab. Do not let validation notes dominate the answer.

## 6. Explanation / Interval Display

The tab card should explain why the example works without turning into a theory wall.

Recommended optional rows:

- `Why this works`: one short sentence.
- `Intervals`: compact comma-separated values.
- `Chord tones`: compact comma-separated values, if present.
- `Source note`: only if the tab follows a source-backed answer or lesson note.

Keep these rows under the tab block. Do not put long theory explanations inside the tab card; the answer body should carry the teaching.

## 7. Mobile Behavior

Tab text must preserve alignment on small screens.

Required behavior:

- Use `pre > code` or equivalent.
- Preserve whitespace exactly.
- Do not wrap tab rows.
- Allow horizontal scrolling inside the tab block.
- Do not create page-level horizontal overflow.
- Keep font size readable for older players.

The tab block may scroll horizontally, but the answer card, source cards, and surrounding layout should remain within the viewport.

## 8. Accessibility / Readability

Accessibility requirements:

- Use semantic text, not an image, for the tab.
- Give the tab block an accessible label such as `"G to C beginner move tab"`.
- Preserve color contrast in the dark/amber theme.
- Do not rely on color alone for validation status.
- Keep the validation badge text visible.
- Use a readable monospace font stack.
- Maintain enough line height for older users.

Readability requirements:

- Tab block should be visually distinct but not louder than the answer.
- Context and explanation text should be short.
- Avoid dense controls in this slice.

## 9. Empty / No-Tab Behavior

If the response has no `tab_example`:

- no tab card renders,
- no empty tab section is visible,
- normal answer/fretboard/source layout is unchanged.

If the response includes malformed or empty tab data:

- hide the tab card,
- avoid `[object Object]`,
- optionally log a console warning in development,
- do not break the answer page.

## 10. Acceptance Criteria For Implementation

Implementation acceptance criteria:

- A normal answer response with a valid `tab_example` shows a compact tab card after the primary answer.
- A response without `tab_example` is visually unchanged.
- Invalid `tab_example.validation.ok === false` payloads do not render in normal user-facing mode.
- Tab text is displayed in a monospace block with preserved whitespace.
- Mobile uses internal horizontal scrolling for tab text.
- Context line displays learner-friendly fields: key, tuning, grip, difficulty.
- Validation status is visible but subtle.
- Explanation and interval rows render when present.
- No complex controls are introduced.
- No fake frontend tab generation exists.
- No backend schema assumptions beyond the committed `tab_example` contract.
- No `[object Object]` appears in rendered tab content.

## Files Changed

- `docs/handoffs/task-completions/2026-06-18-06-answer-triggered-tab-example-ux-followup.md`

## Tests / Checks Run

Planned for this docs-only task:

- `git diff --check`
- `git status --short`

No frontend/backend tests are required because no implementation files were changed.

## Risks

Risk: Low.

The handoff defines UI acceptance behavior only. The main implementation risk is contract drift between Lane 05's final `tab_example` shape and the current Lane 06 tab normalizer, especially field names around validation, rendered tab text, intervals, and context.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-06-answer-triggered-tab-example-ux-followup.md`

## Files That Must Not Be Staged

Do not stage any unrelated parked work, including current dirty backend/API files, UI files, landing/sign assets, corpus/source files, Chroma/vector data, raw design assets, deployment files, or existing handoffs outside this exact file.

## Recommended Next Lane

Lane 05 should finish the answer-triggered `tab_example` implementation and confirm the final payload shape.

Then Lane 06 should update or verify the answer-page renderer against the final `tab_example` shape and browser-smoke at least one real normal answer containing a validated tab example.

## Commit Readiness

Safe to commit as a docs-only handoff if only this file is staged.

## Suggested Next Step

Lane 05: finish the answer-triggered deterministic tab example implementation and hand off the exact `tab_example` payload shape plus test examples to Lane 06.
