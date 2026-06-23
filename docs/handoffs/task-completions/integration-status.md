# Integration Status - Current Reset Snapshot

Generated for ChatGPT reset/guidance on branch `feature/answer-api`.

## 2026-06-23 Deployment / Mac Mini Runtime Status

- Current branch: `feature/answer-api`.
- Current HEAD at this refresh: `564d29c fix: supervise mac mini app runtime`.
- Latest deployment/runtime commit chain:
  - `564d29c fix: supervise mac mini app runtime`
  - `5f8af79 docs: record fretboard svg cache-bust smoke`
  - `7ec5e3a fix: refresh explorer fretboard script cache-bust`
  - `c73abb8 docs: record fretboard svg in-page cache-bust smoke`
  - `64db66b fix: cache bust in-page fretboard background`
  - `7c36c49 docs: record current-head e9 explorer protected smoke`
  - `9562e90 fix: cache-bust fretboard background svg`
  - `00442ec docs: refresh e9 explorer integration status`
- Current priority: deployment wrap-up and protected-preview user-smoke readiness, not new product work.
- Dirty worktree: broad unrelated dirty/untracked work remains parked. Do not broad-stage.

### Mac Mini Reliability Status

- Origin model remains:
  - Internet -> Cloudflare Access -> Cloudflare Tunnel -> Mac mini app on `127.0.0.1:8770` -> local Chroma/Ollama.
- `2026-06-23-12-mac-mini-reliability-audit.md` found:
  - app process was manually started in a detached `screen` session named `steel-rag-private-preview`;
  - app listener was `127.0.0.1:8770`;
  - app logs were under `/tmp/steel-rag-private-preview-8770.log`;
  - no repo app LaunchAgent/LaunchDaemon was installed or loaded;
  - Cloudflare Tunnel was already boot-started by `/Library/LaunchDaemons/com.cloudflare.cloudflared.plist`;
  - Cloudflare Tunnel had durable `/Library/Logs/com.cloudflare.cloudflared.*.log` paths;
  - Cloudflare Tunnel uses inline token arguments in the host plist/process; token value was not printed and must stay out of docs/prompts;
  - FileVault was off;
  - AC sleep was enabled (`sleep 1`);
  - restart after power failure appeared disabled (`autorestart 0`, `autorestartatconnect 0`);
  - Ollama was running but boot supervision was not proven.
- `564d29c` added repo-managed, non-secret launchd assets:
  - `deploy/macos/com.steelguitarrag.private-preview.plist.template`;
  - `deploy/macos/run-private-preview-app.sh`;
  - `deploy/macos/install-private-preview-launchdaemon.sh`;
  - `docs/mac-mini-private-preview-launchd.md`;
  - `docs/handoffs/task-completions/2026-06-23-12-mac-mini-launchd-runtime-hardening.md`.
- Deployment hardening status: **partial**.
  - Repo-managed service assets and durable app log paths are implemented and committed.
  - The app is not proven installed/loaded as a LaunchDaemon.
  - Protected-preview smoke has not been run from a supervised launchd process.
  - Mac sleep/restart-after-power-loss and Ollama boot supervision remain unresolved operational caveats.

### Cloudflare Tunnel Status

- Cloudflare Tunnel remains the documented protected-preview ingress.
- Audit evidence indicates `/Library/LaunchDaemons/com.cloudflare.cloudflared.plist` exists with `RunAtLoad=True` and `KeepAlive={'SuccessfulExit': False}`.
- Tunnel boot-start status: likely yes, based on launchd metadata and root-owned running process observed in the audit.
- Tunnel hardening still pending:
  - inline tunnel token should eventually be migrated/rotated through a separate Lane 11/Lane 12 security task;
  - no tunnel token, credential, DNS, or Cloudflare Access policy was changed by the launchd-runtime commit.

### Protected Preview Smoke Status

- Latest protected-preview browser smoke before launchd hardening:
  - `2026-06-23-1007-12-fretboard-svg-cache-bust-protected-smoke.md`;
  - exact URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=fretboard-svg-cache-bust-20260623b`;
  - local `/api/version` reported `7ec5e3a`;
  - result: protected Explorer route loaded, refreshed `pedal-steel-fretboard.js` was served, in-page background SVG used `?v=keyhead-vshape-bce771f`, and no Explorer console errors were reported.
- Current HEAD `564d29c` has **not** been protected-preview browser-smoked.
- The launchd-supervised runtime has **not** been installed/loaded/smoked.
- Do not report local API fallback as protected-preview browser smoke.
- User smoke on `app.steelguitarrag.com` is not ready until Lane 12 verifies the current committed runtime.

### User Smoke Target

- Current user-smoke status: **needs Lane 12 verification before user smoke resumes**.
- Next Lane 12 protected-preview smoke URL:
  - `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=564d29c`
- Exact URL for the user after Lane 12 passes:
  - `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=564d29c`
- Root `/` behavior should be recorded by Lane 12, but the exact `/ui/steel-guitar-rag-mock.html` URL remains the safer cache-busted smoke target.

Smoke prompts for Lane 12/user smoke:

- `Show me a G major grip.`
- `Show me a 4-5-6 grip.`
- `Where is G on E9?`
- `Show me a G to C move.`
- `How do I use A+B pedals?`
- `Show me an E-lower move.`
- `Give me a beginner lick in G.`
- `Give me the full tab for a modern copyrighted song.`
- `Tab the whole solo from Together Again.`
- `Transcribe this YouTube recording into tab.`
- `What are good Fender Steel King settings?`
- `Why does my amp buzz at idle?`

Expected guardrails:

- Static grip answers should be fretboard-first.
- Movement examples may include deterministic tab.
- Do not provide full copyrighted song tab.
- Do not transcribe full solos.
- Do not transcribe YouTube/recording audio into tab.
- Gear answers must not carry stale tab/fretboard payloads.
- No raw `[object Object]`.
- No stale tab/fretboard payload on gear answers.

### Remaining Blockers

- App LaunchDaemon not proven installed/loaded.
- Protected-preview browser smoke not complete for current HEAD `564d29c`.
- Protected-preview browser smoke not complete for a launchd-supervised app runtime.
- AC sleep remains enabled unless changed outside repo.
- Restart after power failure remains disabled/unverified unless changed outside repo.
- Ollama boot availability remains unverified.
- Cloudflare Tunnel inline-token hardening remains a separate security/ops task.
- Broad unrelated dirty/untracked work remains parked.

### Next Control Step

Run Lane 12. Do not start new product work before this smoke gate.

```text
Lane 12: Install/load or verify the Mac mini private-preview LaunchDaemon from committed HEAD 564d29c, or explicitly document why the runtime remains manual. Verify local /api/version reports 564d29c or later, verify Cloudflare Access browser auth, record root `/` behavior, and run protected-preview browser smoke at https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=564d29c. Use the 12 smoke prompts listed in integration-status.md. Confirm static grip answers are fretboard-first, movement examples may include deterministic tab, copyrighted song/solo/YouTube transcription requests are refused, gear answers have no stale tab/fretboard payload, and no [object Object] appears. Write a Lane 12 handoff with exact URL tested, cache-busted URL, auth result, expected/current git HEAD, /api/version result, root URL behavior, direct /ui behavior, and API fallback status.
```

### Safe-To-Stage For This Refresh

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-01-integration-status-deployment-wrap.md`

