# Shared Component Map

Status: current implementation audit

Baseline: `origin/main` at `4a77e849c9c9ba8e13429d91ae055d06d0de7ce5`

Companion comparison: local `feature/chord-reader-ssl-v9` at `9a79d454`

This map identifies actual sources before extraction. A file listed here is
not approved to move, rename, or become a public contract.

Implementation note: the governed platform branch now adds isolated
`packages.steel_theory` and `packages.song_model` foundations for M1a–M2a.
They do not replace any product consumer listed below; this map continues to
describe the audited product sources and migration surface.

## Current Shape

The main branch has no `apps/`, `packages/`, or product-neutral `services/`
layout. Shared domain behavior is mixed into the `steel_guitar_rag` package
and browser globals under `ui/`. The fullest observed Companion branch adds
`partner_companions/`, but it is local-only and diverged from `main`.

## Capability Map

| Capability | Current Python/data sources | Current browser/product sources | Coupling and duplication |
|---|---|---|---|
| Steel theory and copedent | `user_copedent.py`, `e9_copedents.py`, `copedent_transfer.py`, `music_text.py`, `steel_rules.py` | `ui/pedal-steel-fretboard.js`, `ui/e9-fretboard-explorer.js`, `ui/melody-workbench.js`, `ui/practice-tools.js` | Open tuning, pitch classes, control deltas, note spelling, and chord parsing are repeated across Python and JavaScript. `tab_engine.py` also defines a separate copedent profile. |
| Fretboard contract/engine | `fretboard_contracts.py`, `fretboard_examples.py`, `fretboard_explorer.py`, `copedent_transfer.py` | `ui/pedal-steel-fretboard.js`, its styles module, Explorer config/loader/app, and versioned Explorer data | Backend produces several dict-shaped payloads; browser behavior is exposed through globals. `fretboard_examples.py` and `fretboard_explorer.py` combine contracts, parsing, theory, teaching copy, and catalog generation. |
| Tablature | `tab_engine.py`, `answer_tab_examples.py`, `melody_models.py`, `melody_arranger.py`, `amazing_tablature_*` | tab/card rendering in `ui/answer-client.js`, `ui/melody-workbench.js`, and `ui/play-song.js` | `TabNote`/`TabEvent` are the strongest typed seed, but Melody and Song Practice transform them into separate payloads. Browser renderers implement their own tokens and selection behavior. |
| Song model | `melody_models.py`, `melody_import.py`, `song_practice.py`, `song_catalog_pipeline.py`, public-domain and practice-track resources | `ui/melody-score.js`, `ui/melody-workbench.js`, `ui/song-projects.js`, `ui/songs.js`, `ui/setup-song.js` | `score_draft_v1`, `song_practice_request_v1`, `song_practice_plan_v1`, catalogs, track manifests, and local browser project/session records overlap without one canonical aggregate. |
| Play-Along and synchronization | `song_practice.py`, `melody_arranger.py`, practice-track manifests | `ui/play-song.js`, `ui/practice-transport.js`, `ui/practice-tools.js`, `ui/practice-reference-validation.js`, analysis client/worker | Clock/seek/loop behavior is separated into a small transport module, while event selection, current/next state, fretboard, tab, and chord presentation remain coupled in large page controllers. |
| RAG product | `api.py`, `answering.py`, answer contracts/routing, retrieval, Chroma/frontier clients, source registries | `ui/steel-guitar-rag-mock.html`, `ui/answer-client.js` | RAG correctly owns retrieval and source behavior, but it currently imports domain helpers from the same flat package. |
| Companion product | Not on `origin/main`. Local branch adds `partner_companions/travis_howdy`, `travis_practice_guide`, and `travis_tutorials` | Companion-local CSS, JavaScript, templates, and static preview packaging | Companion intentionally avoids importing the RAG app, but reimplements event validation, fretboard drawing, tab tokens/table, chord/song timelines, and playback selection in `travis_howdy/release.py` and `site/companion.js`. |

## Strong Contract Seeds

These are the best current inputs to a canonical contract; they are not yet
the contract by themselves:

- `TabNote` and `TabEvent` in `steel_guitar_rag/tab_engine.py`.
- `MelodyInput` and `PositionCandidate` in
  `steel_guitar_rag/melody_models.py`.
- `E9CopedentProfile` and profile identity/digest behavior in
  `steel_guitar_rag/e9_copedents.py`.
- fretboard payload rules in `docs/fretboard-payload-contract.md` and
  `steel_guitar_rag/fretboard_contracts.py`.
- `score_draft_v1` behavior in `docs/melody-exercise-v0.md`.
- Song Practice schemas and canonical timeline hashing in
  `steel_guitar_rag/song_practice.py`.
- `lesson_companion_v1` and exact reviewed-event requirements in the local
  Companion branch's `partner_companions/travis_howdy` sources.

## Highest-Risk Coupling

1. `melody_arranger.py` is more than 3,000 lines and imports fretboard,
   copedent, tab, ranking, and training-policy modules. Moving it first would
   pull multiple domains at once.
2. `fretboard_examples.py` and `fretboard_explorer.py` mix input parsing,
   musical truth, payload creation, validation, and teaching language.
3. `ui/melody-workbench.js` repeats E9 tuning and control deltas rather than
   consuming one generated contract.
4. RAG Play-Along and Howdy each render a fretboard, tab, timeline, and
   current/next state through separate page controllers.
5. The Companion release validator is valuable independent evidence, but its
   schema cannot simply replace RAG song/tab payloads without a field-by-field
   compatibility table.

## Consumer Matrix Required For Extraction

| Shared slice | RAG consumers | Companion consumers | Required characterization |
|---|---|---|---|
| Steel theory/copedent | Chat fretboard answers, Explorer, Melody Studio, Song Practice | Howdy events/chords, Companion validation and display | pitch/control/profile fixtures in both languages |
| Song model | Melody import/studio, catalogs, Song Practice API/UI | Howdy full-song/taught-solo scopes, phrase and chord timelines | schema fixtures, timeline hashes, section/loop behavior |
| Fretboard | Chat cards, Explorer, Melody Studio, Play-Along | Howdy current/next and alternate positions | payload snapshots plus interaction tests |
| Tablature | Chat tab, Melody Studio, Play-Along, print | Howdy tab, printable handout | token/event fixtures and rendering snapshots |
| Play-Along | Song Practice API and browser | Howdy audio/clock/loop/guide state | deterministic clock/seek/current-next tests and browser smoke |

## Ownership Decisions Already Supported By Evidence

- Retrieval, citations, SGF corpus, and source cards remain `PRODUCT:RAG`.
- Travis content, approvals, partner branding, related lessons, and teaching
  presentation remain `PRODUCT:COMPANION`.
- Pitch math, copedent changes, steel events, fretboard state, tab semantics,
  song timelines, and playback synchronization are `PLATFORM:SHARED`.
- Cloudflare projects, Access, tunnels, launch services, ports, CI, and exact
  release activation are `INFRASTRUCTURE`.

The next Companion/Howdy slice may change partner presentation or authored
content within the preserved Companion branch without changing shared domain
truth. Any change to its event, fretboard, tab, chord timeline, or playback
semantics must begin as a shared-contract characterization slice.
