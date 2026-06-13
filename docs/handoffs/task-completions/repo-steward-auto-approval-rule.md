# Repo Steward Auto-Approval Rule

## Task summary

- Requested: update repo protocol so Repo Steward stops asking for routine commit/staging approval after QA, autopilot, or a clear handoff has already approved a scoped slice.
- Completed: added an explicit Repo Steward auto-approval rule, stop conditions, bad/good behavior examples, and required blocker-handoff behavior.
- Intentionally not changed: no implementation files, tests, deployment, auth policy, Cloudflare Access policy, corpus, Chroma/vector stores, embeddings, scraping, source data, source-inbox data, generated artifacts, or design assets.

## Files changed

Changed:

- `AGENTS.md`
- `docs/process/codex-completion-protocol.md`

Created:

- `docs/handoffs/task-completions/repo-steward-auto-approval-rule.md`

Deleted:

- None.

Generated artifacts:

- None.

## Exact rule added

Repo Steward should not ask the user for approval when a slice has already been approved by QA, an `AUTOPILOT USER SMOKE BUG` run, an `AUTOPILOT USER SMOKE ADJUSTMENT` run, or a clear handoff that names the approved files/hunks.

When the approved scope is clear, Repo Steward proceeds with status inspection, exact approved path/hunk staging, staged-diff checks, scoped commit, Repo Steward handoff, and integration-status refresh if required.

Required wording:

```text
Proceeding under Repo Steward auto-approval because QA/autopilot approved the slice and the file scope is clear.
```

Stop conditions were added for missing/contradictory scope, unrelated parked work in the staged diff, secrets/private/corpus/vector/source/deploy/auth-policy hazards, destructive git needs, failed checks, product decisions, and unclear dirty runtime files.

If stopped, Repo Steward must write an exact blocker handoff instead of asking vague approval questions.

## Tests and checks

Run:

```bash
git status --short
git diff --check
```

Result:

- `git diff --check`: passed before editing.
- Final staged checks are run by Repo Steward before commit.

## Integration notes

- This is docs/protocol guidance only.
- The rule is mirrored in `AGENTS.md` and `docs/process/codex-completion-protocol.md`.
- Existing broad dirty worktree lanes remain parked and unrelated to this docs-only commit.

## Risk assessment

Risk: low.

Why: documentation-only change clarifying existing workflow intent. It reduces approval loops but keeps explicit stop conditions for unsafe or unclear commits.

Rollback notes: revert the docs commit if the workflow should return to explicit approval before every Repo Steward commit.

## Commit readiness

Safe to commit.

## Suggested next step

Recommended lane: `01 Repo Steward`.

Commit this docs-only protocol update with:

```text
docs: auto-approve scoped repo steward commits
```
