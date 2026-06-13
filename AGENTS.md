# Agent Operating Model

This repo uses a human-in-the-loop workflow. Codex must classify every task before acting and must not continue into a second phase automatically unless the user explicitly approves it.

The current repo instruction is that the user-facing app name is **The Turnaround**. Many current product docs, UI files, tests, and handoffs still refer to **Steel Guitar RAG**. Do not perform a broad rename in either direction without explicit approval. Keep `pocketsteel`, `pocket-steel`, and `pocket_steel` as internal technical names unless the user explicitly approves a rename.

## Project Purpose

This project builds a steel-guitar learning/search assistant: a retrieval-augmented, source-aware answer system for pedal steel guitar. The product promise is not a generic chatbot. It should answer like a steel-guitar assistant that understands strings, frets, pedals, levers, grips, intervals, copedents, tone/gear symptoms, practice work, and forum wisdom.

The system is expected to combine:

- Steel Guitar Forum retrieval and source cards.
- Deterministic E9 rules and fretboard/copedent logic.
- Curated source/vendor registry answers.
- Private/profile-backed copedent and lesson data behind auth gates.
- Future lesson transcripts, PDFs/OCR notes, manuals, tab docs, and source-inbox material after provenance review.

## Active Lanes

Coordinate work by lane. If a task spans lanes, 01 Repo Steward should split or sequence it.

- `01 Repo Steward`: repo-wide coordination, git hygiene, commit splitting, handoff/status snapshots, integration decisions.
- `02 Corpus Pipeline`: corpus ingestion, normalization, cleaning, chunking, provenance preparation, embed preflight. Do not run scraping or embeddings unless explicitly approved.
- `05 Backend / RAG Integration`: answer-routing, RAG implementation, deterministic rules, answer contracts, source-card behavior, retrieval wiring.
- `06 UX/UI Design`: frontend presentation, answer rendering, fretboard UI, prompt chips, copy, browser smoke.
- `11 Auth / Security`: Cloudflare Access, auth modes, paywall/access-control, privacy/security reviews.
- `12 Self-Hosted Deployment`: runtime startup, private-preview operations, Cloudflare Tunnel/Pages deployment planning, protected-preview smoke.
- `15 QA / Answer Eval`: answer eval, red-team matrices, smoke scripts, browser smoke reports, regression buckets.
- `18 Product / Architecture`: product decisions, API/component contracts, answer/fretboard architecture docs.
- `19 Visual Design / Assets`: logos, brand assets, visual systems, generated images, motion/design source files.

## Standing Safety Rules

- Do not modify scraper behavior unless the user explicitly approves that RED task.
- Do not run live scraping from this repo.
- Do not delete files or data unless the user explicitly approves the exact deletion.
- Do not commit raw data, SQLite databases, credentials, logs, vector indexes, Chroma stores, embeddings, private transcripts, paid transcripts, or licensing metadata dumps.
- Preserve raw corpus data exactly as received. Derived corpus files must stay in ignored generated-output locations unless the user approves a different path.
- Do not expose private source text, private source metadata, private env values, Cloudflare tokens, or credentials.
- Do not touch `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, `source-inbox` raw files, `source-inbox/provenance.json`, `.wrangler/`, DNS/deploy secrets, `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, or generated reports unless the task explicitly names them and the lane permits it.

## Task Modes

### GREEN - Codex Can Proceed

Codex may implement and verify these tasks without stopping for approval:

- docs edits
- small UI copy changes
- tests
- evaluation scripts
- read-only analysis
- non-destructive refactors under one module

### YELLOW - Stop After Plan/Diff

Codex may inspect and propose a plan or diff, but must stop before applying or committing the change unless the user approves:

- RAG prompt changes
- chunking changes
- retrieval ranking changes
- schema changes
- dependency changes
- UI flow changes
- new scripts touching corpus outputs
- broad answer-routing changes
- corpus/source-ingestion pipeline changes

### RED - Ask Before Action

Codex must ask before taking action on:

- deleting files/data
- broad renames
- changing scraper behavior
- changing raw corpus data
- rebuilding embeddings/vector index
- modifying database migrations
- auth/payment/access-control changes
- anything affecting private transcripts or licensing metadata
- deployment, DNS, Tunnel, Cloudflare Access, or secrets changes

## Required Workflow

