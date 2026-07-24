# 2026-06-29 22:18 - Lane 18 Enhanced Fretboard Learning Audit

## Pass / Warn / Fail

Warn.

The audit and implementation-ready product/UX contract are complete. The repo has substantial unrelated dirty and untracked work that predates this task, so this handoff must be staged by exact path only if it is committed later.

## Task Summary

Requested:
- Audit what has already been built that could support an enhanced fretboard learning experience.
- Do not assume "Pocket Explorer" is the right product name or shape.
- Define the smallest valuable next shippable UI/UX-driven fretboard slice.
- Do not implement runtime UI or backend behavior in this audit slice.

Completed:
- Inspected repo guidance, integration status, existing docs, backend fretboard/tab/copedent files, frontend fretboard/answer/Explorer files, and focused tests.
- Produced a concise product/UX audit and implementation-ready contract in this handoff.
- Recommended a next frontend-first slice: **Enhanced Fretboard Learning Card v1**.

Intentionally not changed:
- No runtime UI files.
- No backend behavior.
- No tests.
- No corpus, scraping, embeddings, Chroma/vector stores, auth, DNS, deployment, private transcripts, licensing metadata, secrets, or assets.
- No integration-status refresh because this audit did not change committed integration state or runtime behavior.

## Repo State

- Branch: `feature/answer-api`
- Starting HEAD: `697435e`
- Final HEAD: `697435e`
- Commit hash: not committed
- Task type: docs-only product/UX audit
- Lane: `18 Product / Architecture`
- Task mode: GREEN

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-29-2218-18-enhanced-fretboard-learning-audit.md`

Changed:
- None

Deleted:
- None

Generated artifacts:
- None

## Current Built Surface

### Backend Fretboard Payloads And Rules

`steel_guitar_rag/fretboard_examples.py` already contains the core answer-card fretboard engine:

- `FretboardPosition` with stable ids, root/quality, position kind, fret, strings, grip, pedals/levers, family, tier, notes, intervals, voicing metadata, caveats, and teaching copy.
- `to_position_payload()` emits rich payload fields including `chordTones`, `lowestSoundingNote`, `lowestChordToneRole`, `voicingType`, `inversionLabel`, `intervalsLowToHigh`, `isRootPosition`, `isInversion`, `isPartialVoicing`, `whyUseIt`, `whenToUse`, `soundCharacter`, `movementUse`, `resolutionUse`, `explanationShort`, and `explanationLong`.
- `validate_fretboard_payload()` enforces E9, 10 strings, frets 0-24, canonical pedal/lever labels, stable ids, no raw geometry, notes/interval maps, and pitch-validation metadata.
- `fretboard_payload_for_question()` routes deterministic chord/grip/function prompts to static fretboard payloads before answer display.

Measured payload examples from current code:

| Payload | Current support |
| --- | --- |
| G major positions | 44 positions, 3 visible by default |
| A major positions | 49 positions, 3 visible by default |
| B major positions | 44 positions, 3 visible by default, including lower-octave A+B alternate |
| C# major positions | 44 positions, 3 visible by default |
| G minor positions | 20 positions |
| I-IV-V in G | 3 static positions |
| 5-7-8 with E-lower at fret 3 | 1 diagnostic position |

Important conclusion: the backend already has enough position metadata for a beginner-friendly enhanced answer-card UI. A new backend contract is not required for the next v1 UI slice.

### Static Grip And Movement Support

`steel_guitar_rag/answer_tab_examples.py` already distinguishes static fretboard answers from movement/tab answers:

- `static_fretboard_payload_for_question()` supports static grip prompts such as `Show me a G major grip.` and `Show me a 4-5-6 grip.`
- Static grips return fretboard payloads without tab payloads.
- `tab_example_payload_for_question()` supports safe deterministic movement prompts.
- `fretboard_payload_for_tab_example()` derives fretboard positions from the same validated tab events.
- Parameterized major movement support exists for I-IV, I-V, and I-IV-V-I examples in major keys.
- Movement payloads label provenance as deterministic/original educational examples, not SGF-derived tab or public-domain song arrangements.

Measured examples:

| Prompt | Current behavior |
| --- | --- |
| `Show me a G major grip.` | Static fretboard only, 1 position |
| `Show me a 4-5-6 grip.` | Static fretboard only, 1 position |
| `How do I move from the I chord to the IV chord on E9?` | Tab payload with 2 events and matching fretboard payload |
| `How do I play a 1-4-5-1 in G?` | Tab payload with 4 events and matching fretboard payload |

### Tab Events

`steel_guitar_rag/tab_engine.py` already provides:

- `TabNote`, `TabEvent`, `TabValidationIssue`, and `TabRenderResult`.
- String-aware pedal/lever validation.
- Fixed-width tab rendering.
- Chord and lyric alignment.
- `/api/tab/render` test coverage.

This is sufficient for movement cards later. It should not be pulled into static chord/grip answer cards except when the question is explicitly about movement, licks, fills, transitions, or practice examples over time.

### Copedent And Control Data

`steel_guitar_rag/e9_copedents.py` already provides:

- Emmons E9, Day E9, Custom E9 with LKV, and disabled My Copedent profile concepts.
- 10-string open notes and pitch values.
- Stable control ids, display labels, physical positions, changes, affected strings, raise/lower direction, and string-action descriptions.
- Chart-ready selected copedent payloads and pedal/lever impact metadata.

This supports future control-aware teaching copy, but the next answer-card slice should avoid adding a full copedent selector inside answer cards.

### Explorer Backend

`steel_guitar_rag/fretboard_explorer.py` already supports a much broader deterministic Explorer surface:

- `build_explorer_payload("G")` currently emits 150 positions.
- Payload includes `type`, `version`, `instrument`, `query`, `positions`, `legend`, `filters`, `grip_vocabulary`, `selected_copedent`, `copedent_profile`, and `control_impact_preview`.
- Positions include chord names, chord function, display notes, intervals, inversion, per-string changes, warnings, pitch validation, source guidance refs, and control impacts.
- Grip vocabulary includes core, path, extended, song/tab vocabulary, E-lower pockets, and two-string vocabulary.
- Control impact preview is already chart/panel-ready.

This argues against inventing a separate "Pocket Explorer" architecture right now. The Explorer exists. The next product work should decide how answer-card learning borrows a small amount of Explorer clarity without embedding the full workbench in answers.

### Frontend Answer Fretboard Renderer

`ui/answer-client.js` already:

- Finds `fretboard` payloads in top-level answer responses and tab-example nested shapes.
- Normalizes `positions`, `highlights`, `title`, `description`, `legend`, `query`, `maxFret`, `stringCount`, and tuning labels.
- Finds and normalizes tab examples separately.

`ui/pedal-steel-fretboard.js` already:

- Owns SVG fret/string geometry and keeps the decorative fretboard image as underlay only.
- Renders 10 strings, 24 frets, markers, labels, highlights, selector cards, selected detail, legend, filters, and show-all behavior.
- Supports positions over legacy highlights.
- Supports recommended-position limiting.
- Supports filters for voicing, grip, and pedal/lever combinations.
- Renders notes, intervals, top voice, string changes, warnings, when-to-use copy, short explanation, technical details, omitted intervals, movement use, resolution use, sound character, and caveats.
- Guards against `[object Object]`.

Current answer-card renderer already contains the raw ingredients of an enhanced learning card. The missing piece is not data. It is hierarchy.

### Explorer Frontend

`ui/e9-fretboard-explorer.html`, `ui/e9-fretboard-explorer.js`, `ui/e9-fretboard-explorer-data.js`, and `ui/e9-music-rules.js` already imply or implement:

- visible top-level modes
- Single Grip
- Harmonized Scale Path
- Single-Note Finder
- Voicing Identifier
- Chord / Voicing Finder
- copedent selector/chart
- pedal/lever impact preview
- note workflows including drill and deterministic event sync demo
- active result cards
- right-side "Why this works" inspector
- map/result filters
- chord finder candidate details
- path rail cards
- mode-specific marker rendering

The Explorer is already the advanced/focused workspace. The next answer-card slice should not duplicate it.

## UX Concepts Already Implied

| Concept | Evidence in repo | Current state |
| --- | --- | --- |
| Chord-tone labels | `notes`, `intervals`, `chordTones`, `intervalsLowToHigh`, `lowestChordToneRole` | Data exists; answer-card UI renders in detail but not as a beginner-first visual row |
| Inversions | `voicingType`, `inversionLabel`, `isRootPosition`, `isInversion` | Data and filters exist |
| Grip explanation | `grip`, `tierReason`, `whenToUse`, `soundCharacter`, Explorer grip vocabulary explanations | Exists, but split across detail/technical surfaces |
| Nearby options | `movementUse`, `resolutionUse`, curated answer prose, I-IV-V static payloads | Implied, not a first-class answer-card UI |
| Movement cards | `tab_engine`, `answer_tab_examples`, parameterized movement events | Exists for tab examples; should stay tab-driven |
| Event sync | Explorer note workflow demo and tab-event-derived fretboard payloads | Exists in limited Explorer/demo form |
| Filters | voicing/grip/pedal-lever filters in shared fretboard; Explorer filters | Exists |
| Prompt chips | answer UI and landing surfaces have prompt-chip patterns | Exists but not a core requirement for next card |
| Card layouts | answer-card fretboard selectors, Explorer active results, right inspector | Exists |

## Missing For A Beginner-Friendly Enhanced Fretboard Card

The current shared answer-card fretboard is musically rich but still reads like a position catalog. Beginner gaps:

- The first selected position does not present an obvious "play this first" command.
- Notes and intervals exist, but they are not displayed as a chord-tone row that teaches root/3rd/5th at a glance.
- The three default positions are visible, but their relationship is not summarized as "same chord, three families."
- "Why this works" exists as copy fields, but it is visually buried among many detail fields.
- The user can filter, but the default card does not clearly separate beginner defaults from hidden advanced positions.
- Movement/nearby language exists, but answer cards do not yet frame it as "next step" or "practice this."
- Mobile can render, but dense details can overwhelm before the player understands the primary action.

## Recommendation

Ship **Enhanced Fretboard Learning Card v1**.

Do not name this "Pocket Explorer" yet. The Explorer is already the full workbench. This slice should improve the embedded answer-card fretboard by making deterministic answer payloads teachable at first glance.

### Why This Slice

- Highest value from existing code: it uses current payload fields and renderer.
- No backend contract change is required for v1.
- It improves the most common user path: chord/grip answer results.
- It keeps static positions fretboard-first and movement tab-first.
- It can be verified with focused frontend tests and browser screenshots.
- It does not broaden into a new product surface or architecture.

## Implementation-Ready Contract: Enhanced Fretboard Learning Card v1

### User Value

When a user asks a static chord or grip question, the answer-card fretboard should immediately teach:

- where to start,
- what to play physically,
- what chord tones are under the bar,
- why that position works,
- how the other visible positions compare,
- what to practice for one minute.

### Non-Goals

- Do not create a new Pocket Explorer product surface.
- Do not change backend routing.
- Do not add new chord generation.
- Do not add new tab generation.
- Do not add public-domain song arrangements.
- Do not add arbitrary melody-to-tab.
- Do not change copedent profiles.
- Do not expose SGF snippets inside deterministic fretboard cards.
- Do not move movement/lick/event sequencing into static chord cards.
- Do not touch assets or fretboard geometry.

### UI Layout Requirements

Within `ui/pedal-steel-fretboard.js`, add a beginner-first selected-position learning area using existing position fields.

Recommended visible hierarchy:

1. Selected position header:
   - label, fret, grip, pedals/levers
   - clear "Start here" or "Selected position" label for the first visible default

2. Chord-tone row:
   - per-string chips showing `String 4: G / 1`, `String 5: D / 5`, etc.
   - Use existing `notes` and `intervals`.
   - Fall back to notes-only or intervals-only when one is missing.

3. Why this works:
   - Use `explanationShort`, `whenToUse`, or `soundCharacter`.
   - Keep it to one compact line or short paragraph.

4. Compare starter positions:
   - Show only `visibleByDefault` positions by default.
   - For major position answers, this normally means open/no-pedals, A+F, and A+B.
   - Display compact rows: fret, controls, grip, voicing/inversion.
   - Selecting a row should use the existing selector/detail behavior.

5. Practice prompt:
   - Use `movementUse`, `resolutionUse`, or deterministic fallback copy such as "Play the selected grip once, block, then compare the other starter positions."
   - This is practice guidance, not a tab sequence.

Keep the existing technical details section, but make it secondary.

### Data / Payload Requirements

No required backend change for v1.

Use existing fields:

- `positions[].id`
- `positions[].label`
- `positions[].fret`
- `positions[].strings`
- `positions[].grip`
- `positions[].pedals`
- `positions[].levers`
- `positions[].notes`
- `positions[].intervals`
- `positions[].chordTones`
- `positions[].voicingType`
- `positions[].inversionLabel`
- `positions[].visibleByDefault`
- `positions[].sortOrder`
- `positions[].whenToUse`
- `positions[].soundCharacter`
- `positions[].movementUse`
- `positions[].resolutionUse`
- `positions[].explanationShort`
- `positions[].caveats`

Fallback behavior:

- If `notes` and `intervals` are both missing, omit the chord-tone row.
- If only notes exist, show note chips.
- If only intervals exist, show interval chips.
- If `visibleByDefault` is absent, keep the current renderer behavior.
- If fewer than two starter positions exist, omit compare rows.
- If practice fields are missing, use a generic deterministic practice prompt.

Optional future backend additions, not needed for v1:

- `fretboard.presentation.defaultDetailMode`
- `fretboard.presentation.learningCard`
- `positions[].practicePrompt`
- `positions[].relatedPositionIds`
- `positions[].nextMoveIds`

### Component States

Required states:

- Recommended default state with first visible position selected.
- Selected alternate starter position.
- `All positions` expanded state.
- Grip-filtered state.
- Pedal/lever-filtered state.
- No-match filter state.
- Single-position static grip state.
- Missing notes/interval fallback state.
- Advanced/rootless/partial position selected state.

### Mobile Behavior

- Keep the SVG as an internal horizontal scroller.
- Place learning summary below the SVG and above technical details.
- Show the chord-tone row as wrapping chips.
- Compare starter positions should become a horizontal row or stacked compact list.
- Do not show more than one dense technical section before the beginner learning summary.
- No page-level horizontal overflow.
- No text overlap inside chips/buttons/cards.

### Source / Copyright Constraints

- Deterministic chord/grip cards must be labeled as deterministic E9 rules or app rules data when provenance is shown.
- Do not imply SGF supports exact generated positions unless source-backed evidence is explicitly attached.
- Do not quote SGF fragments in the learning card.
- Movement/lick/fill examples must remain deterministic/original educational examples unless a future public-domain/source-backed arrangement contract is implemented.
- No full copyrighted song tab, lyrics, or note-for-note solo output.

### Expected Test Prompts

Static answer-card prompts:

- `Where can I play a G chord?`
- `Where all can I play a B chord?`
- `How do I play a G-minor chord?`
- `Show me a G major grip.`
- `Show me a 4-5-6 grip.`
- `What does 5-7-8 with E lowered give me at the 3rd fret?`

Movement prompts should remain tab-driven:

- `How do I move from the I chord to the IV chord on E9?`
- `How do I play a 1-4-5-1 in G?`

Unsupported/non-static checks:

- `Tab the whole solo from Together Again.`
- `Use my custom copedent for a I-IV move.`

### Local Browser Smoke Expectations

Smoke the answer UI with a local cache-busted direct URL:

```text
http://127.0.0.1:<port>/ui/steel-guitar-rag-mock.html?v=enhanced-fretboard-learning-card-local
```

Required visual checks:

- Deterministic chord answer renders a fretboard card.
- The selected position learning summary appears without opening technical details.
- Chord-tone chips show strings, notes, and intervals when available.
- Starter-position compare rows show open/no-pedals, A+F, and A+B for a major-position answer.
- Selecting another starter position updates SVG selected marker and learning summary.
- `All positions` still reveals hidden alternates without overwhelming the default state.
- Static grip prompt does not render a tab card.
- Movement prompt still renders tab plus fretboard, not the static learning-card-only path.
- Mobile screenshot has no page-level horizontal overflow.
- No `[object Object]`.
- No raw internal ids, source fragments, or SGF quote dumps in the learning card.

Screenshot evidence:

- desktop full viewport for `Where can I play a G chord?`
- desktop crop of selected learning summary
- mobile full viewport for `Where can I play a G chord?`
- desktop movement prompt verifying tab remains the movement surface

### Protected-Preview Smoke Expectations

After a committed UI slice:

- Use a direct cache-busted protected URL:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=enhanced-fretboard-learning-card-<commit>
```

