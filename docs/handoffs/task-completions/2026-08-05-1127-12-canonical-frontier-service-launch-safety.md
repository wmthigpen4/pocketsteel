# Canonical Frontier Service Launch Safety

## Outcome

Prepared the no-activation deployment-safety slice for the owner-corrected canonical-frontier service. The external service can now be checked against an exact 56-file bundle manifest and the complete 1,948,039-passage index before it is allowed to start.

No service was installed, loaded, started, restarted, deployed, or exposed. No environment file, secret, credential, Cloudflare setting, DNS record, corpus file, vector index, or protected holdout was changed.

## Files

- `deploy/macos/canonical-frontier-service-bundle-v931.json` — exact hashes for the runtime's transitive local Python modules, frozen policies/audits, implementation-ready candidate, and index manifests.
- `scripts/verify_canonical_frontier_service.py` — fail-closed bundle, candidate, path, count, provenance, and index-readiness verifier.
- `deploy/macos/run-canonical-frontier-service.sh` — loopback-only wrapper that requires the verified bundle, server-side token, readable protected environment, executable Python, and credential presence before starting the HTTP service.
- `deploy/macos/com.steelguitarrag.canonical-frontier.plist.template` — separate background service definition for `127.0.0.1:8771`; no secrets or public binding appear in the plist.
- `tests/test_canonical_frontier_service_deploy.py` — success, fingerprint mutation, path escape, shell syntax, verification ordering, loopback, and plist-secret tests.

## Verification

- Real bundle verification: **56 files matched**.
- Canonical index verification: **1,948,039 passages**, complete lexical/vector progress, protected holdout usage zero.
- New deployment-safety unit tests: **6 passed**.
- Focused site/API/deployment tests: **355 passed**.
- Python compile check: passed.
- Shell syntax check: passed.
- `git diff --check`: passed.
- Paid API calls: **0**.

## Remaining deployment work

Before a protected-preview start, add and review an installer/render/preflight command for the dedicated LaunchDaemon, confirm the selected Python environment contains the locked runtime dependencies and locally cached BGE reranker, and explicitly authorize the protected environment and service-state changes.

The application flag remains false. Public activation remains unauthorized.
