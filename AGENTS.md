# Agent Operating Model

This repo uses a human-in-the-loop workflow. Codex should classify every task before acting and should not continue into a second phase automatically unless the user explicitly approves it.

The user-facing app name is The Turnaround. Keep `pocketsteel`, `pocket-steel`, and `pocket_steel` as internal technical names unless the user explicitly approves a rename.

## Task Modes

### GREEN - Codex Can Proceed

Codex may implement and verify these tasks without stopping for approval:

- docs edits
- small UI copy changes
- tests
- evaluation scripts
- read-only analysis
- non-destructive refactors under one module

### YELLOW - Stop After Plan/Diff

Codex may inspect and propose a plan or diff, but must stop before applying or committing the change unless the user approves:

- RAG prompt changes
- chunking changes
- retrieval ranking changes
- schema changes
- dependency changes
- UI flow changes
- new scripts touching corpus outputs

### RED - Ask Before Action

Codex must ask before taking action on:

- deleting files/data
- broad renames
- changing scraper behavior
- changing raw corpus data
- rebuilding embeddings/vector index
- modifying database migrations
- auth/payment/access-control changes
- anything affecting private transcripts or licensing metadata

## Required Closeout

For every task, Codex must end with:

1. What changed
2. Tests run
3. Files touched
4. Risks
5. Human decision needed: yes/no
6. Recommended next step

If a task is YELLOW or RED, the closeout must clearly state what approval is needed before the next phase.

