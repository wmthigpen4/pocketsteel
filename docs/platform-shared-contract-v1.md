# Steel Guitar Platform Shared Contract v1 Candidate

Status: architecture-review candidate; not a runtime or persistence contract

Decision owner: Lane 18 Product / Architecture

Evidence: `docs/platform-contract-comparison.md`,
`tests/fixtures/platform_rag_contract_v1.json`, and
`tests/fixtures/platform_howdy_contract_v1.json`

## Purpose

This candidate defines the smallest shared musical vocabulary needed by Steel
Guitar RAG and Travis Companion. It resolves the M0 contradictions without
making either product's existing payload the platform contract.

The candidate is intentionally limited to clock domains, song structures,
chord events, steel events, copedent snapshots, tablature state, mechanical
validity, and deterministic current/next selection. It does not authorize
runtime extraction, persisted-data migration, product cutover, or deployment.

## Contract Boundary

The shared document is `steel_platform_timeline_v1`. Its required top-level
members are:

| Member | Meaning |
|---|---|
| `schemaVersion` | Exactly `steel_platform_timeline_v1`. |
| `id` | Stable document identity, namespaced by the producer. |
| `revision` | Positive integer revision of that identity. |
| `clocks` | One or more named clock domains. |
| `copedent` | Versioned profile identity plus a serializable snapshot. |
| `positions` | Reusable mechanically validated fretboard positions. |
| `structures` | Optional sections, measures, and phrases. |
| `events` | Typed chord and steel events. |

All IDs are non-empty strings and unique within their collection. References
must resolve inside the same document. Product approvals, teaching copy,
rights, source citations, RAG provenance, partner metadata, display settings,
and release data are outside this boundary.

## Clock Domains

A clock has:

- `id`;
- `kind`: `media` or `window`;
- `durationMs`: a positive integer;
- `parentMapping`: `null` for a root clock, or an object containing
  `parentClockId` and non-negative `parentStartMs` for a window.

Milliseconds are the authoritative v1 synchronization unit. Bar, beat, tick,
tempo, and meter may be added later as musical annotations; they must not
change v1 event selection.

For a window clock, local time maps to its parent as:

```text
parent time = parentStartMs + local time
```

Clock graphs must be acyclic. A window must fit completely inside its parent.
The example maps local `taught-solo` time 0 to full-song time 1000.

## Fretboard Positions

A position has `id`, one or more note states, and `validity`. A note state has
`string`, `fret`, sorted unique `controls`, and resolved `pitch`. It does not
have articulation or transition data because it represents a static mechanical
state. Chord and steel events may reference a position by `positionId`.

Positions preserve RAG's resolved/validated grips and Howdy's fixed chord grips
without making either product infer a chord shape in its browser. The
performance notes on a steel event remain authoritative for what is played;
an optional position reference supplies reusable fretboard state.

## Structures

A structure has `id`, `kind`, `clockId`, `startMs`, `endMs`, and `eventIds`.
`kind` is one of `section`, `measure`, or `phrase`.

Sections, measures, and phrases are distinct. Adapters must not rename one as
another. A structure may contain zero or more event references, but every
reference must resolve and its event must fall inside the structure after both
ranges are mapped to a common clock.

## Typed Event Envelope

Every event has:

| Member | Rule |
|---|---|
| `id` | Stable, unique string. |
| `kind` | `chord` or `steel`. |
| `trackId` | Stable logical stream used for deterministic selection. |
| `clockId` | Existing clock-domain ID. |
| `startMs` | Non-negative integer, inclusive. |
| `endMs` | Integer greater than `startMs`, exclusive. |
| `structureIds` | Zero or more existing structure IDs. |
| `body` | Payload selected by `kind`. |

Canonical ordering is `(clockId, startMs, endMs, trackId, id)`. Events within
one `(clockId, trackId)` stream must not overlap. Separate tracks permit future
melody/harmony voices without making singular current/next selection
ambiguous. Producers must emit deterministic IDs and ordering. Consumers must
not infer event type from the contents of `body`.

### Chord Event

A chord body contains a non-empty `symbol` and nullable `positionId`. Chord
function, spelling, or key context may be added additively after evidence
supports a common vocabulary.

### Steel Event

A steel body contains:

- `role`: `comp`, `melody`, `harmony`, or `unspecified`;
- nullable `chordEventId` referencing a chord event;
- nullable `positionId` referencing a reusable fretboard position;
- one or more `notes`;
- `validity`, containing `status` and mechanical `checks`.

