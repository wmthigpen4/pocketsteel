# Howdy feedback: recommendation grounding and opening sequence correction

## Task summary

Applied the owner's second-round Howdy feedback to the local, ungated
music-first companion.

- Corrected the canonical opening sequence from an A-pedal hammer to the
  observed open-to-fret-1 bar hammer. Event 2 now changes both sustained
  strings 5 and 6 from fret 0 to fret 1 without repicking and renders as
  `0h1` in the browser and PDF.
- Kept Travis's exact “this starts in a cool way” excerpt as timestamped
  supporting evidence. It no longer replaces the actionable instruction or
  the next-move text.
- Replaced the universal three-card related-video row with one or two
  phrase-selected cards. Every match now declares its selected phrase, exact
  Howdy event IDs, canonical concept, relationship, source-backed Travis
  lesson moment, and a learner-facing “Why this lesson” explanation.
- Profile-bound the recommendations to `howdy-54-event-route-v1`. A companion
  with a different or missing profile receives no Howdy recommendations.
  Packaging also rejects unknown phrases, cross-phrase event citations,
  missing phrase coverage, or more than two cards for one phrase.
- Added a real screenshot and exact 0:38 cue from *Hammer-Ons And Pull-Offs*
  for the corrected opening phrase.
- Differentiated the two presentations. The compact lesson companion keeps
  one selected phrase's tab and a collapsed fretboard beneath the lesson. The
  “Open larger practice view” route shows all six tab systems at once and
  opens the complete fretboard.
- Regenerated the three-page printable tab from the corrected 54-event private
  artifact and visually inspected all pages.

No Cloudflare, Access, DNS, deployment, Teachable authorization, analytics,
general app, RAG, model, or authentication changes were made. The review
remains local and ungated.

## Files changed

- `partner_companions/travis_howdy/README.md`
- `partner_companions/travis_howdy/content/related-lessons.json`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `tests/test_travis_companion.py`
- this handoff

Generated and intentionally uncommitted:

- `/Users/cory/.steel-rag/travis-preview/howdy/howdy.transcribed-review.6.json`
- `/Users/cory/.steel-rag/travis-preview/howdy/concept-trail-thumbnails/hammer-ons.jpg`
- `output/pdf/Howdy-music-first-review.pdf`
- `tmp/howdy-owner-review-2026-08-15.2/`
- `tmp/howdy-owner-review-2026-08-15.2.release-manifest.json`

## Tests and checks run

- `.venv/bin/ruff check partner_companions/travis_howdy/release.py tests/test_travis_companion.py` — passed.
- `node --check partner_companions/travis_howdy/site/companion.js` — passed.
- `.venv/bin/pytest -q tests/test_travis_companion.py tests/test_travis_practice_guide.py tests/test_ttt_concept_graph.py` — 40 passed.
- `git diff --check` — passed.
- deterministic bundle packaging and `scripts/verify_travis_companion.py` — passed with 18 allowlisted files, same-origin-only network policy, and all blocked routes preserved.
- local route smoke — four intended routes returned 200; RAG/general-app/traversal routes returned 404.
- in-app browser smoke at `http://127.0.0.1:8897/practice-guide/howdy/` — passed for the corrected current/next sequence, strings 5 and 6 `0h1` tab, open-to-fret-1 position label, exact supporting Travis quote, selected-phrase recommendation change, Teachable comments placement, and the explicit larger-practice-view explanation.
- in-app browser smoke at `http://127.0.0.1:8897/howdy/` — passed for all six separate tab systems and the initially expanded full fretboard.
- PDF QA — three Letter pages; every page rasterized at 150 DPI and visually inspected. Extracted text contains revision `.6`, `0h1`, and the correct bar-hammer legend, with no stale “bar stays at open fret” legend.

## Risks

- The 54-event route, chords, copedent, and print layout remain owner-review
  content, not Travis-approved content.
- The opening bar-hammer correction is grounded in the owner's direct musical
  correction and visual review of the private slow-demo video. Other solo
  events have not received equivalent owner signoff.
- The full-song chord chart remains the audio-reader draft with 32 marked
  ear-check events.
- Related lesson timestamps are exact transcript cue targets, but Teachable
  cross-origin links still cannot automatically seek the player.
- Private audio, screenshots, transcript evidence, corrected companion JSON,
  and the rendered PDF remain outside Git.

## Human decision needed

- Review the opening move at normal and slowed playback and confirm both
  strings 5 and 6 should be shown sustaining under the bar hammer.
- Review whether the phrase-specific “Why this lesson” explanations earn their
  space; they are now deterministic and source-bound, not general catalog
  recommendations.
- Continue owner QA on the remaining solo events and 32 marked full-song chord
  events before any Travis-facing release.

No decision is needed to continue using the local ungated preview.

## Safe-to-stage exact file list

```text
partner_companions/travis_howdy/README.md
partner_companions/travis_howdy/content/related-lessons.json
partner_companions/travis_howdy/release.py
partner_companions/travis_howdy/site/companion.css
partner_companions/travis_howdy/site/companion.js
partner_companions/travis_howdy/templates/companion.fragment.html
tests/test_travis_companion.py
docs/handoffs/task-completions/2026-08-15-1802-06-15-howdy-feedback-recommendations-sequencing.md
```

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing user change)
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- `tmp/`
- `/Users/cory/.steel-rag/`
- all private transcripts, comments, screenshots, audio, rights, approvals, and reviewed musical evidence

## Recommended next lane

Lane 15 for owner musical QA of the remaining route and full-song chords, then
Lane 06 for any density or interaction refinement. Remain local and ungated
until deployment is separately authorized.

## Commit readiness

Ready for one exact-path feature commit. The local HTTP review server is live
on port 8897; no external deployment is authorized or required.
