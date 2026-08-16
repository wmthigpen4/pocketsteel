# Howdy continuous phrase playback

## Task summary

Removed the clunky forced phrase-loop feature from both Howdy presentations.
Choosing a phrase still cues its exact start, but playback now continues through
the rest of the taught solo. As playback crosses a phrase boundary, the selected
phrase, tab system, current move, fretboard state, and related-lesson card advance
with the music.

The loop button, loop state, phrase-end restart logic, loop styling, and loop
copy were removed. The phrase map now describes six practice sections rather
than six loops.

No private musical events, printable tab, Cloudflare, auth, DNS, deployment,
Teachable configuration, RAG, or model behavior changed.

## Files changed

- `partner_companions/travis_howdy/README.md`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `tests/test_travis_companion.py`
- this handoff

Generated and intentionally uncommitted:

- `tmp/howdy-owner-review-2026-08-15.3/`
- `tmp/howdy-owner-review-2026-08-15.3.release-manifest.json`

## Tests and checks run

- `node --check partner_companions/travis_howdy/site/companion.js` — passed.
- `.venv/bin/ruff check partner_companions/travis_howdy/release.py tests/test_travis_companion.py` — passed.
- `.venv/bin/pytest -q tests/test_travis_companion.py tests/test_travis_practice_guide.py tests/test_ttt_concept_graph.py` — 41 passed.
- `git diff --check` — passed.
- deterministic bundle packaging and allowlist verification — passed with 18 files and same-origin-only networking.
- in-app browser smoke — no loop control is present; playback at 100% advanced from phrase 1 into phrase 2 at 0:03 without restarting, and the phrase, tab, move, fretboard, and related video updated together.

## Risks

- Playback now stops and returns to the start only at the end of the complete
  taught-solo scope. Repetition is intentionally manual: select the phrase
  again or use the transport.
- Existing musical and full-song chord review risks are unchanged.

## Human decision needed

Confirm that phrase selection plus continuous playback feels better than
automatic looping. No decision is needed to keep using the local preview.

## Safe-to-stage exact file list

```text
partner_companions/travis_howdy/README.md
partner_companions/travis_howdy/site/companion.css
partner_companions/travis_howdy/site/companion.js
partner_companions/travis_howdy/templates/companion.fragment.html
tests/test_travis_companion.py
docs/handoffs/task-completions/2026-08-15-1928-06-15-howdy-continuous-phrase-playback.md
```

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md` (pre-existing user change)
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- `tmp/`
- `/Users/cory/.steel-rag/`

## Recommended next lane

Lane 15 for owner feel and musical QA. Remain local and ungated until any
deployment is separately authorized.

## Commit readiness

Ready for one exact-path bug-fix commit.