### Files Not To Stage For This Refresh

- Any unrelated dirty/untracked files.
- App code, tests, UI, SVG assets, launchd/deploy scripts, auth/DNS/Cloudflare config, or source files.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Deployment secrets, private env files, rendered plists, tunnel tokens, tunnel credentials, `.wrangler/`, and any secrets.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.

## 2026-06-23 E9 Fretboard Explorer / Harmony Guidance Snapshot

- Current branch: `feature/answer-api`.
- Current HEAD at this refresh: `abed6ff fix: refresh e9 explorer home entry cache-bust`.
- Current project state: the E9 Fretboard Explorer is implemented, committed, protected-preview smoked from the app page into the Explorer route, and ready for user demo/smoke feedback. This snapshot supersedes the stale `e90e157` key-expansion-only status.
- Broad unrelated dirty/untracked work remains parked. Do not broad-stage; use exact-path staging only.

### Latest Relevant Commits

- `abed6ff fix: refresh e9 explorer home entry cache-bust`
- `3081261 feat: add e9 explorer home entry`
- `444f4ed docs: record tracked keyhead protected smoke`
- `bce771f fix: track fretboard keyhead asset`
- `b5fd09a fix: show e9 explorer row explanations`
- `7dac984 feat: add e9 explorer row explanations`
- `fbe269b docs: record e9 explorer expanded-key protected smoke`
- `7fc3846 fix: refresh e9 explorer expanded key cache-bust`
- `d4b26ad fix: expose expanded e9 explorer keys`
- `b860cf3 test: add e9 explorer key expansion QA`
- `be3be01 docs: refresh e9 explorer integration status`
- `e90e157 feat: expand e9 fretboard explorer keys`

### E9 Harmony Knowledge File Status

- `docs/llm-guidance/e9_harmonized_scales_and_diatonic_harmony_knowledge.md` exists.
- It was VTT-enhanced, conflict-audited, and cleaned up in the 2026-06-22 harmony-guidance handoffs.
- Current status: guidance material only, not structured runtime truth.
- Corpus/embedding/RAG status: not ingested, not chunked, not embedded, not connected to Chroma/vector stores, and not wired into SGF/RAG/source-card behavior.
- Ingestion caveat: exact fret/string/pedal tables still require deliberate table-wide pitch validation and ingestion design before any corpus, curated-guidance, embedding, or runtime use.

### Deterministic Explorer Backend Status

- `pocketsteel/fretboard_explorer.py` owns deterministic Explorer row generation and remains independent from RAG/corpus retrieval.
- Musical truth is owned by standard E9 mechanics and pitch validation in code.
- Expanded backend key support is implemented through `build_explorer_payload(key)` / `explorer_rows(key)`.
- Backend-supported key spellings currently include `C`, `C#`, `Db`, `D`, `D#`, `Eb`, `E`, `F`, `F#`, `Gb`, `G`, `G#`, `Ab`, `A`, `A#`, `Bb`, and `B`.
- The browser UI intentionally exposes the QA-covered learner-facing key set: `G`, `C`, `D`, `F`, `Bb`, `Eb`.
- Internal canonical pitch validation remains separate from learner-facing display spelling.
- Key-aware display spelling is implemented:
  - G natural minor: `G A Bb C D Eb F`.
  - C natural minor: `C D Eb F G Ab Bb`.
  - Bb/Eb major render flat spellings where expected.
- Partial diminished / partial m7b5 rules remain enforced:
  - three-note diminished rows stay `partial`;
  - omitted `b7` is recorded;
  - warning text explains the grip does not include b7.
- `explanation_summary` is deterministic teaching copy generated from validated rows; it does not choose fret/string/pedal rows and does not use RAG/corpus text.

### Explorer UI Status

- Browser route exists: `/ui/e9-fretboard-explorer.html`.
- App/home entry exists on `/ui/steel-guitar-rag-mock.html`:
  - label: `Explore the E9 Fretboard`;
  - description: `Choose a key, scale, harmony type, and string group to see validated E9 positions visually.`;
  - link text: `Open Fretboard Explorer`;
  - link target: `/ui/e9-fretboard-explorer.html`.
- Explorer UI includes:
  - expanded key selector for `G`, `C`, `D`, `F`, `Bb`, `Eb`;
  - major / natural minor selector;
  - mode-aware 2-string / 3-string filtering;
  - core grips separated from advanced swaps;
  - `5-7-8` as advanced / E-lower pocket only;
  - compact row buttons;
  - selected-position detail panel;
  - marker tooltip/detail UX;
  - deterministic `explanation_summary` in selected detail under `Why this position works`;
  - technical details collapsed behind `Show technical details`;
  - dense permanent SVG labels suppressed.
- Protected smoke reports confirm no primary `N validated rows` copy, no `E-lower+E-lower`, and no `[object Object]` in the checked Explorer states.

### Fretboard SVG Asset Status

- `public/brand/pedal-steel-fretboard-background.svg` is now tracked in git.
- V-shaped keyhead/tuner layout is committed in `bce771f fix: track fretboard keyhead asset`.
- SVG constraints verified:
  - `viewBox` remains `0 0 1600 420`;
  - root `width` and `height` attributes remain absent;
  - 5 top tuners and 5 bottom tuners are preserved;
  - `data-layer="headstock-keyhead-shell"` and `data-layer="10-tuning-keys"` are present.
- Protected-preview asset routing was verified in `2026-06-23-keyhead-vshape-tracked-asset-protected-smoke.md`.
- Known caveat: direct raw-SVG browser tabs can log a browser-runtime promise warning. The Explorer app page renders normally and this has not blocked Explorer behavior.

### Protected-Preview / Smoke Status

