# Immediate Follow-Up Chips and Answer Workspace Cleanup

## Task summary

Adjusted the full-screen answer workspace from user-smoke feedback. Follow-up chips now submit their displayed question immediately instead of copying text into the composer. The generic fallback chip **Ask a follow-up** was replaced with the actionable question **How does this apply on E9?**, and the remaining fallback labels were rewritten as complete search prompts. Removed the redundant **Return to the stage** control, its styling, DOM reference, and listener. Header Home and the logo remain the answer-workspace routes back to landing.

No backend, answer API, retrieval, source, auth, copedent, or answer-content behavior changed.

## Lane classification

- Primary lane: 06 UX/UI Design
- Verification lane: 15 QA / Answer Eval
- Commit lane: 01 Repo Steward
- Preview lane: 12 Self-Hosted Deployment
- Task mode: YELLOW UI interaction adjustment, explicitly approved through user-smoke comments and the repo autopilot workflow

## Files changed

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-07-15-0848-06-immediate-followup-chips.md`

No files were deleted or generated.

## Tests and checks

- `git diff --check` — passed
- `node --check ui/answer-client.js` — passed
- `node --check ui/pedal-steel-fretboard.js` — passed
- `node --check ui/landing-home.js` — passed
- `.venv/bin/python -m pytest -q tests/test_frontend_answer_ui.py tests/test_landing_home_ui.py tests/test_same_origin_smoke_server.py` — 67 passed
- `.venv/bin/python -m pytest -q` — 1135 passed

## Local browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8921/ui/steel-guitar-rag-mock.html?access=beta_user&v=followup-chip-local-20260715`
- Cache-busted URL tested: same as above
- Exact URL the user should use: protected-preview URL to be recorded after commit
- Auth required: no
- Auth provider: local scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8921`
- Expected backend port: 8921
- Expected git HEAD: `7ed3fc307d25766cef17bcc698ba44d5bcf08fbf` plus scoped working-tree changes
- Version endpoint: not used for working-tree local smoke
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: direct working-tree server and cache-busted page URL
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this focused local UI smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: protected preview until the scoped commit is deployed
- Known caveats: the viewport helper produced an effective 520x1125 narrow viewport for the requested 390x844 viewport

Results:

- Controlled no-source response rendered four actionable fallback questions and no generic **Ask a follow-up** chip.
- Clicking **How does this apply on E9?** immediately replaced the displayed question with that search; it did not populate the composer or return to landing.
- The composer remained empty and unique.
- No `.stage-return` element remained.
- Desktop and effective narrow layouts had no horizontal overflow.
- Browser warnings and errors: none.

## Integration notes

API-provided `response.followups` are still rendered as supplied; the interaction change applies to all rendered follow-up chips so each submits immediately. The manual composer, Enter-key submission, header Ask focus, and loading/error flows remain unchanged.

## Risk assessment

Low. The change removes one redundant navigation control and shortens an existing two-step chip interaction to one step. Rollback is the scoped commit.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-07-15-0848-06-immediate-followup-chips.md`

## Files that must not be staged

Every other modified or untracked path, including concurrent Melody Studio, Backstage, protected corpus, source-inbox, brand, public, deployment, auth, and integration-status work.

## Recommended next lane

Lane 01 exact-path commit, then Lane 12 protected-preview update and authenticated smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the three paths listed above, update the protected preview to that exact commit, and verify immediate chip submission plus the removed stage-return control.
