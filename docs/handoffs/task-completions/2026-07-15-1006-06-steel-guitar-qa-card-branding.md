# Steel Guitar Q&A Landing Card Branding

## Task summary

Updated only the landing Ask feature card’s user-facing branding:

- Card title: `Steel Guitar Q&A`
- Primary CTA: `Open Q&A →`
- Supporting copy: `Get practical, teacher-first pedal-steel help grounded in trusted sources and your setup.`

Preserved the stable `ask-the-brain` ID, launch handlers, full-screen workspace wording/behavior, answer routing, backend APIs, suggested questions, active setup, sources, and all other branding.

## Files changed

- Landing-card copy hunk only in `ui/steel-guitar-rag-mock.html`
- `tests/test_landing_home_ui.py`
- This handoff

## Tests and checks

- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- Inline page script parsed with `vm.Script` — passed.
- `.venv/bin/python -m pytest -q tests/test_landing_home_ui.py tests/test_frontend_answer_ui.py tests/test_same_origin_smoke_server.py -k 'not test_backstage_plan_and_activity_uses_all_approved_assets'` — 72 passed.
- `git diff --check` — passed.
- Local desktop browser — exact title/CTA, zero card overflow, zero editable inputs, and CTA opened the existing blank focused Ask workspace.
- Local narrow browser — effective 520×1125 viewport, zero page/card overflow, no clipping, zero editable inputs.
- Browser warnings/errors — none.

## Integration notes

The full-screen workspace intentionally continues to read `Ask the Steel Guitar Brain`; the approved scope is landing-card-only. The HTML file contains unrelated parked Backstage/copedent work, so stage only the card-copy hunk.

## Risk assessment

Low. User-facing copy only, with exact card-boundary assertions and responsive browser verification.

## Human decision needed

No.

## Safe-to-stage exact file list

- `tests/test_landing_home_ui.py`
- `docs/handoffs/task-completions/2026-07-15-1006-06-steel-guitar-qa-card-branding.md`
- Landing-card copy hunk only from `ui/steel-guitar-rag-mock.html`

## Files that must not be staged

All unrelated dirty/untracked files and every other HTML hunk.

## Recommended next lane

Lane 01 exact-hunk commit, then Lane 12 protected-preview smoke.

## Commit readiness

Safe to commit.

## Suggested next step

Commit the scoped copy change and verify the exact cache-busted protected-preview URL at desktop and narrow widths.
