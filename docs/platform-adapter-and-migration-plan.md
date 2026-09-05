# Platform v1 Adapter and Non-Migration Plan

Status: M1a core, M1b copedent projections, M2a song/event core, and M2b
read-only RAG adapter implemented; M2c–M2d and consumer cutover remain
separate architecture-review candidates

## Adapter Boundary

Adapters are pure projections from existing product records. They return:

```text
timeline: steel_platform_timeline_v1 candidate
productMetadata: untouched product-only fields
diagnostics: loss, ambiguity, and unsupported-vocabulary findings
```

The source record remains authoritative. An adapter must not write, rename,
backfill, dual-write, or silently repair it. A non-empty error diagnostic
prevents parity approval.

## Steel Guitar RAG Projection

Source evidence is the `song_practice_plan_v1` fixture and its associated tab,
fretboard, selection, and loop projections.

| RAG source | Candidate projection |
|---|---|
| plan identity/revision | namespaced timeline `id`; adapter-supplied revision 1 for an ephemeral projection |
| target copedent ID/revision | `copedent.profileId` and `copedent.revision` |
| resolved copedent profile | canonical `copedent.snapshot` and digest |
| plan event timing | one `media` clock; unchanged `startMs`/`endMs` |
| event `chord` | distinct chord event with deterministic `rag:chord:<event-id>` identity |
| event position | reusable position plus steel event with deterministic `rag:steel:<event-id>` identity |
| chord/position streams | deterministic `chords` and `steel-main` track IDs |
| `sectionId` | `section` structure reference |
| `measureId` | `measure` structure reference |
| event `role` | steel body `role` |
| note `changes` | note `controls` |
| standalone tab-note `articulation` | mapped articulation/transition entries or an explicit diagnostic; Song Practice position notes have no implied articulation |
| resolved pitch | note `pitch` |
| position validation | mechanical `validity`; product warnings remain outside |
| plan provenance | RAG `productMetadata`; never copied into mechanical validity |

Repeated adjacent RAG chord values may initially remain separate chord events
to guarantee a lossless one-event projection. Coalescing them is a later,
separately tested normalization and is not part of the first adapter.

## Travis Companion / Howdy Projection

Source evidence is the sanitized `lesson_companion_v1` fixture pinned to the
preserved Companion commit.

| Howdy source | Candidate projection |
|---|---|
| companion ID/revision | namespaced timeline `id` and `revision` |
| `media.scopes.fullSong` | root `media` clock |
| `media.scopes.taughtSolo` | `window` clock mapped to the full-song start |
| `chordTimeline` | chord events on the taught-solo clock; fixed chord grips become reusable positions |
| `events` | steel events on the taught-solo clock |
| chord/performance streams | deterministic `chords` and `steel-main` track IDs |
| event `phraseId` | `phrase` structure reference |
| bar/beat fields | product metadata until shared musical-position evidence is complete |
| `tabNotes[].controls` | note `controls` |
| `tabNotes[].technique` | mapped articulation/transition entries or an explicit diagnostic |
| `notationPitch` | cross-check for the resolved note pitch, not a replacement for it |
| compact copedent | expanded snapshot from an explicitly matched profile ID/revision supplied to the adapter |
| `musicalVerified` | Companion product metadata |
| approvals/release/review | Companion product metadata |
| instruction/rhythm/movement | Companion product metadata until each has a reviewed shared vocabulary |

The low-level Howdy selector currently saturates at the final item. Its adapter
must expose canonical nullable selection. Companion presentation may continue
showing the last card through a product-only display rule.

The sanitized Howdy snapshot identifies affected strings but not semitone
deltas or a profile revision. The adapter must receive an explicitly approved
canonical profile match; conventional A/B behavior must not be guessed from
control names. A missing match is an error diagnostic and blocks parity.

## Required Adapter Diagnostics

Each adapter reports:

- unmapped source fields;
- unsupported source technique tokens;
- missing or ambiguous clock mappings;
- dangling structure or chord references;
- copedent controls that cannot be expanded to semitone changes;
- pitch disagreement between source notation and canonical resolution;
- relative chord functions that lack the key context needed for absolute
  normalization;
- any transformation that would discard information.

Warnings may permit shadow comparison. Errors prevent parity and consumer
cutover. Diagnostics must contain field paths and safe summaries, not private
lesson text or partner-review material.

## Persistence Guarantee

The M1/M2 implementation phase is read-only with respect to product data:

- no database or storage migration;
- no change to `song_practice_request_v1`, `song_practice_plan_v1`,
  `score_draft_v1`, or `lesson_companion_v1`;
