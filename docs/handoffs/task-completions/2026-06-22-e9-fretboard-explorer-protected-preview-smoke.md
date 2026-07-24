# E9 Fretboard Explorer Protected Preview Smoke

## Task Summary

Lane: 12 Self-Hosted Deployment / Protected Preview

Requested:
- Verify the exact protected-preview E9 Fretboard Explorer URL after Lane 15 local smoke passed but protected-preview smoke was blocked by Cloudflare Access.
- Use an authenticated Cloudflare Access browser session.
- Do not modify app code, corpus, embeddings, Chroma, scraper output, auth config, DNS, deployment config, assets, or private source data.

Completed:
- Read the required E9 Explorer handoffs and current integration status.
- Confirmed branch and current repo HEAD.
- Confirmed `/api/version` reports a runtime commit that contains the Explorer surface.
- Used the authenticated in-app browser session to smoke the exact protected-preview Explorer URL.
- Verified the Explorer controls, G major rows, G natural-minor spelling, E9 mechanical spellings, advanced `5-7-8` E-lower pocket, warnings/per-string details, protected asset loading, app mock entry link, console status, and narrow viewport.
- Ran the requested automated checks.

Intentionally not changed:
- No implementation files.
- No backend, UI, auth, DNS, deployment config, assets, corpus, embeddings, Chroma, scraper output, source-inbox, private source data, or vector data.
- No protected-preview restart or deployment was performed.

Historical note:
- An earlier Lane 12 attempt in this same handoff was blocked because the in-app browser landed on Cloudflare Access login and Chrome browser control was unavailable. The authenticated rerun below supersedes that blocked result.

## Pass / Warn / Fail

**Pass.**

The exact protected-preview Explorer URL loaded in an authenticated Cloudflare Access browser session and matched the expected local-smoke behavior.

## Smoke Target

- Target type: protected-preview
- Result type: authenticated browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; the in-app browser loaded the Explorer page, not the Access login page
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `a5389f2` or later containing `a5389f2` and `a9dfd70`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"7bb46b8","git_branch":"feature/answer-api","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not needed; endpoint exists
- Whether app root `/` works: not retested for this Explorer-specific smoke
- Whether app root `/` is expected to work: yes, but this task targets the direct Explorer URL
- Whether `/ui/steel-guitar-rag-mock.html` works: yes; checked to verify the `Explore the E9 Fretboard` entry
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user and Lane 12
- Do not test these URLs: local `127.0.0.1` as proof of protected-preview browser behavior; app root as a substitute for the Explorer URL
- Known caveats: current repo HEAD is `7bb46b8`, a docs-only smoke handoff commit on top of `a9dfd70`; runtime includes the Explorer implementation commit `a5389f2`

## Commit / Runtime Evidence

Branch:

```text
feature/answer-api
```

Current repo HEAD at task start:

```text
7bb46b8
```

Commits under test are present in recent history:

```text
7bb46b8 docs: record E9 explorer protected-preview smoke
a9dfd70 docs: record E9 explorer browser smoke
a5389f2 feat: add e9 fretboard explorer surface
```

`/api/version`:

```json
{
  "git_sha": "7bb46b8",
  "git_branch": "feature/answer-api",
  "server_started_at": "2026-06-22T19:43:46.515970+00:00",
  "python_module": "steel_guitar_rag.api",
  "retrieval_mode": "hybrid_private_first",
  "auth_provider": "cloudflare_access"
}
```

## Browser Smoke Results

Exact URL:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622
```

Authenticated page load:
- Passed.
- Browser title: `E9 Fretboard Explorer - Steel Guitar RAG`.
- Browser URL remained the exact protected-preview URL.
- Page entry/header identified `E9 Fretboard Explorer`.

Controls:
- Passed.
- Four selectors rendered:
  - `explorer-key`: `G only`.
  - `explorer-scale`: `G major`, `G natural minor`.
  - `explorer-harmony`: `2-string harmonized scale`, `3-string diatonic harmony`.
  - `explorer-string-group`: `All string groups`, core grips, advanced swaps, and 2-string pairs.

G major rows:
- Passed.
- Default G major / 3-string / `4-5-6` view rendered `8 validated rows`.
- Scale notes showed `G A B C D E F#`.
- Fretboard SVG mounted.

G natural minor spelling:
- Passed.
- Switching to `G natural minor` rendered `G A Bb C D Eb F`.
- Bad learner-facing sequence `G A A# C D D# F` was not present.
- Natural-minor rows used flat spellings such as `Bb` and `Eb`.

Sharp-oriented E9 mechanical labels:
- Passed.
- The page retained E9 tuning/mechanical spellings including `F#`, `D#`, and `G#`.
- In the `5-7-8` E-lower pocket details, per-string changes showed `Eb/D#`.

Core grips and advanced swaps:
- Passed.
- The string-group selector separates core grips from advanced swaps.
- Page explanatory text states core grips are separated from advanced swaps.

