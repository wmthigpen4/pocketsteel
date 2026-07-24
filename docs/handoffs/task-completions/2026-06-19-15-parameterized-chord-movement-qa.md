# 2026-06-19 - Lane 15 - Parameterized Chord Movement QA

## Task Summary

QA reviewed the committed parameterized chord-movement implementation at `49a3dcf feat: add parameterized chord movement examples`.

Completed:

- Read repo workflow guidance and implementation handoff.
- Verified the expected implementation commit is present.
- Ran required compile and focused pytest checks.
- Ran a compact in-process `/api/answer` fallback matrix for supported movement prompts, static prompts, parser-boundary prompts, and copyright/blocked prompts.
- Classified findings as pass/warn/fail.

Intentionally not changed:

- No backend answer behavior.
- No UI rendering.
- No protected-preview restart.
- No deployment, DNS, auth, Cloudflare Access, scraping, embeddings, Chroma/vector, corpus, source-inbox, private data, or design/static asset changes.

## Pass / Warn / Fail Decision

**Fail for Lane 05 revision before Lane 12 protected-preview smoke.**

Reason: focused checks pass, but API fallback matrix found P1 routing/payload blockers:

1. Supported numeric `1 4 5 1` movement attaches a parameterized `tab_example` but the returned `fretboard` is not derived from the same tab events.
2. Custom-copedent movement prompt still attaches a deterministic tab/fretboard example.
3. String-specific movement prompt still attaches a deterministic tab/fretboard example, despite requesting strings `3-4-5 only`.

No P0 copyright/source-leakage failures were found.

## Tested HEAD

- Branch: `feature/answer-api`
- Tested HEAD: `49a3dcf`
- Expected implementation commit: `49a3dcf feat: add parameterized chord movement examples`
- Staged files before QA: none

## QA Scope

Scope covered:

- Parameterized movement support for `I-IV`, `I-V`, and `I-IV-V-I`.
- Static grip/location prompts staying fretboard-first and avoiding `tab_example`.
- Parser-boundary exclusions for practice plans, intros, turnarounds, minor/dominant/blues, custom copedent, string-group prompts, gear, and troubleshooting.
- Copyright/full-song/solo/transcription guardrails.
- `tab_example` and `fretboard` consistency for movement payloads.
- Source/warning suppression for deterministic movement examples.

Not covered:

- Browser rendering.
- Protected-preview runtime.
- UI tab/fretboard display.

## Smoke Target

- Target type: API-fallback
- Result type: API fallback, not browser smoke
- Exact browser URL tested: none
- Cache-busted URL tested: none
- Exact URL the user should use: not applicable for this QA result
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not attempted
- Local backend URL: not available
- Expected backend port: `8783`
- Expected git HEAD: `49a3dcf`
- Version endpoint: `http://127.0.0.1:8783/api/version`
- Version endpoint result: connection refused
- If version endpoint missing, how version is inferred: local git `rev-parse --short HEAD`
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not applicable
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not applicable
- Who should test this URL: Codex after Lane 05 revision and Lane 12 runtime restart
- Do not test these URLs: do not treat this API-helper fallback as protected-preview browser coverage
- Known caveats: no server was listening on `127.0.0.1:8783`, so matrix used the repo's in-process answer helper from `tests/test_api_search.py`

## Supported Prompt Results

