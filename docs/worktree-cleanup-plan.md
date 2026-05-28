# Worktree Cleanup Plan

Status date: 2026-05-28
Branch: `feature/answer-api`

This plan splits the remaining dirty worktree into small lanes so generated
artifacts, credentials, corpus outputs, Chroma/vector stores, and local
deployment state stay out of commits.

## Current Dirty Lanes

### Provenance, Legal, And Source Policy

Candidate source-policy/provenance commit files:

- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `docs/admin-legal-provenance-panel.md`
- `docs/copyright-provenance.md`
- `docs/copyright-risk-model.md`
- `docs/corpus-license-policy.md`
- `docs/legal-provenance.md`
- `docs/source-policy-records.md`
- `scripts/capture_source_policy_snapshot.py`
- `scripts/prepare_copyright_review_queue.py`

Do not commit generated provenance queues or snapshots:

- `corpus_metadata/copyright_review_queue.jsonl`
- `corpus_metadata/legal_provenance_events.jsonl`
- `corpus_metadata/legal_snapshots/`
- `corpus_metadata/review_queue/`
- `corpus_metadata/source_policy_snapshots.jsonl`

Recommended action: split this into one documentation/source-registry commit and
one tooling commit if the scripts are still intended. Keep generated queues and
snapshots ignored.

### Root RAG Build Scripts

Candidate review files:

- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `rag_build_forum.py`
- `rag_forums.json`
- `docs/rag-forum-builds.md`
- `pocketsteel/sample_search.py`

Recommended action: park this lane until the project decides whether these
root-level tools are current, obsolete duplicates of newer `pocketsteel/` and
`scripts/phase3_*` modules, or archive candidates. Do not run embedding or
Chroma-reset workflows while reviewing this lane.

### Deployment Docs

Candidate deployment-doc commit files:

- `docs/cloudflare-pages-landing.md`
- `docs/deployment-plan.md`
- `docs/private-preview-operations.md`
- `docs/same-origin-answer-smoke.md`
- `docs/security-audit-private-preview.md`

Recommended action: split into docs-only commits by surface:

1. Public landing/Pages operations.
2. Private preview/access operations.
3. Security audit notes.

Confirm each commit is documentation-only and does not include deploy output,
DNS changes, credentials, or private environment files.

### Auth And Access

Current dirty files are docs-only:

- `docs/private-preview-operations.md`
- `docs/same-origin-answer-smoke.md`
- `docs/security-audit-private-preview.md`

Recommended action: commit only after confirming they describe existing auth
behavior and do not introduce secrets, real tunnel tokens, Cloudflare Access
credentials, private emails beyond approved allowlist examples, or deployment
state that was not already performed.

### Phase 3

Candidate Phase 3 planning/tooling files:

- `docs/phase-3-sample-review.md`
- `scripts/phase3_embed_v2_chroma.py`

Recommended action: treat `scripts/phase3_embed_v2_chroma.py` as a YELLOW/RED
lane because it can create embedding/vector outputs. It may be prepared as
tooling, but do not run it or commit it without explicit approval and tests.
Keep `docs/phase-3-sample-review.md` as a docs-only review artifact unless it
depends on uncommitted generated outputs.

### Generated And Ignored Artifacts

These are local/generated artifacts and should remain ignored or untracked:

- `.wrangler/`
- `archive/`
- `corpus-v2/`
- `private-preview.env`
- `rag-data/`
- `*.env`
- `*.log`
- `*.sqlite`
- `*.db`

Additional generated metadata artifacts are already present locally and should
stay out of commits:

- `corpus_metadata/copyright_review_queue.jsonl`
- `corpus_metadata/legal_provenance_events.jsonl`
- `corpus_metadata/legal_snapshots/`
- `corpus_metadata/review_queue/`
- `corpus_metadata/source_policy_snapshots.jsonl`

Recommended action: commit the `.gitignore` addition for generated
`corpus_metadata` queues/snapshots as a tiny hygiene commit if it remains
correct after review.

### Unknown Or Parked

Park until ownership is clear:

- `rag_build_forum.py`
- `rag_forums.json`
- `pocketsteel/sample_search.py`

Recommended action: inspect for overlap with committed retrieval/API modules.
If obsolete, leave unstaged and later move to archive only with explicit
approval. Do not delete.

## What Should Be Committed

Recommended commit order:

1. `.gitignore` hygiene for generated `corpus_metadata` queue/snapshot outputs.
2. Deployment docs, split by public landing, private preview, and security audit.
3. Provenance/legal/source-policy docs and registry.
4. Provenance tooling, if still wanted and tested.
5. Phase 3 sample-review docs.
6. Phase 3 embed-v2 tooling only after explicit approval and safe dry-run tests.

## What Should Be Ignored

Keep or add ignore coverage for:

- `.wrangler/`
- `archive/`
- `corpus-v2/`
- `private-preview.env`
- `rag-data/`
- `corpus_metadata/*_queue.jsonl`
- `corpus_metadata/*_events.jsonl`
- `corpus_metadata/*_snapshots.jsonl`
- `corpus_metadata/legal_snapshots/`
- `corpus_metadata/review_queue/`
- `*.env`
- `*.log`
- `*.sqlite`
- `*.db`

## What Should Be Parked

Park until the user chooses the lane:

- root RAG build/chunk/embed scripts
- forum build scripts and config
- `pocketsteel/sample_search.py`
- Phase 3 embed-v2 Chroma creation tooling

## What Should Never Be Committed

Never commit:

- raw corpus dumps
- generated corpus-v2 outputs
- Chroma/vector stores
- embedding outputs
- SQLite databases
- credentials
- private env files
- Cloudflare local state
- logs
- private or paid transcripts
- generated legal/provenance queue and snapshot dumps

## Recommended Next Commit

Prepare a plan-only cleanup commit containing:

- `docs/worktree-cleanup-plan.md`

After that, prepare a separate `.gitignore` hygiene commit for generated
`corpus_metadata` outputs if the currently unstaged ignore additions are still
desired.
