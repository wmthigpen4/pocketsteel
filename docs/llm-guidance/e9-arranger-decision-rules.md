# E9 Arranger Decision Rules

## Purpose

This document records the evidence gate for turning steel-guitar teaching material into deterministic Melody Studio decisions. It is an engine contract, not a corpus-ingestion plan and not a source-card policy.

The arranger may use a teaching rule only when all three checks pass:

1. The standard-E9 copedent proves every sounding pitch and control change.
2. Public Steel Guitar Forum material independently supports the playing concept or decision pattern.
3. Reviewed lesson transcripts corroborate the concept without being copied, quoted, exposed, or treated as public provenance.

Cleaned summaries and extracted lesson notes are leads for review, not positional authority. A fret, string, grip, chord name, or pedal/lever claim from a summary must never enter runtime behavior without pitch validation.

## Accepted Decision Rules

### Controls describe interval changes

- A pedal raises the affected fifths to sixths.
- B pedal raises the affected thirds to fourths.
- The E-raise/F lever raises the affected roots by a semitone.
- The E-lower lever lowers the affected roots by a semitone.
- C pedal changes only its affected strings and is not a general-purpose harmony switch.
- Player-facing names may vary by copedent, but the engine must compare canonical mechanical control IDs.

The arranger chooses a control because it produces the required pitch and harmonic function, not because a familiar lick happens to use it.

### Stay in a harmonic pocket when the music allows it

- Preserve the exact melody pitch and register first.
- Prefer a validated route near the current bar position over an unnecessary jump to a more familiar posture.
- Treat a single note or dyad as a subset of its compatible three-string family when that keeps the phrase coherent.
- Retaining an already established F-lever or E-lower posture is normal pocket continuity, not a new complexity event.
- Open, A+B, A+F, and E-lower positions are alternatives whose musical usefulness depends on the current chord, melody register, and route into and out of the position.

### Restrict C and B+C to their actual jobs

- C-pedal use requires an exact affected-string and pitch check.
- B+C is valid for specific minor, scale, and double-stop functions; it is not a default substitute for A+B or a way to make every arrival into a larger grip.
- A transient B+C position must lose to a simpler valid route when it breaks the pocket without adding required harmony.
- Literal user-entered C or B+C tab remains fixed after mechanical validation.

### Harmony follows the melody voice

- Resolve the melody note and scientific register before adding supporting voices.
- The resolved melody remains the highest voice in dyads and triads.
- Supporting notes must fit real chord context when chord symbols exist.
- A non-chord melody tension favors a single note or validated dyad instead of a fabricated triad.
- Texture is a performance choice: passing motion and pickups may be single notes, sustained emphasis may use dyads, and supported arrivals or cadences may use triads.

### Slides are complete musical movements

- A full-grip attack and slide is the primary generated slide model when two or three voices can move mechanically.
- A melody-only slide is an explicit exception. The lesson must say which strings sustain, release, appear, or are repicked.
- A generated slide never overwrites the source or destination event and never invents an extra melody note.
- Endpoint tab must show complete strings, frets, pedals, and levers. Connector columns describe the motion between those endpoints.
- Do not recommend adjacent ornamental transitions or a transition that cannot sustain the stated voices.

### Blocking follows intended sustain

- Do not prescribe blocking merely because the bar or grip changes.
- Sustain voices that are part of a validated full-grip slide or audible pedal/lever glide.
- Block abandoned strings before a new attack when they are not intended to ring into the destination.
- Large string-group changes need an explicit right-hand decision; the exact technique may vary, so the engine should describe the musical result before naming a hand method.

## Runtime Rules Implemented

- Candidate pitches and grips are validated against the standard-E9 copedent.
- The mixed route ranks harmonic correctness, pocket continuity, voice leading, string-group continuity, control posture, bar travel, texture, and difficulty deterministically.
- C-pedal postures remain exceptional, with a validated B+C minor arrival retained as a specific allowed case.
- An established F-lever or E-lower posture may continue without an artificial lever-category penalty.
- Single-note and grip candidates now share canonical `E` and `F` control IDs, preventing the same mechanical posture from being counted as a control change solely because one source used a friendly label.
- Full-grip slides are preferred; one-note-into-three-note generated slides are rejected.
- Reviewed blocking fixtures require a full-grip slide to sustain every attacked string. A changed-grip exception must separately identify the sustained melody, strings blocked before the move, strings repicked at the destination, and newly added strings.
- Reviewed lever-density fixtures prefer the no-lever position when E-lower or F-lever offers no musical or mechanical benefit, while retaining one already established E-lower or F-lever span instead of repeatedly entering and leaving it.
- Tab, fretboard, score, transition instructions, and playback continue to derive from the same event path.

## Rules Still Requiring Focused Product Tests

- Player-facing blocking guidance for non-transition string-group changes.
- Broader phrase-level lever limits beyond the reviewed no-benefit and continuous-span fixtures.
- Additional reviewed harmonic-scale pathways beyond the current G/C major contract.
- Difficulty-aware alternatives that show a simpler route without replacing the musically recommended route.
- Custom-copedent naming and mechanics.

These remain out of runtime until they have reviewed fixtures and mechanical assertions.

## Public Evidence Index

The local SGF corpus review used public discussions including:

- [B & C pedals](https://steelguitarforum.com/Forum5/HTML/007387.html)
- [I-IV change](https://steelguitarforum.com/Forum8/HTML/000542.html)
- [Raising the 4th string to F# on the E9th neck](https://steelguitarforum.com/Forum5/HTML/011717.html)
- [Palm blocking made easy for beginners](https://bb.steelguitarforum.com/viewtopic.php?t=200502)
- [Pick Blocking Technique](https://steelguitarforum.com/Forum8/HTML/000624.html)
- [Whole new look at the fretboard](https://bb.steelguitarforum.com/viewtopic.php?t=363336)
- [Scales for Dummies](https://steelguitarforum.com/Forum5/HTML/005963.html)
- [Do you play 2 or 3 string chords](https://steelguitarforum.com/Forum5/HTML/003950.html)

Forum posts are practical evidence, not mechanical truth by themselves. The copedent validator remains authoritative whenever terminology or positional advice conflicts.

## Privacy and Corpus Boundary

- No private lesson transcript is a public source card.
- No private transcript body, metadata, signed media URL, or lesson-specific wording may be copied into public output.
- This review does not authorize transcript ingestion, embeddings, Chroma changes, scraping, or corpus modification.
- Generalized rules may be retained only through this evidence gate and independent mechanical validation.
