# Lane 12 - Legitimate Grip Vocabulary Protected Smoke

## Task Summary

Requested: complete protected-preview verification for `c30f287 feat: add legitimate E9 grip vocabulary`, refresh integration status, write a Lane 12 handoff, and exact-path commit scoped docs if clean.

Completed:

- Confirmed branch `feature/answer-api`.
- Confirmed current HEAD at task start was `c6a4a9c` and contains implementation commit `c30f287`.
- Checked local `/api/version`.
- Attempted the documented protected-preview LaunchDaemon restart because `/api/version` was stale.
- Ran authenticated protected-preview browser smoke at the required direct Explorer URL.
- Checked root behavior.
- Refreshed integration status with the smoke result and caveats.

Intentionally not changed:

- No app/runtime/UI/backend implementation files were modified by this lane.
- No DNS, Cloudflare Access policy, auth config, secrets, scraping, embeddings, Chroma/vector stores, corpus data, private transcripts, or deployment config were changed.
- No API fallback was used or reported as browser smoke.

Result: **WARN**.

Protected static/browser behavior showed the legitimate grip vocabulary slice, but strict clean-runtime certification is blocked because `/api/version` remains stale and dirty runtime-affecting files are present in the worktree.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=legitimate-grip-vocabulary-c30f287`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=legitimate-grip-vocabulary-c30f287`
- Exact URL the user should use: not cleared for strict user smoke until interactive restart/re-smoke; direct URL above showed expected protected static behavior
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `c6a4a9c`, containing implementation commit `c30f287`
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `{"git_sha":"a6abc61","git_branch":"feature/answer-api","server_started_at":"2026-06-27T17:30:30.410070+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, but it redirects to the app shell and drops the query string
- Whether app root `/` is expected to work: yes for app shell; direct `/ui/...?...` remains required for exact Explorer cache-busted smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes by root redirect
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Lane 12 after interactive restart for strict readiness; the user only if accepting the static-browser caveat
- Do not test these URLs: root URL for cache-busted Explorer verification, because root drops the query string
- Known caveats: stale `/api/version`; non-interactive restart blocked by `sudo`; dirty runtime-affecting Explorer/test files are present

## Runtime And Restart Evidence

- Starting HEAD: `c6a4a9c`
- Final HEAD before docs commit: `c6a4a9c`
- Expected implementation commit: `c30f287`
- `git merge-base --is-ancestor c30f287 HEAD`: passed
- Current HEAD contains `c30f287`: yes
- Local `/api/version`: stale runtime SHA `a6abc61`
- Restart attempt:
  - `deploy/macos/install-private-preview-launchdaemon.sh status`: exited 1
  - `deploy/macos/install-private-preview-launchdaemon.sh restart`: exited 1
  - Failure reason: `sudo: a terminal is required to read the password; either use the -S option to read from standard input or configure an askpass helper`
- Runtime after restart attempt: still `a6abc61`

## Browser Smoke Results

Exact protected Explorer URL loaded after Cloudflare Access authentication.

Verified:

- Page title identified the E9 Fretboard Explorer.
- No Cloudflare Access login page remained after authentication.
- No `[object Object]` appeared.
- No relevant console errors were captured.
- Vocabulary controls included Core, Extended, Song/tab vocabulary, E-lower pockets, Two-string, and All legitimate.

Voicing Identifier cases:

| Case | Result |
| --- | --- |
| `4-6-10` at fret 3 with A+B | `C chord (IV function in G)`, notes `G, C, E`, Extended grip explanation present |
| `3-5-9` at fret 3 open | `Bdim chord (iii function in G)`, notes `B, D, F`, Song/tab vocabulary explanation/watch-out present |
| `5-6-7` at fret 3 with B | `D7 color / partial V7 in G`, notes `D, C, A`, Path grip, omitted `3` |
| `6-7-10` at fret 3 with A+B | `Am chord (ii function in G)`, notes `C, A, E`, Path grip |
| `3-5-8` at fret 3 with B+C | `C chord (IV function in G)`, notes `C, E, G`, Song/tab vocabulary explanation present |
| `5-7-8` at fret 8 with E-lower | `G chord (I function in G)`, notes `G, D, B`, E-lower pocket explanation/watch-out present |

Chord / Voicing Finder cases:

| Case | Result |
| --- | --- |
| `Fmaj7`, Core, common controls | Target `Fmaj7 (Major 7)`, 8 candidates, omitted-tone labeling present, no dominant/V7 mislabel |
| `Fmaj7`, All legitimate, common controls | Target `Fmaj7 (Major 7)`, 24 candidates, non-core candidates surfaced, complete `4-5-6-9` candidates present |
| Candidate selection | Selecting another result updated the selected card and selected SVG marker |
| `F7`, All legitimate, common controls | Target `F7 (Dominant 7)`, dominant candidates surfaced without major-7 mislabel |
| `G major`, E-lower pockets, include levers | Single `5-7-8` fret 8 E-lower G candidate surfaced with `OMITTED none` |
| Default path view | Harmonized scale path remained readable with no object-string rendering |

Root behavior:

- Tested `https://app.steelguitarrag.com/?v=legitimate-grip-vocabulary-c30f287`.
- Final URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- Query string was dropped.
- App shell loaded and no root console errors were captured.

