# Travis Tutorial Companion Workflow

## Task Summary

Implemented the approved Travis Toy Tutorial Companion workflow as a local, production-shaped feature slice. It includes the private authoring API and editor, outbound leased Mac runner, generic `lesson_companion_v3` contract, immutable publishing and rollback, enrollment-gated learner embed, Howdy v1 conversion fixture, Cloudflare D1/R2/Workflow configuration, migrations, and tests.

No production deployment, DNS, Cloudflare Access policy, OAuth registration, secret creation, or external resource mutation was performed. The existing Howdy static release remains available as the fallback.

## Files Changed

- `partner_companions/travis_tutorials/__init__.py`
- `partner_companions/travis_tutorials/schema.py`
- `partner_companions/travis_tutorials/README.md`
- `scripts/analyze_travis_backing_track.js`
- `scripts/convert_howdy_companion_v3.py`
- `steel_guitar_rag/travis_companion_analysis/__init__.py`
- `steel_guitar_rag/travis_companion_analysis/analysis.py`
- `steel_guitar_rag/travis_companion_analysis/runner.py`
- `steel_guitar_rag/travis_companion_analysis/README.md`
- `workers/travis-companion/.dev.vars.example`
- `workers/travis-companion/README.md`
- `workers/travis-companion/wrangler.jsonc`
- `workers/travis-companion/tsconfig.json`
- `workers/travis-companion/vitest.config.ts`
- `workers/travis-companion/worker-configuration.d.ts`
- `workers/travis-companion/migrations/0001_initial.sql`
- `workers/travis-companion/migrations/0002_job_progress.sql`
- `workers/travis-companion/src/env.d.ts`
- `workers/travis-companion/src/domain.ts`
- `workers/travis-companion/src/index.ts`
- `workers/travis-companion/src/ui.ts`
- `workers/travis-companion/tests/domain.test.ts`
- `tests/test_travis_tutorials_companion.py`
- `package.json`
- `package-lock.json`
- `pyproject.toml`
- This handoff.

Deleted files: none.

Generated/private runtime artifacts remain ignored under `.wrangler/` and `output/` and are not part of the commit.

## Implementation Notes

- Authoring supports direct resumable multipart R2 upload, one required primary MP3, track labels and learner/download policy, waveform passage selection, leased analysis, progress, synchronized chord/tab editing, optimistic autosave, append-only edit audit, validation, immutable publish, revision listing, and pointer-only rollback.
- The runner fingerprints FFmpeg-decoded media, aligns passage audio, optionally subtracts the backing, invokes pinned Basic Pitch, normalizes pitch-bend events, translates the approved v3 copedent into the existing Amazing Tablature arranger, and records hashes, versions, confidence, alternatives, and classified failures.
- The runner treats an HTTP 204/empty claim response as an idle queue and continues polling; this was verified while preparing the local acceptance fixture.
- The analysis extra pins `setuptools<81` because Basic Pitch 0.4.0's resampling dependency still imports `pkg_resources`; direct Core ML inference was verified locally against the generated primary MP3.
- Publication permits contiguous uncertain chord spans and mechanically valid generated/unconfirmed tab while still blocking missing media/alignment, invalid timing, empty passages, pitch-range errors, and impossible mechanics.
- Learner access uses exact-origin Teachable OAuth messaging, `courses:read` enrollment verification, one-time embed codes, short-lived lesson/revision-scoped HMAC tokens, private R2 artifacts, authorized ranged playback, and independent download policy.
- Cloudflare Access JWTs are verified with RS256/JWKS for author APIs. The local bypass is accepted only in the development environment.
- The learner iframe uses a stable `/embed/<lesson-slug>` URL. Draft edits do not change the current learner revision.

## Tests and Checks Run

- Full Python suite: `1720 passed`.
- Focused companion tests: `8 passed`.
- Existing Worker tests: `4 passed`.
- Travis Worker tests: `6 passed`.
- TypeScript no-emit check: passed.
- Focused Ruff check: passed.
- JavaScript syntax check: passed.
- Dependency lock check: passed.
- `npm audit --audit-level=high`: `0 vulnerabilities`.
- Wrangler production bundle dry run: passed (`105.35 KiB`, gzip `25.57 KiB`).
- D1 migrations `0001` and `0002` applied successfully in local emulation.
- Wheel build passed and contains the v3 contract and private runner packages.
- Howdy v1-to-v3 golden conversion passed with 4 chord spans, 12 tab events, and the complete 24-second primary track.
- Node backing-track analyzer passed against a synthesized MP3.
- Real Amazing Tablature arrangement passed for a v3-copedent G#4 fixture.
- `git diff --check`: passed.

