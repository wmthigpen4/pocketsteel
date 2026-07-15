# Hide Ask Header Control on the Ask Workspace

## Task summary

- Hid the header `Ask the Steel Guitar Brain` control only while the full-screen Ask workspace is active.
- Kept the same control visible on the answer workspace so it can return the user to a blank, focused question field.
- Preserved Home, Go Backstage, question submission, answer routing, and all other landing/answer behavior.

## Lane classification

- Lane 06 UX/UI Design with Lane 15 verification and Lane 01 exact-hunk commit.
- GREEN user-smoke UI adjustment; autopilot implementation and commit are approved.

## Files changed

- Exact CSS hunk in `ui/steel-guitar-rag-mock.html`.
- Exact regression hunk in `tests/test_frontend_answer_ui.py`.
- This handoff.

No backend, API, auth, source, corpus, vector, deployment-policy, or private files changed.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_frontend_answer_ui.py -k 'answer_ui_header_only_exposes_home_ask_and_backstage or full_screen_ask_is_the_only_primary_search_surface or answer_workspace_has_no_followup_chips_or_composer'` — PASS, 3 tests.
- `node --check ui/answer-client.js` — PASS.
- `git diff --check` — PASS.

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8766/ui/steel-guitar-rag-mock.html?v=hide-ask-header-local-20260715`
- Cache-busted URL tested: same
- Exact URL the user should use: protected-preview URL to be recorded after commit
- Auth required: no; controlled local state
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8766`
- Expected backend port: 8766
- Expected git HEAD: working tree based on `e112f1c052ea43c7bd6ec1a0a60f089095d18009`
- Version endpoint: `http://127.0.0.1:8766/api/version`
- Version endpoint result: local working-tree runtime
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not used
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stale protected-preview cache keys
- Known caveats: requested 390×844 viewport is exposed as effective 520×1125

Results:
- Ask workspace: header Ask control computed to `display: none`; Home and Go Backstage remained visible.
- Answer workspace: header Ask control computed to `display: flex`.
- Clicking it returned to the Ask workspace, focused `#question`, and hid itself.
- Desktop and narrow views had zero horizontal overflow.

## Integration notes

The change is state-scoped CSS: `.page.is-asking .ask-header-link`. The existing answer-page click behavior remains untouched.

## Risk assessment

Low. The selector only affects the redundant control in one shell state. Rollback is the scoped commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- Exact hunk in `ui/steel-guitar-rag-mock.html`.
- Exact hunk in `tests/test_frontend_answer_ui.py`.
- `docs/handoffs/task-completions/2026-07-15-1034-06-hide-ask-header-on-ask-workspace.md`.

## Files that must not be staged

- All unrelated dirty and untracked files, including unrelated hunks in both overlapping files.
- `docs/handoffs/task-completions/integration-status.md` must remain unstaged and be refreshed separately.

## Recommended next lane

Lane 01 exact-hunk commit, then Lane 12 protected-preview browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval with exact-hunk staging, commit, and authenticated protected-preview verification.
