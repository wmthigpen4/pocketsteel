# Chordify localhost cross-check

## Task summary

The user asked to compare three private songs against Chordify, inspect the public technical record behind Chordify, and update the localhost chord-reader proof so a human reviewer can start with machine-identified disagreements.

Completed:

- used the user's authenticated Chordify Premium session to upload the three user-supplied recordings and download the provider's time-aligned MIDI exports;
- added a dependency-free Standard MIDI parser and deterministic product-level comparator;
- normalized enharmonic spellings and collapsed extensions/slash chords to root + major/minor for comparison;
- attached exact agreement, root agreement, compared duration, tempo, and the 12 longest disagreement windows to the ignored local proof bundle;
- updated the local proof UI with live our-engine/Chordify chord display, agreement cards, seekable review windows, and a public-methodology summary with primary-source links;
- kept all scores explicitly described as cross-system agreement rather than ground-truth accuracy.

Intentionally not changed:

- no production/browser inference model, operating threshold, readiness decision, or deployment was changed;
- no Chordify data was committed;
- no claim was made that Chordify is correct when the two systems disagree;
- no Multitracks purchase was made and no paid content was extracted from Multitracks, Hooktheory, Ultimate Guitar, Songsterr, or Sheet Music Direct.

## Results

| Song | Product agreement | Root agreement | Compared audio |
| --- | ---: | ---: | ---: |
| String By | 94.1040% | 94.7015% | 193.963 s |
| Cowboy Take Me Away (No Steel) | 86.6369% | 86.6369% | 286.278 s |
| Together Again backing track | 68.8383% | 71.3956% | 216.447 s |

The most actionable pattern is in Together Again: eight recurring intervals have our engine reporting `D` while Chordify reports `G`, at roughly 20.6, 45.9, 71.2, 96.4, 121.7, 147.0, 172.2, and 197.5 seconds. This is a review queue, not a resolved correction.

The ignored local bundle is byte-deterministic on a second comparator run: SHA-256 `87123f79c4ed88b1f10753a2f38b88f36bcbb629254368d1fa5d09486f7677b5`.

## Technical due diligence

Public Chordify material describes separate chord and beat neural networks. Earlier published systems used Sonic Annotator and HarmTrace; a later engineering report described Kiss FFT features, a TensorFlow convolutional network, and HMM sequence selection. Chordify publishes research/auxiliary repositories and datasets, including HarmTrace-related code, but this audit found no public current production weights or directly reusable current production inference package.

Sources surfaced in the local UI:

- 2012 ISMIR system paper: <https://dreixel.net/research/pdf/cctfm.pdf>
- 2017 Haskell engineering report: <https://www.haskell.org/communities/05-2017/html/report.html>
- Chordify algorithm overview: <https://chordify.net/pages/technology-algorithm-explained/>
- Chordify public GitHub organization: <https://github.com/chordify>

## Files changed

- `scripts/add_chordify_crosscheck.py` — new MIDI parser, chord classifier, comparison, and local-bundle updater.
- `ui/chord-reader-proof/index.html` — optional local cross-check section.
- `ui/chord-reader-proof/proof.js` — local rendering, live Chordify chord, review-window seeking, methodology links.
- `ui/chord-reader-proof/proof.css` — local cross-check layout and review-row states.
- `tests/test_add_chordify_crosscheck.py` — synthetic MIDI/parser/normalization/comparison tests.
- `tests/test_chord_reader_proof.py` — local UI and no-new-dependency contract checks.
- `docs/handoffs/task-completions/2026-08-23-1517-06-chordify-local-crosscheck.md` — this handoff.

Generated but ignored/private:

- `ui/chord-reader-proof/local-tests/proof.json` and its existing local audio directory;
- `~/Documents/Pocket Steel/tmp/chordify-upload/` audio bridge copies and MIDI exports;
- the corresponding Chordify downloads in the user's Downloads directory.