## Smoke Target

- Target: local Wrangler/D1/R2/Workflow emulation; browser smoke completed by Codex.
- Author URL: `http://127.0.0.1:8791/admin?local=1`
- Learner URL: `http://127.0.0.1:8791/embed/local-integration?v=20260817`
- Production URL: not available; the Travis-owned hostname remains an external configuration decision.
- Auth result: development-only author bypass passed. Cloudflare Access was not attempted locally. Learner authorization, revision scoping, token invalidation, and media authorization were exercised through the local test-token flow; live Teachable OAuth was not attempted without credentials.
- Expected pre-commit HEAD: `f3e4caa0ef0553880858fa91cd2ba612b3acaafe`
- `/api/version`: this standalone Worker does not expose that endpoint; code identity was inferred from the local working tree and Wrangler bundle.
- Root `/`: redirects to `/admin` as expected.
- `/ui/steel-guitar-rag-mock.html`: not part of this standalone Worker and not expected to resolve.
- API fallback: author project/media APIs passed locally; this is separate from the completed browser smoke.
- Browser results: project list/editor loaded; track and passage controls rendered; chord split/merge and autosave worked; multi-note tab controls rendered; uncertain chord and generated/unconfirmed tab markers rendered; responsive tablet layout had no horizontal page overflow; learner primary audio returned `206 Partial Content`; disabled download returned `403`; rollback resolved the earlier immutable revision.
- Local acceptance media and a click-by-click test guide were generated under ignored `output/travis-companion-demo/`; they are for local user smoke and are not committed product artifacts.
- Do not test the `example.invalid` resource and origin placeholders as real endpoints.

## Risks

Risk: medium until staging configuration and owner review.

- Live Teachable OAuth and Cloudflare Access behavior require staging credentials and policies and have not been exercised.
- The approved Travis copedent snapshot must be supplied; the documented fallback is intentionally flagged for confirmation before publication.
- The Mac runner requires platform-compatible FFmpeg and pinned Basic Pitch installation. The runner protocol and real arranger were tested, but an end-to-end Basic Pitch analysis of Travis source media was not available.
- Exact Travis hostname, school/course/lesson IDs, resource IDs, and secrets remain unset.
- PDF output was structurally tested and locally generated; Travis should approve its musical presentation in staging.

Rollback: revert the feature commit. No production resources or published learner pointers were changed.

## Human Decision Needed

Before staging or production, supply and approve:

- Travis-owned public hostname and exact allowed Teachable school origins.
- Teachable school/course/lesson IDs and OAuth application credentials.
- Cloudflare Access team domain/audience and author policy.
- D1, R2, Workflow, DNS, and Worker resource provisioning.
- Approved account-level Travis E9 copedent JSON.
- A private Teachable test lesson and owner acceptance of the converted Howdy fixture.

## Safe-to-Stage Exact File List

Safe to stage exactly the files listed in **Files Changed**, including this handoff. Directory-wide staging is safe only for the three new directories:

- `partner_companions/travis_tutorials/`
- `steel_guitar_rag/travis_companion_analysis/`
- `workers/travis-companion/`

Do not use `git add .`.

## Files That Must Not Be Staged

Preserve these unrelated dirty files and generated paths:

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `output/`
- `.wrangler/`
- Any corpus, source-inbox, vector, embedding, credential, environment-secret, deployment, DNS, or raw design asset.

## Recommended Next Lane

Recommended next lane: `12 Self-Hosted Deployment`, but only after explicit approval of the exact staging resource changes and receipt of the configuration decisions above. Provision isolated staging resources, register the Teachable OAuth callback, configure Access, deploy the Worker and runner credentials, convert Howdy, and execute enrolled/unenrolled owner smoke before enabling production.

## Commit Readiness

Safe to commit by exact path. All local tests, bundle checks, migrations, protocol smoke, and browser smoke passed. Protected-preview deployment is intentionally blocked on external configuration and explicit approval; no live change is included in this commit.