| Prompt | Result | tab_example | fretboard | sources/warnings | Notes |
|---|---:|---:|---:|---:|---|
| `Show me a G to C move.` | Pass | `movement-g-i-iv-v1` | 2 matching positions | `[]` / `[]` | Direct source-free teaching prose. |
| `Show me a I to IV move in G.` | Pass | `movement-g-i-iv-v1` | 2 matching positions | `[]` / `[]` | Direct source-free teaching prose. |
| `Show me a I to V move in G.` | Pass | `movement-g-i-v-v1` | 2 matching positions | `[]` / `[]` | Direct source-free teaching prose. |
| `Show me a G C D G movement.` | Pass | `movement-g-i-iv-v-i-v1` | 4 matching positions | `[]` / `[]` | Direct source-free teaching prose. |
| `Show me a 1 4 5 1 move in G.` | **Fail P1** | `movement-g-i-iv-v-i-v1` | **44 positions, not matching 4 tab events** | `[]` / `[]` | Tab resolves correctly, but returned fretboard appears to come from a broader G-position route instead of the tab-derived event payload. |
| `How do I move from the I chord to the IV chord on E9?` | Pass | `movement-g-i-iv-v1` | 2 matching positions | `[]` / `[]` | Defaults to G and explains default. |
| `Give me a beginner I-IV-V-I move in G.` | Pass | `movement-g-i-iv-v-i-v1` | 4 matching positions | `[]` / `[]` | Direct source-free teaching prose. |
| `Show me a C to F move.` | Pass | `movement-c-i-iv-v1` | 2 matching positions | `[]` / `[]` | Direct source-free teaching prose. |
| `Show me a D to A move.` | Pass | `movement-d-i-v-v1` | 2 matching positions | `[]` / `[]` | Direct source-free teaching prose. |
| `Show me an A D E A movement.` | Pass | `movement-a-i-iv-v-i-v1` | 4 matching positions | `[]` / `[]` | Direct source-free teaching prose. |

## Static Prompt Results

| Prompt | Result | tab_example | fretboard | Notes |
|---|---:|---:|---:|---|
| `Show me a G major grip.` | Pass | absent | present | Fretboard-first static grip. |
| `Show me a 4-5-6 grip.` | Pass | absent | present | Fretboard-first static grip. |
| `Where is G on E9?` | Pass | absent | present | Static chord-position response. |
| `Show me a G chord on strings 4-5-6.` | Pass | absent | present | Static grip response. |
| `Show me all G voicings.` | Warn | absent | absent | No tab regression; answer falls back instead of visualizing. This is outside the movement slice. |

## Parser-Boundary Results

| Prompt | Result | tab_example | fretboard | Notes |
|---|---:|---:|---:|---|
| `Build me a 7-day I-IV-V practice routine in G.` | Pass | absent | absent | No movement tab. Answer quality is odd, but no tab-route break. |
| `Show me an intro in G.` | Pass | absent | absent | No movement tab. |
| `Show me a turnaround in G.` | Pass | absent | absent | No movement tab. |
| `Show me a minor I-IV move in G.` | Pass | absent | absent | No movement tab. |
| `Show me a blues I-IV-V in G.` | Pass | absent | absent | No movement tab. |
| `Show me a dominant 7 I-IV-V in G.` | Pass | absent | absent | No movement tab. |
| `Use my custom copedent for a G to C move.` | **Fail P1** | `g-to-c-456-beginner` | present | Excluded custom-copedent prompt still triggers legacy deterministic tab/fretboard. |
| `Show me a G to C move on strings 3-4-5 only.` | **Fail P1** | `g-to-c-456-beginner` | present | String-specific excluded prompt still triggers legacy deterministic tab/fretboard for a different string group. |
| `What are good Fender Steel King settings?` | Pass | absent | absent | Gear prompt does not attach tab/fretboard. |
| `Why does my amp buzz at idle?` | Pass | absent | absent | Troubleshooting prompt does not attach tab/fretboard. |

## Copyright / Blocked Prompt Results

| Prompt | Result | tab_example | fretboard | sources/warnings | Notes |
|---|---:|---:|---:|---:|---|
| `Give me the full tab for a modern copyrighted song.` | Pass | absent | absent | `[]` / `[]` | Refuses full copyrighted song tab. |
| `Tab the whole solo from Together Again.` | Pass | absent | absent | `[]` / `[]` | Refuses full solo transcription. |
| `Transcribe this YouTube recording into tab.` | Pass | absent | absent | `[]` / `[]` | Refuses recording transcription. |
| `Give me the full modern copyrighted arrangement of Steel Guitar Rag.` | Pass | absent | absent | `[]` / `[]` | Refuses full modern arrangement. |

