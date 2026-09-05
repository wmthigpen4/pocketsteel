# Shared Steel-Theory Core

Status: M1a implemented; not connected to either product runtime

## What This Slice Adds

`packages.steel_theory` is the first product-neutral code in the platform
migration. It owns pure values and calculations for:

- numbered E9 strings and scientific open pitches;
- versioned copedent profiles;
- signed semitone changes for named controls;
- deterministic note resolution by string, fret, and held controls;
- major, minor, diminished, and dominant-seventh chord formulas;
- exact grip analysis and transposable position discovery;
- canonical copedent snapshot serialization and digesting;
- major-key scale-degree triad identity.

It imports no Steel Guitar RAG or Travis Companion module. Neither product
imports it yet.

## First Audited Grip Rules

The first rules deliberately include cases missing or mishandled by the older
starter catalogs:

| Rule | Open-position result | Transposition rule |
|---|---|---|
| Strings 4-5-6, no controls | E major | Major chord rooted at the no-pedal bar fret |
| Strings 4-5-6-9, no controls | E7: E-B-G#-D | Dominant 7 rooted at the no-pedal bar fret |
| Strings 5-6-7, A+B | F# minor: C#-A-F# | ii minor relative to the no-pedal major position |

Thus the A+B 5-6-7 grip is F# minor at the nut in E and A minor at fret 3 in
G. The dominant-seventh rule is E7 at the nut and G7 at fret 3. These are
derived from the copedent and chord formulas, not stored as key-specific answer
sentences.

The standard E9 tuning and A/B changes agree with Bobby Lee's public
`Understanding E9th` chart. That chart also identifies the tuning's open major,
minor, and dominant resources. The implementation still verifies every gold
case from pitches rather than trusting a label:

https://b0b.com/wp/copedents/understanding-e9th/

## Compatibility Boundary

The shared basic profile is `emmons-e9-basic`, revision 1. It currently
contains the ten open strings plus A and B pedal changes because those are the
only controls approved by the v1 candidate fixture. It intentionally does not
copy the private/user-specific copedent or guess lever assignments.

The package is additive. Existing product modules, payload schemas, imports,
answer routing, fretboard UI, and saved data are unchanged. The older runtime
may therefore continue to omit 5-6-7 A+B or return incomplete dominant-position
results until a later adapter/cutover slice is tested and approved.

## Fail-Closed Rules

- Unknown strings, controls, qualities, and notes raise errors.
- Frets outside 0–24 raise errors.
- Duplicate grip strings and duplicate controls raise errors.
- A grip is exact only when its distinct pitch classes equal the full target
  chord formula; partial and color voicings are not promoted as full chords.
- Copedent string order, open scientific pitch, control identity, and changed
  strings are validated when the profile is constructed.

## Next Development Gate

M1b may add read-only projections from the existing RAG copedent profile and an
explicitly approved Howdy profile match. It must prove pitch, control, revision,
and snapshot-digest parity without changing either product consumer. The
dominant and ii-minor cases in this document remain regression tests during
that work.
