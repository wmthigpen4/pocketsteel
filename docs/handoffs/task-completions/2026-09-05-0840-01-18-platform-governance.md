# Platform Governance And Repository Cleanup Handoff

Date: 2026-09-05 08:40 CDT

Lane: `18 Product / Architecture` with `01 Repo Steward` and focused `15 QA`

Primary scope: `PLATFORM:SHARED`

Secondary scopes: `PRODUCT:RAG`, `PRODUCT:COMPANION`, and `INFRASTRUCTURE`
for inventory/governance only

Model tier: `HIGH-REASONING`

Routing reason: cross-product ownership, dependency boundaries, migration
ordering, and production/staging preservation

## Run Charter

- Objective: establish the two-products/one-platform operating model, audit the
  current repository/environments, add a dependency-direction check, and begin
  the five cleanup gates without moving runtime code.
- Permitted paths: `AGENTS.md`, repository/documentation indexes, four new
  architecture/inventory documents, PR governance, one standalone boundary
  checker, its tests, and the quality workflow.
- Forbidden paths: product runtime behavior, RAG retrieval/corpus, private
  sources, auth, DNS, Cloudflare settings, deployment scripts, launch-service
  state, runtime ports, releases, branch deletion, and application code moves.
- Consumers to verify: current flat RAG package, transitional
  `partner_companions` boundary, and future `apps/`, `packages/`, `services/`
  roots.
- Budget: one audit/governance slice; no paid model/API calls and no runtime
  mutation.
- Stop conditions: any required deployment change, destructive cleanup,
  ambiguous production commit, or shared-code movement.
- Terminal state: `PASS` for governance; infrastructure and preservation risks
  are explicitly queued rather than expanded into this task.

## Task Summary

Completed:

- Evolved `AGENTS.md` with architectural scopes, finite run charters, model
  routing, escalation/de-escalation, budgets, terminal states, dependency
  direction, shared-platform evidence, and exact-commit promotion rules.
- Added an authoritative current-state/environment inventory, platform
  constitution, shared-component map, migration sequence, and root environment
  pointer.
- Added a PR checklist that carries the same scope/evidence requirements into
  GitHub review.
- Added a dependency-boundary checker and four focused tests. It rejects app
  cross-imports and shared/service dependency inversions in the current
  transitional and future target roots.
- Updated Python CI to create the `.venv` path required by existing repository
  tests and deployment preflight assumptions, then added the boundary check.
- Audited GitHub branches, open PRs, branch protection/rulesets, recent Actions
  runs, local worktrees/releases, active hostnames, launch services, loopback
  versions, and current RAG/Companion implementations.

Intentionally not changed:

- No runtime code, product UI, data, corpus, vector store, auth, deployment
  script, Cloudflare setting, service, port, hostname, branch, worktree, or
  release was moved, deleted, restarted, promoted, or reconfigured.
- No broad `apps/`/`packages/` reorganization was started.
- Node dependency upgrades were not attempted; the current audit requires a
  bounded Cloudflare tooling compatibility slice.

## Concrete Findings

- `origin/main` is `4a77e849`; all five non-main remote branches are fully
  contained in it, but local-only Companion and repair histories remain.
- `main` has no branch protection or repository ruleset and no open PR.
- The last ten completed main workflow runs failed. Current Python failures
  came from the missing `.venv` path; JavaScript fails at `npm audit` after
  syntax, lint, and Worker tests pass.
- Production reports `2780c6b`, 28 commits ahead of `origin/main`, with no named
  branch containing it. Preserve it on a durable ref before cleanup.
- Staging reports `9ff1c61c` and is healthy on port 8771 behind Cloudflare
  Access. A canonical-frontier LaunchAgent is also configured for port 8771
  and repeatedly exits while staging owns the listener.
- The fullest observed Companion/Howdy history is local
  `feature/chord-reader-ssl-v9`, 173 commits ahead and 12 behind `main`. It
  reimplements event validation, fretboard drawing, tab rendering, timeline,
  and playback selection rather than consuming shared contracts.