- Expanded-key protected smoke passed in `2026-06-22-e9-fretboard-explorer-expanded-key-protected-smoke.md`.
- Explanation UI was implemented and later verified through protected Explorer smoke.
- Tracked SVG protected smoke passed in `2026-06-23-keyhead-vshape-tracked-asset-protected-smoke.md`.
- Home-entry protected-preview refresh passed in `2026-06-23-e9-fretboard-explorer-home-entry-preview-refresh.md`.
- Full app smoke from the app page into the Explorer passed in `2026-06-23-e9-fretboard-explorer-full-app-smoke.md`.
- Latest full app smoke target:
  - app/home: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`
  - Explorer: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=e9-explorer-home-entry-20260623`
  - SVG asset: `https://app.steelguitarrag.com/brand/pedal-steel-fretboard-background.svg?qa-smoke=home-entry-20260623`
- Latest `/api/version` evidence from full app smoke:
  - local loopback reported `git_sha: abed6ff`, branch `feature/answer-api`, retrieval mode `hybrid_private_first`, auth provider `cloudflare_access`;
  - unauthenticated protected shell curl returned Cloudflare Access `302`, expected;
  - authenticated browser pages loaded as product pages, not Access login pages.
- Root `/` status: not certified by the latest full app smoke. The canonical tested app URL remains `/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`.

### Tests / QA Status

- Latest full pytest count from relevant E9 Explorer handoffs: `808 passed`.
- Latest focused test counts:
  - `tests/test_frontend_answer_ui.py -q`: `23 passed`.
  - `tests/test_pedal_steel_fretboard_ui.py -q`: `31 passed`.
  - `tests/test_fretboard_explorer.py -q`: `28 passed`.
  - same-origin app-page cache-bust smoke-server test: `1 passed`.
- JS syntax checks reported passing for:
  - `ui/answer-client.js`;
  - `ui/pedal-steel-fretboard.js`;
  - `ui/e9-fretboard-explorer.js`;
  - `ui/e9-fretboard-explorer-data.js`.
- Current docs-only refresh checks are listed in the handoff for this refresh.

### Component / Data Contract Notes

- Explorer browser fixture exposes keyed payloads at `window.STEEL_RAG_E9_EXPLORER_PAYLOADS`.
- Compatibility fallback remains at `window.STEEL_RAG_E9_EXPLORER_PAYLOAD`.
- Explorer payload rows include learner-facing fields:
  - `display_notes`;
  - `display_top_voice`;
  - `display_summary`;
  - `explanation_summary`.
- Explorer source guidance refs are internal identifiers such as `e9-harmony-guidance:*`; they are not SGF/RAG source-card evidence and should not be treated as corpus retrieval.

### Known Risks / Open Issues

- Broad unrelated dirty/untracked worktree remains parked in docs, corpus/source metadata, source-inbox metadata, root RAG scripts, brand/static assets, and historical handoffs.
- Bare root `/` was not the latest full app smoke target; use the exact tested `/ui/steel-guitar-rag-mock.html` URL for demo until Lane 12 certifies root again.
- Explorer mobile/narrow viewport is usable and has no document-level horizontal overflow, but the fretboard area is vertically dense.
- Raw SVG direct-tab warning is recorded as non-blocking.
- Harmony guidance ingestion, chunking, embeddings, and Chroma/RAG wiring are not started and should not start without an explicit ingestion design and approval.

### Recommended Next Steps

1. User demo/smoke the exact protected-preview app URL below and collect feedback:
   - `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623`
2. If the user wants root `/` to become the canonical demo URL, route to Lane 12 to verify root after the current committed HEAD:

```text
Lane 12: Run ProtectedPreviewSmoke for the E9 Fretboard Explorer app entry at current HEAD. Verify /api/version, root `/` behavior, and the canonical app URL. Test https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=e9-explorer-home-entry-20260623 plus /ui/e9-fretboard-explorer.html. Confirm Cloudflare Access login succeeds, the home entry opens the Explorer, expanded keys and explanations work, the tracked SVG asset loads, and no [object Object], E-lower+E-lower, or raw validated-row-count primary copy appears.
```

3. After user feedback, choose the next feature lane:
   - Lane 06 for mobile Explorer density or UI polish.
   - Lane 05 / Lane 18 for additional deterministic Explorer behavior.
   - Lane 02 / Lane 05 for curated-guidance or harmony ingestion planning only after deterministic UI behavior is accepted.

Do not start corpus ingestion, chunking, embeddings, Chroma/vector work, scraping, deployment/auth/DNS changes, or private-source work from this refresh.

