# Howdy Contract Preservation And Characterization

## Run Charter

```text
Objective: Preserve the exact production and Companion histories, select the
  integration base, and freeze a portable Howdy contract fixture without
  merging legacy history or changing runtime behavior.
Lane: 01 Repo Steward + 15 QA / Answer Eval
Primary scope: PRODUCT:COMPANION
Secondary scopes: PLATFORM:SHARED (tests and fixtures only)
Model tier: STANDARD
Routing reason: the platform migration policy already defines the contract
  preparation slice; implementation is bounded preservation and characterization.
Permitted paths: docs/howdy-contract-characterization.md,
  tests/fixtures/platform_howdy_contract_v1.json,
  tests/test_howdy_contract_characterization.py, this handoff, and exact remote
  preservation refs.
Forbidden paths: RAG retrieval/corpus, private source material, auth,
  Cloudflare configuration, deployment, runtime ports, production releases,
  dependencies, and application module movement.
Consumers to verify: preserved Travis/Howdy Python package, browser JavaScript,
  and Travis Companion Worker; governance-base characterization tests.
Success criteria: exact production and Companion refs resolve remotely;
  preserved Companion checks pass with declared extras; source-hash-pinned
  fixture and selection/scope tests pass on the governance base.
Budget: one preservation pair and one sanitized contract fixture.
Stop conditions: private data exposure risk, source hash mismatch, unexplained
  Companion regression, or required runtime/schema change.
Terminal state: PASS
```

## Task Summary

Completed the first Companion slice after governance:

- preserved the exact production commit on
  `preserve/production-2780c6b-20260905`;
- preserved the exact Companion/Howdy head on
  `preserve/companion-howy-v9-9a79d45-20260905`;
- selected `origin/main` commit
  `4a77e849c9c9ba8e13429d91ae055d06d0de7ce5`, followed by governance commit
  `2f7a18b9215d1a27db344cb756966d0f1663b9c1`, as the integration base;
- rejected the 173 unique Companion commits as a wholesale merge unit;
- added a sanitized, hash-pinned Howdy contract fixture and focused tests for
  event, tablature/fretboard grip, chord timeline, media scopes, and playback
  selection behavior.

No runtime, deployment, environment, schema, dependency, product UI, corpus,
private media, or application module was changed.

## Files Changed

Created:

- `docs/howdy-contract-characterization.md`
- `tests/fixtures/platform_howdy_contract_v1.json`
- `tests/test_howdy_contract_characterization.py`
- `docs/handoffs/task-completions/2026-09-05-0903-01-15-howdy-contract-characterization.md`

Deleted: none.

Generated artifacts: none tracked. The preserved Companion worktree's local
Python environment received its already-declared `companion` test dependencies;
that environment change is not part of Git.

## Tests And Checks

- Tracked-file secret-pattern scan on the Companion worktree: passed.
- Preserved Companion Python tests:
  `tests/test_travis_companion.py tests/test_travis_tutorials_companion.py`:
  42 passed, 1 skipped.
- `node --check partner_companions/travis_howdy/site/companion.js`: passed.
- Travis Companion Worker TypeScript check: passed.
- Travis Companion Worker tests: 6 passed.
- Characterization tests with `HOWDY_COMPANION_SOURCE` pointing at the
  preserved tracked draft: 5 passed.
- Ruff on the new test: passed.
- JSON parse check: passed.
- Platform dependency-boundary check: passed; 69 managed files scanned.
- `git diff --check`: passed.

The one skipped preserved test requires a platform-specific optional condition
already encoded by that test; no test was disabled or changed in this slice.

## Integration Notes

The source snapshot is pinned to:

- commit: `9a79d454491b843f74942ce9193f335512e402ad`
- tracked draft SHA-256:
  `a5437a788daf312e6a5cb5c7c77e267f6b70aed69aff93961426f424321cfccf`

The fixture deliberately excludes lesson copy, coaching excerpts, transcript
text, media, tester identities, release configuration, and deployment data.
It records only public schema shape and synthetic deterministic semantics.

The next integration slice should characterize equivalent RAG projections in
the same synthetic vocabulary. Shared runtime extraction remains premature
until the two fixture sets expose agreements and contradictions.

## Risk Assessment

Low. The remote changes add non-deployment preservation refs at exact existing
commits. Repository changes are documentation, fixture, and tests only. The
preservation refs provide rollback/recovery anchors and do not affect any
runtime selector.

Rollback: close the characterization PR if unsuitable. Do not delete either
preservation ref as part of rollback; they are recovery evidence.

## Human Decision Needed

No for this completed slice. Any later decision to change a shared semantic
contract still requires M0 comparison evidence.

## Safe-To-Stage Exact File List

- `docs/howdy-contract-characterization.md`
- `tests/fixtures/platform_howdy_contract_v1.json`
- `tests/test_howdy_contract_characterization.py`
- `docs/handoffs/task-completions/2026-09-05-0903-01-15-howdy-contract-characterization.md`

## Files That Must Not Be Staged

- all files from the dirty primary checkout;
- `docs/handoffs/task-completions/integration-status.md` in the preserved
  Companion worktree;
- private review artifacts, media, release configuration, and generated
  bundles;
- any deployment, auth, corpus, or runtime file.

## Recommended Next Lane

Lane 15 QA / Answer Eval with Lane 18 Product / Architecture review.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Characterize the RAG-side event, fretboard, tablature, song, and Play-Along
projections against `platform_howdy_contract_v1` and produce an explicit
agreement/contradiction matrix before proposing M1 shared theory extraction.
