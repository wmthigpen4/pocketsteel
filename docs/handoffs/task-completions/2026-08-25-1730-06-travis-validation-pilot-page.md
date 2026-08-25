# Chord Reader — Travis Validation pilot page

## Task summary

The user correctly reported that the earlier statement “pilot assembled” only
described the collected audio and did not provide an actual validation page.
This autopilot correction builds and verifies the missing clickable localhost
page.

The page loads the 15 selected private tracks, displays the frozen domain-gated
v8 engine's predictions as editable chord boxes, synchronizes them with audio,
and records human review decisions. A reviewer can mark a prediction correct,
enter a replacement chord, flag timing, mark uncertainty, add a segment note,
add whole-song feedback, confirm all remaining boxes in a track, filter the
review grid, switch songs, and download a structured JSON feedback file.

Untouched boxes remain explicitly `unreviewed`; they never count as human
confirmed. Feedback auto-saves in browser local storage. The automated browser
smoke used an isolated `session=automated-smoke` storage namespace, and the
user-facing URL opens the clean default namespace.

## Scope and execution cap

- selected private tracks: 15;
- selected audio duration: 46.1 minutes;
- v8 inference passes over the selected set: exactly one;
- generated prediction segments: 2,104;
- fitting, tuning, parameter search, or retry: zero;
- BTC or NNLS inference: zero;
- model weights changed: no;
- deployment, DNS, Tunnel, Access, or auth changed: no.

The page displays the v8 engine's own segment confidence. It does not claim
that the retained BTC/NNLS Consensus Confidence v1 research selector is active
in this runtime. The public-development result is disclosed separately as
99.6% precision at 39.8% selective coverage and 79.9% full-coverage accuracy.

## Files changed

- `.gitignore`
- `scripts/build_local_chord_reader_test.py`
- `ui/chord-reader-travis-validation/index.html`
- `ui/chord-reader-travis-validation/validation.css`
- `ui/chord-reader-travis-validation/validation.js`
- `tests/test_travis_validation_ui.py`
- this handoff

Generated but ignored/private:

- `ui/chord-reader-travis-validation/local-data/proof.json`
- `ui/chord-reader-travis-validation/local-data/audio/` with 15 MP3 files
- `~/Documents/Pocket Steel/tmp/chord-reader-validation/`

The builder now derives browser audio URLs from any repository-contained output
directory and removes leading numeric inventory prefixes from display titles.
The default existing local-proof output remains supported.

## Tests and checks

- focused pytest:
  `pytest -q tests/test_travis_validation_ui.py tests/test_chord_reader_proof.py`
  — 9 passed;
- `node --check ui/chord-reader-travis-validation/validation.js` — passed;
- Ruff check for the builder and new test — passed;
- Ruff format check for the builder and new test — passed;
- `git diff --check` — passed;
- generated-bundle validation — 15 tracks, 15 MP3s, and 2,104 segments;
- localhost HTTP checks — page, prediction JSON, and MP3 returned 200;
- browser smoke — passed with no console errors.

## Browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8898/ui/chord-reader-travis-validation/?v=2&session=automated-smoke`
- Cache-busted URL tested: `http://127.0.0.1:8898/ui/chord-reader-travis-validation/?v=2&session=automated-smoke`
- Exact URL the user should use: `http://127.0.0.1:8898/ui/chord-reader-travis-validation/?v=2`
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8898`
- Expected backend port: `8898`
- Expected git HEAD: scoped implementation commit produced from this handoff
- Version endpoint: none
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: page and asset cache key `v=2` plus tracked implementation
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: yes, as the static server root
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested; unrelated
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes; unrelated
- Who should test this URL: Codex and the user
- Do not test these URLs: production or public URLs; private audio is localhost-only
- Known caveats: localhost cannot be sent to a remote reviewer; browser feedback remains on the current browser until downloaded

Browser assertions:

- exact page title and heading render;
- all 15 named track selectors render;
- the first track renders 139 chord boxes and the full bundle renders 2,104;
- a `Correct` decision changes the first card to `Human-confirmed` and advances progress;
- a `Wrong chord` decision exposes the replacement field and records `G7` in the isolated smoke session;
- whole-song notes save in the isolated smoke session;
- switching to `Nothing's News` updates the selected heading;
- its MP3 reaches `readyState=4` with the expected duration and URL;
- console error count is zero;
- the clean user-facing URL was opened and marked as the deliverable tab.

## Integration notes

This is a localhost/private-review feature. The tracked page contains no audio,
predictions, feedback, credentials, course-session data, or lesson download
URLs. Generated audio and prediction output is ignored by Git.

The exported feedback contract is
`chord_reader_travis_feedback_v1`. It contains the frozen model hashes, source
audio hashes, original prediction and confidence, review status, corrected
chord, segment note, and whole-song note. That export can later feed a bounded
error analysis; it is not automatically ingested or used for training.

## Risk assessment

Medium. The page is functional and private, but the model produced 2,104
change-level segments rather than hand-authored musical bars. Some short or
spurious changes may be tiring to review and should be flagged as timing issues
rather than silently merged. The displayed confidence is v8 model confidence,
not the undeployed Consensus Confidence v1 selector and not measured accuracy.

The current link works only on this computer while the localhost server is
running. Sending the page to a remote reviewer requires a separate protected
hosting and audio-rights decision. Public deployment is inappropriate for the
course MP3s.

Rollback is the six tracked implementation/test paths plus this handoff. The
ignored private output can remain locally without affecting the repository.

## Human decision needed

No for local user smoke. Yes before remote use: choose an authenticated private
hosting path and confirm that these course downloads may be made available to
the named reviewer through that protected page. Deployment/auth is RED and was
not attempted.

## Safe-to-stage exact file list

- `.gitignore`
- `scripts/build_local_chord_reader_test.py`
- `ui/chord-reader-travis-validation/index.html`
- `ui/chord-reader-travis-validation/validation.css`
- `ui/chord-reader-travis-validation/validation.js`
- `tests/test_travis_validation_ui.py`
- `docs/handoffs/task-completions/2026-08-25-1730-06-travis-validation-pilot-page.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `ui/chord-reader-travis-validation/local-data/`
- `~/Documents/Pocket Steel/tmp/`
- all audio, generated predictions, feedback exports, browser/session data,
  credentials, course materials, and unrelated files

## Recommended next lane

Lane 06 local user smoke at the exact URL. After the interaction is accepted,
Lane 18/11 can design a private remote-review contract; Lane 12 deployment must
wait for explicit approval of the exact protected hosting plan.

## Commit readiness

Safe to commit

## Suggested next step

Open `http://127.0.0.1:8898/ui/chord-reader-travis-validation/?v=2`, review a few
boxes on two songs, reload the page to confirm persistence, and download a test
feedback file. Do not deploy the private audio publicly.
