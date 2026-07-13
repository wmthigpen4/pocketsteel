# Cloudflare Access issuer compatibility repair

## Task summary

Protected-preview smoke after the security-baseline commit showed that Cloudflare Access authenticated the browser at the edge, while the application session remained anonymous. The application verifier now accepts Cloudflare's semantically equivalent issuer forms with or without the trailing slash, while preserving exact issuer validation. Validation failures are classified with safe diagnostic codes that do not expose tokens, email addresses, or environment values.

Intentionally unchanged: Access policy, DNS, credentials, allowlists, auth roles, API success contracts, corpus/vector data, and private source data.

## Files changed

- `pocketsteel/cloudflare_access.py`
- `pocketsteel/access_control.py`
- `tests/test_cloudflare_access.py`
- This handoff

No files were deleted and no generated artifacts were created.

## Tests and checks

- `PYTHONPATH=.:scripts .venv/bin/pytest -q tests/test_cloudflare_access.py tests/test_api_search.py` — **319 passed**.
- `git diff --check -- pocketsteel/access_control.py pocketsteel/cloudflare_access.py tests/test_cloudflare_access.py` — passed.
- Protected-preview restart via the documented user-level `SIGTERM`/launchd `KeepAlive` path — succeeded.
- Authenticated protected browser reload — passed: the header exposed **Go Backstage** and the question input was enabled.

The first `.venv/bin/pytest` invocation without `PYTHONPATH` failed collection on `rag_common`; fixing that repository test-path debt remains in the approved automated-quality loop.

## Integration notes

- Both `https://team.cloudflareaccess.com` and `https://team.cloudflareaccess.com/` issuer claim forms are accepted when the configured issuer is otherwise identical.
- Failures retain the public `401` contract and add only a non-sensitive internal diagnostic classification.
- A final committed-HEAD restart and four-workspace protected smoke are still required before closing the security loop.

## Risk assessment

Low. The verifier still pins RS256, validates signature/audience/expiry, and permits only two normalized forms of the same configured issuer. Rollback is the scoped repair commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- `pocketsteel/access_control.py`
- `pocketsteel/cloudflare_access.py`
- `tests/test_cloudflare_access.py`
- `docs/handoffs/task-completions/2026-07-13-1455-11-cloudflare-issuer-compatibility.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (separate coordination refresh)
- All unrelated dirty corpus, vector, source-inbox, private-data, deployment, design, and generated-artifact paths

## Recommended next lane

Lane 01 Repo Steward for exact-path commit, then Lane 12 protected-preview restart and authenticated four-workspace smoke.

## Commit readiness

Safe to commit.

## Suggested next step

Commit these four exact paths, restart protected preview at the committed HEAD, verify `/api/version`, then smoke Chat, Explorer, Melody Studio, and Lessons.
