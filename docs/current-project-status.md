# Current Steel Guitar RAG Project Status

> Historical snapshot retained for context. It is no longer the current status source; use `docs/handoffs/task-completions/integration-status.md` for the active integration snapshot.

Last updated: 2026-06-01

This checkpoint records the current working state for Steel Guitar RAG / Steel Guitar RAG private preview. It is documentation only and does not switch runtime behavior, mutate Chroma, run embeddings, deploy, or change DNS.

## Private Preview Status

- `app.steelguitarrag.com` is protected by Cloudflare Access.
- SGF v2 retrieval is active for the protected preview path.
- Private source retrieval is available only behind explicit environment and auth gates.
- Private E9 profile answers are working for authorized users.
- B+C exercise and learning-plan answers are working.
- Markdown table rendering is working for copedent-style answers.
- Curated vendor links are working for buying/current-source guidance.
- No outside testers should be invited until burn-in is complete.

## Source Layers

- Steel rules layer: stable E9, copedent, pedal/lever, and theory facts.
- Curated source registry: current/vendor/official links and maintained public references.
- SGF v2 Chroma: public Steel Guitar Forum retrieval.
- Private source collection: `corpus-private/vector-stores/chroma`, collection `steel_guitar_private_sources_v1`.
- Source-inbox pipeline: inventory -> normalize -> chunk -> preflight -> approved embedding script.

## Current Commands

Protected private-preview startup with private sources enabled:

```bash
source ~/.steel-rag/env/private-preview.env

STEEL_RAG_AUTH_PROVIDER=cloudflare_access \
STEEL_RAG_ANSWER_AUTH_MODE=production \
STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first \
STEEL_RAG_ENABLE_PRIVATE_SOURCES=true \
STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma \
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 \
STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma \
STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 \
STEEL_RAG_RETRIEVAL_DEBUG=false \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2 \
  --answer-auth-mode production \
  --auth-provider cloudflare-access
```

Rollback to SGF-only:

```bash
STEEL_RAG_RETRIEVAL_MODE=sgf_only \
STEEL_RAG_ENABLE_PRIVATE_SOURCES=false \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --v2-chroma-path corpus-v2/vector-stores/chroma \
  --v2-collection steel_guitar_unified_v2
```

Private source search smoke:

```bash
.venv/bin/python scripts/search_private_sources.py --query "What is my E9 copedent?"
.venv/bin/python scripts/search_private_sources.py --query "What does A+F do?"
.venv/bin/python scripts/search_private_sources.py --query "What is the 10th string on E9?"
.venv/bin/python scripts/search_private_sources.py --query "What are my common grips?"
```

Source-inbox pipeline:

```bash
.venv/bin/python scripts/inventory_source_inbox.py
.venv/bin/python scripts/normalize_source_inbox_text.py
.venv/bin/python scripts/chunk_private_sources.py
.venv/bin/python scripts/private_source_embed_preflight.py
.venv/bin/python scripts/embed_private_sources_chroma.py --dry-run
```

Real private embedding requires explicit approval and `--confirm-preflight-pass`. Do not run a real embedding command as part of docs, status, or cleanup commits.

## Known Dirty Lanes

- Provenance/legal/source policy.
- Private lesson mechanical grounding code and generated data.
- Source-inbox inventory generated files.
- Root RAG/build scripts.
- UI, lesson, and tab stubs.

## Warnings

- Do not commit `corpus-private/`.
- Do not commit raw `source-inbox` content.
- Do not commit Chroma/vector stores, embeddings, DBs, logs, private env files, or secrets.
- Do not expose private sources to anonymous/public users.
- Do not run live scraping, embeddings, deploy, DNS changes, or Chroma mutation as part of this checkpoint.