## Files Changed

- Created `docs/handoffs/task-completions/2026-06-28-0944-12-legitimate-grip-vocabulary-protected-smoke.md`.
- Updated `docs/handoffs/task-completions/integration-status.md`.

No implementation files were modified by this lane.

## Tests And Checks

Commands run:

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log -8 --oneline`
- `git merge-base --is-ancestor c30f287 HEAD`
- `curl -sS http://127.0.0.1:8770/api/version || true`
- `deploy/macos/install-private-preview-launchdaemon.sh status`
- `deploy/macos/install-private-preview-launchdaemon.sh restart`
- protected-preview browser smoke at the exact cache-busted Explorer URL
- protected-preview root behavior browser check
- `git diff --check`

Results:

- HEAD contains `c30f287`.
- `git diff --check` passed before documentation edits.
- Protected browser smoke completed after Cloudflare Access authentication.
- Non-interactive LaunchDaemon restart did not complete because `sudo` required a terminal password.

Skipped:

- Focused JS/Python tests were not run because no implementation fix was made in this lane.
- API fallback was not used.

## Dirty Worktree / Staging Notes

Dirty runtime-affecting files were present and intentionally left unstaged:

- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`

Other broad unrelated dirty/untracked work remains parked, including corpus/provenance/RAG/brand/design/documentation files. Do not broad-stage.

## Integration Notes

The direct protected Explorer URL demonstrates the legitimate grip vocabulary in the authenticated browser, but this is not a strict clean-runtime proof:

- `/api/version` reports `a6abc61`, not `c6a4a9c`.
- The protected static server is serving a worktree with dirty Explorer JS/test changes.
- Root drops query strings, so direct `/ui/e9-fretboard-explorer.html?...` URLs are required for cache-busted Explorer smoke.

## Risk Assessment

Risk: **medium**.

Why:

- Browser-visible behavior for the requested Explorer slice passed.
- Runtime SHA is stale.
- Dirty runtime-affecting files mean the protected static smoke is not cleanly attributable only to committed HEAD.

Rollback notes:

- No code changes were made by this lane.
- If a docs-only commit is created, revert that commit to remove only the handoff/status update.

## Human Decision Needed

Yes.

Decision: run the interactive Mac mini LaunchDaemon restart from a terminal session with sudo available, then rerun Lane 12 protected-preview smoke so `/api/version` reports current HEAD or a later commit containing `c30f287` and the dirty runtime files are either committed or cleared.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-28-0944-12-legitimate-grip-vocabulary-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- corpus/source/provenance files
- Chroma/vector stores
- embeddings
- scraping outputs
- private transcripts/private source files
- secrets/env files
- brand/design/generated assets
- unrelated dirty or untracked files

## Recommended Next Lane

Lane 12 Self-Hosted Deployment.

## Commit Readiness

Safe to commit docs-only warning handoff/status update.

## Suggested Next Step

Lane 12 prompt:

```text
Rerun protected-preview smoke for legitimate grip vocabulary after interactive LaunchDaemon restart. Verify /api/version reports current HEAD or later containing c30f287, confirm dirty runtime files are either committed or cleared, then retest https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=legitimate-grip-vocabulary-c30f287 and mark user-smoke readiness only if strict runtime/static certification passes.
```
