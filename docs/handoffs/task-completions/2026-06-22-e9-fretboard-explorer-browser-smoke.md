# E9 Fretboard Explorer Browser Smoke

## Task Summary

Lane 15 QA browser-smoked the new browser-accessible E9 Fretboard Explorer surface from commit `a5389f2`.

Completed:

- Read the required Lane 06 browser surface handoff and earlier Explorer backend/display QA handoffs.
- Tested the exact protected-preview URL in the in-app browser.
- Ran local same-origin browser fallback against the committed static Explorer page because protected preview redirected to Cloudflare Access login.
- Verified Explorer controls, G major rows, G natural minor learner-facing spelling, core/advanced grip labeling, `5-7-8` advanced E-lower pocket display, per-string changes, no `[object Object]`, and narrow viewport usability in local fallback.
- Ran the requested automated checks and full pytest.

Intentionally not changed:

- No implementation files.
- No UI files.
- No corpus, embeddings, Chroma, scraper output, deployment, auth, DNS, assets, private source data, or unrelated dirty/untracked files.

## Pass / Warn / Fail

**Warn.**

The Explorer surface behavior passes local same-origin browser smoke and automated checks. The exact protected-preview URL could not be product-smoked because the in-app browser was redirected to Cloudflare Access login.

This is an access/session blocker for protected-preview browser verification, not a confirmed Explorer product defect.

## Smoke Target

- Target type: protected-preview plus local fallback
- Result type: protected-preview blocked by auth; local browser smoke fallback completed
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622`
- Auth required: yes for protected preview
- Auth provider: Cloudflare Access
- Cloudflare Access login result: failed/not available in in-app browser session; page redirected to Cloudflare Access login
- Local backend URL: none; local static fallback used
- Expected backend port: not applicable for static fallback
- Expected git HEAD: `a5389f2`
- Version endpoint: not applicable; static page
- Version endpoint result: not checked
- If version endpoint missing, how version is inferred: repo `HEAD` was `a5389f2`; exact committed static files were served locally
- Whether app root `/` works: not tested for protected preview
- Whether app root `/` is expected to work: not required for this Explorer URL
- Whether `/ui/steel-guitar-rag-mock.html` works: protected preview not tested due auth; local fallback works and includes `Explore the E9 Fretboard`
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user or Lane 12 with authenticated protected-preview access
- Do not test these URLs: root-only URL as a substitute for this task; this task targets `/ui/e9-fretboard-explorer.html`
- Known caveats: local fallback does not prove Cloudflare Access/protected-preview deployment behavior

## Commit Under Test

- `a5389f2`

Branch:

- `feature/answer-api`

## Files Changed

Created:

- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-browser-smoke.md`

No test or implementation files were modified.

## Browser Smoke Results

### Protected Preview

Exact URL:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622
```

Result:

- Redirected to Cloudflare Access login.
- Page title observed: `Sign in ・ Cloudflare Access`
- Visible heading observed: `Log in to Steel Guitar RAG Private Preview`
- Explorer page content was not reachable in the in-app browser session.

Protected-preview checklist status:

- Exact Explorer URL loads: blocked by Cloudflare Access login.
- No Cloudflare/protected-preview/auth issue blocks the page: **failed in in-app browser session**.
- Explorer page title/content: not reached on protected preview.
- Console errors for Explorer page: not applicable because Explorer page did not load.

Chrome fallback was not used because the Chrome skill requires explicit approval before switching to Chrome solely to work around missing/expired authentication.

### Local Same-Origin Fallback

Local URL:

```text
http://127.0.0.1:8896/ui/e9-fretboard-explorer.html
```

Startup:

```bash
.venv/bin/python -m http.server 8896 --bind 127.0.0.1
```

Result:

- Page title: `E9 Fretboard Explorer - Steel Guitar RAG`
- Entry text identifies the page as `E9 Fretboard Explorer`.
- Page labels data as `Validated Explorer data`.
- Page text says it uses validated Explorer rows, not corpus retrieval or RAG-generated fretboard positions.
- No console errors observed in local fallback.
- Local static server logged 404s for `/brand/pedal-steel-fretboard-background.svg`; this did not block functional Explorer rendering and did not appear as a browser console error in the in-app browser capture.

Controls:

- Key selector exists and is disabled as `G only`.
- Scale selector has `G major` and `G natural minor`.
- Harmony/view selector has `2-string harmonized scale` and `3-string diatonic harmony`.
- String group selector has:
  - `All string groups`
  - core groups: `3-4-5`, `4-5-6`, `5-6-8`, `6-8-10`
  - advanced swaps: `5-6-7`, `6-7-10`, `5-7-8`
  - two-string pairs: `3-5`, `5-6`, `6-10`, `4-6`, `3-4`

G major:

- Default local view rendered G major rows.
- `All string groups` in G major / 3-string view rendered `34 validated rows`.
- Core grip row cards are labeled `Core grip`.
- Advanced rows are labeled `Advanced swap`.

G natural minor:

- Learner-facing scale display shows `G A Bb C D Eb F`.
- Bad canonical learner-facing sequence `G A A# C D D# F` was not present.
- Natural-minor row text uses flat spellings such as `Bb` and `Eb` where expected.

