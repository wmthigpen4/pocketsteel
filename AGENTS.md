# Agent Operating Model

This repo uses a human-in-the-loop workflow. Codex must classify every task before acting. For a new feature, the user approves the feature scope once; that approval authorizes the normal end-to-end Autopilot loop through implementation, tests, exact-path commits, protected-preview update, automated smoke, and the user-smoke handoff. Ask again only when the work expands beyond the approved scope or reaches an unapproved RED action.

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

## Lane Operating Model

Use these lane defaults when the user gives a short workflow command. Task-specific handoffs, smoke docs, or user instructions override lane defaults only within the named scope.

- `01 Repo Steward`: owns exact-path staging, commit splitting, integration-status refreshes, dirty-worktree triage, and final commit hygiene. Lane 01 must never use `git add .` and must not commit product decisions or unclear scopes.
- `05 Backend / RAG Integration`: owns answer routing, deterministic rules, answer contracts in code, retrieval orchestration, source-card behavior, backend API behavior, and feature-flagged backend integrations. Broad answer-routing, retrieval, Chroma, SGF, or prompt changes are YELLOW unless the user explicitly approves implementation.
- `06 UX/UI Design`: owns answer presentation, frontend rendering, fretboard UI, prompt chips, copy, responsive layout, and browser smoke for UI behavior. UI changes require focused frontend checks and browser smoke when practical.
- `11 Auth / Security`: owns Cloudflare Access, auth modes, privacy/security review, access-control decisions, secrets handling guidance, and private-data exposure review. Auth/security changes are RED unless explicitly approved.
- `12 Self-Hosted Deployment`: owns runtime startup, protected-preview restart/verification, Cloudflare Tunnel/Pages deployment planning, version verification, and deployment smoke. Deployment, DNS, Tunnel, Access, and secrets actions are RED unless explicitly approved.
- `15 QA / Answer Eval`: owns answer evals, red-team matrices, smoke scripts, regression buckets, browser smoke reports, and QA design review. Lane 15 verifies behavior and writes QA handoffs; it does not implement product/code changes unless explicitly asked.
- `18 Product / Architecture`: owns product decisions, API/component contracts, answer/fretboard architecture docs, routing policy design, and cross-lane implementation recommendations. Lane 18 should not implement runtime behavior unless explicitly instructed.
- `19 Visual Design / Assets`: owns brand assets, visual systems, generated images, motion/design source files, and visual design directions. Do not touch `ui/brand/`, `Neon Sign/`, raw design assets, or generated visual artifacts unless the task explicitly names them.

## Standing Safety Rules

- Do not modify scraper behavior unless the user explicitly approves that RED task.
- Do not run live scraping from this repo.
- Do not delete files or data unless the user explicitly approves the exact deletion.
- Do not commit raw data, SQLite databases, credentials, logs, vector indexes, Chroma stores, embeddings, private transcripts, paid transcripts, or licensing metadata dumps.
- Preserve raw corpus data exactly as received. Derived corpus files must stay in ignored generated-output locations unless the user approves a different path.
- Do not expose private source text, private source metadata, private env values, Cloudflare tokens, or credentials.
- Do not touch `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, `source-inbox` raw files, `source-inbox/provenance.json`, `.wrangler/`, DNS/deploy secrets, `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, or generated reports unless the task explicitly names them and the lane permits it.

## Private Corpus Guardrails

- `corpus-private/` must remain uncommitted.
- Generated private JSONL files, eval outputs, reports, and derived private artifacts must remain ignored unless the user explicitly approves exact paths.
- Private-review guidance must not be exposed as public source material.
- Do not use broad staging around private or generated corpus material.
- Do not add public answer routing for private material without explicit protected-preview/auth design and approval.
- Do not copy large private guidance bodies into prompts, answers, source cards, handoffs, or smoke reports.
- Private/profile-backed material must stay behind the correct auth and review controls.

## Production Wiring Guardrails

- Do not modify `/api/answer`, Chroma/vector stores, SGF retrieval, UI rendering, auth, DNS, deployment, or Cloudflare configuration unless the task explicitly says so.
- Feature flags for private, experimental, protected-preview, or retrieval-related work must default off.
- Public production behavior must not change as a side effect of docs, QA, protected-preview, or private-review work.
- API fallback does not prove browser behavior, protected-preview UI behavior, or Cloudflare Access behavior.
- Do not deploy, restart protected preview, change DNS, or touch secrets unless the user explicitly approves that lane/task.

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

