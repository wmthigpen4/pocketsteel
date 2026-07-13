# Lane 12 Handoff: Interest Spam Auto-Delete

## Task Summary

- Deleted exactly the 26 production D1 interest-form rows the user reviewed and
  explicitly approved for deletion.
- Verified before deletion that all 26 live rows matched the reviewed ID set
  and that no newer/unreviewed row existed.
- Verified after deletion that `interest_submissions` contained zero rows.
- Updated the weekly digest Worker to delete high-confidence spam/test rows by
  exact ID before composing or sending Pushover.
- Added a conservative deterministic spam classifier for marketing
  solicitations and gibberish-only bot submissions.
- Preserved ambiguous submissions as `review`; those rows remain stored and
  visible in Pushover.
- Made the Worker send a weekly summary even when no real rows are pending.
- Did not deploy the Worker.

## Files Changed

- `workers/interest-digest.js`
  - Adds high-confidence spam classification.
  - Fetches unnotified `spam` and `test` rows for cleanup.
  - Deletes classified spam/test rows before any Pushover request.
  - Constrains each automatic delete by exact row ID and
    `notified_at is null`.
  - Exposes dry-run deletion previews and actual deletion counts.
  - Sends the weekly no-submission summary.
- `tests/test_public_landing_page.py`
  - Covers spam patterns, existing spam/test cleanup, cleanup-before-notify
    ordering, deletion failure, dry-run safety, and empty weekly summaries.
- `docs/interest-list-operations.md`
  - Documents automatic cleanup rules, query scope, dry-run behavior, and
    weekly empty summaries.
- `docs/handoffs/task-completions/2026-07-13-1037-12-interest-spam-auto-delete.md`
  - This handoff.

No repository files were deleted. No private submission contents, names, email
addresses, or row IDs were copied into repository documentation.

## Tests And Checks

- Pre-delete production D1 verification — 26 total rows and 26 approved rows.
- Exact-ID production D1 deletion — succeeded with `changes = 26`.
- Post-delete production D1 verification — `remaining_rows = 0`.
- `node --check workers/interest-digest.js` — passed.
- `.venv/bin/python -m pytest tests/test_public_landing_page.py` — 42 passed.
- Scoped `git diff --check` — passed.
- Live Pushover send — skipped to avoid an unsolicited notification.
- Production Worker deployment — skipped pending explicit RED approval.

## Integration Notes

- No schema, migration, binding, secret, auth, DNS, cron schedule, corpus,
  Chroma, RAG, UI, or landing-form behavior changed.
- Automatic cleanup matches existing `spam`/`test` status, known test
  addresses, explicit marketing-solicitation categories, or a narrow
  gibberish-only signature.
- URL count alone still results in `review`, not deletion.
- Dry-run performs no writes and reports `wouldDeleteCount` plus per-row
  `would_delete`.
- Every D1 delete is awaited. A cleanup failure prevents Pushover from sending.
- The weekly schedule remains `0 14 * * 1`.
- Existing unrelated dirty and protected worktree files remain parked.

## Risk Assessment

- Risk: medium because future automatic spam deletion is irreversible.
- False-positive exposure is reduced by conservative named patterns; ambiguous
  rows remain reviewable.
- Code rollback stops future automatic cleanup but cannot restore rows already
  deleted. Production D1 recovery would require a separate Cloudflare recovery
  operation if ever needed.

## Human Decision Needed

Yes. Explicit approval is still required to deploy the committed
`steel-rag-interest-digest` Worker to production. The current 26-row deletion
is complete and needs no further decision.

## Safe-To-Stage Exact File List

- `workers/interest-digest.js`
- `tests/test_public_landing_page.py`
- `docs/interest-list-operations.md`
- `docs/handoffs/task-completions/2026-07-13-1037-12-interest-spam-auto-delete.md`

## Files That Must Not Be Staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-13-1022-01-interest-digest-exact-path-commit.md`
- `docs/handoffs/task-completions/2026-07-13-1030-12-interest-review-name-table.md`
- Every unrelated dirty, untracked, private, corpus, vector, source-inbox,
  design, deployment, and generated path currently parked in the worktree.

## Recommended Next Lane

- `01 Repo Steward` for exact-path commit.
- Then `12 Self-Hosted Deployment` only after explicit production deployment
  approval.

## Commit Readiness

Safe to commit

## Suggested Next Step

Lane 01 prompt: `Run ExactPathCommit using docs/handoffs/task-completions/2026-07-13-1037-12-interest-spam-auto-delete.md and stage only its four safe-to-stage files.`
