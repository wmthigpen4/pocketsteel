# Lane 12 - Legitimate Grip Vocabulary Protected Smoke Rerun

## Task Summary

Requested: complete protected-preview verification for the legitimate 3-string E9 grip vocabulary slice, including browser smoke, scoped regression fix if needed, integration-status refresh, handoff, and exact-path commit.

Completed:

- Confirmed branch `feature/answer-api`.
- Confirmed current HEAD at task start was `0247804` and contains implementation commit `c30f287`.
- Checked local `/api/version`.
- Inspected the prior Lane 05 handoff and the prior Lane 12 warning handoff.
- Inspected the documented LaunchDaemon restart path.
- Validated the scoped Explorer/test worktree diff as an in-scope smoke fix.
- Ran focused JS syntax checks and focused pytest suites.
- Ran authenticated protected-preview browser smoke at the required direct Explorer URL.
- Checked root behavior.
- Refreshed integration status.

Intentionally not changed:

- No DNS, Cloudflare Access policy, auth config, secrets, scraping, embeddings, Chroma/vector stores, corpus data, private transcripts, source records, or deployment config were changed.
- No API fallback was used or reported as browser smoke.

Result: **PASS/WARN**.

Protected static/browser behavior passed and the scoped Explorer smoke fix passed focused tests. Runtime-version proof remains a warning because `/api/version` still reports stale SHA `a6abc61`.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=legitimate-grip-vocabulary-c30f287`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=legitimate-grip-vocabulary-c30f287`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=legitimate-grip-vocabulary-c30f287`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `0247804` at task start, containing `c30f287`; final commit will include scoped smoke fix/docs
- Version endpoint: `http://127.0.0.1:8770/api/version`
- Version endpoint result: `{"git_sha":"a6abc61","git_branch":"feature/answer-api","server_started_at":"2026-06-27T17:30:30.410070+00:00","python_module":"pocketsteel.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, but it redirects to `/ui/steel-guitar-rag-mock.html` and drops the query string
- Whether app root `/` is expected to work: yes for app shell; direct Explorer URL is required for exact cache-busted Explorer smoke
- Whether `/ui/steel-guitar-rag-mock.html` works: yes by root redirect
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: the user may run focused static Explorer smoke at the direct URL; Lane 12 should rerun after interactive LaunchDaemon restart for strict runtime certification
- Do not test these URLs: root URL for cache-busted Explorer validation, because root drops the query string
- Known caveats: stale `/api/version`; non-interactive restart still requires terminal sudo

## Runtime And Repo Evidence

- Branch: `feature/answer-api`
- Starting HEAD: `0247804`
- Expected implementation commit: `c30f287`
- `git merge-base --is-ancestor c30f287 HEAD`: passed
- Local `/api/version`: stale runtime SHA `a6abc61`
- Documented restart path inspected: `deploy/macos/install-private-preview-launchdaemon.sh restart`
- Restart was not reattempted after the prior failure because the documented path requires interactive sudo from this environment.

## Scoped Smoke Fix

The worktree contained a small Explorer/test diff directly related to this smoke:

- `ui/e9-fretboard-explorer.js`
  - Adds E-lower pocket control-state inclusion for Chord / Voicing Finder when a lever-inclusive scope is selected.
  - Includes E-lower pocket groups in Core Chord / Voicing Finder search so the learner can surface the practical `5-7-8` E-lower pocket without switching away from Core.
  - Keeps string action labels in `all` mode instead of switching to selected-only.
- `tests/test_frontend_answer_ui.py`
  - Adds regression coverage for Chord / Voicing Finder surfacing `5-7-8` with E-lower.
  - Tightens the string action label mode assertion to `all`.

No broader product, backend, corpus, auth, DNS, or deployment behavior was changed.

## Browser Smoke Results

Protected Explorer URL loaded after Cloudflare Access authentication.

Page-level checks:

- Page identified as E9 Fretboard Explorer.
- No Cloudflare Access login page remained after authentication.
- No `[object Object]`.
- No relevant browser console errors.
- Vocabulary controls included Core, Extended, Song/tab vocabulary, E-lower pockets, Two-string, and All legitimate.

Voicing Identifier cases:

| Case | Result |
| --- | --- |
| `4-6-10` at fret 3 with A+B | `C chord (IV function in G)`, notes `G, C, E`, wide-grip explanation present |
| `3-5-9` at fret 3 open | `Bdim chord (iii function in G)`, notes `B, D, F`, 9th-string context/watch-out present |
| `5-6-7` at fret 3 with B | `D7 color / partial V7 in G`, notes `D, C, A`, path-grip explanation present |
| `6-7-10` at fret 3 with A+B | `Am chord (ii function in G)`, notes `C, A, E`, lower path-grip explanation present |
| `3-5-8` at fret 3 with B+C | `C chord (IV function in G)`, notes `C, E, G`, spread-grip explanation present |
| `5-7-8` at fret 8 with E-lower | `G chord (I function in G)`, notes `G, D, B`, E-lower pocket explanation/watch-out present |

Chord / Voicing Finder cases:

| Case | Result |
| --- | --- |
| `Fmaj7`, Core, common controls | Target `Fmaj7 (Major 7)`, 8 candidates, omitted-tone labeling present, no dominant/V7 mislabel |
| `Fmaj7`, All legitimate, common controls | Target `Fmaj7 (Major 7)`, 24 candidates, non-core candidates surfaced, complete `4-5-6-9` candidates present |
| Candidate selection | Selecting another result updated the selected card/detail and SVG marker state |
| `F7`, All legitimate, common controls | Target `F7 (Dominant 7)`, dominant candidates surfaced without major-7 mislabel |
| `G major`, E-lower pockets, include levers | Single `5-7-8` fret 8 E-lower G candidate surfaced with E-lower pocket explanation and omitted-none detail |
| `D7`, All legitimate, common controls | Structured Root/Quality controls resolved to `D7 (Dominant 7)` candidates |

Default Harmonized Scale Path:

- Path mode showed the low path rail with 8 readable cards.
- No `[object Object]`.
- No visible candidate spam from no-effect controls.

Root behavior:

- Tested `https://app.steelguitarrag.com/?v=legitimate-grip-vocabulary-c30f287`.
- Final URL: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- Query string was dropped.
- App shell loaded.
- No root console errors captured.

