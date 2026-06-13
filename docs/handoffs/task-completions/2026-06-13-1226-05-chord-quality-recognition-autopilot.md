# Chord Quality Recognition Autopilot

## Task summary

- Requested: fix the user-smoke bug where `sus` was treated as an invalid chord root, and cover the same class of standard chord-quality aliases for suspended, dominant, diminished, and augmented language.
- Completed: added deterministic rootless chord-quality normalization and teacher-first concept answers before invalid-symbol guardrails. Rooted unsupported qualities now explain chord tones and ask for tuning/copedent context instead of using SGF fragments or invented E9 positions.
- Intentionally not changed: backend `/api/answer` schema, UI files, deployment, DNS, auth policy, corpus data, Chroma/vector stores, embeddings, source-inbox data, scraping, and visual assets.

## Files changed

- `pocketsteel/fretboard_examples.py`
  - Added `RootlessChordQualityRequest`.
  - Added rootless chord-quality alias normalization for `sus`, `sus2`, `sus4`, `suspended`, `dominant`, `dom`, `dom7`, `dominant 7`, `7th`, `V7`, `5 dominant 7`, `5 dom 7`, `5^7`, `dim`, `diminished`, `dim7`, `aug`, `augmented`, and `+ chord`.
  - Added teacher-first chord-quality definition answers.
  - Prevented rootless quality aliases from entering invalid chord-symbol guardrails.
  - Extended rooted unsupported-quality parsing for compact symbols such as `Gsus4`, `Dsus2`, `Gdim`, and `Gaug`.
- `pocketsteel/curated_answers.py`
  - Routed rootless chord-quality answers before invalid chord-symbol guardrails.
  - Included chord-tone definitions in unsupported rooted-quality answers.
- `tests/test_fretboard_examples.py`
  - Added parser and direct-answer tests for rootless quality aliases and guardrail bypass.
- `tests/test_api_search.py`
  - Added API regressions for rootless quality prompts and rooted unsupported quality prompts.
  - Updated the `5^7` expectation from ambiguous notation to V7 concept handling.
- `docs/handoffs/task-completions/2026-06-13-1226-05-chord-quality-recognition-autopilot.md`
  - This handoff.

## Tests and checks

- `.venv/bin/python -m pytest tests/test_fretboard_examples.py tests/test_api_search.py`
  - `243 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py tests/test_answer_eval.py tests/test_full_answer_quality_eval.py`
  - `54 passed`
- `.venv/bin/python -m pytest`
  - `677 passed`
- `git diff --check`
  - Passed

## Smoke Target

- Target type: `API-fallback`
- Exact browser URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`
- Cache-busted URL: protected-preview browser smoke deferred to Lane 12
- Auth required: local API fallback no browser auth; local `/api/answer` required dev role header
- Auth provider: local scaffold; protected preview Cloudflare Access
- Local backend URL: `http://127.0.0.1:8793`
- Expected backend port: `8793`
- Expected git HEAD: `f6d8ad2` plus this uncommitted scoped patch during local smoke
- Version endpoint result: `{"git_sha":"f6d8ad2","git_branch":"feature/answer-api","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"scaffold"}`
- Root URL status: not used as proof
- API fallback status: API fallback only, not browser smoke
- Exact URL Cory should test: protected-preview UI path after Lane 12 restart/verification for the committed hash

## Smoke result

- Local API fallback smoke passed: `23 prompts / 23 pass / 0 fail`.
- Covered rootless qualities: sus, dominant, dom7, 5 dom 7, 5^7, diminished, dim, dim7, augmented, aug, `+ chord`.
- Covered rooted quality prompts: `G7`, `D7`, `Gdim`, `Gaug`, `Gsus4`, `Dsus2`.
- Reconfirmed existing major prompts: `G`, `A`, and `D` chord prompts still return fretboard payloads.
- Reconfirmed off-domain guardrail: `What is the capital of France?` stays source-free and fretboard-free.

## Integration notes

- Rootless quality questions now explain the concept and ask for a root/key before E9 mapping.
- Rootless quality questions return no fretboard, no source cards, and no warnings.
- Rooted unsupported qualities stay deterministic and source-free, with chord-tone definitions and no hallucinated position payload.
- `5^7` is now intentionally treated as V7/scale-degree dominant language rather than generic ambiguous notation.
- Existing dirty `pocketsteel/api.py` `/api/version` work was not touched or staged by this slice.

## Risk assessment

- Risk: low to medium.
- Why: the change is deterministic and test-covered, but it broadens routing for theory/chord-quality language before retrieval.
- Rollback notes: revert the chord-quality helper/routing changes and the corresponding tests if quality routing causes unexpected false positives.

## Commit readiness

- Safe to commit.
- Commit hash: recorded in the final Repo Steward closeout after this handoff was committed.
- Commit message: `backend: recognize common chord qualities`

## Suggested next step

Lane 12 protected-preview verification after the commit:

```text
LANE: 12 Self-Hosted Deployment
REASONING: MEDIUM
Branch: feature/answer-api

Restart or verify the protected-preview runtime after the chord-quality recognition commit.

Smoke Target:
- Target type: protected-preview
- Exact browser URL: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html
- Cache-busted URL: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=chord-quality-recognition-<commit>
- Auth required: yes
- Auth provider: Cloudflare Access
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: chord-quality recognition commit or later
- Version endpoint result: record if available
- Root URL status: record observed behavior; do not use root as a substitute for the UI path
- API fallback status: browser smoke required for protected preview
- Exact URL Cory should test: same cache-busted protected-preview URL after Cloudflare Access login

Verify:
- `How do I play a sus chord?` explains suspended quality and asks for a root/key.
- `What is 5^7?` explains V7/scale-degree dominant and asks for key.
- `How do I play Gsus4 on E9?` explains chord tones without raw forum fragments or invented fretboard positions.
- `How do I play a G chord on the E9?` still returns deterministic fretboard behavior.
- Off-domain guardrails remain source-free and fretboard-free.
```
