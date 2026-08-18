# Semantic answer architecture completion audit

Audit date: 2026-08-18

This audit measures the implementation against the requested end state rather than against the existence of commits. The requested search experience is **not yet complete** because live-model and protected enabled-path evidence is still missing.

## Requirement evidence

| Requirement | Authoritative evidence | Status |
| --- | --- | --- |
| Semantic meaning owns enabled-path answer routing | `OpenAIResponsesSemanticAnswerer`, strict six-route schema, API-boundary revalidation, and semantic routing integration tests | Locally proven |
| Source-free conceptual steel teaching is composed directly | Real Responses-adapter-to-`/api/answer` integration test proves one structured request, no retrieval, no sources, and no fretboard | Locally proven with simulated provider response; real-model quality pending |
| Exact strings/frets/notes/pedals/levers remain deterministic | Semantic exact plans must contain no answer and a bounded `tool_query`; deterministic and tool-miss tests prohibit forum fallback | Locally proven |
| Retrieval occurs only when evidence is required | Valid semantic plans disable legacy corpus promotion/contextual probes; teaching, exact, clarify, guardrail, and policy tests assert zero search calls | Locally proven |
| Sourced claims use only the verified canonical frontier | Source/hybrid plans cannot contain prose, cannot enter legacy synthesis, and fail honestly when the frontier is unavailable | Locally proven; protected integration pending |
| Hybrid output combines only verified deterministic and verified sourced portions | Frontier-success and frontier-failure regressions cover full and deterministic-only partial shapes | Locally proven |
| Local policy cannot be weakened by the model or conversation context | Unsafe/unbounded, sensitive-personal-attribute, and specific-private-biography checks run before semantic authority and before corpus probing; regressions assert zero model/search calls | Locally proven |
| Existing `/api/answer` and frontend contract remain stable | No frontend files changed; full repository suite and WSGI response-shape tests pass | Locally proven |
| Rollback remains available | Feature defaults off; planner outage falls back for valid in-domain requests and fails closed for legacy off-domain requests | Locally proven |
| OpenAI calls are deliberate, bounded, and measurable | Server-only key, `store:false`, low reasoning, bounded context/output/timeout, structured schema, token/latency telemetry, full-bank metrics | Locally proven; real values pending |
| All six authorities pass representative real-model evaluation | 32-case bank and resilient evaluator exist | **Missing: approved key-bearing run** |
| Enabled search behavior passes protected acceptance | Ten-case, exact-authorization, fail-before-answer smoke runner exists | **Missing: exact release, both flags active, authorized run** |
| Public activation | Separate deployment decision by design | **Not authorized** |

## Deliberate local exceptions

Authenticated profile-control requests remain local deterministic operations and do not require semantic interpretation. Non-negotiable local policy guardrails also remain zero-call. These are explicit authority boundaries, not keyword-based substitutes for ordinary answer routing.

## Current proof set

- Semantic authority bank: 32 held-out prompts across all six routes.
- Protected acceptance bank: 10 requests across all six routes, contextual source/off-domain follow-ups, and two personal-policy boundaries.
- Full repository regression after local-policy hardening: 1,785 passed in 87.41 seconds.
- Canonical frontier loopback readiness: live/ready on `127.0.0.1:8771` during the runtime audit.
- Deployed site adapter: older commit during the runtime audit; no claim that protected preview contains this architecture.

## Remaining completion sequence

1. Explicitly authorize use of an approved server-side key for the 32 planner requests.
2. Run `scripts/run_semantic_answer_eval.py`; require every route and authority check to pass, then review token/latency/cost measurements and teaching prose.
3. Build and inspect an exact protected release containing the semantic commits.
4. Explicitly authorize protected flag activation/restart with semantic and canonical frontier enabled together.
5. Run `scripts/run_semantic_answer_preview_smoke.py` with exact authorization for 10 answer requests.
6. Review every trace and response; require all activation and case checks to pass before considering public rollout.

OpenAI's official guidance recommends representative evaluation and comparing task success, completeness, tokens, latency, and cost rather than assuming a configuration is better. The implemented banks and telemetry are designed around that gate: [model guidance](https://developers.openai.com/api/docs/guides/latest-model), [evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices).
