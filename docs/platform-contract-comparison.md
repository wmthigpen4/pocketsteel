# RAG and Howdy Contract Comparison

Status: M0 characterization with M1 copedent decisions recorded; event-model
architecture inputs remain candidates

Baselines:

- RAG: `origin/main` at `4a77e849c9c9ba8e13429d91ae055d06d0de7ce5`
- Howdy: `preserve/companion-howy-v9-9a79d45-20260905` at
  `9a79d454491b843f74942ce9193f335512e402ad`

The fixtures `platform_rag_contract_v1.json` and
`platform_howdy_contract_v1.json` freeze observable behavior without declaring
either product's current shape to be the final platform schema.

## Agreement and Contradiction Matrix

| Concern | Agreement | Difference or contradiction | M1/M2 direction |
|---|---|---|---|
| Runtime authority | Both paths are deterministic and do not require RAG/model calls to select authored steel state. | Howdy declares `runtimeMode` and `modelCallsAllowed`; RAG records `provenance.ragUsed: false`. | Shared contracts need one explicit authority/provenance object with product extensions. |
| Event identity | Both use stable string IDs and ordered millisecond ranges. | Howdy events are note/tab events; Stage 1 RAG Song Practice events are chord-comping events. | Do not collapse them into one untyped event. Define a shared timed-event envelope plus typed steel-note and chord events. |
| Timing boundary | Both use inclusive `startMs` and exclusive `endMs`. | RAG permits pre-roll with `current: null, next: first`; Howdy falls back to the final item in its low-level selector and separately masks out-of-solo display state. | Preserve explicit pre-roll/active/post-roll states; do not encode them through fallback items. |
| Next selection | Both derive next state from ordered events. | RAG returns `next: null` at the final event; Howdy saturates next to the final event. | Canonical selector should return nullable `current` and `next`; product adapters may repeat the final card visually. |
| Song clock | Both use millisecond clocks and exact authored ranges. | RAG uses one absolute recording timeline. Howdy's steel events are relative to `taughtSolo`, which is mapped into a separate `fullSong` clock. | Shared song model needs named clock domains and explicit relative/absolute transforms. |
| Sections and phrases | Both group events under stable IDs. | RAG uses `sectionId` and `measureId`; Howdy uses `phraseId`, phrase event lists, and bar/beat fields. | Make sections, measures, and phrases separate optional structures rather than aliases. |
| Chords | Both have timed chord identity and can attach validated E9 positions. | RAG embeds `chord` in every comp event; Howdy references a separate `chordTimeline` through `chordEventId`. | Prefer a distinct chord-event stream referenced by steel events; provide an adapter for Stage 1 embedded chords. |
| Tablature note | Both identify string, fret, controls, and a playing gesture. | RAG names the fields `changes` and `articulation`; Howdy names them `controls` and `technique`, with optional path/destination fields in reviewed data. | Choose canonical `controls` plus a structured articulation/transition object; retain aliases only in adapters. |
| Fretboard state | Both are ten-string E9, use frets 0–24, and carry fixed grips rather than deriving them in the browser. | RAG positions include resolved pitch, validation, intervals, completeness, and alternatives. Howdy uses event tab notes directly for current/next display and requires fixed chord grips only for labeled chords. | Canonical engine output should use RAG's resolved/validated position depth while accepting Howdy event references and product presentation metadata. |
| Copedent | Both identify strings high-to-low and named controls. | RAG references a versioned profile ID/revision and resolves control effects centrally. Howdy embeds a compact copedent snapshot whose control entries identify affected strings. | M1 defines profile identity/revision plus a canonical snapshot/digest. Howdy expansion requires an explicit profile match and diagnostics for its omitted revision/deltas. |
| Validation state | Both reject invalid string/fret/control combinations. | RAG uses position validation evidence; Howdy adds human `musicalVerified`, chord verification, approvals, and release review. | Mechanical validity belongs to the platform; human/partner approval belongs to Companion metadata. |
| Looping | Both seek to exact millisecond boundaries. | RAG loops bar ranges in the transport; Howdy exposes phrase/taught-solo behaviors and a full-song layer. | Canonical playback state should accept named loop ranges independent of bar, phrase, or product layer. |
| Privacy and source text | Both can operate without sending audio, lyrics, or private text to the deterministic planner. | Howdy has additional partner approval, media-rights, and sourced coaching constraints. | Keep source rights, verbatim excerpts, tester identity, and partner approvals outside the shared musical core. |

## Decisions Supported by Evidence

The following choices are now sufficiently supported for a future contract
proposal:

1. Use a typed timed-event envelope rather than adopting either existing event
   object wholesale.
2. Keep chord events distinct from steel-note/tab events.
3. Make clock domain explicit whenever an authored passage is a window inside a
   longer recording.
4. Use nullable current/next state with explicit pre-roll, active, and post-roll
   phases.
5. Standardize tablature controls separately from articulation/transition.
6. Keep platform mechanical validation separate from product approval state.

## Decisions Still Open

M0 does not yet establish:

- the canonical event/version names;
- whether canonical time stores milliseconds only or also musical ticks;
- broader copedent controls beyond the approved A/B shared core;
- the transition vocabulary for slides, pedal glides, sustains, repicks, and
  releases;
- how melody/harmony voices attach to the timed-event envelope;
- persistence and migration rules for existing Song Practice projects or
  private Companion review artifacts.

Those decisions require a bounded M1/M2 proposal and adapter plan. No existing
payload should be renamed or migrated before that review.