### Safe-To-Stage For This Refresh

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-06-23-e9-explorer-integration-status-refresh.md`

### Files Not To Stage For This Refresh

- Any unrelated dirty/untracked files.
- App code, tests, UI, SVG assets, or source files.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Deployment/auth/DNS/secrets files.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.
- Parked closeout handoffs such as `docs/handoffs/task-completions/2026-06-23-01-keyhead-vshape-asset-commit.md` unless a later task explicitly includes them.

## 2026-06-19 Repo Steward Review / Next Slice Gate

- Review start HEAD: `d10fb85 docs: refresh integration status after landing smoke`.
- Current HEAD observed before final review staging: `ca699a0 docs: define parameterized chord movement contract`.
- Current branch at review: `feature/answer-api`.
- Index at review start: clean; no staged files.
- Integration-status audit result: current enough after this review update. The completed landing-page slice, deploy/smoke commit, public URLs, protected-app separation, Direct Upload caveat, parameterized chord-movement contract, and next control-loop state are recorded here.
- Recent committed chain reviewed:
  - `ca699a0 docs: define parameterized chord movement contract`
  - `d10fb85 docs: refresh integration status after landing smoke`
  - `3f1b3dc docs: record private preview landing smoke`
  - `0bbdef0 refresh private preview landing page`
  - `ae1d669 fix blocked song tab routing`
  - `b2190c9 fix song tab copyright refusal wording`
  - `7a36b71 docs: record hanging sign protected preview smoke`
  - `4b8ac0c fix: align hanging sign placement`
  - `6f51493 test: add Steel Guitar Rag curated QA`
  - `edae8ef docs: add ChatGPT project context bundle`
  - `bb6745b add steel guitar rag curated reference`
  - `56277fd docs: design public-domain song tab architecture`
- Recent handoffs reflected or intentionally left as historical:
  - `2026-06-19-18-parameterized-chord-movement-contract.md` is committed and defines the next backend implementation contract;
  - landing refresh and landing deploy/smoke are reflected in the landing section below;
  - Steel Guitar Rag curated/reference work is committed and QA-reviewed;
  - hanging sign/logo/layout work is committed and protected-preview smoke-reviewed;
  - blocked song-tab routing and copyright wording fixes are committed, with historical Lane 12 smoke handoffs showing the earlier failures that led to the subsequent fixes;
  - tab-engine and fretboard-first guidance remains preserved as the recommended next product direction.
- Dirty worktree status: not clean. Broad unrelated parked work remains in docs, source/corpus metadata, root RAG scripts, source-inbox metadata, UI/static/brand assets, private/generated helper files, and historical handoffs. Do not broad-stage.
- Known parked dirty tracked paths at review include `README.md`, `corpus_metadata/source_policies/README.md`, `corpus_metadata/source_registry.json`, `docs/answer-eval-report.md`, `docs/cloudflare-pages-landing.md`, `docs/copyright-provenance.md`, `docs/corpus-license-policy.md`, `docs/current-commands.md`, `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`, `docs/source-inbox-inventory.md`, root RAG scripts, `source-inbox/inventory.json`, and `ui/brand/steel-guitar-rag-landing-*` assets.
- Safety result: safe to proceed to the next product slice only with exact-path scope. If the next slice overlaps any dirty parked file, route or isolate that parked work before implementation.
- Next recommended slice: Lane 05 Backend / RAG Integration for parameterized chord-movement implementation using the committed Lane 18 contract.
- Stop conditions for the next slice: do not run deployment, protected-preview restart, scraping, embeddings, Chroma/vector rebuilds, corpus jobs, DNS/auth changes, or Cloudflare Access changes unless the next prompt explicitly names that lane and action.

## 2026-06-19 Private-Preview Public Landing Refresh

- Landing deploy/smoke baseline before the docs refresh: `3f1b3dc docs: record private preview landing smoke`.
- Public landing refresh implementation: committed in `0bbdef0 refresh private preview landing page`.
- Deployment/smoke handoff: committed in `3f1b3dc docs: record private preview landing smoke`.
- Status: refreshed private-preview public landing copy is implemented, deployed, smoked, and documented.
- Verified public landing URLs:
  - `https://steelguitarrag.com/?v=0bbdef0`
  - `https://www.steelguitarrag.com/?v=0bbdef0`
  - `https://841e0459.steel-guitar-rag-landing.pages.dev/?v=0bbdef0`
- Verified behavior:
  - refreshed landing copy is live on public root, `www`, and Pages deployment URLs;
  - desktop and mobile browser smoke passed;
  - no horizontal overflow observed;
  - no relevant console errors observed;
  - interest form remains present and points to `/api/interest`;
  - no `/api/answer` exposure was found on the public landing page.
- Protected app separation:
  - `https://app.steelguitarrag.com/` remains the Cloudflare Access-protected app route;
  - it is separate from the public Pages landing page;
  - this landing slice did not change protected app behavior.
- Checks and deploy evidence:
  - `cmp -s ui/steel-guitar-rag-landing.html deploy/landing/index.html`: passed.
  - `.venv/bin/python -m pytest tests/test_public_landing_page.py -q`: `31 passed`.
  - `git diff --check`: passed.
  - Cloudflare Pages deploy completed with Wrangler Direct Upload.
  - Browser smoke covered desktop/mobile public landing page.
  - Header/content checks covered public root, `www`, Pages deployment, and protected app root behavior.
- Unchanged systems:
  - no backend behavior changed;
  - no auth, DNS, Cloudflare Access policy, deployment config, Chroma/vector stores, embeddings, scraping, corpus, private source, or protected app behavior changed.
- Risk/caveat:
  - Cloudflare Pages Direct Upload means a future stale manual Cloudflare Pages upload could overwrite the refreshed artifact.
- Control-loop state:
  - stop the landing-page slice;
  - choose the next product slice;
  - if continuing tab-engine work, use Lane 18 or Lane 05 for parameterized chord-movement examples;
  - if the refreshed landing page gets visual/copy feedback, route back to Lane 06.

## 2026-06-18 Deterministic Tab Engine Slice

- Current repository HEAD after Repo Steward commit: `686fd3c feat: add deterministic tab engine slice`.
- Tab-engine status: committed.
- Implementation summary:
  - Added deterministic `pocketsteel/tab_engine.py` with default 10-string E9 profile, structured tab events, validation issues, fixed-width rendering, deterministic examples, and payload rendering.
  - Added `POST /api/tab/render` in `pocketsteel/api.py`; `/api/answer`, RAG retrieval, Chroma, corpus, auth, deployment, and UI rendering were not changed.
  - Added focused coverage in `tests/test_tab_engine.py`.
- Active-lane handoffs committed:
  - `docs/handoffs/task-completions/2026-06-18-05-tab-engine-first-slice.md`
  - `docs/handoffs/task-completions/2026-06-18-15-tab-engine-qa-matrix.md`
  - `docs/handoffs/task-completions/2026-06-18-1516-06-tab-engine-answer-ux.md`
  - `docs/handoffs/task-completions/2026-06-18-18-tab-engine-product-architecture.md`
- Checks run by Repo Steward:
  - `.venv/bin/python -m py_compile pocketsteel/tab_engine.py pocketsteel/api.py`: passed.
  - `.venv/bin/python -m pytest tests/test_tab_engine.py -q`: `15 passed`.
  - `.venv/bin/python -m pytest tests/test_api_contract.py -q`: `4 passed`.
  - `.venv/bin/python -m pytest tests/test_api_search.py -q`: `246 passed`.
  - `git diff --check`: passed.
  - `.venv/bin/python -m pytest -q`: `735 passed, 2 failed`.
- Full-suite failures are unchanged unrelated static/UI caveats:
  - `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`.
  - `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`.
- Dirty worktree remains broad with unrelated docs/corpus/source/static/design/UI files parked. Do not stage broad changes around `integration-status.md`; exact-path or exact-hunk staging remains required.
- Recommended next slices:
  - Lane 06 can implement answer-page tab rendering from the committed `/api/tab/render` contract when explicitly requested.
  - Lane 18/Product can refine tab feature guardrails and answer integration scope.
  - Lane 15 can add browser/UI tab smoke only after UI rendering exists.

## 2026-06-14 Steel Guitar 101 Foundation Router Update

