# Semantic Answer Orchestrator

The semantic answer path is a default-off replacement authority layer for `/api/answer`. It reduces dependence on prompt-specific regex routing without changing the public API or frontend response contract.

## Authority model

One structured OpenAI Responses API call may select one of six routes:

| Route | Owner of the displayed answer | Retrieval |
| --- | --- | --- |
| `deterministic` | Existing music/fretboard/copedent tools | Forbidden |
| `semantic_teacher` | GPT-5.6 Terra, constrained to source-free conceptual teaching | Forbidden |
| `source_backed_rag` | Existing verified canonical frontier | Required |
| `hybrid` | Deterministic result plus verified frontier context | Required only for the sourced part |
| `clarify` | One structured missing-context question | Forbidden |
| `guardrail` | Existing local scope/safety copy | Forbidden |

Known deterministic fretboard questions bypass the planner and continue to use zero OpenAI calls. The planner supplies a canonical `tool_query` only when semantic interpretation is needed to reach an existing deterministic resolver. It never supplies the exact music result itself.

The application validates every returned field and the cross-field authority invariants. A source-backed plan containing answer prose is rejected. A teaching plan requesting sources, a fretboard, or a copedent is rejected. Exact and hybrid plans without a bounded deterministic tool query are rejected. Local unsafe classification runs before the planner and cannot be weakened by it.

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

Source-backed and hybrid routes should also run with the existing canonical frontier enabled:

```text
STEEL_RAG_CANONICAL_FRONTIER_ENABLED=true
```

If the semantic planner fails, valid in-domain requests fall back to the current router. Legacy off-domain decisions fail closed with no retrieval. The complete rollback is `STEEL_RAG_SEMANTIC_ANSWER_ENABLED=false`.

## API-call budget

| Request type | Semantic planner calls | Other model calls |
| --- | ---: | ---: |
| Known deterministic fretboard request | 0 | 0 |
| Previously unrecognized exact request | 1 | 0 after the deterministic resolver succeeds |
| Conceptual teaching | 1 | 0 |
| Clarification or guardrail requiring semantic interpretation | 1 | 0 |
| Source-backed | 1 | Existing canonical synthesis/verification calls |
| Hybrid | 1 | Existing canonical synthesis/verification calls |

The current slice does not add embeddings, rebuild indexes, change corpus data, change `/api/answer`, or change frontend rendering.

## Evaluation and rollout

The held-out bank is `evals/semantic_answer_authority_v1.jsonl`. Run it only in an approved environment with a server-side OpenAI key:

```bash
.venv/bin/python scripts/run_semantic_answer_eval.py
```

Promotion gates:

1. Route accuracy passes the held-out authority bank, including all guardrail and clarification cases.
2. Every deterministic `tool_query` preserves the user's chord, key, tuning, and requested operation.
3. Source-free teaching answers pass teacher-first review and contain no invented exact positions.
4. Source-backed and hybrid prompts pass the canonical frontier citation and entailment gates.
5. Latency, API cost, outage fallback, and conversation-follow-up behavior pass protected-preview evaluation.
6. The flag is enabled only in protected preview first. Public activation remains a separate explicit deployment decision.