- Every lane task must start with the Universal Task Start checklist below.
- Every lane task must finish with the Universal Task Finish checklist below.
- Inspect current code before editing implementation. Do not patch by memory.
- Read relevant handoffs in `docs/handoffs/task-completions/` before touching overlapping lanes.
- For YELLOW or RED tasks, produce a plan/diff and stop for approval unless the user has already explicitly approved implementation.
- Do not enter a materially different or expanded phase automatically. Within an approved Autopilot feature scope, proceed from design to code, tests, exact-path commit, protected-preview update, and automated smoke without repeated approval.
- Do not commit unless explicitly instructed or the user has approved an Autopilot feature/bug-fix scope that includes the normal exact-path commit loop.
- Do not use `git add .`.
- Stage exact paths only. Use hunk-level staging when overlapping lane changes share files.
- Treat `docs/handoffs/task-completions/integration-status.md` as a coordination artifact unless the user explicitly asks to commit it.

## Steel Guitar RAG Autopilot Mode

When the user asks for a feature or bug fix, default to an end-to-end Autopilot Feature Run unless the request explicitly says to plan only, inspect only, or stop before implementation. Do not make the user approve each internal lane transition. Use lanes as internal phases, keep the scope tight, and stop only for the stop conditions below.

Lane ownership during autopilot:

- Lane 05 owns backend, RAG, API, answer routing, and answer contract work.
- Lane 06 owns UI, fretboard, tab rendering, browser behavior, and frontend smoke.
- Lane 15 owns QA, regression, eval, and smoke verification.
- Lane 01 owns exact-path staging, commit hygiene, dirty-worktree protection, and integration refresh.
- Lane 12 owns protected-preview restart and smoke after committed runtime changes.
- Lane 18 owns product, API, source, and copyright architecture when product judgment or contract design is needed.

Autopilot lifecycle:

1. Inspect repo guidance and git state.
2. Plan the smallest safe slice.
3. Implement the feature or fix.
4. Run focused tests and checks.
5. Run local API or browser smoke when relevant.
6. Stage exact intended files or hunks only.
7. Commit the completed scope.
8. Restart or update protected preview when the approved feature scope includes the normal protected-preview loop and the documented command is safe; otherwise stop before deployment.
9. Run protected-preview smoke for runtime or user-facing changes.
10. Refresh `docs/handoffs/task-completions/integration-status.md`.
11. Return one pass/warn/fail report.

User-facing runtime changes are not done until protected-preview smoke is recorded. After automated protected-preview smoke passes, mark the build ready for user smoke. User smoke comes after Codex implementation, tests, commit, protected-preview update, and protected-preview smoke. A failed user-smoke report becomes the next autopilot bug-fix run.

Autopilot stop conditions:

- RED actions are needed and were not explicitly authorized.
- Product judgment is required before implementation can be correct.
- Dirty runtime state is unsafe or cannot be isolated from the requested slice.
- Tests fail for unrelated reasons that cannot be classified.
- The work would touch auth, DNS, secrets, scraping, embeddings, vector rebuilds, raw corpus, private transcripts, source-inbox raw/provenance data, paid transcript/licensing material, or Cloudflare policy without explicit authorization.

Protected-preview smoke requirements:

- Record the exact cache-busted URL.
- Record the auth result.
- Record the expected `HEAD`.
- Record `/api/version` result when available.
- Record root `/` behavior.
- Record `/ui/steel-guitar-rag-mock.html` behavior.
- Record API fallback status.
- State explicitly that API fallback is not browser smoke.

### Universal Task Start

At the start of every lane task:

1. Read `AGENTS.md`.
2. Read the user-specified handoff, workflow file, or latest relevant handoff for the lane.
3. Run `git status --short`.
4. Identify whether the task is docs-only, code, QA, deployment, commit, or mixed.
5. Identify the lane and task mode: GREEN, YELLOW, or RED.
6. Respect no-stage/no-commit unless the user explicitly instructed staging or committing.
7. Name any protected paths or unrelated dirty files that constrain the work.

### Universal Task Finish

At the end of every lane task:

1. Write a markdown handoff under `docs/handoffs/task-completions/`.
2. Run the required checks for the task type, including `git diff --check` for docs-only changes.
3. Run `git status --short` after changes.
4. Do not stage or commit unless explicitly instructed or an approved autopilot/Repo Steward rule applies.
5. In the final response, report the handoff path, checks run, files touched, risks, human decisions needed, and recommended next lane.

Every handoff must include:

- task summary,
- files changed,
- tests/checks run,
- risks,
- human decision needed,
- safe-to-stage exact file list,
- files that must not be staged,
- recommended next lane,
- commit readiness.

## Named Workflows

Short workflow commands should rely on these standing rules plus the referenced handoff or user prompt for task-specific details.

### ProtectedPreviewSmoke

Lane ownership: `12 Self-Hosted Deployment`.

Standing rules:

- Lane 12 owns protected-preview restart and verification.
- Do not modify files unless explicitly requested.
- Do not stage or commit.
- Read deployment/preview docs and the referenced smoke or readiness handoff.
- Run `git status --short` before and after.
- Verify current `HEAD`.
- Verify `/api/version` matches expected `HEAD`.
- API fallback does not count as a browser pass.
- Cloudflare Access browser smoke is required when the task or handoff specifies it.
- Stop before restart if dirty runtime-affecting files are present and cannot be isolated.
- Write a root/user-smoke verification handoff.

The task prompt or referenced handoff must provide:

- exact smoke URL,
- fallback URL,
- version query string,
- prompt list,
- feature-specific pass criteria.

### Lane15DesignReview

Lane ownership: `15 QA / Answer Eval`.

Standing rules:

- Docs/design review only unless explicitly told otherwise.
- Do not change code.
- Do not stage.
- Do not commit.
- Read the referenced design handoff and relevant product/answer guidance.
- Verify design guardrails, protected paths, auth/private-data constraints, source-card behavior, and next-lane readiness.
- Write a QA handoff under `docs/handoffs/task-completions/`.

### Lane15Smoke

Lane ownership: `15 QA / Answer Eval`.

Standing rules:

- Run the tests and smoke checks specified by the user prompt or referenced handoff.
- Inspect relevant handoffs before running checks.
- Verify feature flag behavior when the feature is flag-gated.
- Verify no unintended production, deployment, auth, corpus, Chroma, SGF, or UI changes occurred.
- Include the Browser Smoke Target block when browser smoke or API fallback is involved.
- Write a smoke/QA handoff under `docs/handoffs/task-completions/`.

### ExactPathCommit

Lane ownership: `01 Repo Steward` only.

Standing rules:

- Use only when a QA/autopilot/user-approved handoff names exact files or hunks to commit.
- Never use `git add .`.
- Stage only exact files or hunks approved by the QA handoff.
- Leave unrelated dirty files untouched.
- Run `git diff --cached --check`.
- Review `git diff --cached --name-only`.
- Review the cached diff before committing.
- Commit only after exact-path review confirms no unrelated files, secrets, credentials, private data, Chroma/vector data, corpus/source data, scraping outputs, deployment changes, auth changes, or generated artifacts are staged without explicit approval.
- Write a Repo Steward handoff after the commit attempt, whether it succeeds or stops on a blocker.

## Short-Command Examples

- `Lane 15: Run Lane15DesignReview for docs/handoffs/task-completions/curated-guidance-routing-design.md.`
- `Lane 12: Run ProtectedPreviewSmoke using docs/handoffs/task-completions/<file>.md with version <version>.`
- `Lane 01: Run ExactPathCommit using docs/handoffs/task-completions/<qa-file>.md.`
- `Lane 15: Run Lane15Smoke using docs/handoffs/task-completions/<smoke-plan>.md.`
- `Lane 18: Update the product contract using docs/handoffs/task-completions/<design-input>.md.`

## Repo Steward Auto-Approval Rule

Repo Steward should not ask the user for approval when a slice has already been approved by QA, an `AUTOPILOT USER SMOKE BUG` run, an `AUTOPILOT USER SMOKE ADJUSTMENT` run, or a clear handoff that names the approved files/hunks.

When the approved scope is clear, Repo Steward must proceed with:

1. Inspect current git status.
2. Identify the approved files/hunks from the handoff.
3. Identify unrelated dirty/parked files.
4. Stage exact approved paths or hunks only.
5. Run required staged-diff checks.
6. Commit with the agreed scoped commit message.
7. Write a Repo Steward handoff.
8. Update `integration-status.md` if the protocol requires a refresh.