Record:

- Cloudflare Access result.
- Expected HEAD.
- `/api/version` result when available.
- Whether runtime HEAD contains the UI commit or whether this is static/browser proof only.
- Root behavior caveat, if root redirects and drops query strings.
- Screenshot paths or explicit screenshot capture failure.
- API fallback status must be `not used` or `API fallback, not browser smoke`.

### Exact Files Likely To Be Touched

Likely Lane 06 implementation files:

- `ui/pedal-steel-fretboard.js`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_frontend_answer_ui.py` if answer-page integration assertions need to change
- `docs/handoffs/task-completions/<timestamp>-06-enhanced-fretboard-learning-card.md`

Possibly touched only if needed:

- `ui/answer-client.js` if the implementation needs top-level `fretboard.notes`, `fretboard.warnings`, or `selectedPositionId` passed through. Avoid this for v1 if possible.

Not expected for v1:

- `steel_guitar_rag/fretboard_examples.py`
- `steel_guitar_rag/answer_tab_examples.py`
- `steel_guitar_rag/fretboard_explorer.py`
- backend API files
- Explorer workbench files
- assets

## Backend Contract Changes Required

None for v1.

Backend follow-up only if Lane 06 discovers missing data in real answer payloads:

- Add `practicePrompt` or `learningSummary` as optional fields.
- Add `relatedPositionIds` only when a true nearby-options UI is planned.
- Add `presentation` metadata only if the same payload needs multiple display modes.

## Frontend Component Changes Required

Implement inside `ui/pedal-steel-fretboard.js`:

- A helper that builds chord-tone chips from `highlight.notes` and `highlight.intervals`.
- A helper that selects starter compare rows from visible/default positions.
- A compact learning-summary section in `renderPositionDetail()`.
- CSS for chord-tone chips and starter comparison rows.
- Fallback rendering for missing notes/intervals.
- Tests proving object values still do not render as `[object Object]`.

Keep current filters, selector cards, SVG geometry, legend, recommended cap, and technical details behavior.

## Risks / Blockers

Risks:

- UI density: the current answer-card detail already has many fields. The slice must improve hierarchy, not add another dense block.
- Mobile readability: chord-tone chips and compare rows need screenshot proof.
- Scope creep: do not pull in Explorer mode controls, copedent chart, or tab event sync.
- Terminology: do not introduce a product name before the UX shape is proven.

Blockers:

- None for a frontend-only v1 slice.

## Recommended Next Implementation Prompt

```text
Lane 06 UX/UI Design

