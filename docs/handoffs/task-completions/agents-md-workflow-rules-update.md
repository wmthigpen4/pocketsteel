# AGENTS.md Workflow Rules Update

## Task Summary

- What was requested: update `AGENTS.md` so future lane commands can be short and workflow-driven, with reusable rules for lane operating models, universal task start/finish, named workflows, private corpus guardrails, production wiring guardrails, and short-command examples.
- What was completed: revised `AGENTS.md` only for repo protocol content and created this required handoff.
- What was intentionally not changed: no app code, backend code, UI, prompts, `/api/answer`, Chroma/vector stores, SGF retrieval, auth, DNS, deployment, corpus-private, source-inbox data, generated reports, staging, or commits were touched.

## Files Changed

- Changed:
  - `AGENTS.md`
- Created:
  - `docs/handoffs/task-completions/agents-md-workflow-rules-update.md`
- Deleted:
  - None
- Generated artifacts:
  - None

## Tests And Checks

Commands run:

- `git status --short`
  - Passed before editing. Showed a broad pre-existing dirty worktree unrelated to this task.
- `sed -n '1,260p' AGENTS.md`
  - Passed for repo protocol inspection.
- `sed -n '260,620p' AGENTS.md`
  - Passed for repo protocol inspection.
- `test -f docs/handoffs/task-completions/agents-md-workflow-rules-update.md; printf '%s\n' $?`
  - Passed. Returned `1`, confirming the handoff did not exist before this task.

- `git status --short`
  - Passed after editing. Broad pre-existing dirty worktree remains; this task touched only `AGENTS.md` and this handoff.
- `git diff --check`
  - Passed.
- `git diff --no-index --check -- /dev/null docs/handoffs/task-completions/agents-md-workflow-rules-update.md`
  - Passed. Used because this handoff is new and untracked, so normal `git diff --check` does not inspect its contents.
- `git status --short -- AGENTS.md docs/handoffs/task-completions/agents-md-workflow-rules-update.md`
  - Passed. Shows only `M AGENTS.md` and `?? docs/handoffs/task-completions/agents-md-workflow-rules-update.md` for this task scope.

Skipped tests:

- Unit, browser, API, and eval tests were skipped because this was a docs-only protocol update with no executable app behavior changed.

## Integration Notes

- New reusable workflow sections in `AGENTS.md`:
  - Lane operating model.
  - Universal Task Start.
  - Universal Task Finish.
  - Named workflow: `ProtectedPreviewSmoke`.
  - Named workflow: `Lane15DesignReview`.
  - Named workflow: `Lane15Smoke`.
  - Named workflow: `ExactPathCommit`.
  - Private corpus guardrails.
  - Production wiring guardrails.
  - Short-command examples.
- Future short lane prompts can now point to a named workflow plus a handoff path instead of repeating long boilerplate.
- `ExactPathCommit` remains Lane 01 only and keeps `git add .` forbidden.
- Protected-preview verification remains Lane 12 owned and requires clear smoke target details from the task prompt or referenced handoff.

## Risk Assessment

Risk level: low.

Why:

- This is a docs/protocol-only change.
- No executable code or deployment behavior changed.
- The main risk is protocol ambiguity if future agents interpret these additions too broadly.

Rollback notes:

- Revert only the `AGENTS.md` protocol additions and this handoff if the workflow language needs to be rewritten.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `AGENTS.md`
- `docs/handoffs/task-completions/agents-md-workflow-rules-update.md`

## Files That Must Not Be Staged

- Any pre-existing dirty files outside the two safe-to-stage paths above.
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- `source-inbox/` raw data or provenance
- `.wrangler/`
- DNS/deployment secrets
- `public/`
- `ui/brand/`
- `Neon Sign/`
- generated reports or raw design assets

## Commit Readiness

Safe to commit

## Recommended Next Lane

Recommended lane: `01 Repo Steward`.

Suggested next step: if this protocol update is accepted, Lane 01 can run `ExactPathCommit` for `AGENTS.md` and `docs/handoffs/task-completions/agents-md-workflow-rules-update.md` only.
