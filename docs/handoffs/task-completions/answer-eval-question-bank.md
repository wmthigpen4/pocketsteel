# Answer Eval Question Bank

## Task summary
- What was requested: read the repo guidance, existing answer/eval/UI smoke surfaces, then create answer-eval planning artifacts with at least 250 JSONL questions across the required buckets.
- What was completed: created a 264-question JSONL answer-eval bank, added expected behavior guidance, added an answer-eval README, validated every JSONL row, and ran relevant answer-eval/red-team/exploratory/frontend/fretboard tests.
- What was intentionally not changed: no runtime implementation, answer routing, retrieval, Chroma/vector stores, embeddings, corpus data, source-inbox files, scraping, deployment, DNS, auth, UI runtime, or browser smoke harness code was changed.

## Files changed
- Changed files:
  - None from this task.
- Created files:
  - `tests/answer_eval/question_bank.jsonl`
  - `tests/answer_eval/expected_behaviors.md`
  - `tests/answer_eval/README.md`
  - `docs/handoffs/task-completions/answer-eval-question-bank.md`
- Deleted files:
  - None.
- Generated artifacts:
  - None outside the requested repository planning artifacts.

## Question counts by bucket
- Valid forum-wisdom steel questions: 22
- Copedent-aware position questions: 22
- Fretboard-rendering questions: 22
- Gear diagnosis questions: 22
- Practice-plan questions: 22
- Tab/interval explainer questions: 22
- Source-required questions: 22
- Off-domain guardrail questions: 22
- Impossible or abusive large-output questions: 22
- Regression cases from known failures: 22
- Home-screen TRY ASKING prompt questions: 22
- Ambiguous steel terms that need clarification or careful routing: 22
- Total: 264

## Coverage notes
- Concrete steel-guitar topics included:
  - E9 9th string
  - wound 6th string
  - string 6 lower
  - B+C pedals
  - E-lower position
  - A+B position
  - F lever
  - vertical lever
  - diminished chords
  - blocking
  - bar slants
  - volume pedal
  - Fender Steel King
  - hum/buzz diagnosis
  - playing behind a singer
  - harmonized scales
  - tab explanation
  - copedent-specific position finding
- Regression coverage includes:
  - `[object Object]`
  - weak-source warning leakage
  - raw SGF fragment answers
  - missing source links/cards where sources are required
  - non-position questions showing fretboards
  - position questions missing fretboards
  - stale protected-preview behavior
  - invalid chord prompts
  - missing-context prompts
  - off-domain and large-output retrieval leaks

## Implementation hooks discovered but not changed
- `scripts/run_answer_eval.py`
  - Current lightweight eval harness reads `tests/fixtures/user_question_bank.json`.
  - It does not currently read JSONL or the richer expected-domain/source/fretboard metadata.
- `scripts/run_full_answer_quality_eval.py`
  - Current strict local eval also uses the existing JSON question bank and layered evaluator logic.
- `scripts/run_product_red_team_smoke.py`
  - Current product red-team matrix uses `tests/fixtures/product_red_team_prompt_matrix.json`.
  - This is the closest existing smoke harness to the new JSONL bank, but wiring was intentionally left for a scoped future QA task.
- `scripts/run_exploratory_answer_smoke.py`
  - Current broad exploratory smoke has built-in question lists and failure detectors.
- Frontend/UI smoke tests discovered:
  - `tests/test_frontend_answer_ui.py`
  - `tests/test_pedal_steel_fretboard_ui.py`
  - `tests/test_same_origin_smoke_server.py`
  - These were not changed because this task is an eval question-bank planning task.

## Tests and checks
- Exact commands run:
  ```bash
  git status --short
  git diff --check
  .venv/bin/python - <<'PY'
  import json
  from collections import Counter
  from pathlib import Path
  required={'id','bucket','question','expected_domain','expected_intent','retrieval_allowed','sources_required','fretboard_allowed','copedent_required','expected_answer_shape','must_include','must_not_include','notes'}
  path=Path('tests/answer_eval/question_bank.jsonl')
  counts=Counter(); ids=set()
  for line_number,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
      row=json.loads(line)
      missing=required-row.keys()
      if missing: raise SystemExit(f'line {line_number} missing {sorted(missing)}')
      if row['id'] in ids: raise SystemExit(f'duplicate id {row["id"]}')
      ids.add(row['id']); counts[row['bucket']]+=1
  print(f'validated {len(ids)} rows')
  for bucket,count in counts.items(): print(f'{bucket}: {count}')
  PY
  .venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py tests/test_product_red_team_smoke.py tests/test_exploratory_answer_smoke.py tests/test_frontend_answer_ui.py tests/test_pedal_steel_fretboard_ui.py
  ```
- Results:
  - `git status --short`: showed a broad pre-existing dirty worktree plus the new `tests/answer_eval/` files.
  - `git diff --check`: passed.
  - JSONL validation: `validated 264 rows`, with 22 rows in each required bucket.
  - Focused pytest set: `133 passed`.
- Tests skipped and why:
  - Full pytest was not run because this task only added planning fixtures/docs and did not alter runtime or test harness behavior.
  - No live smoke was run because the request was to create/update eval/test-planning artifacts, not execute the new bank against a server.

## Integration notes
- The new bank is not currently wired into any evaluator.
- Future wiring should preserve all row metadata:
  - `expected_domain`
  - `expected_intent`
  - `retrieval_allowed`
  - `sources_required`
  - `fretboard_allowed`
  - `copedent_required`
  - `must_include`
  - `must_not_include`
- The bank is intended as a broad product-eval source, not a replacement for:
  - `tests/fixtures/user_question_bank.json`
  - `tests/fixtures/product_red_team_prompt_matrix.json`
  - existing smoke scripts
- Schema/API/component/data contract changes:
  - None to runtime contracts.
  - New planning-fixture schema documented in `tests/answer_eval/README.md`.
- Assumptions:
  - JSONL is acceptable as a planning fixture even though current eval harnesses use JSON.
  - Some rows allow fretboard payloads while not requiring them; a future harness should decide pass/fail by expected intent and prompt context.
- Blockers:
  - None for the planning artifact.
- Human decisions needed:
  - Yes before wiring this bank into automated CI/smoke because pass/fail semantics should be selected deliberately.

## Risk assessment
- Risk: Low.
- Why: this task added static eval-planning artifacts only. Existing relevant tests passed, and no runtime behavior was modified.
- Rollback notes:
  - Remove `tests/answer_eval/question_bank.jsonl`, `tests/answer_eval/expected_behaviors.md`, `tests/answer_eval/README.md`, and this handoff.

## Commit readiness
Safe to commit

## Suggested next step
- Recommended lane: Lane 15 QA / Answer Eval.
- Exact next Codex prompt:
  ```text
  LANE: 15 QA / Answer Eval
  REASONING: MEDIUM

  Wire tests/answer_eval/question_bank.jsonl into a local-only eval runner without changing runtime answer behavior. Preserve the row metadata fields, support bucket filters and JSON/Markdown output to /tmp by default, and add tests that validate JSONL loading plus a few mocked pass/fail classifications. Do not touch Chroma, embeddings, corpus data, scraping, deployment, DNS, auth, or UI runtime code.
  ```