Implement Enhanced Fretboard Learning Card v1 using docs/handoffs/task-completions/2026-06-29-2218-18-enhanced-fretboard-learning-audit.md.

Goal:
Make embedded deterministic fretboard answer cards teach at first glance without changing backend behavior.

Scope:
- Modify only ui/pedal-steel-fretboard.js and focused frontend tests unless inspection proves ui/answer-client.js needs pass-through.
- Use existing position payload fields: notes, intervals, chordTones, voicing/inversion metadata, visibleByDefault, whenToUse, soundCharacter, movementUse, resolutionUse, explanationShort, and caveats.
- Add a beginner-first selected-position learning summary with chord-tone chips, why-this-works copy, starter-position comparison rows, and one practice prompt.
- Keep static chord/grip answers fretboard-first.
- Keep movement/lick/progression prompts tab-driven.
- Do not change backend, Explorer payload generation, fretboard geometry, assets, auth, deployment, corpus, scraping, embeddings, Chroma/vector stores, private materials, or source/provenance files.

Run:
- node --check ui/pedal-steel-fretboard.js
- node --check ui/answer-client.js
- .venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py tests/test_frontend_answer_ui.py -q
- git diff --check
- local browser screenshot smoke for:
  - Where can I play a G chord?
  - Show me a G major grip.
  - How do I move from the I chord to the IV chord on E9?

