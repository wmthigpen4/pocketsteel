# Interest-Digest Worker Hardening

## Task Summary

- Implemented the approved Interest-Digest hardening loop.
- Added a scoped D1 migration for digest deliveries and delivery parts.
- Added transactional weekly delivery claims, persistent part hashes and
  attempts, definite-failure retry of only unsent parts, and concurrency
  suppression.
- Made ambiguous network outcomes fail safe: they are not automatically
  retried because doing so could duplicate a notification.
- Required both a verified Cloudflare Access JWT and the existing admin token
  for PII-bearing `/dry-run` and `/run` routes. The JWT verifier checks RS256,
  signature, issuer, audience, expiry, and key rotation through a bounded JWKS
  cache.
- Kept a loopback-only local Access bypass for development; it is ignored for
  non-loopback hostnames.
- Batched moderation and related delivery-state writes, enabled Workers
  Observability, and added structured non-PII logs.
- Updated the operations runbook.
- Intentionally did not send a live Pushover notification, inspect submission
  contents, change DNS, or touch app auth policy, corpus, source-inbox, vector,
  private, or generated data.

## Files Changed

- `workers/interest-digest.js`
- `wrangler-interest-digest.toml`
- `migrations/interest-digest/0001_delivery_state.sql`
- `tests/test_public_landing_page.py`
- `docs/interest-list-operations.md`
- `docs/handoffs/task-completions/2026-07-13-1613-11-interest-digest-hardening.md`

No files were deleted. Temporary local D1 and Wrangler output stayed under
`/tmp` and is not a repository artifact.

## Tests And Checks

- `.venv/bin/python -m pytest tests/test_public_landing_page.py -q` — 47 passed.
- `.venv/bin/python -m pytest -q` — 1,028 passed.
- `node --check workers/interest-digest.js` — passed.
- `node --check functions/api/interest.js` — passed.
- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `npx --yes wrangler@latest deploy --dry-run --outdir /tmp/interest-digest-hardening-dry-run --config wrangler-interest-digest.toml` — passed; D1 binding resolved.
- `npx --yes wrangler@latest d1 migrations apply STEEL_RAG_INTEREST_D1 --local --persist-to /tmp/interest-digest-d1 --config wrangler-interest-digest.toml` — passed.
- Local Cloudflare-runtime `GET /dry-run` with the loopback-only bypass and test admin token — HTTP 200 with no rows and no writes.
- The same bypass addressed through a non-loopback hostname — HTTP 403.
- Focused tests cover valid Access JWTs, expiry, same-`kid` JWKS rotation,
  missing identity, concurrent claims, definite multipart failure, cross-window
  retry, successful-part suppression, and ambiguous network outcomes.
- `git diff --check` for the scoped files — passed.

Remote migration application and Worker deployment intentionally occur only
after the exact-path implementation commit. They will be recorded in a
separate deployment handoff.

## Integration Notes

- New D1 tables:
  - `interest_digest_deliveries`
  - `interest_digest_delivery_parts`
- New Worker secrets required for administrative routes:
  - `INTEREST_DIGEST_ACCESS_ISSUER`
  - `INTEREST_DIGEST_ACCESS_AUD`
  - `INTEREST_DIGEST_ACCESS_JWKS_URL`
- Existing `INTEREST_DIGEST_ADMIN_TOKEN`, Pushover secrets, D1 binding, Cron
  schedule, and public interest capture contract remain unchanged.
- Scheduled events are trusted Worker entry points and do not pass through the
  HTTP admin-auth boundary.
- An unfinished older delivery is resumed or blocks a newer weekly delivery
  before a new window can be created. This prevents cross-window resend of
  parts already recorded as sent.
- `integration-status.md` remains a separate, pre-existing coordination edit.

## Risk Assessment

Medium. The change affects a scheduled Worker and applies a D1 schema
migration. The migration is additive and rollback-safe for the existing
submission table. Worker rollback can restore the previous script while
leaving the two unused delivery tables in place. An `ambiguous` part requires
manual operator reconciliation; this favors no duplicate notification over an
automatic resend with unknowable outcome.

## Human Decision Needed

No. The user explicitly approved the D1 migration, Worker deployment, Access
configuration, exact-path commit, and verification for this loop.

## Safe-To-Stage Exact File List

- `workers/interest-digest.js`
- `wrangler-interest-digest.toml`
- `migrations/interest-digest/0001_delivery_state.sql`
- `tests/test_public_landing_page.py`
- `docs/interest-list-operations.md`
- `docs/handoffs/task-completions/2026-07-13-1613-11-interest-digest-hardening.md`

## Files That Must Not Be Staged

- `docs/handoffs/task-completions/integration-status.md`
- All unrelated dirty or untracked files.
- All corpus, source-inbox, private, vector, generated report, visual design,
  brand, deployment artifact, credential, secret, and local Wrangler paths.

## Recommended Next Lane

`01 Repo Steward` for exact-path commit, followed by `12 Self-Hosted
Deployment` for remote migration application, secret-name-preserving Access
configuration, Worker deployment, and non-notifying verification.

## Commit Readiness

Safe to commit

## Suggested Next Step

Stage only the six files listed above, review the cached diff, commit the
Interest-Digest hardening loop, then apply the remote D1 migration and deploy
the committed Worker without invoking a live Pushover send.
