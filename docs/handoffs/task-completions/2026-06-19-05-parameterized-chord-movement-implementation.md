# 2026-06-19 - Lane 05 - Parameterized Chord Movement Implementation

## Task Summary

Implemented the first backend slice from the committed Lane 18 parameterized chord-movement contract.

Completed:

- Added deterministic standard 10-string E9 movement generation for major-key:
  - `I-IV`
  - `I-V`
  - `I-IV-V-I`
- Added natural-language parsing for supported movement prompts such as:
  - `Show me a G to C move.`
  - `Show me a I to IV move in G.`
  - `Show me a I to V move in G.`
  - `Show me a G C D G movement.`
  - `Show me a 1 4 5 1 move in G.`
  - `How do I move from the I chord to the IV chord on E9?`
  - `Give me a beginner I-IV-V-I move in G.`
- Generated examples as original deterministic educational exercises with `tab_example` plus matching derived `fretboard`.
- Kept static grip/chord-location prompts fretboard-first with no visible `tab_example`.
- Suppressed source cards/warnings for generated parameterized movement examples so SGF/source cards do not imply support for exact generated tab.

Intentionally not changed:

- No UI rendering files.
- No `/api/answer` schema change.
- No SGF retrieval, Chroma/vector, embeddings, scraping, corpus, source-inbox, auth, DNS, deployment, private transcripts, or visual/design assets.
- No song tab, public-domain arrangement, named-artist solo, melody-to-tab, recording transcription, or custom-copedent generation.

## Files Touched

- `pocketsteel/answer_tab_examples.py`
  - Added parameterized movement parsing/generation.
  - Generated structured tab events and rendered/validated them through `pocketsteel.tab_engine.render_tab`.
  - Added deterministic provenance metadata:
    - `rightsStatus: original_educational_example`
    - `provenanceType: deterministic_exercise`
    - `sourcePolicy: no_external_song_source`
    - `generator: parameterized_e9_chord_movement_v1`
- `pocketsteel/api.py`
  - For `parameterized_chord_movement` tab payloads, clears `sources` and `warnings`.
  - Always uses the generated movement answer body for parameterized movement examples so the answer prose matches the tab/fretboard payload.
- `tests/test_tab_engine.py`
  - Added direct resolver coverage for supported major-key progressions, default-key behavior, metadata, and unsupported requests.
- `tests/test_api_search.py`
  - Added `/api/answer` coverage for `I-IV`, `I-V`, `I-IV-V-I`, default-key numeral movement, and unsupported progression requests.
- `docs/handoffs/task-completions/2026-06-19-05-parameterized-chord-movement-implementation.md`
  - This handoff.

## Supported Movement Scope

Supported:

- Standard 10-string E9.
- Major-key roots including sharps/flats parsed by pitch class.
- `I-IV`:
  - I: open/no-pedals 4-5-6 at the key fret.
  - IV: same-fret A+B partial on strings 5-6.
- `I-V`:
  - I: open/no-pedals 4-5-6 at the key fret.
  - V: nearby A+B major grip on strings 3-4-5.
- `I-IV-V-I`:
  - I open/no-pedals.
  - IV same-fret A+B partial.
  - V nearby A+B.
  - I return.

Representative generated G examples:

- `movement-g-i-iv-v1`
  - G fret 3 no pedals, strings 4-5-6.
  - C partial fret 3 A+B, strings 5-6.
- `movement-g-i-v-v1`
  - G fret 3 no pedals, strings 4-5-6.
  - D fret 5 A+B, strings 3-4-5.
- `movement-g-i-iv-v-i-v1`
  - G fret 3 no pedals.
  - C partial fret 3 A+B.
  - D fret 5 A+B.
  - G fret 3 no pedals.

## Unsupported / Out Of Scope

No generated movement tab is attached for:

- Full copyrighted song tab.
- Full solo transcription.
- Recording/YouTube transcription.
- Named-song or named-artist solo reconstruction.
- Minor progressions.
- Dominant/seventh/blues progressions.
- Intro/turnaround prompts currently covered by existing teacher-first answer routes.
- Practice routines/workouts/plans.
- Static string/grip diagnostics.
- Static chord-position/grip prompts.
- Custom-copedent requests.

## Tests And Checks Run

Run from `/Users/cory/Documents/Pocket Steel`:

- `git status --short`
  - Broad unrelated dirty/untracked worktree remains parked.
- `git rev-parse --short HEAD`
  - Starting HEAD: `8dab461`.
- `git diff --cached --name-only`
  - Empty before staging.
- `.venv/bin/python -m py_compile pocketsteel/answer_tab_examples.py`
  - Passed during implementation.
- `.venv/bin/python -m py_compile pocketsteel/tab_engine.py pocketsteel/answer_tab_examples.py pocketsteel/api.py pocketsteel/api_contract.py`
  - Passed.
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q`
  - Passed: `25 passed`.
- `.venv/bin/python -m pytest tests/test_api_search.py -k 'tab_example or static_g or movement or full_solo or copyrighted_song' -q`
  - Passed: `18 passed, 251 deselected`.
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
  - Passed: `5 passed`.
- `.venv/bin/python -m pytest tests/test_api_search.py -q`
  - Passed: `269 passed`.
- `git diff --check`
  - Passed.

Skipped:

- Frontend/browser smoke: no frontend files touched.
- Deployment/protected-preview restart: outside Lane 05 scope.
- Full pytest: not required by the user prompt; the required focused backend/API suites passed.

## Risks

Risk level: medium-low.

Reasons:

- The parser is intentionally narrow but still introduces new natural-language matching around chord movement.
- To avoid regressions, the resolver explicitly excludes static grips, string diagnostics, routines/plans, turnarounds/intros, minor/dominant/blues progressions, custom copedent requests, and blocked song/transcription requests.
- Generated examples are deterministic, mechanically validated, and source-free.

Rollback:

- Revert changes in `pocketsteel/answer_tab_examples.py`, the small `pocketsteel/api.py` source/warning clearing branch, and the associated tests.

## Blockers

None for this slice.

## Safe-To-Stage Exact File List

- `pocketsteel/answer_tab_examples.py`
- `pocketsteel/api.py`
- `tests/test_tab_engine.py`
- `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-06-19-05-parameterized-chord-movement-implementation.md`

## Files That Must Remain Unstaged

- Existing unrelated dirty or untracked worktree files, including:
  - `README.md`
  - `corpus_metadata/source_policies/README.md`
  - `corpus_metadata/source_registry.json`
  - `docs/answer-eval-report.md`
  - `docs/cloudflare-pages-landing.md`
  - `docs/copyright-provenance.md`
  - `docs/corpus-license-policy.md`
  - `docs/current-commands.md`
  - `docs/handoffs/task-completions/integration-status.md`
  - `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
  - `docs/source-inbox-inventory.md`
  - root RAG scripts
  - `source-inbox/inventory.json`
  - `source-inbox/provenance.json`
  - `ui/brand/*`
  - `public/brand/*`
  - `Neon Sign/`
  - corpus-private, Chroma/vector stores, embeddings, deployment/auth/DNS files, scraping outputs, private transcripts, secrets, generated reports, and design assets.

## Recommended Next Lane

Lane 15 focused QA, then Lane 12 protected-preview smoke after QA or direct runtime deployment decision.

Suggested Lane 15 prompt:

`Lane 15: Run focused QA for parameterized E9 chord-movement examples at the current backend commit. Verify supported I-IV, I-V, and I-IV-V-I prompts return deterministic source-free tab_example plus matching fretboard, static grip prompts remain fretboard-first with no tab_example, unsupported song/transcription/custom/minor/dominant prompts stay blocked or answer-only, and no UI files changed.`

## Human Decision Needed

No.

## Commit Readiness

Safe to commit.
