# 2026-06-23 Lane 15 Visual Smoke Hardening

## Task Summary

Requested: strengthen QA/browser-smoke standards so future UI-facing handoffs prove the interface is visually usable before asking for user smoke.

Completed: updated the completion protocol, eval rubric, and answer-eval expected behaviors to require screenshot-backed visual evidence for UI-facing smoke reports. The new standard explicitly rejects DOM-count-only visual passes and adds focused checks for the main app header/search area and E9 Fretboard Explorer controls, selected groups, fretboard markers/clusters, full-string-lane regressions, internal labels, `[object Object]`, and console status.

Intentionally not changed: production UI, backend answer routing, protected preview runtime, corpus, Chroma, embeddings, scraping, auth, DNS, secrets, and private-source files.

## Files Changed

Changed files:

- `docs/process/codex-completion-protocol.md`
- `docs/llm-guidance/eval-rubric.md`
- `tests/answer_eval/expected_behaviors.md`

Created files:

- `docs/handoffs/task-completions/2026-06-23-15-visual-smoke-hardening.md`

Deleted files: none.

Generated artifacts: none.

## Tests And Checks

Commands run:

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log -10 --oneline`
- `git diff --name-only`
- `git diff --cached --name-only`
- `git diff --check`

Results:

- Initial branch: `feature/answer-api`
- Starting HEAD: `efc3660`
- `PLAN.md` and `plan.md` were not present.
- `git diff --check` result: passed.

Tests skipped:

- No pytest or browser smoke was run because this was a docs-only QA-standard update.
- No docs lint command was discovered during this scoped pass.

## QA Standard Changed

Future UI-facing smoke reports must include screenshot-backed evidence before saying `visual pass`.

The standard now requires:

- exact protected-preview/local/production target URLs and cache-busted URLs
- visible-state checks, not only DOM counts, marker counts, API payload checks, or console output
- screenshot paths or cropped-image evidence for changed visual regions
- mobile/narrow screenshots when responsive behavior is in scope
- explicit comparison to the intended visual reference when the user provides a screenshot or says to match a reference
- `technical pass; visual not verified` wording when screenshots cannot be captured

Main app visual checks now include:

- Q&A/search remains visually primary
- header buttons are visible, separated, readable, and not overlapping
- answer, source-card, fretboard, tab, and prompt-chip regions do not crowd each other
- no raw internal labels or `[object Object]`

Explorer visual checks now include:

- key, scale, harmony/view, and string-group controls are visible and selected states are obvious
- selected string groups visibly update both row/card/detail output and fretboard markers/clusters
- full-string lanes are absent unless explicitly requested
- core and advanced groups remain distinguishable when relevant
- raw internal labels do not appear
- console status is recorded

## Integration Notes

This is a Lane 15 QA standard change only. Future Lane 06 and Lane 15 browser-smoke handoffs should not mark UI changes as visually passing unless screenshot evidence is present.

API fallback remains useful for backend behavior, but it cannot satisfy visual smoke requirements.

## Risk Assessment

Risk: low.

Reason: docs/test-planning guidance only; no runtime code changed.

Rollback: revert the three documentation edits and this handoff if the standard proves too strict.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/process/codex-completion-protocol.md`
- `docs/llm-guidance/eval-rubric.md`
- `tests/answer_eval/expected_behaviors.md`
- `docs/handoffs/task-completions/2026-06-23-15-visual-smoke-hardening.md`

## Files That Must Not Be Staged

All unrelated dirty, untracked, generated, corpus, source-inbox, design, public/static, and private files currently present in the worktree.

Do not stage:

- `docs/handoffs/task-completions/integration-status.md`
- `corpus-private/`
- `corpus-v2/`
- `source-inbox/`
- `public/`
- `ui/brand/`
- `Neon Sign/`
- Chroma/vector stores
- embeddings
- deployment/auth/DNS/secrets files

## Recommended Next Lane

Lane 15 / Lane 06.

Suggested next task:

`Lane 15: Apply the visual smoke hardening standard to the next protected-preview Explorer or main-app UI smoke. Include screenshot paths and mark the result technical-only if screenshots cannot be captured.`

## Commit Readiness

Safe to commit.
