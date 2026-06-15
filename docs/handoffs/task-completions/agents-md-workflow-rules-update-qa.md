# AGENTS.md Workflow Rules Update QA

## Task Summary

- What was requested: review the `AGENTS.md` workflow-rules update using the `Lane15DesignReview` workflow and confirm it supports short workflow-driven Codex commands.
- What was completed: read `AGENTS.md`, reviewed the implementation handoff, inspected the relevant protocol diff, and verified the requested workflow and guardrail sections are present.
- What was intentionally not changed: no implementation files, app code, backend code, UI, corpus, Chroma/vector stores, auth, DNS, deployment, generated reports, staging, or commits were touched.

## Pass/Fail Decision

Pass.

`AGENTS.md` now supports the requested short workflow-driven command model and includes the requested protocol coverage:

- Lane responsibilities: present in `Active Lanes` and expanded in `Lane Operating Model`.
- Universal task start/finish rules: present as `Universal Task Start` and `Universal Task Finish`.
- `ProtectedPreviewSmoke` workflow: present.
- `Lane15DesignReview` workflow: present.
- `Lane15Smoke` workflow: present.
- `ExactPathCommit` workflow: present and scoped to Lane 01 only.
- Private corpus guardrails: present.
- Production wiring guardrails: present.
- Short-command examples: present.

## Design Review Notes

- The workflow update is consistent with the repo's human-in-the-loop model: tasks still require classification, no automatic phase jumping, exact-path staging, and no commit without explicit instruction or an approved Repo Steward/autopilot path.
- `Lane15DesignReview` correctly constrains this lane to docs/design review by default and requires a QA handoff.
- `ProtectedPreviewSmoke` correctly keeps protected-preview restart and verification owned by Lane 12, requires version checks, and clarifies that API fallback does not count as browser pass.
- `ExactPathCommit` correctly reserves commit execution for Lane 01, forbids `git add .`, and requires staged-diff review.
- The private corpus and production wiring guardrails are explicit enough to prevent accidental public routing, deployment, or generated-private-data staging from short commands.

## Files Changed

- Created:
  - `docs/handoffs/task-completions/agents-md-workflow-rules-update-qa.md`
- Reviewed:
  - `AGENTS.md`
  - `docs/handoffs/task-completions/agents-md-workflow-rules-update.md`
- Deleted:
  - None
- Generated artifacts:
  - None

## Tests And Checks

Commands run:

- `sed -n '1,260p' AGENTS.md`
  - Passed. Reviewed updated lane responsibilities, guardrails, universal workflows, named workflows, and short-command examples.
- `sed -n '260,560p' AGENTS.md`
  - Passed. Reviewed surrounding existing repo protocol for consistency.
- `sed -n '1,260p' docs/handoffs/task-completions/agents-md-workflow-rules-update.md`
  - Passed. Reviewed implementation handoff.
- `rg -n "Lane Operating Model|Universal Task Start|Universal Task Finish|ProtectedPreviewSmoke|Lane15DesignReview|Lane15Smoke|ExactPathCommit|Private Corpus Guardrails|Production Wiring Guardrails|Short-Command Examples" AGENTS.md`
  - Passed. Confirmed all requested sections are present.
- `git diff -- AGENTS.md docs/handoffs/task-completions/agents-md-workflow-rules-update.md`
  - Passed. Reviewed the scoped protocol diff.
- `git status --short`
  - Passed. Confirmed broad pre-existing dirty worktree remains; this QA task only created this handoff.
- `git diff --check`
  - Passed.
- `git diff --no-index --check -- /dev/null docs/handoffs/task-completions/agents-md-workflow-rules-update-qa.md`
  - Passed with expected exit code `1` for a new untracked file diff and no whitespace-error output.
- `git status --short -- AGENTS.md docs/handoffs/task-completions/agents-md-workflow-rules-update.md docs/handoffs/task-completions/agents-md-workflow-rules-update-qa.md`
  - Passed. Shows only the reviewed protocol file and the two handoffs in this task scope.
- `git status --short`
  - Not rerun globally after the final handoff wording tweak; scoped status was run and the broad worktree was already known to be dirty.

Skipped tests:

- Pytest, API, browser, and UI tests were skipped because this was a docs-only QA review with no executable behavior changed.

## Integration Notes

- Lane 01 can use this QA handoff plus the implementation handoff to exact-path commit the protocol update if desired.
- No schema, API, runtime, deployment, auth, UI, corpus, Chroma, or answer behavior changes are involved.
- Historical handoffs were not rewritten.

## Risk Assessment

Risk level: low.

Why:

- The reviewed change is documentation/protocol only.
- The named workflows reinforce existing repo rules instead of loosening them.
- The main risk is future over-broad interpretation of short commands, but the update includes task-specific handoff/user prompt scoping and standing protected-path guardrails.

Rollback notes:

- Revert only `AGENTS.md`, `docs/handoffs/task-completions/agents-md-workflow-rules-update.md`, and this QA handoff if the workflow language needs to be replaced.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `AGENTS.md`
- `docs/handoffs/task-completions/agents-md-workflow-rules-update.md`
- `docs/handoffs/task-completions/agents-md-workflow-rules-update-qa.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files outside the three safe-to-stage paths above.
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

Safe to commit.

## Recommended Next Lane

Recommended lane: `01 Repo Steward`.

Suggested next prompt:

```text
Lane 01: Run ExactPathCommit using docs/handoffs/task-completions/agents-md-workflow-rules-update-qa.md. Stage only AGENTS.md, docs/handoffs/task-completions/agents-md-workflow-rules-update.md, and docs/handoffs/task-completions/agents-md-workflow-rules-update-qa.md. Do not stage unrelated parked worktree files.
```