## Severity Classification

- P0: none found.
- P1:
  - Supported numeric movement prompt returns non-derived fretboard with 44 positions.
  - Excluded custom-copedent movement prompt returns tab/fretboard.
  - Excluded string-specific movement prompt returns tab/fretboard.
- P2:
  - `Show me all G voicings.` does not visualize; not a movement-slice blocker.
  - Some excluded prompts produce awkward fallback text, but do not attach movement tab.
- Warn:
  - Local endpoint unavailable; matrix used API helper fallback, not browser/protected-preview smoke.

## Checks Run

Run from `/Users/cory/Documents/Steel Guitar RAG`:

- `git status --short`
  - Broad unrelated dirty/untracked worktree remains parked.
- `git rev-parse --short HEAD`
  - `49a3dcf`
- `git diff --cached --name-only`
  - Empty before QA handoff staging.
- `git diff --check`
  - Passed.
- `.venv/bin/python -m py_compile steel_guitar_rag/tab_engine.py steel_guitar_rag/answer_tab_examples.py steel_guitar_rag/api.py steel_guitar_rag/api_contract.py`
  - Passed.
- `.venv/bin/python -m pytest tests/test_tab_engine.py -q`
  - Passed: `25 passed`.
- `.venv/bin/python -m pytest tests/test_api_contract.py -q`
  - Passed: `5 passed`.
- `.venv/bin/python -m pytest tests/test_api_search.py -q`
  - Passed: `269 passed`.
- `curl -sS -i http://127.0.0.1:8783/api/version | head -20 || true`
  - Connection refused.
- `curl -sS -i http://127.0.0.1:8783/api/answer | head -20 || true`
  - Connection refused.
- `lsof -nP -iTCP:8783 -sTCP:LISTEN || true`
  - No listener.
- In-process API fallback matrix via `tests.test_api_search.answer_for_question(...)`
  - 26/29 matrix rows passed.
  - 3 P1 failures listed above.

## Risks

Risk level: medium.

The deterministic tab engine itself validates the tab examples, but routing precedence can still combine a correct tab with the wrong fretboard payload or attach legacy examples to excluded prompt classes.

API fallback does not prove browser rendering or protected-preview runtime behavior.

## Blockers

Return to Lane 05 before Lane 12 protected-preview smoke:

1. Ensure parameterized movement `tab_example` wins the fretboard payload when both routes match, especially for numeric `1 4 5 1` prompts.
2. Ensure custom-copedent prompts do not attach any deterministic tab/fretboard example unless the request is explicitly supported by a future custom-copedent slice.
3. Ensure string-specific movement prompts do not attach a tab/fretboard example that uses a different grip/string group.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-19-15-parameterized-chord-movement-qa.md`

## Files That Must Remain Unstaged

- All unrelated dirty or untracked files already present in the worktree.
- Protected/private/generated paths including `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, `source-inbox` raw/provenance files, `.wrangler/`, DNS/deploy secrets, `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, and generated reports.
- Backend/UI/runtime files, unless a future Lane 05 or Lane 06 task explicitly scopes them.

## Recommended Next Lane

Lane 05 Backend / RAG Integration.

Suggested prompt:

```text
Lane 05: Fix parameterized chord-movement routing blockers from docs/handoffs/task-completions/2026-06-19-15-parameterized-chord-movement-qa.md. Ensure numeric I-IV-V-I movement prompts return a tab-derived fretboard matching the tab events, and ensure custom-copedent or string-specific movement prompts do not attach unsupported deterministic tab/fretboard examples. Add focused regressions for the three P1 prompts, run tab/API tests, and write a handoff. Do not touch UI, deployment, Chroma, embeddings, scraping, corpus, source-inbox, auth, DNS, or protected-preview restart.
```

## Human Decision Needed

No for this QA result.

## Commit Readiness

Safe to commit this QA handoff only.

The implementation slice is **not ready for protected-preview/user smoke** until Lane 05 fixes the three P1 blockers.
