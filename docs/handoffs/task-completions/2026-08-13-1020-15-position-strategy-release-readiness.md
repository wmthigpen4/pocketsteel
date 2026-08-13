# Position-strategy repair release readiness

## Task summary

- Cleared the canonical-frontier preflight blocker for the approved position-strategy/search-quality repair.
- Confirmed the active frontier service root is the self-contained frozen copy at `/Users/cory/.steel-rag/services/canonical-frontier-v1034-fallback-20260806`.
- Updated the repository deployment fingerprint manifest to match that independently verified 76-file v1034 bundle exactly.
- Updated the environment-sensitive deployment test to use the frozen service root by default with an explicit environment override for future verified roots.
- Re-ran focused and complete application verification successfully.
- No corpus, vector index, embedding, source data, auth, DNS, Cloudflare configuration, UX, UI, or public page was changed.

## Files changed

### Search repair

- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/curated_contracts.py`
- `steel_guitar_rag/curated_answers.py`
- `steel_guitar_rag/answer_contracts.py`
- `steel_guitar_rag/api.py`
- `evals/golden_user_smoke_bank.yaml`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `tests/test_canonical_frontier_client.py`

### Frozen frontier verification

- `deploy/macos/canonical-frontier-service-bundle-v931.json`
- `tests/test_canonical_frontier_service_deploy.py`

### Handoffs

- `docs/handoffs/task-completions/2026-08-13-0948-18-search-quality-routing-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-13-1002-05-position-strategy-routing-repair.md`
- `docs/handoffs/task-completions/2026-08-13-1020-15-position-strategy-release-readiness.md`

## Tests and checks

- `python3 scripts/verify_canonical_frontier_service.py --service-root /Users/cory/.steel-rag/services/canonical-frontier-v1034-fallback-20260806 --manifest deploy/macos/canonical-frontier-service-bundle-v931.json`
  - PASS: 76 files verified; 1,948,039 passages; protected holdout usage zero.
- Repository manifest compared byte-for-byte with the active frozen bundle manifest.
  - PASS.
- `.venv/bin/pytest -q tests/test_canonical_frontier_service_deploy.py::CanonicalFrontierLaunchFilesTests::test_installer_render_and_preflight_are_read_only`
  - PASS: 1 passed.
- `.venv/bin/pytest -q tests/test_answer_intent_classifier.py tests/test_canonical_frontier_client.py tests/test_api_search.py tests/test_golden_user_smoke_bank.py tests/test_canonical_frontier_service_deploy.py`
  - PASS: 494 passed.
- `.venv/bin/ruff check steel_guitar_rag/answer_intent_classifier.py steel_guitar_rag/curated_contracts.py steel_guitar_rag/curated_answers.py steel_guitar_rag/answer_contracts.py steel_guitar_rag/api.py tests/test_answer_intent_classifier.py tests/test_api_search.py tests/test_canonical_frontier_client.py tests/test_canonical_frontier_service_deploy.py`
  - PASS.
- `.venv/bin/pytest -q`
  - PASS: 1,666 passed in 88.06 seconds.
- `git diff --check`
  - PASS.

## Integration notes

- The active canonical-frontier LaunchAgent already uses the verified self-contained root and remains healthy on loopback port 8771.
- The old mutable workspace path is no longer the deployment-test default.
- `STEEL_RAG_TEST_CANONICAL_FRONTIER_SERVICE_ROOT` can point the read-only deployment test at a future verified root.
- The release must be constructed as an isolated descendant of protected SHA `4a77e849`, not by deploying the current feature branch.
- Existing UX/UI and Cloudflare Access/Tunnel infrastructure must remain unchanged.

## Risk assessment

- Medium application risk from deterministic-miss escalation; low deployment-manifest risk because the repository manifest is byte-identical to the already-running verified manifest.
- Rollback is the isolated release’s parent SHA `4a77e849`.

## Human decision needed

- No. The user explicitly authorized restoration of the verified service root and an isolated release from the protected SHA.

## Safe-to-stage exact file list

- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/curated_contracts.py`
- `steel_guitar_rag/curated_answers.py`
- `steel_guitar_rag/answer_contracts.py`
- `steel_guitar_rag/api.py`
- `evals/golden_user_smoke_bank.yaml`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`
- `tests/test_canonical_frontier_client.py`
- `deploy/macos/canonical-frontier-service-bundle-v931.json`
- `tests/test_canonical_frontier_service_deploy.py`
- `docs/handoffs/task-completions/2026-08-13-0948-18-search-quality-routing-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-13-1002-05-position-strategy-routing-repair.md`
- `docs/handoffs/task-completions/2026-08-13-1020-15-position-strategy-release-readiness.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing unrelated modification).
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md` (pre-existing unrelated untracked file).
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md` (pre-existing unrelated untracked file).
- Corpus, source, Chroma/vector, embedding, private-data, environment, secret, log, generated, UI, public-page, DNS, auth, Tunnel, and Cloudflare configuration files.

## Recommended next lane

- Lane 01 exact-path commit, then Lane 12 isolated release from `4a77e849` and protected-preview smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval: stage only the exact files above, commit the repair, cherry-pick that commit onto a detached worktree rooted at `4a77e849`, validate the isolated diff and tests, activate the existing protected-preview LaunchAgent, and smoke the existing authenticated app UI.
