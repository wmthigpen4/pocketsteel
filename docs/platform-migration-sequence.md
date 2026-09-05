# Steel Guitar Platform Migration Sequence

Status: planned, not authorized for broad movement

Baseline: current-state audit dated 2026-09-05

The repository will move by contract and consumer, not by directory tree. Each
step is independently reversible and ends at a named terminal state.

## Current Position

M0 contract characterization is complete on the governed integration stack.
The source-pinned RAG and Howdy fixtures and their contradiction matrix are the
evidence for `docs/platform-shared-contract-v1.md`. The candidate contract and
`docs/platform-adapter-and-migration-plan.md` now await architecture review.

No runtime extraction or persisted-data migration has started. A review pass
authorizes only M1a, the pure steel-theory/copedent core; it does not authorize
song/event adapters, consumer cutover, deployment, or broad reorganization.

## Entry Gates Before Extraction

1. Preserve the running production commit and active Companion history on
   named backed-up refs.
2. Repair the existing CI baseline or record a narrowly accepted failure with
   an owner and deadline. Platform movement does not proceed on an unexplained
   red baseline.
3. Resolve the staging/canonical-frontier port ownership conflict without
   interrupting the healthy staging listener.
4. Choose the exact Companion integration base; do not merge its 173 unique
   commits wholesale.
5. Add characterization fixtures that can run from both product histories.

## M0 — Freeze Observable Contracts

Scope: `PLATFORM:SHARED` documentation and tests only.

- Inventory current schemas, JSON payloads, browser globals, version fields,
  and public Python imports.
- Capture representative pitch/control, fretboard, tab, song, and playback
  fixtures from RAG and Howdy.
- Define compatibility vocabulary and identify contradictions.
- Do not move modules or change runtime behavior.

Exit: fixture suites pass on the chosen RAG and Companion candidate commits.

## M1 — Steel Theory And Copedent Core

Start with pure deterministic behavior: pitch classes, scientific pitch,
tuning, control deltas, note spelling, copedent identity/revision, and control
resolution.

- Extract behind existing Python imports and a generated/static browser data
  contract.
- Keep product labels and profile-management UX in each app.
- Prove parity for Chat fretboard answers, Explorer, Melody Studio, Song
  Practice, and Howdy fixtures.

Exit: one canonical rule set with compatibility adapters; no product imports.

## M2 — Song And Steel Event Model

Reconcile `TabEvent`, `MelodyInput`, `PositionCandidate`, `score_draft_v1`,
Song Practice plan/timeline fields, and `lesson_companion_v1` into versioned
contracts.

- Define song identity/revision, sections, tempo/meter, clock units, chord
  events, steel events, source linkage, and review/verification state.
- Keep private/partner approvals and RAG provenance as product metadata
  extensions rather than weakening the shared core.
- Add dual adapters before changing persisted or packaged artifacts.

Exit: both products round-trip canonical fixtures without information loss.

## M3 — Fretboard Engine

Separate state and pitch resolution from product query parsing, teaching copy,
catalog generation, and visual styling.

- Canonical input: tuning/copedent, fret, active controls, selected strings,
  and optional current/next event.
- Canonical output: resolved pitches, validated positions/markers, movement,
  and stable selection identifiers.
- RAG retains Explorer and answer-card adapters; Companion retains Howdy cues
  and theme.

Exit: RAG and Howdy render the same canonical fixtures with product-specific
presentation and no duplicated fretboard math.

## M4 — Tablature Engine

Move validation and render-model creation behind the canonical steel event.

- Preserve current text/print/browser outputs through adapters.
- Make semantic transitions and articulation explicit instead of encoding
  them only in display tokens.
- Keep PDF branding, page layout, answer-card layout, and partner styling in
  their products.

Exit: shared event fixtures drive RAG Chat, Melody Studio, Play-Along, Howdy,
and print tests.

## M5 — Play-Along Engine

Extract the deterministic state machine after song, event, fretboard, and tab
contracts are stable.

- Own clock, speed, seek, loop, count-in/metronome state, current/next event,
  chord/section lookup, and synchronized selection.
- RAG owns Songs/Play-Along workflow and persistence UX.
- Companion owns full-song versus taught-solo modes, Travis cues, help density,
  related lessons, and partner presentation.

Exit: identical state-machine fixtures pass in both consumers, followed by
staging browser smoke on every affected surface.

## M6 — Product Shell Placement

Only after M1–M5 are stable may product entry points move toward `apps/` and
shared code toward `packages/`. Use compatibility shims and one bounded move
per commit. Do not combine a shell move with domain changes or deployment.

## Required Evidence For Every Migration Slice

```text
Objective and architectural scope
Model tier and routing reason
Permitted and forbidden paths
Old and new contract versions
Known consumer list
Characterization tests
Shared tests
RAG consumer tests
Companion consumer tests
Staging smoke targets/results
Full candidate SHA and source branch
Rollback SHA
Terminal state
```

The only successful terminal state is `PASS`. `BLOCKED`,
`NEEDS_PRODUCT_DECISION`, `NEEDS_ARCHITECTURE_DECISION`, `REGRESSION`, and
`BUDGET_EXHAUSTED` preserve the evidence and stop without broadening scope.

## First Companion Slice After Governance

The next safe slice is preparation, not a refactor:

```text
Objective: Preserve and characterize the current Howdy contract.
Lane: 01 Repo Steward + 15 QA / Answer Eval
Primary scope: PRODUCT:COMPANION
Secondary scope: PLATFORM:SHARED (tests/fixtures only)
Model tier: STANDARD
Permitted paths: exact Companion branch docs, fixtures, and focused tests
Forbidden paths: RAG retrieval/corpus, auth, Cloudflare, deployment, runtime
  ports, production release, broad module moves
Success: named remote preservation ref; exact integration base; fixtures for
  event, fretboard, tab, chord timeline, and playback selection; existing
  Companion checks green
Terminal states: PASS | BLOCKED | NEEDS_ARCHITECTURE_DECISION | REGRESSION
```

After that slice, product-only Howdy presentation work can continue immediately.
Changes to shared semantics enter M0/M1 rather than growing another Companion-
specific implementation.
