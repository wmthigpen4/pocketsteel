# Mobile Chord Reader Playing Layout

## Task summary

- Corrected the prior incomplete mobile fix. Aligning the active row within the internal scroller did not remove the large information blocks above the timeline or fix ambiguous two-column reading order.
- Rebuilt the phone playing view so the persistent strip shows Play/Pause, the current chord, and the next chord.
- Moved the one-column chord timeline immediately below the persistent strip on phones.
- Moved song metadata, audio scrubbing, timing diagnostics, confidence details, legend, and disclosure below the timeline on phones.
- Made mobile chord rows compact and full-width so the active row is first and the next change is directly beneath it.
- Bumped CSS to `v=4` and JavaScript to `v=5` for device cache invalidation.
- Left the pre-existing `integration-status.md` edit parked.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lanes: `15 QA / Answer Eval`, `12 Self-Hosted Deployment`, `01 Repo Steward`
- Mode: user-smoke mobile UI bug fix.

## Files changed

- `ui/chord-reader-owner-test/index.html`
- `ui/chord-reader-owner-test/owner-test.css`
- `ui/chord-reader-owner-test/owner-test.js`
- `tests/test_owner_chord_reader_ui.py`
- `docs/handoffs/task-completions/2026-08-26-1527-06-mobile-playing-layout.md`

## Tests and checks

- `.venv/bin/python -m pytest tests/test_owner_chord_reader_ui.py -q` — passed, 4 tests.
- `node --check ui/chord-reader-owner-test/owner-test.js` — passed.
- `node --test tests/owner_chord_reader_timing.test.js` — passed, 2 tests.
- `git diff --check` — passed.
- Protected-hostname browser smoke selected change 40 at `1:37.9` and verified the persistent strip showed current chord `1` and next chord `4` while the same change 40 card remained active.
- Playback was paused after smoke.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://chords.steelguitarrag.com/ui/chord-reader-owner-test/?v=mobile-playing-layout-1`
- Cache-busted URL tested: `https://chords.steelguitarrag.com/ui/chord-reader-owner-test/?v=mobile-playing-layout-1`
- Exact URL the user should use: `https://chords.steelguitarrag.com/`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded using the existing browser session
- Local backend URL: `http://127.0.0.1:8899`
- Expected backend port: `8899`
- Expected git HEAD: scoped mobile-playing-layout commit produced from prior HEAD `581cf147`
- Version endpoint: none; version inferred from the scoped commit and cache-busted assets
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not applicable
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: no
- Who should test this URL: Codex and the user
- Do not test these URLs: do not substitute `app.steelguitarrag.com`
- Known caveats: the Mac and port-8899 owner server must remain running

## Integration notes

- Desktop/tablet-wide layouts retain their multi-column timeline and complete control surface.
- At `560px` and below, `.reader-card` becomes an ordered flex layout: transport first, timeline second, supporting metadata afterward.
- At `560px` and below, the timeline is one column and each row is a compact two-area card.
- The mobile transport hides change number and elapsed time to prioritize Play/Pause, current chord, and next chord.
- Next-chord calculation handles a second chord within a split bar before advancing to the next timeline item.

## Risk assessment

- Risk: low. The change is isolated to the owner workbench and primarily to the phone media query.
- Rollback: revert the CSS/JS/HTML asset versions and mobile layout changes in this commit.

## Human decision needed

- No. User smoke can continue on the actual phone or tablet.

## Safe-to-stage exact file list

- `ui/chord-reader-owner-test/index.html`
- `ui/chord-reader-owner-test/owner-test.css`
- `ui/chord-reader-owner-test/owner-test.js`
- `tests/test_owner_chord_reader_ui.py`
- `docs/handoffs/task-completions/2026-08-26-1527-06-mobile-playing-layout.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `ui/chord-reader-owner-test/local-data/`
- Generated media, credentials, environment files, and logs

## Recommended next lane

- Lane 15 user smoke on the actual phone/tablet viewport.

## Commit readiness

Safe to commit

## Suggested next step

Reload `https://chords.steelguitarrag.com/` on the phone or tablet. Confirm the strip reads Play/Pause, current chord, next chord, followed immediately by the single-column chord list.
