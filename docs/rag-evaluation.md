# RAG Evaluation

This lightweight evaluation system checks whether Steel Guitar RAG's Electronics-only RAG retrieves useful forum content and produces grounded, practical answers.

## Current Scope

Indexed corpus:

- Steel Guitar Forum - Electronics forum only

Do not add gold questions for Pedal Steel technique, E9 theory, B+C pedals, copedent changes, harmonized scales, tab, or other non-Electronics topics until those sources are actually indexed.

## Files

- `eval/electronics_gold_questions.jsonl`: 20 Electronics-focused questions
- `eval/run_rag_eval.py`: eval runner wrapping the existing RAG answer path
- `eval/results/`: dated eval outputs
- `eval/README.md`: quick usage notes

## Run

From the repo root:

```bash
python3 eval/run_rag_eval.py
```

This creates a dated folder such as:

```text
eval/results/electronics-YYYYMMDD-HHMMSS/
```

The folder contains:

- `results.jsonl`
- `summary.json`

## Result Fields

Each result row preserves:

- question ID, topic, and question text
- generated answer
- retrieved chunks, including full chunk text, excerpt, metadata, rank, and distance
- source thread links
- timestamp
- model/settings, including embedding model, chat model, Chroma path, collection, and top-k
- any question-level error

## Manual Scoring

Each result row includes blank manual scoring fields:

- `retrieval_relevance`: 1-5
- `answer_accuracy`: 1-5
- `electronics_specificity`: 1-5
- `source_grounding`: 1-5
- `practical_usefulness`: 1-5
- `hallucination_risk`: `low`, `medium`, or `high`
- `failure_type`
- `reviewer_notes`

Allowed `failure_type` values:

- `bad_retrieval`
- `weak_chunking`
- `missing_metadata`
- `generic_answer`
- `unsupported_claim`
- `wrong_electronics_logic`
- `citation_problem`
- `good_answer`

## Notes

The runner does not refactor or alter the working RAG pipeline. It calls the existing Electronics answer function and stores review artifacts for later inspection.

The runner does not expand evaluation to non-Electronics sources.
