# Canonical Frontier v931 Protected Preview No-Go

- Branch: `fix/local-play-along-route-options`
- Site revision: `2a56f2e113db4be31bc8d19a69e424217ea32c33`
- Date: 2026-08-05
- Decision: `NO-GO / feature disabled`
- Public activation: `Not authorized and not performed`

## Plain-English Result

Candidate v931 was installed in the protected preview, smoke-tested, and evaluated on the untouched 151-case protected retrieval set. It passed the latency requirement but failed the retrieval-quality requirement by a wide margin:

- Protected Recall@10: `111 / 151 = 73.51%`
- Required Recall@10: `at least 90%`
- Median retrieval latency: `3.159 seconds`
- P95 retrieval latency: `3.725 seconds`
- Retrieval-evaluation API spend: `$0.00`

The result is definitive for v931. More answer-generation judging cannot repair missing evidence, so no further paid evaluation should be performed on this candidate.

## Deployment And Rollback

- Exact detached release: `/Users/cory/.steel-rag/releases/2a56f2e1-canonical-frontier-v931`
- Protected site port: `8770`
- Candidate service port: `8771`
- Candidate feature flag: `STEEL_RAG_CANONICAL_FRONTIER_ENABLED`
- The site restarted on exact revision `2a56f2e1` and passed live, ready, and version checks.
- The candidate service passed an authenticated loopback smoke and returned a neutral, attributed four-step answer.
- The candidate feature is now `false` in the protected environment and in the running site process.
- Port `8771` has no listener.
- The protected site remains live and ready on port `8770`.

No public activation occurred.

## Verification

Focused site and service tests passed before deployment:

- `421 passed`
- Unauthorized service request returned `401`.
- Authorized service request returned `200`.
- The smoke answer contained four supported claims and one source.
- Cold smoke latency was `13.98 seconds`; the complete protected retrieval run subsequently measured the steady retrieval latency shown above.

## Protected Evidence

Frozen candidate:

- `/Users/cory/Documents/sgf-scrape-test/rag-evaluation/audit/canonical-frontier-implementation-ready-v931.json`
- SHA-256: `de364c4ccd6c0b459b440d24524bf659646511ce60c17692e42145a99114291a`

Completed protected retrieval evaluation:

- `/Users/cory/Documents/sgf-scrape-test/rag-evaluation/release/canonical-frontier-protected-v931-retrieval.json`
- SHA-256: `26ab6a3715958a31799e59cdb7f12bfb2c50882131d8d2f529070eaed2de87f0`
- Status: `protected_retrieval_gate_failed`
- Evaluation split: `holdout`
- Cases consumed: `151 / 151`

Protected answer-evaluation policy and state:

- Policy: `/Users/cory/Documents/sgf-scrape-test/rag-evaluation/release/canonical-frontier-protected-v931-policy.json`
- Policy SHA-256: `62896b94063a808cb9fd3ec320d699738aab5f0e4eba564392564ce138ab911e`
- State: `/Users/cory/Documents/sgf-scrape-test/rag-evaluation/release/canonical-frontier-protected-v931-state.json`
- State SHA-256: `f4e0adc48349faff9a9c1e48f9818645333d33145b8bbe4ddf17f1b8dbcd7efd`

The paid answer evaluation is not valid release evidence. It encountered a scorer database mismatch, a source-ID representation mismatch, resource contention, and then `credit_balance_exhausted`. It used 38 protected cases, made 24 successful model requests, and recorded `$0.144994` of API spend before stopping. It must not be described as a clean or complete answer-quality evaluation.

The internally tracked cumulative spend floor is `$10.0311372`; including the conservative `$0.15` allowance retained for the unmetered protected smoke produces a conservative accounting floor of `$10.1811372`. This is accounting conservatism, not a statement that the smoke was billed at `$0.15`.

## Infrastructure Exception

The installed `com.steelguitarrag.canonical-frontier` system LaunchDaemon cannot read the corpus under `Documents` because of macOS privacy controls. It is not serving traffic, but launchd still has the failed definition loaded and periodically retries it. A future administrator-approved cleanup should boot out that definition, then either remove it or relocate the service's corpus/index into a system-service-readable directory before reinstalling it.

This exception does not affect the existing protected site on port `8770`.

## Architecture Decision

The overall architecture remains sound:

- one canonical lexical/vector corpus and source-ID scheme;
- deterministic fretboard and tablature engines;
- an attributed answer compiler;
- claim verification and explicit partial/clarify/abstain modes;
- a default-off site client with fallback.

The v931 retriever policy is rejected. Its development result did not generalize to unseen source-disjoint questions. The next candidate, v932, must be developed without inspecting or tuning against protected per-case misses.

## v932 Development Direction

1. Treat the 151-case v931 protected set as consumed and preserve it only as historical release evidence.
2. Use development evidence only to replace the small, fast candidate-pool policy with a higher-recall retrieval cascade.
3. Measure both direct answer-bearing recall and source-group recall before answer generation.
4. Keep retrieval under the ten-second end-to-end budget through persistent model loading, caching, and bounded reranking—not by prematurely shrinking the candidate pool.
5. Require a robust development lower bound above 90%, including partitions and perturbations, before creating a fresh source-disjoint protected set.
6. Run paid answer-quality evaluation only after the new candidate passes protected retrieval.

## Files Intentionally Untouched

The unrelated untracked handoff below belongs to another task and was not modified or staged:

- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
