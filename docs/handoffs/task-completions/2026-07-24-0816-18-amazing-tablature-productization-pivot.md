# Lane 18 — Amazing Tablature productization pivot

## Task summary

The user explicitly ended further Amazing Tablature training, supervised
review, tuning, and sealed-test work. Lane 18 stopped the ground-truth loop
and audited the current product code to define a bounded site-wide
productization program.

The current engine already supports mechanically validated single notes,
dyads, triads, mixed texture, alternate positions, bar slides, pedal glides,
lever glides, synchronized tablature/fretboard events, and saved-copedent
retargeting. The primary gap is that these capabilities are exposed through
separate product paths with inconsistent controls and explanations.

No product/runtime implementation was made in this planning task.

Before the pivot, the two newly submitted private review receipts were
verified and applied fail-closed:

- focused licks: 8 newly accepted score systems, 4 unresolved systems, 13
  total locked accepted score systems after carry-forward;
- current main packet: 8 feedback lines retained as unresolved, with no false
  approval;
- official sealed-test run count remained zero.

The unresolved private review work is now parked. It will not generate another
review packet unless the user explicitly reopens training in a future program.

## Current capability assessment

### Already implemented

- Normalized note, interval, literal-position, chord, duration, and phrase
  inputs.
- Candidate enumeration for one-, two-, and three-note E9 solutions.
- Exact melody pitch/register as the top voice.
- Chord-aware harmony filtering and ranking.
- Saved-copedent retargeting.
- Hard pitch and mechanical validation.
- Mixed-texture route planning.
- Exact alternate positions for a selected event.
- Bar-slide, pedal-glide, and lever-glide transitions.
- Attack, sustain, release, repick, and add-voice choreography.
- Synchronized score, tablature, and fretboard event payloads.
- A private learned mixed-route ranker with deterministic fallback and
  comparison.

### Not yet unified

- Melody Studio, Q&A melody responses, Fretboard Explorer paths, song
  practice, progression guidance, static tab examples, and the low-level tab
  renderer do not all consume one arrangement contract.
- Texture choice is split across arrangement-route names and style names.
- Technique intent is not a first-class user request.
- Style labels do not consistently disclose whether their ranking is learned
  or deterministic.
- Identical style outputs can still be presented as if they were meaningfully
  different.
- The Fretboard Explorer does not yet offer the same Amazing Tablature route
  generation available to Melody Studio.

## Productization contract

Create one shared, versioned arrangement service used by every interactive
fretboard/tab surface.

### Arrangement request

- Ordered normalized musical events:
  - scientific pitch or scale degree;
  - duration and measure/beat when known;
  - chord context when known;
  - tie, phrase boundary, and articulation when known.
- Exact target copedent ID/revision or saved-profile snapshot.
- Texture:
  - `single`;
  - `two_voice`;
  - `three_voice`;
  - `mixed`.
- Movement approach:
  - `best_fit`;
  - `slides`;
  - `pedal_lever_motion`;
  - `compact_pocket`;
  - `clean_repick`.
- Optional constraints:
  - maximum fret range;
  - preferred/avoided strings;
  - allowed controls;
  - preserve current position;
  - melody must remain on top.

### Arrangement response

- One recommended route plus materially distinct alternates.
- For every event:
  - exact melody pitch;
  - complete sounding pitch set;
  - string, fret, pedal, and lever actions;
  - texture size;
  - chord tones and intervals;
  - alternate validated positions;
  - selection reason.
- For every transition:
  - slide, squeeze/release, lever movement, hold, repick, add, or block;
  - affected and sustained strings;
  - controls before/after;
  - bar movement;
  - playable instruction.
- Route summaries:
  - counts of single notes, dyads, and triads;
  - slides, pedal glides, lever glides, repicks, and position changes;
  - deterministic validation result;
  - learned or deterministic ranking provenance;
  - difference from the recommended route.

## UI simplification

Replace the current overlapping arrangement/style controls with two primary
questions:

1. **How many voices?** Single note, two-note harmony, three-note harmony, or
   mixed.
2. **How should it move?** Best fit, slides, pedal/lever motion, stay in a
   pocket, or clean repicks.

Names such as Singing Steel, Smooth Harmony, and Full Harmony may remain as
descriptive presets, but each must disclose the concrete texture/movement
policy it applies. A preset is hidden when it produces the same route as the
current choice. The UI must never imply that seven independently learned
styles exist.

Every result should display:

- playable tablature first;
- synchronized fretboard movement;
- a concise “why this route” explanation;
- exact pitch/mechanical validation;
- alternative single-, two-, and three-note treatments;
- a visible comparison when a learned ranker changed the deterministic
  recommendation.

## Site-wide integration sequence

### Slice 1 — Shared arrangement core

- Introduce the common request/response contract.
- Wrap the existing arranger and private ranker without changing the frozen
  model.
- Make texture and movement intent explicit.
- Deduplicate identical routes.
- Require deterministic pitch and mechanical validity for every returned
  route.
- Add a dedicated arrangement API used by other endpoints.

### Slice 2 — Melody Studio and Q&A

