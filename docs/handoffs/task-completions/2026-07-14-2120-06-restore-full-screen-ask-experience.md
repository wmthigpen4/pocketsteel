# Restore Full-Screen Ask Experience

## Task summary

Restored the existing full-screen Ask workspace after a question is submitted from the landing card. The landing page structure, artwork, navigation, spacing, and other cards were intentionally left unchanged. The landing Ask textarea is now 96px tall with 15px text, and its button reads **Ask the Brain**. In the answer workspace, the header **Ask the Steel Guitar Brain** control focuses and scrolls to the single existing follow-up composer. Additional questions replace the current answer without returning to the landing page. Home, the logo, and Return to the stage retain their home behavior.

No backend, answer API, authentication, retrieval, source, answer-content, asset, corpus, or deployment configuration behavior was changed.

## Lane classification

- Primary lane: 06 UX/UI Design
- Verification lane: 15 QA / Answer Eval
- Commit lane: 01 Repo Steward
- Preview lane: 12 Self-Hosted Deployment
- Task mode: YELLOW UI flow change, explicitly approved for end-to-end implementation by the user

## Files changed

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `tests/test_frontend_answer_ui.py`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-14-2120-06-restore-full-screen-ask-experience.md`

No files were deleted. No generated artifacts were created.

## Tests and checks

- `node --check ui/answer-client.js` — passed
- `node --check ui/pedal-steel-fretboard.js` — passed
- `node --check ui/landing-home.js` — passed
- `node --check ui/melody-score.js` — passed
- `.venv/bin/python -m pytest -q tests/test_frontend_answer_ui.py tests/test_landing_home_ui.py tests/test_same_origin_smoke_server.py` — 66 passed
- `.venv/bin/python -m pytest -q` — 1133 passed
- `git diff --check` — passed before commit staging

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8921/ui/steel-guitar-rag-mock.html?access=beta_user&v=full-screen-ask-local-20260714`
- Cache-busted URL tested: `http://127.0.0.1:8921/ui/steel-guitar-rag-mock.html?access=beta_user&v=full-screen-ask-local-20260714`
- Exact URL the user should use: protected-preview URL to be recorded by Lane 12 after commit
- Auth required: no
- Auth provider: local scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8921`
- Expected backend port: 8921
- Expected git HEAD: `4ba4014266c8627ea58f6098c8128f012d495439` plus the scoped working-tree UI changes
- Version endpoint: not used for working-tree local smoke
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: direct working-tree server and cache-busted stylesheet URL
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this local UI smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: protected preview until the scoped commit is deployed
- Known caveats: the browser viewport helper reported an effective 520x1125 viewport for the requested 390x844 narrow viewport

Results:

- Desktop: landing rendered without horizontal overflow; textarea computed to 96px and 15px; first submission opened the full-screen workspace.
- Desktop: the header Ask control focused the existing `#followup-question`; submitting a second question kept the workspace visible, kept landing hidden, cleared the composer, and replaced the displayed question and answer.
- Narrow: the compact header label rendered as **Ask**; the same first-question, focus, and in-place follow-up behavior passed without horizontal overflow.
- Exactly one `#followup-question` existed in the workspace.
- Home returned to the landing page and hid the answer workspace; the landing textarea remained 96px and 15px.
- Browser console errors and warnings: none.

## Integration notes

The follow-up field was not moved or duplicated. Existing submission handlers, chips, Enter handling, loading/error behavior, access checks, and copedent context remain on their existing code paths. The stylesheet cache key changed to `full-screen-ask-20260714-1`.

## Risk assessment

Low. The change is limited to one navigation listener, a focus helper, landing Ask-card presentation, cache key, and focused regression assertions. Rollback is the scoped implementation commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `tests/test_frontend_answer_ui.py`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-14-2120-06-restore-full-screen-ask-experience.md`

## Files that must not be staged

Every other modified or untracked path in the dirty worktree, including protected corpus, source-inbox, brand, public, deployment, and integration-status paths.

## Recommended next lane

Lane 01 Repo Steward for exact-path staging and commit, followed by Lane 12 protected-preview update and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval with the exact files listed above, then update and smoke the protected preview at an exact cache-busted URL.
