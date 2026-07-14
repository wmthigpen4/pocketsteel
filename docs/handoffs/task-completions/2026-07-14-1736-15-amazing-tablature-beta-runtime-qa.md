# Amazing Tablature beta runtime QA

## Task summary

- Independently checked the Lane 05 integration of approved beta model `at-44c59f08724d501e` against the promotion contract, deterministic guardrails, focused behavior tests, the full regression suite, and local browser behavior.
- Confirmed the runtime exposes only sanitized copedent-neutral metadata and learned weights.
- Confirmed stable promotion was not performed and private artifacts remain ignored.
- No runtime code was changed as part of the QA conclusion.

## Files changed

- Created this QA handoff only.
- The reviewed implementation files are listed in the safe-to-stage section.

## Tests and checks

- Exact promotion/runtime artifact comparison — passed.
- Focused beta contract, copedent transfer, arranger decision, Melody Studio, and frontend tests — 69 passed.
- Targeted regression rerun after cost-order correction — 32 passed.
- Full suite: `.venv/bin/python -m pytest -q` — 1,125 passed.
- `npm run check:js` — passed.
- Ruff on all touched Python/test paths — passed.
- `git diff --check` — passed.
- Local browser smoke — passed with no warnings/errors and a successful style-triggered rebuild.
- Private promotion artifact ignore check — passed via `git check-ignore`.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8890/ui/melody-workbench.html?v=amazing-tablature-beta-local-20260714&access=beta_user`
- Cache-busted URL tested: `http://127.0.0.1:8890/ui/melody-workbench.html?v=amazing-tablature-beta-local-20260714&access=beta_user`
- Exact URL the user should use: pending Lane 12 protected-preview smoke after commit
- Auth required: yes, local development role scaffold
- Auth provider: scaffold
- Cloudflare Access login result: not attempted
- Local backend URL: `http://127.0.0.1:8890`
- Expected backend port: 8890
- Expected git HEAD: uncommitted reviewed worktree at smoke time
- Version endpoint: `/api/version`
- Version endpoint result: not used as proof before commit
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not tested in this focused smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested in this focused smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex only
- Do not test these URLs: local port 8890 as proof of Cloudflare Access or protected-preview behavior
- Known caveats: protected-preview authentication and exact committed version still require Lane 12 verification

## Integration notes

- The approved beta ranker is a subordinate deterministic tie-breaker; it cannot relax hard pitch, register, harmony, control-effect, melody-on-top, or fallback validation.
- Best Fit resolves to an approved family by phrase role and does not use invented `auto` weights.
- The initial learned-score placement caused four existing deterministic arrangement regressions. Lane 05 moved the score behind the structural and texture constraints; the exact failing tests and the full suite then passed.
- The beta registry points to `at-44c59f08724d501e`; stable remains unset.

## Risk assessment

- Medium. Regression and privacy gates are green, but the first evidence set is intentionally small: 45 training decisions and six holdouts. Beta observation should continue before any stable proposal.
- Rollback requires a reviewed revert plus normal protected-preview restart; no dataset or profile migration is involved.

## Human decision needed

- No. Exact beta approval has already been given. Stable promotion is outside this approval.

## Safe-to-stage exact file list

- `pocketsteel/amazing_tablature_model.py`
- `pocketsteel/melody_decision_rules.py`
- `pocketsteel/melody_ranker.py`
- `pocketsteel/melody_arranger.py`
- `tests/test_amazing_tablature_training.py`
- `tests/test_copedent_transfer.py`
- `tests/test_melody_arranger_decision_fixtures.py`
- `docs/llm-guidance/melody-copedent-transfer-rules.md`
- `docs/handoffs/task-completions/2026-07-14-1735-05-amazing-tablature-beta-runtime-integration.md`
- `docs/handoffs/task-completions/2026-07-14-1736-15-amazing-tablature-beta-runtime-qa.md`

## Files that must not be staged

- All `corpus-private/` content and all unrelated dirty/untracked files.
- `docs/handoffs/task-completions/integration-status.md`, which already contains unrelated coordination changes and is not part of this implementation commit.
- Source inbox, corpus/vector, database, secret/env, auth, DNS, deployment, brand, design, and generated media paths.

## Recommended next lane

- Lane 01 exact-path commit, followed by Lane 12 protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

- `Lane 01: Run ExactPathCommit using this handoff, then Lane 12: run ProtectedPreviewSmoke for the resulting exact commit.`
