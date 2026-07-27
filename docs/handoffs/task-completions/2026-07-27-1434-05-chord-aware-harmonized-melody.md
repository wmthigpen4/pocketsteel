# Lane 05/06/12 — Chord-Aware Harmonized Melody

## Task summary

Implemented the approved deterministic chord-aware harmonized melody arranger.
The scientific-pitch melody remains the highest sounding voice, while the
engine builds playable two-voice harmony beneath it using an explicit chord
timeline.

Completed:

- added the `chord_aware_harmony` route family;
- preserved chord provenance as `source`, `user`, `confirmed`, or `suggested`;
- restricted the Chord-aware claim to authoritative source/user chords;
- added key-only thirds and sixths labels when no chord track exists;
- added a visible editable chord lane aligned to score events;
- added chord-aware event metadata, explanations, fallbacks, playback/tab/
  fretboard synchronization, and Best Fit selection;
- expanded MusicXML chord support through major, minor, 7th, 6th, diminished,
  augmented, suspended, and slash-chord symbols;
- froze the founder's ten-note G/C/D example at the exact requested pitches,
  strings, frets, pedals, and F lever positions;
- kept supervised learning out of the chord-aware critical path.

Intentionally not changed:

- OMR recognition behavior;
- auth, Cloudflare Access, DNS, Tunnel routing, secrets, corpus, embeddings,
  private source data, or provider configuration;
- the user's existing dirty coordination and historical handoff files.

Implementation commit:
`736d4cff0c05241245c29a17985065496f7c2156`
(`feat: add chord-aware harmonized melody routes`).

## Verification fixture

The frozen route resolves exactly as:

`G/B → G/B → A/C → B/D → E/C → F#/D → F#/D → G/E → A/F# → D/A`

with grips:

`4+6@3 open, 4+6@3 open, 4+6@4 F, 4+6@6 F, 5+6@3 A+B,
5+6@5 A+B, 5+6@5 A+B, 4+5@3 A, 5+6@10 open, 6+8@5 B`.

Every event preserves the submitted scientific octave as the highest sounding
pitch.

## Files changed

- `steel_guitar_rag/melody_models.py`
- `steel_guitar_rag/melody_arranger.py`
- `steel_guitar_rag/melody_import.py`
- `steel_guitar_rag/amazing_tablature_runtime.py`
- `steel_guitar_rag/amazing_tablature_product.py`
- `ui/melody-score.js`
- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `deploy/landing/melody-score.js`
- `tests/test_chord_aware_harmony.py`
- `tests/test_melody_assistant.py`
- `tests/test_melody_import.py`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`

No files were deleted.

## Tests and checks

- Frozen chord-aware fixture and chord vocabulary:
  `16 passed`.
- Focused import/UI/static-server suite:
  `53 passed`.
- Focused product/runtime/arranger/copedent/API suite:
  `425 passed`.
- Ruff on all changed Python and test files: passed.
- Frontend JavaScript syntax checks: passed.
- `git diff --check` and cached diff check: passed.
- Complete repository suite after the final fixture:
  `1536 passed in 71.29s`.
- Immediate consecutive complete repository suite:
  `1536 passed in 71.47s`.
- Direct mypy invocation was not a green gate: it reported existing type debt
  across imported fretboard, OMR, ranker, and runtime modules. No mypy-only
  changes were made; the repository's full pytest and Ruff gates are green.

## Local browser smoke

Smoke Target:

- Target type: local
- Result type: browser smoke
- Exact browser URL tested:
  `http://127.0.0.1:8791/ui/melody-workbench.html?access=beta_user&v=chord-aware-harmony-local`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending protected activation
- Auth required: no
- Auth provider: local development scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8791`
- Expected backend port: `8791`
- Expected git HEAD:
  `736d4cff0c05241245c29a17985065496f7c2156`
- Version endpoint: not used by the disposable local stub
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: working-tree source
  and cache-busted asset names
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: the disposable port was stopped after smoke
- Known caveats: local smoke does not prove protected activation

Browser result:

- Melody Studio loaded with zero warnings or errors;
- the Staff editor exposed the visible Chord timeline;
- its empty state explicitly advertised key-only thirds and sixths;
- entering G on the selected score event immediately produced a visible
  `G · measure 1 · beat 1 · user` chord change.

## Protected activation status

The immutable release was prepared and passed detached-release preflight:

- release: `~/.steel-rag/releases/736d4cff-chord-aware`
- SHA: `736d4cff0c05241245c29a17985065496f7c2156`

Activation reached the macOS administrator-password prompt and was stopped
without replacing the running service. Current production remains healthy on
release `7e52032`:

- `/health/live`: live
- `/health/ready`: ready
- `/api/version`: `git_sha=7e52032`
- port 8770 listener: running under the existing supervised process

Run this from the repository and enter the Mac administrator password:

```bash
STEEL_RAG_REPO_DIR="$HOME/.steel-rag/releases/736d4cff-chord-aware" \
STEEL_RAG_DATA_DIR="$HOME/Documents/Steel Guitar RAG" \
STEEL_RAG_EXPECTED_GIT_SHA=736d4cff0c05241245c29a17985065496f7c2156 \
deploy/macos/install-private-preview-launchdaemon.sh activate
```

Protected browser smoke must follow successful activation. Until then, the
production URL does not prove this feature.

## Integration notes

The new route contract adds:

- route `harmonyType=chord_aware_harmony`;
- route/tab `harmonyBasis=chord_track`;
- per-event `activeChord`, `chordBasis`, `supportingPitchValues`,
  `supportingPitches`, `harmonyInterval`, and `harmonyFunction`;
- a single-note `textureFallback` explanation when no legal supporting voice
  exists.

Chord changes carry forward until the next change. Suggested/derived chords
remain editable but do not enable the Chord-aware label.

## Risk assessment

Medium-low for the committed implementation: deterministic outputs, exact
mechanical validation, focused coverage, two consecutive full-suite passes,
and local browser smoke are green. Production remains on the previous healthy
release until administrator-authorized activation and protected browser smoke.

Rollback after activation remains the prior immutable `7e520323-import-music`
release.

## Human decision needed

Yes. An administrator must run the exact activation command above and enter
the Mac password. No product or musical decision is pending.

## Safe-to-stage exact file list

- `docs/handoffs/task-completions/2026-07-27-1434-05-chord-aware-harmonized-melody.md`

The implementation files are already committed in `736d4cff`.

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-07-23-1603-20-canonical-validation-review-ready.md`
- all unrelated historical untracked handoffs
- `corpus-private/**`
- credentials, environment files, logs, uploaded scores, vector stores,
  embeddings, and detached-release state

## Recommended next lane

Lane 12 protected activation and browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Run the exact administrator activation command, then ask Codex to complete
protected smoke at the cache-busted production Melody Studio URL.
