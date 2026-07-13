# Landing user-smoke adjustments

## Task summary

Implemented the requested landing-page user-smoke adjustments on `feature/answer-api`:

- Kept the hanging sign anchored to the upper-left at desktop and mobile breakpoints.
- Removed `validated positions` from the Explorer preview caption and removed the redundant `Open the full Explorer` link.
- Changed the preview introduction to `See three ways to play G major across the neck.`
- Added the plain-language position headings `No pedals`, `A + F lever`, and `A + B pedals`.
- Added Explorer-style string/action labels inside the highlighted notes: `4 / 5 / 6`, `4F / 5A / 6`, and `4 / 5A / 6B`.
- Replaced the trust-note row with the restored shimmering source-aware AI footer and retained its explanatory popover.

The answer workspace, Backstage behavior, workspace routes, renderer internals, protected brand assets, backend, auth, corpus, and deployment configuration were intentionally not changed.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Task mode: YELLOW UI flow/copy adjustment, explicitly approved through direct user-smoke feedback and handled under the Autopilot adjustment workflow.

## Files changed

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `ui/landing-home.js`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1755-06-landing-user-smoke-adjustments.md`

No files were deleted. No generated visual assets were created or changed.

## Tests and checks

- `node --check ui/landing-home.js` — passed.
- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `.venv/bin/python -m pytest -q tests/test_landing_home_ui.py tests/test_frontend_answer_ui.py tests/test_same_origin_smoke_server.py tests/test_smoke.py tests/test_pedal_steel_fretboard_ui.py tests/test_lesson_workbench_ui.py` — `97 passed`.
- `.venv/bin/python -m pytest -q` — `1035 passed`.
- Scoped `git diff --check` for the five implementation/test files — passed.
- Local browser smoke — passed.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?access=beta_user&v=landing-feedback-local-20260713-4`
- Cache-busted URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?access=beta_user&v=landing-feedback-local-20260713-4`
- Exact URL the user should use: protected-preview URL will be recorded after commit and restart
- Auth required: no for local development smoke
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8897`
- Expected backend port: `8897`
- Expected git HEAD: `d92f29f2ee820e4289ac20d4577de254048c76c4` plus the scoped working-tree adjustment
- Version endpoint: not used for this local static-render check
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: cache-busted assets and direct DOM verification from the working tree
- Whether app root `/` works: not tested in this focused local smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: public marketing landing page or unrelated workspace routes for this focused adjustment
- Known caveats: the responsive viewport capability reported a scaled layout viewport, but the mobile media rules were active; geometry confirmed the sign and shell shared the same left edge and the document had zero horizontal overflow.

Browser assertions:

- Headings rendered as `No pedals`, `A + F lever`, and `A + B pedals`.
- String/action labels rendered as `4, 5, 6`, `4F, 5A, 6`, and `4, 5A, 6B`.
- The hanging sign remained aligned with the shell's left edge at desktop and the mobile breakpoint.
- No document overflow, `[object Object]` text, `validated positions` copy, or redundant full-Explorer link appeared.
- The footer shimmer animation was active.
- The footer explanation opened and closed with correct expanded state.
- Browser console log was empty.

## Integration notes

The landing adapter now supplies presentation-only labels to the existing `DEMO_POSITIONS`; it does not modify shared fretboard data or renderer behavior. The preview continues to use the same real fretboard renderer as Explorer.

No public API, schema, backend, auth, source, or route contract changed.

## Risk assessment

Low. Changes are limited to landing markup, landing styles, the landing renderer adapter, and focused assertions. Rollback is the single scoped UI commit produced from this handoff.

## Human decision needed

No. The user supplied the final wording and label preference directly.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `ui/landing-home.js`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1755-06-landing-user-smoke-adjustments.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `ui/brand/`
- `Neon Sign/`
- `public/`
- Corpus, source-inbox, backend, auth, deployment, config, and all other unrelated dirty or untracked paths.

## Recommended next lane

`01 Repo Steward` for exact-path staging and the scoped commit, followed by `12 Self-Hosted Deployment` for protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Autopilot with exact-path staging of the six approved files, commit the landing adjustment, restart the protected preview using the documented runtime wrapper, and record authenticated protected-preview browser smoke against the new commit.