- no dual writes;
- no automatic backfill;
- no checked-in private Companion artifact;
- no product schema-version bump;
- no switch in the current runtime reader or renderer;
- no deployment or feature-flag activation.

Canonical projections are created in memory during tests or disabled shadow
comparison. Rollback removes or disables the new validator/adapters; existing
records remain untouched because they were never rewritten.

## Bounded Implementation Sequence

### Slice M1a — Steel-Theory Core

Implement pure pitch, note spelling, copedent profile/snapshot, control-delta,
mechanical resolution, and canonical snapshot serialization behavior. Consume
only the copedent and position portions of the synthetic candidate fixture. Do
not import either product and do not move existing product modules.

Exit: shared unit tests pass and the platform package has no product imports.

### Slice M1b — Copedent Projections

Add read-only copedent projections from the characterized RAG profile and from
an explicitly approved Howdy profile match. Compare string, control, pitch,
revision, and digest behavior. Do not change either product consumer.

Exit: zero copedent error diagnostics; both characterization suites pass.

Outcome: implemented for the RAG A/B projection and the explicitly approved
sanitized Howdy `synthetic-e9` fixture match. The successful projections share
one snapshot/digest and preserve warnings for RAG controls outside M1a and
Howdy's omitted revision/deltas. Neither product consumes the projection.

### Slice M2a — Song/Event Core

Implement pure clock, structure, position, event-envelope, validation,
serialization, and selection behavior against the synthetic candidate fixture.
The package may depend on the approved steel-theory package; neither shared
package may import a product.

Exit: shared clock/event tests pass and dependency direction remains green.

Outcome: implemented in `packages.song_model` against the synthetic fixture.
The strict validator, canonical serializer/digest, root-clock transforms, and
nullable selection are shared-only. Product records, APIs, browsers,
persistence, production, and the test site are unchanged.

### Slice M2b — RAG Adapter

Add a pure adapter for the characterized RAG fixture. Compare canonical
projection with existing RAG pitch, event, and selection behavior. Do not
change RAG API or browser consumers.

Exit: zero error diagnostics and documented warnings; existing RAG tests pass.

Outcome: implemented as `project_rag_song_practice`. The characterized plan
projects with zero errors. RAG-only fields are preserved as product metadata;
derived clock/structure ranges and the existing saturated post-roll display
behavior are explicit warnings. The adapter is not called by a product
runtime and changes no source record.

### Slice M2c — Howdy Adapter

Port only the minimum sanitized mapping code needed to project the preserved
Howdy fixture. Do not merge the legacy branch or copy private review content.

Exit: zero error diagnostics, explicit technique mappings, and preserved
Companion characterization tests.

### Slice M2d — Cross-Product Parity

Normalize equivalent synthetic progressions from both adapters and compare
clock transforms, copedent pitch, chord references, steel-note state, and
selection. Relative `I`/`IV` chords may be compared with absolute `G`/`C` only
when explicit G-major harmonic context is supplied; adapters must not infer the
key from product identity or teaching copy. Differences in product metadata
are expected and excluded.

Exit: shared semantics match without modifying either source record.

### Later Consumer Cutover

Consumer cutover is a separate approved change. It requires RAG and Companion
consumer tests, protected-preview smoke for every deployed surface, an exact
candidate commit, rollback commit, and explicit persistence decision.

## Acceptance Matrix

| Gate | Shared | RAG | Companion |
|---|---|---|---|
| Candidate example validates | required | — | — |
| Clock transforms and boundaries | required | current timeline parity | full-song/taught-solo parity |
| Copedent snapshot digest | required | registry projection | compact-snapshot expansion |
| Pitch/control mechanical checks | required | resolved-position parity | notation/tab-note parity |
| Chord reference integrity | required | embedded-chord split | existing chord reference |
| Technique mapping diagnostics | required | `articulation` mapping | `technique` mapping |
| Current/next behavior | nullable canonical result | pre/post-roll parity | saturation retained only in UI adapter |
| Persistence unchanged | required | request/plan unchanged | lesson package unchanged |

## Architecture Review Outcome

Reviews have ended in `PASS` for M1a, M1b, M2a, and M2b only. Each later-slice
review ends in one of:

- `PASS`: approve only the named next slice;
- `NEEDS_ARCHITECTURE_DECISION`: list exact contract choices to revise;
- `NEEDS_PRODUCT_DECISION`: list product behavior that cannot be projected
  without loss;
- `BLOCKED`: name missing evidence.

M2c and later slices remain bounded by their own consumer evidence and normal
repository gates. M2b completion does not authorize the Howdy adapter,
cross-product parity, a runtime consumer, persistence change, deployment, or
directory move.
