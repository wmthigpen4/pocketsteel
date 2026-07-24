# Natural-Language Chord Intent User Smoke Fix

## Task Summary

Autopilot user smoke found that casual chord-position questions still fell through to SGF/forum fragments instead of deterministic E9 chord answers and fretboard payloads. This Lane 05 backend slice added broader natural-language chord intent normalization for major and minor chord-position requests.

Completed:
- Normalized filler/noise words such as `uh`, `um`, `just`, `can you`, `in the hell`, `heck`, and `freaking` before deterministic chord parsing.
- Normalized worded accidentals such as `D sharp` and `D-sharp` through the existing sharp/flat normalizer.
- Broadened major/minor chord-position patterns for `find`, `where are`, `look like`, `positions for`, `give me`, and fretboard/E9 context phrases.
- Added direct learner-friendly major triad tone text to major-position answers.
- Added specific D#/Eb learner-friendly wording for D# major and D# minor requests.
- Preserved source-free deterministic fretboard behavior for chord-position answers.

Intentionally not changed:
- No UI files.
- No deployment, DNS, auth, corpus, Chroma, embeddings, scraping, private source data, or visual assets.
- No broad answer architecture or schema changes.
- No protected-preview restart.

## Lane Classification

Lane 05 Backend / RAG Integration: backend answer routing, deterministic fretboard parsing, and regression tests.

## Files Changed

- `steel_guitar_rag/fretboard_examples.py`
  - Added `normalize_chord_intent_text(...)` and `chord_context_pattern()`.
  - Routed major/minor/multi/unsupported/fretboard parsing through the normalized text path.
  - Expanded major/minor chord-position regex coverage.
  - Updated minor-position answer prefix wording.
- `steel_guitar_rag/curated_answers.py`
  - Added learner-facing major triad spellings.
  - Added D#/Eb major explanation and major chord-tone sentence for major position answers.
- `tests/test_api_search.py`
  - Added API-level natural-language major/minor chord intent regressions.
  - Updated minor-position wording expectations.
- `tests/test_fretboard_examples.py`
  - Added direct parser/payload regressions for natural-language chord intent variants.
- `docs/handoffs/task-completions/natural-language-chord-intent-user-smoke-fix.md`
  - This handoff.

Generated artifacts: none.
Deleted files: none.

## Behavior Before / After

### `Where can I find D# chords on the pedal steel E9?`

Before: fell through to SGF fragments about unrelated topics.

After: first sentence is `D# is usually easier to think of as Eb on E9. Eb major is Eb-G-Bb.` Response includes `D# major positions on E9`, `sources: []`, `warnings: []`, and a fretboard payload.

### `How do I play a D-sharp minor on E9?`

Before: fell through to SGF fragments.

After: first sentence is `D# minor is D#-F#-A#. You can also think of it as Eb minor: Eb-Gb-Bb.` Response includes `D# minor positions on E9`, `sources: []`, `warnings: []`, and a fretboard payload.

### `How do I play uh A minor on E9?`

Before: filler word confused the route and allowed SGF fragments.

After: first sentence is `A minor is A-C-E: root, minor 3rd, and perfect 5th.` Response includes `A minor positions on E9`, `sources: []`, `warnings: []`, and a fretboard payload.

### `What's a B minor look like?`

Before: fell through to unrelated B6/Bm6/diminished fragments.

After: first sentence is `B minor is B-D-F#: root, minor 3rd, and perfect 5th.` Response includes `B minor positions on E9`, `sources: []`, `warnings: []`, and a fretboard payload.

### `How in the hell do you play a C major chord?`

Before: returned unhelpful C scale / G7-style fragments and no fretboard.

After: first sentence is `C major is C-E-G: root, major 3rd, and perfect 5th.` Response includes `C major positions on E9`, `sources: []`, `warnings: []`, and a fretboard payload.

## Smoke Target

- Target type: API-fallback
- Result type: API fallback, not browser smoke
- Exact browser URL tested: not tested
- Cache-busted URL tested: not tested
- Exact URL the user should use: protected preview still requires Lane 12 restart/verification from this commit or later before user smoke resumes
- Auth required: no for local fake-source API fallback; protected preview auth not attempted
- Auth provider: local scaffold for API fallback; Cloudflare Access not attempted
- Cloudflare Access login result: not attempted
- Local backend URL: `http://127.0.0.1:8783` temporary in-process WSGI server with fake SGF sources
- Expected backend port: `8783` for API fallback; protected preview remains expected on `8770`
- Expected git HEAD: `36ab10e` before commit; post-commit HEAD to be recorded by Repo Steward/autopilot closeout
- Version endpoint: not used for API fallback
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: local working tree and test process
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: yes in protected preview after Lane 12 verification
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes in protected preview after Lane 12 verification
- Who should test this URL: Lane 12 should verify protected preview after commit; the user should not resume smoke until Lane 12 verifies
- Do not test these URLs: do not treat local API fallback as protected-preview browser smoke
- Known caveats: protected-preview browser smoke was not run in this lane; no Chroma-backed server was started because this slice was validated with fake SGF sources and the task prohibited Chroma changes