Acceptance:
- Selected learning summary is visible without opening technical details.
- Chord-tone chips show strings, notes, and intervals where available.
- Major-position answers compare the three starter families.
- Static grip prompt renders no tab card.
- Movement prompt still renders tab plus fretboard.
- Desktop and mobile screenshots show no page-level horizontal overflow and no `[object Object]`.

Write a Lane 06 handoff with screenshots, checks, risks, safe-to-stage files, and protected-preview smoke recommendation.
```

## Files Inspected

- `AGENTS.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/fretboard-payload-contract.md`
- `docs/e9-fretboard-position-engine.md`
- `docs/steel-guitar-rag-fretboard-product-concept.md`
- `steel_guitar_rag/fretboard_examples.py`
- `steel_guitar_rag/fretboard_explorer.py`
- `steel_guitar_rag/e9_copedents.py`
- `steel_guitar_rag/tab_engine.py`
- `steel_guitar_rag/answer_tab_examples.py`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/api_contract.py`
- `ui/answer-client.js`
- `ui/pedal-steel-fretboard.js`
- `ui/e9-fretboard-explorer.js`
- `tests/test_fretboard_examples.py`
- `tests/test_fretboard_payload_qa.py`
- `tests/test_tab_engine.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_fretboard_explorer.py`

## Tests And Checks

