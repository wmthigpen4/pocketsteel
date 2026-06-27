# Integration Status - Current Reset Snapshot

Generated for ChatGPT reset/guidance on branch `feature/answer-api`.

## Current State

- Current branch: `feature/answer-api`.
- Latest implementation commit: `3c78758 feat: redesign landing page around explorer and brain`.
- Latest public landing redesign commit: `3c78758 feat: redesign landing page around explorer and brain`.
- Latest local public landing smoke: **PASS at commit `3c78758` for direct static landing URL `http://127.0.0.1:8770/ui/steel-guitar-rag-landing.html?v=landing-explorer-brain-local-visual-2`**. Smoke verified an Explorer-first hero, large E9 fretboard preview above the fold on desktop, top navigation for Fretboard Explorer and Brain paths, five Explorer mode cards, compact lower Steel Guitar Brain band, no page-level horizontal overflow on desktop/tablet/mobile checks, no relevant console errors, and no public `/api/answer` or private app-shell link exposure from the static landing HTML. Local root `http://127.0.0.1:8770/` still redirects to `/ui/steel-guitar-rag-mock.html`.
- Latest protected-preview public landing smoke: **PASS for direct static landing URL `https://app.steelguitarrag.com/ui/steel-guitar-rag-landing.html?v=landing-redesign-3c78758`, with root-routing caveat**. Cloudflare Access was already authenticated in the in-app browser. Direct static landing URL showed `Explore the E9 neck. Ask better questions.`, Explorer hero, compact Brain band, five mode cards, no page-level horizontal overflow, no relevant console errors, and no `/api/answer` or `steel-guitar-rag-mock.html` exposure from static landing HTML. Protected root `https://app.steelguitarrag.com/?v=landing-redesign-3c78758` still redirects to `/ui/steel-guitar-rag-mock.html` and shows the app shell hero `Ask the steel guitar brain.` `/api/version` reports runtime SHA `4040a47`, so this verifies cache-busted static file behavior rather than a runtime restart to `3c78758`. Lane 12 / product should confirm whether root should serve the redesigned landing page or continue app-shell redirect behavior before user smoke.
- Latest local Explorer Chord / Voicing Finder smoke: **PASS at commit `a08eba4`**. Local browser smoke verified `Chord / Voicing Finder` is selectable at `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=chord-voicing-finder-local-2`; `Fmaj7` returned practical partial and complete candidates without dominant-7 mislabeling; `Cmin9` parsed as `Cm9` and produced a clear no-practical-candidate state under default filters; `V7 in G` resolved to `D7`; selecting a candidate updated the selected card/detail and kept one selected SVG highlight; changing Grip vocabulary from Core to All practical expanded Fmaj7 candidates from 14 to 24; no `[object Object]` or `omitted 0` text appeared.
- Protected-preview Explorer Chord / Voicing Finder smoke: **not run yet**. Recommended Lane 12 URL after protected-preview refresh: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-voicing-finder-a08eba4`.
- Previous Explorer Dominant 7 / V7 implementation commit: `c6fa25e fix: label dominant seven grip vocabulary`.
- Latest local Explorer Dominant 7 / V7 smoke: **PASS at commit `c6fa25e`**. Local browser smoke verified Build Grip exposes `Core triads`, `Dominant 7 / V7`, `Extended grips`, and `All practical`; selecting Dominant 7 / V7 reveals D7/V7 and practical 9th-string grip options including `4-5-6-9`; Voicing Identifier accepts `G / fret 10 / strings 4-5-6-9 / Open` and displays `D7`, `V7 in G`, notes `D, A, F#, C`, and `Dominant 7 / V7 grip`; glossary contains flat-7, dominant-7, V7, and 9th-string definitions; no `[object Object]` or browser console errors.
- Latest protected-preview Explorer Dominant 7 / V7 smoke: **PASS at commit `c6fa25e`**. The protected URL `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=dominant-v7-c6fa25e` loaded after Cloudflare Access authentication, served `e9-fretboard-explorer.js?v=dominant-v7-grips-20260627`, exposed the Dominant 7 / V7 grip vocabulary, showed practical 9th-string D7/V7 candidates, and displayed the exact D7/V7 identifier label for fret 10 strings 4-5-6-9. Browser console error log was empty.
- Current repo HEAD at implementation refresh: `a08eba4 feat: add explorer chord voicing finder`; status refresh commit follows separately.
- Runtime commit smoked for E9 copedent selector/chart: `ecec173 feat: add E9 copedent selector and chart`.
- Related impact-preview runtime smoke: `670d635 feat: add e9 pedal lever impact preview contract`.
- Latest local UI smoke status: **PASS for Explorer Voicing Identifier control polish at commit `de7f545`**. Local browser smoke verified `Voicing identifier` appears in Explore mode, Fret is constrained to `1` through `10`, Strings use selectable chips with a maximum of three selections, pedals/levers are individually multi-selectable, combined preset buttons such as `A+B` and `B+C` are absent, `F / fret 3 / strings 4-6-10 / A pedal + B pedal` computes `G, C, E` and identifies `C / V function in F`, odd `G / fret 3 / strings 1-2-3 / open` calculates notes while warning that it is not a common musical grip, attempting a fourth string is blocked with a clear warning, and no `[object Object]` or relevant console errors appear.
- Protected-preview status: **PASS for Explorer Voicing Identifier control polish at commit `de7f545`, with version caveat**. The protected page loaded `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-controls-de7f545` after Cloudflare Access. Smoke verified Voicing Identifier mode, individual pedal/lever multi-select, no combined `A+B` / `B+C` preset buttons, max-three string selection behavior, `F / fret 3 / strings 4-6-10 / A pedal + B pedal` identifying `C / V function in F`, odd `G / fret 3 / strings 1-2-3 / open` calculating notes with a non-common-grip warning, blocked fourth string selection, no `[object Object]`, and no relevant console errors. `/api/version` still reports runtime SHA `4040a47`, so this pass verifies static UI behavior at the cache-busted page URL, not a runtime restart.
- User-smoke status: **ready for focused user smoke at the direct cache-busted Explorer URL below**.
- App control state: **park or choose the next small slice**.
- Repo audit status: **WARN / clean Explorer scope, dirty parked work remains**. Audit after the smoke-driven Explorer changes found no staged files and no dirty Explorer runtime/test files. The remaining dirty/untracked work is unrelated parked corpus/provenance/RAG/brand/design/documentation work and must not be broad-staged.
- Broad unrelated dirty/untracked work remains parked. Do not broad-stage.