`validity.status` is `valid`, `invalid`, or `unverified`. Platform validators
may report only mechanical facts such as string bounds, fret bounds, defined
controls, and pitch consistency. Human musical review and partner approval do
not belong in this object.

## Tablature Note and Performance Vocabulary

A steel note contains:

- `string`: integer 1–10 for the current E9 candidate;
- `fret`: integer 0–24;
- `controls`: sorted unique control IDs representing the held state;
- `pitch`: resolved `midi` integer plus scientific-pitch `label`;
- `articulations`: zero or more transient actions;
- `transitions`: zero or more paths into this state.

The held state and the way the player arrived there are separate. Controls are
not articulations, and a display token is not the semantic transition.

Initial articulation kinds are `pick`, `repick`, `sustain`, `release`, and
`unspecified`. Initial transition kinds are `bar-slide`, `control-change`,
`mixed`, and `unspecified`. A transition may add `fromFret`, `toFret`,
`controlsAdded`, or `controlsReleased` when applicable.

Adapters must not guess when a source technique cannot be mapped. They return
an explicit diagnostic and use `unspecified` only while preserving the source
value outside the shared document for review.

## Copedent Identity and Snapshot

The copedent object has:

- `profileId`: stable profile identity;
- `revision`: positive integer;
- `snapshotDigest`: `sha256:` followed by the digest of canonical snapshot
  JSON;
- `snapshot`: tuning name, string order, open pitches, and control changes.

`snapshot.stringOrder` is `numbered-high-to-low`. The snapshot contains exactly
one entry for every supported string. A control has an `id` and one or more
changes; each change names a string and signed semitone delta.

Profile identity is authoritative for lookup. The snapshot makes packaged and
offline consumers reproducible. A producer must fail rather than emit a digest
that does not match its canonical snapshot serialization. Canonical snapshot
serialization is UTF-8 JSON with object keys sorted lexicographically, no
insignificant whitespace, and Unicode characters emitted directly.

## Deterministic Selection

Selection accepts a clock ID, track ID, and time in that clock. It returns:

```text
phase: pre-roll | active | post-roll
currentEventId: string | null
nextEventId: string | null
```

The active interval is inclusive at `startMs` and exclusive at `endMs`.
Before the first event, current is null and next is the first event. During an
event, current is that event and next is the following event or null. In a gap
between events, phase remains `active`, current is null, and next is the next
event. At or after the final end, both are null. Products may visually keep the
final card, but that is presentation state and does not change canonical
selection.

## Version and Compatibility Policy

- v1 readers reject an unknown `schemaVersion`.
- Additive optional fields may be introduced without renaming existing fields
  or changing their meaning.
- New required fields, changed units, changed selection boundaries, or changed
  enum meaning require a new contract version.
- Adapters own legacy aliases such as `changes`, `technique`, and embedded
  chords. The shared contract does not expose duplicate aliases.
- A valid v1 document is an interchange projection. It is not automatically a
  product's persistence model.

## Review Decisions

Architecture review must explicitly accept or change these proposed choices:

1. milliseconds are authoritative in v1;
2. chord and steel events use one typed envelope;
3. sections, measures, and phrases remain distinct;
4. steel events reference separate chord events;
5. controls, articulations, and transitions are separate;
6. copedents carry both identity/revision and a reproducible snapshot;
7. canonical selection uses nullable current and next IDs;
8. reusable validated positions preserve fixed fretboard grips;
9. non-overlapping logical tracks make singular selection deterministic;
10. product approval and provenance remain outside the shared document.

Until that review passes, `steel_platform_timeline_v1` is a candidate name and
must not be used in product runtime or persisted artifacts.

## Acceptance Gate for Implementation

The first implementation slice may begin only after review and must remain
side-effect-free. It must provide:

- a pure validator and deterministic canonical serializer;
- clock-graph and clock-transform tests;
- mechanical copedent/pitch validation;
- current/next selection tests for pre-roll, boundaries, gaps, and post-roll;
- a RAG adapter tested against `platform_rag_contract_v1.json`;
- a Howdy adapter tested against `platform_howdy_contract_v1.json`;
- diagnostics for every unmapped source field or technique;
- proof that no product read/write path, schema version, deployment, or
  persisted record changed.

The proposed example lives in
`tests/fixtures/platform_shared_contract_v1_candidate.json`. Its tests verify
the candidate's internal invariants; they do not constitute architecture
approval or runtime adoption.
