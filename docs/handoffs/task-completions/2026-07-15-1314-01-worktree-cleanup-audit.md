# Repo Steward Worktree Cleanup Audit

## Task summary

- Requested: scan the repository for dirty files, uncommitted work, and related Git clutter, then clean up what is safe.
- Lane: `01 Repo Steward`.
- Task type: mixed Git hygiene and documentation.
- Task mode: GREEN for read-only inspection and the non-destructive ignore correction; RED cleanup candidates were left untouched because exact deletion, stash-drop, worktree-removal, protected-path, and deployment authorization was not provided.
- Current branch and HEAD: `feature/answer-api` at `3cb63c3e739c1492634db24588173c9cb89bb2e0`.
- Completed: added exact ignore rules for generated corpus/vector output and the protected source provenance file. This reduced visible untracked paths from `1,837` to `449` before this handoff was created, without deleting, moving, staging, stashing, or committing any work.
- Intentionally not changed: all pre-existing tracked edits, coordination docs, protected assets, source/corpus work, private helper code, stashes, detached runtime worktrees, and Git history.

## Scan results

- Index changes: `0`.
- Unmerged/conflicted paths: `0`.
- Worktree deletions: `0`.
- Pre-existing tracked modifications: `17`.
- Visible untracked paths before cleanup: `1,837`.
- Visible untracked paths after the ignore correction and before this handoff: `449`.
- Correctly reclassified as ignored: `1,388` paths.
- Remaining visible untracked size: about `800M`, dominated by protected/raw design and public-brand assets.
- Stashes: `4`, all named parked runtime/frontend cleanup from June 13. They contain substantive source, UI, test, ingestion, and private/corpus-adjacent work and were not dropped.
- Git worktrees: `61` total, including this primary worktree and `60` detached runtime worktrees. `git worktree prune --dry-run --verbose` found no stale/prunable metadata.
- Remote state: the branch has no configured upstream. The local HEAD is `461` commits ahead and `0` behind the existing `origin/feature/answer-api` remote-tracking ref at `f05dc6d`; no fetch or push was performed.
- Object database: no garbage reported; `git count-objects -vH` reported `0 bytes` of garbage.

## Files changed

- Modified: `.gitignore`
  - Added `data/clean/`.
  - Added `data/chunks/`.
  - Added `data/rag/chroma/`.
  - Added `source-inbox/provenance.json`.
- Created: `docs/handoffs/task-completions/2026-07-15-1314-01-worktree-cleanup-audit.md`.
- Deleted files: none.
- Moved files: none.
- Generated artifacts: none.

## Remaining parked work

The remaining tracked modifications are not one commit-ready slice:

- Source policy/registry and source-inbox inventory work: `README.md`, `corpus_metadata/source_policies/README.md`, `corpus_metadata/source_registry.json`, `docs/copyright-provenance.md`, `docs/corpus-license-policy.md`, `docs/source-inbox-inventory.md`, and `source-inbox/inventory.json`.
- Old RAG/corpus pipeline work: `rag_answer.py`, `rag_build_clean_corpus.py`, `rag_chunk_corpus.py`, and `rag_embed_chroma.py`.
- Parked operations/coordination docs: `docs/cloudflare-pages-landing.md`, `docs/current-commands.md`, `docs/handoffs/task-completions/integration-status.md`, and `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`.
- Protected visual assets: `ui/brand/steel-guitar-rag-landing-alpha.webm` and `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`.

The remaining untracked paths include historical handoffs/product docs, `Neon Sign/`, `public/`, deployment assets, private-lesson helper scripts, scraper/forum files, source-policy configs, and two UI image assets. These cannot be safely committed, ignored, archived, or deleted as one bundle.

## Tests and checks

- `git status --short --branch`: completed.
- `git diff --stat` and `git diff --numstat`: completed.
- `git diff --name-only --diff-filter=U`: no conflicts.
- `git stash list` and exact stash stats: completed; no stash changed.
- `git worktree list --porcelain`: completed.
- `git worktree prune --dry-run --verbose`: no prunable worktrees.
- `git check-ignore -v data/clean data/chunks data/rag/chroma source-inbox/provenance.json`: all four exact rules verified.
- `git diff --check`: passed.
- Runtime tests: skipped because no runtime implementation changed.
- Browser/deployment smoke: skipped because no runtime or deployment action was authorized or performed.

## Integration notes

- The latest feature work is already committed; current HEAD is `3cb63c3`.
- The visible dirty state is primarily intentional parked history and protected material, not a single forgotten feature commit.
- The four stashes overlap older runtime/UI/corpus work and must not be dropped without a dedicated comparison against current HEAD.
- The detached worktrees are real runtime worktrees, not stale metadata; removing them is a deployment/runtime cleanup action.
- `integration-status.md` remains a modified coordination artifact and was not staged.

## Risk assessment

- Risk: low for the applied ignore correction. It is non-destructive and aligns generated corpus/vector output and protected provenance with standing repository policy.
- Remaining cleanup risk: high if handled broadly. `git clean`, stash drops, worktree removals, broad staging, or bulk asset deletion could destroy protected or intentionally parked work.
- Rollback for the applied change: remove only the four added `.gitignore` lines.

## Human decision needed

- Yes.
- Exact decision required before a fully clean status can be pursued: identify which specific parked tracked/untracked slice should be committed versus discarded, and explicitly authorize any exact cache deletion, stash drop, detached worktree removal, design/public asset deletion, or protected-path cleanup. Broad cleanup commands are not safe here.

## Safe-to-stage exact file list

- `.gitignore`
- `docs/handoffs/task-completions/2026-07-15-1314-01-worktree-cleanup-audit.md`

## Files that must not be staged

- Every other currently modified or untracked path.
- In particular: `source-inbox/`, `data/`, `public/`, `ui/brand/`, `Neon Sign/`, private-lesson helper files, scraper/forum files, corpus/vector output, deployment assets, and `docs/handoffs/task-completions/integration-status.md`.

## Recommended next lane

- `01 Repo Steward`, after the user supplies an exact keep/commit/discard decision for one parked slice at a time.

## Commit readiness

Needs human review first

## Suggested next step

- Review and, if desired, commit only the two safe cleanup documentation paths above. Then choose one exact follow-up: reconcile the old source/RAG slice, audit the four stashes, or authorize removal of named runtime worktrees/assets. Do not combine those scopes.
