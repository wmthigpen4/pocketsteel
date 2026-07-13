# Melody Studio Portrait Print User-Smoke Fix

## Task summary

Repaired Melody Studio's printed tablature after the supplied native-browser PDF showed a three-page landscape result with screen-only controls on page one and tablature split across pages two and three.

The print action now produces a dedicated Letter portrait sheet containing only:

- a compact Melody Studio / Steel Guitar RAG masthead;
- the clean song or melody title;
- the selected E9 arrangement label;
- the complete fixed-width tablature; and
- `www.steelguitarrag.com` in the footer.

The print sheet excludes Edit melody, the attribution link, Octave colors, String labels, Note labels, staff notation, fretboard, route controls, transport, playback controls, and all other screen chrome. It no longer prints the backend's misleading `Complete E9 lesson` suffix. Single-section complete songs also omit the redundant `Complete song` tab heading.

This task intentionally did not change the on-screen lesson, arranger decisions, API contracts, source attribution behavior on screen, auth, deployment configuration, corpus, or private data.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lanes: `15 QA / Answer Eval`, `01 Repo Steward`, and `12 Self-Hosted Deployment`
- Task type: user-smoke UI/PDF bug fix
- Task mode: approved Autopilot user-smoke adjustment

## Files changed

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-13-1233-06-melody-portrait-print-fix.md`

Generated verification artifacts under `tmp/pdfs/` remain untracked/ignored and must not be committed.

## Tests and checks

- `node --check ui/melody-workbench.js` - passed.
- `node --check ui/melody-score.js` - passed.
- `node --check ui/pedal-steel-fretboard.js` - passed.
- `.venv/bin/python -m pytest -q tests/test_melody_workbench_ui.py tests/test_same_origin_smoke_server.py tests/test_melody_assistant.py tests/test_tab_engine.py` - **86 passed**.
- `.venv/bin/python -m pytest -q` - **971 passed**.
- Scoped `git diff --check` - passed.
- Supplied PDF inspection:
  - source artifact: three pages;
  - source orientation: Letter landscape;
  - page one contained only title/source/screen controls;
  - tablature started on page two and overflowed onto page three.
- Working-tree PDF verification:
  - generated from Amazing Grace in G with Recommended arrangement;
  - **one page**;
  - **Letter portrait** (`612 x 792 pt`);
  - clean title `Amazing Grace`;
  - arrangement line `E9 tablature · Recommended arrangement`;
  - complete tablature visible;
  - no Edit melody, attribution link, octave/string/note toggles, or `Complete E9 lesson` copy;
  - `www.steelguitarrag.com` visible in the footer;
  - latest rendered PNG inspected visually with no clipping, overlap, or pagination defect.

## Smoke Target

- Target type: local
- Result type: browser smoke plus generated-PDF visual verification
- Exact browser URL tested: `http://127.0.0.1:8784/ui/melody-workbench.html?access=beta_user&v=portrait-print-local-20260713-2`
- Cache-busted URL tested: same as above
- Exact URL the user should use: pending protected-preview restart after commit
- Auth required: yes
- Auth provider: local development scaffold
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8784`
- Expected backend port: 8784
- Expected git HEAD: working tree based on `068495b59ebc3c2f3199683a5b853ab9f9042a3c`
- Version endpoint: not used for working-tree verification
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: cache-busted working-tree assets served from the scoped local server
- Whether app root `/` works: not part of this local print-layout check
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: served by the same local smoke app; not the print target
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: prior `sgf-arranger-1bea429`, `blocking-lever-fixtures-068495b`, or unversioned protected URLs
- Known caveats: the local PDF was generated through headless Chrome after the in-app local workflow was verified. Protected Cloudflare Access smoke and `/api/version` verification follow the exact-path commit and restart.

## Integration notes

- The print sheet is a top-level print-only element. The print media rule hides every other body child, preventing hidden or newly added screen controls from leaking into paper output.
- The on-screen result title remains unchanged. A pure client helper derives a truthful print title from the material song name or removes only the `Complete/Section N E9 lesson` suffix.
- The selected route continues to determine printed tab content; the print label is now `E9 tablature · <route>`.
- Multi-section requests retain phrase headings. A one-section complete song does not print a redundant section heading.
- The canonical Melody Exercise documentation now requires Letter portrait, compact one-page output, print-only branding, and suppression of attribution links and screen chrome.

## Risk assessment

- Risk: low.
- Reason: the behavioral change is isolated to print-only DOM/CSS and print-title preparation. On-screen rendering and API contracts are unchanged, and the full suite plus an actual generated PDF are green.
- Rollback: revert the scoped implementation commit and restart the protected preview.

## Human decision needed

No. The user explicitly requested this print repair and branding treatment.

## Safe-to-stage exact file list

- `ui/melody-workbench.html`
- `ui/melody-workbench.js`
- `tests/test_melody_workbench_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/melody-exercise-v0.md`
- `docs/handoffs/task-completions/2026-07-13-1233-06-melody-portrait-print-fix.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (separate coordination artifact)
- Everything under `tmp/pdfs/`
- All unrelated dirty or untracked corpus, source-inbox, private-data, pipeline, landing, deployment, public/brand, `ui/brand/`, `Neon Sign/`, and interest-digest paths

## Recommended next lane

`01 Repo Steward` for exact-path staging and commit, then `12 Self-Hosted Deployment` for protected-preview restart, version verification, authenticated browser smoke, and a final native-print user-smoke handoff.

## Commit readiness

Safe to commit

## Suggested next step

Commit only the six exact paths above, restart the protected preview, verify `/api/version`, arrange Amazing Grace with Recommended arrangement, and confirm the protected print-only DOM contains the clean title, route, tab, and website footer before handing one cache-busted URL to the user.
