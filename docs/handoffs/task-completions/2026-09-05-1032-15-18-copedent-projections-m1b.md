# Read-Only Copedent Projections M1b Handoff

Date: 2026-09-05 10:32 CDT

Lane: `18 Product / Architecture` with focused `15 QA` and `01 Repo Steward`
closeout

Primary scope: `PLATFORM:SHARED`

Secondary scopes: `PRODUCT:RAG` and `PRODUCT:COMPANION` for read-only contract
inputs and characterization tests only

Model tier: `STANDARD`

Routing reason: M1b is a bounded implementation of the approved M1 copedent
contract and consumer matrix

## Run Charter

- Objective: add pure, read-only projections from the live characterized RAG
  copedent payload and the approved sanitized Howdy copedent fixture into the
  M1a shared profile, with explicit diagnostics and no consumer change.
- Permitted paths: `packages/steel_theory/`, one new projection test, the
  sanitized Howdy fixture approval metadata, M1 platform documentation, and
  this handoff.
- Forbidden paths: RAG/Companion runtime sources, APIs, browser/UI code,
  private/player copedents, event/song adapters, persistence, deployment,
  services, releases, DNS, dependencies, and directory movement.
- Consumers to verify: RAG `emmons-e9-basic` payload, sanitized Howdy
  `synthetic-e9` fixture, M1a core, M0 RAG/Howdy characterization suites, and
  the platform dependency boundary.
- Success criteria: both accepted projections produce the same canonical
  snapshot/digest with zero errors; omissions are warnings; mismatches fail
  closed; all M1a dominant-seventh and A+B ii-minor cases remain green.
- Budget: one copedent-projection slice; no runtime integration, paid calls,
  deployment, or data mutation.
- Stop conditions: need to infer a private/user copedent, change a product
  consumer, weaken mismatch validation, or expand into the event model.
- Terminal state: `PASS`; M1b completes in shadow/read-only form.

## Task Summary

Completed:

- Added shared projection result, diagnostic, and approved-profile-match types.
- Added a RAG projection that consumes the existing public profile payload,
  preserves ID/revision/open pitches, and projects the approved A/B core with
  exact signed semitone changes.
- Added a Howdy projection that expands the compact sanitized fixture only
  through the named `synthetic-e9` to `emmons-e9-basic` revision 1 approval.
- Verified that all ten Howdy open pitches and exact A/B affected-string lists
  match before using the approved canonical deltas and revision.
- Emits warnings for RAG controls outside M1a and for Howdy's omitted control
  deltas/revision. Those source omissions are never silently treated as source
  evidence.
- Rejects missing approval, malformed input, duplicate controls, missing RAG
  controls, open-string disagreement, affected-string disagreement, explicit
  semitone disagreement, revision disagreement, and scientific-pitch/MIDI
  disagreement.
- Proved that both successful projections have the same canonical snapshot and
  digest and preserve the dominant-seventh and A+B 5-6-7 ii-minor gold rules.

Intentionally not changed:

- Neither product imports or calls the new projection at runtime.
- No product answer, fretboard card, Companion lesson, API, schema, saved
  record, private copedent, or deployment changed.
- RAG's additional pedals/levers were not moved into the M1a core.
- The Howdy approval applies only to the synthetic sanitized fixture; it does
  not identify or authorize any private/player-specific copedent.
- Song/event modeling and product event adapters remain outside M1b.

## Files Changed

- `docs/platform-adapter-and-migration-plan.md`
- `docs/platform-contract-comparison.md`
- `docs/platform-migration-sequence.md`
- `docs/platform-shared-contract-v1.md`
- `docs/steel-theory-core.md`
- `packages/steel_theory/__init__.py`
- `packages/steel_theory/projections.py`
- `tests/fixtures/platform_howdy_contract_v1.json`
- `tests/test_platform_copedent_projections.py`
- this handoff

No files were moved or deleted and no generated artifact is part of the slice.

## Tests And Checks

- M1 projection/core plus M0 characterization/candidate/boundary tests: 32
  passed.
- Full locked Python 3.12 suite in the isolated worktree: 1,672 passed; three
  macOS host-layout checks initially failed because the worktree has no local
  `.venv` by design.
- The affected host-layout group passed 11/11 after temporarily presenting the
  locked validation environment at the ignored `.venv` path; the link was then
  moved out of the worktree.
- Ruff check and formatting: passed for all shared package and new test files.
- Mypy: passed for all three shared source files.
- Platform dependency boundary: passed; 73 managed source files scanned.
- `git diff --check`: passed.

Hosted exact-commit CI is still required. The known Python and Node dependency
audit advisories predate M1b and remain out of scope.

## Integration Notes

The RAG projection intentionally narrows the existing larger product profile to
A/B and reports the remaining controls as `controls_outside_m1a`. The Howdy
projection cannot derive semitone changes from control letters, so the caller
must provide an `ApprovedProfileMatch`. The fixture records that approval ID
and its synthetic-only limitation.

`CopedentProjection.profile` is absent whenever an error diagnostic exists.
Warnings preserve known source omissions while allowing read-only parity.

## Risk Assessment

Risk: low.

The code is additive, pure, and unconsumed. Rollback is removal of the
projection module/tests/metadata; no product data needs rollback. The main
future risk is mistaking this synthetic Howdy match for evidence about a real
private/player copedent, which the API, fixture, and documentation explicitly
prohibit.

## Human Decision Needed

No decision is needed to merge M1b after exact-commit functional CI succeeds.

Yes before M2a: architecture must separately authorize the pure song/event
core. Product event adapters and runtime cutover require later independent
approval and evidence.

## Safe-To-Stage Exact File List

- `docs/platform-adapter-and-migration-plan.md`
- `docs/platform-contract-comparison.md`
- `docs/platform-migration-sequence.md`
- `docs/platform-shared-contract-v1.md`
- `docs/steel-theory-core.md`
- `docs/handoffs/task-completions/2026-09-05-1032-15-18-copedent-projections-m1b.md`
- `packages/steel_theory/__init__.py`
- `packages/steel_theory/projections.py`
- `tests/fixtures/platform_howdy_contract_v1.json`
- `tests/test_platform_copedent_projections.py`

## Files That Must Not Be Staged

- `.venv/`, build directories, wheels, caches, and package metadata generated
  during local verification
- all RAG and Companion runtime source files
- all private/player copedents, deployment, release, corpus, vector, log, auth,
  and Cloudflare state

## Recommended Next Lane

`18 Product / Architecture` plus `15 QA`: review M2a as a pure shared
song/event core against the synthetic candidate fixture. Keep RAG and Howdy
event adapters, consumers, persistence, and deployment outside that slice.

## Commit Readiness

Safe to commit after exact-path staging, complete cached-diff review, and
`git diff --cached --check`. Hosted exact-commit CI remains promotion evidence.

## Suggested Next Step

Authorize only M2a: implement the product-neutral clock, structure, position,
typed event, validation, serialization, and nullable selection behavior against
the synthetic candidate. Do not connect either product yet.
