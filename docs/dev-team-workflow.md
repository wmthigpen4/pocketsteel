# Developer Team Workflow

Steel Guitar RAG uses a conservative, human-in-the-loop workflow. The goal is to keep daily development moving while protecting scraper behavior, raw corpus data, private materials, paid transcripts, licensing metadata, generated indexes, and credentials.

## Names

- User-facing app name: Steel Guitar RAG.
- Python package/import namespace: `steel_guitar_rag`.
- Distribution, repository, package, and URL slug: `steel-guitar-rag`.

## Task Classification

Classify every task before acting.

### GREEN

Codex can implement and verify without stopping for approval:

- docs edits
- small UI copy changes
- tests
- evaluation scripts
- read-only analysis
- non-destructive refactors under one module

Expected closeout: summarize the change, checks, files touched, risks, whether a human decision is needed, and the recommended next step.

### YELLOW

Codex can inspect and propose a plan or diff, then must stop for approval before applying changes:

- RAG prompt changes
- chunking changes
- retrieval ranking changes
- schema changes
- dependency changes
- UI flow changes
- new scripts touching corpus outputs

Expected closeout: state the approval needed before the next phase.

### RED

Codex must ask before taking action:

- deleting files or data
- broad renames
- changing scraper behavior
- changing raw corpus data
- rebuilding embeddings or vector indexes
- modifying database migrations
- auth, payment, or access-control changes
- anything affecting private transcripts, paid transcripts, or licensing metadata

Expected closeout: state the exact action that needs explicit approval.

## Safety Rules

- Do not modify scraper behavior without explicit RED approval.
- Do not run live scraping from this repo.
- Do not delete files or data without explicit approval.
- Do not commit raw data, SQLite databases, credentials, logs, Chroma stores, embeddings, vector indexes, private transcripts, paid transcripts, or licensing metadata dumps.
- Keep generated corpus outputs in ignored locations such as `data/processed/`, `data/indexes/`, `rag-data/electronics/`, or `rag-data/forums/`.
- Prefer small, reviewable changes. Keep unrelated refactors out of the same task.

## Suggested Branch And Review Flow

1. Confirm task mode from `AGENTS.md`.
2. Inspect current status with `git status --short`.
3. For GREEN tasks, make the smallest complete change and run relevant lightweight checks.
4. For YELLOW tasks, inspect and prepare a plan or proposed diff only, then request approval before editing.
5. For RED tasks, stop and request approval before commands or edits.
6. Before handoff, run `git diff --check` and any relevant tests.
7. Close out with changed files, moved files, commands run, risks, human decision needed, and the recommended next task.

## Data Handling

Raw scrape output, local SGF exports, generated corpora, SQLite manifests, and vector stores are local working artifacts. They should not be committed.

Small fixtures can live under `tests/fixtures/` when they are intentionally tiny, shareable, and free of private transcripts, paid transcripts, credentials, licensing metadata dumps, or large scrape excerpts.

## When In Doubt

Choose the more cautious task mode, explain the uncertainty, and ask for the smallest approval that unblocks the work.
