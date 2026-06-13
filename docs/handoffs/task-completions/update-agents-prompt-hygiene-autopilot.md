# Prompt Hygiene And Autopilot Protocol Update

## Task Summary

Requested:

- Tighten repo protocol guidance so future user-smoke work is less approval-heavy, less noisy, and clearer about exact smoke targets.
- Update `AGENTS.md` and duplicated completion-protocol guidance.
- Keep the task documentation-only.

Completed:

- Tightened User Smoke Bug Autopilot triggers to cover both bug and adjustment reports.
- Clarified Repo Steward should proceed without another approval when QA has approved a clear scoped slice.
- Added prompt hygiene rules so stale historical checks are not copied into unrelated tasks.
- Added privacy wording requiring neutral references to the user and path-neutral docs where executable precision is not needed.
- Added user-smoke freeze rules that park broad feature work during smoke testing.
- Clarified the integration-status refresh required after a successful autopilot fix and commit.

Intentionally not changed:

- No implementation files, UI runtime files, deployment files, DNS/auth settings, corpus/source data, Chroma/vector stores, embeddings, source-inbox data, generated reports, or design assets were modified.
- `docs/handoffs/task-completions/integration-status.md` was read for context but not changed.

## Files Changed

Changed:

- `AGENTS.md`
- `docs/process/codex-completion-protocol.md`

Created:

- `docs/handoffs/task-completions/update-agents-prompt-hygiene-autopilot.md`

Deleted:

- None.

Generated artifacts:

- None.

## Tests And Checks

Run:

```bash
git status --short
git diff --check
```

Results:

- `git status --short` confirmed the broad pre-existing dirty worktree remains, with this task scoped to the protocol docs and this handoff.
- `git diff --check` passed.

Skipped:

- Full pytest was not run because this is a documentation/protocol-only update.

## Integration Notes

- Future Repo Steward tasks should not ask for another approval after QA approves a scoped slice and names exact files or hunks.
- Future autopilot tasks should update `integration-status.md` after a successful scoped commit, but should not mix that coordination refresh into the implementation commit unless repo protocol explicitly allows it.
- Future prompts and handoffs should avoid stale historical regression checklists unless relevant to the touched area or smoke target.
- Future browser smoke prompts and reports should include the explicit `Smoke Target` block and exact URL the user should test.

Schema/API/component/data contract changes:

- None.

Assumptions:

- This is a docs-only protocol change.
- Existing broad dirty worktree files remain parked and should not be staged with this task.

Blockers:

- None.

Human decisions needed:

- No.

## Risk Assessment

Risk: low.

Why:

- The change is documentation-only and narrows future agent behavior with clearer stop conditions, staging rules, prompt hygiene, and smoke-target requirements.

Rollback:

- Revert the docs commit if the protocol becomes too restrictive or too permissive.

## Commit Readiness

Safe to commit

## Suggested Next Step

Recommended lane: `01 Repo Steward`.

Exact task:

```text
Continue user-smoke coordination from the latest integration-status snapshot. Keep broad dirty lanes parked, use exact-path staging only, and follow the tightened autopilot/prompt-hygiene protocol.
```
