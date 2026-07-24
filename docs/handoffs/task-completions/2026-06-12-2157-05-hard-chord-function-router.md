# Hard Chord/Function Router

## Task summary
- Requested: add a pre-retrieval deterministic router so chord-position-shaped questions either produce pitch-math answers plus fretboard payloads, or return deterministic limited support, and never fall through to SGF fragment synthesis.
- Completed: broadened major-position parsing for plural/place phrasing, added key/function parsing for Nashville and Roman numeral questions, added pitch-validated minor-position payload generation, and wired deterministic curated answers for function/minor questions.
- Immediate fixes covered:
  - "Where are some places to play C chords?" now routes to C major positions with fretboard payload.
  - "I am in the key of G. Where can I play a 6m chord?" now maps to E minor and returns deterministic minor positions with fretboard payload.
  - "Show me the vi chord in G" and "Where is Em on E9?" route to the same deterministic E minor path.
- Intentionally not changed: deployment, DNS, Chroma/vector data, embeddings, scraping, auth, frontend rendering, and non-chord retrieval behavior.

## Files changed
- Changed files:
  - `steel_guitar_rag/fretboard_examples.py`
  - `steel_guitar_rag/curated_answers.py`
  - `tests/test_fretboard_examples.py`
  - `tests/test_api_search.py`
- Created files:
  - `docs/handoffs/task-completions/2026-06-12-2157-05-hard-chord-function-router.md`
- Deleted files: none.
- Generated artifacts: none.

## Tests and checks
- Command:
  - `.venv/bin/python -m pytest tests/test_fretboard_examples.py tests/test_api_contract.py tests/test_api_search.py tests/test_api_answer_private_retrieval.py tests/test_answer_eval.py tests/test_full_answer_quality_eval.py`
- Result:
  - `254 passed in 0.66s`
- Command:
  - `.venv/bin/python -m pytest`
- Result:
  - `512 passed in 4.15s`
- Command:
  - `git diff --check`
- Result:
  - passed with no whitespace errors.
- Local curl verification server:
  - `STEEL_RAG_RETRIEVAL_MODE=sgf_only STEEL_RAG_ENABLE_PRIVATE_SOURCES=false STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 .venv/bin/python scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8783 --answer-auth-mode local_dev --auth-provider scaffold`
- Curl verified:
  - `Where are some places to play C chords?`
  - `I am in the key of G. Where can I play a 6m chord?`
- Tests skipped: none.

## Integration notes
- Root cause found:
  - The prior deterministic router caught some exact `play X chord` patterns, but missed plural/place phrasing like "places to play C chords" and did not parse key-relative function requests such as `6m in G`.
  - An early function parser shape could have confused bare `I` in "I am..." and `1-4-5` progression wording, so the implementation guards those cases explicitly.
- Deterministic C major answer after fix:
  - The answer starts with standard E9 C major starter positions: 8th fret open/no pedals, 11th fret A+F, and 15th fret A+B.
  - `sources` is `[]`.
  - `warnings` is `[]`.
  - `fretboard` payload is present.
  - Curl showed 44 C major positions and visible starter IDs `c-open-8`, `c-af-11`, and `c-ab-15`.
- Deterministic G 6m / E minor answer after fix:
  - The answer states `6m in G is E minor (E-G-B)`.
  - Visible deterministic positions:
    - 3rd fret with A pedal, grip 4-5-6.
    - 8th fret with E-lower, grip 4-5-6.
    - 10th fret with B+C, grip 4-5-6.
  - `sources` is `[]`.
  - `warnings` is `[]`.
  - `fretboard` payload is present.
  - Curl showed 20 E minor positions and visible IDs `e-minor-a_pedal_minor-4-5-6-3`, `e-minor-e_lower_minor-4-5-6-8`, and `e-minor-b_c_minor-4-5-6-10`.
- Schema/API contract notes:
  - No response shape changes were introduced.
  - Existing fretboard payload contract is reused.
  - Deterministic chord/function answers continue to suppress SGF sources.
- Assumptions:
  - Minor support should remain pitch-math limited to validated common grips for now, not presented as exhaustive.
  - Unsupported function qualities should use deterministic limited support rather than retrieval fallback.
- Blockers: none found.
- Human decisions needed: none for this implementation.

## Risk assessment
- Low.
- Why:
  - The change is scoped to deterministic parsing and answer/payload construction for chord-position/function questions.
  - It does not touch Chroma, embeddings, scraping, auth, deployment, or frontend rendering.
  - Focused and full test suites passed.
- Rollback notes:
  - Revert the changes in `steel_guitar_rag/fretboard_examples.py`, `steel_guitar_rag/curated_answers.py`, `tests/test_fretboard_examples.py`, and `tests/test_api_search.py` if this router causes unexpected over-routing.

## Commit readiness
Safe to commit

## Suggested next step
- Lane 06 UX/UI Design should do a protected-preview browser smoke for the new C major and E minor/function payloads.
- Suggested task:
  - "Run protected-preview smoke for `Where are some places to play C chords?`, `I am in the key of G. Where can I play a 6m chord?`, `Show me the vi chord in G`, and `Where is Em on E9?`; verify the selector renders deterministic payloads, source cards stay hidden, and no SGF fragment text appears."
