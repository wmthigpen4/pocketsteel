# v932 local tree reranker rejected

## Result

A no-cost, answer-blind tree reranker was evaluated on all 553 broad development questions using source-grouped out-of-fold validation. It scored 435/553, or 78.66% Recall@10, and is rejected.

This is worse than the 84.81% single-passage cross-encoder and 83.18% dual-passage cross-encoder. The canonical top-200 candidate ceiling remains 94.21%, so the unresolved problem is selecting the right ten discussions rather than finding them in the broad pool.

## Controls

- Canonical depth-200 discussion candidates only.
- Runtime-available rank, RRF, title-overlap, and dual-passage-overlap features only.
- No reference answers or benchmark category features.
- Gold-discussion-group fold assignment prevents the same answer source from training and validating a fold.
- All 553 development questions scored.
- Protected cases used: 0.
- API calls and spend: 0.

## Decision

Do not extend the local feature-model branch. The next discriminating experiment remains the frozen 35-case Luna tournament, capped at $1.75, which currently cannot run because the API returns `credit_balance_exhausted`.

If model-assisted ranking fails after funded credit is available, the fallback is a new attributed knowledge-card layer on the canonical corpus. The existing 2.1-million-card experiment is not sufficient release evidence: it is tied to an older 311,767-source corpus and its prior Gemma/card-ranking approaches were rejected.

## Evidence

- Implementation: `/Users/cory/Documents/sgf-scrape-test/train_canonical_v932_tree_group_reranker_v2.py` (`0f4c68d6885c97fd2fc6e834fbd06165de9434c7ccd0389d6113c04a3edbf8e0`)
- Development report: `/Users/cory/Documents/sgf-scrape-test/rag-evaluation/benchmark/canonical-v932-tree-group-reranker-oof-v943.json` (`1cbc7f76eceab292542556e7a97d093aa7ede7746c4e937fa841fc2ec1fd14f1`)
- Updated eight-gate audit: `/Users/cory/Documents/sgf-scrape-test/rag-evaluation/audit/world-class-goal-current-v938.json` (`fe5f8d3ad78564f2123dc015081fbfbe3cee5dc2b34e5e8170dec5afee319328`)
