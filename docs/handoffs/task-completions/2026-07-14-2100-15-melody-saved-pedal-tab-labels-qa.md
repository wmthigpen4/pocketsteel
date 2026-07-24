# QA — Melody Studio Saved Pedal Tab Labels

## Task summary

- Independently checked the scoped label-selection behavior and its interaction with the preceding `G`/`GG` fix.
- Confirmed generated tab no longer contains `A pedal`, `B pedal`, or `C pedal` for legacy saved included-profile controls with matching compact shorthand.
- Confirmed the full 31-note arrangement remains ready and custom labels remain mechanically separate.
- No product code was changed during the QA phase beyond the implementation and regression files named below.

## Files changed

- QA handoff created: this file.
- Implementation under review: `steel_guitar_rag/copedent_transfer.py`, `steel_guitar_rag/melody_arranger.py`, and `tests/test_copedent_transfer.py`.
- Deleted files: none.
- Generated artifacts: none.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_copedent_transfer.py -k 'complete_song_arranges_when_player_uses_distinct_g_and_gg_labels or transfer_uses_stable_ids_when_player_g_label_collides_with_arranger_code'` — 2 passed.
- Relevant Melody/copedent selection — 29 passed.
- `.venv/bin/python -m pytest -q` — 1,133 passed in 60.32 seconds.
- `.venv/bin/ruff check steel_guitar_rag/copedent_transfer.py steel_guitar_rag/melody_arranger.py tests/test_copedent_transfer.py` — passed.
- `npm run check:js` — passed.
- `git diff --check` — passed for the scoped implementation.

## Integration notes

- Scope is backend presentation metadata and generated tablature only.
- No schema, auth, account-write, corpus, retrieval, model, mechanical, or deployment-policy changes occurred.
- Browser smoke is still required after the exact commit and protected-preview restart.

## Risk assessment

- Risk: low.
- The condition is narrow and preserves arbitrary saved labels rather than globally abbreviating every control description.

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

- Lane 01 Repo Steward for exact-path commit.

## Commit readiness

Safe to commit

## Suggested next step

- Proceed under Repo Steward auto-approval with only the exact five-file list above.
