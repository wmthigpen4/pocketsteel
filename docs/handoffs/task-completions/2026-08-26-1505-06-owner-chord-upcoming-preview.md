# Owner Chord Reader Upcoming Preview

## Task summary

- Changed the owner chord-reader timeline so a newly active chord row aligns to the top of the scrollable chord window.
- This keeps upcoming changes visible below the active chord on phone and tablet layouts instead of parking the active card at the bottom edge.
- Replaced page-level `scrollIntoView` behavior with scrolling scoped only to the chord grid, preventing playback from moving the surrounding page.
- Bumped the owner JavaScript cache key from `v=3` to `v=4`.
- Intentionally left the pre-existing `integration-status.md` edit parked.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Supporting lanes: `15 QA / Answer Eval`, `12 Self-Hosted Deployment`, `01 Repo Steward`
- Mode: user-smoke UI bug fix under the approved owner-workbench scope.

## Files changed

- `ui/chord-reader-owner-test/owner-test.js`
- `ui/chord-reader-owner-test/index.html`
- `tests/test_owner_chord_reader_ui.py`
- `docs/handoffs/task-completions/2026-08-26-1505-06-owner-chord-upcoming-preview.md`

## Tests and checks

- `.venv/bin/python -m pytest tests/test_owner_chord_reader_ui.py -q` — passed, 4 tests.
- `node --check ui/chord-reader-owner-test/owner-test.js` — passed.
- `node --test tests/owner_chord_reader_timing.test.js` — passed, 2 tests.
- Protected-hostname browser smoke — passed.
- Selected change 40 at `1:37.9`; the same card remained active with `NOW`, and its row aligned to the top of the timeline with changes 41–60 visible after it.
- Playback was paused after smoke.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://chords.steelguitarrag.com/ui/chord-reader-owner-test/?v=active-preview-1`
- Cache-busted URL tested: `https://chords.steelguitarrag.com/ui/chord-reader-owner-test/?v=active-preview-1`
- Exact URL the user should use: `https://chords.steelguitarrag.com/`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded using the existing browser session
- Local backend URL: `http://127.0.0.1:8899`
- Expected backend port: `8899`
- Expected git HEAD: scoped upcoming-preview commit produced from prior HEAD `cbe4af87`
- Version endpoint: none; version inferred from the scoped commit and cache-busted UI asset
- Whether app root `/` works: yes
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not applicable
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: no
- Who should test this URL: Codex and the user
- Do not test these URLs: do not use `app.steelguitarrag.com` for this owner workbench
- Known caveats: the Mac and loopback chord-reader server must remain running

## Integration notes

- The new scroll calculation uses the active card and chord-grid bounding rectangles plus the grid's current `scrollTop`.
- Only the grid scroll position changes; the page viewport is left alone.
- The active card remains first in its row. On the two-column phone layout, subsequent changes remain beside and below it.

## Risk assessment

- Risk: low. The change is isolated to owner-workbench timeline scrolling and its cache key.
- Rollback: restore the prior `scrollIntoView({ block: "nearest" })` line and asset key, though that recreates the reported bottom-edge behavior.

## Human decision needed

- No. User smoke can continue.

## Safe-to-stage exact file list

- `ui/chord-reader-owner-test/owner-test.js`
- `ui/chord-reader-owner-test/index.html`
- `tests/test_owner_chord_reader_ui.py`
- `docs/handoffs/task-completions/2026-08-26-1505-06-owner-chord-upcoming-preview.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `ui/chord-reader-owner-test/local-data/`
- Any generated media, credentials, environment files, or logs

## Recommended next lane

- Lane 15 user smoke on the actual phone or tablet.

## Commit readiness

Safe to commit

## Suggested next step

Reload `https://chords.steelguitarrag.com/` on the phone or tablet and confirm the active row stays high enough to preview the upcoming chord changes while playing.
