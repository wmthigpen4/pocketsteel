# Howdy Contract Characterization

Status: M0 preparation; no runtime or schema change

## Provenance And Integration Base

The observed Companion source is preserved at:

- ref: `preserve/companion-howy-v9-9a79d45-20260905`
- commit: `9a79d454491b843f74942ce9193f335512e402ad`
- source: `partner_companions/travis_howdy/content/howdy.draft.json`
- source SHA-256: `a5437a788daf312e6a5cb5c7c77e267f6b70aed69aff93961426f424321cfccf`

The selected integration base is `origin/main` at
`4a77e849c9c9ba8e13429d91ae055d06d0de7ce5`, with platform governance from
`2f7a18b9215d1a27db344cb756966d0f1663b9c1` applied first. The 173 unique
Companion commits are evidence, not a merge unit. Future integration must port
one characterized contract or product slice at a time.

Production history is independently preserved at
`preserve/production-2780c6b-20260905`, pointing to
`2780c6bc4f93cb7abaf237440b5801b0f197e3a0`.

## Frozen Observable Semantics

The portable fixture `tests/fixtures/platform_howdy_contract_v1.json` records
only public, deterministic contract evidence. It contains no source media,
transcript text, coaching excerpts, tester identities, release configuration,
or deployment credentials.

The first frozen semantics are:

1. `lesson_companion_v1` is deterministic and forbids model calls at runtime.
2. Events have unique stable IDs, ordered non-overlapping relative timing,
   phrase and chord references, notation pitch, and one or more tablature notes
   unless explicitly represented as a rest.
3. Tablature notes identify string, fret, controls, and technique. The current
   contract uses ten-string E9 bounds: strings 1–10 and frets 0–24.
4. Phrase timing is derived from its first and last event.
5. Chord boundaries cover their referenced events within 50 ms. A labeled
   chord carries a fixed fretboard grip rather than asking the browser to infer
   one.
6. `fullSong` covers the complete media duration. `taughtSolo` maps an absolute
   window to the relative event clock, and the final event ends at that relative
   duration.
7. Playback selection uses inclusive starts and exclusive ends. Current and
   next selection saturate at the final event instead of producing a missing
   selection.
8. The Play-Along layer selects the full-song clock. Other current Howdy layers
   select the taught-solo clock.

These are characterization constraints, not the final shared platform schema.
Contradictions found during M0 must be documented before changing them.

## Consumer Evidence

At the preserved Companion commit, with the declared companion extras present:

- `tests/test_travis_companion.py` and
  `tests/test_travis_tutorials_companion.py`: 42 passed, 1 skipped;
- Companion browser JavaScript syntax: passed;
- Travis Companion Worker TypeScript check: passed;
- Travis Companion Worker tests: 6 passed.

The characterization suite can additionally verify the source snapshot by
setting `HOWDY_COMPANION_SOURCE` to the preserved draft path. Normal CI validates
the sanitized fixture without requiring the legacy application tree.

## Cross-Product Follow-On

The matching RAG snapshot now lives in
`tests/fixtures/platform_rag_contract_v1.json`. The evidence and resulting
agreement/contradiction matrix are recorded in
`docs/platform-contract-comparison.md`.

The next bounded architecture slice may propose the M1/M2 typed event, clock,
copedent, and tablature vocabulary with compatibility adapters. Do not extract
shared runtime code or migrate persisted product payloads in that proposal.
