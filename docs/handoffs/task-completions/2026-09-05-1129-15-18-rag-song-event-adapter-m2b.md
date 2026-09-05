# Read-Only RAG Song/Event Adapter M2b Handoff

Date: 2026-09-05 11:29 CDT

Lane: `18 Product / Architecture` with focused `15 QA` and `01 Repo Steward`
closeout

Primary scope: `PLATFORM:SHARED`

Secondary scope: `PRODUCT:RAG` for read-only characterized input and tests only

Model tier: `STANDARD`

Routing reason: M2b is a bounded implementation of the approved adapter map
using the already accepted M1/M2 shared contracts

## Run Charter

- Objective: project one characterized `song_practice_plan_v1` into the shared
  timeline with zero errors, preserved product metadata, and explicit warnings
  for every non-equivalent behavior.
- Permitted paths: `packages/song_model/`, one focused adapter test, M2 platform
  documentation, and this handoff.
- Forbidden paths: RAG/Companion runtime sources, API/browser consumers,
  fixtures, persistence, private lessons, dependencies, deployment, services,
  DNS, production/test releases, and directory movement.
- Consumers to verify: live RAG Song Practice planner, pinned RAG
  characterization fixture, M1b copedent projection, M2a timeline, existing
  RAG characterization tests, complete repository suite, and dependency gate.
- Success criteria: zero adapter errors for the pinned plan; exact timing,
  chord, role, section, measure, position, controls, and pitch projection;
  source immutability; product metadata retained; differences diagnosed.
- Budget: one read-only RAG adapter; no Howdy mapping, product consumer,
  persistence, deployment, paid call, or broad reorganization.
- Stop conditions: need to change the shared contract, infer missing musical
  data, discard a source field, change RAG behavior, or touch a protected path.
- Terminal state: `PASS`; M2b completes in shadow/read-only form.

## Task Summary

Completed:

- Added `project_rag_song_practice`, a product-neutral adapter that accepts
  plain source data and an explicit shared copedent profile.
- Converts every ready RAG event into separate deterministic chord and steel
  events on non-overlapping logical tracks.
- Converts section and measure IDs into distinct namespaced structures and
  derives their ranges from referenced event boundaries.
- Converts resolved RAG positions into reusable shared positions and checks
  source MIDI/labels against the M1 copedent core.
- Keeps static Song Practice positions free of invented articulations or
  transitions.
- Preserves RAG-only route, provenance, warnings, display labels, event status,
  alternate positions, teaching instructions, chord-analysis values, and note
  display values outside the shared timeline.
- Preserves and reports new unknown RAG-only fields rather than discarding or
  guessing them.
- Records the derived media duration and structure ranges as warnings.
- Records the known selection difference: RAG presentation saturates on its
  final event, while canonical shared selection returns null at post-roll.
- Fails closed on source schema/profile mismatch, unresolved events, invalid
  timing, unsupported roles, position conflicts, control/pitch disagreement,
  and shared reference/overlap failures.

Intentionally not changed:

- No RAG or Companion runtime imports or calls the adapter.
- No API, browser, playback controller, source fixture, saved plan, schema
  version, feature flag, or dependency changed.
- RAG alternate positions were retained as product metadata rather than added
  to the shared v1 contract.
- Rest/manual events remain explicit adapter errors because shared v1 has no
  reviewed rest or unresolved-position event vocabulary.
- Production and `test.steelguitarrag.com` were not contacted or changed.

## Files Changed

- `docs/platform-adapter-and-migration-plan.md`
- `docs/platform-migration-sequence.md`
- `docs/platform-shared-contract-v1.md`
- `docs/rag-song-event-adapter.md`
- `docs/shared-component-map.md`
- `docs/song-event-core.md`
- `packages/song_model/__init__.py`
- `packages/song_model/rag_adapter.py`
- `tests/test_platform_rag_song_adapter.py`
- this handoff

No existing files were moved or deleted and no generated artifact belongs in
the commit.

## Tests And Checks

- Full Python suite: 1,697 passed.
- Focused RAG adapter, M2a core, M1b projection, RAG characterization, and
  dependency-boundary suite: 37 passed.
- New M2b tests: seven passed.
- Ruff: passed for all shared package and new adapter test files.
- Mypy: passed for all shared source files.
- Platform dependency boundary: passed; 76 managed source files scanned.
- Secret-pattern scan: passed.
- Asset budget: passed for 1,373 tracked files and 51 Explorer chunks.
- Dependency lock integrity: passed for five environments.
- JavaScript syntax and lint: passed.
- Worker tests: four passed.
- `git diff --check`: passed.

Hosted exact-commit CI is required after commit. The known Python and Node
dependency-audit advisories predate M2b; this slice changes no dependency or
lock file.

## Integration Notes

The successful fixture produces four canonical events from two source events:
`rag:chord:event-a`, `rag:steel:event-a`, `rag:chord:event-b`, and
`rag:steel:event-b`. It also produces one section, one measure, two reusable
positions, and one 2,000 ms media clock.

The adapter receives a `CopedentProfile`; it does not import RAG. Tests prove
that the live RAG profile can first pass through the M1b copedent projection,
then drive M2b. Plans using controls outside that approved profile fail with a
path-based diagnostic instead of being approximated.

The plan's timeline hash is used as an opaque deterministic projection ID. It
cannot be recomputed from a plan alone because its original key, meter, style,
and route-preference inputs are not all retained in `song_practice_plan_v1`.

## Risk Assessment

Risk: low.

The adapter is additive, deterministic, in-memory, and unconsumed. Rollback is
removal of the adapter/tests/docs exports. No source or persisted product data
needs rollback.

## Human Decision Needed

No decision is needed to merge M2b after hosted exact-commit CI records the
known audit-only baseline.

Yes before M2c: authorize only the read-only sanitized Howdy event adapter.
Cross-product parity, runtime cutover, persistence, and deployment remain
separate decisions.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-09-05-1129-15-18-rag-song-event-adapter-m2b.md`
- `docs/platform-adapter-and-migration-plan.md`
- `docs/platform-migration-sequence.md`
- `docs/platform-shared-contract-v1.md`
- `docs/rag-song-event-adapter.md`
- `docs/shared-component-map.md`
- `docs/song-event-core.md`
- `packages/song_model/__init__.py`
- `packages/song_model/rag_adapter.py`
- `tests/test_platform_rag_song_adapter.py`

## Files That Must Not Be Staged

- `.venv/`, `node_modules/`, `uv.lock`, caches, package metadata, and other
  generated local verification artifacts
- all RAG and Companion runtime sources and product fixtures
- all private lessons/copedents, deployment, release, corpus, vector, log,
  auth, and Cloudflare state

## Recommended Next Lane

`18 Product / Architecture` plus `15 QA`: M2c, a pure read-only Howdy adapter
against `tests/fixtures/platform_howdy_contract_v1.json`, using only its
sanitized contract and explicitly approved synthetic copedent match.

## Commit Readiness

Safe to commit after exact-path staging, full cached-diff review, and
`git diff --cached --check`. Hosted exact-commit CI remains promotion evidence.

## Suggested Next Step

Authorize only M2c. Do not merge the legacy Companion branch, import private
lesson/review content, connect a runtime consumer, persist a shared timeline,
or deploy either product.
