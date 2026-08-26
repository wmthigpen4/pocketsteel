# Lane 06 — Owner chord-reader timing fix

## Task summary

Fixed the owner listening page so its active chord boxes follow the timing source
that actually passed validation. Songs with an anchored downbeat phase retain the
latest Travis beat-aligned bar display and switch supported split chords at the
bar midpoint. Songs with an unresolved phase now fall back automatically to the
frozen ensemble's exact raw transition timestamps instead of displaying a guessed
bar grid as authoritative.

The local server now also supports HTTP byte ranges for generated MP3 files. This
fixes card-to-timestamp seeking in Chrome and on mobile/tablet browsers; the old
full-file response caused card taps to restart playback at 0:00.

## Lane classification

- Primary lane: 06 UX/UI Design
- Supporting lanes: 05 local timing contract; 15 QA; 01 exact-path commit
- Task mode: approved Autopilot bug fix
- Deployment/auth/DNS: not changed; publishing remains a separate RED lane

## Files changed

- `package.json`
- `scripts/serve_owner_chord_reader.py`
- `ui/chord-reader-owner-test/index.html`
- `ui/chord-reader-owner-test/owner-test.css`
- `ui/chord-reader-owner-test/owner-test.js`
- `ui/chord-reader-owner-test/timing.js`
- `tests/test_owner_chord_reader_ui.py`
- `tests/owner_chord_reader_timing.test.js`
- this handoff

## Corrected first-song result

- Track: Goodness of God (Radio Version) — Jenn Johnson
- Prediction engine: frozen domain-gated v8 ensemble used by Travis validation
- Downbeat phase: unresolved, confidence 1.21%
- Display mode: `exact-model-transitions`
- Displayed changes: 96 raw ensemble segments
- Mean model confidence: 83.62%
- Example corrected boundary: G-sharp remains active through 17.999 seconds;
  C-sharp / NNS 4 activates at exactly 18.000 seconds
- The rejected bar adapter had activated that C-sharp box at 17.345 seconds,
  655 milliseconds before the model transition

Generated audio and predictions remain under ignored
`ui/chord-reader-owner-test/local-data/` and were not staged.

## Tests and checks

- `npm run check:js` — PASS
- `node --test tests/chord_phase_anchor.test.js tests/owner_chord_reader_timing.test.js` — PASS, 5 tests
- `.venv/bin/python -m pytest -q tests/test_owner_chord_reader_ui.py tests/test_travis_validation_ui.py tests/test_chord_reader_bar_product.py` — PASS, 17 tests
- Ruff format/check on the changed Python files — PASS
- `git diff --check` — PASS
- Full-engine rerun on the attached MOV — PASS; 92 evaluation bars, 96 exact display changes
- HTTP range smoke (`bytes=1000-1999`) — PASS, `206 Partial Content`, exact 1,000-byte range
- Browser media smoke — PASS; seekable range `0–234.4361` seconds
- Browser click smoke — PASS; Change 3 sought to 18.049 seconds and showed NNS 4
- Tablet breakpoint smoke — PASS; persistent transport computed `position: sticky`, remained visible, and synchronized at Change 96
- Browser console errors — none

## Smoke target

- URL: `http://127.0.0.1:8899/ui/chord-reader-owner-test/`
- Server: `.venv/bin/python scripts/serve_owner_chord_reader.py --host 127.0.0.1 --port 8899`
- Current state: server running and revised browser tab marked as the deliverable
- Auth: none; loopback-only binding remains enforced
- Public deployment: not attempted

## Risks

- Exact model timing removes the bar-grid timing error; it does not claim the
  predicted chord itself is correct.
- Very short raw predictions are preserved because suppressing or merging them
  would change the engine's transition contract. Low-confidence flickers remain
  visibly labeled for listening review.
- The localhost page still cannot be reached from a separate phone/tablet.
  Publishing needs an approved private upload/storage, analyzer runtime, auth,
  retention, and copyright-exposure design before it can be safe on the public
  Steel Guitar RAG domain.

## Human decision needed

Listen through this corrected localhost version. If the transition boxes now
track the recording correctly enough for owner testing, approve the private
deployment/auth design for `steelguitarrag.com`; no deployment action was taken
in this slice.

## Safe-to-stage exact file list

- `package.json`
- `scripts/serve_owner_chord_reader.py`
- `ui/chord-reader-owner-test/index.html`
- `ui/chord-reader-owner-test/owner-test.css`
- `ui/chord-reader-owner-test/owner-test.js`
- `ui/chord-reader-owner-test/timing.js`
- `tests/test_owner_chord_reader_ui.py`
- `tests/owner_chord_reader_timing.test.js`
- `docs/handoffs/task-completions/2026-08-26-1425-06-owner-chord-reader-timing-fix.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing user/coordination edit)
- `ui/chord-reader-owner-test/local-data/`
- the original Messages attachment
- unrelated generated, private, audio, model, cache, or corpus files

## Recommended next lane

After the owner listening smoke, Lane 18 should define the private mobile upload
and analyzer contract, Lane 11 should approve access control and retention, and
Lane 12 can implement/publish only after the user authorizes that RED deployment
scope.

## Commit readiness

Ready for an exact-path commit of the nine listed tracked paths. The unrelated
dirty integration-status file must remain unstaged.
