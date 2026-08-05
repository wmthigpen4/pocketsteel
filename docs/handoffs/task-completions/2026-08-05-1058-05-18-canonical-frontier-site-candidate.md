# Canonical Frontier Site Candidate

## Task summary

The four-day model and retrieval exploration converged on a canonical hybrid retrieval architecture with GPT-5.6 Terra as an atomic answer compiler, a high-precision deterministic citation-entailment fast path, and GPT-5.6 Luna as a conditional independent verifier. This slice starts integrating that architecture into Steel Guitar RAG without changing public or protected-preview behavior.

Completed:

- Added a server-side client for the independently deployed canonical-frontier service.
- Added a default-off feature flag: `STEEL_RAG_CANONICAL_FRONTIER_ENABLED`.
- Routed only source-dependent steel-guitar questions to the candidate when enabled.
- Preserved deterministic fretboard, copedent, practice, melody, and tablature routes ahead of the candidate.
- Required every returned answer claim to cite a returned source and declare either deterministic or independent semantic verification.
- Added bounded HTTPS/loopback URL validation, a server-side bearer token, a bounded response body, and a bounded timeout.
- Added automatic fallback to the existing answer path when the candidate is unavailable, times out, or returns an invalid response.
- Kept the candidate disabled and did not deploy, restart, change DNS, alter Cloudflare Access, or touch secrets.

Intentionally not changed:

- Public/protected-preview runtime configuration.
- Existing Chroma/vector stores, embeddings, corpus files, scraping, source inbox, or private sources.
- UI rendering or answer request schema.
- Deterministic fretboard or tablature engines.
- Deployment, DNS, Tunnel, Cloudflare, authentication, or billing configuration.

## Lane classification

- Primary lanes: `05 Backend / RAG Integration` and `18 Product / Architecture`.
- Task mode: YELLOW, with implementation already authorized by the user's request to select the architecture and begin site integration.
- Deployment remains RED and was not performed.

## Files changed

- `steel_guitar_rag/canonical_frontier_client.py` — new default-off, fail-closed service client and response validator.
- `steel_guitar_rag/api.py` — candidate routing after deterministic/curated paths and before legacy source retrieval.
- `tests/test_canonical_frontier_client.py` — flag, configuration, citation validation, enabled route, disabled route, and outage fallback tests.
- `docs/handoffs/task-completions/2026-08-05-1058-05-18-canonical-frontier-site-candidate.md` — this handoff.

No files were deleted. No generated corpus, vector, embedding, private-source, secret, or deployment artifacts were created in this repository.

## Tests and checks

- `python3 -m unittest discover -s tests` in the exploration/runtime workspace: **915 passed**.
- Focused application test command with the existing Python 3.12 environment: **349 passed**.
  - `tests/test_canonical_frontier_client.py`
  - `tests/test_api_contract.py`
  - `tests/test_api_search.py`
- Full application pytest: **1,592 passed, 1 environmental failure**.
  - The failure is `tests/test_song_catalog_pipeline.py::test_catalog_pipeline_cli_reports_and_checks_registry` because this worktree does not contain the test's hard-coded `.venv/bin/python` path.
  - Running the exact catalog command with the existing repository Python environment passed and reported `valid: true` with no errors.
- Python compile checks passed for the new runtime, client, API, and tests.
- `git diff --check`: passed.
- Real loopback HTTP smoke from the site client through the new service boundary with fake model calls: complete answer, one verified claim, one source, zero paid calls.
- Real canonical retriever smoke against the 1,948,039-passage index: six sources returned; warm retrieval measured 3.9–4.7 seconds.
- One capped live production-shaped runtime smoke: complete four-claim answer, one cited canonical source, Terra + conditional Luna, no retry, $0.0123489 actual spend, 12.452-second total latency. This single exhaustive request is above the under-10-second median goal and remains a tail-latency monitoring case.

## Integration notes

Enablement requires all three server-side settings:

- `STEEL_RAG_CANONICAL_FRONTIER_ENABLED=true`
- `STEEL_RAG_CANONICAL_FRONTIER_URL=<HTTPS or explicit loopback URL>`
- `STEEL_RAG_CANONICAL_FRONTIER_TOKEN=<server-side secret>`

The flag defaults off. The token is never returned to the browser. The site accepts only schema version 1 responses whose answer claims are present in the answer text, cite returned source IDs, and use an approved verification mode. Clarification and abstention responses may not expose claims or sources.

The independent service candidate lives in the exploration workspace and exposes `/v1/answer`, `/health/live`, and `/health/ready`. Its ready payload explicitly states that runtime activation is not authorized. The service retries one malformed Terra response, drops every claim rejected by Luna, and never emits model-generated tablature.

## Risk assessment

Risk: **medium**.

- Public behavior risk is currently low because the flag defaults off and no runtime configuration changed.
- Candidate enablement risk is medium because it adds a paid external model dependency and a persistent local retrieval service.
- The fresh 20-case evidence passed answerable coverage and projected median-latency thresholds, but two strict `none` labels became safe, explicitly limited partial answers rather than abstentions.
- One live exhaustive four-claim request took 12.452 seconds, so tail latency requires ongoing observation even though the fresh projected median was 8.342 seconds.
- Rollback is immediate: leave or set `STEEL_RAG_CANONICAL_FRONTIER_ENABLED=false`.

## Human decision needed

**Yes, later — not to preserve this default-off implementation.** Before enabling the candidate in protected preview, the owner should complete a small expert product checkpoint focused on answer correctness, teaching usefulness, citation fit, and whether verified partial answers are preferable to abstention for incompletely supported questions. Activation, deployment, secrets, and preview restart require their own explicit lane authorization.

## Safe-to-stage exact file list

- `steel_guitar_rag/canonical_frontier_client.py`
- `steel_guitar_rag/api.py`
- `tests/test_canonical_frontier_client.py`
- `docs/handoffs/task-completions/2026-08-05-1058-05-18-canonical-frontier-site-candidate.md`

## Files that must not be staged

- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md` — unrelated pre-existing untracked operations note.
- Any corpus, Chroma/vector, embedding, private-source, source-inbox, `.wrangler`, credential, log, environment, or generated artifact.

## Recommended next lane

`15 QA / Answer Eval`: review the frozen architecture decision and this candidate, then run a small owner-facing product checkpoint against default-off local candidate responses. After that passes, `01 Repo Steward` can confirm the exact commit and `12 Self-Hosted Deployment` can separately plan a protected-preview-only enablement.

## Commit readiness

**Safe to commit.** The exact four-file slice is isolated, focused tests are green, the full suite's only failure is the missing worktree-local interpreter path, and no unrelated dirty file is included.

## Suggested next step

Run Lane 15 against this handoff and the canonical-frontier architecture decision, using 8–10 representative questions rather than another broad model bakeoff. Do not enable or deploy during that review.
