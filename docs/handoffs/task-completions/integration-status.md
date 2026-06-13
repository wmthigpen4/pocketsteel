# Integration Status Snapshot

Generated for ChatGPT reset/guidance on branch `feature/answer-api`.

## 1. Current overall project state

- Current branch: `feature/answer-api`.
- Current HEAD: `7be3ce0 Add invalid chord symbol guardrail`.
- Current `git diff --check`: passed.
- Current index: empty; nothing is staged.
- Private preview remains protected by Cloudflare Access.
- Latest full pytest reported by handoffs: `585 passed` from Lane 05 final red-team blocker fix.
- Latest Lane 15 final red-team rerun did not rerun full pytest because it changed no runtime/QA files, but targeted checks passed.
- Latest smoke status from handoffs:
  - Protected-preview invalid-chord smoke: `17/17` prompts passed.
  - Home-prompt hard failures: `18 -> 0 -> 0`.
  - Product red-team hard failures: `28 -> 4 -> 0`.
  - Final product red-team matrix: `51 total / 51 pass / 0 warn / 0 fail`.
- Outside testers are no longer blocked by these covered QA suites, but still need a human burn-in/go-live decision.
- New coordination/guidance work is present but uncommitted:
  - expanded `AGENTS.md`
  - `docs/llm-guidance/`
  - `tests/answer_eval/`
  - `docs/handoffs/task-completions/llm-guidance-bootstrap.md`
  - `docs/handoffs/task-completions/answer-eval-question-bank.md`
- `docs/handoffs/task-completions/integration-status.md` is a coordination artifact and should remain unstaged unless explicitly approved.

## 2. Recent tasks completed, grouped by active lane

### 01 Repo Steward

- Committed deterministic answer-routing and QA work in `3bb0ded`.
- Committed invalid chord-symbol guardrail in `7be3ce0`.
- Refreshed integration status after protected-preview invalid-chord smoke and final red-team reruns.
- Added uncommitted guidance bootstrap docs for future Codex/LLM lanes:
  - repo protocol in `AGENTS.md`
  - answer contract guidance
  - eval rubric
  - product memory
  - known failures

### 05 Backend / RAG Integration

- Committed:
  - B9/E-lower fretboard payload
  - beginner chord-concept deterministic routing
  - practical advice intent-mode routing
  - invalid chord-symbol guardrail
- Latest uncommitted backend work from Lane 05 final red-team handoffs:
  - A+B concept prompts route to deterministic pedal-combination explanation.
  - `Where is a G chord on E9?` routes to deterministic G major positions with top-level fretboard payload.
  - string-5-with-A-pedal interval questions answer from E9 string/pedal facts.
  - full/partial voicing prompts ask for missing fret, strings/grip, pedals/levers, and chord/key before classification.
  - broader home/red-team guardrails and practical coaching routes remain test-green in handoffs but not yet committed.

### 06 UX/UI Design

- Committed fretboard UI positions, reasons, tabs/colors/direct display, cache-bust behavior, and interactive selector work.
- Uncommitted UI copy candidates remain:
  - home-underneath copy
  - home prompt quality pass
- Minor UI polish note remains from protected-preview smoke:
  - deterministic selector text can expose implementation-style metadata such as `full_chord_position`.

### 12 Self-Hosted Deployment / Ops

- Protected-preview invalid-chord smoke passed using a human-authenticated Cloudflare Access session.
- No DNS, deployment, Tunnel, Access, `.wrangler`, private env, or server config changes are part of the current safe-to-stage candidates.

### 15 QA / Answer Eval

- Product red-team matrix is clear at `51 pass / 0 warn / 0 fail`.
- Home-prompt smoke is clear for hard failures at `34 pass / 5 warn / 0 fail`.
- Recurring invalid-chord smoke coverage is handoff-green.
- New uncommitted broad answer-eval planning fixture exists under `tests/answer_eval/`:
  - `264` JSONL prompts across `12` buckets.
  - Focused validation/tests reported `133 passed`.
  - Not wired into runtime or CI yet.

### 18 Product / Architecture

- Product/contract docs remain parked unless explicitly requested.
- New `docs/llm-guidance/product-memory.md` captures product identity, promise, source layers, and current user copedent facts.

### 19 Visual Design / Assets

