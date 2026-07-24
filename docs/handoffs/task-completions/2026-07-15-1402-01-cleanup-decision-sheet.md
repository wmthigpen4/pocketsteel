# Repo Cleanup Decision Sheet

## Task summary

- Requested: explain the remaining cleanup decisions in an easy, actionable format.
- Lane: `01 Repo Steward`.
- Task type and mode: read-only Git hygiene analysis (GREEN), with proposed protected/deletion/deployment-adjacent actions that remain RED until the user chooses them.
- Current branch and HEAD: `feature/answer-api` at `3cb63c3e739c1492634db24588173c9cb89bb2e0`.
- No file, stash, worktree, deployment, or remote state was changed in this decision pass other than creating this handoff.

## Recommended default package

The user can authorize the complete recommended package by replying exactly:

> Use the recommended cleanup defaults.

That reply authorizes only the following bounded actions:

1. Commit the reviewed cleanup ignore rules and the two cleanup handoffs with exact-path staging.
2. Remove the 59 clean, inactive, unlocked runtime worktrees listed below while retaining the active protected-preview worktree `3cb63c3-playing-context` and the primary repository worktree.
3. Delete only the exact regenerable cache paths, two unused UI images, and four byte-identical public-brand duplicates listed below.
4. Preserve raw design masters locally and add narrow ignore rules for `Neon Sign/`, the accidental quoted Neon log tree, and named public-brand source/master exports. Do not delete those masters.
5. Preserve the remaining tracked and untracked work in clearly named, exact-scope local stashes by category; do not commit or discard the old RAG/source, protected visual, private-helper, scraper/forum, deployment, or bulk handoff work.
6. Keep the four existing June 13 stashes until a separate audit proves each is superseded.
7. Do not push, deploy, restart, change auth/DNS/secrets, scrape, rebuild embeddings, or modify corpus/private/source content.

## Decisions and recommendations

### 1. Cleanup commit

- Decision: commit the safe ignore correction and cleanup records now, or leave them dirty.
- Recommendation: **Commit**.
- Exact scope: `.gitignore`, `2026-07-15-1314-01-worktree-cleanup-audit.md`, and this decision handoff.
- Impact: one small documentation/Git-hygiene commit; no runtime behavior changes.

### 2. Inactive runtime worktrees

- Decision: remove or retain 59 detached runtime worktrees.
- Evidence: all 59 are present, clean, unlocked, and have no tracked modifications. The active listener on port `8770` uses `~/.steel-rag/runtime/3cb63c3-playing-context`, which is excluded.
- Recommendation: **Remove the 59 inactive worktrees; keep the active one**.
- Estimated savings: about `9.1 GiB`.
- Exact inactive manifest:

```text
~/.steel-rag/runtime/0629b1a
~/.steel-rag/runtime/07468a0-hide-ask-header
~/.steel-rag/runtime/0f48dc0-remove-recent-route
~/.steel-rag/runtime/101177f
~/.steel-rag/runtime/1091385-full-screen-ask
~/.steel-rag/runtime/129bfa4
~/.steel-rag/runtime/1f9ffca
~/.steel-rag/runtime/23a6623
~/.steel-rag/runtime/26e0d5c
~/.steel-rag/runtime/30f6aa3-arrange-speed
~/.steel-rag/runtime/321c353-remove-open-question
~/.steel-rag/runtime/47bf77e-steel-guitar-qa
~/.steel-rag/runtime/4b68bf9
~/.steel-rag/runtime/4ba4014
~/.steel-rag/runtime/563a742-chord-karaoke-learner
~/.steel-rag/runtime/56e7271
~/.steel-rag/runtime/57de961
~/.steel-rag/runtime/5a7fbfa
~/.steel-rag/runtime/5dac9b6
~/.steel-rag/runtime/65772ff-staff-retry
~/.steel-rag/runtime/69f63d3
~/.steel-rag/runtime/6e83e42
~/.steel-rag/runtime/70ec6c7-setup-identity
~/.steel-rag/runtime/746c7a3-chord-karaoke
~/.steel-rag/runtime/7a98cdb-spotlight-ask
~/.steel-rag/runtime/7b7ebb0-classic-country-fretboard
~/.steel-rag/runtime/7c20122-tab-learning
~/.steel-rag/runtime/7dc4ba5
~/.steel-rag/runtime/7ed3fc3-backstage-boundary
~/.steel-rag/runtime/7f99e61-immediate-followups
~/.steel-rag/runtime/824d89c-overview-divider
~/.steel-rag/runtime/90a5480
~/.steel-rag/runtime/9566515
~/.steel-rag/runtime/a0b6650-style-impact
~/.steel-rag/runtime/a0f1e26
~/.steel-rag/runtime/a424960-setup-return
~/.steel-rag/runtime/aa6df7f
~/.steel-rag/runtime/ac38989
~/.steel-rag/runtime/af62ccf
~/.steel-rag/runtime/b3e8348
~/.steel-rag/runtime/b3f3b32-arrange-speed
~/.steel-rag/runtime/b46a709
~/.steel-rag/runtime/b63d949
~/.steel-rag/runtime/b7f8235
~/.steel-rag/runtime/baa1ac2
~/.steel-rag/runtime/be468f4
~/.steel-rag/runtime/c9cee8c
~/.steel-rag/runtime/cd897a7
~/.steel-rag/runtime/d561525
~/.steel-rag/runtime/e112f1c-answer-cleanup
~/.steel-rag/runtime/e14a8bc-style-impact-cache
~/.steel-rag/runtime/e153d7c
~/.steel-rag/runtime/e1d4d7a
~/.steel-rag/runtime/e42d17c
~/.steel-rag/runtime/eb08276
~/.steel-rag/runtime/ee11202
~/.steel-rag/runtime/f6a8d9a-classic-country-move
~/.steel-rag/runtime/fb63762
~/.steel-rag/runtime/fd436e8
```

