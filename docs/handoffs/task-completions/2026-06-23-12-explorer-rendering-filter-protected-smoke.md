# Lane 12 - Explorer Rendering Filter Protected Smoke

## Task Summary

Requested Lane 12 protected-preview verification for the committed Explorer rendering/filter fix at `283468b fix: restore explorer filter rendering`.

Completed:
- Confirmed the runtime was stale at `f2581f8`, refreshed the launchd-supervised protected-preview app process, and verified `/api/version` now reports `283468b`.
- Verified the authenticated protected-preview Explorer URL loads with the expected cache-busted scripts.
- Verified the Explorer filter/rendering states from Lane 15 against the protected preview.
- Verified the canonical app page and root redirect behavior.
- Ran focused app prompt spot-checks for static grip, movement, and blocked full-song tab behavior.

Intentionally not changed:
- No backend, frontend, Explorer data, corpus, Chroma/vector stores, embeddings, scraping, DNS, Cloudflare Access policy, secrets, or tunnel configuration.
- No API fallback was used as a browser-smoke substitute.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=283468b`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=283468b`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=283468b`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; browser was already authenticated and did not land on the Access login page.
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `283468b`
- Version endpoint: `/api/version`
- Version endpoint result: `git_sha=283468b`, `git_branch=feature/answer-api`, `auth_provider=cloudflare_access`, `retrieval_mode=hybrid_private_first`, `server_started_at=2026-06-23T22:54:31.633782+00:00`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, it redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes, as a redirect to the canonical app page
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: both Codex and the user
- Do not test these URLs: stale cache-bust URLs from prior Explorer slices
- Known caveats: root redirects to `/ui/steel-guitar-rag-mock.html` and drops the query string; use direct `/ui/...` URLs when preserving a cache-bust matters.

## Runtime And Deployment Evidence

- Branch: `feature/answer-api`
- Starting HEAD: `283468b`
- Runtime before refresh: `/api/version` reported stale `f2581f8`
- Runtime after refresh: `/api/version` reported `283468b`
- Listener: Python process on `127.0.0.1:8770`
- Listener PID after refresh: `90810`
- Listener start time: `Tue Jun 23 17:54:31 2026`
- LaunchDaemon: `com.steelguitarrag.private-preview` running
- App command: `scripts/serve_v2_rerank_smoke.py --host 127.0.0.1 --port 8770 ... --answer-auth-mode production --auth-provider cloudflare-access`
- Cloudflare Tunnel: process present; token contents intentionally not recorded

## Explorer Browser Smoke

URL tested:
- `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=283468b`

Result: Pass.

Observed:
- Page title: `E9 Fretboard Explorer - Steel Guitar RAG`
- Cloudflare Access login: succeeded/already authenticated
- Script cache-busts:
  - `pedal-steel-fretboard.js?v=explorer-render-fix-20260623`
  - `e9-fretboard-explorer-data.js?v=explorer-render-fix-20260623`
  - `e9-fretboard-explorer.js?v=explorer-render-fix-20260623`
- Stale `explorer-ui-cleanup-20260623` cache-bust was not present.
- Expanded key selector exposed the expected validated key set.
- Key, scale, and harmony controls were aligned at the same top position and height.
- The string group control rendered below the top controls.
- Learner copy for the `5&8 branch` and advanced swaps was present.
- No visible raw `five_eight_branch` label appeared in page text.
- No `[object Object]`.
- No browser console errors recorded.

Filter/rendering checks:

| State | Expected cards | Actual cards | Expected SVG highlights | Actual SVG highlights | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| G major, 3-string all | 34 | 34 | 34 | 34 | Pass |
| G major, 2-string all | 44 | 44 | 44 | 44 | Pass |
| G major, 2-string `5-8` | 4 | 4 | 4 | 4 | Pass |
| Switch back to 3-string all | 34 | 34 | 34 | 34 | Pass |

Additional filter notes:
- The `5-8` option appeared under `2-string groups`, not as a separate `5&8` optgroup.
- Switching from `2-string` / `5-8` back to `3-string diatonic harmony` reset the group selection to `all`.
- The 5-8 rows rendered as advanced branch/pocket positions.

## Main App And Root Smoke

Canonical app URL tested:
- `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=283468b`

Root URL tested:
- `https://app.steelguitarrag.com/?v=283468b`

Result: Pass.

Observed:
- Canonical app page loaded through Cloudflare Access.
- Q&A input was present; app-level Backstage unlock control worked.
- `Explore Fretboard` link was present.
- Link target: `/ui/e9-fretboard-explorer.html`
- Root redirected to `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html` and dropped the query string.
- No `[object Object]`.
- No browser console errors recorded.