- Visual/design assets and raw brand files remain parked.
- Do not stage `Neon Sign/`, `public/`, `ui/brand/`, large `.mov`, `.aep`, autosaves, or design-working files without dedicated review.

## 3. Files changed across recent tasks

### Committed baseline

- `7be3ce0 Add invalid chord symbol guardrail`
  - `pocketsteel/curated_answers.py`
  - `pocketsteel/fretboard_examples.py`
  - `tests/test_api_search.py`
  - `tests/test_fretboard_examples.py`
  - `docs/handoffs/task-completions/2026-06-13-2352-05-invalid-chord-symbol-guardrail.md`

### Lane 05 backend red-team fixes

- `pocketsteel/answer_contracts.py`
- `pocketsteel/curated_answers.py`
- `pocketsteel/fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-14-0117-05-red-team-blocker-cluster-fix.md`
- `docs/handoffs/task-completions/2026-06-14-0127-05-final-red-team-blockers.md`

### Lane 15 QA smoke/red-team tooling

- `scripts/run_exploratory_answer_smoke.py`
- `tests/test_exploratory_answer_smoke.py`
- `scripts/run_product_red_team_smoke.py`
- `tests/fixtures/product_red_team_prompt_matrix.json`
- `tests/test_product_red_team_smoke.py`
- `docs/handoffs/task-completions/2026-06-14-0032-15-recurring-invalid-chord-smoke-coverage.md`
- `docs/handoffs/task-completions/2026-06-14-0052-15-home-prompt-answer-smoke.md`
- `docs/handoffs/task-completions/2026-06-14-0101-15-product-red-team-matrix.md`
- `docs/handoffs/task-completions/2026-06-14-0120-15-red-team-rerun-after-cluster-fix.md`
- `docs/handoffs/task-completions/2026-06-14-0129-15-final-red-team-rerun.md`

### LLM guidance and eval-planning docs

- `AGENTS.md`
- `docs/llm-guidance/answer-contract.md`
- `docs/llm-guidance/eval-rubric.md`
- `docs/llm-guidance/product-memory.md`
- `docs/llm-guidance/known-failures.md`
- `docs/handoffs/task-completions/llm-guidance-bootstrap.md`
- `tests/answer_eval/README.md`
- `tests/answer_eval/expected_behaviors.md`
- `tests/answer_eval/question_bank.jsonl`
- `docs/handoffs/task-completions/answer-eval-question-bank.md`