- Current repository HEAD: `36f53ea backend: add steel guitar 101 foundation answers`.
- Backend smoke-bug fix committed:
  - Added deterministic Steel Guitar 101 foundation answers for beginner concepts including steel guitar, pedal steel, lap steel, console steel, E9, C6, copedent, changer, pedals/levers, grips, pockets, slants, and basic steel-guitar vocabulary.
  - Added source-free comparison answers for lap steel vs pedal steel, E9 vs C6, dobro vs steel guitar, and pedal steel vs regular guitar.
  - Preserved off-domain guardrails and existing chord/fretboard deterministic resolvers.
- Files committed:
  - `pocketsteel/curated_answers.py`
  - `tests/test_api_search.py`
  - `docs/handoffs/task-completions/steel-guitar-101-foundation-router-fix.md`
- Tests run:
  - `git diff --check`: passed.
  - Focused 101/API tests: `5 passed, 233 deselected`.
  - `.venv/bin/python -m pytest tests/test_answer_intent_classifier.py tests/test_api_search.py tests/test_fretboard_examples.py -q`: `367 passed`.
  - `.venv/bin/python -m pytest tests/test_answer_eval.py tests/test_full_answer_quality_eval.py tests/test_api_contract.py -q`: `68 passed`.
  - `.venv/bin/python scripts/run_full_answer_quality_eval.py`: `151 pass / 33 warn / 111 fail`, private-source behavior correct.
  - `.venv/bin/python -m pytest`: `706 passed, 2 failed`.
- Known unrelated full-suite caveats remain unchanged:
  - `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`.
  - `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`.
- Generated private eval reports from the strict eval remain unstaged and must stay unstaged:
  - `corpus-private/reports/full-answer-quality-eval.md`
  - `corpus-private/reports/full-answer-quality-eval.json`
- Protected-preview restart status: not run for this backend-only commit.
- User smoke may continue after protected preview is restarted to a runtime that includes `36f53ea`.
- Exact URL for user smoke remains: `https://app.steelguitarrag.com/`.
- Dirty worktree remains broad with parked docs/corpus/source/static/design/private/generated files; do not stage them without an exact lane-approved scope.

## 1. Current Overall Project State

- Current repository HEAD: `449cdee docs: record 05e8748 browser-ready verification`.
- Verified protected-preview runtime HEAD: `05e8748 backend: replace quarantine fallback with teacher routes`.
- Current app readiness: browser-ready for user smoke/use.
- Exact user smoke URL: `https://app.steelguitarrag.com/`.
- Root behavior: protected-preview root redirects to `/ui/steel-guitar-rag-mock.html` and was verified in an authenticated Cloudflare Access browser session.
- Q&A unlock: passed after session initialization.
- Do not reopen completed `05e8748` smoke work unless new evidence shows a real user-facing blocker.
- Do not restart broad QA today unless a new real blocker is found.

## 2. Recent Tasks Completed By Active Lane

### Lane 01 Repo Steward

- Committed browser-ready verification docs:
  - `449cdee docs: record 05e8748 browser-ready verification`
  - committed `minimal-browser-verification-05e8748.md`
  - committed `2026-06-14-1700-15-runtime-05e8748-automated-qa.md`
  - committed `root-user-smoke-verification-after-resolver-fix-05e8748.md`
- Refreshed final readiness docs:
  - `docs/handoffs/task-completions/integration-status.md`
  - `docs/handoffs/task-completions/final-readiness-refresh-05e8748.md`
- Cleaned trailing whitespace in `docs/answer-eval-report.md` so `git diff --check` passes, but did not commit it because the file also contains a large parked generated-report rewrite.

### Lane 05 Backend / RAG Integration

- `05e8748 backend: replace quarantine fallback with teacher routes`
  - replaced remaining quarantine/backstop leakage paths with teacher routes;
  - fixed deterministic resolver issues for off-domain math bait, A-minor/B-flat parsing, string/fret/pedal diagnostics, Cmaj7/C7 where-to-play prompts, frustration prompts, repair prompts, and SGF quarantine regressions.
- Prior supporting backend fixes remain committed:
  - `24fd8e9 backend: fix repair fallback and chord classifier drift`
  - `1f91ed2 backend: block sgf primary answer leakage`
  - `c8b0d3b backend: quarantine sgf text from answer body`
  - `fd89e2d backend: fix remaining broad qa p1 blockers`
  - `a9eaa82 backend: fix broad qa chord and guardrail blockers`
  - `2cdea8a backend: normalize natural chord intent prompts`
  - `36ab10e backend: route chord qualities to fretboard answers`
  - `658c069 backend: answer practical chord questions directly`

### Lane 06 UX/UI Design

- `6a5f978 ui: improve answer page spacing`
- `28ae8f4 Fix answer card desktop section width`
- Recent user-smoke UI/layout work is not the blocker now; app root/browser readiness is verified for runtime `05e8748`.
- Known static/UI full-suite caveats remain backlog unless reclassified:
  - landing source vs deployed static HTML mismatch;
  - missing public fretboard background route in same-origin static smoke.

### Lane 12 Self-Hosted Deployment

- Root protected-preview verification after `05e8748`: passed.
- Verified:
  - runtime `/api/version` reported `05e8748`;
  - root URL loaded through Cloudflare Access and redirected to `/ui/steel-guitar-rag-mock.html`;
  - Q&A unlocked in the authenticated browser session;
  - fallback `/ui/steel-guitar-rag-mock.html` worked;
  - authenticated browser smoke passed.

### Lane 15 QA / Answer Eval

- Runtime `05e8748` automated QA:
  - focused automated API fallback smoke: `36` prompts, `36` true pass / `0` true blockers;
  - strict scorer SGF leakage gates: `0` hits across SGF primary leakage, forum-fragment leakage, weak-source primary wording, off-domain source cards, lesson/scale/lick hard gates, and deterministic teacher answer source fragments;
  - focused pytest set: `376 passed`.
- Minimal authenticated browser verification:
  - six requested prompts passed;
  - off-domain source cards absent;
  - fretboard rendered where expected;
  - Q&A unlocked after Cloudflare Access session initialization.

## 3. Files Changed Across Recent Tasks

Committed in `449cdee`:

- `docs/handoffs/task-completions/minimal-browser-verification-05e8748.md`
- `docs/handoffs/task-completions/2026-06-14-1700-15-runtime-05e8748-automated-qa.md`
- `docs/handoffs/task-completions/root-user-smoke-verification-after-resolver-fix-05e8748.md`