- Replace overlapping route/style controls with Voices and Movement.
- Expose single-, two-, three-note, and mixed alternatives for the same input.
- Render slides and squeezes directly in tablature and the synchronized
  fretboard.
- Use the same arrangement bundle in Q&A melody/arrangement answers.
- Preserve exact saved-copedent personalization.

### Slice 3 — Fretboard Explorer and practice surfaces

- Add “Build a phrase from here” to single-note, grip, chord/voicing, scale
  path, and movement-path modes.
- Offer 1/2/3-voice variants from the selected note, position, scale segment,
  or chord progression.
- Route Song Practice and progression guidance through the same service.
- Keep the low-level tab renderer presentation-only; it must render validated
  arrangement events rather than invent choices.

### Slice 4 — Product QA and protected rollout

- Cross-surface parity: identical input, copedent, texture, and movement must
  yield identical musical events everywhere.
- Hard invariants:
  - 100% target-pitch agreement;
  - 100% mechanical validity;
  - melody remains the highest sounding voice;
  - no unsupported control combinations.
- Variant-value gate: every displayed alternate must differ in texture,
  position, or transition strategy.
- Test phrases:
  - single-note scale/run;
  - harmonized scale;
  - chord arrivals;
  - bar-slide phrase;
  - pedal squeeze/release phrase;
  - lever-resolution phrase;
  - saved-copedent phrase.
- Focused backend, UI, accessibility, and browser tests.
- Exact-path commit, protected-preview activation, automated smoke, then one
  bounded user-smoke handoff.

## Hard finish line

This program is complete when the user can enter or select a phrase on any
supported interactive surface and receive:

- mechanically valid playable tablature;
- synchronized fretboard playback;
- explicit single-, two-, three-note, and mixed options;
- validated slides and pedal/lever squeezes when appropriate;
- materially distinct approaches with honest provenance;
- the same result contract across Melody Studio, Q&A, Fretboard Explorer, and
  practice surfaces.

No additional supervised review, retraining, validation adjudication, or
sealed-test work is part of this program.

## Files changed

Private ignored operational work completed before the pivot:

- `corpus-private/melody-decisions/batches/atb-20260716-training-278-semantic-v2/sealed-test/lane15-ground-truth-draft/apply_latest_dual_review_receipts.py`
- Digest-pinned private receipt-application outputs under the two source
  batches.

Public planning handoff:

- `docs/handoffs/task-completions/2026-07-24-0816-18-amazing-tablature-productization-pivot.md`

No runtime, UI, API, model, rules, source image, embedding, vector store,
deployment, authentication, or protected-data file was changed.

## Tests and checks

- Read repository operating guidance and current product/answer guidance.
- Audited current branch and HEAD.
- Audited Melody Studio arrangement routes and UI controls.
- Audited private learned-ranker runtime integration.
- Audited style catalog and learned-style coverage.
- Audited Fretboard Explorer modes and current API surfaces.
- Verified both private receipts by exact packet/submission digest.
- Ran the dual-receipt applicator twice; the second run was idempotent.
- Verified the frozen code contract before and after receipt application.
- Verified both sealed cohorts remained in annotation state with zero
  official test runs.
- `git diff --check` will be run at closeout.

## Integration notes

- Current branch: `feature/answer-api`.
- Current HEAD: `8cdfac8ec2cccc6a625415a0e27fec7bd3c4ff6e`.
- Current private model: `at-b97d1a6cf902ba05`.
- Current validation result remains 119/124 top-one, 124/124 top-three, and
  124/124 mechanically valid.
- The visible catalog has seven presets, but the sanitized learned artifact
  contains independent learned weights for four canonical families:
  `chord_melody`, `harmonized`, `lever_driven`, and `single_note_run`.
- `auto` maps phrase roles to those learned families. `vocal_steel` and
  `fixed_pocket` are deterministic policies, not separately learned model
  heads.
- The private beta must continue to fail closed to deterministic arrangement
  behavior if its external artifact is unavailable or invalid.

## Risk assessment

Risk: medium.

The core musical capabilities exist, which lowers algorithmic risk. The main
risks are contract fragmentation, inconsistent behavior between surfaces,
misleading style labels, performance on large candidate catalogs, and
accidental weakening of hard pitch/mechanical validation. The phased shared
contract and cross-surface parity gates directly address these risks.

Rollback is to leave the existing private beta and current UI unchanged.

## Human decision needed

Yes. Approve this bounded productization program. Approval authorizes the
normal Autopilot implementation, focused tests, exact-path commits,
protected-preview update, automated smoke, and one user-smoke handoff. It does
not authorize more training, embeddings, scraping, auth changes, or a sealed
test.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-24-0816-18-amazing-tablature-productization-pivot.md`

## Files that must not be staged

- `corpus-private/**`
- Existing unrelated dirty and untracked handoffs
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`

## Recommended next lane

Lane 18 contract finalization, immediately followed by Lane 05 shared backend
implementation and Lane 06 site-wide UI integration within one Autopilot
feature run.

## Commit readiness

Needs human review first.

## Suggested next step

Approve the Amazing Tablature productization pivot and replace the existing
training goal with the bounded site-wide integration goal described above.