## Protected URLs

Use direct `/ui/...?...` URLs for cache-busted validation after Cloudflare Access login:

```text
Explorer copedent selector/chart:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625

Explorer numeric marker readability after commit `bc69d97`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-marker-readability-20260626b

Explorer harmonized-scale clarity after commit `f2b28ef`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-harmonized-scale-clarity-f2b28ef

Explorer notation selector after commit `5ff8fcb`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-notation-mode-5ff8fcb

Explorer notation marker labels after commit `0b113af`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-notation-marker-labels-0b113af

Explorer top-note marker-source labels after commit `71a163e`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-top-note-marker-source-71a163e

Explorer harmonized scale path mode after commit `726cb80`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-harmonized-path-mode-726cb80

Explorer header button style after commit `cbb6313`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-header-button-style-cbb6313

Explorer compact glossary Close button after commit `3b0c1e1`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=glossary-close-compact-3b0c1e1

Explorer top-label chip order after commit `64f9fff`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=top-label-chip-order-64f9fff

Explorer path-mode string-group visibility after commit `7b934e6`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=path-string-group-visibility-7b934e6

Explorer compact control layout after commit `672ec51`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=compact-controls-672ec51

Explorer Voicing Identifier mode after commit `4ac80e8`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-identifier-4ac80e8

Explorer Voicing Identifier control polish after commit `de7f545`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-controls-de7f545

Explorer Dominant 7 / V7 grip vocabulary after commit `c6fa25e`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=dominant-v7-c6fa25e

Explorer marker/impact/glossary UI baseline commit `4a3f422`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-marker-impact-glossary-4a3f422

Main app:
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=explorer-compact-copedent-20260625

Root:
https://app.steelguitarrag.com/?v=explorer-compact-copedent-20260625
```