- Git registered 66 worktrees and the release root contained 121 immediate
  directories. Cleanup requires an active-reference/commit manifest first.

## Files Changed

- `.github/pull_request_template.md`
- `.github/workflows/quality.yml`
- `AGENTS.md`
- `ENVIRONMENTS.md`
- `README.md`
- `docs/README.md`
- `docs/architecture.md`
- `docs/current-state-inventory.md`
- `docs/platform-architecture.md`
- `docs/platform-migration-sequence.md`
- `docs/shared-component-map.md`
- `scripts/check_platform_boundaries.py`
- `tests/test_platform_boundaries.py`
- this handoff

No files were moved or deleted. The ignored local `.venv/` is a verification
environment and must not be staged.

## Tests And Checks

- `python3 scripts/check_platform_boundaries.py`: passed; 69 managed current
  source files scanned.
- focused boundary tests: 4 passed.
- Python compile check for the new checker: passed.
- Ruff for the checker and tests: passed.
- mypy for the checker: passed.
- `git diff --check`: passed before staging.
- Full Python suite in a fresh locked Python 3.12 `.venv`: 1,647 passed in the
  clean post-commit checkout. The pre-commit run had one expected failure
  because the deployment preflight test rejects a dirty checkout before
  reaching its branch-check assertion.
- GitHub audit: current main run had 1,636 passed, 3 skipped, 4 failed before
  this CI fix; JavaScript audit failure remains unresolved.

## Integration Notes

The boundary checker enforces forbidden dependency edges; it does not claim
that current flat RAG modules are already separated. It treats
`steel_guitar_rag/` as transitional RAG ownership,
`partner_companions/` as transitional Companion ownership, and future
`packages/` as shared. Contract characterization must precede reclassification
or movement of mixed current modules.

The Python workflow fix is intentionally limited to environment creation. It
does not change deployment scripts or weaken their exact-release checks.

## Risk Assessment

Risk: medium.

The committed changes are governance, tests, and CI-safe environment setup, so
runtime rollback is not applicable. The operational findings are high
importance: production is ahead of named Git history and two services claim
port 8771. Those risks are unchanged by this commit and must be handled in
separate exact-scope slices.

## Human Decision Needed

Yes, before destructive or external cleanup:

1. Approve a durable remote preservation ref for production commit `2780c6b`
   and the chosen Companion history.
2. Choose the Companion integration base rather than wholesale-merging the
   173-commit local branch.
3. Approve an infrastructure repair plan for port 8771 and the canonical
   LaunchAgent/runbook alignment.
4. Choose whether `main` branch protection should require both quality jobs
   after the Node dependency audit is repaired.

No decision is needed to use the new governance rules or begin the bounded
Companion characterization slice.

## Safe-To-Stage Exact File List

- `.github/pull_request_template.md`
- `.github/workflows/quality.yml`
- `AGENTS.md`
- `ENVIRONMENTS.md`
- `README.md`
- `docs/README.md`
- `docs/architecture.md`
- `docs/current-state-inventory.md`
- `docs/platform-architecture.md`
- `docs/platform-migration-sequence.md`
- `docs/shared-component-map.md`
- `docs/handoffs/task-completions/2026-09-05-0840-01-18-platform-governance.md`
- `scripts/check_platform_boundaries.py`
- `tests/test_platform_boundaries.py`

## Files That Must Not Be Staged

- `.venv/`
- all pre-existing files in other checkouts
- all runtime, release, corpus, vector, private-source, log, and Cloudflare
  state outside this isolated worktree

## Recommended Next Lane

`01 Repo Steward` plus `15 QA`: preserve and characterize the exact current
Howdy contract as specified in `docs/platform-migration-sequence.md`. Do not
move shared code in that slice.

## Commit Readiness

Safe to commit. Exact-path staging, cached-name review, complete cached diff
review, `git diff --cached --check`, and the clean post-commit suite passed.

## Suggested Next Step

Preserve production and Companion commits on named remote refs, then build
cross-product characterization fixtures for steel events, fretboard state,
tablature tokens, song/chord timelines, and playback current/next selection.