### 3. Regenerable caches and unused UI images

- Recommendation: **Delete**.
- Cache savings: about `12M`.
- The two UI PNGs have no app references; the only `mockup_search_card.png` references are tests asserting that it is absent.
- Exact deletion list:

```text
__pycache__/
steel_guitar_rag/__pycache__/
tests/__pycache__/
scripts/__pycache__/
scripts/ingest/__pycache__/
.pytest_cache/
steel_guitar_rag.egg-info/
ui/assets/landing/mockup_search_card.png
ui/assets/music_staff.png
```

### 4. Public and raw design assets

- Current size: about `746M` under `public/` and `47M` under `Neon Sign/`.
- Recommendation: **Keep raw masters locally but ignore them; delete only verified duplicates**.
- The four public copies below are byte-identical to tracked copies under `ui/brand/` and, for the landing pair, `deploy/landing/brand/`:

```text
public/brand/steel-guitar-rag-landing-alpha.webm
public/brand/steel-guitar-rag-landing-fallback-alpha.png
public/brand/steel-guitar-rag-hanging-sign.webm
public/brand/steel-guitar-rag-hanging-sign-fallback.png
```

- Keep but narrowly ignore the AEP/MOV masters and named unreferenced MP4/WebM/PNG exports. Do not broadly ignore the whole `public/` tree.
- Preserve the three untracked `deploy/landing/brand/` assets in the deployment/docs parked stash because the current index does not reference the hanging-sign pair and the modified deployment doc is not an approved deploy slice.

### 5. Old tracked source/RAG work

- Scope: 11 files spanning source policy/registry, source-inbox inventory metadata, and old RAG clean/chunk/embed/answer changes.
- Recommendation: **Preserve in an exact-scope named stash; do not commit or discard**.
- Reason: the slice mixes YELLOW RAG/chunking changes with protected source inventory work and is not a current tested feature slice.

### 6. Coordination docs, historical handoffs, private helpers, and scraper/forum files

- Scope: 398 untracked docs, four tracked coordination/operations docs, nine untracked top-level helper/forum files, two config files, and three deployment assets.
- Recommendation: **Preserve in named exact-scope stashes by lane/category; do not bulk-commit or delete**.
- This makes the primary worktree clean while keeping every file recoverable for later review.
- No scraper, embedding, private-corpus, deployment, or auth command will be run.

### 7. Existing stashes

- Scope: four June 13 stashes containing substantive runtime/UI/test/ingestion work.
- Recommendation: **Keep and audit later**.
- Do not drop any now; exact comparison against current HEAD is still required.

### 8. Remote backup

- Current state: local HEAD is 461 commits ahead and 0 behind the existing remote-tracking ref; the branch has no configured upstream.
- Recommendation: **Do not push as part of cleanup**.
- After the worktree is clean, run a separate secret/history audit and then decide whether to push this feature branch or a new backup branch.

## Files changed

- Created: `docs/handoffs/task-completions/2026-07-15-1402-01-cleanup-decision-sheet.md`.
- Deleted, moved, staged, committed, stashed, ignored, deployed, or pushed: none in this decision pass.

## Tests and checks

- Re-read `AGENTS.md` and the cleanup audit.
- Re-ran `git status --short --branch` and dirty-path counts.
- Verified the active port `8770` process cwd is `~/.steel-rag/runtime/3cb63c3-playing-context`.
- Scanned all 59 inactive worktrees: `59 clean`, `0 dirty`, `0 missing`, `0 locked`.
- Measured runtime worktrees: `9.2G` total, active worktree `171M`, inactive estimate `9.1 GiB`.
- Checked references for both untracked UI images: neither is used by the app.
- Checked public-brand references and SHA-256 hashes for the four recommended duplicate deletions.
- Runtime tests and browser smoke: not run because no implementation/runtime change was made.

## Integration notes

- The active protected-preview process must remain running from `3cb63c3-playing-context` throughout cleanup.
- Cleanup should be sequenced: commit safe metadata, remove verified inactive worktrees, delete exact junk/duplicates, add narrow ignores, then create exact named stashes for the remaining parked scopes.
- A final status, stash manifest, retained-worktree manifest, and disk-savings handoff is required after execution.

## Risk assessment

- Read-only decision pass: low risk.
- Recommended execution: medium risk because it includes exact deletions and protected-preview-adjacent worktree cleanup, mitigated by the clean/unlocked scan, explicit manifest, active-worktree exclusion, exact-path deletion lists, and preservation of substantive work in stashes.

## Human decision needed

- Yes.
- Easiest response: `Use the recommended cleanup defaults.`
- Alternatively, reply with overrides such as `Use defaults, but keep the UI images` or `Only do items 1, 2, and 3`.

## Safe-to-stage exact file list

- `.gitignore`
- `docs/handoffs/task-completions/2026-07-15-1314-01-worktree-cleanup-audit.md`
- `docs/handoffs/task-completions/2026-07-15-1402-01-cleanup-decision-sheet.md`

## Files that must not be staged

- Every other currently modified or untracked path unless a later audited handoff explicitly approves it.
- In particular: source/RAG pipeline files, `source-inbox/`, `public/`, `ui/brand/`, `Neon Sign/`, deployment assets, private helpers, scraper/forum files, bulk historical handoffs, and `integration-status.md`.

## Recommended next lane

- `01 Repo Steward` to execute the selected cleanup package with exact-path operations and a final clean-status audit.

## Commit readiness

Needs human review first

## Suggested next step

- User reply: `Use the recommended cleanup defaults.`
