# RAG Evaluation

This directory contains lightweight evaluation scaffolding for The Turnaround.

Current scope: Steel Guitar Forum Electronics forum only.

Run the full Electronics eval set:

```bash
python3 eval/run_rag_eval.py
```

For a smoke run:

```bash
python3 eval/run_rag_eval.py --limit 3
```

Each run writes a dated folder under `eval/results/` containing:

- `results.jsonl`: one row per question with the generated answer, retrieved chunks, source thread links, model/settings, timestamp, and manual scoring placeholders
- `summary.json`: run metadata and aggregate counts

Manual scoring fields are left blank for review:

- `retrieval_relevance`: 1-5
- `answer_accuracy`: 1-5
- `electronics_specificity`: 1-5
- `source_grounding`: 1-5
- `practical_usefulness`: 1-5
- `hallucination_risk`: `low`, `medium`, or `high`
- `failure_type`: `bad_retrieval`, `weak_chunking`, `missing_metadata`, `generic_answer`, `unsupported_claim`, `wrong_electronics_logic`, `citation_problem`, or `good_answer`
- `reviewer_notes`

Do not add non-Electronics gold questions until those forums are indexed.

