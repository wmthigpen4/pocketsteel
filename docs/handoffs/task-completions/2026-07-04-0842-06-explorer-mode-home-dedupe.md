# 2026-07-04 08:42 - Lane 06 - Explorer Mode Home Dedupe

## Task summary

Requested: fix the E9 Fretboard Explorer showing two competing mode/task entry rows after Explorer Mode Home v1. Completed: kept the six "Choose what you want to learn" task cards as the single visible primary entry system, removed the older five-card `Single Grip` / `Harmonized Scale Path` / `Single-Note Finder` / `Voicing Identifier` / `Chord / Voicing Finder` row from the default page, and retained the hidden mode select as internal state for existing task-card and query-param behavior.

Intentionally not changed: no backend behavior, no Explorer musical rules, no answer-page handoff logic, no corpus/scraping/embeddings/Chroma/auth/DNS/deployment/private-source files, and no broad Explorer redesign.

## Files changed

- `ui/e9-fretboard-explorer.html`
  - Removed the visible legacy mode-card row and its CSS.
  - Kept the internal `#explorer-explore-mode` select in a hidden state-only panel.
  - Updated the Explorer script cache key to `explorer-mode-home-dedupe-20260704`.
- `tests/test_frontend_answer_ui.py`
  - Updated focused assertions to require the six task cards as the visible mode home.
  - Added assertions that the legacy `.explorer-mode-tabs` / `data-explorer-mode-tab` row is absent from the HTML.
  - Updated the script cache-bust expectation.

## Tests and checks

- `node --check ui/e9-fretboard-explorer.js` - passed
- `node --check ui/pedal-steel-fretboard.js` - passed
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - passed, 24 tests
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - passed, 43 tests
- `git diff --check` - passed

## Browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8899/ui/e9-fretboard-explorer.html?v=explorer-mode-home-dedupe-local`
- Cache-busted URL tested: `http://127.0.0.1:8899/ui/e9-fretboard-explorer.html?v=explorer-mode-home-dedupe-local`
- Exact URL the user should use: protected-preview URL after Lane 12 refresh, with `?v=explorer-mode-home-dedupe-<commit>`
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8899`
- Expected backend port: 8899
- Expected git HEAD: `468fc75` at start of implementation
- Version endpoint: not used for this static local smoke
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: local working tree served by `python -m http.server` from repo root
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: not required for this Explorer-only smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: not required for this Explorer-only smoke
- Who should test this URL: Codex locally; the user after protected-preview refresh
- Do not test these URLs: production/root URLs without the refreshed runtime/cache key
- Known caveats: local static smoke does not prove protected-preview runtime state

Local smoke results:
- No-query Explorer load: passed
  - Six task cards rendered.
  - `.explorer-mode-tabs` count: 0.
  - `[data-explorer-mode-tab]` count: 0.
  - Hidden mode panel computed display: `none`.
  - Controls and fretboard rendered.
  - No `[object Object]`.
  - No page-level horizontal overflow.
- Task card clicks: passed
  - `Find a chord` selected mode `chord`.
  - `Find a note` selected mode `note`.
  - `Explore a grip` selected mode `single`.
  - `Walk a harmonized scale` selected mode `path`.
  - `Study a movement path` selected mode `path`.
  - `Identify a voicing` selected mode `voicing`.
  - All retained controls and zero legacy mode tabs.
- Static handoff URL: passed
  - URL: `http://127.0.0.1:8899/ui/e9-fretboard-explorer.html?mode=single&source=answer&key=G&fret=3&strings=4-5-6&grip=4-5-6&v=explorer-mode-home-dedupe-local-static`
  - Selected mode `single`, selected task `explore-grip`, string group `4-5-6`.
- Movement handoff URL: passed
  - URL: `http://127.0.0.1:8899/ui/e9-fretboard-explorer.html?mode=path&source=movement-card&key=G&progression=I-IV&v=explorer-mode-home-dedupe-local-movement`
  - Selected mode `path`, selected task `study-movement-path`, path-family control visible.
- Mobile/narrow smoke: passed
  - URL: `http://127.0.0.1:8899/ui/e9-fretboard-explorer.html?v=explorer-mode-home-dedupe-local-mobile`
  - Six task cards rendered, zero legacy mode tabs, controls visible, no `[object Object]`, no page-level horizontal overflow.
- Console errors: none observed.

## Integration notes

- The underlying `#explorer-explore-mode` select remains in the DOM for existing JS state and safe query-param startup.
- The visible legacy row is removed, so `elements.modeTabs` is an empty NodeList in normal HTML; the existing JS already handles this because it only iterates the collection.
- Safe query startup from answer-page handoffs remained valid in local smoke.

## Risk assessment

Risk: low. This removes duplicate presentation only. The mode state select and existing task-card event paths remain unchanged. Rollback is limited to restoring the removed mode-tab markup/CSS and reverting the test expectations.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-07-04-0842-06-explorer-mode-home-dedupe.md`

## Files that must not be staged

- Any unrelated dirty or untracked files currently parked in the worktree.
- `README.md`
- `corpus_metadata/*`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- `rag_*.py`
- `source-inbox/*`
- `ui/brand/*`
- `public/brand/*`
- `Neon Sign/`
- Corpus/private/source/provenance/vector/deployment/auth/secrets files.

## Recommended next lane

Lane 12 protected-preview refresh/smoke for the committed cache-busted Explorer URL, then user smoke.

## Commit readiness

Safe to commit.

## Suggested next step

Lane 12: run protected-preview smoke for `/ui/e9-fretboard-explorer.html?v=explorer-mode-home-dedupe-<commit>` and verify the Explorer shows only the six task cards as the primary entry row, with no visible legacy five-card mode row.