Commands run before/while auditing:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -10 --oneline
git diff --name-only
git diff --cached --name-only
.venv/bin/python - <<'PY'
from steel_guitar_rag.fretboard_examples import get_fretboard_examples, fretboard_payload_for_question
from steel_guitar_rag.answer_tab_examples import tab_example_payload_for_question, static_fretboard_payload_for_question, fretboard_payload_for_tab_example
from steel_guitar_rag.fretboard_explorer import build_explorer_payload
# read-only payload inspection
PY
```

Results:

- Git inspection completed.
- Branch confirmed as `feature/answer-api`.
- HEAD confirmed as `697435e`.
- No staged files were reported at task start.
- Read-only payload inspection completed successfully after correcting the Explorer function name to `build_explorer_payload`.

Final checks run after this file was written:

```bash
git diff --check
git diff --check -- docs/handoffs/task-completions/2026-06-29-2218-18-enhanced-fretboard-learning-audit.md
git status --short -- docs/handoffs/task-completions/2026-06-29-2218-18-enhanced-fretboard-learning-audit.md
git diff --cached --name-only
git diff --cached --check
```

Results:

- `git diff --check`: passed.
- `git diff --check -- docs/handoffs/task-completions/2026-06-29-2218-18-enhanced-fretboard-learning-audit.md`: passed.
- `git status --short -- docs/handoffs/task-completions/2026-06-29-2218-18-enhanced-fretboard-learning-audit.md`: showed only this handoff as untracked.
- `git diff --cached --name-only`: no staged files.
- `git diff --cached --check`: passed; no staged diff.

Tests skipped:

- Frontend/browser tests skipped because no runtime UI changed.
- Pytest skipped except read-only import/payload inspection because this was a docs-only audit.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-29-2218-18-enhanced-fretboard-learning-audit.md`

## Files That Must Not Be Staged

Do not stage unrelated existing dirty/untracked files, including:

- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `ui/brand/steel-guitar-rag-landing-alpha.webm`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- `Neon Sign/`
- `answer_private_lessons.py`
- `config/`
- `data/`
- `deploy/landing/brand/`
- `public/brand/`
- `source-inbox/provenance.json`
- any corpus/private data, Chroma/vector stores, embeddings, generated reports, deployment/auth files, raw design assets, or unrelated handoffs/assets.

## Recommended Next Lane

Lane 06 UX/UI Design.

## Commit Readiness

Needs human review first.

Reason:
- The handoff is docs-only and isolated, but it contains product/UX recommendations.
- The user authorized docs-only audit work, but did not provide a commit message or explicitly require this audit to be committed.
- The worktree has extensive unrelated dirty/untracked files, so exact-path staging is required if committed.

## Suggested Next Step

Run the Lane 06 prompt above to implement Enhanced Fretboard Learning Card v1 as a focused frontend slice.
