# Semantic Answer Orchestrator

The semantic answer path is a default-off replacement authority layer for `/api/answer`. It reduces dependence on prompt-specific regex routing without changing the public API or frontend response contract.

## Authority model

When the feature is enabled, one structured OpenAI Responses API call selects one of six routes for every answer request except local deterministic profile-control requests and requests rejected by non-negotiable local unsafe, unbounded-output, sensitive-personal-attribute, or specific-private-biography guardrails:

| Route | Owner of the displayed answer | Retrieval |
| --- | --- | --- |
| `deterministic` | Existing music/fretboard/copedent tools | Forbidden |
| `semantic_teacher` | GPT-5.6 Terra, constrained to source-free conceptual teaching | Forbidden |
| `source_backed_rag` | Existing verified canonical frontier | Required |
| `hybrid` | Deterministic result plus verified frontier context | Required only for the sourced part |
| `clarify` | One structured missing-context question | Forbidden |
| `guardrail` | Existing local scope/safety copy | Forbidden |

The planner supplies a canonical `tool_query` for deterministic work. The adapter preserves the original exact request with that query so notation and requested operations cannot be lost during semantic restatement. It never supplies the exact music result itself. Existing deterministic music tools remain the only authority for exact strings, frets, notes, pedals, levers, chord positions, tablature, and copedent facts.

The application revalidates every result at the API boundary, including results from injected or alternate planner implementations. The selected route is the authority decision; redundant `needs_*` flags are canonicalized from that route so a contradictory model flag cannot accidentally grant retrieval or fretboard authority. A source-backed plan containing answer prose is rejected, as is teaching prose that contains exact numbered fret/string instructions, exact string-to-pitch changes, citations, or unsupported claims about player/forum consensus. Exact and hybrid plans without a bounded deterministic tool query are rejected. These checks are an output safety boundary; they do not classify the user's request. Local policy guardrails run before the planner and cannot be weakened by it or by conversation context. They are isolated from ordinary semantic routing and cannot start corpus probing or retrieval.

Once a semantic result is valid, legacy corpus promotion and contextual corpus probes are disabled for that request. Source-backed and hybrid routes can enter only the verified canonical frontier. If that frontier is unavailable, source-backed requests return an honest `503`; hybrid requests return only the verified deterministic portion with an explicit warning. Neither route falls through to legacy fragment synthesis.

This uses Structured Outputs through `text.format` with `strict: true`, matching the current [official OpenAI Structured Outputs guidance](https://developers.openai.com/api/docs/guides/structured-outputs). The default model is `gpt-5.6-terra`, whose official model page lists support for Responses and Structured Outputs: [GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra).

## Configuration

The path remains disabled unless all rollout gates pass.

```text
STEEL_RAG_SEMANTIC_ANSWER_ENABLED=false
STEEL_RAG_SEMANTIC_ANSWER_MODEL=gpt-5.6-terra
STEEL_RAG_SEMANTIC_ANSWER_TIMEOUT_SECONDS=20
OPENAI_API_KEY=<server-side secret>
```

`OPENAI_API_KEY` must remain in the protected server environment. It must never be sent to the browser, committed, logged, or copied into a handoff.

Source-backed and hybrid routes require the existing canonical frontier:

```text
STEEL_RAG_CANONICAL_FRONTIER_ENABLED=true
```

If the semantic planner fails, valid in-domain requests fall back to the current router. Legacy off-domain decisions fail closed with no retrieval. The complete rollback is `STEEL_RAG_SEMANTIC_ANSWER_ENABLED=false`.

## API-call budget

| Request type | Semantic planner calls | Other model calls |
| --- | ---: | ---: |
| Local profile-control or policy-guardrail request | 0 | 0 |
| Exact deterministic request | 1 | 0 after the deterministic resolver succeeds |
| Conceptual teaching | 1 | 0 |
| Clarification or guardrail requiring semantic interpretation | 1 | 0 |
| Source-backed | 1 | Existing canonical synthesis/verification calls |
| Hybrid | 1 | Existing canonical synthesis/verification calls |

The current slice does not add embeddings, rebuild indexes, change corpus data, change `/api/answer`, or change frontend rendering. It does intentionally add one planner call to recognized deterministic questions while the feature flag is enabled, so the semantic planner—not the legacy regex classifier—owns routing authority consistently.

Successful planner calls record the resolved model, provider latency, input tokens, cached input tokens, output tokens, reasoning-output tokens, and total tokens in the server route log. The log includes the existing trace ID but not the user's question or the model answer. Provider metrics are application metadata and never enter the model's Structured Outputs schema or the public `/api/answer` response.

The authenticated `/api/session` response exposes `features.semanticAnswer` and `features.canonicalFrontier` only when each path is active. This gives protected smoke a read-only way to prove that both required authorities are enabled without weakening the minimal public `/api/version` and health responses.

## Evaluation and rollout

The held-out bank is `evals/semantic_answer_authority_v1.jsonl`. Run it only in an approved environment with a server-side OpenAI key:

```bash
.venv/bin/python scripts/run_semantic_answer_eval.py
```

Use `--case-id ID` to rerun one named case without paying for the entire bank again. Repeat the option to select more than one case.

The report includes per-route correctness, every individual failure, request completion count, model identity, token totals, and total/median/p95 wall latency. Expected provider or contract failures are recorded and the remaining cases continue, so one failure cannot hide the rest of the bank. Cost is intentionally not hard-coded: calculate it from the captured usage and the approved environment's current model pricing.

The authorized 2026-08-18 live run passed every authority after correcting one evaluator-only notation mismatch. The full rerun produced 31/32 under the stale `A+F` assertion; that row selected the correct `hybrid` route. The corrected `A-plus-F` row then passed a bounded one-case live rerun, giving passing live evidence for all 32 cases. The full rerun used 29,145 tokens and had 1.748-second median and 7.799-second p95 wall latency.

Promotion gates:

1. Route accuracy passes the held-out authority bank, including all guardrail and clarification cases; the evaluator reports results per route.
2. Every deterministic `tool_query` preserves the user's chord, key, tuning, and requested operation.
3. Source-free teaching answers pass teacher-first review and contain no exact/source authority violations; these violations fail the automated evaluation even when the selected route is correct.
4. Source-backed and hybrid prompts pass the canonical frontier citation and entailment gates.
5. Latency, API cost, outage fallback, and conversation-follow-up behavior pass protected-preview evaluation.
6. The flag is enabled only in protected preview first. Public activation remains a separate explicit deployment decision.

After both flags are activated in a separately authorized protected release, run the ten-request acceptance matrix. The runner reads the Access JWT from an environment variable, refuses non-HTTPS origins except loopback HTTP, requires an exact request-count authorization, and stops before answer calls if `/api/session` does not prove both features active:

```bash
STEEL_RAG_PREVIEW_ACCESS_JWT=<protected-session-jwt> \
  .venv/bin/python scripts/run_semantic_answer_preview_smoke.py \
  --base-url https://app.steelguitarrag.com \
  --authorize-answer-requests 10 \
  --output output/semantic-answer-preview-smoke.json
```

The matrix covers deterministic, source-free teaching, source-backed, hybrid, clarification, and guardrail authorities plus contextual source/off-domain follow-ups and the two local personal-policy boundaries. The output path is optional and should remain an uncommitted QA artifact.

The preview runner also accepts repeatable `--case-id ID` selectors. Exact request authorization is checked against the selected subset, allowing a failed case to be retested without spending on the entire matrix. The full bank is still validated before selection, so a subset run cannot conceal a malformed or incomplete acceptance bank.
