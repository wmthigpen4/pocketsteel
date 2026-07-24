# 2026-07-01 19:33 - Lane 18 Fretboard Explorer Next UX Audit

## Pass / Warn / Fail

Warn.

The product/UX audit is complete and recommends a docs-backed next Lane 06 slice. The warning is not about the recommendation; it is about repo hygiene. The worktree already had substantial unrelated dirty and untracked files before this audit, so any staging or commit must use exact paths only.

## Task Summary

Requested:

- Audit the current Fretboard Explorer experience after recent RAG, Enhanced Fretboard Learning Card, Parameterized Movement Cards, and Movement Lesson Card work.
- Determine the next practical Fretboard Explorer improvement that makes the app feel more useful, premium, and beginner-friendly.
- Do not implement runtime UI or backend changes.
- Produce a focused audit/design contract handoff and commit docs-only work if safe.

Completed:

- Inspected repo governance, integration status, current Explorer UI/code, answer-page fretboard/tab UI, backend fretboard/tab contracts, tests, and recent handoffs.
- Identified the current Explorer modes and answer-page learning/movement surfaces.
- Audited where static grip answers, movement answers, tab examples, and Explorer modes are disconnected.
- Recommended one next shippable Lane 06 slice: **Explorer Handoff v1**.

Intentionally not changed:

- No runtime UI files.
- No backend behavior.
- No tests.
- No corpus, scraping, embeddings, Chroma/vector stores, auth, DNS, deployment config, private transcripts, licensing metadata, secrets, or assets.
- No broad Pocket Explorer architecture.
- No melody input, public-domain song arrangement, arbitrary tab generation, or SVG event stepping implementation.

## Repo State

- Branch: `feature/answer-api`
- Starting HEAD: `ea0f4cd`
- Final HEAD / commit hash if committed: pending at handoff creation; report final value after exact-path commit.
- Task type: docs-only product/UX audit.
- Lane: `18 Product / Architecture`.
- Task mode: GREEN for this handoff.

## Files Changed

Created:

- `docs/handoffs/task-completions/2026-07-01-1933-18-fretboard-explorer-next-ux-audit.md`

Changed:

- None.

Deleted:

- None.

Generated artifacts:

- None.

## Files Inspected

Repo guidance and status:

