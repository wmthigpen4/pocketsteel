# Module Boundary Remediation

## Task summary

Completed the compatibility-preserving maintainability loop from the approved technical-debt remediation plan. The work separates cohesive contracts, process bootstrap, browser configuration, browser styles, and an oversized interactive regression fixture without changing public API, Melody, Explorer, fretboard, curated-answer, or browser payload contracts.

Intentionally not changed: answer policy, arranger ranking, copedent logic, corpus/retrieval data, auth policy, deployment configuration, private data, product naming, or generated Explorer payloads.

## Files changed

- `steel_guitar_rag/api.py`: retains public `create_app`, `build_arg_parser`, and `main` compatibility while delegating CLI bootstrap.
- `steel_guitar_rag/api_cli.py`: new bounded process/CLI bootstrap boundary.
- `steel_guitar_rag/curated_answers.py`: imports and re-exports stable curated contracts/reference facts.
- `steel_guitar_rag/curated_contracts.py`: new curated-answer value object and compact fact boundary.
- `steel_guitar_rag/fretboard_examples.py`: imports and re-exports fretboard constants/request contracts.
- `steel_guitar_rag/fretboard_contracts.py`: new stable fretboard request/constant boundary.
- `steel_guitar_rag/melody_arranger.py`: imports and re-exports Melody value objects and supported-mode contracts.
- `steel_guitar_rag/melody_models.py`: new Melody request/path value-object boundary.
- `ui/pedal-steel-fretboard.js`: rendering/interaction logic remains here; CSS is externalized.
- `ui/pedal-steel-fretboard-styles.js`: new UMD/CommonJS-compatible style boundary.
- `ui/e9-fretboard-explorer.js`: state and behavior remain here; immutable UI configuration is externalized.
- `ui/e9-fretboard-explorer-config.js`: new UMD/CommonJS-compatible Explorer configuration boundary.
- `ui/e9-fretboard-explorer.html`, `ui/melody-workbench.html`, `ui/steel-guitar-rag-mock.html`: load the new browser boundaries before their consumers.
- `tests/test_e9_explorer_controls_ui.py`: new focused home for the large interactive Explorer regression.
- `tests/test_frontend_answer_ui.py`, `tests/test_pedal_steel_fretboard_ui.py`, `tests/test_same_origin_smoke_server.py`, `tests/test_melody_workbench_ui.py`: boundary/load-order regressions updated.
- `package.json`: core syntax gate covers both new JavaScript boundaries.

No files were deleted. No generated artifacts were created.

## Tests and checks

- `.venv/bin/pytest -q` — **1028 passed** after the final edits.
- Focused fretboard/contract suite — **64 passed**.
- Focused Melody arranger suite — **41 passed**.
- Focused curated-answer selection — **17 passed**.
- Focused frontend/fretboard/same-origin suite — **81 passed** before the final full run.
- Split Explorer/frontend suite — **27 passed**.
- `npm run check:js` — passed, including both new browser modules.
- `npm run lint:js` — passed.
- `npm run test:worker` — **4 passed** in the Cloudflare Workers runtime.
- Ruff on every touched Python module and the new test module — passed.
- Mypy CI scope — passed.
- `pip-audit -r requirements/runtime.lock` — no known vulnerabilities.
- `npm run audit:node` — zero vulnerabilities.
- Dependency-lock, asset-budget, and secret-pattern checks — passed.
- `git diff --check` on the exact scope — passed.

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8894/ui/steel-guitar-rag-mock.html?v=module-boundaries-local`
- Cache-busted URL tested: `http://127.0.0.1:8894/ui/steel-guitar-rag-mock.html?v=module-boundaries-local`
- Exact URL the user should use: protected-preview URL after commit/restart; do not use this stopped local server
- Auth required: no for static surfaces; local API session remained anonymous
- Auth provider: local development scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8894`
- Expected backend port: `8894`
- Expected git HEAD: `e486e6031ac12c02af7966f183062a44d9fc6c2a` plus the reviewed uncommitted boundary diff
- Version endpoint: `/api/version`
- Version endpoint result: not used as a commit identity because the boundary diff was not yet committed
- If version endpoint missing, how version is inferred: exact working tree and cache-busted static URLs
- Whether app root `/` works: not tested in this local slice
- Whether app root `/` is expected to work: yes in the protected preview
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: the stopped local `:8894` server after this handoff
- Known caveats: anonymous local CSP reports received the expected authorization rejection; this did not affect page rendering

Browser results:

- Chat loaded with the four-workspace navigation and no object-string leakage.
- Explorer loaded the lazy manifest/chunk, displayed 37 validated cards, rendered the fretboard, and exercised the new config/style boundaries.
- Melody Studio and Lessons loaded with expected headings and no object-string leakage.
- The new static modules returned 200 with ETag, Last-Modified, immutable caching, and security headers.

## Integration notes

- Public imports remain available from their prior modules; the new Python modules are internal boundaries.
- The new browser modules must load before `pedal-steel-fretboard.js` and `e9-fretboard-explorer.js`, respectively.
- No API schema, response, score, tab, fretboard payload, route ID, or feature-flag change was made.
- This is a runtime/static change and therefore requires exact-path commit, protected-preview restart, `/api/version` verification, and authenticated browser smoke.

## Risk assessment

Low to medium. The refactor is mostly mechanical and the full suite plus local browser smoke are green. The remaining risk is stale protected-preview HTML caching or script load order; cache-busted protected smoke is required. Rollback is the single scoped commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- `package.json`
- `steel_guitar_rag/api.py`
- `steel_guitar_rag/api_cli.py`
- `steel_guitar_rag/curated_answers.py`
- `steel_guitar_rag/curated_contracts.py`
- `steel_guitar_rag/fretboard_examples.py`
- `steel_guitar_rag/fretboard_contracts.py`
- `steel_guitar_rag/melody_arranger.py`
- `steel_guitar_rag/melody_models.py`
- `ui/pedal-steel-fretboard.js`
- `ui/pedal-steel-fretboard-styles.js`
- `ui/e9-fretboard-explorer.js`
- `ui/e9-fretboard-explorer-config.js`
- `ui/e9-fretboard-explorer.html`
- `ui/melody-workbench.html`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_e9_explorer_controls_ui.py`
- `tests/test_frontend_answer_ui.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_pedal_steel_fretboard_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1654-01-module-boundaries.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` in this implementation commit.
- `docs/handoffs/task-completions/2026-07-13-1618-12-interest-digest-hardening-deploy.md` in this implementation commit.
- Every other modified or untracked path not named in the safe-to-stage list, especially corpus, source-inbox, private/generated, brand, public, Neon Sign, deployment asset, and historical handoff paths.

## Recommended next lane

`01 Repo Steward`, then `12 Self-Hosted Deployment` after the exact-path commit.

## Commit readiness

Safe to commit.

## Suggested next step

Proceed under Repo Steward auto-approval: stage only the listed paths, review the cached diff, commit the module-boundary slice, restart the protected preview, and run authenticated cache-busted smoke across Chat, Explorer, Melody Studio, and Lessons.
