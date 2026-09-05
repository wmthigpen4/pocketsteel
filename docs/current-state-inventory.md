# Steel Guitar Repository And Environment Inventory

Status: authoritative audit snapshot

Observed: 2026-09-05 America/Chicago

Git baseline: `origin/main` at
`4a77e849c9c9ba8e13429d91ae055d06d0de7ce5`

This inventory records what exists before platform extraction or repository
reorganization. Runtime observations are point-in-time evidence, not
authorization to restart, reconfigure, delete, or promote anything.

## Product And Deployable Surfaces

| Surface | Current implementation | Environment | Observed state |
|---|---|---|---|
| Steel Guitar RAG protected app | Flat Python package `steel_guitar_rag/` plus `ui/` | `app.steelguitarrag.com` through Cloudflare Access and Tunnel to loopback port 8770 | Access redirects correctly; loopback `/api/version` reported `2780c6b` |
| Companion staging / Play-Along | RAG Play-Along on `main`; later Howdy/Travis work exists only in local descendant branches | `test.steelguitarrag.com` through Cloudflare Access to loopback port 8771 | Access redirects correctly; loopback `/api/version` reported `9ff1c61c` |
| Public marketing and interest form | `deploy/landing/` and `functions/api/interest.js` | `steelguitarrag.com` on Cloudflare Pages | Anonymous root returned HTTP 200 |
| Canonical frontier service | Immutable local service bundle and LaunchAgent | Intended loopback-only service | LaunchAgent was loaded with repeated exit code 1 while port 8771 was owned by staging |
| Candidate protected app | Immutable local release | Loopback port 8772 | `/api/version` reported `476a51e` |
| Travis/Howdy static preview | `partner_companions/` and `deploy/travis-preview/` on local Companion branches | Dedicated protected Pages design at `travis-preview.steelguitarrag.com` | Not present on `origin/main`; deployment state was not changed in this audit |

## Environment Contract

The sanctioned application flow is:

```text
local development
  -> staging: test.steelguitarrag.com
  -> production: app.steelguitarrag.com
```

The public Pages site is a separate product surface and is not a stage in the
protected application's promotion chain. Companion work stays in staging until
its exact commit and product-specific smoke are approved. All environments use
immutable release artifacts; no environment follows a mutable branch.

### Current drift that must be preserved before cleanup

- Production reported `2780c6bc4f93cb7abaf237440b5801b0f197e3a0`,
  which is 28 commits ahead of `origin/main` and is not reachable from a named
  local or remote branch. The immutable release exists locally, but the commit
  needs a named, backed-up branch before branch or release cleanup.
- Staging reported `9ff1c61c30e32bfb22b3b424079323120b13bc04`,
  which is reachable from `main` and 36 commits behind it.
- A candidate runtime reported
  `476a51e044e8157d201c17aec9b659a944f76cb4`, 15 commits ahead of
  `main`, with no named branch containing it.
- The staging application owns port 8771. The canonical-frontier LaunchAgent
  is also configured for 8771 and was repeatedly exiting. Resolve the service
  port/ownership contract before any restart; do not stop the healthy staging
  listener as part of diagnosis.
- The checked-in operations docs describe an older LaunchDaemon-centered
  state. The observed application, staging, candidate, and frontier jobs are
  user LaunchAgents. Documentation and runtime state are therefore not fully
  aligned.

## GitHub And Branch Inventory

- Repository: `wmthigpen4/steel-guitar-rag`.
- Default branch: `main`.
- Open pull requests at audit time: none.
- Branch protection: none on `main`.
- Repository rulesets: none.
- Workflow token defaults to read-only and cannot approve pull requests.

Every non-main remote branch is fully contained in `main`; the first number
below is commits behind `main`, and every branch is zero commits ahead:

| Remote branch | Behind | Last commit date | Disposition |
|---|---:|---|---|
| `codex/rag-v0-electronics` | 899 | 2026-05-22 | deletion candidate after preservation review |
| `codex/steel-guitar-rag-ui-mock` | 898 | 2026-05-22 | deletion candidate after preservation review |
| `feature/answer-api` | 119 | 2026-07-24 | deletion candidate after confirming no external automation references it |
| `feature/enhanced-play-along-staging` | 77 | 2026-08-02 | retain until staging/Companion lineage is named and documented |
| `fix/local-play-along-route-options` | 33 | 2026-08-04 | retain until Companion lineage is named and documented |

