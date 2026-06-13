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
- Exact URL Cory should use:
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
- Who should test this URL: Codex / Cory / both
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

Repo Steward commit rule: when QA approves a scoped slice and names the approved files or hunks, Repo Steward should proceed with exact-path or exact-hunk staging and commit. Do not ask Cory for another approval. If the approved scope is missing, contradictory, or includes unrelated or unsafe files, stop and write a blocker handoff instead.

## User Smoke Bug Autopilot

When Cory pastes a user-smoke bug and explicitly says `autopilot` or `handle this end-to-end`, Codex should proceed without asking for repeated approval, subject to the stop conditions below.

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
10. If tests and smoke pass, stage exact paths/hunks and commit without asking Cory for another approval.
11. If protected preview restart is required and the approved restart command is documented, run it and verify.
12. Stop after restart/verify and report the exact URL Cory should test.

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
- Exact URL Cory should test:
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

- If focused tests, required smoke, and QA criteria pass, commit the scoped fix without asking Cory for another approval.
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
- exact URL Cory should test
- remaining caveats
- whether user smoke can continue

Example autopilot prompt Cory can paste:

```text
Autopilot: The protected preview answer for "How do I play a G chord on the E9?" shows no fretboard cards in Recommended. Handle this end-to-end. Use the current integration-status.md, keep unrelated dirty files parked, add a regression test, run focused UI/API tests and browser smoke with a Smoke Target block, commit only the scoped fix if green, and report the exact URL I should test.
```
