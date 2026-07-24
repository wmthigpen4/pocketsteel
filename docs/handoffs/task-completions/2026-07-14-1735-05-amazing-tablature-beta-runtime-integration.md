# Amazing Tablature beta runtime integration

## Task summary

- Integrated the explicitly approved challenger `at-44c59f08724d501e` as the runtime Amazing Tablature beta policy.
- Copied only the sanitized, copedent-neutral promotion contract into public runtime code: exact weights, feature names, schema identifiers, example count, model ID, and beta status.
- Applied the learned score only after deterministic pitch, register, harmony, control-effect, phrase-role, pocket, texture, and voice-leading constraints. Hard mechanics remain authoritative.
- Mapped Best Fit phrase roles onto approved learned style families instead of inventing untrained `auto` weights.
- Did not expose source material, annotations, source actions, private profile data, or private paths. Did not change auth, corpus, Chroma, embeddings, scraping, DNS, Tunnel, secrets, or deployment policy.

## Files changed

- `steel_guitar_rag/amazing_tablature_model.py` — sanitized immutable beta model contract.
- `steel_guitar_rag/melody_decision_rules.py` — exposes exact approved model identity and public audit metadata.
- `steel_guitar_rag/melody_ranker.py` — keeps the compatibility trainer on the ranker contract version rather than mislabeling new output as the approved runtime model.
- `steel_guitar_rag/melody_arranger.py` — adds the learned copedent-neutral tie-break score within deterministic constraints.
- `tests/test_amazing_tablature_training.py`
- `tests/test_copedent_transfer.py`
- `tests/test_melody_arranger_decision_fixtures.py`
- `docs/llm-guidance/melody-copedent-transfer-rules.md`
- This handoff.
- No files deleted. Private promotion/evaluation artifacts remain ignored under `corpus-private/melody-decisions/`.

## Tests and checks

- Promotion artifact/runtime exactness check — passed for model ID, status, schema, feature schema, feature names, example count, copedent-neutral flag, and all style weights.
- Focused Python tests — 69 passed.
- Regression tests after ranking-order adjustment — 32 passed.
- Full test suite: `.venv/bin/python -m pytest -q` — 1,125 passed.
- `npm run check:js` — passed.
- `node --check ui/answer-client.js` — passed.
- `node --check ui/melody-workbench.js` — passed.
- Ruff on touched Python files and tests — passed.
- `git diff --check` — passed.
- `.venv/bin/python scripts/amazing_tablature.py status` — beta channel points to `at-44c59f08724d501e`; stable remains unset.

## Local smoke target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8890/ui/melody-workbench.html?v=amazing-tablature-beta-local-20260714&access=beta_user`
- Cache-busted URL tested: `http://127.0.0.1:8890/ui/melody-workbench.html?v=amazing-tablature-beta-local-20260714&access=beta_user`
- Exact URL the user should use: protected-preview URL to be supplied by Lane 12 after exact-commit restart
- Auth required: yes, local development role scaffold
- Auth provider: scaffold
- Cloudflare Access login result: not attempted; local smoke does not prove Access behavior
- Local backend URL: `http://127.0.0.1:8890`
- Expected backend port: 8890
- Expected git HEAD: uncommitted reviewed worktree at smoke time
- Version endpoint: `/api/version`
- Version endpoint result: not used as proof before commit
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not tested in this focused local smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested in this focused local smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex only; the user should use the later protected URL
- Do not test these URLs: local port 8890 as proof of protected-preview or Cloudflare Access behavior
- Known caveats: local browser smoke is not protected-preview smoke

## Local browser result

- `1 2 3 5` in G produced synchronized score, tab, fretboard, and note steps.
- Best Fit rendered initially; switching to Pocket Playing rebuilt the result, updated the explanation, and changed the tab.
- Browser warnings/errors: none.
- An unauthenticated content request returned 401 before the authenticated local role was used.

## Integration notes

- Approved model ID: `at-44c59f08724d501e`.
- Dataset hash: `e89b79c3e290621191444de661f5ad7107048b80a0d1ba1cacba7b662ce9a103`.
- Model SHA-256: `5fb3f4013b7d7b32906accf94f2442cd2d458bbffc47368d79c9ab44fe082a2d`.
- Promotion report SHA-256: `a8498bb97b2706aa37d0d6738a5a3c997db2e4fe833637d62579d5642a00d350`.
- Evaluation: mechanical accuracy 1.0, preference accuracy 1.0, six held-out examples, no privacy findings.
- Batch: 51 accepted annotations; 45 training examples; six holdouts; zero blocking exceptions; six nonblocking audit samples.
- No API schema removal or stored-data migration is involved.

## Risk assessment

- Medium. All automated and local browser checks pass, and deterministic mechanics remain hard constraints. The evidence base is still the first batch with 45 training examples and six holdouts, so beta quality should not be represented as stable quality.
- Rollback is a normal reviewed revert of the runtime integration commit followed by the documented protected-preview restart. No private dataset mutation is required.

## Human decision needed

- No for beta runtime integration. The exact beta model was explicitly approved.
- Stable promotion remains unapproved and requires a separate exact-model decision plus independent Lane 15 readiness.

## Safe-to-stage exact file list

- `steel_guitar_rag/amazing_tablature_model.py`
- `steel_guitar_rag/melody_decision_rules.py`
- `steel_guitar_rag/melody_ranker.py`
- `steel_guitar_rag/melody_arranger.py`
- `tests/test_amazing_tablature_training.py`
- `tests/test_copedent_transfer.py`
- `tests/test_melody_arranger_decision_fixtures.py`
- `docs/llm-guidance/melody-copedent-transfer-rules.md`
- `docs/handoffs/task-completions/2026-07-14-1735-05-amazing-tablature-beta-runtime-integration.md`
- `docs/handoffs/task-completions/2026-07-14-1736-15-amazing-tablature-beta-runtime-qa.md`

## Files that must not be staged

- Everything under `corpus-private/`, including the promotion artifact, annotations, evaluations, reports, models, and source material.
- Existing unrelated dirty/untracked files, including corpus/source inventories, source inbox files, brand/design assets, generated media, deployment material, and `docs/handoffs/task-completions/integration-status.md`.

## Recommended next lane

- Lane 15 for the independent runtime QA gate, then Lane 01 exact-path commit and Lane 12 protected-preview verification.

## Commit readiness

Safe to commit

## Suggested next step

- `Lane 01: Run ExactPathCommit using docs/handoffs/task-completions/2026-07-14-1736-15-amazing-tablature-beta-runtime-qa.md.`
