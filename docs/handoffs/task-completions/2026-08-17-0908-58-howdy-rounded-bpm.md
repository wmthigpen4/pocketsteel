# Howdy rounded BPM

## Task summary

Rounded learner-facing BPM values to whole numbers while retaining the precise authored timing grid internally. The taught solo now displays `80 BPM`; the full song remains `158 BPM`. The printable tablature generator uses the same whole-number presentation rule.

## Files changed

- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/release.py`
- `tests/test_travis_companion.py`
- This handoff

## Verification

- `77 passed` across the companion and shared practice-tool suites.
- JavaScript syntax, Ruff, and `git diff --check` passed.
- Static bundle isolation verifier passed.
- In-app browser confirmed `Taught solo · 80 BPM`, `Full song · 158 BPM`, and no visible `79.8`.
- Regenerated all three printable-tab pages, extracted `80 BPM` from each, and confirmed `79.8` is absent.
- Rasterized and visually inspected all three PDF pages; headers, systems, page numbering, and footers remain present without clipping.

## Smoke Target

- Local route: `http://127.0.0.1:8897/practice-guide/howdy/`
- Authentication: none
- Expected behavior: whole-number BPM labels in the companion and printable PDF
- Caveat: local preview only

## Risks

- Rounding is presentation-only; playback and authored event boundaries continue using the precise internal grid.

## Human decision needed

None.

## Safe-to-stage list

- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/release.py`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-17-0908-58-howdy-rounded-bpm.md`

## Must-not-stage list

- `docs/handoffs/task-completions/integration-status.md` (pre-existing user edit)
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/` (generated/private partner artifacts)
- `tmp/`
- `~/.steel-rag/`

## Recommended next lane

Use the same whole-number BPM formatter for every future companion and printable artifact.

## Commit readiness

Safe to commit.
