# Lane 06 — Local chord-reader song listening test

## Task summary

Added a deliberately local-only, experimental chord-reader view for three user-supplied songs. The existing frozen v8 proof remains the default page. Opening the same proof page with `?v=9` or `?local=1` loads an ignored local bundle, copies no source paths into JSON, and presents an audio player plus clickable chord segments and model confidence.

This is a listening test, not an accuracy evaluation. No reference charts were supplied, the R5 readiness result remains NO-GO, no operating threshold was selected, and no deployment/player authorization is implied.

## Lane classification

- Primary lane: 06 UX/UI Design
- Supporting lane: 20 ML experiment presentation
- Task mode: explicitly authorized local experimental run

## Files changed

- `.gitignore`
- `scripts/build_local_chord_reader_test.py`
- `ui/chord-reader-proof/index.html`
- `ui/chord-reader-proof/proof.css`
- `ui/chord-reader-proof/proof.js`
- `tests/test_chord_reader_proof.py`
- This handoff

## Local-only generated files

- `ui/chord-reader-proof/local-tests/proof.json`
- `ui/chord-reader-proof/local-tests/audio/*.mp3`

The entire `ui/chord-reader-proof/local-tests/` tree is ignored by Git and must not be staged. Its current proof JSON SHA-256 is `ebd20baf4bb570a7701e4e76e49b98cea083715079de61011cfeab391fa1e1c4`.

## Model run results

| Song | Duration | Segments | Mean model confidence | Audio at >=80% confidence | Audio below 50% confidence | Route |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| String By | 3:15 | 67 | 83.2% | 71.9% | 1.7% | expanded-mixture |
| Cowboy Take Me Away (No Steel) | 4:50 | 185 | 77.7% | 61.0% | 7.2% | expanded-mixture |
| TOGETHERAGAINBACKINGTRACK-191201-185354 | 3:45 | 130 | 74.5% | 26.7% | 0.6% | conservative-sparse |

These values describe model behavior only. Confidence is the model's own probability and must not be reported as chord accuracy.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_chord_reader_proof.py` — PASS, 6 tests
- `node --check ui/chord-reader-proof/proof.js` — PASS
- Ruff check and format check on the new Python generator and proof tests — PASS
- Exact copied-audio SHA-256 comparison against all three source files — PASS
- Local bundle schema, model/audio receipts, and three-track result inventory — PASS
- `git diff --check` — PASS

## Smoke Target

- Target type: local
- Result type: browser smoke and local audio listening test
- Exact browser URL tested: `http://127.0.0.1:8898/ui/chord-reader-proof/?v=9&local=1&refresh=20260821-final`
- Exact URL the user should use: `http://127.0.0.1:8898/ui/chord-reader-proof/?v=9`
- Auth required: no
- Auth provider: none
- Local backend URL: `http://127.0.0.1:8898/`
- Expected backend port: 8898
- Expected git HEAD during smoke: working tree based on `63e847ac86f83666b4599618cfbcbe1565b7f91e`
- Version endpoint: not applicable to the static local server
- If version endpoint missing, how version is inferred: cache-busted CSS/JavaScript assets plus inspected DOM title, track inventory, audio URLs, and rendered result counts
- Whether app root `/` works: static server root is available; the tested surface is the proof path
- Who should test this URL: user and Codex
- Do not test these URLs: production/player URLs; this experiment is localhost-only
- Known caveats: generated audio/prediction files are intentionally ignored and must be regenerated on another checkout

## Browser result

PASS in the Codex in-app browser. The page rendered the experimental/NO-GO disclosure, all three track selectors, exact segment counts 67/185/130, and behavior summaries 83.2%/77.7%/74.5%. Each copied MP3 reached media `readyState=4`; the Together Again duration was observed as 224.59517 seconds. Clicking a prediction sought the audio control. The frozen benchmark was hidden only in local mode. A second smoke without `?v=9` confirmed the original v8 proof and its default content remain intact.

## Risk assessment

Low for the product because the feature is explicit, local, ignored-data-only, and does not alter the deployed/default chord reader. Scientific risk is contained by prominent wording that confidence is not accuracy and readiness remains NO-GO.

## Human decision needed

Yes, for any accuracy claim. A user-confirmed chord chart or timed manual corrections are needed before these three runs can be scored. Promotion, threshold selection, and production/player wiring remain separate prohibited decisions.

## Safe-to-stage exact file list

- `.gitignore`
- `scripts/build_local_chord_reader_test.py`
- `ui/chord-reader-proof/index.html`
- `ui/chord-reader-proof/proof.css`
- `ui/chord-reader-proof/proof.js`
- `tests/test_chord_reader_proof.py`
- `docs/handoffs/task-completions/2026-08-21-1431-06-local-chord-reader-song-test.md`

## Files that must not be staged

- `ui/chord-reader-proof/local-tests/`
- The three source MP3 files in Google Drive
- Any R4/R5 experiment output or protected label/reference source

## Recommended next lane

Lane 01 exact-path commit. If the user provides or confirms timed chords, a new bounded Lane 20 scoring pass can compare these predictions with that reference without retraining.

## Commit readiness

Safe to commit the seven exact files above. Keep the ignored local bundle on this machine so the localhost listening page continues to work.