No files were deleted.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_add_chordify_crosscheck.py tests/test_chord_reader_proof.py` — **8 passed**.
- `npm run check:js` — **passed** for the repository JavaScript syntax suite.
- `.venv/bin/ruff check scripts/add_chordify_crosscheck.py tests/test_add_chordify_crosscheck.py tests/test_chord_reader_proof.py` — **passed**.
- `.venv/bin/ruff format --check scripts/add_chordify_crosscheck.py tests/test_add_chordify_crosscheck.py tests/test_chord_reader_proof.py` — **passed**.
- `git diff --check` — **passed**.
- Comparator rerun produced the same ignored proof SHA-256 — **passed**.

One attempted test command named nonexistent `tests/test_chord_reader_local_song_test.py`; pytest exited before running tests. It was immediately replaced by the correct focused command above. No test was skipped.

## Browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8898/ui/chord-reader-proof/?v=9`
- Cache-busted URL tested: `http://127.0.0.1:8898/ui/chord-reader-proof/?v=9&check=2`
- Exact URL the user should use: `http://127.0.0.1:8898/ui/chord-reader-proof/?v=9`
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8898`
- Expected backend port: `8898`
- Expected git HEAD: current scoped implementation commit after Lane 01
- Version endpoint: none
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: tracked UI bytes plus the ignored proof bundle SHA above
- Whether app root `/` works: not tested
- Whether app root `/` is expected to work: yes, as a static repository file server listing; it is not the canonical target
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: unrelated to this local proof
- Who should test this URL: both
- Do not test these URLs: protected preview or production; this private local bundle is intentionally ignored and local-only
- Known caveats: agreement is between two automated systems and is not a measured accuracy score

Browser assertions passed:

- local proof loaded without the error state;
- String By rendered 94.1% product and 94.7% root agreement;
- song switching to Together Again rendered 68.8% product and 71.4% root agreement;
- the Together Again review table exposed eight recurring D-vs-G rows;
- methodology source links were present.

## Integration notes

The tracked UI contract is additive: existing frozen v8 proof JSON remains unchanged, while local `chord_reader_local_song_test_v1` bundles may optionally contain `crossCheck` per track plus a bundle-level `crossCheckMethodology`. The comparator uses only Python's standard library. It supports ordinary Standard MIDI files with PPQ timing and rejects SMPTE timing.

The next useful product action is human review of the seekable mismatch windows, especially the recurring Together Again D/G pattern. Confirmed corrections can become a small private adjudication set in a separately approved model cycle; Chordify agreement alone must not become a training label.

## Risk assessment

**Medium.** The implementation is local-only and additive, but machine-to-machine agreement can create false confidence if described as truth. The UI and handoff repeatedly disclose this limitation. Rollback is the exact seven tracked paths listed below; ignored private outputs can remain local or be removed later only with explicit approval.

## Human decision needed

**No** for the scoped implementation and local smoke. The next human task is evidentiary rather than a code approval: listen to the prioritized disagreement windows and mark our engine, Chordify, or neither as correct.

## Safe-to-stage exact file list

- `scripts/add_chordify_crosscheck.py`
- `ui/chord-reader-proof/index.html`
- `ui/chord-reader-proof/proof.js`
- `ui/chord-reader-proof/proof.css`
- `tests/test_add_chordify_crosscheck.py`
- `tests/test_chord_reader_proof.py`
- `docs/handoffs/task-completions/2026-08-23-1517-06-chordify-local-crosscheck.md`

## Files that must not be staged

- `ui/chord-reader-proof/local-tests/`
- `~/Documents/Pocket Steel/tmp/chordify-upload/`
- any source audio, downloaded MIDI, browser profile/session data, or Chordify content
- unrelated worktree files, if any appear

## Recommended next lane

Lane 01 Repo Steward for the exact-path implementation commit, followed by local user smoke. No protected-preview update is appropriate because the comparison bundle contains ignored private audio-derived data and is intentionally localhost-only.

## Commit readiness

Safe to commit

## Suggested next step

Lane 01: stage exactly the seven safe paths above, review the cached diff, commit the local Chordify cross-check, and leave the private ignored bundle untouched.