Root caveat:

- Root redirects to `/ui/steel-guitar-rag-mock.html`.
- Root drops query strings during redirect.
- Direct `/ui/...?...` URLs remain required when exact cache-busting matters.

## E9 Copedent Selector Status

Selector status: **PASS**.

Recorded behavior:

- `Emmons E9` is visible and selected by default.
- `Day E9` is visible and selectable.
- `My Copedent (E9)` is visible but disabled.
- Backstage/coming-soon copy is visible for the disabled personal copedent option.
- C6 is not exposed as an active Explorer copedent option.
- Existing Explorer key/scale/harmony/string-group controls remain available.
- No `[object Object]` was reported in the accepted selector/chart smoke.

## E9 Copedent Chart Status

Chart status: **PASS**.

Recorded behavior:

- Visual copedent chart renders in the Explorer.
- Chart shows strings 1-10.
- Chart shows open notes.
- Chart shows control columns for pedals and knee levers.
- Chart shows physical positions such as `P1`, `P2`, `P3`, `LKL`, `LKR`, `LKV`, `RKR`, and `RKL`.
- Chart shows note movement cells such as `B -> C#`, `E -> F`, `E -> Eb/D#`, `D -> C#`, and raise/lower labels.
- Day E9 switches physical pedal order to C-B-A while preserving named A/B/C semantics.
- Right-knee lever controls appear where present in the contract.

## Pedal / Lever Impact Preview Status

Impact preview status: **PASS with provenance caveat from earlier Lane 12 evidence**.

Recorded behavior:

- `Pedal and lever impact preview` section renders.
- Preview cards render A pedal, B pedal, C pedal, E-raise lever, and E-lower lever.
- Preview shows affected strings and before/after changes such as `B -> C#`, `G# -> A`, `E -> F#`, `E -> F`, and `E -> Eb/D#`.
- Selected-row detail renders `Changes used here`.
- Row-level active controls show string-level pedal effects.
- Explorer filtering remained functional during impact-preview smoke, including `5-7-8` reducing visible cards to that group.
- No `[object Object]` and no relevant console/page errors were reported.

Known impact-preview caveat:

- Earlier protected-preview impact-preview evidence was gathered while serving scoped Lane 06 Explorer UI worktree assets. The later copedent selector/chart commit now contains the selector/chart UI baseline, but future user-smoke defects should still be routed by exact slice rather than broad feature work.

## Compact Explorer / Copedent Controls Status

Local smoke status at commit `9a3513b`: **PASS**.

Protected-preview status at commit `5a59739`: **PASS WITH TOOLING CAVEAT AFTER CLOUDFLARE ACCESS AUTHENTICATION**.

Lane 12 authenticated rerun summary:

- Repo HEAD: `662679f`.
- Expected UI code commit: `5a59739`.
- Runtime commit: `4040a47`.
- Runtime contains `5a59739`: yes.
- Actual `/api/version`: `4040a47`.
- LaunchDaemon: running as `system/com.steelguitarrag.private-preview`.
- Listener: Python on `127.0.0.1:8770`.
- Previous stale runtime `ffac52a` is resolved.
- Protected browser URL tested:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-compact-copedent-20260625
```

- Result: authenticated protected-preview browser smoke passed for the compact Explorer/copedent UI.
- Cloudflare Access result: succeeded; the Explorer page loaded without Access login, verification-code, or sign-in text.
- Root behavior: unauthenticated root returns HTTP `302` to Cloudflare Access; authenticated root browser recheck was limited by browser automation attach loss after the Explorer smoke.
- API fallback status: not used as browser smoke.

Recorded behavior:

- Copedent chart is hidden by default and opens from a compact `View chart` dialog control.
- `Emmons E9` remains the default and no longer exposes the user-specific LKV/B-to-Bb control.
- `Custom E9 (with LKV)` is selectable and retains the LKV/B-to-Bb setup.
- External E9 reference context is not exposed in Explorer learner-facing UI or payload source context.
- Pedal/lever impact preview is compact by default and opens details from control tabs.
- Fretboard labels use either interval labels or note labels; they do not combine fret numbers with note/interval text.
- Authenticated protected-preview smoke showed the fretboard SVG present and partially visible at the fold in the current in-app browser viewport, with no horizontal overflow.
- Compact string-group filtering changed the visible card list to `4-5-6`; resetting to `All 3-string groups` restored the larger result set.
- Pedal/lever impact preview was compact and interactive; selecting `A pedal` changed the selected control detail.
- Notes / Intervals toggle worked.
- No relevant console errors were captured.
- Desktop local smoke at 1280x720 showed the fretboard visible without scrolling after the compact control pass.
- Mobile local smoke at 390x844 had no page-level horizontal overflow; the fretboard remains below the first viewport because of normal mobile stacking.

Smoke Target:

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
- Expected git HEAD: 662679f; expected UI code commit: 5a59739
- Version endpoint: http://127.0.0.1:8770/api/version
- Version endpoint result: git_sha=4040a47; runtime contains UI commit 5a59739
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: unauthenticated root returns Cloudflare Access 302; authenticated root browser recheck was limited by browser automation attach loss after Explorer smoke
- Whether app root `/` is expected to work: yes, protected root redirects to app UI
- Whether `/ui/steel-guitar-rag-mock.html` works: expected yes; not the primary URL for this Explorer-only smoke
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user
- Do not test these URLs: uncache-busted Explorer URLs for this slice
- Known caveats: direct `/ui/...?...` URL remains required for exact cache-busted Explorer smoke; browser automation detached during temporary-tab root/version checks after the Explorer smoke
```

## Explorer Marker / Impact / Glossary Status

Local smoke status for marker/impact/glossary baseline at commit `4a3f422`: **PASS**.

Marker readability status at commits `0ec8932` and `bc69d97`: **PASS locally and on protected preview**.

Lane 06 local browser smoke summary:

- Exact local URL tested:

```text
http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-marker-impact-glossary-20260626e
```

- Fretboard rendered.
- SVG marker labels were compact (`2 pos.`, short note/interval cues) rather than long multi-value labels.
- Same-fret/string-group marker tooltip exposed both positions for the grouped `fret 3 / 4-5-6` case.
- Position cards above the fretboard rendered as a wrapping grid.
- Notes / Intervals mode updated active cards and marker labels.
- Glossary opened and closed and used learner-facing terms only.
- Pedal/lever impact preview supported multi-select and clear/reset.
- E-lower on `3-5` reported no direct impact and named affected strings `4, 8`.
- B pedal on `3-5` reported `String 3 G# -> A` and included a B-alone caution.
- A+B together reported string 5 and string 6 changes.
- No `[object Object]`.
- No relevant browser console warnings/errors.

Unreadable marker bug fix summary:

- Commit `0ec8932` changed default SVG marker labels from musical note/interval blobs to compact marker IDs such as `1`, `1+`, `2`, etc.
- Cards now show matching `Marker N` badges and carry `data-marker-id`.
- Card click/selection maps back to a selected SVG marker.
- Full notes/intervals/pedals/levers remain available through marker tooltip/aria labels and selected-card detail.
- Commit `bc69d97` refreshed `e9-fretboard-explorer.js` to `?v=explorer-marker-readability-20260626`; this was required because protected preview initially still loaded the old script query and reproduced long labels.

Protected-preview marker readability smoke: **PASS**.

