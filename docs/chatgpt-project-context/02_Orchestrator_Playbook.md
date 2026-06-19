# 02 Orchestrator Playbook

## Default Development Loop

1. Decide the slice.
2. Run one code lane per surface area.
3. Run docs, QA, and smoke lanes in parallel only when file scope does not conflict.
4. Run Repo Steward for exact-path commit hygiene.
5. Run Lane 12 protected-preview smoke for runtime/user-facing changes.
6. Run user smoke.
7. Refresh `docs/handoffs/task-completions/integration-status.md`.
8. Stop or choose the next slice.

## Parallel Lane Rules

Parallel lanes are safe when they touch different surfaces:

- Lane 05 backend and Lane 15 QA planning can run in parallel if QA does not edit backend files.
- Lane 06 UI and Lane 18 architecture can run in parallel if architecture is docs-only.
- Lane 12 protected-preview smoke can run after runtime files are committed or isolated.
- Lane 01 Repo Steward should run after implementation and QA handoffs identify exact files/hunks.

Do not run lanes in parallel when they touch the same files:

- `pocketsteel/api.py`
- `pocketsteel/curated_answers.py`
- `pocketsteel/fretboard_examples.py`
- `tests/test_api_search.py`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/integration-status.md`

## When To Stop Coding

Stop coding when:

- the slice passes focused tests and needs QA,
- the fix requires product judgment,
- dirty runtime files cannot be isolated safely,
- a protected path is needed but not explicitly approved,
- test failures are unrelated and not already classified,
- the next phase is deployment, DNS, auth policy, scraping, embeddings, or corpus work.

## Defect Routing Rules

- Backend answer quality, routing, source-card behavior, deterministic rules: Lane 05.
- Fretboard cards, tab rendering, answer layout, UI state, browser rendering: Lane 06.
- Cloudflare Access, private beta unlock, session behavior, privacy/security: Lane 11.
- Runtime restart, `/api/version`, root route, protected preview smoke: Lane 12.
- Regression matrix, smoke QA, scorer behavior, browser QA reports: Lane 15.
- Product contracts, tab/fretboard architecture, source/copyright policy: Lane 18.
- Brand assets, motion assets, logo/sign artwork: Lane 19.
- Commit splitting, exact staging, integration snapshots: Lane 01.

## After Each Lane Finishes

Every lane should produce a concise handoff under `docs/handoffs/task-completions/` with:

- what changed,
- files touched,
- checks run,
- risks,
- blockers,
- safe-to-stage files,
- files that must remain unstaged,
- recommended next lane.

Repo Steward should not infer approval from vibes. It should commit only exact approved scope or stop with a blocker handoff.
