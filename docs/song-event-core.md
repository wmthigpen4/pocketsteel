# Shared Song and Steel-Event Core

Status: M2a implemented; no product consumer or persistence migration

Scope: `PLATFORM:SHARED`

The `packages.song_model` package is the product-neutral implementation of the
reviewed synthetic `steel_platform_timeline_v1` contract. It gives RAG and
Companion one deterministic vocabulary for time, song structure, chords,
steel performance, reusable fretboard positions, and current/next selection.
Neither product consumes it yet.

## Accepted M2a Boundary

M2a includes only:

- immutable clock, structure, position, chord-event, steel-event, note,
  articulation, transition, and validity values;
- a strict in-memory parser and validator;
- canonical dictionary/JSON serialization and a reproducible timeline digest;
- window-to-root clock transforms;
- nullable current/next event selection for pre-roll, active playback, gaps,
  boundaries, and post-roll;
- mechanical note checks against the accepted shared copedent core.

The shared package imports only `packages.steel_theory`. It does not import
RAG, Companion, browser code, persistence, deployment, or partner content.

## Fail-Closed Rules

The parser rejects:

- unknown schema versions and fields outside the v1 interchange boundary;
- missing, repeated, or dangling IDs;
- invalid or cyclic clock graphs and windows that exceed their parent;
- event or structure ranges outside their named clock;
- non-reciprocal structure membership;
- noncanonical event ordering and overlap on the same logical track;
- steel events outside their referenced chord event;
- unresolved positions or chord references;
- pitches that disagree with string, fret, controls, and copedent;
- repeated or unsorted controls; and
- unknown role, validity, articulation, or transition vocabulary.

Separate tracks may overlap. Product-specific approvals, teaching copy,
provenance, release state, and display preferences remain outside the shared
document.

## Evidence

`tests/test_platform_song_model.py` proves exact round-trip behavior against
the synthetic candidate and covers clock transforms, selection boundaries,
gaps, independent tracks, reference integrity, same-track overlap, mechanical
pitch validation, technique vocabulary, schema versioning, and product-field
exclusion. The earlier characterization test remains independent evidence.

The user's previously identified deterministic fretboard rules remain M1
regressions: strings 4-5-6-9 form the transposable dominant seventh family,
and strings 5-6-7 with A+B form the ii-minor family at the open major
position. M2a resolves every timeline note through that accepted core.

## Explicit Non-Changes

M2a does not:

- adapt RAG or Howdy records;
- change `song_practice_plan_v1`, `lesson_companion_v1`, or any stored record;
- change an API, browser consumer, current production behavior, or test site;
- introduce a dual write, backfill, feature flag, or deployment; or
- move existing product modules into a new directory layout.

## Next Gate

M2b is the next bounded candidate: a read-only RAG event adapter tested against
the pinned RAG fixture. It must preserve the source record, return explicit
loss/ambiguity diagnostics, and make no runtime consumer change. M2c remains a
separate Howdy adapter slice, followed by cross-product parity in M2d.