- Inspect current code before editing implementation. Do not patch by memory.
- Read relevant handoffs in `docs/handoffs/task-completions/` before touching overlapping lanes.
- For YELLOW or RED tasks, produce a plan/diff and stop for approval unless the user has already explicitly approved implementation.
- Do not implement a second phase automatically. For example, do not proceed from docs planning into code, code into commit, or local smoke into deployment without approval.
- Do not commit unless explicitly instructed.
- Do not use `git add .`.
- Stage exact paths only. Use hunk-level staging when overlapping lane changes share files.
- Treat `docs/handoffs/task-completions/integration-status.md` as a coordination artifact unless the user explicitly asks to commit it.
- When QA approves a scoped slice and names the approved files or hunks, Repo Steward should proceed with exact-path or exact-hunk staging and commit. Do not ask the user for another approval. If the approved scope is missing, contradictory, or includes unrelated or unsafe files, stop and write a blocker handoff instead.

## User Smoke Bug Autopilot

When the user pastes a user-smoke bug and explicitly says `autopilot` or `handle this end-to-end`, Codex should proceed without asking for repeated approval, subject to the stop conditions below.

Allowed actions:

1. Inspect current repo state.
2. Classify the bug as backend/API, UI, QA/test, deployment, docs-only, or mixed.
3. Choose the primary lane behavior internally.
4. Modify only files needed for the smallest safe fix.
5. Add or update focused regression tests.
6. Run focused tests.
7. Run broader relevant tests if the touched area requires it.
8. Run browser smoke or API fallback with an explicit `Smoke Target` block.
9. Write a handoff in `docs/handoffs/task-completions/`.
10. If tests and smoke pass, stage exact paths/hunks and commit without asking the user for another approval.
11. If protected preview restart is required and the approved restart command is documented, run it and verify.
12. Stop after restart/verify and report the exact URL the user should test.

Required `Smoke Target` block for autopilot runs:

```text
Smoke Target:
- Target type:
- Exact browser URL:
- Cache-busted URL:
- Auth required:
- Auth provider:
- Local backend URL:
- Expected backend port:
- Expected git HEAD:
- Version endpoint result:
- Root URL status:
- API fallback status:
- Exact URL the user should test:
```

Stop and write a blocker handoff instead of proceeding if:

1. The worktree has dirty implementation files unrelated to the bug and they cannot be isolated safely.
2. The fix would require destructive git actions such as reset, checkout, clean, or dropping changes.
3. The fix touches secrets, auth policy, Cloudflare Access policy, DNS, corpus, Chroma, embeddings, private source data, or scraping.
4. Tests fail and the failure is not clearly caused by the current bug.
5. The approved file/hunk scope is unclear.
6. The bug appears to require product judgment rather than implementation.
7. The restart command is missing or ambiguous.
8. Browser smoke cannot authenticate and API fallback is insufficient for the bug.

Commit rule:

- If focused tests, required smoke, and QA criteria pass, commit the scoped fix without asking the user for another approval.
- Use exact-path or exact-hunk staging.
- Never stage unrelated parked files.

Handoff requirement:

Every autopilot run must produce one final handoff with:

- bug summary
- lane classification
- files changed
- tests run
- smoke target
- smoke result
- commit hash if committed
- preview restart result if run
- exact URL the user should test
- remaining caveats
- whether user smoke can continue

Example autopilot prompt the user can paste:

```text
Autopilot: The protected preview answer for "How do I play a G chord on the E9?" shows no fretboard cards in Recommended. Handle this end-to-end. Use the current integration-status.md, keep unrelated dirty files parked, add a regression test, run focused UI/API tests and browser smoke with a Smoke Target block, commit only the scoped fix if green, and report the exact URL I should test.
```

## Required Handoff Behavior

Every task must write a markdown report to:

`docs/handoffs/task-completions/`

Use the filename format:

`YYYY-MM-DD-HHMM-<lane-number>-<short-task-name>.md`

Every handoff must include:

- Task summary: what was requested, what was completed, what was intentionally not changed.
- Files changed: changed files, created files, deleted files, generated artifacts.
- Tests and checks: exact commands run, results, skipped tests and why.
- Integration notes: what another lane needs to know, schema/API/component/data contract changes, assumptions, blockers, human decisions needed.
- Risk assessment: low/medium/high, why, rollback notes if relevant.
- Commit readiness: exactly one of `Safe to commit`, `Not ready to commit`, or `Needs human review first`.
- Suggested next step: recommended lane and exact prompt/task for that lane.

