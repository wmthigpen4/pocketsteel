# Canonical Frontier Owner-Corrected Implementation Readiness

## Outcome

The model and architecture exploration is closed. The selected canonical-frontier architecture is implemented in the site behind a default-off feature flag and is ready for an isolated protected-preview deployment plan. It has not been deployed or activated.

Selected architecture:

- Canonical hybrid lexical/vector passage retrieval with discussion-group expansion and reranking over 1,948,039 indexed passages.
- GPT-5.6 Terra as a bounded atomic typed-claim answer compiler.
- High-precision deterministic entailment as the zero-latency verification path.
- GPT-5.6 Luna only for claims the deterministic validator cannot prove.
- Complete, qualified-partial, clarify, and abstain response modes with cited source cards and neutral attributed voice.
- Deterministic fretboard and tablature engines remain separate and authoritative; model-generated tablature is prohibited.
- The site service client is default-off, bounded, fail-closed, and falls back to the existing answer path.

## Owner checkpoint and correction

Codex pre-reviewed all 20 fresh development answers and sent only four edge cases to the owner. The owner accepted three and requested one change: preserve Ulric Utsi-Åhlin's pickup-identification guess as an attributed guess instead of replacing all available guidance with an abstention.

The answer contract and semantic guard now preserve useful attributed uncertainty without promoting it to fact. The one-case live confirmation returned:

- Bobby Boggs's recommendation to inspect the pickup bottom.
- Bobby Boggs's hedged “most likely a 12-1” assessment for the Carter instance.
- Ulric Utsi-Åhlin's BC-12 guess with the 12-1 and E66 alternatives.
- An explicit limit that these are hedged, instance-specific leads rather than a definitive identification procedure.

The corrected result was `partial`, not `complete`, and every correction check passed.

## Verification

- Exploration/runtime regression: **922 passed, 0 failed**.
- Fresh development answerable coverage: **94.12%**.
- Codex pre-review: **17 of 18 eligible answers at least 4/5 for both correctness and usefulness (94.44%)**.
- Citation-fit pre-review: **20 of 20 passed**.
- Owner checkpoint: **four of four decisions saved; three accepted, one corrected and live-confirmed**.
- Focused site integration tests: **349 passed**.
- Site client-to-service loopback smoke: passed.
- Protected holdout cases consumed: **0**.
- Tracked cumulative API testing spend: **$9.8861432 of the $20 owner cap**.
- The owner-correction attempt cost $0.0087094 and the successful confirmation cost $0.0102559.

Frozen implementation-readiness evidence:

`/Users/cory/Documents/sgf-scrape-test/rag-evaluation/audit/canonical-frontier-implementation-ready-v931.json`

## Site implementation

The site integration remains in commit `9e6ac02a feat: add default-off canonical frontier candidate`, coordinated by `5814f7b8 docs: record canonical frontier integration status`.

Enablement requires all three server-side settings:

- `STEEL_RAG_CANONICAL_FRONTIER_ENABLED=true`
- `STEEL_RAG_CANONICAL_FRONTIER_URL=<HTTPS service URL>`
- `STEEL_RAG_CANONICAL_FRONTIER_TOKEN=<server-side secret>`

No settings, secrets, deployments, restarts, DNS, authentication, corpus, embeddings, or indexes were changed during this checkpoint.

## What is decided versus still unproven

Decided and implemented:

- Model family and role split.
- Retrieval architecture.
- Claim/citation verification boundary.
- Uncertainty, partial-answer, clarification, and abstention behavior.
- Separation of conversational knowledge from deterministic tablature.
- Default-off site integration and fallback behavior.

Still required before public activation:

- Deploy the Python retrieval/answer service to an isolated protected-preview host.
- Configure the three server-side settings only in that protected preview.
- Smoke-test representative knowledge questions, failure fallback, source links, conversation context, and deterministic tablature routes.
- Measure preview latency and error rate; the existing exhaustive live smoke was a 12.452-second tail case even though the fresh projected median was 8.342 seconds.
- Run the untouched protected release evaluation only after the preview candidate is immutable.
- Obtain explicit public-activation authorization after those checks pass.

## Recommended next lane

Prepare the isolated protected-preview deployment specification and rollback procedure. Deployment and activation remain separate actions requiring explicit authorization.
