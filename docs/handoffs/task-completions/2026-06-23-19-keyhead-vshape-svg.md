# 19 Visual Design / Assets - Keyhead V-Shape SVG

## Task summary

- What was requested: Adjust the leftmost pedal steel fretboard background SVG keyhead so the visible shell and 5-over/5-under tuner rows read as a real V/taper shape: widest near the roller nut and narrower moving left away from the neck.
- What was completed: Edited the standalone SVG used by `ui/pedal-steel-fretboard.js` at `public/brand/pedal-steel-fretboard-background.svg`. Only the intended `data-layer="headstock-keyhead-shell"` and `data-layer="10-tuning-keys"` SVG blocks were manually changed. The tuner rows now monotonically converge moving left away from the roller nut, with 5 tuners retained on the top side and 5 on the bottom side.
- What was intentionally not changed: Did not change SVG viewBox/dimensions, neck/fretboard position, roller nut, pickup, changer, body shell, strings, fret markers, answer UI, tab UI, prompt layout, API behavior, answer routing, source cards, corpus files, auth, deployment, DNS, embeddings, private materials, or unrelated dirty work.

## Files changed

- Changed files:
  - `public/brand/pedal-steel-fretboard-background.svg`
- Created files:
  - `docs/handoffs/task-completions/2026-06-23-19-keyhead-vshape-svg.md`
- Deleted files: None.
- Generated artifacts: None.

## Tests/checks run

- Exact commands run:
  - `test -f AGENTS.md && sed -n '1,240p' AGENTS.md || true`
  - `test -f agents.md && sed -n '1,240p' agents.md || true`
  - `test -f PLAN.md && sed -n '1,240p' PLAN.md || true`
  - `test -f plan.md && sed -n '1,240p' plan.md || true`
  - `sed -n '1,220p' README.md`
  - `test -f integration-status.md && sed -n '1,220p' integration-status.md || test -f docs/handoffs/task-completions/integration-status.md && sed -n '1,220p' docs/handoffs/task-completions/integration-status.md || true`
  - `git status --short`
  - `git diff --cached --name-only`
  - `rg -n "headstock-keyhead-shell|10-tuning-keys|pedal-steel-fretboard-background|DECORATIVE_BACKGROUND_HREF|keyhead|tuning" . --glob '*.svg' --glob '*.js' --glob '*.html'`
  - `git ls-files | rg 'pedal-steel-fretboard-background|fretboard.*\\.svg|brand/.*\\.svg'`
  - `sed -n '1,260p' public/brand/pedal-steel-fretboard-background.svg`
  - `git ls-files -- public/brand/pedal-steel-fretboard-background.svg ui/pedal-steel-fretboard.js`
  - `git status --short -- public/brand/pedal-steel-fretboard-background.svg ui/pedal-steel-fretboard.js`
  - Python XML parse/viewBox/layer count check for `public/brand/pedal-steel-fretboard-background.svg`
  - Python XML parse/tuner-count/tuner-coordinate check for `public/brand/pedal-steel-fretboard-background.svg`
  - `curl -I 'http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?access=beta_user&v=keyhead-vshape'`
  - `curl -I 'http://127.0.0.1:8770/brand/pedal-steel-fretboard-background.svg'`
  - Browser smoke at `http://127.0.0.1:8770/brand/pedal-steel-fretboard-background.svg`
  - Browser smoke at `http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?access=beta_user&v=keyhead-vshape`
  - `git check-ignore -v public/brand/pedal-steel-fretboard-background.svg || true`
  - `git log --all --name-only --oneline -- public/brand/pedal-steel-fretboard-background.svg`
  - `git diff --check`
  - `node --check ui/pedal-steel-fretboard.js && node --check ui/answer-client.js`
