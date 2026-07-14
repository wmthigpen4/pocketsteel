# 03 Lane Map

## Lanes And Responsibilities

### 01 Repo Steward

Owns repo-wide coordination, exact-path staging, commit splitting, dirty-worktree triage, integration-status refreshes, and final commit hygiene. Must never use `git add .`.

### 02 Corpus Pipeline

Owns corpus ingestion, normalization, cleaning, chunking, provenance preparation, and embed preflight. Do not run scraping, embeddings, or private corpus changes without explicit approval.

### 05 Backend / RAG Integration

Owns answer routing, deterministic E9 rules, answer contracts, retrieval orchestration, source-card behavior, backend API behavior, and feature-flagged backend integrations.

### 06 UX/UI Design

Owns answer presentation, frontend rendering, fretboard UI, tab cards, prompt chips, responsive layout, and browser smoke for UI behavior.

### 11 Auth / Security

Owns Cloudflare Access, auth modes, paywall/access-control, privacy/security reviews, private-data exposure review, and session diagnostics.

### 12 Self-Hosted Deployment

Owns runtime startup, protected-preview restart/verification, Cloudflare Tunnel/Pages deployment planning, `/api/version` verification, and deployment smoke.

### 15 QA / Answer Eval

Owns answer evals, red-team matrices, smoke scripts, browser smoke reports, scorer hardening, regression buckets, and QA design review.

### 18 Product / Architecture

Owns product decisions, API/component contracts, answer/fretboard/tab architecture docs, routing policy design, source/copyright policy, and cross-lane implementation recommendations.

### 19 Visual Design / Assets

Owns logos, brand assets, visual systems, generated images, motion/design source files, and visual design directions.

### 20 Amazing Tablature Training

Owns private score/tab batch intake, source-copedent decoding, copedent-neutral decision annotations, exception review, deterministic challenger training, held-out evaluation, and exact-model promotion readiness. Private evidence stays ignored and never becomes RAG, Chroma, embeddings, source cards, or public fixtures. Runtime integration belongs to Lane 05, player-facing controls to Lane 06, independent model QA to Lane 15, commits to Lane 01, and preview operations to Lane 12.

## Lanes That Can Usually Run In Parallel

- Lane 05 implementation and Lane 15 QA planning, if QA is docs-only.
- Lane 06 UI implementation and Lane 18 docs architecture, if architecture does not edit UI files.
- Lane 15 smoke and Lane 18 product review, if smoke is read-only.
- Lane 20 private annotation and Lane 15 evaluation-design review, if neither edits the same tests or handoff.
- Lane 01 integration refresh and Lane 15 docs-only QA, if they avoid the same handoff files.

## Lanes That Must Not Touch Same Files At The Same Time

- Lane 05 and Lane 06 must not both edit `ui/steel-guitar-rag-mock.html`, `ui/answer-client.js`, or shared answer payload expectations.
- Lane 05 and Lane 15 must not both edit `tests/test_api_search.py` unless exact-hunk staging is planned.
- Lane 06 and Lane 15 must not both edit `tests/test_frontend_answer_ui.py` unless exact-hunk staging is planned.
- Lane 01 should not commit `integration-status.md` with implementation files unless explicitly asked for a docs coordination commit.
- Lane 12 should not restart protected preview from dirty runtime files unless the task explicitly says to smoke that dirty state.
- Lane 20 must not edit runtime ranking or Melody Studio UI concurrently with Lane 05 or Lane 06; it hands off a sanitized exact model artifact after approval.
