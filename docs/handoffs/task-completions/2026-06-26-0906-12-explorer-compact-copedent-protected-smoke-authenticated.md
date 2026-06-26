# Lane 12 - Compact Explorer Copedent Protected Smoke Authenticated

## Task Summary

Reran protected-preview browser smoke for the compact E9 Fretboard Explorer copedent UI after Cloudflare Access authentication was completed in the in-app browser.

Completed:

- Verified repo/runtime state for `feature/answer-api`.
- Confirmed current HEAD `662679f` contains required UI commit `5a59739`.
- Confirmed local runtime `/api/version` reports `4040a47`, not stale `ffac52a`.
- Ran authenticated browser smoke at the exact protected Explorer URL.
- Refreshed `integration-status.md` with the authenticated result.

Intentionally not changed:

- No app runtime/UI/backend code.
- No DNS, Cloudflare Access policy, secrets, auth policy, scraping, embeddings, Chroma/vector stores, raw corpus, or private transcript files.
- No API fallback was reported as browser smoke.

## Smoke Target

```text
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625
- Cache-busted URL tested: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625
- Exact URL the user should use: https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected UI code commit: 5a59739
- Expected git HEAD: 662679f
- Version endpoint: http://127.0.0.1:8770/api/version
- Version endpoint result: git_sha=4040a47, git_branch=feature/answer-api, auth_provider=cloudflare_access, retrieval_mode=hybrid_private_first
- If version endpoint missing, how version is inferred: not applicable
- Whether runtime HEAD contains 5a59739: yes
- Whether app root `/` works: unauthenticated root returns Cloudflare Access 302; authenticated root browser check was limited by browser automation attach loss after Explorer smoke
- Whether app root `/` is expected to work: yes, with redirect to app UI; direct `/ui/...?...` remains preferred for exact cache-busted Explorer smoke
- Whether `/ui/e9-fretboard-explorer.html` works: yes
- Whether `/ui/e9-fretboard-explorer.html` is expected to work: yes
- Who should test this URL: the user
- Do not test these URLs: uncache-busted Explorer URL for this slice if validating fresh assets
- Known caveats: direct `/ui/...?...` URL remains the canonical cache-busted smoke target; temporary-tab browser automation detached after the UI smoke while checking version/root behavior
```

## Protected Smoke Results

Overall result: **PASS with tooling caveat**.

Verified in authenticated protected-preview browser:

- Page loaded at the exact cache-busted Explorer URL.
- Page title identified `E9 Fretboard Explorer`.
- Cloudflare Access was already satisfied; page did not show Access login, verification-code, or sign-in text.
- Explorer scripts loaded with `?v=explorer-compact-copedent-20260625`.
- Compact controls rendered:
  - Key selector.
  - E9 setup selector.
  - Scale selector.
  - Harmony/view selector.
  - Multi-select string group selector.
- `Emmons E9` was selected by default.
- `Custom E9 (with LKV)` existed as a selectable setup.
- `My Copedent (E9) - Coming soon in Backstage` existed and was disabled.
- `Core grips` and `Advanced swaps` remained visually/data separated in the string-group selector.
- `5-7-8` appeared only under the advanced swaps group.
- `Showing validated positions` appeared.
- Raw `N validated rows` primary copy did not appear.
- No `E-lower+E-lower` duplicate label appeared.
- No visible `[object Object]`.
- No relevant browser console errors were captured.
- No horizontal overflow was detected.

## Interaction Results

Explorer interactions passed:

- `View chart` opened the selected setup chart.
- Chart close button closed the chart.
- With `Emmons E9`, the chart showed strings 1-10 and did not expose the LKV/B-to-Bb custom setup.
- String-group filtering changed the visible card list to `4-5-6`; resetting to `All 3-string groups` restored the larger result set.
- Pedal/lever impact preview was compact and interactive; selecting `A pedal` changed the selected control detail.
- Notes / Intervals toggle worked:
  - Notes mode showed note marker labels such as `G D B`.
  - Intervals mode showed interval marker labels such as `1 5 3`.
- Fretboard SVG rendered. On reload at the current authenticated browser viewport (`831x874`), the SVG was present and partially visible at the fold with no horizontal overflow.
- Fretboard marker labels did not combine fret number with note/interval text in a single marker label; fret numbers remained separate axis labels.

## Root Behavior

- Unauthenticated `curl -I https://app.steelguitarrag.com/?v=explorer-compact-copedent-20260625` returned HTTP `302` to Cloudflare Access, confirming root remains protected.
- Authenticated root behavior was not fully rechecked in-browser in this rerun because the browser automation session detached after the Explorer smoke while opening temporary tabs for `/api/version` and root checks.
- This does not invalidate the Explorer browser smoke; it does mean root behavior should continue to be treated as secondary to the direct `/ui/e9-fretboard-explorer.html?...` cache-busted URL for this slice.

## Files Changed

- `docs/handoffs/task-completions/2026-06-26-0906-12-explorer-compact-copedent-protected-smoke-authenticated.md`
- `docs/handoffs/task-completions/integration-status.md`

No app/runtime code changed.

## Tests And Checks Run

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git merge-base --is-ancestor 5a59739 HEAD
curl -sS http://127.0.0.1:8770/api/version
git diff --check
git diff --cached --name-only
curl -sSI 'https://app.steelguitarrag.com/?v=explorer-compact-copedent-20260625' | sed -n '1,12p'
```

Results:

- Branch: `feature/answer-api`.
- Current HEAD: `662679f`.
- Required UI commit `5a59739` is an ancestor of current HEAD.
- Runtime `/api/version`: `4040a47`, branch `feature/answer-api`, auth provider `cloudflare_access`, retrieval mode `hybrid_private_first`.
- Runtime is not stale `ffac52a`.
- `git diff --check`: passed.
- Index was empty before staging.
- Root unauthenticated header check: HTTP `302` to Cloudflare Access.

Browser checks:

- Authenticated protected Explorer smoke passed as browser smoke.
- Console error/warning capture returned no entries during the final Explorer check.

## Integration Notes

- Runtime `4040a47` is acceptable for this smoke because it contains `5a59739`; the later repo HEAD `662679f` is docs-only follow-up work.
- Use the direct Explorer URL for user smoke:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625
```

- Root remains protected by Cloudflare Access. For exact Explorer cache-busting, do not rely on root redirect behavior.

## Risk Assessment

Risk: **low**.

Why:

- No app/runtime code was modified.
- Protected browser smoke reached and interacted with the authenticated Explorer page.
- Runtime was confirmed fresh enough for the UI commit under test.

Residual risk:

- Browser automation detached during temporary-tab root/version checks after the Explorer smoke. Root authenticated behavior was not fully rechecked in-browser during this rerun.
- Broad unrelated dirty/untracked files remain parked in the worktree and must not be broad-staged.

Rollback notes:

- No runtime changes were made.
- If the user reports Explorer regressions, route UI issues back to Lane 06 and runtime/version issues back to Lane 12.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-26-0906-12-explorer-compact-copedent-protected-smoke-authenticated.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- Backend/runtime files.
- UI implementation files.
- Tests.
- Deployment/launchd files.
- Auth/DNS/Cloudflare config.
- Corpus, Chroma/vector stores, embeddings, scraper output, raw/private source files.
- Unrelated docs, assets, generated reports, and parked handoffs.

## Recommended Next Lane

User smoke, then Lane 01 if integration status needs another formal refresh after user feedback.

## Commit Readiness

Safe to commit.

## Suggested Next Step

User smoke the compact Explorer copedent UI at:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625
```
