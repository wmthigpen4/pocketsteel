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
- SHA-256: `d1c0522ff5ac2e07b625670c4901aa3373fe443b0a6b55609ab423f313cd0163`

Manual structured-output and tournament smoke passed:

- Selected candidates: `10`
- Expected calls: `5`
- Fallback calls: `0`
- Mock candidate-ID validation: passed

The development-only discussion-expansion retriever is also implemented:

- `/Users/cory/Documents/sgf-scrape-test/rag_canonical_frontier_tournament_retriever_v2.py`
- SHA-256: `96c9922cf32022fa425ee753371f0df1386c9c2908a345ef9e14d414189bb05c`
- Real canonical-index smoke: `10` passages from `10` unique selected discussions
- Cold local retrieval latency with a mock tournament: `4.78 seconds`
- Warm local retrieval latency with a mock tournament: `1.85 seconds`
- Activation authorization metadata: `false`

Separate integrated runtime factory:

- `/Users/cory/Documents/sgf-scrape-test/canonical_frontier_v932_runtime_candidate.py`
- SHA-256: `c4033ede0d0fd52522e8aafa0eb67158a3bb4d6b17ec17f31c8b8474823fad79`
- It composes the tournament retriever, ten-group context, Terra compiler, and conditional verifier without changing the active v931 service factory.
- Real canonical retrieval plus schema-valid mocked model responses passed end to end in `4.69 seconds` from a cold process.
- Focused unit suite: `15 tests passed`.

## Frozen 35-Case Pilot

Policy:

- `/Users/cory/Documents/sgf-scrape-test/rag-evaluation/training/canonical-v932-luna-tournament-pilot-policy-v936.json`
- SHA-256: `b4c54c374d5cc645ad680bbb7dd8f73f8c1cf76eb0cdb255365d159b68007d7d`

Runner:

- `/Users/cory/Documents/sgf-scrape-test/run_canonical_v932_luna_tournament_pilot_v2.py`
- SHA-256: `ac88330aea91dd906b249b436fe1d0484e45925036d2c857dd39e1819c853b73`

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

Evaluation mode fails closed on provider, schema, or credit errors so infrastructure failures cannot be counted as ranking failures. Product/runtime mode retains deterministic hybrid-order fallback.

Final protected-preview safety check after development:

- Feature flag: `false`
- Port `8770`: listening, live, and ready
- Served site revision: `2a56f2e1`
- Port `8771`: no listener

## Current Blocker

The OpenAI API returned `credit_balance_exhausted` during the v931 protected answer evaluation. Raising the monthly API limit did not add funded API credit. The v932 pilot is therefore implemented and preflighted but intentionally not executed until funded credit is available.

No additional owner review is required for the 35 cases. The runner scores the frozen gold evidence automatically after the ranker returns its gold-blind selections.

## Next Decision

- If the 35-case tournament reaches the retrieval and latency gates, integrate discussion expansion plus the existing Terra compiler and evaluate that complete development pipeline.
- If it fails, stop trying raw-post rerankers and build offline atomic knowledge cards from the canonical corpus before repeating broad development evaluation.
- Only a development winner receives a newly constructed source-disjoint protected set.

No public or protected-preview activation is authorized by this checkpoint.
