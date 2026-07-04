# 2026-07-04 12:00 - Lane 12 - Voicing Identifier Hardening Protected Smoke

## Task Summary

Ran protected-preview browser smoke for the Voicing Identifier hardening/cache-bust commits.

Completed:
- Verified the protected Explorer page loads the fresh `voicing-identifier-hardening-20260704` script cache-busts.
- Verified the 5-7-8 open G Voicing Identifier case renders as a no-3rd color voicing, not a plain G chord.
- Verified protected root and app shell behavior.

Intentionally not changed:
- No files were modified during smoke before this handoff/status documentation.
- No restart, deployment, DNS, auth, corpus, Chroma/vector, embedding, scraper, private data, or asset changes.

## Files Changed

- `docs/handoffs/task-completions/2026-07-04-1200-12-voicing-identifier-hardening-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

Deleted files: none.

Generated artifacts: none.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-identifier-hardening-380f942`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-identifier-hardening-380f942`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-identifier-hardening-380f942`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded / already authenticated in the in-app browser
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: implementation/cache-bust commits through `380f942`; docs status refresh through `57e5312`
- Version endpoint: `https://app.steelguitarrag.com/api/version`
- Version endpoint result: browser navigation blocked with `net::ERR_BLOCKED_BY_CLIENT`
- If version endpoint missing, how version is inferred: protected page script URLs loaded `e9-music-rules.js?v=voicing-identifier-hardening-20260704` and `e9-fretboard-explorer.js?v=voicing-identifier-hardening-20260704`
- Whether app root `/` works: yes, redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes, current behavior is app-shell redirect with query string dropped
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user
- Do not test these URLs: uncache-busted Explorer URLs for this change
- Known caveats: `/api/version` could not be read through the browser; protected smoke is static/browser proof at the exact cache-busted URL, not strict runtime version proof.

## Protected Smoke Result

Pass with version-endpoint caveat.

Verified on `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-identifier-hardening-380f942`:
- Page loaded after Cloudflare Access-authenticated session.
- Script URLs included:
  - `e9-music-rules.js?v=voicing-identifier-hardening-20260704`
  - `e9-fretboard-explorer.js?v=voicing-identifier-hardening-20260704`
- Voicing Identifier 5-7-8 open G at fret 3 rendered:
  - `G5/add9(no3)`
  - `Color voicing / no 3rd`
  - omitted `3rd (B)`
  - no-3rd warning text
- It did not render `G chord: D, A, G`.
- It did not render `G5/add9(no3) chord` in the active result header.
- No `[object Object]`.
- No relevant console errors or warnings.

Root/app-shell checks:
- `https://app.steelguitarrag.com/?v=voicing-identifier-hardening-380f942` redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html` and dropped the query string.
- `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=voicing-identifier-hardening-380f942` loaded the app shell with no `[object Object]` and no relevant console errors.

## Tests and Checks

Previously passed for the implementation/cache-bust slice:

```bash
node --check ui/e9-music-rules.js
node --check ui/e9-fretboard-explorer.js
node --check ui/pedal-steel-fretboard.js
.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q
.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q
git diff --check
```

This smoke handoff is docs-only; `git diff --check` was run before staging.

## Integration Notes

- User smoke can use the direct Explorer URL above.
- This smoke does not require an API fallback and does not claim API fallback as browser proof.
- If strict runtime SHA proof is required, Lane 12 should use a version endpoint path that is not blocked by the browser extension or verify local `/api/version` after a documented protected-preview restart.

## Risk Assessment

Risk: low.

Why:
- The protected page loaded the current static cache-busted scripts and the exact target case passed.
- Remaining caveat is only strict `/api/version` access from the browser.

Rollback notes:
- Revert commits `380f942` and `91955e0` if the UI hardening needs to be backed out.

## Human Decision Needed

No.

## Safe-to-Stage Exact File List

- `docs/handoffs/task-completions/2026-07-04-1200-12-voicing-identifier-hardening-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- All unrelated parked dirty/untracked files.

## Recommended Next Lane

User smoke against:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-identifier-hardening-380f942
```

## Commit Readiness

Safe to commit.
