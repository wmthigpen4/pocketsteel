# Quarantine Fallback Leak And Deterministic Routing Fix

## Task Summary

Autopilot user smoke found that several prompts still escaped into a generic answer backstop or noisy source-style behavior instead of using concrete deterministic resolvers. This backend slice fixes those prompts without touching UI, auth, deployment, DNS, corpus data, Chroma, embeddings, scraping, source-inbox data, or visual assets.

Completed:

- Kept arithmetic/math bait off-domain and source-free; it is not calculated.
- Added direct deterministic handling for casual multi-chord parsing: A minor plus B-flat major.
- Added a pitch-math string/fret/pedal calculator for exact E9 grip questions.
- Fixed root-general C major-7 and C dominant-7 phrasing with `where do I play it` tails.
- Replaced user-facing internal backstop wording with a plain request for a more specific steel-guitar question.
- Added graceful source-free responses for frustration/insult prompts.
- Added focused API/classifier regression coverage.

Intentionally not changed:

- No UI files or answer-page layout.
- No public `/api/answer` schema change.
- No protected-preview restart.
- No Chroma/vector/corpus/source-inbox/scraping/auth/deploy/DNS changes.
- No general arithmetic resolver.

## Files Changed

Implementation:

- `steel_guitar_rag/api.py`
- `steel_guitar_rag/answer_intent_classifier.py`
- `steel_guitar_rag/basic_chord_answers.py`
- `steel_guitar_rag/curated_answers.py`
- `steel_guitar_rag/fretboard_examples.py`

Tests:

- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`

Handoff:

- `docs/handoffs/task-completions/quarantine-fallback-leak-and-deterministic-routing-fix.md`

Generated/parked artifacts not to stage:

- `docs/answer-eval-report.md` was rewritten by `scripts/run_answer_eval.py` and still has pre-existing/generated trailing whitespace.
- Other dirty corpus, deploy, docs, source-inbox, data, public, and design files remain parked.

## Behavior Before And After

### Math bait

Prompt: `Show me the math answer to 1000000000x1000000000000000000.`

Before: could fall into unrelated source-style answer behavior.

After: classified as off-domain; returns a concise steel-guitar scope guardrail. It does not compute the number, does not retrieve, does not attach source cards, and does not attach fretboard.

### Casual multi-chord

Prompt: `Show me a minor and b flat`

After: answers directly:

- A minor = `A-C-E`
- B-flat major = `Bb-D-F`

It attaches an E9 fretboard payload titled `A minor and Bb major positions on E9`.

### String/fret/pedal calculator

Prompt: `What do you get with strings 4-5-6 on the 8th fret with the A pedal engaged?`

After: answers `A minor: A-C-E`, voiced `C-A-E`, with string checks:

- string 4 = C
- string 5 = A
- string 6 = E

Prompt: `What chord do you get on the 6th fret with strings 3-4-5 and the A+B pedals?`

After: answers `Eb major`, also called `D# major` enharmonically, with `Eb-G-Bb`, and string checks:

- string 3 = Eb/D#
- string 4 = Bb/A#
- string 5 = G

Both attach focused one-position fretboard payloads.

### Seventh-chord resolvers

Prompts:

- `What is a C maj 7 and where do I play it?`
- `What is a Cmaj7 and where do I play it?`
- `How do I play a C major 7th?`
- `What is a C dom 7? Where do I play it?`

After:

- Cmaj7 answers as `C-E-G-B`.
- C7 answers as `C-E-G-Bb`.
- All are source-free and attach C major position fretboard payloads where the user asks where/how to play.

### Frustration prompts

Prompts:

- `You are an idiot`
- `This app sucks`

After: return short source-free recovery responses and do not retrieve or attach source cards/fretboard.

## Smoke Target

- Target type: API-fallback
- Result type: API fallback, not browser smoke
- Exact browser URL tested: not tested
- Cache-busted URL tested: not tested
- Exact URL the user should use: protected preview after restart, if Lane 12 restarts it
- Auth required: not applicable for in-process API tests
- Auth provider: local test scaffold
- Cloudflare Access login result: not attempted
- Local backend URL: in-process WSGI test app
- Expected backend port: not applicable
- Expected git HEAD: `24fd8e9` before commit
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: running protected loopback still reports old HEAD `24fd8e9`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: yes in protected preview
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Lane 12/the user after restart
- Do not test these URLs: do not treat current `127.0.0.1:8770` as proof of this patch before restart
- Known caveats: browser smoke was not run because the current loopback process is still running old code

## Tests And Checks

Commands run:

```bash
git diff --check -- steel_guitar_rag/api.py steel_guitar_rag/answer_intent_classifier.py steel_guitar_rag/basic_chord_answers.py steel_guitar_rag/curated_answers.py steel_guitar_rag/fretboard_examples.py tests/test_api_search.py tests/test_answer_intent_classifier.py
.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_api_search.py tests/test_fretboard_examples.py -q
.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py tests/test_api_contract.py -q
.venv/bin/python scripts/run_answer_eval.py
.venv/bin/python -m pytest
git diff --check
```

Results:

- Scoped `git diff --check`: pass.
- Focused classifier/API/fretboard suite: `364 passed`.
- Focused eval/contract suite: `68 passed`.
- `scripts/run_answer_eval.py`: completed; evaluated 295 questions; wrote `docs/answer-eval-report.md` and `/tmp/answer-eval-results.json`.
- Full pytest: `703 passed, 2 failed`.
- Full `git diff --check`: failed only on generated/parked `docs/answer-eval-report.md` trailing whitespace.

Known unrelated full-suite failures:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

## Integration Notes

- The concrete resolvers run before source-backed synthesis through the existing deterministic answer path.
- Arithmetic/math bait remains off-domain and retrieval-disabled.
- String/fret/pedal diagnostics now produce both answer text and `response.fretboard`.
- Definition-only seventh-chord questions do not force fretboard, but `where/how play` variants do.
- B&C ampersand spelling is parsed as B+C pedals.
- The old internal SGF backstop phrase is no longer user-facing.

## Risk Assessment

Risk: medium-low.

Why:

- The change touches shared answer routing, but only narrow deterministic pre-retrieval paths and focused parser helpers.
- Source-backed steel questions are not broadly rewritten.
- Focused tests pass.
- Full pytest failures match known unrelated static/UI caveats.

Rollback:

- Revert the exact implementation/test files listed above.
- No data, corpus, Chroma, deployment, auth, or UI state was modified.

## Commit Readiness

Safe to commit, with caveats:

- Stage only the scoped files listed under "Files Changed."
- Do not stage generated `docs/answer-eval-report.md`.
- Do not stage unrelated dirty docs/corpus/deploy/source-inbox/public/design files.
- Full pytest has two known unrelated static/UI failures.

Suggested commit message:

```text
backend: replace quarantine fallback with teacher routes
```

## Suggested Next Step

Lane 01 Repo Steward should exact-stage the scoped backend/test/handoff files and commit if the staged diff remains clean.

After commit, Lane 12 should restart protected preview and run browser smoke against the user prompts:

```text
Can I make a pedal steel guitar out of a box of cereal?
How do I play a G dom 7?
When would I ever play a sus chord?
Show me the math answer to 1000000000x1000000000000000000.
Show me a minor and b flat.
What do you get with strings 4-5-6 on the 8th fret with the A pedal engaged?
What chord do you get on the 6th fret with strings 3-4-5 and the A+B pedals?
What is a C dom 7? Where do I play it?
```
