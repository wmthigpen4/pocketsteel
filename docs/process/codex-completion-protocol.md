# Codex Completion Protocol

At the end of every task, write a markdown handoff report to:

docs/handoffs/task-completions/

Filename format:

YYYY-MM-DD-HHMM-<lane-number>-<short-task-name>.md

Examples:

2026-06-11-1430-06-hero-spacing.md
2026-06-11-1510-05-answer-routing.md
2026-06-11-1545-15-answer-eval.md

Active lanes:

- 01 Repo Steward
- 02 Corpus Pipeline
- 05 Backend / RAG Integration
- 06 UX/UI Design
- 11 Auth / Security
- 12 Self-Hosted Deployment
- 15 QA / Answer Eval
- 18 Product / Architecture
- 19 Visual Design / Assets

Each handoff must include:

## Task summary
- What was requested
- What was completed
- What was intentionally not changed

## Files changed
- Changed files
- Created files
- Deleted files
- Generated artifacts

## Tests and checks
- Exact commands run
- Results
- Tests skipped and why

## Smoke Target
Include this section before test steps whenever the task includes browser smoke, protected-preview smoke, production smoke, UI browser verification, or an API fallback used because browser tooling could not run.

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

Rules:

- If the correct URL is `/ui/steel-guitar-rag-mock.html`, do not shorten the instruction to "test app.steelguitarrag.com."
- If app root `/` is not wired, stale, or not the intended smoke target, state that explicitly.
- Browser smoke pass/fail is invalid unless the exact URL tested is recorded.
- API fallback smoke must not be reported as browser smoke.
- If protected preview requires Cloudflare Access, record whether Cloudflare Access login succeeded before protected-preview behavior was tested.
- If cache-busting is required, include the full cache-busted URL.
- If browser tooling fails and the task falls back to API requests, label the result `API fallback, not browser smoke`.
- Local `127.0.0.1` results do not prove protected-preview or production behavior.
- QA handoffs must include `URL tested` and `URL user should test`.

### Visual Smoke Evidence

For any UI-facing change, browser smoke must verify visible states, not only DOM counts, marker counts, API payloads, or console output. A handoff may say `visual pass` only when screenshot evidence exists.

Required visual evidence:

- full-page or viewport screenshot for the target state
- cropped screenshot for the changed UI region when the defect is local
- mobile/narrow screenshot when the change affects responsive layout or when mobile smoke is requested
- screenshot paths in the handoff, or an explicit statement that screenshot capture failed

If screenshots cannot be captured, report `technical pass; visual not verified` rather than `visual pass`.

Required visible-state checks for main app UI smoke:

- Q&A/search remains visible and primary
- header buttons are visible, separated, readable, and not overlapping
- source cards, fretboard cards, tab cards, or prompt chips do not dominate the primary answer unless the task explicitly intends that
- no raw internal labels, `[object Object]`, or stale cache/version hints appear

Required visible-state checks for E9 Fretboard Explorer UI smoke:

- key, scale, harmony/view, and string-group controls are visible, readable, and show the selected state
- selected string groups visibly change both the row/card/detail area and the fretboard/SVG state
- fretboard markers/clusters are visible in the expected places
- full-string lanes are absent unless the prompt or feature explicitly requests full-lane rendering
- core and advanced groups remain visually distinguishable when that feature is in scope
- raw internal labels such as implementation branch names do not appear
- console status is recorded

When the user provides a screenshot or says "make it look like X," the smoke report must compare the current screenshot against that reference. If the implementation matches technical selectors but differs visibly from the reference, report a visual failure or warning instead of a pass.

## Integration notes
- What another lane needs to know
- Schema/API/component/data contract changes
- Assumptions
- Blockers
- Human decisions needed

## Risk assessment
- Low / Medium / High
- Why
- Rollback notes, if relevant

## Commit readiness
State exactly one:
- Safe to commit
- Not ready to commit
- Needs human review first

## Suggested next step
- Which active lane should act next
- Exact recommended task/prompt for that lane

Do not commit unless explicitly instructed.
Do not stage broad dirty worktree changes.
If committing is requested, stage only files listed in the handoff report.

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
