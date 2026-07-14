# Updated Landing Score Artwork

## Task summary

- Replaced the Melody Studio landing-card score with the user-supplied four-note artwork.
- Removed the source image's baked black surround and produced a tightly framed transparent 3:1 PNG so the treble clef, 4/4 signature, staff, and all four notes remain large and legible.
- Preserved the existing card layout, accessible container label, static-image renderer contract, full Melody Studio renderer, fretboard preview, backend, dependencies, and brand assets.

## Files changed

- `ui/assets/landing/melody-score.png`
- `ui/melody-score.js`
- `ui/steel-guitar-rag-mock.html` — one cache-key hunk only
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py` — one cache-key assertion hunk only
- `docs/handoffs/task-completions/2026-07-14-1455-06-updated-landing-score-artwork.md`

No files were deleted. The source file in `~/Downloads` was read but not modified or staged.

## Tests and checks

- `node --check ui/melody-score.js` — pass
- `node --check ui/landing-home.js` — pass
- `node --check ui/answer-client.js` — pass
- `node --check ui/pedal-steel-fretboard.js` — pass
- `.venv/bin/python -m pytest -q tests/test_landing_home_ui.py tests/test_same_origin_smoke_server.py tests/test_frontend_answer_ui.py` — 55 passed
- `.venv/bin/python -m pytest -q` — 1110 passed
- `git diff --check` — pass
- Local browser smoke at desktop and narrow widths — pass

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8920/ui/steel-guitar-rag-mock.html?v=updated-score-artwork-local-20260714`
- Cache-busted URL tested: `http://127.0.0.1:8920/ui/steel-guitar-rag-mock.html?v=updated-score-artwork-local-20260714`
- Exact URL the user should use: protected-preview URL to be recorded after commit and restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8920`
- Expected backend port: 8920
- Expected git HEAD: uncommitted working tree based on `e1d4d7a6f387060507b259d68a33a9ca8767f75a`
- Version endpoint: not available on the static local server
- Version endpoint result: not available
- If version endpoint missing, how version is inferred: cache-busted asset URL and inspected working-tree files
- Whether app root `/` works: yes, as a static directory listing; not used for smoke
- Whether app root `/` is expected to work: no, not as the canonical app route
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: stale protected-preview cache keys from earlier score iterations
- Known caveats: local static smoke does not prove protected-preview authentication or runtime version

Browser assertions: one 1452×484 PNG rendered at 210×70; exact 3:1 proportion; no SVG or Canvas descendant; no card/page horizontal overflow; no console warning or error. Visual checks confirmed a clear large treble clef and 4/4 signature, four complete notes, attached stems/beam, no clipping, and no black rectangle.

## Integration notes

- The landing preview continues to return `true` from `STEEL_RAG_MELODY_SCORE.renderPreview(container)` and reports `data-score-renderer="static-png-preview"`.
- The asset query and script query changed to `updated-score-artwork-20260714-1`.
- No API, schema, auth, corpus, retrieval, or full-workspace rendering contract changed.

## Risk assessment

- Low. The change is isolated to one static landing asset, intrinsic image metadata, cache keys, and focused tests.
- Rollback is the scoped implementation commit.

## Human decision needed

- No.

## Safe-to-stage exact file list

- `ui/assets/landing/melody-score.png`
- `ui/melody-score.js`
- Exact Melody score cache-key hunk in `ui/steel-guitar-rag-mock.html`
- `tests/test_landing_home_ui.py`
- Exact Melody score cache assertion hunk in `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-14-1455-06-updated-landing-score-artwork.md`

## Files that must not be staged

- Every other dirty or untracked file, including `docs/handoffs/task-completions/integration-status.md`, `ui/assets/music_staff.png`, protected paths, corpus/source files, brand assets, and unrelated Backstage work.

## Recommended next lane

- Lane 01 exact-hunk commit, followed by Lane 12 protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Proceed under Repo Steward auto-approval: stage only the exact files/hunks above, commit the updated score artwork, restart the protected preview from that exact commit, and record the authenticated cache-busted URL.
