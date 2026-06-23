# 2026-06-23 - Lane 06 - Restore Backstage Button Font

## Task Summary

Requested: restore the previously accepted `Go Backstage` header button typography from git history and apply that same style to both upper-right header buttons.

Completed:
- Inspected `ui/steel-guitar-rag-mock.html` across candidate commits `1c0bbd6`, `2d3d662`, `5031f43`, `0c050ee`, `e1103be`, `fd342b9`, `b547178`, and `HEAD`.
- Identified `e1103be` / `1c0bbd6` as the last known-good pre-`fd342b9` style: `.backstage-trigger` had no explicit `font-family`, `font-size`, `font-weight`, `line-height`, or `letter-spacing`; it inherited the page/button typography.
- Removed the rejected `b547178` neutral system stack from `.header-action-button`.
- Removed explicit font size, weight, line-height, and letter-spacing from `.header-action-button` so both `Explore Fretboard` and `Go Backstage` inherit the same prior accepted typography.
- Preserved `Explore Fretboard` as a link to `/ui/e9-fretboard-explorer.html`.
- Preserved `Go Backstage` / backstage settings behavior on `.backstage-trigger`.

Intentionally not changed:
- App-wide `--font-ui` and page typography were not changed.
- Backend, Explorer data, prompt chips, auth, DNS, launchd, tunnel, corpus, Chroma, embeddings, scraping, secrets, private-source files, and unrelated dirty files were not touched.

## Pass / Warn / Fail

Pass with caveat.

Caveat: the restored prior accepted behavior inherits the app page font stack, whose root variable begins with `"Gill Sans", "Gill Sans MT"`. The shared header button rule itself no longer explicitly uses `Gill Sans`, `var(--font-ui)`, the rejected neutral stack, or a decorative/lesson font. This matches the historical Go Backstage implementation before `fd342b9`.

## Branch / HEAD

- Branch: `feature/answer-api`
- Starting HEAD: `ca38c81`
- Final HEAD / commit hash if committed: pending at handoff creation

## Exact Prior Commit / Style Used As Source Of Truth

Source commits inspected:
- `1c0bbd6 fix: separate backstage and fretboard header actions`
- `e1103be fix: clean up explorer controls and key labels`

Restored style source:
- `e1103be:ui/steel-guitar-rag-mock.html` lines around the header actions.
- Historical `.backstage-trigger` shared box styles included display, alignment, gap, min-height, padding, border, radius, background, color, cursor, and shadow.
- Historical `.backstage-trigger` did not set `font-family`, `font-size`, `font-weight`, `line-height`, or `letter-spacing`.

Rejected styles:
- `fd342b9` added explicit `font-family: var(--font-ui)`, `font-size: 14px`, `font-weight: 800`, `letter-spacing: 0`, and `line-height: 1` to the shared header button.
- `b547178` replaced that with the neutral `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` stack, which user smoke rejected.

## Files Touched

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-restore-backstage-button-font.md`

## What Changed

- `.header-action-button` no longer sets explicit typography beyond box/link behavior.
- Both header controls share the same inherited typography and same button style family.
- The focused frontend test now asserts `.header-action-button` does not include:
  - `font-family:`
  - `font-size:`
  - `font-weight:`
  - `line-height:`
  - `var(--font-ui)`
  - `var(--font-lesson)`
  - `Gill Sans`
  - the rejected neutral stack marker `-apple-system, BlinkMacSystemFont`

## Visual Smoke Result

Smoke target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8896/ui/steel-guitar-rag-mock.html?access=beta_user&v=restore-backstage-font-smoke`
- Cache-busted URL tested: same as above
- Auth required: no
- Auth provider: none
- Local backend URL: none, static `http.server`
- Expected backend port: not applicable
- Expected git HEAD: `ca38c81` before commit
- Version endpoint: not applicable to static smoke
- Whether app root `/` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Who should test this URL: Codex locally; Lane 12 should test protected preview next
- Known caveats: `/api/session` returned 404 under static server, expected for this smoke method and unrelated to header styling.

Computed browser style results:
- `Explore Fretboard` and `Go Backstage` had matching font family, size, weight, padding, radius, height, icon count, and top alignment.
- Shared `.header-action-button` CSS text did not contain an explicit `font-family`.
- Shared `.header-action-button` CSS text did not contain the rejected neutral stack.
- Both controls still rendered in the upper-right header area.
- `Explore Fretboard` still links to `/ui/e9-fretboard-explorer.html`.
- `Go Backstage` remains the backstage/settings button with `aria-controls="backstage"`.

## Checks Run

Passed:
- `git diff --check`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `node --check ui/e9-fretboard-explorer.js`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - 23 passed
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - 32 passed

## Risks

Risk: low to medium.

Reason:
- Code scope is small and restores the old Go Backstage typography mechanism.
- Product risk remains because the inherited app font stack includes Gill Sans at page level, even though that is the historical accepted behavior and no longer explicitly applied by the header button rule.

Rollback:
- Revert this commit to return to the rejected neutral-stack rule, or set a product-approved explicit font stack on `.header-action-button` in a follow-up.

## Blockers

None.

## Human Decision Needed

No for this requested restoration.

If the inherited app font stack is still rejected in user smoke, a product decision is needed for the exact desired explicit button font stack.

## Safe-To-Stage Exact File List

- `ui/steel-guitar-rag-mock.html`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-23-06-restore-backstage-button-font.md`

## Files That Must Remain Unstaged

- All unrelated parked files shown by `git status --short`, including README/docs/provenance/corpus/source-inbox changes, RAG helper scripts, `ui/brand/` files, `public/`, raw design assets, corpus/private/source-inbox data, generated reports, deployment/auth/DNS/secrets, and unrelated untracked files.

## Recommended Next Lane

Lane 12 Self-Hosted Deployment: protected-preview smoke for the restored header button font.

Then user smoke the header buttons.

## Commit Readiness

Safe to commit.

## Suggested Next Step

```text
Lane 12: Run protected-preview smoke for commit <commit> and verify both upper-right header buttons restored the prior Go Backstage typography behavior: Explore Fretboard opens /ui/e9-fretboard-explorer.html, and Go Backstage remains the backstage/settings control.
```
