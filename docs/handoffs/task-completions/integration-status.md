# Integration Status - Current Reset Snapshot

Generated for ChatGPT reset/guidance on branch `feature/answer-api`.

## Current State

- Current branch: `feature/answer-api`.
- Latest Explorer compact tools cleanup commit: `dc54893 fix: compact explorer fretboard controls`. This commit moves the scale summary into the Explorer controls box, compacts the fretboard display tools into a wrapping row, removes the duplicate visible `Labels` heading beside the `String labels` toggle, removes copedent/profile copy and the extra context sentence from the Pedal and lever impact panel, and shortens lever impact buttons to `F`, `E`, `G`, and `D` while preserving internal control IDs. Focused checks passed: `node --check` for Explorer/data/answer/fretboard JS, `tests/test_frontend_answer_ui.py`, `tests/test_pedal_steel_fretboard_ui.py`, `tests/test_fretboard_explorer.py`, and `git diff --check`.
- Latest protected-preview Explorer compact tools cleanup smoke: **PASS / static-browser behavior verified**. Protected URL `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=compact-explorer-tools-dc54893` loaded after prior Cloudflare Access authentication and served `e9-fretboard-explorer.js?v=compact-explorer-tools-20260628`. Smoke verified the scale summary is inside the controls box, the old standalone scale pill is absent, the fretboard display tools use a compact wrapping row, the visible duplicate `Labels` heading is gone, the `String labels` control remains present, the impact preview no longer shows copedent/profile copy or the `Choose one or more controls...` context sentence, levers appear as `F`, `E`, `G`, and `D`, no `[object Object]`, no page-level horizontal overflow in the measured viewport, and no relevant console warnings/errors.
- Latest Explorer Voicing Identifier copy cleanup commit: `b02e9c6 fix: clarify voicing identifier copy`. This commit removes the redundant learner-facing active-results sentence `Card and SVG marker show the same fret/string group.` and changes Voicing Identifier summaries to chord-first language, e.g. `C chord (IV function in G)`. It also explains alternate spread grips that use string 4 instead of string 8, refreshes `e9-fretboard-explorer.js` to `?v=voicing-identifier-copy-20260627`, and adds focused frontend regression coverage. Focused checks passed: `node --check` for Explorer/fretboard/answer JS, `tests/test_frontend_answer_ui.py`, `tests/test_pedal_steel_fretboard_ui.py`, local browser smoke at `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=voicing-identifier-copy-local`, and `git diff --check`.
- Latest local Explorer Voicing Identifier copy smoke: **PASS / local static-browser behavior verified**. Smoke used Voicing Identifier mode, G major, fret 3, strings 4-6-10, A pedal + B pedal. It verified `C chord (IV function in G)`, `String 4 gives G, String 6 gives C, String 10 gives E`, the string-4/string-8 alternate-grip explanation, no redundant card/SVG sentence, no `[object Object]`, and no console errors.
- Latest protected-preview Explorer Voicing Identifier copy smoke: **PASS / static-browser behavior verified**. Protected URL `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-identifier-copy-b02e9c6` loaded after prior Cloudflare Access authentication and served `e9-fretboard-explorer.js?v=voicing-identifier-copy-20260627`. Smoke verified Voicing Identifier mode, G major, fret 3, strings 4-6-10, A+B, `C chord (IV function in G)`, the string-4/string-8 alternate-grip explanation, no redundant card/SVG sentence, no `[object Object]`, and no console errors. This verifies cache-busted static/browser behavior rather than a Python runtime restart.
- Latest Explorer Chord / Voicing Finder card-label cleanup commit: `bec3847 fix: clean up chord map card labels`. This commit fixes chord-map candidate cards so long field values render in dedicated label/value rows instead of writing across adjacent columns. It also disables ambiguous SVG top labels only for Chord / Voicing Finder fretboard markers, leaving top-note context in the card/detail/tooltip surfaces while preserving labels in other Explorer modes. Focused checks passed: `node --check` for Explorer/fretboard/answer JS, `tests/test_frontend_answer_ui.py`, `tests/test_pedal_steel_fretboard_ui.py`, local browser smoke, protected-preview browser smoke, and `git diff --check`.
- Latest protected-preview Explorer Chord / Voicing Finder card-label cleanup smoke: **PASS / static-browser behavior verified**. Protected URL `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-label-cleanup-bec3847` loaded after prior Cloudflare Access authentication and served `e9-fretboard-explorer.js?v=chord-map-label-cleanup-20260627`. Smoke verified Chord / Voicing Finder with `F` + `Dominant 7`, card fields using label/value grid rows with wrapping, no SVG top-note labels above markers in chord-map mode, no `[object Object]`, no page-level horizontal overflow, and no console errors.
- Latest Explorer impact-control grouping commit: `e80d637 fix: group explorer impact controls`. This commit changes the Pedal and lever impact controls from one flat row into labeled groups: `Pedals` with compact `A`, `B`, and `C` buttons, and `Levers` with the existing lever controls. It keeps the same internal control IDs, clear behavior, detail-panel text, fretboard behavior, and Explorer cache-busts. Focused checks passed: `node --check` for Explorer/fretboard/answer JS, `tests/test_frontend_answer_ui.py`, `tests/test_pedal_steel_fretboard_ui.py`, and `git diff --check`.
- Latest protected-preview Explorer impact-control grouping smoke: **PASS / static-browser behavior verified**. Protected URL `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=impact-control-groups-e80d637` loaded after prior Cloudflare Access authentication. Smoke verified Harmonized scale path mode, impact controls grouped under `Pedals` and `Levers`, pedal button labels `A`, `B`, and `C`, lever controls preserved, clear button preserved, no `[object Object]`, no page-level horizontal overflow, and no console errors.
- Latest Explorer path-card color-link commit: `44b0c38 fix: color link explorer path cards`. This commit makes Harmonized scale path rail cards use the same marker-tone color system as the result cards and SVG fretboard highlights. It adds `data-marker-tone` and `data-string-group` metadata to path step cards, updates path-card CSS to read `--explorer-marker-color`, and refreshes `e9-fretboard-explorer.js` to `?v=path-card-colors-20260627`. Focused checks passed: `node --check` for Explorer/fretboard/answer JS, `tests/test_frontend_answer_ui.py`, `tests/test_pedal_steel_fretboard_ui.py`, and `git diff --check`.
- Latest protected-preview Explorer path-card color-link smoke: **PASS / static-browser behavior verified**. Protected URL `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=path-card-colors-44b0c38` loaded after prior Cloudflare Access authentication. Smoke verified Harmonized scale path mode, eight path rail cards, marker tones `1` through `8`, string groups `6-8-10` and `6-7-10`, SVG highlights with matching marker-tone metadata, distinct computed card colors by marker tone, no `[object Object]`, no page-level horizontal overflow, and no console errors.
- Latest Explorer compact display-controls commit: `c515c5a fix: compact explorer fretboard display controls`. This commit removes the redundant active-result summary copy above Explorer cards, including strings like `all 3-string groups: 33 visible positions` and `Cards match the SVG markers below.` It also groups Notation, Pitch register, and Labels into one fretboard display-control row and changes the marker-detail control into a compact `String labels` switch. Focused checks passed: `node --check` for Explorer/fretboard/answer JS, `tests/test_frontend_answer_ui.py`, `tests/test_pedal_steel_fretboard_ui.py`, and `git diff --check`.
- Latest protected-preview Explorer compact display-controls smoke: **PASS / static-browser behavior verified**. Protected URL `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=compact-fretboard-tools-c515c5a` loaded after prior Cloudflare Access authentication and served `e9-fretboard-explorer.js?v=compact-fretboard-tools-20260627`. Smoke verified the active-result summary text was removed, the compact Labels toggle rendered at about 129px by 30px, `Marker detail` text was absent, the controls appeared before the card/fretboard area, no `[object Object]`, no console errors, and no horizontal overflow in the measured viewport. The first protected attempt at `?v=compact-fretboard-tools-8538645` showed stale active-result text until the Explorer script cache-bust was refreshed.
- Latest Explorer string/action marker-label commit: `d5a8b63 feat: add explorer string action marker labels`. This commit adds an optional `String labels` toggle near the Explorer fretboard. The default is off; toggling on renders compact per-string marker labels such as `3B`, `4C`, and `5C` directly on selected/visible SVG marker bubbles, with shorthand mapping for A/B/C pedals, E-raise as `F`, E-lower as `E`, D/G levers as `D`/`G`, and B-to-Bb/LKV/vertical as `V`. It keeps learner-facing per-string detail text separate from compact marker metadata. Focused checks passed: `node --check` for Explorer/data/answer/fretboard JS, Explorer musical red-team tests, Explorer backend tests, frontend answer UI tests, pedal-steel fretboard UI tests, and `git diff --check`. Local browser smoke passed at `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=string-action-labels-local`.
- Latest protected-preview Explorer string/action marker-label smoke: **PASS / static-browser behavior verified with runtime-version caveat**. Protected URL `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=string-action-labels-d5a8b63` loaded after prior Cloudflare Access authentication and showed the new `String labels` toggle. Detailed protected smoke at `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=string-action-labels-8b9ae59` verified default off, Voicing Identifier strings 3-4-5 with B+C pedals rendering `3B`, `4C`, `5C` when toggled on, toggling off removing labels, no invalid marker labels, no `[object Object]`, no console errors, no horizontal overflow, and no marker metadata leaking into detail text. Root redirected to `/ui/steel-guitar-rag-mock.html`. `/api/version` reports runtime SHA `a6abc61`, so Lane 12 should refresh/restart protected preview before a strict runtime-version pass.
- Latest Explorer octave/register awareness commit: `9851e7c feat: add explorer pitch register display`. This commit adds deterministic scientific-pitch/register metadata to standard E9 Explorer rows, selected copedent strings, control-impact previews, shared browser music rules, and the static Explorer data bundle. It adds a `Pitch register` display control with Off, Scientific, and Octave band modes, keeps SVG marker labels uncluttered, and adds glossary entries plus a Peterson/StroboPlus follow-up note. Checks passed: `py_compile` for changed backend modules, `node --check` for Explorer/data/music-rules/answer/fretboard JS, focused Explorer/frontend/fretboard/API tests, `git diff --check`, and full `.venv/bin/python -m pytest` with `864 passed`. Local in-app browser smoke was attempted at `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-octave-register-local-20260627` but blocked by browser webview attach timeout, so this commit still needs Lane 12/Lane 15 protected-preview browser smoke before user smoke.
- Current Explorer octave/register URL after commit `9851e7c`: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-octave-register-9851e7c` after Cloudflare Access login. Use this direct cache-busted URL after protected-preview runtime/static refresh; root redirects to the app shell and drops query strings.
- Latest public landing redesign commit: `4181985 feat: redesign public landing page`. This commit replaces the prior public static landing page with a dark premium, stage-lit, Explorer-first page matching the attached references. It keeps the top-left hanging sign, local static assets, interest-list form contract, and no public `/api/answer` or app-shell exposure from the landing HTML. Focused checks passed: `git diff --check`, `.venv/bin/python -m pytest tests/test_public_landing_page.py -q` with 34 passed, and `.venv/bin/python -m pytest tests/test_same_origin_smoke_server.py -q` with 12 passed. Local browser smoke passed at `http://127.0.0.1:8770/ui/steel-guitar-rag-landing.html?v=dark-premium-landing-local-2`.
- Latest protected-preview public landing smoke: **PASS / static-browser behavior verified with root-routing and runtime-version caveats**. Direct URL `https://app.steelguitarrag.com/ui/steel-guitar-rag-landing.html?v=dark-premium-landing-4181985` loaded after prior Cloudflare Access authentication. Smoke verified the dark premium landing page, H1 `Explore the neck. Ask better questions.`, top-left hanging sign, Explorer preview, five mode cards, Brain section, `Unlock the full explorer` CTA, no app-shell exposure from the static landing page, no page-level horizontal overflow on desktop or narrow/mobile viewport, no `[object Object]`, and no relevant console warnings/errors. Root `https://app.steelguitarrag.com/?v=dark-premium-landing-4181985` still redirects to `/ui/steel-guitar-rag-mock.html` and drops the query string. Local `/api/version` reports runtime SHA `a6abc61`, so this verifies cache-busted static/browser behavior, not a restarted Python runtime at `4181985`.
- Recent Explorer integration closeout commit: `ec42aa1 docs: record chord finder map view smoke`. This branch contains the required recent Explorer commits: `b55a12e feat: add shared explorer music rules boundary`, `dba7347 fix: improve explorer mobile control density`, `d988db7 fix: use structured chord finder controls`, and `c423e4b feat: map chord finder candidates on fretboard`.
- Latest full Explorer integration closeout: **PASS/WARN**. Focused checks passed for Explorer JS, shared music rules JS, Explorer data JS, answer/fretboard JS syntax, Explorer musical red-team tests, Explorer backend tests, frontend answer UI tests, pedal-steel fretboard UI tests, and API contract tests. Protected Chrome session loaded the cache-busted Explorer at `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=integration-closeout-ec42aa1` after Cloudflare Access authentication; prior protected map-view smoke remains the detailed interaction proof at `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-view-c423e4b`. Non-interactive LaunchDaemon restart was blocked because `sudo` requires a password, so local `/api/version` still reports runtime SHA `a6abc61`; this is a strict runtime-version warning, not an Explorer static/browser behavior failure.
- Current Explorer user-smoke URL: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=integration-closeout-ec42aa1` after Cloudflare Access login. Use direct `/ui/...?...` URLs for cache-busted validation because root redirects to the app shell and drops query strings.
- Latest implementation commit: `c423e4b feat: map chord finder candidates on fretboard`.
- Latest Explorer Chord / Voicing Finder map-view commit: `c423e4b feat: map chord finder candidates on fretboard`. This commit makes Chord / Voicing Finder render the filtered candidate set on the SVG fretboard instead of showing only the selected candidate. It adds learner-facing map filters for All, Open, Pedals, Levers, Low frets, Mid frets, High frets, Complete, and Core; keeps cards and SVG markers in sync; resets selection when filters/root/quality/scope change; and refreshes `e9-fretboard-explorer.js` to `?v=chord-map-view-20260627`. Local checks passed: `node --check` for Explorer/data/answer/fretboard JS; focused frontend, fretboard UI, Explorer red-team, Explorer backend, and API contract tests. Local browser smoke passed at `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=chord-map-view-local`, verifying `F` + `Major` + `All practical` shows 24 cards and 13 marker clusters, Open reduces to 8 cards and 8 markers, card/marker selection syncs, and no `[object Object]` appears.
- Latest protected-preview Explorer Chord / Voicing Finder map-view smoke: **PASS / static-browser behavior verified with version-endpoint caveat**. Protected URL `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-view-c423e4b` loaded after prior Cloudflare Access authentication and served `e9-fretboard-explorer.js?v=chord-map-view-20260627`. Smoke verified Chord / Voicing Finder, `F` + `Major` + `All practical` controls, 24 candidate cards, 13 SVG marker clusters, map filters, Open reducing to 8 open cards and 8 markers, card selection updating the matching SVG marker/detail panel, no `[object Object]`, no relevant console warnings/errors, root redirecting to `/ui/steel-guitar-rag-mock.html`, and the direct app shell URL loading. `/api/version` could not be read through browser direct navigation because the browser reported `net::ERR_BLOCKED_BY_CLIENT`, so this verifies protected static/browser behavior at the cache-busted URL rather than strict runtime SHA proof.
- Latest structured Chord / Voicing Finder commit: `d988db7 fix: use structured chord finder controls`. This commit removes the visible free-text `Target chord or function` input from the Explorer Chord / Voicing Finder main workflow and makes the visible UI use structured Root, Quality, and Pedals / levers scope controls. It preserves internal parser utilities for compatibility, keeps backend/music rules unchanged, adds learner-facing quality labels, includes sharp/flat root options, and refreshes `e9-fretboard-explorer.js` to `?v=structured-chord-picker-20260627`. Local checks passed: `node --check` for Explorer/data/answer/fretboard JS; focused frontend/fretboard/Explorer musical red-team/backend Explorer tests; and full `.venv/bin/python -m pytest -q` with `861 passed`. Local browser smoke passed at `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=structured-chord-picker-local`.
- Latest protected-preview structured Chord / Voicing Finder smoke: **PASS / static-browser behavior verified with version-endpoint caveat**. Protected URL `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=structured-chord-finder-d988db7` loaded after prior Cloudflare Access authentication and served `e9-fretboard-explorer.js?v=structured-chord-picker-20260627`. Smoke verified no free-text target input, Root options with sharp/flat spellings, learner-facing Quality options, default `Fmaj7`, `D` + `Dominant 7` resolving to `Target: D7` candidates, fretboard highlights, no normal-use parser errors, no `[object Object]`, and no relevant console warnings/errors. Root `/` redirected to `/ui/steel-guitar-rag-mock.html`. `/api/version` could not be read through the browser tool because the endpoint open was blocked with `net::ERR_BLOCKED_BY_CLIENT`, so this pass verifies protected static/browser behavior at the cache-busted URL rather than strict runtime SHA proof.
- Latest Explorer shared music-rules boundary commit: `b55a12e feat: add shared explorer music rules boundary`. This commit implements the additive copedent naming cleanup contract in the deterministic Explorer backend/static payload path, keeping stable semantic control IDs while adding learner-facing display labels, mechanical names, player shorthand, compatibility aliases, physical positions, travel/change type, affected strings, and per-string action metadata. It also routes Explorer UI control labels through the new display-label fields and keeps the shared deterministic pitch/voicing rules as the source of truth. Local checks passed: `py_compile` for `pocketsteel/e9_copedents.py` and `pocketsteel/fretboard_explorer.py`; `node --check` for `ui/e9-fretboard-explorer.js`, `ui/e9-fretboard-explorer-data.js`, `ui/answer-client.js`, and `ui/pedal-steel-fretboard.js`; focused Explorer/API/frontend tests; and full `.venv/bin/python -m pytest` with `861 passed`. Local browser smoke passed at `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=shared-rules-contract-local-smoke-20260627`, verifying cleaned control labels, Custom E9/LKV naming, major-7 vs dominant-7 voicing behavior, no `[object Object]`, and no relevant console warnings/errors. Protected preview was not restarted in this Lane 05 run; Lane 12 should restart/verify runtime before protected user smoke.
- Latest protected-preview Explorer shared music-rules boundary smoke: **PASS / strict runtime proof complete**. After the user performed the interactive Mac mini LaunchDaemon restart, local `/api/version` reports runtime SHA `a6abc61` on `feature/answer-api` with `server_started_at=2026-06-27T17:30:30.410070+00:00`; `a6abc61` contains implementation commit `b55a12e feat: add shared explorer music rules boundary`. Protected URL `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=shared-rules-boundary-b55a12e` loaded after Cloudflare Access authentication and served `e9-music-rules.js?v=shared-music-rules-20260627` plus `e9-fretboard-explorer.js?v=shared-music-rules-20260627`. Smoke verified Explorer load, no `[object Object]`, no relevant console warnings/errors, cleaned copedent/control labels, Emmons without learner-facing LKV/B-to-Bb controls in the impact section, Custom E9 with LKV/B-to-Bb semantics, Voicing Identifier, Chord / Voicing Finder, Fmaj7 major-7 candidates with omitted tones and no dominant/V7 mislabel, grip vocabulary changing Fmaj7 breadth from 14 Core candidates to 24 All practical candidates, V7 in G resolving to D7 candidates, Cmin9/Cm9 parsing to a clear no-practical-voicing state, selected result state, notation controls, no page-level horizontal overflow at 1280x720, and root redirecting to `/ui/steel-guitar-rag-mock.html` while dropping the query string. API fallback was not used. The direct cache-busted Explorer URL is ready for user smoke.
- Previous Explorer mobile-density commit: `dba7347 fix: improve explorer mobile control density`.
- Latest Explorer mobile-density commit: `dba7347 fix: improve explorer mobile control density`. This commit changes only the Explorer static UI/CSS and a focused frontend assertion: the visible result cards render as a horizontal scroll rail instead of a deep multi-row wall before the fretboard, and narrow chip groups use one-line horizontal scrolling. Local checks passed (`node --check` for Explorer/data/answer/fretboard JS, `tests/test_frontend_answer_ui.py`, `tests/test_fretboard_explorer.py`, `tests/test_pedal_steel_fretboard_ui.py`). Local browser smoke passed at `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=explorer-mobile-density-371de09-local`. Protected-preview browser smoke passed at `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-mobile-density-84844bb`; Cloudflare Access was already authenticated, no `[object Object]` or console warnings/errors appeared, desktop/mobile result rails rendered with horizontal scrolling, Glossary/Copedent dialogs opened and closed, and the protected URL remained page-level overflow-free. `/api/version` still reports runtime SHA `4040a47`, so the result verifies protected static/browser behavior at the cache-busted Explorer URL rather than a Python runtime restart to `dba7347`.
- Latest public landing redesign commit: `3c78758 feat: redesign landing page around explorer and brain`.
- Latest local public landing smoke: **PASS at commit `3c78758` for direct static landing URL `http://127.0.0.1:8770/ui/steel-guitar-rag-landing.html?v=landing-explorer-brain-local-visual-2`**. Smoke verified an Explorer-first hero, large E9 fretboard preview above the fold on desktop, top navigation for Fretboard Explorer and Brain paths, five Explorer mode cards, compact lower Steel Guitar Brain band, no page-level horizontal overflow on desktop/tablet/mobile checks, no relevant console errors, and no public `/api/answer` or private app-shell link exposure from the static landing HTML. Local root `http://127.0.0.1:8770/` still redirects to `/ui/steel-guitar-rag-mock.html`.
- Latest protected-preview public landing smoke: **PASS for direct static landing URL `https://app.steelguitarrag.com/ui/steel-guitar-rag-landing.html?v=landing-redesign-3c78758`, with root-routing caveat**. Cloudflare Access was already authenticated in the in-app browser. Direct static landing URL showed `Explore the E9 neck. Ask better questions.`, Explorer hero, compact Brain band, five mode cards, no page-level horizontal overflow, no relevant console errors, and no `/api/answer` or `steel-guitar-rag-mock.html` exposure from static landing HTML. Protected root `https://app.steelguitarrag.com/?v=landing-redesign-3c78758` still redirects to `/ui/steel-guitar-rag-mock.html` and shows the app shell hero `Ask the steel guitar brain.` `/api/version` reports runtime SHA `4040a47`, so this verifies cache-busted static file behavior rather than a runtime restart to `3c78758`. Lane 12 / product should confirm whether root should serve the redesigned landing page or continue app-shell redirect behavior before user smoke.
- Latest local Explorer Chord / Voicing Finder smoke: **PASS at commit `a08eba4`**. Local browser smoke verified `Chord / Voicing Finder` is selectable at `http://127.0.0.1:8770/ui/e9-fretboard-explorer.html?v=chord-voicing-finder-local-2`; `Fmaj7` returned practical partial and complete candidates without dominant-7 mislabeling; `Cmin9` parsed as `Cm9` and produced a clear no-practical-candidate state under default filters; `V7 in G` resolved to `D7`; selecting a candidate updated the selected card/detail and kept one selected SVG highlight; changing Grip vocabulary from Core to All practical expanded Fmaj7 candidates from 14 to 24; no `[object Object]` or `omitted 0` text appeared.
- Protected-preview Explorer Chord / Voicing Finder smoke: **WARN / browser behavior passed with runtime-version caveat**. Protected URL `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-voicing-finder-a08eba4` loaded after Cloudflare Access authentication and served `e9-fretboard-explorer.js?v=chord-voicing-finder-20260627`. Smoke verified `Chord / Voicing Finder` is selectable; `Fmaj7` returned 14 Core partial candidates with omitted tones and 24 All practical candidates including complete high-confidence `4-5-6-9` candidates; `Cmin9` parsed as `Cm9` and showed a clear no-practical-voicing state under Core; `V7 in G` resolved to `D7` candidates; selecting a result highlighted one fretboard marker; changing Grip vocabulary changed candidate breadth; no `[object Object]` or relevant console errors appeared. `/api/version` still reports runtime SHA `4040a47`, which does not contain `a08eba4`, so this verifies protected static/browser behavior at the cache-busted URL rather than a clean runtime restart to the current UI commit.
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
Explorer compact tools cleanup after commit `dc54893`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=compact-explorer-tools-dc54893

