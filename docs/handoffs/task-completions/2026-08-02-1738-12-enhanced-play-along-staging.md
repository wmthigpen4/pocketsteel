# Enhanced Play-Along Staging Deployment

## Task Summary

- Implemented the enhanced Play-Along release in the canonical Steel Guitar
  RAG repository on `feature/enhanced-play-along-staging`.
- Added local MP3, M4A/AAC, and WAV import, worker-based analysis, OPFS audio
  storage, IndexedDB project/session storage, duplicate detection, relinking,
  Review, four practice modes, bar-aligned looping, speed presets, count-in,
  metronome, and Song Map navigation.
- Added a Chords/NNS display switch that updates Now, Next, and every Song Map
  chord without changing the reviewed project data.
- Preserved the existing Steel Guitar RAG visual system and integrated the
  feature into the existing home page, `/songs`, `/setup/:id`, and `/play/:id`
  journeys.
- Published the exact committed release to the self-hosted staging service at
  `test.steelguitarrag.com`. Production at `app.steelguitarrag.com` was not
  changed.
- Replaced the temporary standalone test Worker with the shared Mac Mini
  Cloudflare Tunnel route and deleted the obsolete `steel-guitar-rag-test`
  Worker after verifying the new staging route.

## Source And Release Identity

- Branch: `feature/enhanced-play-along-staging`
- Feature commit: `fbbc823ecf984f1fbd3b4d762b55bc0b2e61f02c`
- Remote branch: `origin/feature/enhanced-play-along-staging`
- Detached release directory:
  `/Users/cory/.steel-rag/releases/fbbc823e-play-along-staging`
- Staging origin: `127.0.0.1:8771`
- Staging LaunchAgent: `com.steelguitarrag.staging`

## Staging Infrastructure

- Added a Cloudflare Access self-hosted application named
  `Steel Guitar RAG Staging` for `test.steelguitarrag.com`.
- Reused the existing `Allow me only` Access policy.
- Created a staging-only environment file with the staging application's AUD;
  the production environment file was not modified.
- Updated tunnel `steel-rag-mac-mini` so:
  - `app.steelguitarrag.com` continues to use `127.0.0.1:8770`.
  - `test.steelguitarrag.com` uses `127.0.0.1:8771`.
- Added a proxied `test` Tunnel DNS record for the existing tunnel.
- Detached `test.steelguitarrag.com` from `steel-guitar-rag-test`, verified the
  Worker had no other routes or domains, and deleted it. It can be recreated
  only by redeploying its former Worker source/configuration.

## Tests And Checks

- Full Python suite: `1559 passed`.
- Focused Play-Along tests: `48 passed`.
- `npm run check:js` — passed, including the new analysis and practice tools.
- Scoped Ruff checks — passed.
- Python wheel and sdist build — passed.
- Browser E2E on the exact feature code — passed for WAV import, local
  analysis, Review, player navigation, duplicate prevention, NNS, inclusive
  Song Map looping, speed/count-in persistence, no autoplay, and no console
  errors.
- Live staging Access check — unauthenticated traffic redirects to Cloudflare
  Access.
- Live authenticated `/songs` check — curated catalog loads and `Add a Song`
  appears with the local-only privacy copy.
- Live authenticated player check — Amazing Grace loads, transport becomes
  ready, Now/Next switches to NNS, and Song Map renders NNS values including
  altered chords and `N.C.`.
- Local staging `/api/version` reports `git_sha: fbbc823`.
- Staging LaunchAgent is running from the detached release with the
  staging-only environment file.
- Cloudflare API returns 404 for the deleted obsolete Worker.

## Known Repository Baseline

- Repo-wide Ruff and mypy still report unrelated pre-existing debt. The scoped
  new/changed code checks pass.
- The worktree contains an intentionally untracked `.venv` symlink used to run
  the canonical environment. It must not be staged.
- The original canonical checkout remains dirty from unrelated user work and
  was not modified or cleaned by this task.

## Risk Assessment

Medium. The feature is isolated to staging and stores imported recordings only
on the user's device, but browser audio decoding support varies by codec and
device. The staging hostname now depends on the Mac Mini service and tunnel
being online. Production remains on its existing origin and release.

## Human Decision Needed

No deployment decision is pending. The staging site is ready for product
feedback. Promotion to production should happen only after that feedback is
addressed and the staging branch is reviewed and merged through the normal
repository flow.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-08-02-1738-12-enhanced-play-along-staging.md`

## Files That Must Not Be Staged

- `.venv`
- All unrelated dirty or untracked files in the canonical checkout.
- Local release directories, LaunchAgents, environment files, logs, Wrangler
  credentials, and any other operator or secret-bearing path.

## Recommended Next Lane

Product feedback on `https://test.steelguitarrag.com`, followed by a scoped
feature revision on `feature/enhanced-play-along-staging`. After approval, use
the repository's review/merge flow and promote an exact reviewed commit to the
production release directory and origin.

## Commit Readiness

Safe to commit the handoff file by exact path.
