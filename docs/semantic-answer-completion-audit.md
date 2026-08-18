# Semantic answer architecture completion audit

Audit date: 2026-08-18

This audit measures the implementation against the requested end state rather than against the existence of commits. The live-model authority gate passes, and exact protected release `2780c6bc4f93cb7abaf237440b5801b0f197e3a0` is active with both required authorities enabled. Public activation remains a separate decision.

## Requirement evidence

| Requirement | Authoritative evidence | Status |
| --- | --- | --- |
| Semantic meaning owns enabled-path answer routing | `OpenAIResponsesSemanticAnswerer`, strict six-route schema, API-boundary revalidation, and semantic routing integration tests | Locally proven |
| Source-free conceptual steel teaching is composed directly | Real Responses-adapter-to-`/api/answer` integration test plus eight live held-out teaching cases | Proven locally and with the live model |
| Exact strings/frets/notes/pedals/levers remain deterministic | Semantic exact plans must contain no answer and a bounded `tool_query`; deterministic and tool-miss tests prohibit forum fallback | Locally proven |
| Retrieval occurs only when evidence is required | Valid semantic plans disable legacy corpus promotion/contextual probes; teaching, exact, clarify, guardrail, and policy tests assert zero search calls | Locally proven |
| Sourced claims use only the verified canonical frontier | Source/hybrid plans cannot contain prose, cannot enter legacy synthesis, and fail honestly when the frontier is unavailable | Proven locally and in protected preview |
| Hybrid output combines only verified deterministic and verified sourced portions | Frontier-success and frontier-failure regressions cover full and deterministic-only partial shapes | Locally proven |
| Local policy cannot be weakened by the model or conversation context | Unsafe/unbounded, sensitive-personal-attribute, and specific-private-biography checks run before semantic authority and before corpus probing; regressions assert zero model/search calls | Locally proven |
| Existing `/api/answer` and frontend contract remain stable | No frontend files changed; full repository suite and WSGI response-shape tests pass | Locally proven |
| Rollback remains available | Feature defaults off; planner outage falls back for valid in-domain requests and fails closed for legacy off-domain requests | Locally proven |
| OpenAI calls are deliberate, bounded, and measurable | Server-only key, `store:false`, low reasoning, bounded context/output/timeout, structured schema, token/latency telemetry, full-bank metrics | Proven; full rerun measured 29,145 tokens, 1.748-second median, and 7.799-second p95 wall latency |
| All six authorities pass representative real-model evaluation | Full rerun passed 31/32 under one stale notation assertion; the correctly routed row passed after the evaluator assertion was corrected and rerun alone | **Passed: live evidence for all 32 cases** |
| Enabled search behavior passes acceptance | Isolated loopback evidence covers all ten matrix cases. Exactly ten protected requests were issued: eight passed, the first exposed an exact-parser miss that was repaired and passed on the next request, and the final browser-context pronoun case returned a safe clarifier because its preceding browser context differed from the runner fixture | Protected release active; one exact-fixture contextual rerun requires a separately authorized request |
| Public activation | Separate deployment decision by design | **Not authorized** |

## Deliberate local exceptions

Authenticated profile-control requests remain local deterministic operations and do not require semantic interpretation. Non-negotiable local policy guardrails also remain zero-call. These are explicit authority boundaries, not keyword-based substitutes for ordinary answer routing.

## Current proof set

- Semantic authority bank: 32 held-out prompts across all six routes.
- Protected acceptance bank: 10 requests across all six routes, contextual source/off-domain follow-ups, and two personal-policy boundaries.
- Authorized live model bank: passing evidence for all 32 held-out cases across all six authorities. The full rerun was 31/32 only because the evaluator demanded `A+F` while the source prompt used `A-plus-F`; the corrected row passed a one-case live rerun.
- Full live rerun metrics: 29,145 tokens, 92.972 seconds total wall latency, 1.748-second median, and 7.799-second p95.
- Enabled-path loopback acceptance: 8/10 initially; both failures were deterministic-adapter misses. After one structural adapter repair, the bounded exact and hybrid rerun passed 2/2. Combined evidence covers all ten cases and all six authorities.
- Full repository regression after contract hardening: 1,788 passed in 86.47 seconds.
- Full repository regression after deterministic-adapter repair: 1,792 passed in 87.22 seconds.
- Canonical frontier loopback readiness: live/ready on `127.0.0.1:8771` during the runtime audit.
- Protected preview release: `2780c6bc4f93cb7abaf237440b5801b0f197e3a0`, with `features.semanticAnswer=true` and `features.canonicalFrontier=true`.
- Protected request accounting: exactly ten `/api/answer` submissions, with no request beyond the authorized cap. The direct standard-E9 position miss was repaired in release commit `abe5508`; the remaining contextual-pronoun result was a safe clarifier under browser-provided context rather than the bank's explicit Buddy Emmons context.

## Remaining rollout decision

Public rollout is still separate and unapproved. Before that decision, run the one contextual-source fixture with its exact explicit conversation context under a separately authorized protected-request budget; the current ten-request authorization is exhausted.

OpenAI's official guidance recommends representative evaluation and comparing task success, completeness, tokens, latency, and cost rather than assuming a configuration is better. The implemented banks and telemetry are designed around that gate: [model guidance](https://developers.openai.com/api/docs/guides/latest-model), [evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices).