Repo Steward should say what it is about to do, but should not stop for user approval. Use this wording:

> Proceeding under Repo Steward auto-approval because QA/autopilot approved the slice and the file scope is clear.

Stop and write a blocker handoff only if:

1. The approved file/hunk list is missing.
2. The approved file/hunk list is contradictory.
3. The staged diff includes unrelated parked work.
4. The staged diff includes secrets, tokens, credentials, env files, private data, Chroma/vector data, corpus/source data, scraping outputs, or deployment/auth policy changes not explicitly approved.
5. The diff requires destructive git actions such as reset, checkout, clean, deleting files, or dropping changes.
6. Tests/checks fail.
7. The task is a product decision rather than a scoped commit.
8. Dirty runtime files make it unclear what should be committed.

If a stop condition is hit, Repo Steward should not ask vague approval questions. It should write the exact blocker, exact files involved, why auto-approval could not proceed, and the proposed safe next step.

Bad Repo Steward behavior when QA/autopilot has already approved the scoped slice:

- Do not say "Human decision needed: approve commit?"
- Do not say "Should I proceed?"
- Do not say "Waiting for approval."
- Do not say "Would you like me to commit this?"

Good Repo Steward behavior:

- "QA approved this scoped slice. Proceeding with exact-hunk staging."
- "Auto-approval applies. Staging only the approved files."
- "Stopped because the approved scope conflicts with dirty parked files."

## Prompt Hygiene And Privacy

- Do not carry every historical bug, caveat, or stale checklist item forward into every new task.
- Historical regression checks should appear only when relevant to the touched area or smoke target.
- Object-string rendering checks belong in broad browser smoke, UI rendering, answer-card/source-card/fretboard rendering, and regression suites. Do not repeat them in metadata-only, docs-only, corpus-registry, privacy-cleanup, or backend-only prompts unless that backend change affects rendered structured output.
- Weak-source warnings and raw source fragments belong in answer-composer/browser-smoke QA, not every task.
- Do not include stale checklist items just because they appeared in earlier prompts.
- Do not refer to the user by personal name in prompts, handoffs, UI text, docs, source notes, or smoke reports. Use "the user," "you," or neutral phrasing.
- If local filesystem paths expose a personal username, prefer path-neutral forms such as `~/Documents/Pocket Steel` in documentation and handoffs where executable precision is not required.

## User Smoke Bug Autopilot

When the user provides an `AUTOPILOT USER SMOKE BUG`, `AUTOPILOT USER SMOKE ADJUSTMENT`, or explicitly says `autopilot` or `handle this end-to-end`, Codex should proceed without asking for repeated approval, subject to the stop conditions below.

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
11. After a successful autopilot fix and commit, update `docs/handoffs/task-completions/integration-status.md`.
12. If protected preview restart is explicitly required by the task and the approved restart command is documented, run it and verify.
13. Stop after restart/verify and report the exact URL the user should test.

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

1. The worktree has dirty runtime or implementation files unrelated to the bug and they cannot be isolated safely.
2. The fix would require destructive git actions such as reset, checkout, clean, or dropping changes.
3. The fix touches secrets, auth policy, Cloudflare Access policy, DNS, corpus, Chroma, embeddings, private source data, source-inbox, or scraping.
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

After a successful autopilot fix and commit, the integration-status refresh must include:

- current HEAD
- bug or adjustment summary
- commit hash
- files committed
- tests run
- smoke target
- smoke result
- protected-preview restart status if run
- exact URL the user should test
- whether user smoke may continue
- remaining caveats
- dirty worktree summary
- parked files

Do not mix the implementation commit and integration-status refresh in the same commit unless the existing repo protocol explicitly allows it.

## User Smoke Freeze

During user smoke testing, do not start broad feature development.

Allowed during the freeze:

- smoke-blocking bug fixes
- small smoke-readiness adjustments
- tests for observed failures
- protected-preview verification
- exact scoped commits

Park during the freeze:

- new major features
- auth/paywall changes
- corpus/Chroma/scraping changes
- broad visual redesign
- deployment architecture changes
- large refactors

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
- Human decision needed: yes/no, with exact decision if yes.
- Safe-to-stage exact file list, or `None`.
- Files that must not be staged.
- Recommended next lane.
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