## Files Changed

- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-28-0956-12-legitimate-grip-vocabulary-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Tests And Checks

Commands run:

- `git status --short`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git log -6 --oneline`
- `git merge-base --is-ancestor c30f287 HEAD`
- `curl -sS http://127.0.0.1:8770/api/version || true`
- `git diff --check`
- `git diff --cached --name-only`
- `node --check ui/e9-fretboard-explorer.js`
- `node --check ui/e9-music-rules.js`
- `node --check ui/e9-fretboard-explorer-data.js`
- `node --check ui/answer-client.js`
- `node --check ui/pedal-steel-fretboard.js`
- `.venv/bin/python -m pytest tests/test_explorer_musical_red_team.py -q` - `4 passed`
- `.venv/bin/python -m pytest tests/test_fretboard_explorer.py -q` - `42 passed`
- `.venv/bin/python -m pytest tests/test_frontend_answer_ui.py -q` - `24 passed`
- `.venv/bin/python -m pytest tests/test_pedal_steel_fretboard_ui.py -q` - `36 passed`
- `.venv/bin/python -m pytest tests/test_api_contract.py -q` - `5 passed`
- protected-preview browser smoke at the exact cache-busted Explorer URL
- protected-preview root behavior browser check

Skipped:

- Full pytest was not run; focused checks cover the scoped Explorer/UI/API-contract smoke fix.
- API fallback was not used.

## API Fallback Status

Not used. Protected-preview result is authenticated browser smoke.

## Integration Notes

- The direct protected Explorer URL is the correct user-smoke URL for this slice.
- Root redirects to the app shell and drops query strings, so root must not be used for exact Explorer cache-busted verification.
- `/api/version` is stale at `a6abc61`; that affects strict runtime certification but not the observed protected static Explorer behavior.

## Risk Assessment

Risk: **medium**.

Why:

- The scoped UI/test fix is small and focused, and all focused checks passed.
- Browser-visible Explorer behavior passed.
- Runtime SHA remains stale, so strict LaunchDaemon-runtime certification still needs a terminal-based restart and rerun.

Rollback notes:

- Revert the final scoped commit from this run to remove the UI/test smoke fix and docs/status update.

## Human Decision Needed

Yes.

Decision: whether to require strict `/api/version` certification before user smoke. If yes, run the interactive Mac mini LaunchDaemon restart with sudo available and rerun this Lane 12 smoke.

## Safe-To-Stage Exact File List

- `ui/e9-fretboard-explorer.js`
- `tests/test_frontend_answer_ui.py`
- `docs/handoffs/task-completions/2026-06-28-0956-12-legitimate-grip-vocabulary-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- corpus/source/provenance files
- Chroma/vector stores
- embeddings
- scraping outputs
- private transcripts/private source files
- secrets/env files
- brand/design/generated assets
- unrelated dirty or untracked files

## Recommended Next Lane

Lane 12 Self-Hosted Deployment if strict runtime proof is required; otherwise user smoke at the exact Explorer URL.

## Commit Readiness

Safe to commit scoped smoke fix and docs.

## Suggested Next Step

For strict runtime certification:

```text
Lane 12: Restart the Mac mini LaunchDaemon interactively, verify /api/version reports the current HEAD containing the legitimate grip vocabulary smoke fix, then rerun protected-preview smoke at https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=legitimate-grip-vocabulary-c30f287.
```
