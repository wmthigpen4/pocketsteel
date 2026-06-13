# Default E9 Chord-Position Routing Fix

## Task Summary

Requested: fix the user-smoke blocker where `How do you play a C chord?` fell through to retrieval/forum-style evidence instead of deterministic E9 chord-position help.

Completed: broadened the deterministic major-chord position parser and answer-intent classifier so app-context `how do you play` prompts route the same way as `how do I play` prompts. The fix keeps pure theory prompts such as `What is a C chord?` theory-only and fretboard-free.

Intentionally not changed: UI, `/api/answer` schema, auth, deployment, corpus, Chroma/vector data, scraping, source data, and visual assets.

## Files Changed

- `pocketsteel/fretboard_examples.py`
  - Extended major-chord location parsing to accept `How do you play ...` phrasing, including across-fretboard phrasing.
- `pocketsteel/answer_intent_classifier.py`
  - Extended position language detection to accept `How do you play/make ...`.
  - Added `where do ...` to explicit visual-position language so classifier output matches deterministic answer routing.
- `tests/test_fretboard_examples.py`
  - Added coverage that `How do you play a C chord?` returns the C major E9 fretboard payload.
- `tests/test_answer_intent_classifier.py`
  - Added classifier coverage for default E9 chord-position prompts.
- `tests/test_api_search.py`
  - Added API regression coverage for C/G/A/D default chord-position prompts.
  - Reconfirmed `What is a C chord?` remains source-free, warning-free, and fretboard-free theory text.

## Smoke Target

- Target type: local browser smoke; protected-preview verification still required after commit
- Exact browser URL: `http://127.0.0.1:8877/ui/steel-guitar-rag-mock.html?access=beta_user&v=default-e9-chord-routing-local`
- Cache-busted URL: `https://app.steelguitarrag.com/?v=default-e9-chord-routing-<commit>`
- Auth required: local no; protected preview yes
- Auth provider: local scaffold; protected preview Cloudflare Access
- Local backend URL: `http://127.0.0.1:8877`
- Expected backend port: `8877` for local smoke; `8770` remains the standard local protected-preview/backend expectation
- Expected git HEAD: current worktree, then the new commit after Repo Steward commit
- Version endpoint result: not used for local smoke
- Root URL status: local root redirects to `/ui/steel-guitar-rag-mock.html`; protected-preview root still needs Lane 12 verification
- API fallback status: not used as the acceptance proof; local browser smoke was run
- Exact URL the user should test: `https://app.steelguitarrag.com/?v=default-e9-chord-routing-<commit>` after Cloudflare Access login, once Lane 12 verifies the protected runtime

## Smoke Result

Local browser smoke passed for `How do you play a C chord?`.

Observed:

- Answer rendered as deterministic C major E9 starter positions.
- Fretboard rendered.
- No raw forum/SGF fragments appeared in the primary answer.
- No weak-source primary warning appeared.
- No `[object Object]` appeared.
- The UI displayed a `No sources returned` source-note card, not retrieval evidence.

Protected-preview browser smoke was not run because this code was not yet committed/restarted into the protected runtime.

## Tests And Checks

- `git diff --check` - passed.
- Behavior probe for `How do you play a C chord?`, `How do I play a C chord?`, `Where do I play a C chord?`, `Show me C chord positions.`, `What is a C chord?`, and `What is the capital of France?` - passed.
- `.venv/bin/python -m pytest tests/test_fretboard_examples.py tests/test_answer_intent_classifier.py tests/test_api_search.py -q` - `323 passed`.
- `.venv/bin/python -m pytest tests/test_api_contract.py tests/test_answer_eval.py tests/test_full_answer_quality_eval.py -q` - `54 passed`.
- `.venv/bin/python -m pytest -q` - `640 passed, 2 failed`.

Known unrelated full-suite failures:

- `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
- `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`

## Integration Notes

No API response schema changed.

The answer-intent contract now marks default app-context chord-position prompts such as `How do you play a C chord?` as:

- `domain: steel_guitar`
- `intent: copedent_position`
- `needs_fretboard: true`
- `retrieval_allowed: false`

Pure theory wording still stays separate: `What is a C chord?` remains a source-free, warning-free theory answer with no required fretboard payload.

## Risk Assessment

Risk: low to medium. The code change is a small parser/classifier expansion, but the touched files contain unrelated parked dirty hunks from other backend work. Repo Steward must stage exact hunks only.

Rollback: revert the eventual scoped commit if this routing causes unexpected over-classification.

## Commit Readiness

Safe to commit with exact-hunk staging only.

Do not stage unrelated dirty hunks in:

- `pocketsteel/fretboard_examples.py`
- `pocketsteel/answer_intent_classifier.py`
- `tests/test_fretboard_examples.py`
- `tests/test_answer_intent_classifier.py`
- `tests/test_api_search.py`

## Suggested Next Step

Lane 12 should verify the protected-preview runtime after the commit:

```text
LANE: 12 Self-Hosted Deployment
REASONING: MEDIUM
Branch: feature/answer-api

Restart or verify protected-preview runtime from the default E9 chord-position routing commit or later.

Smoke Target:
- Target type: protected-preview root
- Exact browser URL: https://app.steelguitarrag.com/
- Cache-busted URL: https://app.steelguitarrag.com/?v=default-e9-chord-routing-<commit>
- Auth required: yes
- Auth provider: Cloudflare Access
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: default E9 chord-position routing commit or later
- Version endpoint result: record `/api/version` if available
- Root URL status: record observed behavior; root is expected to serve the app shell but must be verified
- API fallback status: not acceptable for this bug
- Exact URL the user should test: https://app.steelguitarrag.com/?v=default-e9-chord-routing-<commit> after Cloudflare Access login

Verify `How do you play a C chord?` returns deterministic C major E9 positions with a fretboard, no raw forum fragments, no unrelated source cards, no weak-source primary warning, and no object-string rendering.
```
