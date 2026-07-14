# Landing Melody PNG Preview

## Task summary

Replaced the landing-card Melody Studio score approximation with the user-supplied production artwork at `ui/assets/landing/melody-score.png`. The landing-only `renderPreview(container)` now creates one decorative `<img>` with intrinsic dimensions and a responsive class. It creates no Canvas and no SVG. The full Melody Studio renderer, playback, composition behavior, fretboard, lessons, backend, auth, corpus, and deployment configuration were not changed.

The supplied `ui/assets/music_staff.png` was RGB-only and contained a baked near-white checkerboard/background. The original source remains untouched and untracked. A deterministic local cleanup created the production RGBA derivative by isolating the existing dark/warm notation, preserving small enclosed note and glyph fills, adding a narrow antialias edge, and making the remaining source background fully transparent. No notation was traced, redrawn, or generated.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Verification: `15 QA / Answer Eval`
- Exact-path/hunk commit: `01 Repo Steward`
- Protected-preview verification: `12 Self-Hosted Deployment`
- Task mode: approved Autopilot UI adjustment

## Files changed

- `ui/assets/landing/melody-score.png` — new 2172×724 RGBA production asset with real transparency
- `ui/melody-score.js` — landing preview now mounts the approved PNG as a decorative image
- `ui/workspace-shell.css` — stable 3:1 responsive sizing with `object-fit: contain`
- `ui/steel-guitar-rag-mock.html` — score script and stylesheet cache keys only; other dirty hunks are unrelated and must remain unstaged
- `tests/test_landing_home_ui.py` — PNG path, alpha, intrinsic-size, semantic-image, no-Canvas/no-SVG, and responsive CSS regressions
- `tests/test_same_origin_smoke_server.py` — cache keys and successful PNG static serving only; other dirty hunks are unrelated and must remain unstaged
- This handoff

No file was deleted. `ui/assets/music_staff.png` remains the untouched untracked source and must not be staged.

## Tests and checks

- `node --check ui/melody-score.js` — passed
- `node --check ui/landing-home.js` — passed
- `node --check ui/answer-client.js` — passed
- `node --check ui/pedal-steel-fretboard.js` — passed
- `.venv/bin/python -m pytest -q tests/test_landing_home_ui.py tests/test_same_origin_smoke_server.py tests/test_frontend_answer_ui.py` — 55 passed
- `.venv/bin/python -m pytest -q` — 1,108 passed, 1 unrelated failure in `tests/test_e9_explorer_controls_ui.py::test_e9_fretboard_explorer_controls_are_mode_aware`; the dirty unrelated `ui/e9-fretboard-explorer.js` now calls `document.addEventListener`, while that test's document stub does not implement it
- Scoped `git diff --check` — passed
- Production PNG inspection — `2172×724`, `RGBA`, alpha extrema `(0, 255)`, nonempty-alpha bounds `(116, 176, 2047, 525)`
- Local static requests — landing `200`; PNG `200 image/png`
- Local browser smoke — passed at desktop and phone widths with zero relevant browser logs

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8917/ui/steel-guitar-rag-mock.html?v=landing-melody-png-local-1`
- Cache-busted URL tested: `http://127.0.0.1:8917/ui/steel-guitar-rag-mock.html?v=landing-melody-png-local-1`
- Exact URL the user should use: protected-preview URL will be recorded after the exact-hunk commit and restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8917`
- Expected backend port: 8917
- Expected git HEAD: working tree based on `69f63d30555bd49a12e655bf35b0c29d588a9c4a`
- Version endpoint: unavailable on the static-only local server
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: cache-busted assets were served directly from the scoped working tree
- Whether app root `/` works: static directory listing only
- Whether app root `/` is expected to work: no for this local static smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: the local URL after the temporary server stops, historical protected-preview URLs, or uncached landing URLs
- Known caveats: the full suite has one classified unrelated dirty-worktree Explorer test failure; local static API calls return expected missing-route responses and are not protected-preview API smoke

## Local browser smoke result

**Pass.**

- One `img.home-melody-score-image` loaded from `assets/landing/melody-score.png`.
- Natural dimensions were `2172×724`; rendered dimensions were `210×70`, an exact 3:1 ratio.
- The image was fully contained inside the preview at desktop and phone widths.
- `object-fit` computed to `contain`.
- The image had empty alt text while the existing labeled preview container retained the accessible description.
- The preview contained zero Canvas and zero SVG descendants.
- No horizontal document overflow occurred.
- Visual inspection showed the complete clef, 4/4 signature, all five staff lines, and the final note with the dark card background visible through transparent areas. No checkerboard or opaque rectangle was visible.
- Browser logs were empty.

## Integration notes

- `STEEL_RAG_MELODY_SCORE.renderPreview(container)` retains its boolean return contract.
- Landing diagnostic marker: `data-score-renderer="static-png-preview"`.
- Image marker: `data-preview-kind="approved-melody-score-png"`.
- The full `render(...)` notation path and its VexFlow/fallback behavior are unchanged.
- The landing cache keys become `landing-melody-png-20260714-1` for both `workspace-shell.css` and `melody-score.js`.

## Risk assessment

Low. The runtime change is limited to the decorative landing score preview and its styling. The asset cleanup is deterministic and the untouched source is preserved. Rollback requires reverting the scoped commit; no data or configuration migration is involved.

## Human decision needed

No. The slice is ready for exact-hunk commit and protected-preview verification.

## Safe-to-stage exact file list

- `ui/assets/landing/melody-score.png`
- `ui/melody-score.js`
- `ui/workspace-shell.css`
- only the two landing cache-key hunks in `ui/steel-guitar-rag-mock.html`
- `tests/test_landing_home_ui.py`
- only the two cache-key assertions and PNG-serving assertion block in `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-14-1417-06-landing-melody-png-preview.md`

## Files that must not be staged

- `ui/assets/music_staff.png` — untouched source asset
- all unrelated hunks in `ui/steel-guitar-rag-mock.html`
- all unrelated hunks in `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/integration-status.md`
- all unrelated dirty/untracked runtime, Explorer, Backstage, corpus, source-inbox, brand, deployment, private-data, and historical-handoff files

## Recommended next lane

`01 Repo Steward` for exact-path/exact-hunk commit, then `12 Self-Hosted Deployment` for authenticated protected-preview smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Autopilot exact-hunk approval, commit only the listed asset, implementation, test, and handoff changes, update the protected preview from that exact commit, and run authenticated desktop/mobile smoke at a new cache-busted URL.