Currently changed by recent coordination/cleanup:

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/final-readiness-refresh-05e8748.md`
- `docs/handoffs/task-completions/repo-steward-05e8748-browser-ready-docs-commit.md`
- `docs/handoffs/task-completions/repo-steward-answer-eval-whitespace-cleanup.md`
- `docs/answer-eval-report.md` (trailing whitespace cleaned, but content rewrite remains parked/uncommitted)

Broad parked dirty/untracked files remain outside the 05e8748 readiness scope, including docs/corpus/source metadata, root RAG scripts, landing/static/design assets, source-inbox metadata, historical handoffs/assets, `public/`, `ui/brand/`, `Neon Sign/`, and private-lesson helper scripts/data.

## 4. Conflicts Or Overlapping Changes

- `docs/answer-eval-report.md` is the main overlap risk:
  - whitespace has been cleaned;
  - `git diff --check` passes;
  - the file still contains a large generated report-content rewrite, so it is not safe to stage as a whitespace-only change.
- `docs/handoffs/task-completions/integration-status.md` is a coordination artifact and should not be bundled with implementation commits.
- Many untracked handoffs/assets are historical or parked; do not stage them without exact scope.
- Static/UI full-suite caveats should not be mixed with backend answer/RAG commits.

## 5. Schema / API / Component / Data Contract Changes

- No new `/api/answer` schema change is pending from this readiness refresh.
- Runtime `05e8748` confirms answer routing behavior is ready without schema migration.
- Protected-preview `/api/version` was used as the runtime identity source.
- Root route behavior: `/` redirects to `/ui/steel-guitar-rag-mock.html`; this is verified and acceptable for current user smoke.
- API fallback QA must remain labeled as API fallback, not browser smoke.
- No corpus, Chroma/vector, embedding, source-inbox, scraping, auth-policy, DNS, or deployment contract changes are part of the current ready state.

## 6. Tests Reported By Lane

### Lane 05 Backend

- `05e8748` implementation handoff reported:
  - focused answer/classifier/API tests: `364 passed`;
  - contract/eval tests: `68 passed`;
  - full pytest: `703 passed, 2 failed`.
- The two full-suite failures were classified as unrelated static/UI failures:
  - landing source vs deployed static HTML mismatch;
  - missing public fretboard background route.

### Lane 12 Deployment / Protected Preview

- Authenticated protected-preview browser smoke: passed.
- `/api/version`: reported `05e8748`.
- Root route: passed.
- Fallback UI route: passed.
- Unauthenticated local `/api/answer`: still returned `401`, as expected.

### Lane 15 QA

- Focused automated API fallback smoke: `36` true pass / `0` true blockers.
- Strict scorer:
  - `295` questions;
  - `152` pass, `33` warn, `110` fail by broad scorer;
  - true blocker count for requested runtime QA scope: `0`;
  - strict SGF leakage hard gates all `0`.
- Focused pytest set: `376 passed`.
- Minimal browser verification: six prompt smoke passed.

### Lane 01 Repo Steward

- `git diff --check`: passed after `docs/answer-eval-report.md` trailing whitespace cleanup.
- Browser-ready handoff docs committed in `449cdee`.
- Current coordination refresh not committed.

## 7. Blockers Or Human Decisions Needed

- User smoke/use is ready now at `https://app.steelguitarrag.com/`.
- No human decision is needed before using the app.
- Human decision is needed only if someone wants to commit parked docs/report/source/static work.
- Do not treat broad strict eval failures as user-smoke blockers unless a future lane reclassifies a specific row as a true product failure.
- Do not restart broad QA today unless a new real blocker appears.

## 8. Dirty Worktree / Commit Readiness

- Current worktree is broadly dirty with parked non-runtime work.
- `git diff --check`: passes.
- Runtime readiness remains based on committed runtime `05e8748` and committed verification docs, not the broad dirty worktree.
- Dirty tracked files include:
  - `README.md`
  - `corpus_metadata/source_policies/README.md`
  - `corpus_metadata/source_registry.json`
  - `deploy/landing/index.html`
  - `docs/answer-eval-report.md`
  - `docs/cloudflare-pages-landing.md`
  - `docs/copyright-provenance.md`
  - `docs/corpus-license-policy.md`
  - `docs/current-commands.md`
  - `docs/handoffs/task-completions/integration-status.md`
  - `docs/handoffs/task-completions/qa-no-op-answer-intent-classifier-source-backed-fix.md`
  - `docs/source-inbox-inventory.md`
  - root RAG scripts
  - `source-inbox/inventory.json`
- Many untracked historical handoffs/assets and design/source/corpus helper files remain parked.

## 9. Files Safe To Stage

Safe only if a docs-only coordination commit is explicitly requested:

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/final-readiness-refresh-05e8748.md`
- `docs/handoffs/task-completions/repo-steward-05e8748-browser-ready-docs-commit.md`
- `docs/handoffs/task-completions/repo-steward-answer-eval-whitespace-cleanup.md`

Safe only if explicitly approving the generated report-content rewrite as its own docs/report slice:

- `docs/answer-eval-report.md`

## 10. Files That Should Remain Unstaged

Keep unstaged unless a later exact lane approves them:

- implementation/runtime files not part of a current scoped task;
- root RAG/build scripts;
- corpus metadata/source policy files;
- `source-inbox/` inventory/provenance files;
- `public/`, `ui/brand/`, `Neon Sign/`, raw/generated design assets;
- deployment/static files such as `deploy/landing/index.html` unless a Lane 06/static task owns them;
- broad historical handoffs/assets;
- `docs/answer-eval-report.md` unless committing the full generated report-content update is explicitly approved.

## 11. Recommended Next Tasks By Lane

- Primary action: use the app at `https://app.steelguitarrag.com/`.
- Lane 12: no action unless runtime becomes unavailable or a new protected-preview issue appears.
- Lane 15: optional scorer calibration backlog only; do not run broad QA today unless a new real blocker appears.
- Lane 06: optional static/full-suite cleanup only if someone wants full-suite cleanliness.
- Lane 01: optional docs-only coordination commit if desired.
- Lane 05: only open new backend work for a new true user-facing blocker.

## 12. Exact Codex Prompts For Next Recommended Tasks

### Primary User Smoke / Use

```text
Use https://app.steelguitarrag.com/ for authenticated protected-preview user smoke. If a new issue appears, report the exact prompt, expected behavior, actual browser behavior, and whether the issue is visible in the UI or only in API output. Do not reopen completed 05e8748 smoke work unless new evidence contradicts the committed handoffs.
```

### Optional Lane 15 Scorer Calibration

