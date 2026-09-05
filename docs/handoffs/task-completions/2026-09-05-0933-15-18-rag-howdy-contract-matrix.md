# RAG and Howdy Contract Matrix

## Run Charter

```text
Objective: Characterize the RAG event, fretboard, tablature, song, and
  Play-Along projections and compare them with the preserved Howdy contract.
Lane: 15 QA / Answer Eval + 18 Product / Architecture
Primary scope: PLATFORM:SHARED
Secondary scopes: PRODUCT:RAG and PRODUCT:COMPANION (characterization only)
Model tier: HIGH-REASONING for the cross-product contradiction classification;
  STANDARD for fixtures, tests, and documentation.
Routing reason: the slice compares independently evolved domain contracts and
  identifies which semantics can safely become shared.
Permitted paths: docs/howdy-contract-characterization.md,
  docs/platform-contract-comparison.md,
  tests/fixtures/platform_rag_contract_v1.json,
  tests/test_rag_contract_characterization.py, and this handoff.
Forbidden paths: runtime modules, product UI, dependencies, persisted data,
  corpus, private media, auth, deployment, Cloudflare, ports, and broad moves.
Consumers to verify: RAG Song Practice arranger, tab engine, static fretboard
  contract, Song Projects selection, Play-Along loop helpers, and the existing
  Howdy characterization fixture.
Success criteria: source-hash-pinned RAG fixture; executable projections for
  all named consumers; explicit agreement/contradiction matrix; focused tests
  green.
Budget: one RAG fixture and one comparison matrix.
Stop conditions: source drift, unexplained regression, schema implementation,
  or need to read private Companion review artifacts.
Terminal state: PASS
```

## Task Summary

Completed the RAG half of M0 contract characterization and compared it with
the preserved Howdy contract. The slice records actual output from the RAG
Song Practice arranger, typed tab events, static fretboard payloads, browser
current/next selection, and bar-loop projection.

The comparison identifies supported directions for a future proposal without
renaming or replacing either product's existing payloads.

## Files Changed

Created:

- `docs/platform-contract-comparison.md`
- `tests/fixtures/platform_rag_contract_v1.json`
- `tests/test_rag_contract_characterization.py`
- `docs/handoffs/task-completions/2026-09-05-0933-15-18-rag-howdy-contract-matrix.md`

Modified:

- `docs/howdy-contract-characterization.md`

Deleted: none. Generated artifacts: none.

## Tests and Checks

- Cross-product characterization tests: 10 passed.
- Focused RAG contract and consumer suite: 145 passed.
- Ruff on the new RAG characterization test: passed.
- RAG fixture JSON parse check: passed.
- Platform dependency-boundary check: passed; 69 managed files scanned.
- `git diff --check`: passed.

Browser smoke was not run because no browser or runtime behavior changed. The
existing browser modules were exercised through their exported deterministic
selection and loop functions.

## Integration Notes

The strongest agreements are stable IDs, millisecond ranges, ten-string E9
bounds, fixed grips, deterministic selection, and separation from RAG/model
calls.

The material contradictions are:

- chord-comping events versus steel-note/tab events;
- embedded chords versus a referenced chord timeline;
- one absolute clock versus full-song and taught-solo clock domains;
- RAG nullable pre-roll/final-next state versus Howdy final-item saturation;
- `changes`/`articulation` versus `controls`/`technique` naming;
- centrally versioned/resolved RAG copedents versus an embedded Howdy snapshot;
- mechanical validation versus product approval/review state.

The evidence supports a typed timed-event envelope, distinct chord events,
explicit clock domains, nullable current/next state, canonical controls plus a
structured articulation/transition object, and separation of platform
validity from product approval.

## Risk Assessment

Low. All repository changes are docs, synthetic fixtures, and tests. Source
hash pins intentionally make future drift visible. No product payload,
persisted object, UI, or runtime dependency changed.

Rollback: revert this commit. The prior Howdy characterization and remote
preservation refs remain valid independently.

## Human Decision Needed

No for this characterization slice. The next M1/M2 contract proposal will
require architecture review before any runtime implementation.

## Safe-To-Stage Exact File List

- `docs/howdy-contract-characterization.md`
- `docs/platform-contract-comparison.md`
- `tests/fixtures/platform_rag_contract_v1.json`
- `tests/test_rag_contract_characterization.py`
- `docs/handoffs/task-completions/2026-09-05-0933-15-18-rag-howdy-contract-matrix.md`

## Files That Must Not Be Staged

- every runtime module named by the fixture's source hashes;
- all dirty files in the primary and preserved Companion worktrees;
- private review data, media, release configuration, and generated bundles;
- deployment, auth, corpus, and environment files.

## Recommended Next Lane

Lane 18 Product / Architecture, followed by Lane 15 contract review.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Draft a versioned, implementation-free M1/M2 shared contract proposal for the
typed event envelope, clock domains, chord references, copedent snapshots, and
tablature transitions. Include explicit RAG and Howdy adapters and persistence
non-migration guarantees, then stop for architecture review.
