# 06 Tab Engine Product Direction

## Product Correction

SVG fretboard owns static positions. Tab engine owns movement over time.

Static grips, static chord locations, and "where is this chord" questions should use the fretboard payload first. Tab is reserved for sequences, movement, licks, exercises, and time-based events.

## Current Tab-Engine Status

The committed tab engine provides:

- standard 10-string E9 profile,
- structured tab events,
- fixed-width rendering,
- validation for string range, fret range, note count, duplicate strings, mixed frets, unknown changes, and changes on unaffected strings,
- examples for G open, G-to-C movement, A+B major position, E-lower color, and beginner lick,
- `/api/tab/render` for deterministic rendering,
- optional answer-triggered tab payloads for safe movement examples.

## Static Grip Behavior

Static examples should be fretboard-first:

- "Show me a G major grip."
- "Show me a 4-5-6 grip."
- "Where is G on E9?"
- "Show me a G chord on strings 4-5-6."

Expected output:

- direct teaching prose,
- fretboard payload,
- no tab example by default.

## Movement / Sequence Behavior

Movement examples may include tab:

- "Show me a G to C move."
- "How do I use A+B pedals?"
- "Show me an A+B example."
- "Show me an E-lower move."
- "Give me a beginner lick in G."

Expected output:

- direct teaching prose,
- compact deterministic tab example,
- matching fretboard payload when useful,
- no source-card dependency.

## Phrase-Sequence Roadmap

Recommended ladder:

1. Deterministic examples.
2. Parameterized chord moves.
3. User-provided melody notes to tab.
4. User-provided lyrics/chords or public-domain material to short fills.
5. Tab explanation and validation.
6. SVG event sync.
7. Practice exercise generator.
8. User copedent profiles.

Do not skip straight to arbitrary song transcription or prompt-only ASCII tab generation.

## Event Stepper Concept

Future UI should treat tab as event data:

- one event equals one pick attack,
- event ids connect tab, fretboard highlight, and explanation,
- selecting a tab event highlights strings/frets/controls on the SVG fretboard,
- selecting a fretboard event can reveal the corresponding tab step,
- backend sends musical event data, not UI geometry.

## Public-Domain Song Tab Direction

Public-domain song tab is a future architecture track, not a shortcut around copyright. It requires:

- explicit song registry,
- verified rights status,
- cited melody/chord/lyric source records,
- stored/cited melody data,
- deterministic arrangement planning,
- mechanical and steel-practical validation,
- source/provenance UI.

If rights status or source basis is missing, the app should not generate song tab.

## Validation Layers

### Mechanical

Validate strings, frets, pedals/levers, affected strings, duplicate strings, slants, and impossible combinations.

### Musical

Validate chord tones, intervals, voice leading, event order, and whether the output matches the requested musical goal.

### Steel-Practical

Prefer playable grips, reasonable bar movement, clear pedal timing, beginner-safe alternatives, and practical copedent assumptions.

### Source / Provenance

Mark whether tab is deterministic exercise, source-backed practice concept, or public-domain song arrangement. Never imply a source supports exact tab unless it actually does.
