# QA Browser Smoke Target Template Update

## Task summary

- Requested: update QA/browser-smoke planning docs so smoke reports tell the user exactly where to test and clearly separate browser smoke from API fallback.
- Completed: tightened the existing browser-smoke target template and added the same required target block to answer-eval expected behaviors.
- Intentionally not changed: implementation files, UI files, Chroma/vector stores, corpus data, deployment config, generated reports, and historical smoke handoffs.

## Files changed

- Changed files:
  - `AGENTS.md`
  - `docs/process/codex-completion-protocol.md`
  - `docs/llm-guidance/eval-rubric.md`
  - `tests/answer_eval/expected_behaviors.md`
- Created files:
  - `docs/handoffs/task-completions/qa-browser-smoke-target-template-update.md`
- Deleted files: none.
- Generated artifacts: none.

## New required fields

Every browser smoke report, protected-preview smoke report, production smoke report, or API fallback used because browser tooling could not run must include:

```text
Smoke Target:
- Target type: local | protected-preview | production-root | API-fallback
- Result type: browser smoke | API fallback, not browser smoke
- Exact browser URL tested:
- Cache-busted URL tested:
- Exact URL the user should use:
- Auth required: yes/no
- Auth provider: Cloudflare Access / none / other
- Cloudflare Access login result: succeeded / failed / not required / not attempted
- Local backend URL:
- Expected backend port:
- Expected git HEAD:
- Version endpoint:
- Version endpoint result:
- If version endpoint missing, how version is inferred:
- Whether app root `/` works:
- Whether app root `/` is expected to work:
- Whether `/ui/steel-guitar-rag-mock.html` works:
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work:
- Who should test this URL: Codex / the user / both
- Do not test these URLs:
- Known caveats:
```

Validity rules:

- Browser smoke pass/fail is invalid unless the exact URL tested is recorded.
- API fallback smoke must be labeled `API fallback, not browser smoke`.
- Protected-preview smoke must state whether Cloudflare Access login succeeded.
- If root `/` is not expected to work or is not the canonical target, the report must say so.

## Examples

Protected-preview browser smoke:

```text
Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=verify-77ff8f6-chord-fretboard-routing
- Cache-busted URL tested: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=verify-77ff8f6-chord-fretboard-routing
- Exact URL the user should use: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=verify-77ff8f6-chord-fretboard-routing after Cloudflare Access login
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 77ff8f6 or later containing `backend: route chord position prompts to fretboard`
- Version endpoint: /api/version
- Version endpoint result: unavailable; no version endpoint exposed
- If version endpoint missing, how version is inferred: protected-preview process logs plus behavior for routing smoke prompts
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not canonical for this smoke; do not rely on root unless Lane 12 verifies root routing
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both
- Do not test these URLs: bare `https://app.steelguitarrag.com` without confirming root is intended; local `127.0.0.1` as proof of protected-preview behavior
- Known caveats: protected preview must serve HEAD `77ff8f6` or later; API fallback is not browser smoke
```

Local browser smoke:

```text
Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: http://127.0.0.1:8783/ui/steel-guitar-rag-mock.html?v=local-smoke
- Cache-busted URL tested: http://127.0.0.1:8783/ui/steel-guitar-rag-mock.html?v=local-smoke
- Exact URL the user should use: http://127.0.0.1:8783/ui/steel-guitar-rag-mock.html?v=local-smoke
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: http://127.0.0.1:8783
- Expected backend port: 8783
- Expected git HEAD: current worktree HEAD recorded in the handoff
- Version endpoint: /api/version
- Version endpoint result: record response if available
- If version endpoint missing, how version is inferred: `git rev-parse --short HEAD` plus restarted local process evidence
- Whether app root `/` works: record observed result
- Whether app root `/` is expected to work: state yes/no for the local smoke command used
- Whether `/ui/steel-guitar-rag-mock.html` works: record observed result
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: protected preview unless this task explicitly asks for it
- Known caveats: local evidence does not prove protected-preview cache, auth, or routing behavior
```

API fallback:

```text
Smoke Target:
- Target type: API-fallback
- Result type: API fallback, not browser smoke
- Exact browser URL tested: none
- Cache-busted URL tested: none
- Exact URL the user should use: https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=verify-77ff8f6-chord-fretboard-routing after Cloudflare Access login
- Auth required: yes for protected-preview browser smoke
- Auth provider: Cloudflare Access
- Cloudflare Access login result: not attempted
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: 77ff8f6 or later containing `backend: route chord position prompts to fretboard`
- Version endpoint: /api/version
- Version endpoint result: record response if available
- If version endpoint missing, how version is inferred: local process evidence only; not protected-preview proof
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: unknown or not canonical, as applicable
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes for browser smoke
- Who should test this URL: the user or Lane 12 after browser access is available
- Do not test these URLs: do not treat API URL as browser smoke
- Known caveats: API fallback cannot validate UI rendering, Cloudflare Access, cache-busting, or static asset freshness
```

## Current recommended smoke URL

For the current user-smoke pause point, use:

`https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=verify-77ff8f6-chord-fretboard-routing`

Protected-preview testing requires Cloudflare Access login, and the expected protected-preview backend should be HEAD `77ff8f6` or later unless `docs/handoffs/task-completions/integration-status.md` supersedes that target.

## Tests and checks

- `git status --short`: broad pre-existing dirty worktree confirmed before edits.
- `git diff --check`: passed.

## Integration notes

- QA / Answer Eval should treat browser smoke reports without an exact URL tested as invalid.
- Lane 06 and Lane 12 should include the `Smoke Target` block whenever a UI/protected-preview smoke is requested.
- Repo Steward should not accept API fallback as proof of browser smoke or protected-preview readiness.

## Risk assessment

- Low. This task only updates documentation and test-planning expectations.
- Rollback: revert the documentation edits if the team chooses a different browser-smoke reporting template.

## Commit readiness

Safe to commit

## Suggested next step

- Lane: 12 Self-Hosted Deployment or 15 QA / Answer Eval.
- Exact task: rerun protected-preview browser smoke with the required `Smoke Target` block and report the exact URL the user should use.