- `AGENTS.md`
- `docs/handoffs/task-completions/integration-status.md`
- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log --oneline -20`
- `git diff --name-only`
- `git diff --cached --name-only`

Recent handoffs:

- `docs/handoffs/task-completions/2026-06-29-2218-18-enhanced-fretboard-learning-audit.md`
- `docs/handoffs/task-completions/2026-06-29-2327-06-enhanced-fretboard-learning-card.md`
- `docs/handoffs/task-completions/2026-06-30-0520-12-enhanced-fretboard-learning-card-protected-smoke.md`
- `docs/handoffs/task-completions/2026-06-30-2057-05-parameterized-movement-cards-v1.md`
- `docs/handoffs/task-completions/2026-06-30-2217-06-movement-lesson-card-ui-v1.md`
- `docs/handoffs/task-completions/2026-06-30-2337-12-movement-lesson-cachefix-protected-smoke.md`
- `docs/handoffs/task-completions/2026-06-28-1632-06-explorer-workbench-redesign.md`
- `docs/handoffs/task-completions/2026-06-27-1110-18-fretboard-musical-product-audit.md`
- `docs/handoffs/task-completions/2026-06-24-sgf-fretboard-opportunity-analysis.md`

Frontend and tests:

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-data.js`
- `ui/e9-music-rules.js`
- `ui/pedal-steel-fretboard.js`
- `ui/answer-client.js`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_fretboard_explorer.py`
- `tests/test_tab_engine.py`

Backend contracts:

- `steel_guitar_rag/fretboard_examples.py`
- `steel_guitar_rag/fretboard_explorer.py`
- `steel_guitar_rag/answer_tab_examples.py`
- `steel_guitar_rag/tab_engine.py`

## Current Fretboard Explorer Modes

The standalone Explorer currently exposes five top-level modes as visible mode tabs, with the old `<select>` retained as an accessible/state proxy:

| Mode | Current purpose | Surface |
| --- | --- | --- |
| `Single Grip` | Jump to one playable pocket. | Top mode tab plus grip/key/copedent/filter controls. |
| `Harmonized Scale Path` | Trace diatonic movement across the neck. | Top mode tab plus scale/path/fret-range controls and path rail. |
| `Single-Note Finder` | Locate a target note and related note workflows. | Top mode tab plus note-workflow panels. |
| `Voicing Identifier` | Identify what a selected shape is. | Top mode tab plus selected shape controls and inspector. |
| `Chord / Voicing Finder` | Search practical shapes for a target chord/color. | Top mode tab plus chord finder target controls and candidate results. |

The Explorer has become a real workbench. It already includes copedent selection, copedent chart, control impact preview, notation modes, pitch-register options, string-action labels, active result cards, central fretboard stage, and a persistent "Why this works" inspector.

## Answer-Page Fretboard Improvements Now Present

Recent answer-page work has materially changed the relationship between answers and fretboard visuals:

- Static chord and grip answers are fretboard-first and do not show tab by default.
- The embedded fretboard now includes a selected-position learning summary.
- The learning summary shows chord-tone chips from existing `notes` and `intervals`.
- It shows concise "Why this works" and "Try this next" copy from deterministic payload fields and fallbacks.
- It shows starter-position comparison rows when multiple starter positions are present.
- Parameterized movement answers now use deterministic tab examples plus matching fretboard states.
- Movement Lesson Card UI explains start, resolve, controls used, event path, why it works, tab-to-fretboard relationship, and practice nudge.
- Protected-preview smoke passed for movement lesson, static grip/location, explicit `5-7-8`, and Fender Steel King source-backed/non-fretboard cases.

The answer page now teaches well in the moment. The Explorer teaches deeply out of context. The missing product layer is a clean handoff between those two surfaces.

## Current Disconnections

### Static Grip Answers

Static grip answers now provide a strong embedded learning card, but the transition to deeper exploration is generic:

- The app header links to `/ui/e9-fretboard-explorer.html`.
- The embedded fretboard card does not offer a position-specific "open this in Explorer" action.
- The Explorer has no query-state contract for opening directly to the same key, mode, grip, fret, strings, pedals, or levers.
- A beginner who sees "G major, fret 3, strings 4-5-6" has to re-enter that context manually in the Explorer.

### Movement Answers

Movement answers now correctly use tab plus fretboard, but they still stop short of exploration:

- The Movement Lesson Card says the tab and fretboard use the same event order.
- The Explorer has a Harmonized Scale Path mode, but movement answers do not link to an Explorer state.
- The Explorer does not yet accept progression/deep-link context such as `mode=path&key=G&progression=I-IV`.
- Timed event stepping belongs later. For now, the missing piece is a route from "I just learned this move" to "show me the related Explorer path."

### Tab Examples

Tab examples are deterministic and validated, but the UI surfaces are separate:

- The tab card owns event order.
- The embedded fretboard owns static event states.
- The Explorer owns broader neck exploration.
- There is no visible user path that explains which surface to use next.

### Source-Backed Non-Fretboard Answers

Source-backed gear answers now correctly clear stale tab/fretboard UI. That behavior should remain unchanged. Explorer links should appear only when the answer includes deterministic fretboard/tab state that can be represented in the Explorer.

## Explorer UX Issues Remaining

The current Explorer is powerful, but it still feels like an expert workbench before it feels like a beginner-friendly teaching entry.

Observed issues:

- Mode labels are better than raw filters, but still assume the user knows which mode matches their question.
- The first decision is "mode", while a beginner often thinks in jobs: "find a chord," "compare grips," "show what pedals do," "find this note."
- Controls are dense above and around the fretboard, especially key, copedent, grip vocabulary, scale, string group, notation, and display controls.
- The default `Single Grip` mode is logical, but it does not explain why it is the safest starting place.
- Mobile layout has improved, but the page still has a lot of controls before the user gets a direct task outcome.
- Answer-page learning and Explorer workbench use related concepts, but they do not share a visible "continue learning" flow.
- There are no prompt chips or task cards on Explorer that map to the most common user jobs.
- Deep state is not URL-addressable. QA and user smoke rely on manual interactions instead of stable links for exact Explorer states.

## Recommendation

Ship **Explorer Handoff v1** as the next Lane 06 slice.

This is a frontend-only UX bridge. It should not create a new "Pocket Explorer" product surface yet. It should make the existing Explorer feel connected to answer-page learning cards and easier to enter from common beginner jobs.

### Why This Slice

- It uses existing deterministic data and existing Explorer modes.
- It improves the product continuity problem created by recent success: answers now teach, but deeper exploration is one generic click away.
- It is smaller and safer than building a new Explorer abstraction.
- It does not require backend generation changes.
- It creates stable URL states that make QA and protected-preview smoke more precise.
- It supports both user paths: starting in the answer page and starting in the Explorer.

## Recommended Next Slice: Explorer Handoff v1

### User Value

After reading a fretboard answer, the user should be able to continue in the Explorer without rebuilding the same musical context.

Examples:

- From a static G major answer, click "Explore this position" and land on G, Single Grip, strings 4-5-6, selected near fret 3.
- From a G major answer with multiple starter positions, click "Compare in Explorer" and land on a G major chord/voicing finder or filtered single-grip view.
- From a movement answer like "G to C move," click "Explore related path" and land on G Harmonized Scale Path or a conservative path-mode state.
- From the Explorer itself, choose task-first cards such as "Find a chord," "Compare grips," "Trace a path," "Find a note," or "Identify a shape" before touching dense controls.

### Non-Goals

- Do not create a new Pocket Explorer product name or broad architecture.
- Do not add melody-to-tab.
- Do not add public-domain song arrangements.
- Do not add arbitrary tab generation.
- Do not add timed SVG event stepping.
- Do not change backend answer routing.
- Do not change tab engine validation.
- Do not add new music rules.
- Do not imply SGF support for deterministic generated examples.
- Do not show Explorer links for source-backed non-fretboard answers such as gear settings.
- Do not add C6 or non-E9 scope.

### UI Contract

#### Answer-Page Fretboard Link

Add a contextual action in the embedded fretboard learning area:

- Label: `Explore this position`
- Placement: inside the selected-position learning summary or immediately below it.
- Appears when a selected position has enough musical state: `key` or query root, `fret`, `strings`, and optional `pedals`/`levers`.
- Opens `/ui/e9-fretboard-explorer.html` with query params.
- Does not replace existing selector cards or learning summary.
- Does not appear for non-fretboard answers.

Recommended query shape:

```text
/ui/e9-fretboard-explorer.html?mode=single&key=G&grip=4-5-6&fret=3&strings=4-5-6&pedals=&levers=&source=answer
```

#### Answer-Page Compare Link

Add a secondary action only when the fretboard payload contains more than one position for the same root/quality:

- Label: `Compare in Explorer`
- Opens Chord / Voicing Finder when root/quality are known:

```text
/ui/e9-fretboard-explorer.html?mode=chord&root=G&quality=major&source=answer
```

- If root/quality are not known, omit the compare action rather than guessing.

#### Movement Lesson Link

Add a conservative movement-specific action:

- Label: `Explore related path`
- Appears only for deterministic movement examples with key/progression context.
- Opens path mode, not timed event sync:

```text
/ui/e9-fretboard-explorer.html?mode=path&key=G&progression=I-IV&source=movement-card
```

- Copy should not imply the Explorer will replay the tab event sequence.
- Do not add this link for static answers.

#### Explorer Task-First Entry

Add a compact task-first entry row above or adjacent to the existing mode tabs:

| Task card | Opens mode | Suggested copy |
| --- | --- | --- |
| Find a chord | `chord` | `Search practical positions for a chord.` |
| Compare grips | `single` | `See one playable pocket at a time.` |
| Trace a path | `path` | `Follow connected scale or progression movement.` |
| Find a note | `note` | `Locate notes and pedal changes.` |
| Identify a shape | `voicing` | `Check what a string/fret/control shape spells.` |

The existing mode tabs should remain. The task cards are a beginner entry layer, not a replacement for expert controls.

#### Explorer Query-State Handling

Explorer should read query params at startup and apply the safest matching state:

| Param | Purpose | Fallback |
| --- | --- | --- |
| `mode` | `single`, `path`, `note`, `voicing`, `chord` | `single` |
| `key` | Explorer key selector | `G` if unsupported |
| `root` | Chord finder root | derive from `key` only where safe, else `G` |
| `quality` | Chord finder quality | `major` |
| `grip` | String group filter, e.g. `4-5-6` | current default |
| `strings` | Position strings, e.g. `4-5-6` | ignored unless valid |
| `fret` | Desired selected row fret | ignored unless 0-24 |
| `pedals` | `+` or comma separated controls | ignored unless known |
| `levers` | `+` or comma separated controls | ignored unless known |
| `progression` | Path-mode context such as `I-IV` | ignored for v1 display except optional note copy |
| `source` | `answer`, `movement-card`, or `explorer` | informational only |

Invalid params must fail soft. The Explorer should render its default state rather than throwing or showing an empty page.

### Data / Backend Contract

No backend change is required for v1.

Lane 06 should derive links from existing normalized frontend data:

- `response.fretboard.positions[]`
- position `id`
- position `label`
- position `fret`
- position `strings`
- position `grip`
- position `pedals`
- position `levers`
- position `root`
- position `quality`
- `response.fretboard.query`, where present
- normalized tab `kind`, `contextData`, and `events` for movement links

Backend should not send raw x/y geometry. The Explorer and shared fretboard component remain responsible for geometry.

Future backend enhancement, not v1:

- Add an optional `explorerLink` object to fretboard payloads if frontend-derived links prove brittle.
- Add explicit `explorerIntent` to movement payloads only after URL-state behavior is stable.

### Expected Files For Lane 06

Likely touched:

- `ui/e9-fretboard-explorer.html`
- `ui/e9-fretboard-explorer.js`
- `ui/pedal-steel-fretboard.js`
- `ui/steel-guitar-rag-mock.html`
- `ui/answer-client.js` only if normalized context needed for link generation is missing.
- `tests/test_frontend_answer_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`

Possibly touched:

- `tests/test_fretboard_explorer.py` if static HTML or generated Explorer data assumptions need assertions.

Should not be touched:

- `steel_guitar_rag/fretboard_examples.py`
- `steel_guitar_rag/fretboard_explorer.py`
- `steel_guitar_rag/answer_tab_examples.py`
- `steel_guitar_rag/tab_engine.py`
- corpus/source/scraping/Chroma/auth/deployment files.

### Test Plan

Focused static checks:

```bash
node --check ui/e9-fretboard-explorer.js
node --check ui/answer-client.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
git diff --check
```

Focused assertions to add:

- Answer-page static fretboard renders `Explore this position`.
- Static G major link includes mode/key/fret/strings/grip params.
- Static non-fretboard source-backed answer renders no Explorer link.
- Movement Lesson Card renders `Explore related path` for deterministic movement examples.
- Movement link includes mode/path/key/progression/source params.
- Explorer task-first entry cards exist and map to the five current modes.
- Explorer startup applies valid `mode=chord&root=G&quality=major`.
- Explorer startup applies valid `mode=single&key=G&grip=4-5-6&fret=3`.
- Invalid query params fail soft and do not render `[object Object]`.

### Browser Smoke Prompts

Local browser smoke should use real UI interactions, not API fallback:

- `Show me a G major grip.`
  - Verify fretboard visible, learning summary visible, `Explore this position` visible, no tab.
  - Click the Explorer link.
  - Verify Explorer loads, mode is `Single Grip`, key is `G`, and the matching/nearest grip context is selected or visible.
- `Where is G on E9?`
  - Verify starter positions visible and `Compare in Explorer` visible.
  - Click compare.
  - Verify Explorer opens Chord / Voicing Finder for G major.
- `Show me a G to C move.`
  - Verify Movement Lesson Card, deterministic tab, and matching fretboard remain visible.
  - Verify `Explore related path` link exists.
  - Click it and verify Explorer opens path mode in G.
- `What are good Fender Steel King settings?`
  - Verify no stale tab/fretboard and no Explorer handoff link.

Smoke target must record the exact local URL and cache-busted protected URL. API fallback must not be reported as browser proof.

### Mobile Smoke Expectations

Viewport targets:

- 390px wide mobile.
- 768px tablet.
- Desktop at least 1280px wide.

Mobile pass criteria:

- Task-first Explorer entry cards are readable without text clipping.
- Mode/task controls wrap cleanly and do not overlap the fretboard.
- Answer-page `Explore this position` and `Compare in Explorer` actions are tappable and not buried behind horizontal fretboard scroll.
- Opening Explorer links from answer page lands at the correct state on mobile.
- No page-level incoherent overlap.
- No `[object Object]`.
- Horizontal inspection of the fretboard itself can remain if it is the existing intentional fretboard behavior, but the new task/link controls must not create extra page-level overflow.

## What Should Wait

Do not build these in the next slice:

- A new "Pocket Explorer" brand/product shell.
- Arbitrary melody-to-tab input.
- Public-domain song arrangement.
- Copyrighted song tab generation.
- Full tab-to-SVG timed event stepping.
- User copedent editor.
- Advanced progression composer.
- General movement/lick generator beyond current deterministic examples.
- Source-backed SGF lick extraction.
- Broad visual redesign.
- New backend music rules.

## Risks / Blockers

Risks:

- Query-state handling can become a hidden state machine if it tries to cover every mode fully. Keep v1 narrow and fail soft.
- `pedal-steel-fretboard.js` is shared by answer-page renderers. Link additions must not disrupt existing static/movement/stale-state behavior.
- Movement links must not imply event playback. V1 is only a path/context handoff.
- The Explorer already has dense controls. Task cards must clarify entry, not add another dense control row.
- Many unrelated dirty files exist. Exact-path staging is mandatory.

Blockers:

- None for a Lane 06 frontend-only implementation slice.
- Browser smoke is required before marking user-facing behavior ready.
- Protected-preview smoke is required after implementation commit and runtime/cache-bust update.

## Human Decision Needed

No for the recommended next implementation slice.

Human decision would be needed before:

- Renaming the Explorer to "Pocket Explorer."
- Turning deterministic movement links into timed event playback.
- Adding melody input or song arrangement.
- Adding backend-generated `explorerLink` contracts.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-07-01-1933-18-fretboard-explorer-next-ux-audit.md`