```text
LANE: 15 QA / Answer Eval
REASONING: LOW
Branch: feature/answer-api

Calibrate scorer false positives from the 05e8748 runtime QA run without changing backend product behavior.

Read:
- docs/handoffs/task-completions/2026-06-14-1700-15-runtime-05e8748-automated-qa.md
- scripts/run_full_answer_quality_eval.py
- tests/test_full_answer_quality_eval.py

Focus only on scorer/eval noise:
- music-theory notation such as I-to-IV being mistaken for first-person forum fragments;
- direct capability caveats being mistaken for raw SGF/forum text;
- joke/song-title prompts where the scorer overstates unrelated theory fragments.

Do not modify backend answer behavior, UI, deployment, auth, corpus, Chroma/vector stores, embeddings, source-inbox, scraping, DNS, secrets, or visual assets.

Run focused scorer tests and write a handoff. Do not commit unless Repo Steward is explicitly invoked.
```

### Optional Lane 06 Static / Full-Suite Cleanup

```text
LANE: 06 UX/UI Design
REASONING: MEDIUM
Branch: feature/answer-api

Fix only the two unrelated static/UI full-suite failures if full-suite cleanliness is desired:
- landing source vs deployed static HTML mismatch;
- missing public fretboard background route in same-origin static smoke.

Read:
- AGENTS.md
- tests/test_public_landing_page.py
- tests/test_same_origin_smoke_server.py
- deploy/landing/index.html
- relevant public/static files

Do not touch backend answer routing, /api/answer schema, corpus, Chroma/vector stores, embeddings, source-inbox, scraping, DNS, auth policy, secrets, or unrelated handoffs.

Run the two focused static tests and any minimal related frontend/static checks. Write a handoff naming exact files/hunks for Repo Steward.
```

### Optional Lane 01 Docs Coordination Commit

```text
LANE: 01 Repo Steward
REASONING: LOW
Branch: feature/answer-api

Commit only the docs-only final readiness coordination refresh if desired.

Candidate files:
- docs/handoffs/task-completions/integration-status.md
- docs/handoffs/task-completions/final-readiness-refresh-05e8748.md
- docs/handoffs/task-completions/repo-steward-05e8748-browser-ready-docs-commit.md
- docs/handoffs/task-completions/repo-steward-answer-eval-whitespace-cleanup.md

Do not stage docs/answer-eval-report.md unless separately approving the full generated report-content rewrite. Do not stage implementation files, UI files, deployment/auth/DNS files, corpus/source-inbox/Chroma/embedding data, design assets, or unrelated handoffs.

Run git diff --cached --check, git diff --cached --name-only, and git diff --cached before committing.
```

## 2026-06-18 Tab Engine UI And Planning Follow-On

- Current repository HEAD after Repo Steward reconciliation: `54a28c7 fix: clear tab examples on stage return`.
- Relevant committed tab-engine follow-on commits:
  - `0bd0780 test: add tab engine ui QA coverage`
  - `07f9b9d feat: render tab examples on answer page`
  - `54a28c7 fix: clear tab examples on stage return`
- Backend baseline remains `686fd3c feat: add deterministic tab engine slice`.
- UI state:
  - Answer-page tab rendering is committed.
  - Tab examples render from normalized backend/API tab payloads; no fake frontend tab generator was added.
  - Follow-up fix clears tab examples when returning from answer workspace to the home/stage view.
- Planning handoffs to keep with this follow-on work:
  - `docs/handoffs/task-completions/2026-06-18-05-answer-triggered-tab-examples-implementation-plan.md`
  - `docs/handoffs/task-completions/2026-06-18-12-tab-engine-deploy-smoke-plan.md`
  - `docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-examples-architecture.md`
  - `docs/handoffs/task-completions/2026-06-18-19-tab-card-visual-guidance.md`
- Focused checks run by Repo Steward:
  - `.venv/bin/python -m py_compile pocketsteel/tab_engine.py pocketsteel/api.py`: passed.
  - `.venv/bin/python -m pytest tests/test_tab_engine.py -q`: `16 passed`.
  - `.venv/bin/python -m pytest tests/test_api_contract.py -q`: `4 passed`.
  - `.venv/bin/python -m pytest tests/test_api_search.py -q`: `246 passed`.
  - `node --check ui/answer-client.js`: passed.
  - `node --check ui/pedal-steel-fretboard.js`: passed.
  - `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`: `20 passed`.
  - `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`: `29 passed`.
  - `git diff --check`: passed.
  - `.venv/bin/python -m pytest -q`: `738 passed, 2 failed`.
- Full-suite failures remain the known unrelated static/UI caveats:
  - `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
  - `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`
- Dirty runtime caveat:
  - `ui/steel-guitar-rag-mock.html` and `tests/test_frontend_answer_ui.py` still contain unrelated landing-sign cache-bust changes after the tab-specific hunk was committed.
- Next recommended slice: Lane 05 answer-triggered deterministic tab examples using the architecture and implementation-plan handoffs above.

## 2026-06-18 Answer-Triggered Tab Examples Reconciliation

- Current repository HEAD before final Repo Steward commit: `dc1f4b8 feat: attach deterministic tab examples to answers`.
- Already committed answer-triggered tab work:
  - `2bf2767 docs: define answer-triggered tab UX behavior`
  - `812b46a test: define answer-triggered tab example QA`
  - `dc1f4b8 feat: attach deterministic tab examples to answers`
- This reconciliation found and fixed one small API/UI contract bridge:
  - backend emits optional `tab_example.rendered_tab`
  - committed browser renderer consumes normalized `response.tabs`
  - `ui/answer-client.js` now normalizes `tab_example.rendered_tab` into the existing tab-card model
  - `tests/test_frontend_answer_ui.py` now covers the `tab_example` API shape
- Handoffs ready to commit with this reconciliation:
  - `docs/handoffs/task-completions/2026-06-18-12-answer-triggered-tab-examples-smoke.md`
  - `docs/handoffs/task-completions/2026-06-18-18-answer-triggered-tab-architecture-review.md`
  - `docs/handoffs/task-completions/2026-06-18-01-answer-triggered-tab-repo-steward-commit.md`
- Supported answer-triggered tab examples from the committed backend slice:
  - G major grip / 4-5-6 grip
  - G to C move
  - A+B pedal major position
  - E-lower color move
  - beginner G lick
- Blocked/no-tab cases remain intentional:
  - unrelated gear/vendor/history questions
  - named copyrighted/full-song tab requests
  - full solos or recording transcriptions
  - unsupported arbitrary tab requests
- Focused checks run by Repo Steward:
  - `node --check ui/answer-client.js`: passed
  - `node --check ui/pedal-steel-fretboard.js`: passed
  - `.venv/bin/python -m py_compile pocketsteel/tab_engine.py pocketsteel/answer_tab_examples.py pocketsteel/api.py pocketsteel/api_contract.py`: passed
  - `.venv/bin/python -m pytest tests/test_tab_engine.py -q`: `20 passed`
  - `.venv/bin/python -m pytest tests/test_api_contract.py -q`: `5 passed`
  - `.venv/bin/python -m pytest tests/test_api_search.py -q`: `255 passed`
  - `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`: `20 passed`
  - `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`: `29 passed`
  - `.venv/bin/python -m pytest tests/test_tab_engine.py tests/test_api_contract.py tests/test_api_search.py tests/test_frontend_answer_ui.py -q`: `300 passed`
  - `git diff --check`: passed
  - `.venv/bin/python -m pytest -q`: `752 passed, 2 failed`
- Full-suite failures remain known unrelated static/UI caveats:
  - `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
  - `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`
