# Transcript-backed ungated Howdy companion

## Task summary

Replaced the layout-only local Howdy proof with a deterministic,
transcript-backed E9 transcription for owner review at
`http://127.0.0.1:8899/howdy/`. The same local runtime serves the compact
embed demo and printable view. No Access gate, login, remote deployment,
Cloudflare project, DNS record, partner identity, or general application
surface was added or changed.

The private companion contains 54 authored events across six phrase ranges and
an eight-bar, 4/4 track grid at approximately 79.8 BPM. Six selected
current-move headlines use concise verbatim Travis excerpts with lesson
timestamps; other cells explicitly say that no excerpt is attached. Literal
strings, frets, pedals, slides, repicks, and releases remain separate from the
quote. Chord symbols are withheld because the lesson states the key but does
not supply a chord chart.

## Files changed

- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/README.md`
- `scripts/package_travis_companion.py`
- `tests/test_travis_companion.py`
- this handoff

Ignored/private outputs were refreshed outside Git:

- the transcript-backed companion JSON and hash-pinned owner-review audio
  excerpt under `~/.steel-rag/travis-preview/howdy/`;
- the local Pages bundle under `tmp/travis-preview-draft/`;
- `output/pdf/Howdy-transcript-backed-review.pdf`.

No raw transcript, full lesson video, signed media URL, private token, or
licensed source media is staged or named as a repository input.

## Tests and checks

- Private companion validation: passed; 54 events, six phrases, 24,064 ms.
- `.venv/bin/python -m pytest tests/test_travis_companion.py -q`: 18 passed.
- `scripts/verify_travis_companion.py`: passed; 12 allowlisted files,
  same-origin-only networking, all blocked routes verified.
- Live local route checks: `/howdy/`, `/howdy/embed-demo/`, and `/howdy/print/`
  returned 200; RAG/app routes and traversal probes returned 404.
- Browser interaction smoke: audio loaded, playback advanced the event state,
  and selected source moments showed a timestamped verbatim excerpt.
- Browser presentation smoke: full, compact embed, and print routes all loaded
  the same six phrase ranges; the print route exposed the same packaged PDF.
- PDF QA: three letter-size pages rasterized at 150 DPI and inspected; all six
  phrase systems, ten tab strings, controls, revision, page numbers, and draft
  warning were present without clipping.
- `git diff --check`: required before commit.

## Risks

- The route is transcribed and camera/audio checked, but Travis has not
  approved the music, copedent labels, audio rights, chords, or print layout.
- The final closing cells use the lesson camera and pitch evidence where the
  transcript names the motion but not every string. They are intentionally
  still marked review-required.
- The local audio excerpt is for owner review only and remains outside Git.
- The local URL is reachable only from this machine while the existing Pages
  development process remains running.

## Human decision needed

Review the transcription, especially the fifth-string turnaround and closing
descent. Do not send the URL or artifacts to Travis until brand, music, print,
and audio-rights approval is explicitly recorded.

## Safe-to-stage exact file list

- `partner_companions/travis_howdy/README.md`
- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/site/companion.css`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `scripts/package_travis_companion.py`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-14-1048-12-local-ungated-howdy-preview.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- the three pre-existing unrelated untracked handoffs
- `tmp/`, `.wrangler/`, `output/`, private source/video/audio/transcript data,
  the private companion JSON, identities, credentials, and all unrelated dirty
  files

## Recommended next lane

Lane 06 should collect owner UX/transcription feedback. Lane 15 should perform
independent musical and print QA after any corrections. Lane 12 remains out of
scope until an explicitly authorized isolated preview deployment.

## Commit readiness

Safe to commit after the final diff and status checks pass.
