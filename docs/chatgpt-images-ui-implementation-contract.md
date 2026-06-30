# ChatGPT Images To UI Implementation Contract

## Purpose

This contract defines how ChatGPT Images mockups become Codex-buildable frontend slices for The Turnaround / Steel Guitar RAG without losing the premium visual direction or drifting into untestable pixel-copy work.

The mockup is a visual brief. The implementation source of truth remains the repo:

- HTML, CSS, SVG, and JavaScript define layout, behavior, accessibility, and responsive states.
- Existing UI contracts define musical rendering behavior.
- The SVG fretboard/grid remains the source of truth for strings, frets, hit targets, and musical geometry.
- Decorative images may support mood, but must not encode fret/string positions or functional UI state.

## Inputs Required For A Visual UI Slice

Each mockup implementation task should provide:

- Target route or component, for example `ui/e9-fretboard-explorer.html` or `ui/steel-guitar-rag-landing.html`.
- One or more mockup images, with the preferred desktop reference identified.
- The primary user job for the screen.
- Required content and actions.
- Explicit non-goals, such as no backend changes, no asset changes, or no new routing.
- Expected smoke target: local route, protected-preview route, or both.
- Whether the slice should preserve current copy exactly or may revise product copy.

If the mockup conflicts with existing musical behavior, source/auth rules, or fretboard geometry, the repo contract wins and the handoff must call out the visual compromise.

## Mockup Interpretation Workflow

Before coding, the Lane 06 implementer should convert the mockup into a short implementation spec:

1. Identify the page hierarchy.
   - Primary object on the screen.
   - Secondary support panels.
   - Primary CTA or interaction.
   - Content that should be visible above the fold.

2. Extract visual intent.
   - Mood: premium, teaching diagram, backstage, dense workbench, quiet utility, etc.
   - Density: sparse landing hero, compact app surface, card grid, inspector layout.
   - Material language: brass trim, dark stage, paper lesson, metal panel, SVG diagram.
   - What must feel similar versus what can adapt to implementation constraints.

3. Convert the image into implementation tokens.
   - Background roles.
   - Surface roles.
   - Text roles.
   - Border roles.
   - Accent roles.
   - Focus and selected-state roles.
   - Spacing, radius, shadow, and layout constraints.

4. Inventory components.
   - Header/navigation.
   - Primary stage or hero.
   - Controls/toolbars.
   - Cards/lists.
   - Detail/inspector panels.
   - SVG/fretboard/chart elements.
   - Empty, loading, disabled, and selected states.

5. Inventory assets.
   - Which raster assets are required.
   - Which visual elements should be recreated in CSS/SVG.
   - Which existing assets can be reused.
   - Which asset paths are in scope and which are protected.

6. Define responsive behavior before editing.
   - Desktop layout.
   - Tablet layout.
   - Mobile/narrow layout.
   - Horizontal scroll behavior for fixed-format tools such as fretboards.
   - What remains visible without scrolling.

7. Define smoke assertions.
   - Viewports to test.
   - Interactions to click.
   - Screenshot regions to capture.
   - Manual comparison criteria against the mockup.

## Design Tokens

Use CSS custom properties for repeated visual decisions. Scope tokens to the page or component unless the same token has already become a shared app primitive.

Recommended token groups:

- `--bg-*`: page and stage backgrounds.
- `--surface-*`: panels, cards, controls, and inspectors.
- `--text-*`: primary, secondary, muted, inverse, and disabled text.
- `--line-*`: borders, dividers, hairlines, and grid lines.
- `--accent-*`: brand gold/amber and secondary mode colors.
- `--state-*`: selected, hover, focus, warning, success, and danger.
- `--shadow-*`: panel depth and glow.
- `--radius-*`: control, card, and panel radii.
- `--space-*`: recurring spacing steps.

Token rules:

- Prefer existing page tokens when they already match the direction.
- Do not create a broad global design system in a feature slice unless explicitly requested.
- Avoid one-note palettes. Premium should come from hierarchy, contrast, material, and restraint, not a single color wash.
- Use stable dimensions for fixed-format UI such as fretboards, charts, mode tabs, and toolbars.
- Do not scale font size with viewport width.
- Text must not overlap, clip, or overflow its parent at the tested breakpoints.

## Assets: Export Versus Recreate

Export a raster asset directly when it is the subject or material of the mockup:

- Real or generated steel guitar photography.
- Brand sign video or fallback image.
- Stage/background photography or texture that carries the visual identity.
- Complex atmospheric illustration that is not a data layer.
- Transparent foreground object that would be costly and fragile to rebuild in CSS.

Recreate in HTML/CSS/SVG when the element is functional or semantic:

- Text, headings, buttons, links, form fields, and badges.
- Cards, panels, borders, shadows, and layout grids.
- Icons when a repo-approved icon set or simple accessible text control exists.
- Fretboard geometry, string rows, fret lines, notes, intervals, markers, and hit targets.
- Copedent charts, source cards, answer sections, tab cards, and inspectors.
- Any element that needs dynamic data, accessibility text, keyboard focus, or responsive reflow.

Asset handling rules:

- Do not edit `ui/brand/`, `public/`, `Neon Sign/`, deployment assets, or raw design assets unless the task explicitly names those paths and the lane permits it.
- New assets require provenance, intended route, fallback behavior, dimensions, compression choice, and cache-busting plan.
- Do not bake user-facing copy into an image unless it is a decorative brand mark with accessible fallback text.
- Keep decorative images `aria-hidden` unless the image itself communicates required content.
- For fretboard work, a guitar image is decorative only. The SVG/grid coordinate model owns all playable positions.

## Implementation Chunking

Codex should implement mockup-driven UI in small, reviewable chunks:

1. Shell and token pass.
   - Establish page background, container width, type scale, core tokens, and main regions.

2. Primary stage.
   - Build the hero, fretboard stage, answer area, or main workbench anchor.

3. Controls and interaction states.
   - Add tabs, segmented controls, selectors, buttons, disabled states, selected states, and focus behavior.

4. Cards and inspectors.
   - Place repeated items, source/detail panels, result cards, and explanatory copy.

5. Asset integration.
   - Add approved raster/video assets with fallbacks and load behavior.

6. Responsive pass.
   - Verify desktop, tablet, and mobile structure.

7. Test and smoke pass.
   - Run syntax/unit/static tests.
   - Run browser screenshot smoke.
   - Compare screenshots against the mockup and report differences.

Each chunk should preserve existing behavior unless the user explicitly requests behavior changes. Do not mix broad UI redesign, backend routing, auth/deployment, and asset creation in one commit.

## Responsive Contract

Every mockup-derived slice must define and test:

- Desktop viewport around `1440 x 900` or the reference mockup size.
- Medium/tablet viewport around `1024 x 768` when the layout has columns or side panels.
- Narrow/mobile viewport around `390 x 844` or `430 x 932`.
- No page-level horizontal overflow except intentional internal scrollers for wide diagrams.
- Header controls remain readable and separated.
- Primary action remains reachable.
- Fretboards/charts keep stable aspect and do not resize based on dynamic labels.
- Cards and buttons do not change size unexpectedly when selected, hovered, or populated.
- Long words, roots, control labels, and badge strings wrap or compress cleanly.

For SVG fretboards and charts:

- Geometry stays mathematically defined in SVG or data-driven layout.
- Decorative underlays cannot define coordinates.
- Labels must be legible on mobile or hidden behind an explicit detail/legend pattern.
- Highlight color must be paired with shape, text, or detail state.

## Browser Screenshot Smoke

UI-facing mockup implementation is not complete without visual smoke.

Minimum local smoke:

- Use a direct cache-busted route, for example `http://127.0.0.1:<port>/ui/<page>.html?v=<slice-local>`.
- Capture desktop screenshot.
- Capture mobile/narrow screenshot.
- Capture cropped screenshot for the changed region when the change is local.
- Record console errors and relevant warnings.
- Verify no `[object Object]`, raw internal branch labels, or stale cache/version strings appear.

Protected-preview smoke is required after committed user-facing runtime/static UI changes when the slice is meant for protected preview:

- Use a direct cache-busted protected URL.
- Record Cloudflare Access login result.
- Record expected HEAD and `/api/version` result when available.
- State clearly when static UI was verified but runtime HEAD differs.
- API fallback does not count as browser smoke.

Required visual checks:

- The primary screen hierarchy matches the mockup intent.
- The key visual object is visible in the first viewport.
- Text is readable and not overlapping.
- Assets load and fallback states work.
- Controls show selected, hover/focus, disabled, and default states where relevant.
- The layout does not become card-inside-card clutter.
- Source cards, fretboards, tab cards, and prompt chips do not visually overpower the primary answer unless the task intends that.
- For Explorer/fretboard pages, selected row/card/detail state and SVG state agree.

## Manual User Comparison

The user should compare screenshots against the mockup for:

- Overall premium feel.
- Correct first impression and hierarchy.
- Whether the product object is prominent enough.
- Whether the page feels like the same design direction, not merely the same content.
- Whether spacing and scale feel intentional.
- Whether the UI is easier to understand than the previous version.
- Whether any important mockup element was omitted.
- Whether the mobile version preserves the same intent without overcrowding.

Pixel-perfect matching is not the default goal. If pixel-perfect matching is required, the task must say so and provide exact dimensions, fonts, assets, and acceptable deviation.

## Acceptance Criteria

A mockup-to-UI slice is acceptable when:

- The implementation spec identifies what was exported as assets versus recreated in code.
- The changed files are scoped to the approved UI/test/docs paths.
- Existing data contracts and protected paths are preserved.
- The mockup's hierarchy, mood, and primary user job are visible in the built UI.
- Desktop and mobile screenshots are captured and compared to the reference.
- Tests appropriate to the touched files pass.
- `git diff --check` passes.
- The handoff lists exact safe-to-stage files and unrelated files that must remain unstaged.
- Any visual compromises are recorded as warnings, not hidden.

## Recommended Lane 06 Prompt Template

```text
Lane 06 UX/UI Design

Use docs/chatgpt-images-ui-implementation-contract.md and the attached mockup(s) to implement a scoped UI slice for <target route/component>.

Before coding:
- Inspect AGENTS.md, integration-status.md, the target UI file(s), relevant tests, and the latest related handoff.
- Convert the mockup into a short implementation spec: hierarchy, tokens, components, asset decisions, responsive behavior, acceptance criteria.
- Do not touch backend, auth, deployment, corpus, Chroma/vector stores, scraping, embeddings, private materials, or unrelated assets.

Implement only:
- <exact target files or UI area>

Run:
- syntax checks for touched JS
- focused frontend/static tests
- git diff --check
- local browser screenshot smoke at desktop and mobile viewports

If committed and preview-bound, route to Lane 12 for protected-preview browser smoke with a direct cache-busted URL.

Write a handoff under docs/handoffs/task-completions/ with screenshot paths, visual comparison notes, safe-to-stage files, risks, and recommended next lane.
```

## Recommended Lane 19 Prompt Template

Use Lane 19 only when the slice requires new or edited visual assets.

```text
Lane 19 Visual Design / Assets

Create or prepare the approved raster/video assets for <target UI slice> using docs/chatgpt-images-ui-implementation-contract.md.

Deliver only asset files and an asset handoff. Include provenance, dimensions, compression choice, fallback image, intended route, and exact paths. Do not edit UI implementation, backend, auth, deployment, corpus, Chroma/vector stores, scraping, embeddings, or private materials.
```