`5-7-8` advanced E-lower pocket:
- Passed.
- Switching back to `G major` and selecting `5-7-8` rendered `2 validated rows`.
- Both rows were labeled `ADVANCED SWAP - E-LOWER POCKET`.
- Rows appeared at frets `8` and `20`.
- Per-string details showed string 8 E-lower change: `from: E; to: Eb/D#`.

Partial diminished / partial m7b5 warnings:
- Passed.
- Warning text remained visible, including partial-warning language in natural-minor rows and the page note about partial diminished or partial m7b5 rows.

Per-string pedal/lever changes:
- Passed.
- The `5-7-8` E-lower pocket details showed per-string changes.

`[object Object]`:
- Passed.
- No `[object Object]` appeared in the Explorer page, natural-minor view, advanced-pocket view, mobile view, or mock-entry check.

Landing/app mock entry:
- Passed.
- `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-browser-surface-20260622` contained the link text `Explore the E9 Fretboard`.
- The link target was `e9-fretboard-explorer.html`.

## Asset Routing Result

Protected-preview page asset inventory showed:

```text
https://app.steelguitarrag.com/ui/pedal-steel-fretboard.js?v=e9-explorer-browser-surface-20260622
https://app.steelguitarrag.com/ui/e9-fretboard-explorer-data.js?v=e9-explorer-browser-surface-20260622
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.js?v=e9-explorer-browser-surface-20260622
https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg
```

The page asset inventory reported:

```text
scripts: 4
images: 2
stylesheet: 1
inline SVGs: 1
```

The inline SVG was named:

```text
10-string E9 pedal steel fretboard with highlighted positions
```

Result:
- Passed.
- The expected fretboard background asset loaded from the protected-preview hostname.
- The pedal-steel fretboard SVG mounted.

## Console Errors

Passed.

Browser console error logs for the Explorer page and mobile viewport were empty.

## Mobile / Narrow Viewport Result

Tested at `390x844`.

Result:
- Passed for MVP usability.
- Page title remained `E9 Fretboard Explorer - Steel Guitar RAG`.
- Page content still identified `E9 Fretboard Explorer`.
- All four controls were visible at `336px` width.
- No document-level horizontal overflow: `scrollWidth` was `390` and viewport width was `390`.
- Fretboard SVG remained present.
- No `[object Object]`.
- No console errors.

Caveat:
- The SVG itself measured wider than the viewport (`700px`) inside its scrollable/contained region, but it did not cause document-level horizontal overflow. This is acceptable for MVP protected-preview smoke.

## Automated Tests Run

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
node --check ui/e9-fretboard-explorer.js
node --check ui/e9-fretboard-explorer-data.js
node --check ui/pedal-steel-fretboard.js
node --check ui/answer-client.js
.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
.venv/bin/python -m pytest -q
git diff --check
```

Results:
- Branch: `feature/answer-api`.
- HEAD at task start: `7bb46b8`.
- JS syntax checks: passed.
- `tests/test_pedal_steel_fretboard_ui.py -q`: 31 passed.
- `tests/test_frontend_answer_ui.py -q`: 22 passed.
- `tests/test_fretboard_explorer.py -q`: 11 passed.
- Full pytest: 790 passed.
- `git diff --check`: passed after this handoff update.

## Files Changed

Modified:

- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-protected-preview-smoke.md`

No implementation files were changed.

## Issues Found

No protected-preview product issues found.

## Blockers

None for the E9 Fretboard Explorer protected-preview smoke.

## Risks

Risk: low.

Why:
- Exact protected-preview URL loaded after Cloudflare Access authentication.
- Runtime reports a commit containing the Explorer implementation.
- Browser smoke matched the local Lane 15 behavior.
- Automated checks passed.
- No code/config/deployment/auth/data changes were made.

Rollback notes:
- No runtime changes were made by this Lane 12 smoke.
- If a future issue appears, route UI/product behavior to Lane 06 and protected-preview runtime issues to Lane 12.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-22-e9-fretboard-explorer-protected-preview-smoke.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked files, especially:

- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings.
- `source-inbox/` raw/provenance files.
- `.wrangler/`, DNS/deployment/auth/secrets files.
- `public/`, `ui/brand/`, `Neon Sign/`, raw/generated design assets.
- Existing parked docs/corpus metadata/root RAG script changes.
- Any implementation files under `steel_guitar_rag/`, `ui/`, `scripts/`, or `tests` not explicitly scoped by a new handoff.

## Recommended Next Lane

Lane 01 Repo Steward, only if integration status should be refreshed with the E9 Explorer protected-preview pass.

## Commit Readiness

Safe to commit as a docs-only protected-preview smoke handoff update.

## Suggested Next Step

User smoke can continue on the exact Explorer URL:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-browser-surface-20260622
```