### UI copy candidates

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-14-0031-06-home-underneath-rag-copy.md`
- `docs/handoffs/task-completions/2026-06-14-0039-06-home-prompt-quality-pass.md`

### Parked dirty lanes

- Provenance/legal/source policy:
  - `README.md`
  - `corpus_metadata/source_policies/README.md`
  - `corpus_metadata/source_registry.json`
  - `docs/copyright-provenance.md`
  - `docs/corpus-license-policy.md`
  - related provenance/source-policy docs/scripts
- Landing/Cloudflare Pages:
  - `deploy/landing/index.html`
  - `docs/cloudflare-pages-landing.md`
  - `tests/test_public_landing_page.py`
  - `ui/steel-guitar-rag-landing.html`
  - `deploy/landing/brand/`
  - `public/`
  - `ui/brand/`
- Source-inbox/private ingestion:
  - `docs/source-inbox-inventory.md`
  - `source-inbox/inventory.json`
  - `source-inbox/provenance.json`
  - private/source ingestion scripts and configs
- Root RAG/build/chunk scripts:
  - `rag_answer.py`
  - `rag_build_clean_corpus.py`
  - `rag_chunk_corpus.py`
  - `rag_embed_chroma.py`
  - `scripts/chunk_corpus.py`
  - `tests/test_chunk_corpus.py`
- Deployment/smoke docs/server:
  - `docs/current-commands.md`
  - `scripts/serve_answer_smoke.py`

## 4. Conflicts or overlapping changes

- `pocketsteel/answer_contracts.py`, `pocketsteel/curated_answers.py`, `pocketsteel/fretboard_examples.py`, and `tests/test_api_search.py` overlap between multiple backend answer-routing lanes.
- `scripts/run_product_red_team_smoke.py` overlaps between product red-team matrix tooling and QA matcher updates.
- `scripts/run_exploratory_answer_smoke.py` and `tests/test_exploratory_answer_smoke.py` overlap between recurring invalid-chord and home-prompt smoke coverage.
- `ui/steel-guitar-rag-mock.html` and `tests/test_frontend_answer_ui.py` overlap between home-underneath copy and home prompt quality pass.
- `AGENTS.md`, `docs/llm-guidance/`, and `tests/answer_eval/` are docs/planning guidance and should not be mixed with runtime answer-routing commits.
- Hunk-level staging may be needed if committing overlapping backend or UI lanes separately.
- Do not use `git add .`.

## 5. Schema/API/component/data contract changes

- Public `/api/answer` response shape remains unchanged.
- `response.fretboard.positions` remains the frontend fretboard visual contract.
- Latest uncommitted backend behavior additions:
  - expanded `scope_guardrail` for off-domain and large-output prompts
  - expanded malformed chord guardrail for `Cmajorish` and `G/F`
  - expanded home-prompt coaching modes
  - expanded missing-context clarification
  - concrete deterministic A+B-in-G movement answer with fretboard payload
  - A+B concept deterministic explanation
  - G-on-E9 deterministic visual routing
  - string-5-with-A-pedal interval explanation
  - full/partial voicing missing-context clarifier
  - source-backed forum-wisdom summaries with source cards preserved where appropriate
- New guidance/planning contracts:
  - `docs/llm-guidance/answer-contract.md` defines the answer classification shape and allowed answer behaviors.
  - `docs/llm-guidance/eval-rubric.md` defines pass/fail expectations.
  - `tests/answer_eval/question_bank.jsonl` defines a planning fixture schema for broad answer-quality smoke.
- No Chroma/vector, embedding, scraper, DNS, deployment, auth, or storage contract changed.

## 6. Tests reported by each lane

- Invalid chord guardrail commit:
  - full pytest: `551 passed`
  - `git diff --check`: passed
- Protected-preview invalid chord smoke:
  - all `17` protected-preview prompts passed
  - targeted pytest: `206 passed` and `54 passed`
  - `git diff --check`: passed
- Lane 05 red-team blocker-cluster fix:
  - `tests/test_api_search.py`: `182 passed`
  - `tests/test_api_contract.py`: `4 passed`
  - focused answer/eval group: `236 passed`
  - `tests/test_fretboard_examples.py`: `39 passed`
  - full pytest: `584 passed`
  - `git diff --check`: passed
- Lane 15 red-team rerun after cluster fix:
  - home-prompt smoke: `39 total / 34 pass / 5 warn / 0 fail`
  - product red-team smoke: `51 total / 47 pass / 0 warn / 4 fail`
  - `tests/test_product_red_team_smoke.py -q`: `9 passed`
  - full pytest: `584 passed`
  - `git diff --check`: passed
- Lane 05 final red-team blocker fix:
  - focused four-blocker regression: `1 passed`
  - focused answer/eval suite: `237 passed`
  - fretboard suite: `39 passed`
  - full pytest: `585 passed`
  - `git diff --check`: passed
- Lane 15 final red-team rerun:
  - direct checks for the four former failures: all passed
  - home-prompt smoke: `39 total / 34 pass / 5 warn / 0 fail`
  - product red-team smoke: `51 total / 51 pass / 0 warn / 0 fail`
  - answer/full eval subset: `50 passed`
  - API/fretboard/contract subset: `226 passed`
  - `git diff --check`: passed
- LLM guidance bootstrap:
  - `git diff --check`: passed
  - no doc lint target found in `pyproject.toml`
  - full pytest skipped because docs/config guidance only
- Answer eval question bank:
  - JSONL validation: `264` rows, `22` in each of `12` buckets
  - focused pytest set: `133 passed`
  - `git diff --check`: passed

## 7. Blockers or human decisions needed

- No remaining hard failures are reported for home-prompt smoke.
- No remaining hard failures are reported for the product red-team matrix.
- Outside testers are no longer blocked by these two QA suites, but a human burn-in/go-live decision is still required.
- Human decision needed: approve commit splitting for backend, QA, UI, guidance docs, and eval-planning chunks.
- Human decision needed: decide whether the new LLM guidance layer should be committed before or after backend/QA split commits.
- Human decision needed: decide whether the broad `tests/answer_eval/` planning bank should be committed now or wait until a runner is planned.
- Human decision needed: decide whether protected-preview smoke should rerun after backend/QA chunks are committed.

## 8. Dirty worktree / commit readiness

- Ready for scoped commit splitting with explicit approval:
  - Lane 05 backend red-team fixes.
  - Lane 15 recurring invalid-chord/home-prompt/product-red-team QA tooling.
  - Lane 06 home-underneath/home prompt quality UI copy.
  - LLM guidance docs.
  - Answer-eval planning bank.
- Needs exact-path/hunk staging because several files overlap across lanes.
- Coordination artifacts should stay unstaged unless explicitly approved:
  - `docs/handoffs/task-completions/integration-status.md`
  - Repo Steward refresh handoffs
- Parked:
  - provenance/legal/source policy
  - landing/Cloudflare Pages and brand assets
  - source-inbox/private ingestion
  - root RAG/build/chunk scripts
  - deployment/smoke docs/server changes
  - visual/design docs/assets

## 9. Which files are safe to stage

Exact paths only, with explicit approval:

- Lane 05 backend red-team fixes:
  - `pocketsteel/answer_contracts.py`
  - `pocketsteel/curated_answers.py`
  - `pocketsteel/fretboard_examples.py`
  - `tests/test_api_search.py`
  - `docs/handoffs/task-completions/2026-06-14-0117-05-red-team-blocker-cluster-fix.md`
  - `docs/handoffs/task-completions/2026-06-14-0127-05-final-red-team-blockers.md`
- Lane 15 QA smoke/red-team tooling:
  - `scripts/run_exploratory_answer_smoke.py`
  - `tests/test_exploratory_answer_smoke.py`
  - `scripts/run_product_red_team_smoke.py`
  - `tests/fixtures/product_red_team_prompt_matrix.json`
  - `tests/test_product_red_team_smoke.py`
  - `docs/handoffs/task-completions/2026-06-14-0032-15-recurring-invalid-chord-smoke-coverage.md`
  - `docs/handoffs/task-completions/2026-06-14-0052-15-home-prompt-answer-smoke.md`
  - `docs/handoffs/task-completions/2026-06-14-0101-15-product-red-team-matrix.md`
  - `docs/handoffs/task-completions/2026-06-14-0120-15-red-team-rerun-after-cluster-fix.md`
  - `docs/handoffs/task-completions/2026-06-14-0129-15-final-red-team-rerun.md`
- Lane 06 UI copy:
  - `ui/steel-guitar-rag-mock.html`
  - `tests/test_frontend_answer_ui.py`
  - `docs/handoffs/task-completions/2026-06-14-0031-06-home-underneath-rag-copy.md`
  - `docs/handoffs/task-completions/2026-06-14-0039-06-home-prompt-quality-pass.md`
- LLM guidance layer:
  - `AGENTS.md`
  - `docs/llm-guidance/answer-contract.md`
  - `docs/llm-guidance/eval-rubric.md`
  - `docs/llm-guidance/product-memory.md`
  - `docs/llm-guidance/known-failures.md`
  - `docs/handoffs/task-completions/llm-guidance-bootstrap.md`
- Answer-eval planning bank:
  - `tests/answer_eval/README.md`
  - `tests/answer_eval/expected_behaviors.md`
  - `tests/answer_eval/question_bank.jsonl`
  - `docs/handoffs/task-completions/answer-eval-question-bank.md`
- Coordination-only, only with explicit approval:
  - `docs/handoffs/task-completions/integration-status.md`

## 10. Which files should remain unstaged

- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, DBs, logs, generated reports.
- `/tmp` smoke/eval reports.
- Raw `source-inbox` content and `source-inbox/provenance.json`.
- `.wrangler/`, private env files, deployment secrets, DNS/deploy artifacts.
- `Neon Sign/`, `public/`, `ui/brand/`, `deploy/landing/brand/`, large `.mov`, `.aep`, autosaves, and design-working files.
- Provenance/legal/source-policy files unless explicitly requested.
- Root RAG/build scripts unless explicitly requested.
- Landing/Cloudflare Pages files unless explicitly requested.
- Any broad dirty lane not listed in the exact safe-to-stage paths above.

## 11. Recommended next tasks by lane

- 01 Repo Steward:
  - Split and commit the test-green backend, QA, UI, guidance, and eval-planning chunks using exact-path/hunk staging.
- 15 QA / Answer Eval:
  - Decide whether to wire `tests/answer_eval/question_bank.jsonl` into a local-only evaluator.
- 12 Self-Hosted Deployment / Ops:
  - After commit splitting, rerun protected-preview smoke if the human wants preview confidence before outside testers.
- 06 UX/UI Design:
  - Optionally handle selector metadata polish after commit splitting.

## 12. Exact Codex prompts for the next recommended tasks

### Lane 01 Repo Steward - split current safe commits

```text
LANE: 01 Repo Steward
REASONING: HIGH
Branch: feature/answer-api