## Browser Smoke Target Clarity

Every browser smoke prompt, browser smoke handoff, protected-preview smoke report, production smoke report, or API fallback used in place of browser tooling must include this block before test steps:

```text
Smoke Target:
- Target type: local | protected-preview | production-root | API-fallback
- Result type: browser smoke | API fallback, not browser smoke
- Exact browser URL tested:
- Cache-busted URL tested:
- Exact URL the user should use:
- Auth required: yes/no
- Auth provider: Cloudflare Access / none / other
- Cloudflare Access login result: succeeded / failed / not required / not attempted
- Local backend URL:
- Expected backend port:
- Expected git HEAD:
- Version endpoint:
- Version endpoint result:
- If version endpoint missing, how version is inferred:
- Whether app root `/` works:
- Whether app root `/` is expected to work:
- Whether `/ui/steel-guitar-rag-mock.html` works:
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work:
- Who should test this URL: Codex / the user / both
- Do not test these URLs:
- Known caveats:
```

Additional rules:

- If the correct URL is `/ui/steel-guitar-rag-mock.html`, do not simply say "test app.steelguitarrag.com."
- If root `/` is not wired or is not the canonical target, say that explicitly.
- Browser smoke pass/fail is invalid unless the exact URL tested is recorded.
- API fallback smoke must not be reported as browser smoke.
- If Cloudflare Access login is required, say whether login succeeded before protected-preview behavior was tested.
- If cache-busting is needed, include the complete `?v=...` URL.
- If browser tooling fails and API fallback is used, label the result as `API fallback, not browser smoke`.
- If a result comes from local `127.0.0.1`, do not imply that it proves protected-preview or production behavior.
- Every QA handoff that includes browser smoke must include `URL tested` and `URL user should test`.

## Safe Staging And Commit Rules

- Commit only scoped, test-green, exact-path changes.
- Keep unrelated dirty worktree files parked.
- Never stage generated/private/corpus/vector/design/deploy artifacts unless the user explicitly approves that exact lane and exact paths.
- Backend answer changes and QA tooling often overlap in `pocketsteel/curated_answers.py`, `pocketsteel/answer_contracts.py`, `pocketsteel/fretboard_examples.py`, `tests/test_api_search.py`, `scripts/run_exploratory_answer_smoke.py`, and `scripts/run_product_red_team_smoke.py`. Inspect diffs carefully and patch-stage when needed.
- UI copy and UI rendering often overlap in `ui/steel-guitar-rag-mock.html` and `tests/test_frontend_answer_ui.py`. Do not mix UI-copy commits with backend/RAG commits.

## Test Expectations

- Docs-only changes: run `git diff --check`; run any existing doc lint if the repo defines one.
- Backend answer-routing/RAG changes: run focused API/search/contract/eval tests where possible, then full pytest when reasonable.
- Answer-engine changes require answer/eval tests where possible: `tests/test_api_search.py`, `tests/test_api_contract.py`, `tests/test_answer_eval.py`, `tests/test_full_answer_quality_eval.py`, and relevant smoke tests.
- QA/eval script changes: run the script’s unit tests and, when practical, the relevant smoke/eval command.
- UI changes require browser smoke where possible. At minimum run JS syntax checks and focused frontend tests.
- Fretboard/UI changes should run `node --check ui/answer-client.js`, `node --check ui/pedal-steel-fretboard.js`, and relevant frontend/fretboard tests.
- If a test is skipped, the handoff must say why.

## Answer And Product Guidance

Permanent guidance lives in:

- `docs/llm-guidance/answer-contract.md`
- `docs/llm-guidance/eval-rubric.md`
- `docs/llm-guidance/product-memory.md`
- `docs/llm-guidance/known-failures.md`

Future LLM/Codex lanes should read those files before changing answer routing, evals, UI answer rendering, product copy, or source/corpus behavior.

## Required Closeout

For every task, Codex must end with:

1. What changed
2. Tests run
3. Files touched
4. Risks
5. Human decision needed: yes/no
6. Recommended next step

If a task is YELLOW or RED, the closeout must clearly state what approval is needed before the next phase.

When the user asks for a custom closeout format, include these required fields as well as the user's requested fields.