## Prompt Spot Checks

These were browser checks through the protected-preview app UI, not API fallback.

| Prompt | Result | Notes |
| --- | --- | --- |
| `Show me a G major grip.` | Pass | Direct prose appeared. Fretboard/SVG rendered. One visible position card. No visible tab block. No generic fallback. |
| `Show me a G to C move.` | Pass | Direct prose appeared. Deterministic tab block rendered. Fretboard/SVG rendered with two position cards. No generic fallback. |
| `Give me the full tab for a modern copyrighted song.` | Pass | Refused full copyrighted song tab. No tab block. No fretboard. No generic fallback. |

Source-note caveat:
- Source-free responses still render the UI's `Source notes / No sources returned` section. This is not a populated source-card leak, but it remains visible on source-free answers.

## Files Changed

Created:
- `docs/handoffs/task-completions/2026-06-23-12-explorer-rendering-filter-protected-smoke.md`

Modified implementation files:
- None

Deleted files:
- None

Generated artifacts:
- None

## Tests And Checks Run

- `git status --short` - reviewed; unrelated dirty and untracked files remain parked.
- `git branch --show-current` - `feature/answer-api`
- `git rev-parse --short HEAD` - `283468b`
- `git log -1 --oneline` - `283468b fix: restore explorer filter rendering`
- `curl -sS http://127.0.0.1:8770/api/version` - confirmed runtime `283468b` after refresh.
- `lsof -nP -iTCP:8770 -sTCP:LISTEN` - confirmed Python listener on `127.0.0.1:8770`.
- `ps -p "$(lsof -tiTCP:8770 -sTCP:LISTEN)" -o pid,lstart,command` - confirmed PID `90810` and start time.
- `launchctl print system/com.steelguitarrag.private-preview` - confirmed launchd service running.
- `deploy/macos/install-private-preview-launchdaemon.sh version` - before refresh showed stale runtime `f2581f8`.
- `deploy/macos/install-private-preview-launchdaemon.sh status` - could not complete because non-interactive sudo required a password.
- Browser smoke at protected Explorer URL - pass.
- Browser smoke at protected app URL - pass.
- Browser smoke at protected root URL - pass, redirects to canonical app page.
- `git diff --check` - pass.

Skipped:
- Full pytest was not run because this task was protected-preview verification and no implementation files were changed.

## Integration Notes

- Protected preview is now serving runtime commit `283468b`.
- Explorer rendering/filter state from Lane 15 is verified in the authenticated protected preview.
- The root URL is usable as an entry point but redirects to `/ui/steel-guitar-rag-mock.html` and drops query strings.
- Use direct cache-busted `/ui/...` URLs for precise cache validation.
- No corpus, Chroma, embedding, scraping, DNS, auth, or Cloudflare policy changes were made.

## Risk Assessment

Risk: Low.

Reason:
- Only a docs handoff was created.
- Runtime action was limited to refreshing a stale launchd-supervised protected-preview process so it served the already-committed HEAD.
- No product logic, data, auth policy, DNS, or tunnel configuration was modified.

Rollback:
- If protected preview must be returned to a prior runtime, restart the launchd service from the desired committed checkout. No code rollback was performed by this task.

## Human Decision Needed

No.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-23-12-explorer-rendering-filter-protected-smoke.md`

## Files That Must Not Be Staged

Do not stage unrelated dirty or untracked files, including:
- `README.md`
- `corpus_metadata/source_policies/README.md`
- `corpus_metadata/source_registry.json`
- `docs/answer-eval-report.md`
- `docs/cloudflare-pages-landing.md`
- `docs/copyright-provenance.md`
- `docs/corpus-license-policy.md`
- `docs/current-commands.md`
- `docs/source-inbox-inventory.md`
- `rag_answer.py`
- `rag_build_clean_corpus.py`
- `rag_chunk_corpus.py`
- `rag_embed_chroma.py`
- `source-inbox/inventory.json`
- `ui/brand/*`
- `public/brand/*`
- `corpus-private/`
- `corpus-v2/`
- Chroma/vector stores
- embeddings
- scraper output
- credentials or env files
- any untracked parked handoffs/assets not named in the safe-to-stage list

## Recommended Next Lane

Lane 01 Repo Steward if integration status should be refreshed after this protected-preview pass.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Lane 01: refresh `docs/handoffs/task-completions/integration-status.md` with the `283468b` Explorer rendering/filter protected-preview pass, preserving unrelated parked work.