Split and commit the cleared backend/QA/UI/guidance chunks documented in docs/handoffs/task-completions/integration-status.md.

Do not use git add .
Do not stage corpus-private/, corpus-v2/, Chroma/vector stores, embeddings, source-inbox raw/provenance files, generated reports, .wrangler/, public/, ui/brand/, Neon Sign/, DNS/deploy/secrets files, provenance/legal files, root RAG/build scripts, landing/Cloudflare Pages files, or unrelated dirty lanes.

Recommended order:
1. Lane 05 backend red-team fixes.
2. Lane 15 QA smoke/red-team tooling.
3. Lane 06 UI copy changes.
4. LLM guidance layer docs.
5. Answer-eval planning bank.
6. Coordination-doc commit only if explicitly approved.

Before each commit:
git diff --cached --name-only
git diff --cached --check

After all commits:
.venv/bin/python -m pytest
git diff --check

Expected handoff:
docs/handoffs/task-completions/2026-06-13-HHMM-01-guidance-and-final-red-team-commit-split.md
```

### Lane 15 QA / Answer Eval - wire planning bank

```text
LANE: 15 QA / Answer Eval
REASONING: MEDIUM
Branch: feature/answer-api

Plan a local-only evaluator for tests/answer_eval/question_bank.jsonl without changing runtime answer behavior.

