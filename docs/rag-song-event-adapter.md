# Read-Only RAG Song/Event Adapter

Status: M2b implemented; no RAG consumer or persistence migration

Scopes: `PLATFORM:SHARED` with `PRODUCT:RAG` as a read-only source

`packages.song_model.project_rag_song_practice` converts an existing
`song_practice_plan_v1` value into the shared timeline in memory. The source
plan remains authoritative and is neither modified nor replaced.

## What Is Mapped

| RAG plan value | Shared timeline value |
|---|---|
| timeline hash | namespaced timeline identity |
| target copedent ID/revision | exact supplied shared profile match |
| final event boundary | derived media-clock duration |
| event timing | unchanged half-open chord and steel-event ranges |
| event chord | separate chord event |
| event role | steel-event role |
| section/measure IDs | distinct namespaced structures |
| resolved position | reusable static fretboard position |
| note string/fret/changes | shared held mechanical state |
| note MIDI/pitch label | cross-check against the shared copedent |

Each source event becomes one chord event and one steel event on separate
logical tracks. IDs are deterministic and prefixed with `rag:`. Static Song
Practice positions do not imply articulations or transitions, so the adapter
emits neither.

## Product Metadata And Diagnostics

RAG-only values remain in `product_metadata` with their original values. This
includes the source schema, level, route, provenance, display label, product
warnings, event status, alternate positions, teaching instructions, display
control labels, chord-analysis labels, and note display labels. New unrecognized
RAG-only fields are also preserved and reported rather than discarded.

Warnings record:

- every product-only source field retained outside the shared timeline;
- media duration derived from the final event because the plan has no media
  duration;
- section and measure ranges derived from their referenced event boundaries;
- source-event reordering when canonical timing order is required; and
- the known post-roll difference: RAG presentation retains the final event,
  while shared selection returns nullable current/next IDs after the end.

Errors prevent a timeline from being returned. They cover schema/profile
mismatch, unresolved/manual events, invalid ranges, unsupported roles,
conflicting position IDs, position/note inconsistency, unknown controls,
pitch disagreement, dangling references, and same-track overlap.

## Evidence And Limits

`tests/test_platform_rag_song_adapter.py` creates the characterized RAG plan
through the existing product planner, passes it through the M1b copedent
projection and M2b song adapter, and compares timing, IDs, structures, chords,
positions, pitches, and selection behavior. It also proves that the adapter
does not import `steel_guitar_rag` and that the input plan is unchanged.

M2b is not a RAG runtime integration. No API, browser, saved plan, schema
version, playback controller, feature flag, or deployment consumes the shared
timeline. Alternate positions stay in product metadata until a separate
shared contract decision authorizes them.

## Next Gate

M2c is the next bounded candidate: a read-only Howdy adapter using only the
sanitized, source-pinned Companion fixture and the explicitly approved
synthetic copedent match. Private lesson/review content, runtime consumers,
persistence, and deployment remain outside that slice.
