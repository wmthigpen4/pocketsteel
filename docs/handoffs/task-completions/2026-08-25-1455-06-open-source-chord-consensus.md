# Open-source BTC chord consensus

## Task summary

The user supplied the public Swaram chord finder and `ohollo/chord-extractor` repositories and asked that the existing chord reader be materially enhanced from the research. This bounded local-only slice:

- traced Swaram's public frontend to its public Hugging Face backend and verified that it uses BTC (Bi-directional Transformer for Chord Recognition), harmonic CQT features, a 170-class vocabulary, median filtering, and model-probability Viterbi smoothing;
- verified that `chord-extractor` is a Python/multiprocessing wrapper around the Chordino NNLS-chroma Vamp plugin rather than a separate learned model;
- adapted the compatible Swaram idea to the repository's already pinned, checksum-verified MIT-licensed BTC checkpoint without changing the existing BTC baseline default;
- added one optional, fixed product-level BTC decoder that collapses the 170-class distribution to root + major/minor products, applies a five-frame modal filter, and runs one key-agnostic Viterbi pass with self-transition `0.9`;
- ran that decoder exactly once over the same three private local songs, with zero fitting, zero parameter search, and no retry;
- added a three-system consensus layer over our engine, Chordify, and local BTC output;
- updated the localhost proof to show live BTC/our-engine/Chordify chords, three-way metrics, a prioritized review queue, and public methodology links.

The Chordino/NNLS-chroma path was not copied or installed. Its GPL-2.0/native-plugin constraints make it an isolated future baseline rather than code to merge into the current app.

## Results

| Song | Our vs BTC | All three agree | Our engine supported by at least one checker | Priority review time |
| --- | ---: | ---: | ---: | ---: |
| String By | 92.21% | 90.02% | 98.19% | 3.46 s |
| Cowboy Take Me Away (No Steel) | 87.66% | 83.36% | 90.95% | 25.90 s |
| Together Again backing track | 80.91% | 68.73% | 80.87% | 41.41 s |

“Priority review” is only all-three-disagree time plus time where Chordify and BTC agree against our engine. It is intended to reduce review labor, not to claim that a machine majority is correct.

Across direct our-engine/Chordify disagreement time, BTC backs our side / Chordify's side / neither as follows:

- String By: 58.27% / 40.77% / 0.96%;
- Cowboy: 32.31% / 53.25% / 14.44%;
- Together Again: 38.60% / 53.24% / 8.16%.

The important recurring Together Again `our D / Chordify G` pattern is more favorable to the existing engine than the prior two-system comparison suggested. Across the same 12.49797 disputed seconds, BTC reports D with our engine for 9.53704 seconds (76.3%) and G with Chordify for 2.96093 seconds (23.7%). This is a third machine opinion, not ground truth, but it means the Chordify G label should not be used as an automatic correction.

Ignored proof JSON SHA-256 after consensus attachment: `f9e6dad9cdfb352a43691d0c19b72c02f8414fa294879be9133dd6251a2640e4`.

## Files changed

- `steel_guitar_rag/chord_reader/btc.py`
- `scripts/add_open_source_consensus.py`
- `ui/chord-reader-proof/index.html`
- `ui/chord-reader-proof/proof.css`
- `ui/chord-reader-proof/proof.js`
- `tests/test_add_open_source_consensus.py`
- `tests/test_chord_reader_proof.py`
- this handoff

Generated but ignored/private:

- `ui/chord-reader-proof/local-tests/proof.json`
- the existing ignored local audio copies beneath `ui/chord-reader-proof/local-tests/audio/`

No audio, Chordify MIDI, downloaded model snapshot, credential, session data, or external-service response is tracked.

## Tests and checks

- `.venv/bin/python -m pytest -q tests/test_add_open_source_consensus.py tests/test_add_chordify_crosscheck.py tests/test_chord_reader_proof.py` — **11 passed**.
- `node --check ui/chord-reader-proof/proof.js` — **passed**.
- `.venv/bin/ruff check steel_guitar_rag/chord_reader/btc.py scripts/add_open_source_consensus.py tests/test_add_open_source_consensus.py tests/test_chord_reader_proof.py` — **passed**.
- `.venv/bin/ruff format --check steel_guitar_rag/chord_reader/btc.py scripts/add_open_source_consensus.py tests/test_add_open_source_consensus.py tests/test_chord_reader_proof.py` — **passed**.
- `git diff --check` — **passed**.
- One fixed invocation of `scripts/add_open_source_consensus.py --local-files-only` under the existing chord-reader v4 environment — **passed** for all three songs; no second inference invocation occurred.
- One `--reuse-existing` invocation recomputed summary fields from the retained BTC predictions after UI/report refinement; this did not load or run the model.

