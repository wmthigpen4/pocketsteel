# AGENTS Autopilot Mode Update

## Pass / Warn / Fail

Pass.

## Task Summary

Added a concise `Steel Guitar RAG Autopilot Mode` section to the primary repo instruction file so future feature and bug-fix prompts can run end to end without repeated approvals at each internal lane transition.

The update defines lane ownership, lifecycle, stop conditions, and protected-preview smoke requirements.

## Files Changed

- `AGENTS.md`
- `docs/handoffs/task-completions/2026-06-25-1836-01-agents-autopilot-mode.md`

## Checks Run

- `git diff --check`: passed before staging.
- `git diff --cached --name-only`: reviewed exact docs-only staged file list.
- `git diff --cached`: reviewed exact docs-only staged diff.
- `git diff --cached --check`: passed.

No app test suite was run because this is a docs-only repo-instruction update.

## Risks

Low. The patch is limited to repo workflow instructions and a handoff. It does not modify backend, UI, tests, deployment, auth, DNS, corpus, embeddings, Chroma/vector stores, secrets, or private transcript files.

Primary behavioral risk: future sessions may interpret feature/bug prompts as end-to-end autopilot by default. The added stop conditions preserve RED guardrails and product-judgment stops.

## Blockers

None.

## Safe-To-Stage Exact File List

- `AGENTS.md`
- `docs/handoffs/task-completions/2026-06-25-1836-01-agents-autopilot-mode.md`

## Files Intentionally Left Unstaged

- `agents.md`
- Existing unrelated dirty README/docs/provenance/source-policy files.
- Existing corpus metadata and source-inbox metadata.
- Existing root RAG helper scripts.
- Existing brand/design/generated asset files.
- Any backend, UI, tests, deployment, auth, DNS, corpus, embeddings, Chroma/vector stores, secrets, private transcript, paid transcript, or source-inbox raw/provenance files.

## Human Decision Needed

No.

## Recommended Next Action

Use short future prompts such as:

```text
Use AGENTS.md autopilot mode.

Feature/bug:
[describe the work]

You are authorized to implement, test, commit, protected-preview smoke, and refresh integration status unless a RED guardrail is hit.
```

## Final Commit Hash

Reported in the final closeout after commit. The hash cannot be embedded in the same committed handoff without changing the commit hash.

## Commit Readiness

Safe to commit if staged-diff checks pass.
