# World-class knowledge goal v938 checkpoint

## Decision

The goal is incomplete. Three of eight release gates are proven, one component gate passes but still needs integrated validation, one gate has failed on protected evidence, and three are not yet proven. Gate count is not an estimate of engineering-percent complete.

## Proven now

- Canonical corpus/index: 2,155,158 posts, 1,948,039 display-eligible passages, matching lexical/vector counts, stable `steel-passage-v1` IDs, and `public_forum` provenance retained.
- Frozen benchmark: 303 single-turn cases, including 253 expert evidence cases and 50 controls, plus 10 conversations/40 turns; no source or evidence-group overlap between development and holdout.
- Deterministic music safety: 20/20 fretboard cases, 20/20 valid tablature cases, 17/17 adversarial cases rejected, and zero displayed invalid tablature.

## Not proven or failed

- Protected v931 Recall@10: 111/151 = 73.51%; the 90% gate failed by 16.49 percentage points.
- Claim entailment >=95%: not proven at release scale.
- Expert 4/5 rate >=80%: not proven.
- Conversation retention: isolated contract passes 40/40 turns, but the integrated v932 stack has not run it.
- Median integrated latency <10 seconds: not proven; the projection was 8.34 seconds while one live smoke was 12.45 seconds.

## v932 next experiment

The candidate architecture is canonical top-200 discussion retrieval, four parallel Luna ranking brackets, a Luna final selecting exactly ten discussions, group expansion, local best-passage selection, Terra evidence compilation, and a conditional Luna verifier. Deterministic fretboard and tablature remain separate.

The immutable 35-case development pilot is frozen as `canonical-v932-luna-tournament-pilot-policy-v941`. It permits at most 175 calls, has a calculated conservative ceiling of $1.7279, and fails closed. The prior v939 request was rejected before inference because `uniqueItems` is unsupported in the strict response schema. v941 retains exact item counts in the schema and rejects duplicates in application code.

The corrected v942 execution reached the API and was rejected with `credit_balance_exhausted`. No model response was returned, no state row was written, and recorded new spend is $0. A $20 monthly usage limit is not funded API credit.

## Deployment safety

- Protected service on port 8770: live and ready.
- `STEEL_RAG_CANONICAL_FRONTIER_ENABLED=false` in the protected environment and running process.
- No listener on port 8771.
- The system LaunchDaemon for port 8771 remains spawn-scheduled with exit code 1 because macOS denies it access to the project under `Documents`; it has never become a listener.
- No public activation is authorized.

## Authoritative artifacts

- Goal audit: `/Users/cory/Documents/sgf-scrape-test/rag-evaluation/audit/world-class-goal-current-v938.json` (`7b321e70af8face263222e47995a9db8cb0d02f1d9a23d300115b4954a25eed5`)
- Audit builder: `/Users/cory/Documents/sgf-scrape-test/audit_world_class_goal_v932.py` (`626297456cbea377dab98ea84a23a267bf2fbcb18133cb291a91c930799f6b5c`)
- Frozen pilot policy: `/Users/cory/Documents/sgf-scrape-test/rag-evaluation/training/canonical-v932-luna-tournament-pilot-policy-v941.json` (`8cf5217d7ef1bdcca0b429d461f0981ad63db4f9c51b7a05782fde923694a89a`)
- Tournament implementation: `/Users/cory/Documents/sgf-scrape-test/rag_frontier_group_tournament_v2.py` (`775f3eb9b3283c2b1acf837d2721e2729236814e6c4f9509777ad550888d040a`)
- Pilot runner: `/Users/cory/Documents/sgf-scrape-test/run_canonical_v932_luna_tournament_pilot_v2.py` (`eb30751cea1c30e4506451e696c0bb98e23793f774922d3a4b63dbbc0fc568b3`)

## Verification

- Fifteen v932/runtime unit tests pass.
- Real-index preflight passes for all 35 frozen cases.
- Conservative pilot cost ceiling: $1.727899775.
- Protected holdout cases used by v932: 0.

## Next action

When funded API credit exists, resume the exact v942 pilot. If it passes 90% development Recall@10 plus latency and fallback gates, run integrated development quality checks. If it fails, stop model-ranking exploration and build attributed atomic knowledge cards before any fresh protected evaluation.
