# 04 Codex Prompt Standards

## Required Prompt Blocks

Use these blocks for stable Codex work:

- Lane
- Reasoning level
- Repo governance
- Context
- Goal
- Do / Do not
- Tests/checks
- Handoff
- Git discipline
- Final report
- What happens next

## Reasoning Levels

### Extra High

Use for cross-lane reconciliation, dirty-worktree surgery, protected-preview blockers, source/copyright architecture, auth/security, deployment decisions, and large bug clusters.

### High

Use for backend answer-routing fixes, tab/fretboard contract changes, QA matrix reconciliation, exact-hunk commit splits in shared files, and integration snapshots that affect upcoming work.

### Medium

Use for focused implementation, QA reruns, browser smoke, docs refreshes, and scoped UI fixes.

### Low

Use for exact-path docs commits, simple handoff commits, formatting cleanup, and read-only status checks.

## Approval Behavior Guidance

Codex can proceed for GREEN tasks such as docs edits, tests, read-only analysis, and small copy changes.

Codex should stop after plan/diff for YELLOW tasks unless implementation is explicitly approved. YELLOW includes broad answer routing, retrieval changes, schema changes, dependency changes, UI flow changes, and corpus-output scripts.

Codex must ask before RED actions unless the user explicitly approved that lane/task. RED includes deletion, raw corpus changes, scraper changes, embeddings/vector rebuilds, auth policy, DNS, deployment, Cloudflare Access, secrets, private transcripts, and licensing metadata.

Repo Steward auto-approval applies when QA, autopilot, or a clear handoff names exact approved files/hunks. In that case, Repo Steward should proceed with exact-path or exact-hunk staging and commit, stopping only for missing scope, contradictory scope, unsafe files, unrelated parked work, or failed checks.

## Exact-Path And Hunk Staging Expectations

- Never use `git add .`.
- Use exact paths for clean single-slice files.
- Use exact-hunk staging for shared files.
- Review `git diff --cached --name-only`.
- Review `git diff --cached`.
- Run `git diff --cached --check`.
- Keep unrelated dirty files and staged files untouched.
- Do not stage corpus-private, Chroma/vector stores, embeddings, source-inbox raw files, secrets, deployment/auth policy, or design assets unless the task explicitly names them and the lane permits it.

## Prompt Hygiene

- Do not carry stale bug checklists into unrelated tasks.
- Include object-string, raw-fragment, weak-source, or source-card regressions only when relevant to the touched area.
- API fallback must not be reported as browser smoke.
- Every browser smoke prompt or handoff must include an explicit Smoke Target block with exact URL, cache-busted URL, auth status, expected HEAD, version endpoint result, root status, and API fallback status.
