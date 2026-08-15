# Howdy music-first companion rebuild — implementation handoff

## Task summary

Replaced the text-first Howdy Practice Guide at the owner's existing local URL
with the previously developed deterministic music workspace. The repaired page
now leads with the taught solo and full-song play-along instead of editorial
prose.

The local Teachable-style presentation now provides:

- separate `Taught solo · 0:24` and `Full song · 3:57` practice views;
- six phrase loops, speed control, phrase looping, previous/next move controls,
  the eight-bar solo chord form, 54 synchronized E9 tab events, and a collapsed
  fretboard;
- the complete backing track with a horizontally scrolling 78-bar chord/NNS
  lane and the taught solo's reviewed chord events overlaid at their exact song
  time;
- Key D, 4/4, and 79.8 BPM in the first practice header;
- the corrected open-position A-pedal hammer token `0hA`, with a print legend
  stating that the bar remains at the open fret;
- three unmistakable related-video cards with private same-origin screenshots,
  play icons, exact timestamps, concise learner reasons, and new-tab Teachable
  lesson links;
- a single collapsed `Find a moment in this lesson` search in the taught-solo
  view only;
- the Teachable-style discussion area immediately after the companion;
- a three-page notation-plus-ten-string-tab PDF generated from the same 54
  canonical solo events.

The old `/practice-guide/howdy/` review address is now an explicit local-only
alias of the music-first embed. Release mode rejects that alias, preserving the
reviewed production route map.

No Cloudflare, Access, DNS, deployment, Teachable authorization, analytics,
general app, RAG, model, or authentication changes were made.

## Files changed

- `partner_companions/travis_howdy/content/related-lessons.json`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `partner_companions/travis_howdy/templates/embed.html`
- `partner_companions/travis_howdy/templates/full.html`
- `scripts/package_travis_companion.py`
- `scripts/verify_travis_companion.py`
- `tests/test_travis_companion.py`
- this handoff

Generated and intentionally uncommitted:

- `output/pdf/Howdy-music-first-review.pdf`
- `tmp/howdy-owner-review-2026-08-15.1/`
- `tmp/howdy-owner-review-2026-08-15.release-manifest.json`
- private screenshot assets beneath
  `/Users/cory/.steel-rag/travis-preview/howdy/concept-trail-thumbnails/`

## Tests and checks run

- `.venv/bin/pytest -q tests/test_travis_companion.py tests/test_travis_practice_guide.py tests/test_ttt_concept_graph.py` — 39 passed.
- focused companion test after final edits — 28 passed.
- `node --check partner_companions/travis_howdy/site/companion.js` — passed.
- Python compile checks for release, packaging, and verifier scripts — passed.
- `git diff --check` — passed.
- allowlisted bundle verifier — passed with 17 files, same-origin-only network
  policy, and all general app/RAG routes blocked.
- in-app browser smoke at
  `http://127.0.0.1:8897/practice-guide/howdy/` — passed for the 24-second taught
  solo, six phrase loops, Key D display, `0hA` tab token, related-video cards,
  collapsed lesson search, and discussion placement.
- full-song browser smoke — passed for the 3:57 duration, 78-bar scrolling
  chord/NNS lane, hidden solo tab/move panels, and audio playback advancing from
  `0:00` to `0:01`.
- PDF QA — three Letter pages; every page rasterized at 150 DPI and visually
  inspected; extracted text contains the title, revision, key/meter/tempo,
  chord form, all six phrases, `0hA` legend, control legend, attribution, and
  page numbers.

## Risks

- The solo route, chord form, copedent, and print layout remain explicitly
  owner-review content, not Travis-approved content.
- The full-song chart is still the audio-reader draft. Thirty-two events remain
  marked for an ear check; the UI identifies them with coral dots and does not
  present the chart as approved.
- The related lesson targets are source-backed exact transcript cue windows,
  but a cross-origin Teachable link cannot automatically seek the player yet.
- Private audio, tab evidence, related-video screenshots, and the rendered PDF
  stay outside Git. Rebuilding the complete local preview requires those
  private inputs.
- The browser runtime is deterministic and model-free, but musical approval is
  still a human decision.

## Human decision needed

- Review whether the restored music-first page now feels genuinely useful.
- Ear-check the 32 marked full-song chord events before partner review.
- Approve or correct the 54-event solo transcription, source copedent, chord
  form, and printable layout before any Travis-facing bundle.
- Decide whether the three related video choices are the best detours for this
  particular Howdy phrase.

No decision is needed to keep testing the local ungated preview.

## Safe-to-stage exact file list

```text
partner_companions/travis_howdy/content/related-lessons.json
partner_companions/travis_howdy/release.py
partner_companions/travis_howdy/site/companion.css
partner_companions/travis_howdy/site/companion.js
partner_companions/travis_howdy/templates/companion.fragment.html
partner_companions/travis_howdy/templates/embed.html
partner_companions/travis_howdy/templates/full.html
scripts/package_travis_companion.py
scripts/verify_travis_companion.py
tests/test_travis_companion.py
docs/handoffs/task-completions/2026-08-15-1737-06-15-howdy-music-first-rebuild.md
```

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing user change)
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- `tmp/`
- `/Users/cory/.steel-rag/`
- all private transcripts, comments, screenshots, audio, rights, approvals, and
  reviewed musical evidence

## Recommended next lane

Lane 15 for owner musical QA of the marked chord events and transcription, then
Lane 06 for any final density or interaction refinement. Remain local and
ungated until deployment is separately authorized.

## Commit readiness

Ready for one exact-path feature commit. The local HTTP review server is live on
port 8897; no external deployment is authorized or required.
