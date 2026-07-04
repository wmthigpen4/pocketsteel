# 2026-07-04 09:23 - Lane 06 - Explorer Row List Removal

## Task summary

Requested: remove the duplicative "Explorer row details" box row from the E9 Fretboard Explorer. The user selected `div#explorer-row-list` in protected preview and noted that the same information already appears in the result cards under the fretboard and in the right-side "Why this works" inspector.

Completed: hid the `explorer-details` / `explorer-row-list` compatibility section from layout and accessibility while keeping the DOM target available for existing Explorer JS references. This removes the visible duplicate boxes without changing Explorer music logic, selection state, active result cards, detail panel behavior, handoff query startup, or backend behavior.

Intentionally not changed: no backend/API code, no deterministic music rules, no Explorer data rows, no corpus/scraping/embeddings/Chroma/vector stores, no auth/DNS/Cloudflare Access policy, no private-source files, and no unrelated dirty/untracked work.

## Files changed

- `ui/e9-fretboard-explorer.html`
  - Changed `.explorer-details` and `.explorer-row-list` to `display: none`.
  - Added `hidden aria-hidden="true"` to the `explorer-details` wrapper.
- `tests/test_frontend_answer_ui.py`
  - Added assertions that the row-list compatibility section remains present for JS compatibility but is hidden from the rendered UI.
- `docs/handoffs/task-completions/2026-07-04-0923-06-explorer-row-list-removal.md`
  - This handoff.
- `docs/handoffs/task-completions/integration-status.md`
  - Added a top status note for this UI fix and protected-preview smoke.
- `docs/handoffs/task-completions/assets/2026-07-04-explorer-row-list-removal/`
  - Protected-preview screenshots for desktop, mobile, static handoff, and movement handoff states.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-row-list-remove-20260704`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-row-list-remove-20260704`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-row-list-remove-20260704`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; the page loaded in the authenticated in-app browser session
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: 8770
- Expected git HEAD: final commit from this slice
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"7dcd8cb","git_branch":"feature/answer-api","server_started_at":"2026-07-04T14:12:16.159967+00:00","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: not retested; this Explorer fix uses the direct `/ui/e9-fretboard-explorer.html` URL
- Whether app root `/` is expected to work: expected to redirect to the app shell based on prior Lane 12 smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: not retested; not touched by this fix
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Whether `/ui/e9-fretboard-explorer.html` works: yes, verified in protected browser
- Who should test this URL: Codex and the user
- Do not test these URLs: root-only URLs as proof of cache-busted Explorer behavior
- Known caveats: `/api/version` still reports the pre-fix runtime commit `7dcd8cb` until the LaunchDaemon is restarted after commit; static Explorer HTML served the row-list removal in protected preview

## Protected-preview browser smoke result

PASS for the scoped UI behavior.

Desktop URL:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-row-list-remove-20260704`

Observed:

- Page title: `E9 Fretboard Explorer - Steel Guitar RAG`
- Heading: `E9 Fretboard Explorer`
- Cloudflare Access login text: absent
- Six task cards rendered and visible:
  - `find-chord`
  - `find-note`
  - `explore-grip`
  - `walk-harmonized-scale`
  - `study-movement-path`
  - `identify-voicing`
- Active result cards remained visible under the fretboard: 37 cards observed in the default state.
- `#explorer-row-list` remained in the DOM but computed `display: none`.
- `.explorer-details` computed `display: none`, had `hidden`, had `aria-hidden="true"`, and was not visible.
- Lower controls remained available: active results, selected detail, and pedal/lever impact preview containers were present.
- No page-level horizontal overflow.
- No `[object Object]`.
- No relevant console warnings/errors.

Mobile/narrow URL:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-row-list-remove-20260704-mobile`

Observed:

- Six task cards rendered.
- Active result cards remained visible.
- `#explorer-row-list` computed `display: none` and was not visible.
- `.explorer-details` computed `display: none` and was not visible.
- No page-level horizontal overflow.
- No `[object Object]`.
- No relevant console warnings/errors.

