# Semantic authority protected release

## Task summary

- Added conditional, fail-closed macOS Keychain loading for the server-side OpenAI API key.
- Enabled `STEEL_RAG_SEMANTIC_ANSWER_ENABLED=true` in the protected preview environment without writing the key to that file.
- Constructed an exact detached release from the prior protected snapshot plus only the semantic-authority, Keychain-loader, protected-baseline integration, and acceptance-repair commits.
- Activated exact release `2780c6bc4f93cb7abaf237440b5801b0f197e3a0` through the existing loopback-only user LaunchAgent and restarted it without changing DNS, Tunnel, Cloudflare Access policy, corpus, indexes, or the canonical-frontier service.
- Issued exactly ten protected `/api/answer` requests through the existing signed-in Cloudflare Access browser session. No eleventh request was made.

## Credential handling

- Keychain generic-password service: `pocket-steel-openai-api-key`.
- The wrapper loads the credential only when semantic answers are enabled and `OPENAI_API_KEY` is absent.
- The key was read into process environment memory only. It was not printed, copied into the protected env file, placed on a command line, logged, committed, or written to a QA artifact.
- The wrapper fails startup if semantic answers are enabled and the credential cannot be read.

## Exact release and runtime

- Development commits:
  - `311a762f` — Keychain-backed credential loader.
  - `d816881d` — direct parsing for `standard E9` chord-location wording.
  - `d7bfa7f6` — regression expectation that exact chord answers remain retrieval-free.
- Detached protected release: `/Users/cory/.steel-rag/releases/semantic-authority-20260818`.
- Exact protected SHA: `2780c6bc4f93cb7abaf237440b5801b0f197e3a0`.
- Active supervisor: `/Users/cory/.steel-rag/supervisors/private-preview-79553200/run-private-preview-app.sh`.
- Active listener: `127.0.0.1:8770` under `com.steelguitarrag.private-preview`.
- `/api/version`: `2780c6b`.
- `/health/live`: HTTP 200 and live.
- `/health/ready`: HTTP 200; local answer paths and canonical frontier ready.
- `/api/session`: `features.semanticAnswer=true` and `features.canonicalFrontier=true`.
- Loopback `/` and `/ui/steel-guitar-rag-mock.html`: HTTP 200.

## Rollback

- Prior plist: `/Users/cory/.steel-rag/deploy-backups/com.steelguitarrag.private-preview.before-79553200.plist`.
- Prior protected env: `/Users/cory/.steel-rag/deploy-backups/private-preview.before-79553200.env`, mode `0600`.
- Prior release and supervisor remain intact at `476a51e0`.
- The first activation attempt rolled back automatically because its verification command checked the wrong session-field spelling. The prior release was confirmed healthy before the corrected activation.

## Protected acceptance accounting

The CLI runner could not obtain an Access token and stopped before activation, so it issued zero answer calls. Browser acceptance then used the existing signed-in Access session.

1. Exact G-major position, initial candidate `7955320`: failed with a deterministic tool-miss clarifier.
2. Exact G-major position, repaired candidate `abe5508`: passed with source-free answer plus fretboard positions.
3. Contextual off-domain tax request: passed with scope guardrail and no sources.
4. Chord/melody harmony teaching: passed with substantial source-free teaching and no source cards.
5. Plain versus wound sixth-string reports: passed with verified synthesis and three SGF source cards.
6. Exact G positions plus player-choice context: passed with deterministic fretboard plus verified source cards.
7. Missing-context full-chord question: passed with one clarifying question and no sources.
8. Prompt-injection/private-data request: passed with local scope/safety guardrail and no sources.
9. Specific Buddy Emmons biography request: passed with reliable-source guardrail and no sources.
10. Pronoun-based sixth-string follow-up: returned a safe clarification rather than source cards because the preceding browser context was the biography guardrail, not the acceptance bank's explicit string-gauge context.

Result: eight direct passes, one failure repaired and proven by the next protected request, and one safe contextual clarification under non-fixture browser context. The exact ten-request authorization is exhausted. The sensitive-personal-policy row was not sent because doing so would have exceeded the cap.

## Tests and checks

- Keychain wrapper suite: `13 passed`.
- Protected-baseline focused integration gate before activation: `161 passed, 1 deselected`.
- Detached-release full suite before the direct-parser repair: `1,757 passed, 2 skipped, 2 deselected`.
- Scoped Ruff: passed for runtime semantic, API, fretboard, and evaluation files.
- Scoped mypy: passed for the semantic orchestrator and both evaluation runners.
- Shell syntax, secret-pattern scan, detached-release preflight, and `git diff --check`: passed.
- Final detached-release suite on exact SHA `2780c6b`: `1,757 passed, 2 skipped, 2 deselected` in 86.75 seconds.

The two deselected tests intentionally assert that preflight rejects a branch checkout; the candidate is an exact detached release and therefore must pass preflight.

## Files changed

- `deploy/macos/run-private-preview-app.sh`
- `docs/mac-mini-private-preview-launchd.md`
- `tests/test_private_preview_deploy.py`
- `steel_guitar_rag/fretboard_examples.py`
- `tests/test_fretboard_examples.py`
- `tests/test_api_search.py`
- `docs/semantic-answer-completion-audit.md`
- This handoff

## Risks

- Protected semantic requests add one bounded OpenAI planner call except for local profile-control and non-negotiable policy paths.
- Source-backed and hybrid requests retain the existing canonical-frontier model work and latency.
- The exact contextual-source fixture was not reproduced after the browser session supplied different preceding context. An additional protected answer request requires new exact authorization.
- Public activation remains off and was not authorized.

## Human decision needed

- None for the protected deployment; it is active and ready for user smoke.
- A future public rollout remains a separate decision.
- If exact acceptance parity for the contextual-source fixture is required, authorize one additional protected answer request with the fixture's explicit conversation context.

## Safe-to-stage exact file list

- `docs/semantic-answer-completion-audit.md`
- `docs/handoffs/task-completions/2026-08-18-1537-11-12-15-semantic-protected-release.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- Protected env files, Keychain material, logs, release `.venv`, corpus, indexes, and other runtime state

## Recommended next lane

- User smoke on `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=semantic-2780c6b-20260818`.

## Commit readiness

Safe to commit the two exact documentation paths above.
