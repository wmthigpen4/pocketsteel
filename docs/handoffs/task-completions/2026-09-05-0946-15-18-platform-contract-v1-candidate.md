# Platform Shared Contract v1 Candidate and Design Review

## Run Charter

```text
Objective: Produce an implementation-free, versioned M1/M2 shared-contract
  candidate and adapter/non-migration plan from the completed RAG/Howdy M0
  evidence.
Lane: 18 Product / Architecture + 15 QA / Answer Eval
Primary scope: PLATFORM:SHARED
Secondary scopes: PRODUCT:RAG and PRODUCT:COMPANION (adapter contracts only)
Model tier: HIGH-REASONING for cross-product contract decisions; STANDARD for
  candidate fixture, tests, documentation, and checks.
Routing reason: independently evolved product contracts disagree on event
  type, clock, selection, copedent, tab vocabulary, and review metadata.
Permitted paths: docs/platform-shared-contract-v1.md,
  docs/platform-adapter-and-migration-plan.md,
  docs/platform-migration-sequence.md,
  tests/fixtures/platform_shared_contract_v1_candidate.json,
  tests/test_platform_shared_contract_candidate.py, and this handoff.
Forbidden paths: runtime modules, current product schemas and payloads,
  persistence, dependencies, product UI, corpus, private Companion material,
  auth, deployment, Cloudflare, environment, ports, and broad code movement.
Consumers to verify: M0 RAG fixture, M0 Howdy fixture, future steel-theory and
  song-model packages, RAG adapter, and Howdy adapter.
Success criteria: exact candidate vocabulary; reusable position preservation;
  explicit adapter tables and diagnostics; no-migration guarantee; bounded
  implementation sequence; executable candidate invariants; M0 tests green.
Budget: one candidate contract, one adapter plan, one synthetic example, one
  focused invariant test module, and one migration-status update.
Stop conditions: runtime implementation, product cutover, persisted-data
  change, unsupported inference from private data, or unexplained regression.
Terminal state: PASS for proposal delivery; architecture approval remains a
  separate gate before M1a implementation.
```

## Task Summary

Produced the final architecture-cleanup proposal needed before shared-platform
development. The candidate defines named clock domains, reusable fretboard
positions, typed chord/steel events, copedent identity plus reproducible
snapshot, separate controls/articulations/transitions, mechanical validity,
non-overlapping logical tracks, and nullable deterministic selection.

The adapter plan maps the observed RAG and Howdy shapes without changing either
source. It explicitly blocks guessed Howdy pedal semantics: the preserved
compact snapshot identifies affected strings but must receive an approved
profile/revision match before an adapter may emit semitone changes.

## Design Review Findings

Lane 15 review found the candidate consistent with the M0 evidence after one
correction: fixed Howdy chord grips must remain shared fretboard data. The
candidate therefore includes reusable validated positions referenced by chord
or steel events instead of discarding grips as presentation metadata.

The proposal also preserves these boundaries:

- milliseconds are authoritative for v1 selection;
- sections, measures, and phrases are not aliases;
- chord and steel events remain different event kinds;
- product approval, RAG provenance, rights, teaching copy, and release data do
  not enter mechanical validity;
- existing product schema versions and persistence stay unchanged;
- product-specific final-card saturation may remain a UI rule, not canonical
  selection behavior.

Tempo/meter grids, harmonic/key context, source identity, and richer musical
spelling remain outside this first candidate because the characterized
fixtures do not yet provide enough common evidence to define them without
guessing. Adapters must retain those source fields as product metadata and
report them as not yet mapped. In particular, Howdy `I`/`IV` events cannot be
declared equivalent to RAG `G`/`C` events without explicit G-major context.

## Files Changed

Created:

- `docs/platform-shared-contract-v1.md`
- `docs/platform-adapter-and-migration-plan.md`
- `tests/fixtures/platform_shared_contract_v1_candidate.json`
- `tests/test_platform_shared_contract_candidate.py`
- `docs/handoffs/task-completions/2026-09-05-0946-15-18-platform-contract-v1-candidate.md`

Modified:

- `docs/platform-migration-sequence.md`

Deleted: none. Runtime files changed: none.

## Tests and Checks

- Candidate invariants plus M0 RAG/Howdy characterization: 14 passed.
- Focused candidate, contract, and RAG consumer suite: 149 passed.
- Candidate-test Ruff check: passed.
- Candidate JSON parse: passed.
- Platform dependency boundary check: passed; 69 managed files scanned.
- `git diff --check`: passed.

Browser smoke is not applicable because no browser or runtime behavior
changed.

## Risks

Low runtime risk: the slice contains documentation, a synthetic candidate
fixture, and tests only. The principal architecture risk is premature adoption
of a candidate name or adapter mapping before review.

The candidate does not solve tempo/meter modeling, spelling context, persisted
record migration, or product cutover. Those omissions are explicit and must
not be filled by adapter guesses.

Rollback: revert the candidate commit. M0 fixtures and both products remain
unchanged.

## Human Decision Needed

Yes, before development. Architecture review must accept or revise the ten
choices listed in `docs/platform-shared-contract-v1.md`. A pass authorizes only
M1a, the pure steel-theory/copedent core.

## Safe-To-Stage Exact File List

- `docs/platform-shared-contract-v1.md`
- `docs/platform-adapter-and-migration-plan.md`
- `docs/platform-migration-sequence.md`
- `tests/fixtures/platform_shared_contract_v1_candidate.json`
- `tests/test_platform_shared_contract_candidate.py`
- `docs/handoffs/task-completions/2026-09-05-0946-15-18-platform-contract-v1-candidate.md`

## Files That Must Not Be Staged

- all application and product runtime modules;
- existing product schema payloads and persisted artifacts;
- the preserved Companion worktree and its unrelated dirty handoff;
- private review data, media, corpus, auth, deployment, environment, and
  dependency files;
- `docs/handoffs/task-completions/integration-status.md`.

## Recommended Next Lane

Human/Lane 18 architecture approval, then Lane 01 exact-path commit if this
candidate is left uncommitted; after approval, M1a implementation begins under
`PLATFORM:SHARED` with Lane 15 contract tests.

## Commit Readiness

Safe to commit as an explicitly labeled review candidate after final focused
checks and exact-path review. Committing the proposal does not approve runtime
implementation.

## Suggested Next Step

Review the ten candidate decisions. If accepted, authorize only M1a: the pure
steel-theory/copedent core and its synthetic tests. Do not start event adapters,
consumer cutover, persistence changes, or deployment in that slice.
