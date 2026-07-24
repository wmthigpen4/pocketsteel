# Melody Studio Saved Pedal Tab Labels

## Task summary

- Fixed Melody Studio tablature that rendered legacy descriptive control names such as `A pedal` instead of the player's compact tab symbol `A`.
- Added a dedicated tab-label boundary: legacy included-profile pedal descriptions collapse to their matching stored shorthand, while arbitrary custom labels and distinct travel labels such as `G` and `GG` remain exact.
- Applied the same label to generated tab and event presentation metadata.
- Did not mutate the saved copedent, change mechanics, weaken validation, or touch auth, account storage, corpus, Chroma, embeddings, scraping, DNS, Tunnel, secrets, or deployment policy.

## Lane classification

- Primary lane: 05 Backend / RAG Integration.
- Supporting lanes: 15 QA / Answer Eval, 01 Repo Steward, 12 Self-Hosted Deployment.
- Task mode: GREEN scoped user-smoke bug fix under the approved Autopilot loop.

## Files changed

- `steel_guitar_rag/copedent_transfer.py`
- `steel_guitar_rag/melody_arranger.py`
- `tests/test_copedent_transfer.py`
- This implementation handoff and the accompanying Lane 15 QA handoff.
- Deleted files: none.
- Generated artifacts: none.

## Tests and checks

- Exact label and G/GG regressions: 2 passed.
- Relevant Melody/copedent suite: 29 passed.
- Full Python suite: 1,133 passed.
- `npm run check:js`: passed.
- Ruff on touched Python files: passed.
- `git diff --check` on the scoped files: passed.

## Integration notes

- The saved control label remains authoritative for every genuinely custom name.
- Only a legacy descriptive pedal label that exactly matches `<arranger code> pedal` may collapse to the matching stored shorthand. Thus `A pedal` plus shorthand `A` renders as `A`; `Inside raise` remains `Inside raise`; and `G`/`GG` remain distinct.
- Mechanical control IDs, physical positions, travel, pitch changes, and hard validation are unchanged.

## Risk assessment

- Risk: low. This is a presentation-only selection at the deterministic tab boundary with exact and full-suite coverage.
- Rollback: revert the scoped commit; no data rollback or migration is needed.

## Human decision needed

- No.

## Safe-to-stage exact file list

- `steel_guitar_rag/copedent_transfer.py`
- `steel_guitar_rag/melody_arranger.py`
- `tests/test_copedent_transfer.py`
- `docs/handoffs/task-completions/2026-07-14-2100-05-melody-saved-pedal-tab-labels.md`
- `docs/handoffs/task-completions/2026-07-14-2100-15-melody-saved-pedal-tab-labels-qa.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`.
- All unrelated dirty/untracked corpus, source-inbox, private, account-data, database, vector, brand/design, deployment, auth, historical handoff, and generated files.

## Recommended next lane

- Lane 01 exact-path commit, followed by Lane 12 protected-preview verification.

## Commit readiness

Safe to commit

## Suggested next step

- Commit only the exact safe-to-stage list, restart the isolated protected preview from that commit, and repeat the same full-song browser flow.
