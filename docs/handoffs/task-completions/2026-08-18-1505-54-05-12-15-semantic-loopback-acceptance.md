# Semantic enabled-path loopback acceptance handoff

## Task summary

- Continued the semantic search rollout after the live planner bank passed.
- Audited the running preview read-only: it remains healthy at commit `476a51e`; canonical frontier is active, semantic answers are not active, and no release for `6eefc072` exists.
- Started an isolated loopback app at `127.0.0.1:8870` from commit `6eefc072` with both semantic and canonical authorities enabled. The existing OpenAI Keychain credential was injected only into child-process memory. No launchd, Cloudflare, protected environment, account-usage, corpus, index, or deployment state changed.
- The first ten-case acceptance run passed 8/10 and exposed one shared integration boundary: free-form planner tool language did not reach the strict deterministic chord-position parser.
- Added a bounded deterministic argument fallback for planner-style chord-position language, including hyphenated chord qualities, without broadening routing authority or replacing exact pitch tools.
- Added repeatable `--case-id` selection to the preview runner so exact failed cases can be retested under matching request authorization.
- The repaired exact and hybrid cases passed 2/2 live; together with the unchanged 8/8, all ten enabled-path cases now have loopback passing evidence.
- The isolated app was stopped cleanly after smoke.

## Files changed

- `steel_guitar_rag/fretboard_examples.py`
- `scripts/run_semantic_answer_preview_smoke.py`
- `tests/test_semantic_answer_orchestrator.py`
- `tests/test_semantic_answer_preview_smoke.py`
- `docs/semantic-answer-orchestrator.md`
- `docs/semantic-answer-completion-audit.md`
- `docs/handoffs/task-completions/2026-08-18-1505-54-05-12-15-semantic-loopback-acceptance.md`

Deleted files: none.

## Evidence

- Loopback `/api/version`: `6eefc072`.
- Loopback `/api/session`: `semanticAnswer=true`, `canonicalFrontier=true`.
- Initial matrix: activation pass; 8 passed, 2 failed.
- Failures: exact deterministic omitted its fretboard; hybrid returned sources but omitted the deterministic answer/fretboard.
- Repaired subset: exact deterministic pass; hybrid pass; activation pass.
- Hybrid repair evidence: deterministic answer plus fretboard plus verified source cards.
- Focused semantic/preview/fretboard suite: 115 passed after regression narrowing.
- Full repository suite: 1,792 passed in 87.22 seconds.
- Ruff on changed Python files: pass.
- Scoped mypy on semantic orchestrator and preview runner: pass.
- Generated reports remain uncommitted beneath `output/`.

## Risks

- The deterministic fallback is intentionally limited to planner-style `identify`, `locate`, `map`, `playable ... positions`, or `exact ... positions` language. Full-suite regressions prove it does not preempt existing movement lessons or static grip rendering.
- Protected preview still runs the older release and does not have the semantic feature flag configured.
- The protected app wrapper currently receives no `OPENAI_API_KEY`. The release should use the existing macOS Keychain credential without copying or printing it; adding that protected secret-loading path and changing the environment are RED actions.

## Human decision needed

Yes. Explicitly authorize the protected-release phase, including:

1. adding a Keychain-backed, non-printing OpenAI credential load to the preview wrapper;
2. adding `STEEL_RAG_SEMANTIC_ANSWER_ENABLED=true` to the protected environment;
3. building and activating the exact committed release and restarting preview;
4. making exactly ten protected `/api/answer` requests through the existing Access/Tunnel route.

No DNS, Access policy, Tunnel, corpus, index, or canonical-frontier service change is required.

## Safe-to-stage exact file list

- `steel_guitar_rag/fretboard_examples.py`
- `scripts/run_semantic_answer_preview_smoke.py`
- `tests/test_semantic_answer_orchestrator.py`
- `tests/test_semantic_answer_preview_smoke.py`
- `docs/semantic-answer-orchestrator.md`
- `docs/semantic-answer-completion-audit.md`
- `docs/handoffs/task-completions/2026-08-18-1505-54-05-12-15-semantic-loopback-acceptance.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`.
- The unrelated untracked handoffs dated 2026-08-04, 2026-08-12, and 2026-08-13.
- `output/`, credentials, environment files, logs, corpora, indexes, embeddings, and deployment artifacts.

## Recommended next lane

- Lane 11/12 after explicit RED authorization: implement the protected Keychain load, exact-path commit it, activate the exact release, and run the ten-case protected smoke.

## Commit readiness

The exact local integration-repair slice is ready to commit. Protected activation remains separately gated.
