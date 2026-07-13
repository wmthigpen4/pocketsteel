# Repository And Documentation Cleanup

## Task summary

Completed the repository/documentation loop of the approved technical-debt
remediation plan.

- Replaced the one-line architecture stub with the current four-workspace,
  Access-protected, bounded-runtime, lazy-Explorer, digest-Worker architecture.
- Replaced the outdated private-preview runbook with one current startup,
  health, protected-smoke, Worker, and rollback procedure.
- Added a current threat model and non-destructive recovery procedure.
- Added reproducible Python/Node commands and current operating-document links.
- Marked four superseded plans as historical without deleting them.
- Added narrow retention rules for dependency output, smoke screenshots,
  generated smoke summaries, patch backups, generated reports, and temporary
  output. Existing artifacts were not deleted.
- Classified the pre-existing dirty worktree by path and lane below.
- Intentionally did not modify private/corpus/vector/source-inbox data, retrieval
  behavior, auth policy, DNS, product naming, or unowned dirty implementation.

`docs/handoffs/task-completions/integration-status.md` remains a separate
coordination edit and is not part of this commit.

## Files changed

- `.gitignore`
- `README.md` — this loop adds only the **Current Application And Operations**
  section; the pre-existing provenance hunk remains parked.
- `docs/README.md`
- `docs/architecture.md`
- `docs/current-commands.md` — this loop adds/updates the reproducible baseline
  and setup guidance; the pre-existing local v2-rerank smoke hunk remains parked.
- `docs/private-preview-operations.md`
- `docs/threat-model.md` (new)
- `docs/recovery-procedure.md` (new)
- `docs/self-hosted-deployment-plan.md`
- `docs/v2-private-preview-switch-plan.md`
- `docs/worktree-cleanup-plan.md`
- `docs/phase-3d-embed-v2-plan.md`
- This handoff.

No files were deleted and no generated artifact was created.

## Tests and checks

- `.venv/bin/pytest -q` — **1028 passed**.
- `npm run check:js` — passed.
- `npm run lint:js` — passed.
- `npm run test:worker` — **4 passed** in the Cloudflare Workers runtime.
- `npm run check:locks` — four environments passed.
- `npm run check:assets` — 922 tracked files and 51 Explorer chunks passed.
- `.venv/bin/python scripts/check_secret_patterns.py` — passed.
- `.venv/bin/pip-audit -r requirements/runtime.lock` — no known vulnerabilities.
- `npm run audit:node` — zero vulnerabilities.
- Canonical documentation targets and representative ignore patterns — passed.
- `git diff --check` over the exact documentation/retention scope — passed.

## Dirty-worktree classification

Only path names and Git status were used. Protected/private/generated file
contents were not inspected.

### Lane 01 coordination — parked

- `docs/handoffs/task-completions/integration-status.md` — existing coordination
  edit; it will be replaced separately after the final preview smoke.
- `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
- `docs/handoffs/task-completions/*.md` — 260 untracked historical/coordination
  handoffs; not staged by this loop.

### Lane 02 corpus, provenance, and source policy — protected and parked

- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/source-inbox-inventory.md`
- `source-inbox/inventory.json`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `rag_build_forum.py`
- `rag_forums.json`
- `source-inbox/`
- `data/` — 1,387 untracked paths reported by name only; contents not inspected.

### Lane 05 private lesson / answer work — parked

- `rag_answer.py`
- `answer_private_lessons.py`
- `embed_private_lessons.py`
- `eval_private_lessons.py`
- `search_private_lessons.py`
- `validate_applied_steel_candidates.py`
- `validate_private_lesson_chunks.py`
- `validate_private_lesson_note_quality.py`
- `config/`

### Lanes 12 and 19 deployment/brand/design — protected and parked

- `docs/cloudflare-pages-landing.md`
- `ui/brand/steel-guitar-rag-landing-alpha.webm`
- `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`
- `deploy/landing/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`
- `deploy/landing/brand/steel-guitar-rag-hanging-sign-fallback.png`
- `deploy/landing/brand/steel-guitar-rag-hanging-sign.webm`
- `Neon Sign/`
- `public/`

### Lanes 18 and 19 untracked product/design documents — parked

- `docs/admin-legal-provenance-panel.md`
- `docs/animated-neck-visualization.md`
- `docs/answer-ui-sections.md`
- `docs/codex-queue/`
- `docs/content-ingestion-inventory.md`
- `docs/copyright-risk-model.md`
- `docs/deployment-plan.md`
- `docs/e9-fretboard-position-engine.md`
- `docs/feature-vision.md`
- `docs/feature_backlog`
- `docs/fretboard-visual-design-directions.md`
- `docs/legal-provenance.md`
- `docs/lesson-mode.md`
- `docs/llm-guidance/e9_harmonized_scales_and_diatonic_harmony_knowledge.md`
- `docs/phase-3-sample-review.md`
- `docs/phase-3d-embed-v2-run-report.md`
- `docs/rag-forum-builds.md`
- `docs/same-origin-answer-smoke.md`
- `docs/source-policy-records.md`
- `docs/steel-guitar-rag-fretboard-product-concept.md`
- `docs/steel-guitar-rag-virtual-fretboard-mvp.md`
- `docs/vtt-transcript-ingestion-audit.md`
- `docs/youtube-source-card.md`

Generated smoke evidence, `node_modules/`, patch backups, `tmp/`, and report
output are now ignored prospectively. This does not delete or rewrite any
existing file.

## Integration notes

- `docs/architecture.md` is the current architecture.
- `docs/private-preview-operations.md` is the current application operations
  procedure.
- `docs/current-commands.md` is the verified command list.
- `docs/threat-model.md` and `docs/recovery-procedure.md` are the current
  security/recovery references.
- Historical plans remain readable and explicitly point to current documents.
- README/current-command staging must be hunk-level because both contain
  unrelated pre-existing edits.

## Risk assessment

Low. This loop changes documentation and ignore rules only. Narrow ignore
patterns could hide future generated smoke evidence, which is intentional;
canonical markdown handoffs remain visible. Rollback is a scoped revert.

## Human decision needed

No. The cleanup and exact-path commit are part of the approved remediation run.

## Safe-to-stage exact file list

- `.gitignore`
- `README.md` — only the **Current Application And Operations** hunk
- `docs/README.md`
- `docs/architecture.md`
- `docs/current-commands.md` — only the reproducible-baseline and setup hunks
- `docs/private-preview-operations.md`
- `docs/threat-model.md`
- `docs/recovery-procedure.md`
- `docs/self-hosted-deployment-plan.md`
- `docs/v2-private-preview-switch-plan.md`
- `docs/worktree-cleanup-plan.md`
- `docs/phase-3d-embed-v2-plan.md`
- `docs/handoffs/task-completions/2026-07-13-1707-01-repository-documentation-cleanup.md`

## Files that must not be staged

- The pre-existing README provenance hunk.
- The pre-existing `docs/current-commands.md` local-v2-rerank hunk.
- `docs/handoffs/task-completions/integration-status.md`.
- Every parked path in the classification above.
- All private, corpus, vector, source-inbox, brand, design, deployment artifact,
  credential, secret, generated, and unrelated dirty files.

## Recommended next lane

Lane 01 exact-hunk commit, then Lane 12 restart/version verification and final
authenticated protected browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Stage the exact clean files plus only the two approved README/command-reference
hunks, review the cached diff, commit the cleanup, restart the preview at the
new HEAD, complete authenticated four-workspace smoke, then replace
`integration-status.md` with the concise final snapshot as an unstaged
coordination artifact.
