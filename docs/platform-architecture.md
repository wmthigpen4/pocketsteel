# Steel Guitar Platform Architecture Constitution

Status: governing target architecture

Adopted: 2026-09-05

This document governs changes while the repository moves from a flat Steel
Guitar RAG application toward two products on one shared platform. It does not
authorize a directory move, product merge, deployment, or data migration.

## 1. Two Products, One Platform

Steel Guitar RAG and Travis Companion are separate products.

- Steel Guitar RAG owns source-aware chat, SGF retrieval, citations, corpus
  workflows, general Explorer experiences, and its own product presentation.
- Travis Companion owns Ask Travis, Travis lessons, Howdy, partner-specific
  content and approvals, and its own product presentation.
- The Steel Guitar Platform owns domain truth shared by either product:
  copedents and steel theory, fretboard state and pitch resolution, tablature
  events/rendering contracts, song/timeline representation, playback
  synchronization, and the Play-Along engine.

Neither product owns a private copy of shared domain truth. A product may own
an adapter, workflow, layout, or teaching voice that consumes the platform.

## 2. Target Layers

```text
apps/
  steel-guitar-rag/       PRODUCT:RAG
  travis-companion/       PRODUCT:COMPANION

packages/
  steel-theory/           PLATFORM:SHARED
  song-model/             PLATFORM:SHARED
  fretboard/              PLATFORM:SHARED
  tablature/              PLATFORM:SHARED
  play-along/             PLATFORM:SHARED

services/
  rag/                    PRODUCT:RAG service
  lesson-context/         product-neutral only where its contract proves it
  transcription/         product-neutral only where its contract proves it
```

This is a dependency model, not today's directory inventory. Current source
locations and duplications are in `docs/shared-component-map.md`.

## 3. Dependency Direction

Allowed source dependencies are:

```text
app -> shared package
shared package -> shared package
service -> shared package
```

Forbidden dependencies are:

```text
shared package -> app
shared package -> service implementation
service -> app
RAG app -> Companion app
Companion app -> RAG app
```

Apps call separately deployed services through documented contracts/clients,
not by importing service internals. Tests and build tools may coordinate
layers, but production imports must obey the same direction. CI enforces these
rules for recognized current and target roots.

## 4. Domain Truth And Product Experience

Product experiences may differ. Domain meaning may not.

Both products must agree on at least:

- string number, tuning, scientific pitch, and fret;
- pedal/lever identity, action, and resulting pitch;
- copedent identity, revision, and target/source distinction;
- grip strings, notes, inversion, and validation state;
- steel event start, duration, strings, frets, controls, pitches, and
  articulation;
- song meter, tempo, sections, timeline, chord events, and steel events;
- selected/current/next event and playback/loop state.

Until canonical contracts are extracted, existing schemas are evidence to
reconcile rather than permission to invent a new representation.

## 5. Shared Capability Ownership

Each shared capability has one canonical contract and may have multiple
product adapters:

| Capability | Platform owns | Products may own |
|---|---|---|
| Steel theory/copedent | tuning, changes, pitch math, spelling, identities | labels, help, profile-management UX |
| Fretboard | state, positions, markers, validation, selection events | Explorer filters, Howdy cues, visual theme |
| Tablature | event schema, validation, semantic transitions, render model | card/page layout, print branding |
| Song model | sections, meter, tempo, timeline, source identity, revisions | catalog browsing, lesson narrative |
| Play-Along | clock, seek, speed, loops, current/next events, synchronization | lesson modes, help density, partner presentation |

## 6. Change Standard

A shared-platform change is not complete until its contract, known consumers,
characterization tests, shared tests, RAG integration tests, Companion
integration tests, staging smoke, and exact commit are recorded. If one
consumer is unavailable, report that missing evidence; do not claim platform
completion from one product's success.

Contract changes are additive by default. A breaking change needs a versioned
contract, migration plan, dual-read/adapter period where practical, explicit
consumer cutover, and rollback. A product-specific request that discovers a
contract gap ends with `NEEDS_ARCHITECTURE_DECISION` unless that contract work
was part of the approved scope.

## 7. Environments And Promotion

The protected application path is:

```text
local -> test.steelguitarrag.com -> app.steelguitarrag.com
```

The public root Pages project and dedicated Travis preview are separate
surfaces, not interchangeable stages. Every promotion names a full commit SHA,
clean immutable artifact, test evidence, environment smoke, and rollback SHA.
Production promotes the staging-approved commit, not a rebuilt branch head.

Environment observation never authorizes mutation. A healthy check does not
authorize restart, promotion, DNS, Access, secrets, port changes, or cleanup.

## 8. Repository Evolution Rules

- Stay in one repository while the products share active domain work.
- Do not create empty target directories merely to resemble the diagram.
- Extract one characterized contract and its smallest implementation at a
  time, preserving public imports through adapters.
- Do not mix platform extraction with product redesign, deployment changes,
  corpus work, or branch cleanup.
- Do not move runtime code while CI is red for unrelated reasons unless the
  exact failure is documented and the slice has independent green evidence.
- Keep historical handoffs as evidence, but link current instructions from
  small canonical indexes so agents do not treat old plans as active.

## 9. Decision Authority

`AGENTS.md` governs how Codex operates. This constitution governs product and
platform ownership. `docs/current-state-inventory.md` records observed state;
it cannot override this constitution. Product contracts govern their named
surface. When documents conflict, stop with the exact conflict rather than
choosing the broader permission.
