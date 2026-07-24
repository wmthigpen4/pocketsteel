# 19 Visual Design / Assets - Tab Card Visual Guidance

## 1. Visual goal

Pedal steel tab examples should feel like quiet teaching inserts inside Steel Guitar RAG answer pages: useful, readable, and clearly part of the current black/cream/brass brand, without becoming a showpiece.

The tab card should support the answer, not overtake it. Use a calm dark surface, cream text, restrained brass accents, and enough spacing to make older steel-guitar readers comfortable. Avoid neon-heavy treatments, animated flourishes, or decorative instrument imagery in this slice.

## 2. Layout recommendation

- Render tab as a compact answer sub-card after the relevant paragraph or source-backed explanation.
- Use a simple header row with a short title such as `Tab example` or the phrase name when available.
- Put optional context metadata below the title in one quiet line: tuning, key, fret area, pedals/levers, or difficulty when supplied.
- Keep the tab block as the visual anchor, then place any explanatory note below it.
- If the user did not specifically ask for tab, keep the card visually smaller than the primary answer and avoid expanding it into a dominant module.
- If the user did ask for tab, the card may use a stronger header and slightly more vertical space, but the prose answer should still introduce what the tab demonstrates.

Recommended hierarchy:

1. Small section label or card title.
2. Optional one-line musical context.
3. Monospace tab block.
4. Optional validation/status row.
5. Optional plain-language teaching note.

## 3. Typography recommendation

- Continue the answer page's warm cream text for headings and body copy.
- Use the existing UI sans-serif for card chrome, metadata, labels, and badges.
- Use a true monospace font only for the tab block, because alignment is part of the content.
- Prefer font sizes that remain readable without zooming:
  - Card title: approximately answer subheading size, not hero size.
  - Metadata and badge text: compact but not tiny.
  - Tab block: no smaller than `13px` on desktop and `12px` on mobile, with a comfortable line-height around `1.45`.
- Do not use script, neon display lettering, or ornate type inside the tab card.

## 4. Monospace tab block treatment

- Preserve tab spacing exactly. Use `white-space: pre` or equivalent behavior; do not wrap individual tab lines by default.
- Put the tab in a horizontally scrollable block when needed.
- Use a dark, low-glare code-surface treatment: near-black fill, subtle inner border, and faint brass edge.
- Keep the block background calmer than a code editor. The tab should read like a lesson handout, not a developer console.
- Use cream text with optional muted brass for string labels only if implementation can apply it without changing spacing.
- Avoid syntax highlighting that changes character widths or makes timing/fret positions harder to scan.
- Add subtle left/right scroll affordance on mobile if content overflows.

Practical style target:

- Surface: deep charcoal/black-green.
- Border: low-opacity brass or cream.
- Text: cream.
- Selection/focus outline: brass, clearly visible.
- Padding: enough that first/last characters do not kiss the border.

## 5. Validation badge treatment

Validation badges should reassure, not shout.

- Use small badges in the card header or immediately under the tab block.
- Suggested labels:
  - `Checked` for validated examples.
  - `Generated` for generated but not manually checked examples.
  - `Needs review` for examples that should be treated cautiously.
- Use calm color language:
  - `Checked`: brass border with cream text, optional low-opacity brass fill.
  - `Generated`: muted cream border with muted text.
  - `Needs review`: warm oxide/red-brown accent, not bright error red.
- Do not use pulsing, glowing, or warning-icon-heavy badges.
- If validation is not available, omit the badge rather than implying certainty.

## 6. Mobile behavior

- Keep the card full-width within the answer column.
- Let only the tab block scroll horizontally; avoid making the whole answer page wider than the viewport.
- Keep header, metadata, validation badge, and teaching note wrapping normally.
- Maintain enough tap/scroll room around the tab block so horizontal scrolling does not fight page scrolling.
- Keep card padding slightly tighter than desktop but do not compress the monospace text into illegibility.
- For long examples, consider a collapsed initial height with a clear `Show full tab` control only after Lane 06 confirms the interaction pattern. Do not invent fake animation for this slice.

## 7. Accessibility/readability

- Readability beats cleverness for this audience.
- Use high contrast between the tab text and surface.
- Do not rely on color alone for validation; the badge text must carry the meaning.
- Preserve literal tab text for screen readers and copy/paste.
- If a non-visual text summary exists, place it near the tab: for example, `Example covers strings 4, 5, and 6 at frets 3 and 5 with A+B pedals.`
- Ensure keyboard users can focus the scrollable tab block when it overflows.
- Avoid small all-caps metadata runs that become hard to read.
- Keep decorative borders and shadows subtle enough that they do not blur the tab characters.

