# Answer Badge Cache-Bust Fix

## Task Summary

The updated answer badge fallback image existed in both `public/brand/` and `ui/brand/`, and the local server returned the new PNG bytes. The answer page still referenced the fallback PNG without a query string, so browser/CDN caching could keep showing the old fallback on the answer page.

Completed a scoped UI cache-bust fix for the answer badge asset references only.

## Files Changed

- `ui/steel-guitar-rag-mock.html`
  - Added `?v=answer-badge-rag-artwork-3c4dedb` to the answer badge WebM source, PNG poster, and PNG fallback image.
- `tests/test_frontend_answer_ui.py`
  - Updated the answer badge asset assertions to require the cache-busted URLs.

## Tests And Checks

- `git diff --check` passed.
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` passed: `20 passed`.
- `curl -I http://127.0.0.1:8770/ui/brand/steel-guitar-rag-answer-badge-fallback-alpha.png?v=answer-badge-rag-artwork-3c4dedb` returned `200 OK`, `Content-Type: image/png`, `Content-Length: 574413`.
- Local HTML now contains cache-busted answer badge URLs.

## Smoke Target

- Target type: local
- Result type: browser asset/path verification
- Exact browser URL tested: `http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html`
- Cache-busted URL tested: `http://127.0.0.1:8770/ui/brand/steel-guitar-rag-answer-badge-fallback-alpha.png?v=answer-badge-rag-artwork-3c4dedb`
- Exact URL the user should use: `https://app.steelguitarrag.com/` after the pushed commit is served
- Auth required: local no; protected preview yes
- Auth provider: local none; protected preview Cloudflare Access
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: cache-bust commit or later
- Version endpoint result: not checked for this local asset-path fix
- Root URL status: not reverified in browser
- API fallback status: not applicable

## Integration Notes

- No image/video bytes changed in this fix; those were already committed in `3c4dedb`.
- This fix makes the answer page request the updated answer badge fallback PNG and WebM using explicit cache-busted URLs.
- Unrelated landing-sign cachebuster hunks in the same HTML/test files were intentionally left unstaged.

## Risk Assessment

Low. This is a static URL cache-bust change for already-existing assets. No backend, auth, corpus, deployment config, or schema files changed.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `ui/steel-guitar-rag-mock.html` answer badge URL hunk only
- `tests/test_frontend_answer_ui.py` answer badge assertion hunk only
- `docs/handoffs/task-completions/2026-06-18-1846-01-answer-badge-cache-bust-fix.md`

## Files That Must Not Be Staged

- Unrelated landing-sign cachebuster hunks in `ui/steel-guitar-rag-mock.html`
- Unrelated landing-sign cachebuster hunks in `tests/test_frontend_answer_ui.py`
- `public/brand/steel-guitar-rag-answer-badge-alpha-master.mov`
- Any corpus/private/source/deployment/auth/generated files

## Recommended Next Lane

Lane 12 only if protected-preview freshness needs verification.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Verify the protected preview after the cache-bust commit is available:

```text
Lane 12: verify https://app.steelguitarrag.com/ after Cloudflare Access login and confirm the answer badge fallback PNG request includes ?v=answer-badge-rag-artwork-3c4dedb.
```
