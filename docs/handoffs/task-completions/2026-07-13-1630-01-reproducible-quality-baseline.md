# Reproducible Quality Baseline

## Task Summary

- Added hash-locked Python 3.12 environments for runtime, RAG, test, and
  deployment dependencies.
- Added a pinned Node 24 toolchain for Wrangler, Cloudflare Workers Vitest,
  ESLint, and core JavaScript checks.
- Added Cloudflare-runtime tests for the Interest-Digest Worker.
- Added CI gates for the full Python suite, JavaScript syntax, Worker runtime
  tests, linting, focused type checks, Python and Node dependency audits,
  secret-pattern scanning, dependency-lock integrity, and asset-size budgets.
- Added `pythonpath = ["."]` to pytest configuration and proved the full suite
  works from a fresh virtual environment without setting `PYTHONPATH`.
- Added missing clean-environment test dependencies (`PyYAML` and `chromadb`)
  after the first fresh-environment run exposed them.
- Kept CommonJS-compatible UI helper loading intact by using `.mjs` only for
  the new ESM tooling configuration.
- Made two no-behavior cleanup edits needed by the new gates: an unused JS
  catch binding and a mypy-safe JWKS cache narrowing.
- Did not modify application feature behavior, RAG routing, corpus, Chroma
  contents, source-inbox, auth policy, DNS, or deployment configuration.

## Files Changed

- `.github/workflows/quality.yml`
- `pyproject.toml`
- `requirements-rag.txt`
- `requirements/README.md`
- `requirements/runtime.in`
- `requirements/runtime.lock`
- `requirements/rag.in`
- `requirements/rag.lock`
- `requirements/test.in`
- `requirements/test.lock`
- `requirements/deployment.in`
- `requirements/deployment.lock`
- `package.json`
- `package-lock.json`
- `eslint.config.mjs`
- `vitest.config.mjs`
- `tests/workers/interest-digest.test.js`
- `scripts/check_asset_size_budget.py`
- `scripts/check_dependency_locks.py`
- `scripts/check_secret_patterns.py`
- `functions/api/interest.js`
- `pocketsteel/cloudflare_access.py`
- `docs/handoffs/task-completions/2026-07-13-1630-01-reproducible-quality-baseline.md`

No files were deleted. Temporary clean virtual environments and compiler logs
were created only under `/tmp`.

## Tests And Checks

- Fresh Python 3.12 virtual environment:
  - installed `requirements/test.lock` with `--require-hashes`;
  - installed the project editable with `--no-deps`;
  - ran `env -u PYTHONPATH .../pytest -q` — 1,028 passed.
- Existing environment focused auth/Worker suite — 56 passed.
- `npm ci --ignore-scripts` — passed from `package-lock.json`.
- `npm run check:js` — passed for Worker, Pages Function, Chat, Explorer,
  Melody, score, fretboard, and Lessons JavaScript.
- `npm run lint:js` — passed.
- `npm run test:worker` — 4 tests passed in the Cloudflare Workers runtime.
- `npm run check:assets` — passed; 51 Explorer chunks and tracked-file budgets.
- `npm run check:locks` — four lock environments passed exact-pin/hash checks.
- `npm run audit:node` — zero vulnerabilities.
- `pip-audit -r requirements/runtime.lock` — no known vulnerabilities.
- Ruff on the security/runtime and new quality scripts — passed.
- Mypy on `cloudflare_access.py` and `runtime_dependencies.py` — passed.
- Secret-pattern scan — passed.
- GitHub Actions workflow YAML parse — passed.
- Hash-locked dry-run resolution was verified locally for all four environments.

## Integration Notes

- Canonical Python installs now use one of `requirements/*.lock`, followed by
  `pip install --no-deps -e .`.
- `requirements-rag.txt` remains as a compatibility entry point and delegates
  to `requirements/rag.lock`.
- The 70 MB retired Explorer monolith is the only explicit 75 MiB legacy file
  allowance. All other tracked files are capped at 2 MiB, Explorer chunks at
  64 KiB each, and the chunk set at 2 MiB.
- CI actions are pinned to reviewed commit SHAs rather than floating tags.
- `package.json` intentionally does not set `type: module`; several established
  browser helper tests load UMD/CommonJS exports through `require()`.
- This loop adds tooling boundaries. Larger API/Melody/Explorer/fretboard and
  curated-answer module decomposition remains a separate refactor loop.

## Risk Assessment

Low to medium. Runtime behavior is unchanged, but dependency locks select a
new reviewed graph and CI now enforces it. The fresh-environment full suite and
both dependency audits reduce the risk. Lock regeneration must use Python 3.12
and pip-tools 7.5.3 as documented.

## Human Decision Needed

No. This is within the approved automated-quality remediation loop.

## Safe-To-Stage Exact File List

- `.github/workflows/quality.yml`
- `pyproject.toml`
- `requirements-rag.txt`
- `requirements/README.md`
- `requirements/runtime.in`
- `requirements/runtime.lock`
- `requirements/rag.in`
- `requirements/rag.lock`
- `requirements/test.in`
- `requirements/test.lock`
- `requirements/deployment.in`
- `requirements/deployment.lock`
- `package.json`
- `package-lock.json`
- `eslint.config.mjs`
- `vitest.config.mjs`
- `tests/workers/interest-digest.test.js`
- `scripts/check_asset_size_budget.py`
- `scripts/check_dependency_locks.py`
- `scripts/check_secret_patterns.py`
- `functions/api/interest.js`
- `pocketsteel/cloudflare_access.py`
- `docs/handoffs/task-completions/2026-07-13-1630-01-reproducible-quality-baseline.md`

## Files That Must Not Be Staged

- `docs/handoffs/task-completions/2026-07-13-1618-12-interest-digest-hardening-deploy.md`
- `docs/handoffs/task-completions/integration-status.md`
- All unrelated dirty/untracked files and all corpus, source-inbox, private,
  vector, generated, screenshot, brand, visual-design, auth-secret, and local
  dependency directories.

## Recommended Next Lane

`01 Repo Steward` for exact-path commit, followed by an isolated module-boundary
refactor loop.

## Commit Readiness

Safe to commit

## Suggested Next Step

Stage only the exact files above, commit the reproducible quality baseline,
then decompose the largest modules behind compatibility exports without
changing public API or browser contracts.
