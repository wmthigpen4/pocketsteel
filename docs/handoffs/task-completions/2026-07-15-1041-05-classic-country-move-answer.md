# Classic-Country Move Answer Upgrade

## Task summary

- Replaced the landing example question's simplistic same-fret A+B toggle with a playable classic-country E9 pickup in G.
- The new phrase uses a sustained fret-1 to fret-3 double-stop slide, an A-pedal E-to-D release against held G, a timed full-G landing, and explicit listening/technique guidance.
- Preserved the existing prompt, intent classification, answer API shape, source-free deterministic route, UI, authentication, and active-setup behavior.

## Lane classification

- Lane 05 Backend / RAG Integration with Lane 15 verification and Lane 01 exact-hunk commit.
- User-smoke answer-quality bug; the request authorizes this scoped answer implementation.

## Files changed

- `steel_guitar_rag/curated_answers.py`
- Exact regression hunk in `tests/test_api_search.py`
- This handoff.

No API schema, retrieval, source, auth, corpus, vector, deployment-policy, or private data changed.

## Tests and checks

- Exact classic-country regression — PASS, 1 test.
- Focused home-prompt checks — PASS, 2 tests.
- `tests/test_api_search.py` — PASS, 331 tests.
- `tests/test_answer_eval.py` — PASS, 10 tests.
- A filtered answer-eval command selected no tests and returned pytest exit 5; the full answer-eval file was then run and passed.
- `git diff --check` — PASS.

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8767/ui/steel-guitar-rag-mock.html?v=classic-country-move-local-20260715`
- Cache-busted URL tested: same
- Exact URL the user should use: protected-preview URL to be recorded after commit
- Auth required: no; controlled beta-member preview selected locally
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8767`
- Expected backend port: 8767
- Expected git HEAD: working tree based on `de737fd4ab1458e2f73ffe83c158f022c7900818`
- Version endpoint: `http://127.0.0.1:8767/api/version`
- Version endpoint result: local working-tree runtime
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not used
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: earlier answer-cleanup and header cache keys
- Known caveats: requested 390×844 viewport is exposed as effective 520×1125

Results:
- The landing example prefilled the exact prompt without searching.
- Explicit submission rendered the revised pickup with exact frets, strings, notes, timing, A-pedal movement, sustain, vibrato, blocking, and space.
- The old A+B toggle wording was absent.
- Desktop and narrow layouts had zero page and answer-workspace horizontal overflow.

## Integration notes

- Standard E9 pitch check: fret 1 with A down gives string 4 F and string 5 D; sliding to fret 3 gives G and E; releasing A lowers string 5 from E to D while G holds.
- This remains a source-free original practice phrase, not a transcription or attributed lick.

## Risk assessment

Low. The change replaces one exact curated answer and strengthens its regression. Rollback is the scoped commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- `steel_guitar_rag/curated_answers.py`
- Exact classic-country regression hunk in `tests/test_api_search.py`
- `docs/handoffs/task-completions/2026-07-15-1041-05-classic-country-move-answer.md`

## Files that must not be staged

- All unrelated dirty and untracked files, including song-practice hunks in `tests/test_api_search.py`.
- `docs/handoffs/task-completions/integration-status.md` must remain unstaged and be refreshed separately.

## Recommended next lane

Lane 01 exact-hunk commit, then Lane 12 authenticated protected-preview smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval with exact-hunk staging, commit, and protected browser verification of the exact landing example prompt.
