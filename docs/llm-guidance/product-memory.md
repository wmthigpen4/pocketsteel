# Product Memory

This is durable product context for future Codex/LLM lanes. Read it before changing answer behavior, product copy, UI prompts, source ingestion, fretboard behavior, or evals.

## Product Identity

- The app/product workstream is Steel Guitar RAG.
- The current repo-level naming instruction says the user-facing app name is The Turnaround. Existing UI/docs/handoffs still use Steel Guitar RAG heavily. Do not do a broad rename without explicit user approval.
- The product is a steel-guitar learning/search assistant, not a generic chatbot.
- The answer principle is: strings, frets, pedals, levers, grips, intervals, copedents, and player-practical context first; generic guitar theory last or never.

## Product Promise

Steel Guitar RAG should:

- Search and synthesize Steel Guitar Forum knowledge.
- Explain E9 mechanics through deterministic copedent/fretboard rules.
- Show visual fretboard positions when the user asks concrete position questions.
- Diagnose gear/tone issues with practical isolation steps.
- Turn broad practice/technique questions into usable drills.
- Use source cards when evidence matters.
- Refuse or redirect off-domain, impossible, unsafe, or copyright-problematic requests.

## Future Source Layers

The long-term source plan includes:

- Steel Guitar Forum.
- Lesson transcripts.
- PDFs.
- OCR notes.
- Manuals.
- Tab documents.
- Copedent/rules-engine notes.
- Curated vendor/official source registry.
- Private source collection behind auth/provenance gates.

Do not ingest or embed new source layers without provenance review and explicit approval.

## Core Product Areas

- Forum wisdom search: source-backed synthesis from public SGF/forum data.
- Copedent-aware coach: deterministic E9 and user-profile-aware answers.
- Lesson transcript navigator: future private/authorized lesson lookup and summarization.
- Tab/interval explainer: safe explanation of strings, frets, pedals/levers, chord tones, and intervals.
- Gear diagnosis assistant: buzz/hum/tone/tuner/string/gig troubleshooting with safety cautions.
- Practice plan generator: steel-specific drills, timing goals, listening targets, and short routines.

## Current User Copedent Facts

These facts are represented in `pocketsteel/user_copedent.py` and should be treated as private/user-specific unless an authorized private/profile answer is being generated.

- Instrument label: Emmons Lashley LeGrande E9.
- 10-string E9 open tuning:
  - 1 F#
  - 2 D#
  - 3 G#
  - 4 E
  - 5 B
  - 6 G#
  - 7 F#
  - 8 E
  - 9 D
  - 10 B
- Pedals:
  - A pedal/P1 raises strings 5 and 10 B to C#.
  - B pedal/P2 raises strings 3 and 6 G# to A.
  - C pedal/P3 raises string 4 E to F# and string 5 B to C#.
- Levers:
  - F lever/LKL raises strings 4 and 8 E to F.
  - E-lower/LKR lowers strings 4 and 8 E to Eb/D#.
  - vertical/LKV lowers strings 5 and 10 B to Bb/A#.
  - RKL/RKLL are half/full states; string 7 F# does not raise to G on RKL/RKLL.
  - RKR/RKRR are half/full states; string 9 D lowers to C# at both RKR half-stop and full-stop.
- Common grips:
  - 3-4-5
  - 4-5-6
  - 5-6-8
  - 5-7-8
  - 6-8-10

If future lanes find these facts stale or incomplete, do not patch answer prose directly. Update the structured source and tests after approval.

## Product Readiness Memory

Recent handoffs show:

- Invalid chord guardrails passed protected-preview smoke.
- Home-prompt hard failures were driven to 0 in local smoke.
- Product red-team hard failures were driven to 0 in local smoke.
- Full pytest reached `585 passed` in the latest Lane 05 final red-team blocker handoff.
- Outside testers still require human burn-in/go-live approval even when smoke suites are green.

## Product Tone

Answers should be calm, direct, practical, and steel-specific.

Prefer:

- "Try strings 4-5-6 at the 3rd fret..."
- "The A pedal raises B to C#..."
- "I need the fret, strings, pedals/levers, and target chord before I can classify that voicing."

Avoid:

- "The corpus says..."
- "Useful source-backed points..."
- "I found source cards..."
- generic guitar theory that never lands on pedal steel mechanics
- raw forum chatter
