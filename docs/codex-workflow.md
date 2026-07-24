# Codex Workflow

Steel Guitar RAG uses a human-in-the-loop operating model for Codex work. The goal is to let safe changes move quickly while protecting raw data, scraper behavior, corpus integrity, private materials, and licensing metadata.

Codex should classify each request into one of three modes before acting. When the mode is ambiguous, choose the more cautious mode.

## Lane 20 — Amazing Tablature Training

Lane 20 is the permanent Codex operating home for private great-player score/tab learning. It is command-driven, not a frontend model trainer. A natural request such as `Process the tablature examples in ~/Downloads/New Tabs` is sufficient; Codex reads the durable private registry and invokes `scripts/amazing_tablature.py` rather than depending on conversation memory or a memorized prompt.

The resumable workflow is:

`ingest → annotate → validate → review-exceptions → train → evaluate → report → promote`

New batches require an exact source folder and a known source copedent. Source files and all derived private records remain ignored. Training may create challengers, but Codex stops at the comparison report until the user approves an exact model ID. Stable promotion also requires independent Lane 15 QA before Lane 05 runtime integration, Lane 01 exact-path commit, and Lane 12 protected-preview verification. Full commands, state contracts, and privacy boundaries live in `docs/amazing-tablature-training.md`.

For a new feature, the user approves the scope once. That approval covers the normal end-to-end loop: implementation, focused and full tests, local smoke, exact-path commits, protected-preview update, automated protected smoke, and then user smoke. Codex asks again only for scope expansion, a new product decision, or an unapproved RED action.

## GREEN - Codex Can Proceed

Codex can proceed directly with small, reversible work:

- docs edits
- small UI copy changes
- tests
- evaluation scripts
- read-only analysis
- non-destructive refactors under one module

Expected behavior:

- Make the change.
- Run relevant lightweight checks.
- Summarize the result using the required closeout format.

Examples:

- Add or clarify documentation.
- Add an Electronics-only eval question file.
- Run read-only analysis of current retrieval outputs.
- Clean up wording in Streamlit labels without changing the UI flow.

## YELLOW - Codex Needs Feature-Scope Approval

Codex can inspect, plan, and prepare a proposed diff, but must stop before applying unless the user approves the feature scope. After that single approval, Codex runs the full Autopilot loop without asking at every lane transition:

- RAG prompt changes
- chunking changes
- retrieval ranking changes
- schema changes
- dependency changes
- UI flow changes
- new scripts touching corpus outputs

Expected behavior:

- Explain the proposed change and why it is needed.
- Show a plan or minimal diff.
- Stop and ask for feature-scope approval before applying the change. Once approved, implement, test, commit exact paths, update protected preview when included, and complete automated smoke.

Examples:

- Changing `rag_answer.py` system prompt behavior.
- Changing chunk size, overlap, or thread/post boundary handling.
- Changing Chroma query parameters, reranking, or source filtering.
- Adding required fields to clean corpus records.
- Adding a dependency to `pyproject.toml`.
- Adding a script that writes derived corpus files.

## RED - Codex Must Ask Before Action

Codex must ask before any action involving:

- deleting files/data
- broad renames
- changing scraper behavior
- changing raw corpus data
- rebuilding embeddings/vector index
- modifying database migrations
- auth/payment/access-control changes
- anything affecting private transcripts or licensing metadata

Expected behavior:

- Stop immediately after identifying the RED scope.
- Ask for explicit approval before running commands or editing files.
- State the risk and the exact action being requested.

Examples:

- Deleting generated corpora, raw scrape folders, SQLite manifests, or Chroma stores.
- Renaming `steel_guitar_rag`, package modules, script names, data paths, or the repo broadly.
- Changing scrape retries, queue behavior, parsing behavior, output paths, or database writes.
- Rebuilding `rag-data/electronics/chroma`.
- Mutating licensing metadata or private transcript handling.

## Required Closeout Format

Every Codex task must end with:

1. What changed
2. Tests run
3. Files touched
4. Risks
5. Human decision needed: yes/no
6. Recommended next step

For GREEN tasks, "Human decision needed" is usually "no" unless the result raises a new question.

For YELLOW tasks, "Human decision needed" should usually be "yes" because the next phase requires approval.

For RED tasks, "Human decision needed" must be "yes" before action.

## Repo-Specific Guardrails

- Preserve raw scraped data.
- Do not alter scraper behavior unless explicitly approved.
- Do not rebuild embeddings or vector indexes unless explicitly approved.
- Keep Electronics-only RAG and eval work scoped to the currently indexed Electronics corpus.
- Do not add Pedal Steel technique, E9 theory, B+C pedals, copedent, harmonized-scale, tab, private transcript, or licensing evaluations unless those sources are indexed and approved.
- Do not filter retrieval on copyright or licensing flags until the future review phase is approved.
- Keep Steel Guitar RAG as the user-facing name, use `steel_guitar_rag` for
  Python packages/imports, and use `steel-guitar-rag` for distribution,
  repository, package, and URL slugs.
