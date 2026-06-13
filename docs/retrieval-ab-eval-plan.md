# Retrieval A/B Eval Plan

Task mode: GREEN evaluation tooling. This plan and harness do not run live SGF scraping, rebuild embeddings, reset Chroma, modify Chroma stores, switch app config, or change answer quality logic.

## Purpose

Prepare a repeatable v1 vs v2 retrieval comparison for The Turnaround after Phase 3 v2 embeddings finish. The eval should compare the existing v1 Chroma index with the new v2 Chroma index using the same question bank, topK, and reporting format.

## Inputs

- v1 Chroma path: `~/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma`
- v1 collection: `steel_guitar_unified`
- v2 Chroma path: `corpus-v2/vector-stores/chroma`
- v2 collection: `steel_guitar_unified_v2`
- Shared question bank: `tests/fixtures/user_question_bank.json`
- Default topK: `5`

The harness is intentionally inert by default. `--dry-run` validates the question bank and command shape without opening either Chroma store. Real retrieval requires `--run-v1` and/or `--run-v2`; v2 also requires `--confirm-v2-ready`.

## Metrics

The report compares these retrieval-side signals per side and per question:

- source count
- source URL presence
- forum and source-system coverage
- excerpt cleanliness
- duplicate source rate
- `Top`, email, signature, and raw-link leakage in source excerpts
- metadata completeness
- post identity completeness
- retrieval score distribution

The harness can also attach pass/fail information from separately run answer eval JSON files written by `scripts/run_answer_eval.py`. It does not call `/api/answer` itself.

## Safe Dry Run

Use this while v2 embeddings are still running:

```bash
.venv/bin/python scripts/run_retrieval_ab_eval.py \
  --dry-run \
  --question-bank tests/fixtures/user_question_bank.json \
  --top-k 5
```

This command must not open v1 or v2 Chroma.

## Full A/B Command After V2 Embedding Completes

Run only after the v2 embedding process has fully completed and the v2 Chroma store is no longer being written:

```bash
.venv/bin/python scripts/run_retrieval_ab_eval.py \
  --run-v1 \
  --run-v2 \
  --confirm-v2-ready \
  --v1-chroma-path ~/Documents/sgf-scrape-test/corpus-unified/vector-stores/chroma \
  --v1-collection steel_guitar_unified \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2 \
  --question-bank tests/fixtures/user_question_bank.json \
  --top-k 5 \
  --output corpus-v2/reports/retrieval-ab-eval-v1-v2.md \
  --json-output corpus-v2/reports/retrieval-ab-eval-v1-v2.json
```

Optional answer eval attachment, after running answer eval separately against v1 and v2 API configurations:

```bash
  --v1-answer-eval-json /tmp/answer-eval-v1-results.json \
  --v2-answer-eval-json /tmp/answer-eval-v2-results.json
```

Answer eval attachment is for reporting only. The retrieval A/B harness does not start the API, switch environment variables, or generate answers.

## Review Rules

- Treat v2 as a candidate until the report is reviewed.
- V2 should not win only because excerpts are cleaner. It must maintain or improve useful source coverage while reducing source-card noise.
- Any app config switch from v1 to v2 remains a separate human-approved phase.
- If v2 loses coverage or introduces source identity gaps, keep the app on v1 and use the report to guide a later corpus or chunking pass.

## Safety Confirmation

Creating this plan and harness did not touch v1 Chroma or v2 Chroma. The v2 store must not be opened by this harness until embedding has completed and the command includes `--confirm-v2-ready`.
