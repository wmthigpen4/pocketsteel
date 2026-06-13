# LLM Guidance Bootstrap

## Task summary

- What was requested: create a permanent shared guidance layer for future Codex/LLM lanes working on Steel Guitar RAG / The Turnaround.
- What was completed: read current repo instructions, answer contract docs, answer guardrails, answer-routing code, structured user copedent code, answer UI references, eval tests, product red-team tests, and recent handoffs; then created guidance docs for answer contracts, eval rubric, product memory, and known failures. Updated `AGENTS.md` to point future lanes at the guidance layer and clarify lane workflow, handoffs, safe staging, testing, and safety expectations.
- What was intentionally not changed: no implementation code, tests, Chroma/vector stores, embeddings, corpus-private, corpus-v2, source-inbox raw/provenance data, scraping, deployment, DNS, `.wrangler`, public/brand/design assets, or generated reports were modified.

## Files changed

- Changed files:
  - `AGENTS.md`
- Created files:
  - `docs/llm-guidance/answer-contract.md`
  - `docs/llm-guidance/eval-rubric.md`
  - `docs/llm-guidance/product-memory.md`
  - `docs/llm-guidance/known-failures.md`
  - `docs/handoffs/task-completions/llm-guidance-bootstrap.md`
- Deleted files:
  - None
- Generated artifacts:
  - None

## Why each file exists

- `AGENTS.md`: repo-level operating model for all future Codex/LLM work, including lanes, safety rules, handoff requirements, staging/commit discipline, and test expectations.
- `docs/llm-guidance/answer-contract.md`: durable answer behavior contract for domain classification, guardrails, source-backed answers, copedent-aware answers, fretboard rendering, gear diagnosis, practice plans, tab/interval explainers, and forbidden behavior.
- `docs/llm-guidance/eval-rubric.md`: shared pass/fail rubric for backend eval, smoke, red-team, and frontend answer rendering regressions.
- `docs/llm-guidance/product-memory.md`: durable product memory covering product identity, promise, future source layers, core product areas, current user copedent facts, readiness memory, and tone.
- `docs/llm-guidance/known-failures.md`: regression memory for known and suspected failures from recent handoffs.
- `docs/handoffs/task-completions/llm-guidance-bootstrap.md`: this task-completion handoff and coordination record.

## How future lanes should use these docs

- All lanes should read `AGENTS.md` first.
- Lane 05 Backend / RAG Integration should read `answer-contract.md`, `known-failures.md`, and `eval-rubric.md` before answer-routing or source behavior changes.
- Lane 15 QA / Answer Eval should read `eval-rubric.md` and `known-failures.md` before adding smoke/eval buckets.
- Lane 06 UX/UI Design should read `answer-contract.md`, `eval-rubric.md`, and `product-memory.md` before changing answer UI or prompt surfaces.
- Lane 02 Corpus Pipeline should read `product-memory.md` and `AGENTS.md` before source-inbox/corpus work.
- Lane 18 Product / Architecture should use `product-memory.md` and `answer-contract.md` as baseline assumptions.
- Lane 01 Repo Steward should use all guidance docs when coordinating commit splits or reset snapshots.

## Tests and checks

- Exact commands run:
  - `sed -n '1,260p' AGENTS.md`
  - `find docs/handoffs/task-completions -maxdepth 1 -type f -name '*.md' -print | sort | tail -30`
  - `git status --short`
  - `find docs -maxdepth 3 -type f \( -name '*answer*' -o -name '*contract*' -o -name '*eval*' -o -name '*guidance*' \) | sort`
  - `sed -n '1,260p' docs/answer-generation-contract.md`
  - `sed -n '1,260p' docs/answer-guardrails.md`
  - `sed -n '1,260p' pocketsteel/curated_answers.py`
  - `sed -n '1,260p' pocketsteel/answer_contracts.py`
  - `rg -n "fretboard|source|Object|warning|answer" ui/answer-client.js ui/steel-guitar-rag-mock.html | head -160`
  - `sed -n '1,220p' tests/test_api_search.py`
  - `sed -n '1,240p' tests/test_exploratory_answer_smoke.py`
  - `sed -n '1,220p' tests/test_product_red_team_smoke.py`
  - `sed -n '1,220p' docs/private-answer-hybrid-plan.md`
  - `sed -n '1,240p' pocketsteel/user_copedent.py`
  - `find docs/llm-guidance -maxdepth 2 -type f -print`
  - `rg -n "User E9|copedent|private profile|Open tuning|Common grips" pocketsteel tests docs | head -120`
- Results:
  - Read-only inspection completed.
- Final checks:
  - `git status --short` completed; intended changes are `AGENTS.md`, the new `docs/llm-guidance/` files, and this handoff, with many pre-existing unrelated dirty/untracked lanes still present.
  - `git diff --check` passed.
  - `git diff --cached --name-only` returned no staged files.
  - `pyproject.toml` was inspected; no dedicated documentation lint/check target was present.
- Tests skipped and why:
  - Full pytest was not run because this is documentation/config guidance only.

## Repo uncertainty

- Naming uncertainty remains: the existing repo instruction says the user-facing app name is The Turnaround, while the requested product memory and many current repo artifacts say Steel Guitar RAG. The guidance preserves both and warns against broad rename work without explicit approval.
- Some guidance is based on uncommitted handoffs and dirty worktree state. Future lanes should inspect current code and current `git status` before relying on any snapshot.
- `docs/llm-guidance/` did not previously exist in the inspected tree.

## Integration notes

- No schema/API/component/data contract changed in code.
- No generated/private/source data was staged or modified.
- Future lanes should treat this as process and product guidance, not as a substitute for reading current implementation.
- Human decisions needed:
  - Whether to commit this guidance layer as a docs-only coordination commit.
  - Whether to resolve the product naming split in a separate Product/Architecture lane.

## Risk assessment

- Risk: Low.
- Why: docs-only guidance update. The main risk is over-constraining future lanes if guidance becomes stale; future handoffs should update it when the answer architecture changes.
- Rollback notes: revert `AGENTS.md` and remove the `docs/llm-guidance/` files plus this handoff.

## Commit readiness

Needs human review first

## Suggested next step

- Recommended lane: `01 Repo Steward`.
- Exact recommended prompt:

```text
LANE: 01 Repo Steward
REASONING: MEDIUM
Branch: feature/answer-api

Review the new LLM guidance layer and prepare a docs-only commit if clean.

Stage only:
AGENTS.md
docs/llm-guidance/answer-contract.md
docs/llm-guidance/eval-rubric.md
docs/llm-guidance/product-memory.md
docs/llm-guidance/known-failures.md
docs/handoffs/task-completions/llm-guidance-bootstrap.md

Run:
git diff --cached --name-only
git diff --cached --check
git diff --check

Do not stage implementation files, generated/private data, Chroma/vector stores, embeddings, corpus-private/, corpus-v2/, source-inbox raw/provenance files, .wrangler/, public/, ui/brand/, Neon Sign/, DNS/deploy/secrets files, provenance/legal files, or unrelated dirty lanes.
```
