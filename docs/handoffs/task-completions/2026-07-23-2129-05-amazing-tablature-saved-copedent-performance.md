# Lane 05 — Amazing Tablature saved-copedent performance

## Task summary

The private Amazing Tablature beta was functionally correct on the standard
profile, but protected-preview smoke with a saved E9 copedent exposed an
unacceptable runtime stall. The adapter first built the deterministic
candidate catalogs, then rebuilt the same catalogs for learned ranking. After
that duplicate pass was removed, the frozen learned scorer still rebuilt
mechanical action dictionaries for every candidate triple in the second-order
path search.

The runtime adapter now:

- builds each candidate catalog once;
- shares that catalog between deterministic and learned paths;
- caches candidate and transition state;
- calculates the exact same 21 learned features without repeatedly rebuilding
  intermediate dictionaries;
- preserves the frozen hard pitch, register, harmony, and mechanical gates;
- keeps learned and deterministic routes side by side.

A deliberately non-zero-weight parity test proves the optimized penalty and
selected path are identical to the frozen scorer and frozen path search.

The realistic full saved-profile benchmark for seven melody events improved
from 28.965 seconds to 6.421 seconds. It returned seven learned events under
model `at-b97d1a6cf902ba05`.

Intentionally unchanged:

- frozen rule-engine files and digest;
- the 21-feature schema and ordered feature names;
- the private model artifact and model ID;
- validation and sealed-test data;
- public runtime behavior;
- auth, DNS, Cloudflare policy, corpus, vectors, and embeddings.

## Files changed

- `steel_guitar_rag/amazing_tablature_runtime.py`
- `tests/test_amazing_tablature_runtime.py`
- `docs/handoffs/task-completions/2026-07-23-2129-05-amazing-tablature-saved-copedent-performance.md`

No files were deleted. Private runtime artifacts remain external and ignored.

## Tests and checks

- `.venv/bin/python -m ruff check steel_guitar_rag/amazing_tablature_runtime.py tests/test_amazing_tablature_runtime.py` — PASS.
- `.venv/bin/python -m py_compile steel_guitar_rag/amazing_tablature_runtime.py` — PASS.
- `.venv/bin/python -m pytest tests/test_amazing_tablature_runtime.py -q` — PASS, 6 tests.
- Focused runtime/API/saved-copedent/UI suite — PASS, 410 tests.
- Full repository suite — PASS, 1,464 tests.
- `node --check ui/melody-workbench.js` — PASS.
- `git diff --check` for the scoped implementation and tests — PASS.
- Frozen-code verification for `atrf-0e5e727332f26367` — PASS.
- Frozen rules-engine digest remained
  `0e5e727332f263672301070a4d3f377880dff0175c8d356879b9278360d9fa49`.
- Freeze status remained `frozen_tests_unopened`.
- Realistic full saved-profile benchmark — PASS, 6.421 seconds, seven
  learned events, exact private model ID.

## Integration notes

Create a new immutable release from the resulting commit. Start it with the
existing private preview environment, then verify a saved-copedent arrangement
through the protected Melody Studio. Do not reuse release `1b586e0`; it
contains the slower adapter.

The official sealed evaluation remains closed. This change is outside the
frozen file manifest and does not authorize a sealed test run.

## Risk assessment

Medium. The optimization is parity-tested and the full suite is green, but
protected browser smoke must still prove end-to-end response time and visible
learned/deterministic comparison behavior under the user's saved copedent.
Rollback is the scoped commit revert; the deterministic fallback remains
available through the private-beta feature flag.

## Human decision needed

No for commit and immutable-release construction. Administrator
authentication may still be required to replace the supervised preview
service after local smoke passes.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_runtime.py`
- `tests/test_amazing_tablature_runtime.py`
- `docs/handoffs/task-completions/2026-07-23-2129-05-amazing-tablature-saved-copedent-performance.md`

## Files that must not be staged

- `corpus-private/**`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`
- all unrelated historical untracked handoffs
- private model artifacts and environment files

## Recommended next lane

Lane 01 exact-path commit, followed by Lane 12 immutable-release and protected
preview smoke.

## Commit readiness

Safe to commit

## Suggested next step

Stage only the three listed files, commit the performance fix, build a new
immutable release, and run local plus authenticated protected Melody Studio
smoke using the saved copedent.