- Results:
  - Current branch/worktree guidance inspected.
  - Index was clean at task start: `git diff --cached --name-only` returned no paths.
  - Asset used by the component is standalone SVG via `DECORATIVE_BACKGROUND_HREF = "/brand/pedal-steel-fretboard-background.svg"`.
  - Important repo caveat: `public/brand/pedal-steel-fretboard-background.svg` is untracked in this checkout and has no history from `git log --all --name-only --oneline -- public/brand/pedal-steel-fretboard-background.svg`; it is not ignored by `git check-ignore`.
  - SVG parse passed.
  - SVG `viewBox` remained unchanged: `0 0 1600 420`.
  - SVG still has no explicit `width` or `height` attributes.
  - Tuner counts remain `top: 5`, `bottom: 5`.
  - Top tuner row y-values by x coordinate are `[135, 125, 115, 105, 95]`, converging upward toward the roller nut.
  - Bottom tuner row y-values by x coordinate are `[271, 281, 291, 301, 311]`, converging downward toward the roller nut.
  - `git diff --check`: passed.
  - `node --check ui/pedal-steel-fretboard.js && node --check ui/answer-client.js`: passed.
- Tests skipped and why:
  - No automated UI test suite was run because this is a scoped static SVG asset change.
  - No protected-preview smoke was run; per prompt, Lane 12 should run protected-preview smoke after commit.

## Visual smoke result

- Standalone asset URL tested: `http://127.0.0.1:8770/brand/pedal-steel-fretboard-background.svg`.
- Result: Browser visual inspection passed for the asset itself. The head no longer reads as a midpoint diamond/hourglass; the top and bottom tuner rows converge leftward away from the roller nut; 5 tuners remain on each side; the neck, fretboard panel, roller nut, pickup, changer, and body shell remained visually in place.
- Requested app URL tested: `http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?access=beta_user&v=keyhead-vshape`.
- Result: URL loaded with `200 OK`, but the current local page state kept `#answer-fretboard` hidden (`svgCount: 0`, `backgroundCount: 0`). This confirms local page availability but not embedded fretboard rendering. The meaningful visual inspection for this slice was the standalone SVG asset route.

## Risks

- Low to medium.
- Why: The edit is visually scoped to the keyhead/tuner SVG blocks, with no UI code or coordinate model changes. Risk is elevated only because the used SVG asset is currently untracked in this checkout, so normal `git diff` cannot prove a tracked-file delta or historical baseline.
- Rollback notes: Restore `public/brand/pedal-steel-fretboard-background.svg` from the previous untracked copy/backups if available, or revert the two edited SVG groups to the prior geometry from the previous handoff/backing artifact.

## Human decision needed

- Yes for Repo Steward: decide whether the currently untracked `public/brand/pedal-steel-fretboard-background.svg` should be added/staged as the approved asset path, since it is used by the app but not tracked at this checkout.

## Safe-to-stage files

- `public/brand/pedal-steel-fretboard-background.svg`
- `docs/handoffs/task-completions/2026-06-23-19-keyhead-vshape-svg.md`

## Files that must remain unstaged

- All unrelated dirty/untracked files reported by `git status --short`.
- Specifically do not stage unrelated docs, corpus metadata, source-inbox metadata, root RAG scripts, `ui/brand/` landing/sign assets, `deploy/landing/brand/` assets, `public/brand/` assets other than `public/brand/pedal-steel-fretboard-background.svg`, `Neon Sign/`, `data/`, private/generated helpers, Chroma/vector stores, embeddings, auth/deployment/DNS files, or integration-status files unless a later lane explicitly approves them.

## Commit readiness

Needs human review first

## Recommended next lane

- Next lane: 01 Repo Steward.
- Recommended prompt: Run exact-path commit hygiene for `public/brand/pedal-steel-fretboard-background.svg` and `docs/handoffs/task-completions/2026-06-23-19-keyhead-vshape-svg.md`. Confirm no unrelated files are staged, account for the untracked-asset caveat, run `git diff --cached --name-only`, `git diff --cached`, and `git diff --cached --check`, then commit only if the scoped asset/handoff diff is acceptable.

After Repo Steward commit, run Lane 12 protected-preview smoke for the user-facing visual asset change, then user smoke on a cache-busted protected-preview URL, then refresh `docs/handoffs/task-completions/integration-status.md`.