Protected-preview URL tested and recommended for focused smoke:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-marker-readability-20260626b
```

Protected smoke result:

- Page loaded without Cloudflare Access challenge in the authenticated in-app browser.
- Script list included `e9-fretboard-explorer.js?v=explorer-marker-readability-20260626`.
- Rendered marker labels were numeric/short (`1+`, `2+`, `3`...`30`).
- `longLabels` was empty.
- 34 visible cards had marker IDs and marker text.
- Clicking a card resulted in exactly one selected card and one selected SVG marker.
- No `[object Object]`.
- No console errors.

## Latest Relevant Handoffs

- `docs/handoffs/task-completions/2026-06-23-12-e9-copedent-selector-protected-smoke.md`
- `docs/handoffs/task-completions/2026-06-23-15-e9-copedent-selector-qa.md`
- `docs/handoffs/task-completions/2026-06-23-06-e9-copedent-selector-chart.md`
- `docs/handoffs/task-completions/2026-06-24-12-e9-pedal-lever-impact-preview-protected-smoke.md`
- `docs/handoffs/task-completions/2026-06-24-1045-06-e9-pedal-lever-impact-preview-ui.md`
- `docs/handoffs/task-completions/2026-06-25-1920-06-explorer-compact-copedent-ui.md`
- `docs/handoffs/task-completions/2026-06-25-2045-12-explorer-compact-copedent-protected-smoke.md`
- `docs/handoffs/task-completions/2026-06-25-2052-12-explorer-compact-copedent-protected-smoke-rerun.md`
- `docs/handoffs/task-completions/2026-06-26-0906-12-explorer-compact-copedent-protected-smoke-authenticated.md`
- `docs/handoffs/task-completions/2026-06-26-0959-06-explorer-marker-impact-glossary.md`
- `docs/handoffs/task-completions/2026-06-26-1022-06-explorer-marker-readability.md`
- `docs/handoffs/task-completions/2026-06-26-1030-06-explorer-marker-script-cache-bust.md`

## Remaining Caveats

- Root URL redirects to `/ui/steel-guitar-rag-mock.html` and drops query strings.
- Direct `/ui/...?...` URLs remain required for cache-busted smoke.
- `deploy/macos/install-private-preview-launchdaemon.sh status` and `restart` need interactive sudo in this environment.
- Protected-preview marker readability smoke passed at direct cache-busted URL `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-marker-readability-20260626b`.
- Protected-preview browser smoke for compact Explorer/copedent UI passed after Cloudflare Access was completed in the in-app browser.
- Broad unrelated dirty/untracked files remain parked.

## Current Git / Worktree Notes

Current checked state at this refresh:

- Branch: `feature/answer-api`.
- Repo HEAD before this docs refresh: `bc69d97`.
- Cached index before this docs refresh: empty.
- `git diff --check`: passed before this docs refresh; rerun before commit.

Broad parked dirty/untracked work remains outside this refresh, including:

- README/docs/provenance/legal/source-policy edits.
- Corpus metadata and source-inbox metadata.
- Root RAG/corpus helper scripts.
- Private/corpus-adjacent scripts and data.
- Landing/sign/brand assets and generated visual files.
- Historical untracked handoffs and screenshot/report assets.

Do not stage parked work unless a later exact-scope handoff approves it.

## Safe To Stage For This Refresh

- `docs/handoffs/task-completions/integration-status.md`

## Files Not To Stage For This Refresh

- Backend/runtime files, tests, UI files, deployment/launchd files, auth/DNS/Cloudflare config, tunnel files, source files, paid transcript files, or app assets.
- `corpus-private/`, `corpus-v2/`, Chroma/vector stores, embeddings, generated corpus outputs, scraper output, source-inbox raw/provenance files.
- Deployment secrets, private env files, rendered plists, tunnel tokens, tunnel credentials, `.wrangler/`, and any secrets.
- `public/`, `ui/brand/`, `Neon Sign/`, raw design assets, generated visual assets, and unrelated UI/assets.
- Unrelated handoffs or generated reports.

## Recommended Next Slice

Lane 12 protected-preview restart/smoke for commit `4a3f422`, then user smoke the Explorer marker/impact/glossary UI at the direct cache-busted Explorer URL.

Recommended next slice if continuing:

- Lane 12: verify protected preview serves commit `4a3f422` and smoke the Explorer marker/impact/glossary UI.

Recommended exact control step:

```text
Lane 12: Restart/verify protected preview for commit 4a3f422, then smoke https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-marker-impact-glossary-4a3f422. Verify compact marker labels, grouped marker tooltip, Notes/Intervals, Glossary, contextual impact, A+B multi-select, no [object Object], no console errors, and /api/version HEAD.
```
