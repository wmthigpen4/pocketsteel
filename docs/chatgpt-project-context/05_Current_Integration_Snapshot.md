# 05 Current Integration Snapshot

> Historical snapshot retained for context. It is no longer the current status source; use `docs/handoffs/task-completions/integration-status.md` for the active integration snapshot.

## Branch And Recent HEAD

- Current branch at bundle generation: `feature/answer-api`.
- Current HEAD at bundle generation: `56277fd docs: design public-domain song tab architecture`.
- `integration-status.md` remains the source of truth for reset guidance, but it is broad and includes older readiness snapshots.

## Latest Relevant Commits

- `56277fd docs: design public-domain song tab architecture`
- `1e73d7f fix: align app hanging sign on mobile`
- `c7116d5 docs: record cloudflare login logo deploy`
- `e293212 deploy: publish cloudflare login logo asset`
- `f05dc6d ui: cache bust answer badge artwork`
- `3c4dedb asset: update answer badge rag artwork`
- Earlier tab-engine baseline referenced by integration status:
  - `686fd3c feat: add deterministic tab engine slice`
  - `20d2f84 fix: render fretboard-first static grip answers`

## Current Tab-Engine Status

Committed tab-engine work includes:

- deterministic `steel_guitar_rag/tab_engine.py`,
- `POST /api/tab/render`,
- fixed-width tab rendering,
- validation for string/fret/control issues,
- answer-triggered tab examples for safe movement/sequence prompts,
- fretboard-first handling for static grip prompts,
- product architecture for next tab slices and public-domain song tab direction.

Current product correction:

- SVG fretboard owns static positions.
- Tab engine owns movement over time.

## Latest Protected-Preview Smoke Result

Latest tab-related protected-preview smoke in handoffs:

- `docs/handoffs/task-completions/2026-06-18-12-fretboard-first-static-grips-smoke.md`
- Runtime tested: `20d2f84`.
- Result: protected-preview browser smoke passed for static grip fretboard-first behavior, movement tab behavior, negative/copyright prompts, stale-state clearing, and `/api/version`.

Earlier app readiness snapshot in `integration-status.md` records:

- runtime `05e8748` browser verified,
- `https://app.steelguitarrag.com/` ready for use at that time,
- automated API QA had zero true blockers in that scope.

## Known Unrelated Failures / Caveats

Known full-suite static/UI caveats repeatedly classified as unrelated to backend/tab slices:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

The worktree is broad and dirty with staged and unstaged parked work. Use exact-path or exact-hunk staging only.

## Parked Dirty Work Note

At bundle generation, unrelated staged files existed outside this bundle. They were not modified or unstaged. Any future Repo Steward action must inspect `git status --short` and `git diff --cached --name-only` before committing.

## Next Recommended Slice

Recommended next product slice:

- Lane 18 or Lane 05: choose the next tab-engine step from the product ladder.
- Best narrow implementation candidate: parameterized chord-movement examples for standard E9 major-key I-IV, I-V, and I-IV-V-I movements.
- Do not jump to arbitrary melody or public-domain song tab generation until source/provenance records and rights status are explicit.