No remote branch deletion was performed.

The local repository contains additional unpushed development histories:

- `feature/chord-reader-ml-v3`: 92 commits ahead and 12 behind `main`.
- `feature/chord-reader-ssl-v9`: 173 commits ahead and 12 behind `main`;
  contains the fullest observed Travis Companion, Howdy, and chord-reader work.
- `fix/local-play-along-route-options`: 86 commits ahead and 12 behind `main`.
- `fix/followup-context-20260813`: 2 commits ahead of `main`.
- `repair/qna-frontier-20260813`: 10 commits ahead of `main`.
- `repair/qna-provenance-followup-20260813`: 14 commits ahead of `main`.

These histories must be classified and backed up before removing branches or
worktrees. They must not be merged wholesale merely because they contain newer
work.

## Local Checkout And Release Inventory

At audit time, Git registered 66 worktrees: 58 detached and one prunable. The
local release directory contained 121 immediate release directories. This is
valuable rollback evidence as well as operational clutter.

Cleanup must begin with a manifest containing release path, full commit, active
service references, last-known smoke evidence, and keep/delete decision. Active
release, rollback, service-bundle, and private-data paths are protected. A
prunable worktree record can be pruned only after confirming that it is not the
sole reference to an unpushed commit.

## CI Inventory

One GitHub Actions workflow, `.github/workflows/quality.yml`, runs on pull
requests and pushes to `main` with two jobs:

- Python: full pytest, narrow Ruff and mypy checks, dependency audit,
  secret/asset checks, and lock integrity.
- JavaScript: syntax, narrow ESLint, Worker tests, and `npm audit` at high
  severity.

The last successful main run was commit `001014b9` on 2026-07-24. The ten
completed main runs after that failed; one additional run was cancelled.
At current `main`, failures are:

1. Python: 1,636 passed, 3 skipped, and 4 failed. The failures assume
   `<checkout>/.venv/bin/python`, but CI installs into the setup-python
   environment without creating `.venv`.
2. JavaScript: syntax, lint, and four Worker tests pass; `npm audit` fails on
   high-severity `brace-expansion` and `undici` advisories plus moderate
   findings. The reported `undici` remediation crosses Cloudflare tooling
   versions and requires a bounded dependency-upgrade slice, not an automatic
   force update.

The new platform-boundary check is intentionally independent of the future
directory move. It protects transitional RAG/Companion roots now and will
enforce `apps/`, `packages/`, and `services/` when they appear.

## Current Product Ownership

`origin/main` is still structurally a Steel Guitar RAG application with shared
capabilities embedded inside it. The local Companion branches add
`partner_companions/travis_howdy`, `travis_practice_guide`, and
`travis_tutorials`, plus a dedicated static preview deployment. Those product
sources are not on GitHub `main` and must not be treated as canonical until an
exact integration sequence is approved.

See `docs/shared-component-map.md` for the file-level shared-capability audit
and `docs/platform-migration-sequence.md` for the non-destructive extraction
order.

## Five Cleanup Gates: Initial Status

1. **Inventory and freeze the map — complete for this snapshot.** Products,
   hostnames, services, branches, CI, and local-only histories are identified.
2. **Establish product lanes — governance complete.** `AGENTS.md` now requires
   `PRODUCT:RAG`, `PRODUCT:COMPANION`, `PLATFORM:SHARED`, or `INFRASTRUCTURE`.
3. **Clean branches and documentation — started, no deletion performed.** Five
   remote branches are contained in `main`; local-only Companion and production
   histories require preservation decisions first.
4. **Normalize environments — contract defined, runtime mutation deferred.**
   Local, staging, and production are named; the port conflict and docs/runtime
   drift are recorded for an infrastructure repair slice.
5. **Resume Companion — ready for a bounded preparation slice.** Preserve the
   exact `feature/chord-reader-ssl-v9` history remotely, choose an integration
   base, and characterize Howdy's current event/fretboard/tab/playback behavior
   before extracting or extending shared code.

## Immediate Stop Conditions

Do not delete branches, prune worktrees/releases, change ports, restart jobs,
promote code, or reorganize directories until the exact production and
Companion commits have named durable refs and the affected environment has a
verified rollback SHA.
