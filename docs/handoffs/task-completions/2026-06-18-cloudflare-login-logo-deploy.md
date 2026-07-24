# 2026-06-18 Cloudflare Login Logo Deploy

## Task Summary

Requested:

- Publish the existing Cloudflare login logo PNG so the app origin can serve it at:
  `https://app.steelguitarrag.com/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`
- Do not modify auth policies, Cloudflare Access settings, app behavior, or existing brand assets.

Completed:

- Located the source PNG:
  `ui/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`
- Copied it into the served public asset pipeline:
  `public/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`
- Updated the same-origin/protected-preview static server to serve `/brand/*` from `public/brand/*`.
- Added a focused regression test for the new Cloudflare login logo asset route.
- Committed the deployment/static asset change:
  `e293212 deploy: publish cloudflare login logo asset`
- Restarted the protected-preview app on `127.0.0.1:8770` from commit `e293212`.
- Verified the origin route returns `200 OK` with `Content-Type: image/png`.

Intentionally not changed:

- No Cloudflare Access policy changes.
- No DNS changes.
- No auth behavior changes.
- No Cloudflare Tunnel config changes.
- No app answer/RAG behavior changes.
- No Chroma/vector, embeddings, corpus, source data, or scraping changes.
- Existing source image under `ui/brand/` was not altered.

Important result:

- The app origin now serves `/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`.
- The public unauthenticated URL still returns Cloudflare Access `302`, not `200`, because Cloudflare Access protects `app.steelguitarrag.com/brand/...`.
- Achieving unauthenticated public `200 image/png` requires a Cloudflare Access path bypass or equivalent policy/routing change, which this task explicitly forbade.

## Files Changed

Changed:

- `scripts/serve_answer_smoke.py`
- `tests/test_same_origin_smoke_server.py`

Created:

- `public/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`
- `docs/handoffs/task-completions/2026-06-18-cloudflare-login-logo-deploy.md`

Deleted:

- None.

Generated artifacts:

- None beyond the copied public PNG.

Unchanged source asset:

- `ui/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`

## Deployment Commands Used

Committed the deployment/static route change:

```bash
git add scripts/serve_answer_smoke.py tests/test_same_origin_smoke_server.py public/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png
git diff --cached --name-only
git diff --cached --check
git commit -m "deploy: publish cloudflare login logo asset"
```

Restarted protected preview:

```bash
lsof -tiTCP:8770 -sTCP:LISTEN | xargs kill 2>/dev/null || true
set -a
source ~/.steel-rag/env/private-preview.env
set +a
PYTHONPATH=. \
STEEL_RAG_AUTH_PROVIDER=cloudflare_access \
STEEL_RAG_ANSWER_AUTH_MODE=production \
STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first \
STEEL_RAG_ENABLE_PRIVATE_SOURCES=true \
STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma \
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 \
STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma \
STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 \
STEEL_RAG_RETRIEVAL_DEBUG=false \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --answer-auth-mode production \
  --auth-provider cloudflare-access
```

## Verification Output

Source and public PNG metadata:

```text
ui/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png: size=(400, 287) mode=RGBA extrema=((0, 255), (0, 255), (0, 255), (0, 255))
public/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png: size=(400, 287) mode=RGBA extrema=((0, 255), (0, 255), (0, 255), (0, 255))
bytes_equal= True
```

Runtime version after deploy:

```json
{"git_sha": "e293212", "git_branch": "feature/answer-api", "python_module": "steel_guitar_rag.api", "retrieval_mode": "hybrid_private_first", "auth_provider": "cloudflare_access"}
```

Local origin route:

```text
$ curl -sS -I http://127.0.0.1:8770/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png
HTTP/1.0 200 OK
Content-Type: image/png
Content-Length: 165636
```

Public protected-preview URL:

```text
$ curl -I https://app.steelguitarrag.com/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png
HTTP/2 302
location: https://late-waterfall-73da.cloudflareaccess.com/cdn-cgi/access/login/app.steelguitarrag.com...
www-authenticate: Cloudflare-Access resource_metadata="https://app.steelguitarrag.com/.well-known/cloudflare-access-protected-resource/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png"
```

Interpretation:

- Origin deployment: pass.
- Public unauthenticated `200 image/png`: blocked by Cloudflare Access policy.
- This is expected under the "do not modify Cloudflare Access settings" constraint.

## Tests And Checks

Commands run:

```bash
git status --short
file ui/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png
python3 - <<'PY'
from PIL import Image
from pathlib import Path
for p in [Path('ui/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png'), Path('public/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png')]:
    im = Image.open(p)
    print(f'{p}: size={im.size} mode={im.mode} extrema={im.getextrema()}')
print('bytes_equal=', Path('ui/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png').read_bytes() == Path('public/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png').read_bytes())
PY
.venv/bin/python -m py_compile scripts/serve_answer_smoke.py scripts/serve_v2_rerank_smoke.py
.venv/bin/python -m pytest tests/test_same_origin_smoke_server.py -q
git diff --check
curl -sS http://127.0.0.1:8770/api/version
curl -sS -I http://127.0.0.1:8770/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png
curl -I https://app.steelguitarrag.com/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png
```

Results:

- PNG dimensions/transparency preserved: `400 x 287`, `RGBA`, alpha channel present.
- Source and public PNG bytes identical: yes.
- `py_compile`: passed.
- `tests/test_same_origin_smoke_server.py`: 12 passed.
- `git diff --check`: passed.
- Local origin header check: `200 OK`, `image/png`.
- Public unauthenticated header check: `302` to Cloudflare Access login.

Skipped:

- Full pytest was not run; this was a narrow deployment/static asset route change.
- Browser smoke was not needed for the PNG route. Direct local and public header checks are stronger for this asset-only task.

## Smoke Target

Smoke Target:
- Target type: protected-preview
- Result type: API fallback, not browser smoke
- Exact browser URL tested: not applicable
- Cache-busted URL tested: not applicable
- Exact URL the user should use: `https://app.steelguitarrag.com/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`
- Auth required: yes under current Cloudflare Access policy
- Auth provider: Cloudflare Access
- Cloudflare Access login result: not attempted
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `e293212`
- Version endpoint: `/api/version`
- Version endpoint result: `git_sha=e293212`
- If version endpoint missing, how version is inferred: not needed
- Whether app root `/` works: not tested; not relevant to asset route
- Whether app root `/` is expected to work: yes for normal protected preview, but not part of this task
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested; not relevant to asset route
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both Codex and the user
- Do not test these URLs: do not use `/ui/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png` as the Cloudflare login logo URL; the requested URL is `/brand/...`
- Known caveats: unauthenticated public access is blocked by Cloudflare Access until Access policy/routing is changed

## Integration Notes

- `scripts/serve_answer_smoke.py` now supports `/brand/*` static assets from `public/brand/*`.
- `scripts/serve_v2_rerank_smoke.py` uses the shared `build_app`, so protected preview receives the same route.
- The route is static only; API/auth behavior is unchanged.
- The route is protected externally by Cloudflare Access on `app.steelguitarrag.com`.
- The requested final public URL cannot return unauthenticated `200 image/png` while Cloudflare Access protects that path.

## Risk Assessment

Risk: low for origin deployment; medium for the stated public URL requirement.

Why:

- Origin route is narrow and covered by a focused test.
- The public PNG is byte-identical to the source PNG.
- No auth or DNS settings were changed.
- The remaining public access issue is outside origin code and controlled by Cloudflare Access policy.

Rollback:

1. Revert commit `e293212`.
2. Restart protected preview from the previous known-good commit.
3. Verify `/api/version` and asset behavior.

## Human Decision Needed

Yes.

Decision:

- If the URL must be publicly reachable without Cloudflare Access login, approve a Lane 11/Auth or Cloudflare Access change to bypass Access for exactly:
  `/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`

No human decision is needed for the origin-side deployment; that part is complete.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-18-cloudflare-login-logo-deploy.md`

Already committed in `e293212`:

- `public/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`
- `scripts/serve_answer_smoke.py`
- `tests/test_same_origin_smoke_server.py`

## Files That Must Not Be Staged

- Existing parked dirty files outside this task.
- Cloudflare credentials, `.wrangler/`, env files, DNS/deployment secrets.
- Corpus, Chroma/vector stores, embeddings, source-inbox raw/provenance data, scraping outputs.
- Unrelated `ui/brand`, `public/brand`, `Neon Sign`, landing, docs, source registry, and RAG script changes.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 11 Auth / Security: decide whether to create a Cloudflare Access bypass for exactly `/brand/steel-guitar-rag-hanging-sign-cloudflare-login.png`, so Cloudflare's login page can fetch the image without requiring the same Access login it is trying to display.
