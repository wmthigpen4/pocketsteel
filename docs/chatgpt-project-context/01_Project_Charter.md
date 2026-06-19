# 01 Project Charter

## Product Name

The working project identity is Pocket Steel / Steel Guitar RAG. The user-facing app name in repo guidance is The Turnaround. Do not perform a broad rename without explicit approval.

## Purpose

Build a steel-guitar learning and search assistant that answers like a practical pedal-steel teacher. The product should combine deterministic E9 rules, source-aware Steel Guitar Forum retrieval, curated guidance, private/profile-backed lesson material behind auth gates, and future tab/fretboard teaching tools.

The product is not a generic chatbot. It should understand strings, frets, pedals, levers, grips, intervals, copedents, tone symptoms, gear, blocking, bar movement, practice plans, and forum wisdom.

## Audience

- Pedal steel players learning E9 vocabulary, positions, grips, pedals, levers, and practice habits.
- Players who want source-aware answers from SGF and curated sources.
- The project owner, who needs a reliable protected-preview app and a disciplined multi-lane workflow.

## Core Product Principles

- Teacher-first answers: explain the practical musical idea before presenting evidence.
- Deterministic where possible: use E9 rules, fretboard logic, and tab validation instead of retrieval for pitch/mechanics facts.
- Source-aware where useful: use SGF and curated sources as support, not as raw primary answer text.
- Copyright-aware: do not provide full copyrighted song tabs, solo transcriptions, recording transcriptions, or modern arrangements.
- Private material stays private: private guidance, paid lessons, raw source data, embeddings, Chroma stores, and credentials are never broad-staged or exposed.
- UI should teach: fretboard, tab, and source cards should clarify the answer rather than overwhelm it.

## Current App Direction

The app is moving toward a combined answer, fretboard, and tab teaching experience:

- SVG fretboard owns static positions, grips, chord locations, and visual position cards.
- Deterministic tab engine owns movement over time: events, sequences, short licks, and validated tab output.
- Retrieval and source cards support claims when appropriate, but should not dominate deterministic answers.
- Public-domain song tab support is future architecture work and requires explicit source/provenance records.

## ChatGPT Responsibility

ChatGPT should act as orchestrator:

- decide the next slice,
- choose the correct lane,
- write precise Codex prompts,
- keep source/copyright/auth/private-data guardrails visible,
- prevent broad or stale checklist drift,
- interpret integration-status and recent handoffs,
- stop when a human product decision is needed.

## Codex Responsibility

Codex should execute scoped repo work:

- inspect local guidance and git state,
- modify only approved files,
- run focused checks,
- write handoffs,
- stage exact paths or exact hunks only,
- commit only when instructed or when repo auto-approval rules apply,
- keep unrelated dirty work parked.

## User Decisions

The user decides:

- product direction and naming,
- broad feature priority,
- copyright/source risk tolerance,
- when protected preview is ready for broader user smoke,
- deployment, DNS, auth, and secret changes,
- whether parked dirty work should be committed, isolated, or discarded.
