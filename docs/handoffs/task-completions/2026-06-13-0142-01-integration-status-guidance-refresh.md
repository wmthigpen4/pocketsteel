# Integration Status Guidance Refresh

## Task summary

- What was requested: read latest markdown handoff reports, inspect `AGENTS.md`, `docs/llm-guidance/`, `tests/answer_eval/`, and the current git diff, then create or update `docs/handoffs/task-completions/integration-status.md` for ChatGPT reset/guidance.
- What was completed: refreshed `integration-status.md` with current HEAD, latest smoke/test status from handoffs, recent lane work, overlapping dirty files, exact safe-to-stage paths, parked files, recommended lane tasks, and ready-to-paste prompts.
- What was intentionally not changed: no implementation files, tests, Chroma/vector stores, embeddings, corpus-private, corpus-v2, source-inbox raw/provenance data, scraping, provenance/legal files, deployment secrets, `.wrangler`, DNS config, `public/`, `ui/brand/`, `Neon Sign/`, or raw design assets were modified by this task.

## Files changed

- Changed files:
  - `docs/handoffs/task-completions/integration-status.md`
- Created files:
  - `docs/handoffs/task-completions/2026-06-13-0142-01-integration-status-guidance-refresh.md`
- Deleted files:
  - None
- Generated artifacts:
  - None

## Reports and guidance inspected

- Latest handoffs/read targets included:
  - `docs/handoffs/task-completions/2026-06-14-0127-05-final-red-team-blockers.md`
  - `docs/handoffs/task-completions/2026-06-14-0129-15-final-red-team-rerun.md`
  - `docs/handoffs/task-completions/2026-06-14-0132-01-integration-status-after-final-red-team.md`
  - `docs/handoffs/task-completions/2026-06-14-2356-01-invalid-chord-guardrail-commit.md`
  - `docs/handoffs/task-completions/llm-guidance-bootstrap.md`
  - `docs/handoffs/task-completions/answer-eval-question-bank.md`
  - previous `docs/handoffs/task-completions/integration-status.md`
- Guidance inspected:
  - `AGENTS.md`
  - `docs/llm-guidance/answer-contract.md`
  - `docs/llm-guidance/eval-rubric.md`
  - `docs/llm-guidance/product-memory.md`
  - `docs/llm-guidance/known-failures.md`
  - `tests/answer_eval/README.md`
  - `tests/answer_eval/expected_behaviors.md`
  - `tests/answer_eval/question_bank.jsonl`

## Tests and checks

- Exact commands run:
  - `git status --short`
  - `git diff --name-only`
  - `git diff --check`
  - `git diff --cached --name-only`
  - `find docs/handoffs/task-completions -maxdepth 1 -type f -name '*.md' -print | sort | tail -40`
  - `git branch --show-current`
  - `git rev-parse --short HEAD`
  - `git log --oneline -20`
  - `sed -n '1,260p' AGENTS.md`
  - `find docs/llm-guidance -maxdepth 1 -type f -name '*.md' -print ...`
  - `find tests/answer_eval -maxdepth 2 -type f -print ...`
  - selected `sed` reads of latest handoff reports and prior `integration-status.md`
  - `git diff --stat`
- Results:
  - Branch: `feature/answer-api`
  - HEAD: `7be3ce0 Add invalid chord symbol guardrail`
  - `git diff --check`: passed before and after the update.
  - `git diff --cached --name-only`: empty before and after the update.
  - Worktree remains broadly dirty across unrelated lanes.
- Tests skipped and why:
  - Full pytest was not run because this was documentation-only coordination work and latest handoffs already report the relevant full/test statuses.

## Integration notes

- Snapshot now includes the new LLM guidance layer and answer-eval planning bank in safe-to-stage guidance.
- Snapshot preserves exact safe-to-stage paths and keeps generated/private/source/provenance/design/deploy artifacts parked.
- Schema/API/component/data contract changes from this task: none.
- Runtime behavior changes from this task: none.
- Assumptions:
  - `integration-status.md` remains a coordination artifact unless explicitly approved for commit.
  - The broad worktree is expected and should be split with exact-path/hunk staging.

## Risk assessment

- Risk: Low.
- Why: documentation-only status refresh. The main risk is stale coordination guidance if new handoffs land before the next commit split.
- Rollback notes: revert this handoff and `docs/handoffs/task-completions/integration-status.md` if superseded by a newer snapshot.

## Commit readiness

Needs human review first

## Suggested next step

- Recommended lane: `01 Repo Steward`.
- Exact recommended prompt:

```text
LANE: 01 Repo Steward
REASONING: HIGH
Branch: feature/answer-api

Split and commit the safe backend/QA/UI/guidance chunks documented in docs/handoffs/task-completions/integration-status.md.

Do not use git add .
Do not stage corpus-private/, corpus-v2/, Chroma/vector stores, embeddings, source-inbox raw/provenance files, generated reports, .wrangler/, public/, ui/brand/, Neon Sign/, DNS/deploy/secrets files, provenance/legal files, root RAG/build scripts, landing/Cloudflare Pages files, or unrelated dirty lanes.

Before each commit:
git diff --cached --name-only
git diff --cached --check

After all commits:
.venv/bin/python -m pytest
git diff --check
```