Hard exclusions:
Do not touch Chroma/vector stores, embeddings, corpus-private/, corpus-v2/, source-inbox raw/provenance files, generated reports, .wrangler/, DNS/deploy/secrets files, provenance/legal files, public/, ui/brand/, Neon Sign/, or unrelated dirty lanes.

Inspect:
tests/answer_eval/README.md
tests/answer_eval/expected_behaviors.md
tests/answer_eval/question_bank.jsonl
scripts/run_answer_eval.py
scripts/run_full_answer_quality_eval.py
scripts/run_product_red_team_smoke.py

Stop after a plan unless implementation is explicitly approved.

Expected handoff:
docs/handoffs/task-completions/2026-06-13-HHMM-15-answer-eval-bank-runner-plan.md
```

### Lane 12 Self-Hosted Deployment - protected-preview smoke after commit split

```text
LANE: 12 Self-Hosted Deployment
REASONING: MEDIUM
Branch: feature/answer-api

After Repo Steward commits the backend/QA chunks, rerun authenticated protected-preview smoke for invalid chords, home prompts, and product red-team sentinel prompts.

Hard exclusions:
Do not deploy, change DNS, modify auth, touch Chroma/vector stores, embeddings, corpus-private/, corpus-v2/, source-inbox raw files, provenance/legal files, .wrangler/, public/, ui/brand/, Neon Sign/, or design assets unless explicitly approved.

Run only smoke/read-only checks against the approved preview target.

Expected handoff:
docs/handoffs/task-completions/2026-06-13-HHMM-12-protected-preview-final-red-team-smoke.md
```

Recommended immediate next step: Repo Steward should split and commit the safe docs/backend/QA/UI chunks with exact-path/hunk review, starting with the backend red-team fixes or the docs-only LLM guidance layer depending on human priority.

Commit readiness: partially ready. Several chunks are handoff-green and safe with exact staging, but the worktree is broad and dirty, so `git add .` is not acceptable.

Whether browser smoke is needed: not before commit splitting. Protected-preview smoke is recommended after backend/QA commits if the human wants preview confidence before outside testers.

Whether answer eval is needed: not for this docs-only refresh. The answer-eval planning bank needs a separate Lane 15 decision before wiring.

Whether product/design work is safe to start: safe to plan, but commit splitting should happen first to reduce worktree risk.
