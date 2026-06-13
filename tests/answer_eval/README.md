# Answer Eval Question Bank

This directory contains planning fixtures for broad answer-quality evaluation. The files here are not runtime answer logic and are not currently wired into `/api/answer`.

## Files

- `question_bank.jsonl` - 264 evaluation prompts, one JSON object per line.
- `expected_behaviors.md` - manual interpretation guide for smoke and future evaluator wiring.

## JSONL Schema

Each row has this shape:

```json
{
  "id": "valid_forum-wisdom_steel_questions_001",
  "bucket": "Valid forum-wisdom steel questions",
  "question": "What do players say about wound 6th strings on E9?",
  "expected_domain": "steel_guitar",
  "expected_intent": "forum_wisdom",
  "retrieval_allowed": true,
  "sources_required": true,
  "fretboard_allowed": false,
  "copedent_required": false,
  "expected_answer_shape": "source-backed synthesis with consensus, disagreements, and useful source cards",
  "must_include": ["players", "steel"],
  "must_not_include": ["[object Object]", "source support was weak"],
  "notes": "Forum-wisdom rows require retrieval-backed synthesis, not copied fragments."
}
```

## Buckets

The bank contains 22 rows in each bucket:

- Valid forum-wisdom steel questions
- Copedent-aware position questions
- Fretboard-rendering questions
- Gear diagnosis questions
- Practice-plan questions
- Tab/interval explainer questions
- Source-required questions
- Off-domain guardrail questions
- Impossible or abusive large-output questions
- Regression cases from known failures
- Home-screen TRY ASKING prompt questions
- Ambiguous steel terms that need clarification or careful routing

Total rows: 264.

## How To Use

For manual smoke:

1. Start the intended local or protected-preview answer stack.
2. Select a bucket or sample across all buckets.
3. Ask each `question`.
4. Compare the response with `expected_behaviors.md` and the row metadata.
5. Record any mismatch with the row `id`, observed answer, source-card state, fretboard state, and failure symptom.

For future automation:

- The existing lightweight answer eval currently reads `tests/fixtures/user_question_bank.json` through `scripts/run_answer_eval.py`.
- The full local answer-quality eval currently reads the same JSON fixture through `scripts/run_full_answer_quality_eval.py`.
- The product red-team smoke currently reads `tests/fixtures/product_red_team_prompt_matrix.json` through `scripts/run_product_red_team_smoke.py`.
- This JSONL bank is a broader planning fixture. Wire it into an evaluator only in a scoped QA task so the expected-domain/intent/source/fretboard metadata is preserved.

## Validation

To validate the JSONL structure without running the answer stack:

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path

required = {
    "id",
    "bucket",
    "question",
    "expected_domain",
    "expected_intent",
    "retrieval_allowed",
    "sources_required",
    "fretboard_allowed",
    "copedent_required",
    "expected_answer_shape",
    "must_include",
    "must_not_include",
    "notes",
}

path = Path("tests/answer_eval/question_bank.jsonl")
ids = set()
for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
    row = json.loads(line)
    missing = required - row.keys()
    if missing:
        raise SystemExit(f"line {line_number} missing {sorted(missing)}")
    if row["id"] in ids:
        raise SystemExit(f"duplicate id {row['id']}")
    ids.add(row["id"])
print(f"validated {len(ids)} rows")
PY
```

## Scope Notes

- Do not use this fixture to modify Chroma, embeddings, corpus data, source-inbox material, deployment, DNS, or auth behavior.
- Do not copy private source text into this bank.
- Do not treat this bank as a complete source of musical truth; it is a prompt and expected-behavior coverage matrix.