Explorer octave/register awareness after commit `9851e7c`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=explorer-octave-register-9851e7c

Explorer string/action marker labels after commit `d5a8b63`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=string-action-labels-d5a8b63

Explorer compact display controls after commit `c515c5a`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=compact-fretboard-tools-c515c5a

Explorer path-card color linkage after commit `44b0c38`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=path-card-colors-44b0c38

Explorer impact-control grouping after commit `e80d637`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=impact-control-groups-e80d637

Explorer Chord / Voicing Finder card-label cleanup after commit `bec3847`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-label-cleanup-bec3847

Explorer Voicing Identifier copy cleanup after commit `b02e9c6`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=voicing-identifier-copy-b02e9c6

Explorer shared music-rules / copedent naming boundary after commit `b55a12e`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=shared-rules-boundary-b55a12e

Explorer structured Chord / Voicing Finder after commit `d988db7`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=structured-chord-finder-d988db7

Explorer Chord / Voicing Finder map view after commit `c423e4b`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-map-view-c423e4b

Dark premium public landing page after commit `4181985`:
https://app.steelguitarrag.com/ui/steel-guitar-rag-landing.html?v=dark-premium-landing-4181985

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

Explorer Chord / Voicing Finder after commit `a08eba4`:
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-voicing-finder-a08eba4

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
- `docs/handoffs/task-completions/2026-06-27-1140-12-chord-voicing-finder-protected-smoke.md`
- `docs/handoffs/task-completions/2026-06-27-1227-12-shared-rules-protected-preview-completion.md`

## Remaining Caveats

- Root URL redirects to `/ui/steel-guitar-rag-mock.html` and drops query strings.
- Direct `/ui/...?...` URLs remain required for cache-busted smoke.
- `/api/version` for the protected Mac mini runtime still reports `4040a47`; recent static Explorer UI smoke can pass via cache-busted static assets even when the Python runtime version endpoint is older.
- The documented LaunchDaemon restart path requires interactive `sudo`; Codex could not restart it in the non-interactive tool context on 2026-06-27. Run `deploy/macos/install-private-preview-launchdaemon.sh restart` in a local Terminal, then rerun Lane 12 if strict runtime provenance is required.
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