## Files That Must Not Be Staged

Do not stage unrelated parked work, including:

- `README.md`
- `corpus_metadata/**`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- unrelated untracked handoffs/assets
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/**`
- `ui/brand/**`
- `public/brand/**`
- `Neon Sign/**`
- private/corpus/generated/source data
- Chroma/vector stores, embeddings, scraping outputs, auth/DNS/deployment files, and secrets.

## Recommended Next Lane

Lane 06 UX/UI Design.

## Commit Readiness

Safe to commit if `git diff --check`, exact-path staged diff review, and `git diff --cached --check` pass.

## Suggested Next Step

Lane 06 implementation prompt:

```text
Lane 06 UX/UI Design
Reasoning level: High

Use AGENTS.md autopilot mode.

Implement Explorer Handoff v1 from:
docs/handoffs/task-completions/2026-07-01-1933-18-fretboard-explorer-next-ux-audit.md

Goal:
Create a frontend-only bridge between answer-page fretboard/movement cards and the existing E9 Fretboard Explorer.

Scope:
- Add contextual "Explore this position" and "Compare in Explorer" links for deterministic answer-page fretboard cards.
- Add "Explore related path" for deterministic movement lesson cards only.
- Add safe Explorer query-param startup handling for the narrow v1 params in the handoff.
- Add compact task-first Explorer entry cards that map to the existing five modes.
- Keep all behavior frontend-only unless inspection proves a missing normalized field requires a tiny answer-client normalization fix.

Do not:
- Change backend answer routing or music rules.
- Add new tab generation.
- Add melody/song/public-domain/copyrighted tab features.
- Rename to Pocket Explorer.
- Touch corpus, scraping, embeddings, Chroma/vector stores, auth, DNS, deployment config, private data, licensing metadata, secrets, or assets.

Required checks:
- node --check ui/e9-fretboard-explorer.js
- node --check ui/answer-client.js
- node --check ui/pedal-steel-fretboard.js
- .venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
- .venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
- .venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
- git diff --check

Browser smoke:
- Local browser smoke, not API fallback, for:
  - Show me a G major grip.
  - Where is G on E9?
  - Show me a G to C move.
  - What are good Fender Steel King settings?
- Verify answer-page links, Explorer query-state landing, no stale non-fretboard links, mobile layout, and no [object Object].
```