- Dirty runtime / parked files:
  - unrelated landing-sign cache-bust hunks remain in `ui/steel-guitar-rag-mock.html` and `tests/test_frontend_answer_ui.py`; only the tab-example hunk in the shared test file should be staged for this reconciliation
  - broad parked docs/corpus/source/provenance/visual-design files remain untouched
- Protected-preview status:
  - not restarted by Repo Steward
  - Lane 12 should restart or verify after the reconciliation commit if no dirty runtime gate blocks it
- Exact next Lane 12 prompt:

```text
Lane: 12 Self-Hosted Deployment
Reasoning level: MEDIUM-HIGH

Restart protected preview from the clean committed answer-triggered tab examples HEAD and run browser smoke.

Read:
- AGENTS.md
- docs/handoffs/task-completions/2026-06-18-12-answer-triggered-tab-examples-smoke.md
- docs/handoffs/task-completions/2026-06-18-05-answer-triggered-tab-examples.md
- docs/handoffs/task-completions/2026-06-18-15-answer-triggered-tab-examples-qa.md
- docs/handoffs/task-completions/2026-06-18-01-answer-triggered-tab-repo-steward-commit.md

Do not modify files, stage, commit, change DNS, change Cloudflare Access policy, touch corpus/Chroma/vector stores/embeddings/source-inbox/private source data, or run scraping.

First verify the runtime dirty gate. Stop before restart if dirty runtime-affecting files are present unless the task explicitly authorizes dirty-state smoke.

Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: https://app.steelguitarrag.com/
- Cache-busted URL tested: https://app.steelguitarrag.com/?v=answer-tabs-<HEAD>
- Exact URL the user should use: https://app.steelguitarrag.com/?v=answer-tabs-<HEAD> after Cloudflare Access login
- Auth required: yes
- Auth provider: Cloudflare Access
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD: committed reconciliation HEAD or later
- Version endpoint: /api/version
- Version endpoint result: record exact response
- Root URL status: record observed behavior
- API fallback status: not sufficient for browser tab rendering

Verify:
- `Show me a G major grip` displays a deterministic tab card
- `Show me a G to C move` displays a deterministic tab card
- `How do I use A+B pedals?` displays a deterministic tab card
- unrelated gear/history/vendor prompts show no tab
- named copyrighted/full-song tab requests show no generated tab
- tab rows remain aligned and readable
- no `[object Object]`
- normal answer/source/fretboard rendering remains healthy
```

## 2026-06-18 Tab Example Fretboard Payload And Rendering Reconciliation

- Current repository HEAD before final Repo Steward UI commit: `12eef1d fix: align tab examples with fretboard payloads`.
- Backend tab-example/fretboard payload status:
  - committed in `12eef1d`
  - safe tab prompts attach deterministic `tab_example` and a compatible `fretboard` payload
  - fretboard payload is derived from deterministic tab events/registry, not frontend invention or LLM-generated tab
  - unsupported/copyright/full-song/transcription requests do not attach tab or tab-derived fretboard examples
- Corrected beginner lick semantics:
  - the beginner G lick A+B press event now uses only strings 5 and 6
  - string 8 is not shown as affected by A+B in that press event
  - G-to-C and A+B examples now use clearer action/position semantics from the backend registry
- UI fretboard rendering status:
  - `ui/answer-client.js` normalizes backend-provided nested `tab_example.fretboard` and `tabExample.fretboard`
  - top-level `fretboard` behavior remains unchanged
  - frontend does not invent fretboard positions when backend payload is absent
  - tab and fretboard render together when both payloads are present and clear on later non-tab responses
- Focused checks run by Repo Steward:
  - `git diff --check`: passed
  - `.venv/bin/python -m py_compile pocketsteel/tab_engine.py pocketsteel/api.py pocketsteel/answer_tab_examples.py`: passed
  - `.venv/bin/python -m pytest tests/test_tab_engine.py -q`: `22 passed`
  - `.venv/bin/python -m pytest tests/test_api_contract.py -q`: `5 passed`
  - `.venv/bin/python -m pytest tests/test_api_search.py -q`: `257 passed`
  - `node --check ui/answer-client.js`: passed
  - `node --check ui/pedal-steel-fretboard.js`: passed
  - `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q`: `20 passed`
  - `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q`: `29 passed`
  - `.venv/bin/python -m pytest -q`: `756 passed, 2 failed`
- Full-suite failures remain known unrelated static/UI caveats:
  - `tests/test_public_landing_page.py::test_cloudflare_pages_static_output_matches_landing_source`
  - `tests/test_same_origin_smoke_server.py::test_same_origin_server_serves_public_fretboard_background`
- Unrelated dirty work remains parked:
  - landing/sign cache-bust work in `ui/steel-guitar-rag-mock.html`, `ui/brand/steel-guitar-rag-landing-fallback-alpha.png`, and the unrelated hunk in `tests/test_frontend_answer_ui.py`
  - corpus/source/provenance docs and root RAG scripts
  - source-inbox and broad historical handoff/assets inventory
- Next recommended smoke:
  - Lane 12 should run protected-preview current-HEAD smoke after this Repo Steward commit
  - exact root URL: `https://app.steelguitarrag.com/?v=tab-example-fretboard-<HEAD>`
  - verify `Show me a G major grip`, `Show me a G to C move`, `How do I use A+B pedals?`, `Show me an E-lower move`, and `Give me a beginner lick in G`
  - expected: safe prompts show deterministic tab plus fretboard; no tab/fretboard for unrelated or copyrighted/full-song tab prompts