## 8. What to avoid

- Do not create image assets for tab examples.
- Do not render tab as an image; text must remain selectable, copyable, and spacing-preserved.
- Do not add fake fretboard animation or event-by-event playback in this slice.
- Do not use neon-heavy styling, blinking accents, animated glow, or theatrical signage inside the card.
- Do not make tab cards dominate answers unless the user specifically asked for tab.
- Do not wrap tab lines in a way that breaks alignment.
- Do not use proportional fonts in the tab block.
- Do not add decorative strings, fretboards, pedal icons, or hardware imagery inside the tab block.
- Do not expose internal validation/debug labels to users.

## 9. Future event-by-event fretboard sync visual concept

Future sync can connect tab events to the SVG fretboard without changing this slice.

Concept:

- Treat each playable tab event as a calm step in a teaching sequence.
- Highlight the current tab event row or character span with a soft brass backing.
- Highlight the matching SVG fretboard position with the existing selected-position treatment.
- Show a small step label such as `Step 2 of 5` and optional controls for previous/next.
- Keep playback manual-first. Auto-play, timing animation, and audio should wait for a later product decision.
- Maintain one source of truth for coordinates. The tab event should reference structured fret/string/control data, and the SVG should still render positions from its own coordinate model.

Visual tone:

- Same dark card surface.
- One active brass highlight at a time.
- No bouncing markers, fake bar movement, or animated pedals in the first synced version.
- If reduced motion is enabled, the state should change instantly with no transition.

## 10. Handoff notes for Lane 06

- Implement this as styling/rendering guidance only; no new visual assets are needed.
- Keep current answer-page hierarchy calm: prose first, tab as a supporting card unless the user explicitly asked for tab.
- Preserve spacing exactly in the tab block.
- Make horizontal overflow local to the tab block.
- Use compact validation badges only when the backend/data contract provides validation state.
- Avoid frontend changes outside the answer-page tab rendering work already underway.
- Do not touch corpus, scraping, Chroma, embeddings, DNS, deployment, or private/source-inbox data.

Suggested Lane 06 implementation prompt:

> Implement tab card styling for answer-page tab examples using `docs/handoffs/task-completions/2026-06-18-19-tab-card-visual-guidance.md` as the visual source of truth. Keep tab examples calm, readable, spacing-preserved, and subordinate to the answer unless the user explicitly asked for tab. Modify only the answer-page tab rendering files needed for the current Lane 06 slice. Do not add image assets, fake fretboard animation, scraper/data changes, Chroma/embedding changes, DNS changes, deploy changes, staging, or commits unless separately instructed.

## Completion metadata

### Task summary

- What was requested: Create visual design guidance for rendering pedal steel tab examples inside Steel Guitar RAG answer pages.
- What was completed: Created this Lane 19 handoff with visual, layout, typography, tab block, validation badge, mobile, accessibility, avoidance, future sync, and Lane 06 handoff guidance.
- What was intentionally not changed: No UI code, image assets, frontend files, corpus data, scraping, Chroma, embeddings, DNS, deployment, staging, or commits.

### Files changed

- Changed files: None.
- Created files:
  - `docs/handoffs/task-completions/2026-06-18-19-tab-card-visual-guidance.md`
- Deleted files: None.
- Generated artifacts: None.

### Tests and checks

- Exact commands run:
  - `git status --short`
  - `sed -n '1,220p' docs/process/codex-completion-protocol.md`
  - `test -f docs/fretboard-visual-design-directions.md && sed -n '1,220p' docs/fretboard-visual-design-directions.md || true`
- Results: Confirmed the worktree had many unrelated dirty/untracked files before this task. Confirmed completion protocol and reused existing Steel Guitar RAG visual guidance context.
- Tests skipped and why: No automated tests were run because this is a documentation-only visual handoff.

### Integration notes

- What another lane needs to know: Lane 06 should use this file as the visual source of truth for tab-card styling during answer-page tab rendering.
- Schema/API/component/data contract changes: None.
- Assumptions: Validation badges are optional and should only appear if the tab rendering slice has trustworthy validation state available.
- Blockers: None.
- Human decisions needed: No for this guidance task.

### Risk assessment

- Low.
- Why: Documentation-only guidance, with no runtime or asset changes.
- Rollback notes, if relevant: Remove this file if the guidance should be discarded.

### Commit readiness

Needs human review first

### Suggested next step

- Which active lane should act next: 06 UX/UI Design.
- Exact recommended task/prompt for that lane: Use the suggested Lane 06 implementation prompt above to style answer-page tab cards without changing assets, data, scraping, Chroma, embeddings, DNS, deployment, staging, or commits.