## API Fallback Smoke Result

Temporary local WSGI API fallback with fake SGF sources passed these prompts:

| Prompt | Result | Direct answer first | Fretboard | Sources | Warnings |
| --- | --- | --- | --- | --- | --- |
| `Where can I find D# chords on the pedal steel E9?` | pass | D#/Eb explanation | yes | 0 | [] |
| `How do I play a D-sharp minor on E9?` | pass | D# minor / Eb minor explanation | yes | 0 | [] |
| `How do I play uh A minor on E9?` | pass | A minor tone spelling | yes | 0 | [] |
| `What's a B minor look like?` | pass | B minor tone spelling | yes | 0 | [] |
| `How in the hell do you play a C major chord?` | pass | C major tone spelling | yes | 0 | [] |
| `How do I play a G dom 7?` | pass | G7 tone spelling | yes | 0 | [] |
| `How do I play an F maj 7?` | pass | Fmaj7 tone spelling | yes | 0 | [] |
| `Show me an E minor chord` | pass | E minor tone spelling | yes | 0 | [] |
| `Show me an E major and E minor` | pass | combined major/minor answer | yes | 0 | [] |
| `What is the capital of France?` | pass | scope guardrail | no | 0 | [] |

## Tests And Checks

Commands run:

- `git status --short`
  - Result: broad parked dirty/untracked files remain outside this slice; no pre-existing dirty `steel_guitar_rag/*.py` or `tests` runtime files at task start.
- `.venv/bin/python -m pytest tests/test_api_search.py -k "natural_language or minor_show_requests or rooted_dominant or major_seventh_play or multi_target or smoke_ready_chord"`
  - Result: `7 passed, 213 deselected`.
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py tests/test_api_contract.py tests/test_api_search.py tests/test_answer_eval.py tests/test_full_answer_quality_eval.py tests/test_answer_intent_classifier.py`
  - Result: `389 passed`.
- `.venv/bin/python -m pytest`
  - Result: `652 passed, 2 failed`.
  - Failures are the already-documented unrelated static/UI failures:
    - `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
    - `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`
- `git diff --check`
  - Result: passed.
- Temporary local fake-source API fallback on `127.0.0.1:8783`
  - Result: passed smoke prompts above.

Skipped:
- Protected-preview browser smoke: skipped because this backend lane does not restart/deploy protected preview. Lane 12 must restart/verify after commit.

## Integration Notes

- Deterministic chord-position answers remain source-free with `sources: []` and no weak-source warnings.
- Fretboard payload shape is unchanged.
- Source cards and retrieval behavior for non-deterministic steel questions were not changed.
- The new normalizer is intentionally local to chord-intent parsing and does not alter UI rendering.

## Risk Assessment

Risk: low to medium.

Why:
- The change touches shared chord-position parsing, so broad routing impact is possible.
- Focused API, fretboard, contract, answer eval, full answer quality eval, and classifier tests passed.
- Full pytest failures are known unrelated static/UI issues documented in integration status.

Rollback notes:
- Revert the scoped changes in `steel_guitar_rag/fretboard_examples.py`, `steel_guitar_rag/curated_answers.py`, and the two test files to restore prior literal parser behavior.

## Commit Readiness

Safe to commit for the scoped backend/test/handoff files.

Safe-to-stage list:
- `steel_guitar_rag/fretboard_examples.py`
- `steel_guitar_rag/curated_answers.py`
- `tests/test_api_search.py`
- `tests/test_fretboard_examples.py`
- `docs/handoffs/task-completions/natural-language-chord-intent-user-smoke-fix.md`

Must remain unstaged:
- `README.md`
- `corpus_metadata/**`
- `deploy/**`
- `docs/source-inbox-inventory.md`
- `docs/handoffs/task-completions/integration-status.md` unless a separate Repo Steward refresh is explicitly scoped
- `rag_*.py`
- `source-inbox/**`
- `corpus-private/**`
- `corpus-v2/**`
- `public/**`
- `ui/brand/**`
- `Neon Sign/**`
- private lesson scripts/data and any generated/private/corpus/vector/deploy artifacts

## Suggested Next Step

Lane 12 Self-Hosted Deployment / protected-preview verification should restart or verify protected preview from the new commit and run the protected root smoke target.

Exact next prompt:

```text
Lane 12: Restart/verify protected preview from the latest committed HEAD after the natural-language chord intent fix. Use https://app.steelguitarrag.com/?v=natural-language-chord-intent-<HEAD>, confirm /api/version, Cloudflare Access auth, and browser-smoke the ten prompts from docs/handoffs/task-completions/natural-language-chord-intent-user-smoke-fix.md. Do not change DNS, deploy new code outside the documented loopback restart, or touch Chroma/embeddings/corpus/scraping. Write a protected-preview handoff with the exact URL tested and whether user smoke may resume.
```