## Browser smoke

Smoke Target:
- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8898/ui/chord-reader-proof/?v=9&open-source=1`
- Cache-busted URL tested: `http://127.0.0.1:8898/ui/chord-reader-proof/?v=9&open-source=1`
- Exact URL the user should use: `http://127.0.0.1:8898/ui/chord-reader-proof/?v=9&open-source=1`
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8898`
- Expected backend port: `8898`
- Expected git HEAD: scoped implementation commit produced from this handoff
- Version endpoint: none
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: HTML/JS asset cache key `v=11`, tracked code, BTC revision, and ignored proof SHA above
- Whether app root `/` works: not tested; the proof path is canonical
- Whether app root `/` is expected to work: yes, as a static file server root
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested; unrelated to this local proof
- Who should test this URL: both
- Do not test these URLs: production or protected-preview URLs; private audio-derived data is intentionally localhost-only
- Known caveats: machine consensus is not ground truth; automated browser media seeking could not be proven because the browser-control surface exposes media time as read-only

Browser assertions passed:

- the hero names our ensemble, Chordify, and open-source BTC;
- all three track selectors render;
- live Open-source BTC / Experimental ensemble / Chordify cards render;
- String By renders 94.1% our-vs-Chordify, 58.3% BTC-backs-our-side, 90.0% three-way agreement, and 3 seconds priority review;
- Together Again renders 68.8%, 38.6%, 68.7%, and 41 seconds respectively;
- Together Again explicitly reports the recurring D/G 76.3% BTC vote for our D side;
- 18 prioritized review rows render with all three chords and consensus category;
- all five public methodology links render;
- all three local MP3s reach media `readyState=4`;
- no browser console errors were recorded.

Row/segment seek-and-play remains a user-smoke check. The UI event code is unchanged in structure and syntax-valid, but the automated browser's read-only media wrapper did not expose the resulting seek state reliably.

## Integration notes

The normal `BTCRecognizer.predict()` behavior is unchanged. Probability-aware product decoding is opt-in with `product_viterbi=True`, and the decoder receipt reports fixed parameters plus zero fit/search counts. The main domain-gated engine, production player, model weights, promotion gates, operating thresholds, and R5 readiness status are unchanged.

Public research sources:

- <https://ecoliving-tips.github.io/chord-finder.html>
- <https://huggingface.co/spaces/vineethwilson/swaram-chord-service>
- <https://github.com/jayg996/BTC-ISMIR19>
- <https://github.com/ohollo/chord-extractor>
- <https://code.soundsoftware.ac.uk/projects/nnls-chroma>

## Risk assessment

**Medium.** The implementation is local-only, optional, deterministic, and does not promote a model. The scientific risk is that a reviewer might mistake three-system consensus for accuracy. The UI and payload repeatedly disclose that machine agreement is only review triage. Chordino remains unintegrated because its GPL/native runtime needs a deliberate isolation and licensing decision.

Rollback is the eight tracked paths listed above; ignored BTC output can remain local. No deletion is required.

## Human decision needed

**No** for the scoped implementation and commit. Human listening is still required before converting any consensus row into a correction or accuracy label.

## Safe-to-stage exact file list

- `steel_guitar_rag/chord_reader/btc.py`
- `scripts/add_open_source_consensus.py`
- `ui/chord-reader-proof/index.html`
- `ui/chord-reader-proof/proof.css`
- `ui/chord-reader-proof/proof.js`
- `tests/test_add_open_source_consensus.py`
- `tests/test_chord_reader_proof.py`
- `docs/handoffs/task-completions/2026-08-25-1455-06-open-source-chord-consensus.md`

## Files that must not be staged

- `ui/chord-reader-proof/local-tests/`
- `~/Documents/Pocket Steel/tmp/chordify-upload/`
- the cached BTC snapshot under the user's Hugging Face cache
- all source audio, Chordify MIDI, browser/session data, credentials, and unrelated files

## Recommended next lane

Lane 01 exact-path commit, followed by local user smoke of the Together Again priority rows and highlighted D/G split. A Chordino/NNLS-chroma run should be a separate bounded, isolated licensing/runtime task rather than silently added as a dependency.

## Commit readiness

Safe to commit

## Suggested next step

Open the exact localhost URL, select Together Again, and listen first to the all-disagree and our-engine-outlier rows. Treat the repeated D/G rows as “machine majority currently favors D,” not as confirmed labels.