Static handoff URL:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?mode=single&source=answer&key=G&fret=3&strings=4-5-6&grip=4-5-6&v=explorer-row-list-remove-20260704-static`

Observed:

- Mode initialized to `single`.
- Selected task initialized to `explore-grip`.
- String group initialized to `4-5-6`.
- Active result cards remained visible.
- Right-side selected detail showed the relevant G major grip explanation.
- Row-list remained hidden.
- No page-level horizontal overflow.
- No `[object Object]`.

Movement handoff URL:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?mode=path&source=movement-card&key=G&progression=I-IV&v=explorer-row-list-remove-20260704-movement`

Observed:

- Mode initialized to `path`.
- Selected task initialized to `study-movement-path`.
- Active path cards remained visible.
- Right-side selected detail showed the relevant harmonized scale path explanation.
- Row-list remained hidden.
- No page-level horizontal overflow.
- No `[object Object]`.
- No relevant console warnings/errors.

## Screenshot evidence

- `docs/handoffs/task-completions/assets/2026-07-04-explorer-row-list-removal/protected-row-list-removed-desktop.png`
- `docs/handoffs/task-completions/assets/2026-07-04-explorer-row-list-removal/protected-row-list-removed-mobile.png`
- `docs/handoffs/task-completions/assets/2026-07-04-explorer-row-list-removal/protected-row-list-removed-static-handoff.png`
- `docs/handoffs/task-completions/assets/2026-07-04-explorer-row-list-removal/protected-row-list-removed-movement-handoff.png`

## Tests and checks

- `git status --short` - completed; broad unrelated dirty/untracked work remains parked
- `git branch --show-current` - `feature/answer-api`
- `git rev-parse --short HEAD` - `cf00ec9` at task start
- `git log --oneline -5` - completed
- `node --check ui/e9-fretboard-explorer.js` - passed
- `node --check ui/pedal-steel-fretboard.js` - passed
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - passed, 24 tests
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - passed, 43 tests
- `git diff --check` - passed
- Protected-preview browser smoke - passed for desktop, mobile/narrow, static handoff URL, and movement handoff URL

## Integration notes

- This is a UI-only removal of a visible duplicate result surface.
- The compatibility node remains in the DOM to avoid broad JS rewiring in this slice.
- Existing active result cards under the fretboard remain the primary card rail.
- The right-side "Why this works" inspector remains the primary selected-position detail surface.
- Protected preview served the static HTML change, but `/api/version` reports `7dcd8cb` until the runtime is restarted after this commit.

## Risk assessment

Risk: low. The change is presentation-only and leaves existing JS compatibility paths intact. Focused tests and protected browser smoke passed.

Rollback note: restore `.explorer-details` to `display: grid`, `.explorer-row-list` to `display: flex`, and remove `hidden aria-hidden="true"` from the details wrapper.

## Human decision needed

No.

## Safe-to-stage exact file list

- `ui/e9-fretboard-explorer.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-07-04-0923-06-explorer-row-list-removal.md`
- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/assets/2026-07-04-explorer-row-list-removal/protected-row-list-removed-desktop.png`
- `docs/handoffs/task-completions/assets/2026-07-04-explorer-row-list-removal/protected-row-list-removed-mobile.png`
- `docs/handoffs/task-completions/assets/2026-07-04-explorer-row-list-removal/protected-row-list-removed-static-handoff.png`
- `docs/handoffs/task-completions/assets/2026-07-04-explorer-row-list-removal/protected-row-list-removed-movement-handoff.png`

## Files that must not be staged

- Any unrelated dirty or untracked files currently parked in the worktree
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
- Corpus/private/source/provenance/vector/deployment/auth/secrets files

## Recommended next lane

Lane 12 if strict `/api/version` alignment is required after this commit; otherwise user smoke can continue against the direct Explorer URL.

## Commit readiness

Safe to commit.

## Suggested next step

After commit, restart protected preview only if strict `/api/version` proof is required for the UI slice. For normal static Explorer validation, use:

`https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-row-list-remove-20260704`
