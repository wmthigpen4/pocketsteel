# Hide landing-preview neck-edge labels

## Task summary

Removed the left-side string-number and tuning-note labels from the landing-page fretboard preview only.

Preserved:

- The landing preview's `No pedals`, `A + F lever`, and `A + B pedals` headings.
- The landing preview's playable-position labels: `4 / 5 / 6`, `4F / 5A / 6`, and `4 / 5A / 6B`.
- All string-number and tuning-note labels in the full Fretboard Explorer.
- Shared fretboard renderer behavior and data.

The change is isolated under `.home-explorer-stage`; Explorer does not use that container class.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Task mode: YELLOW landing UI adjustment explicitly approved by direct user-smoke feedback.

## Files changed

- `ui/workspace-shell.css`
- `ui/steel-guitar-rag-mock.html` (stylesheet cache key only)
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1815-06-hide-landing-neck-labels.md`

No shared renderer, Explorer, asset, backend, auth, corpus, source, or deployment file changed.

## Tests and checks

- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `node --check ui/landing-home.js` — passed.
- `.venv/bin/python -m pytest -q tests/test_landing_home_ui.py tests/test_frontend_answer_ui.py tests/test_same_origin_smoke_server.py tests/test_smoke.py tests/test_pedal_steel_fretboard_ui.py` — `94 passed`.
- `.venv/bin/python -m pytest -q` — `1035 passed in 49.28s`.
- Scoped `git diff --check` — passed.
- Local browser smoke of landing and Explorer — passed.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?access=beta_user&v=landing-neck-labels-local-1`
- Cache-busted URL tested: same as above
- Exact URL the user should use: protected-preview URL will be recorded after commit and restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8897`
- Expected backend port: 8897
- Expected git HEAD: working tree on `f9d5c391caf5e5586d124cda0482ee274248b66a`
- Version endpoint: not used for local visual smoke
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: cache-busted local stylesheet served directly from the scoped working tree
- Whether app root `/` works: not tested in this focused smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: historical cached preview URLs or the public marketing landing page
- Known caveats: none for the scoped label behavior

Browser assertions:

- Landing: 10 `[data-string-label]` elements rendered with computed `display:none`.
- Landing: 10 `[data-tuning-label]` elements rendered with computed `display:none`.
- Landing: all nine `[data-string-action-label]` elements remained visible.
- Landing: all three position headings remained visible.
- Explorer URL tested: `http://127.0.0.1:8897/ui/e9-fretboard-explorer.html?access=beta_user&v=landing-neck-labels-explorer-check`.
- Explorer: all 10 string-number labels and all 10 tuning-note labels remained visible with computed `display:block`.
- Both pages had zero document overflow.

## Integration notes

The implementation uses landing-scoped CSS instead of adding a shared renderer option, keeping the behavior local and avoiding any Explorer contract change.

The landing shell stylesheet cache key is now `landing-neck-labels-20260713-1`.

## Risk assessment

Low. One scoped CSS rule hides two renderer label groups only inside the landing preview. Rollback is the single scoped commit.

## Human decision needed

No. The user explicitly requested removal from the landing page and preservation in Explorer.

## Safe-to-stage exact file list

- `ui/workspace-shell.css`
- `ui/steel-guitar-rag-mock.html`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1815-06-hide-landing-neck-labels.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Dirty/unrelated `ui/brand/` files.
- `Neon Sign/`, `public/`, deploy assets, and every unrelated dirty/untracked path.
- Backend, corpus, source-inbox, auth, DNS, Cloudflare, secret, vector, embedding, and generated-data paths.

## Recommended next lane

`01 Repo Steward` for exact-path commit, followed by `12 Self-Hosted Deployment` for protected-preview restart and authenticated landing/Explorer browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Stage exactly the five approved paths, commit the landing-only label cleanup, restart protected preview, and verify the scoped behavior on both the landing page and Explorer.
