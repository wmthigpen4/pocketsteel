# Canonical Frontier v932 Development Checkpoint

- Branch: `fix/local-play-along-route-options`
- Site revision: `1f266696`
- Date: 2026-08-05
- Status: `Development continues / no activation`
- Additional API spend in this checkpoint: `$0.00`

## Plain-English Checkpoint

The protected v931 result showed that the final answer writer was not the immediate blocker. The retriever found answer-bearing evidence in only `73.51%` of protected cases at depth ten.

The broad 553-case development evidence now gives a clearer diagnosis:

- Hybrid discovery Recall@10: `74.14%`
- Correct discussion present within 100 candidates: `92.22%`
- Correct discussion present within 200 candidates: `94.21%`
- Source-grouped out-of-fold local ranker, 100 candidates: `84.81%`
- Source-grouped out-of-fold local ranker, 200 dual-passage candidates: `83.18%`

The local rankers improved over raw hybrid ranking but did not reach the `90%` release gate. Both are rejected as release candidates.

The evidence supports a specific v932 architecture: keep the canonical hybrid retrieval pool at 200 discussion groups, use a small model-assisted tournament to select the ten most likely discussions, expand those discussions to their best passages, then use the existing Terra compiler and claim verification path. Deterministic fretboard and tablature behavior remains separate and unchanged.

## Why This Is Not Another Random Walk

Each step has narrowed the bottleneck:

1. v931 proved the deployed fast retriever does not generalize.
2. The 553-case broad benchmark showed the correct source is usually present deeper in the pool.
3. Source-grouped cross-validation showed that a locally trained compact reranker still loses too many correct sources.
4. The next test changes only the missing capability: semantic selection from a high-recall 200-group pool before answer generation.

The protected 151-case set is consumed and was not inspected or reused for v932 tuning.

## Completed No-Cost Development Tests

### Single-passage group ranker

- Cases: `553`
- Training/evaluation: three source-grouped out-of-fold partitions
- Candidate depth: `100`
- Candidate recall ceiling: `92.22%`
- Selected Recall@10: `84.81%`
- Weakest fold/partition scope: `83.71%`
- API calls/spend: `0 / $0.00`
- Result: `Rejected`

Artifact:

- `/Users/cory/Documents/sgf-scrape-test/rag-evaluation/benchmark/canonical-v932-group-reranker-oof-v934.json`
- SHA-256: `860d479b0b986777fcb334842111de99c7eaa06fc23da42d2362ecc941d591c2`

### Dual-passage group ranker

- Cases: `553`
- Training/evaluation: three source-grouped out-of-fold partitions
- Candidate depth: `200`
- Candidate recall ceiling: `94.21%`
- Selected Recall@10: `83.18%`
- Weakest fold/partition scope: `81.98%`
- API calls/spend: `0 / $0.00`
- Result: `Rejected`

Artifact:

- `/Users/cory/Documents/sgf-scrape-test/rag-evaluation/benchmark/canonical-v932-dual-passage-group-reranker-oof-v935.json`
- SHA-256: `d0b36f4debf618133a055690b62a68eece78999024ee38f0d9e4f426e2d44590`

## Implemented v932 Tournament

The default-off development implementation now:

- accepts at most 200 unique canonical discussion groups;
- splits them into four 50-group brackets;
- runs the four Luna bracket rankings in parallel;
- keeps eight groups from each bracket;
- ranks the 32 finalists down to ten groups;
- uses strict Structured Outputs with an enum of only supplied group IDs;
- validates IDs, uniqueness, and limits in application code;
- falls back deterministically to hybrid order if a ranker call fails;
- never asks the ranker to write an answer or supply factual knowledge.

Implementation:

- `/Users/cory/Documents/sgf-scrape-test/rag_frontier_group_tournament_v2.py`
- SHA-256: `16e213c66a701c05387e8c03e2bebcecbd91e302bbc78467eeed7b200c6a09ec`

Manual structured-output and tournament smoke passed:

- Selected candidates: `10`
- Expected calls: `5`
- Fallback calls: `0`
- Mock candidate-ID validation: passed

## Frozen 35-Case Pilot

Policy:

- `/Users/cory/Documents/sgf-scrape-test/rag-evaluation/training/canonical-v932-luna-tournament-pilot-policy-v936.json`
- SHA-256: `2c1b1e46bfc5abf7a3425d93451d4f73cf1ee842331f9e64e24d238e5459bc3f`

Runner:

- `/Users/cory/Documents/sgf-scrape-test/run_canonical_v932_luna_tournament_pilot_v2.py`
- SHA-256: `3654764cf10f2588ded9248ddbed4e6e58345345fbaf18d81b060a78ef17c098`

The pilot is frozen before results:

- `35` development cases
- `5` deterministic hash-selected cases from each of seven categories
- `200` candidates per case
- `175` maximum Luna requests
- retrieval ranking only; no answer generation
- protected cases used: `0`
- pass gate: at least `90%` Recall@10
- median tournament latency under `6 seconds`
- P95 tournament latency under `9 seconds`
- fallback rate at most `2%`

Dry-run preflight passed:

- Conservative pilot ceiling: `$1.727264525`
- Frozen pilot cap: `$1.75`
- Conservative cumulative floor before pilot: `$10.1811372`
- Maximum conservative cumulative floor after pilot: `$11.908401725`
- Owner cumulative cap: `$20.00`
- API calls made by preflight: `0`

## Current Blocker

The OpenAI API returned `credit_balance_exhausted` during the v931 protected answer evaluation. Raising the monthly API limit did not add funded API credit. The v932 pilot is therefore implemented and preflighted but intentionally not executed until funded credit is available.

No additional owner review is required for the 35 cases. The runner scores the frozen gold evidence automatically after the ranker returns its gold-blind selections.

## Next Decision

- If the 35-case tournament reaches the retrieval and latency gates, integrate discussion expansion plus the existing Terra compiler and evaluate that complete development pipeline.
- If it fails, stop trying raw-post rerankers and build offline atomic knowledge cards from the canonical corpus before repeating broad development evaluation.
- Only a development winner receives a newly constructed source-disjoint protected set.

No public or protected-preview activation is authorized by this checkpoint.