Mechanical/copedent labels:

- `F#`, `D#`, and `G#` appear in E9 tuning/row contexts.
- `Eb/D#` appears in per-string E-lower change details.

Core vs advanced grips:

- Core groups present in all-groups G major view:
  - `3-4-5`
  - `4-5-6`
  - `5-6-8`
  - `6-8-10`
- Advanced groups present in all-groups G major view:
  - `5-6-7`
  - `6-7-10`
  - `5-7-8`
- Row-card labels visually distinguish `Core grip`, `Advanced swap`, and `Advanced swap - E-lower pocket`.

`5-7-8`:

- Selecting `5-7-8` rendered `2 validated rows`.
- Both `5-7-8` rows were labeled `Advanced swap - E-lower pocket`.
- Both `5-7-8` rows used `advanced_pocket`.
- Both showed E-lower per-string change details with `String 8: E -> Eb/D#`.

Warnings and per-string details:

- Partial/diminished warning language is visible in row/card output for relevant natural-minor partial rows.
- Per-string pedal/lever changes are visible.

Regression checks:

- No `[object Object]` appeared.
- Local fallback did not imply RAG generated the Explorer positions; RAG is only mentioned in negated explanatory text.
- Existing shared frontend/fretboard tests passed.

## Console Errors

- Protected preview: not applicable; Explorer page was not reached because Cloudflare Access login blocked it.
- Local fallback: none observed.

## Mobile / Narrow Viewport Result

Tested local fallback at `390x844`.

Observed:

- No document-level horizontal overflow (`scrollWidth` matched `clientWidth`).
- Controls remained visible and usable-width.
- Fretboard region rendered.
- Row cards rendered.
- `G A Bb C D Eb F` remained available in page text.
- No `[object Object]`.
- No console errors.

## Automated Tests Run

```bash
git status --short
git branch --show-current
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/pedal-steel-fretboard.js
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest -q
```

Results:

- JS syntax checks: passed.
- `tests/test_pedal_steel_fretboard_ui.py -q`: 31 passed.
- `tests/test_frontend_answer_ui.py -q`: 22 passed.
- `tests/test_fretboard_explorer.py -q`: 11 passed.
- Full pytest: 790 passed.

`git diff --check` result is recorded after this handoff is written.

## Issues Found

Protected-preview issue:

- In-app browser was not authenticated through Cloudflare Access, so the exact protected-preview URL could not be verified.

Product/UI issues in local fallback:

- No functional Explorer UI issues found.
- Local static fallback logged missing `/brand/pedal-steel-fretboard-background.svg` requests. This should be verified in protected preview because local static serving from repo root may not match deployed static asset routing.

## Blockers

Protected-preview browser verification remains blocked until an authenticated browser session or Lane 12 protected-preview smoke can access the URL.

No blocker found in the local static Explorer surface behavior.

## Risks

Risk: medium until protected-preview access is verified.

Reasons:

- Local same-origin fallback verifies the committed static page behavior.
- It does not prove Cloudflare Access, protected-preview routing, deployment freshness, or cache behavior.
- Local fallback also does not prove deployed static asset routing for `/brand/pedal-steel-fretboard-background.svg`.

## Human Decision Needed

No product decision is needed.

Operational decision if protected-preview verification is required now:

- Run Lane 12 protected-preview smoke with an authenticated Cloudflare Access browser session, or explicitly approve Chrome browser fallback for this QA task.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-browser-smoke.md`

## Files That Must Not Be Staged

- Unrelated dirty/parked files shown by `git status --short`.
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores.
- embeddings.
- scraper outputs.
- deployment/auth/DNS files.
- source-inbox raw/provenance files.
- UI brand/design assets.
- generated/private data or reports.

## Recommended Next Step

Lane 12 protected-preview verification:

```text
Run ProtectedPreviewSmoke for https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622 from an authenticated Cloudflare Access browser session. Verify the Explorer page loads on protected preview, no console errors appear, and the local-passing Explorer checks match protected-preview behavior.
```

## Recommended Next Lane

Lane 12 Self-Hosted Deployment / protected-preview verification.

## Commit Readiness

Safe to commit the QA handoff only.
