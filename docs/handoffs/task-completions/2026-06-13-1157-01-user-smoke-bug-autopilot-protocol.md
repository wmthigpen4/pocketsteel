# User Smoke Bug Autopilot Protocol

- Branch: `feature/answer-api`
- Lane: `01 Repo Steward`
- Date: 2026-06-13
- Commit readiness: `Safe to commit`

## Task Summary

Requested: add a permanent User Smoke Bug Autopilot protocol so the user can paste one bug report and Codex can fix, validate, commit, and prepare restart verification without repeated approval prompts.

Completed:

- Added the autopilot protocol to `AGENTS.md`.
- Added the same operational protocol to `docs/process/codex-completion-protocol.md`.
- Included allowed actions, stop conditions, commit rule, required smoke target block, required final handoff fields, and one example prompt the user can paste.

Intentionally not changed:

- No implementation files were modified.
- No deployment, DNS, Cloudflare Access policy, Chroma/vector stores, embeddings, corpus-private, corpus-v2, source-inbox, scraping, provenance/legal files, generated reports, public assets, `ui/brand`, `Neon Sign`, or design assets were touched.

## Files Changed

Changed:

- `AGENTS.md`
- `docs/process/codex-completion-protocol.md`

Created:

- `docs/handoffs/task-completions/2026-06-13-1157-01-user-smoke-bug-autopilot-protocol.md`

Deleted:

- None.

Generated artifacts:

- None.

## Tests And Checks

Required checks:

```bash
git status --short
git diff --check
```

Commit checks:

```bash
git diff --cached --check
git diff --cached --name-only
```

No full pytest was run because this is a docs-only protocol update.

## Integration Notes

Future user-smoke bug reports can now opt into autopilot by saying `autopilot` or `handle this end-to-end`.

Autopilot still stops for unsafe or unclear cases, including unrelated dirty implementation files that cannot be isolated, destructive git actions, secrets/auth/DNS/corpus/vector/private-data/scraping changes, ambiguous restart commands, product judgment calls, unrelated test failures, or browser-smoke authentication blockers where API fallback is insufficient.

Schema/API/component/data contract changes: none.

Assumptions:

- This protocol is documentation/config guidance only.
- The broad dirty worktree remains parked.

Blockers:

- None for this docs-only update.

Human decisions needed:

- No immediate decision needed for this protocol commit.

## Risk Assessment

Risk: low.

Why:

- Docs-only protocol change.
- It narrows autopilot behavior with explicit stop conditions and exact-path staging requirements.

Rollback:

- Revert the docs commit if the protocol wording is too broad or too restrictive.

## Suggested Next Step

Recommended lane: `12 Self-Hosted Deployment`.

Continue with protected-preview/root-route verification for `166bf0f` or later before broader user smoke.
