# Lane 12 Chord / Voicing Finder Protected Smoke

## Task Summary

Requested Lane 12 protected-preview browser smoke for the latest E9 Fretboard Explorer Chord / Voicing Finder build.

Completed:

- Inspected repo guidance, integration status, and the Lane 18 product audit.
- Verified branch, HEAD, and local runtime `/api/version`.
- Ran authenticated protected-preview browser smoke at the exact cache-busted Explorer URL.
- Refreshed `integration-status.md` with the protected-smoke result and runtime-version caveat.

Intentionally not changed:

- No app runtime/UI/backend code was edited.
- No DNS, Cloudflare Access policy, secrets, auth policy, scraping, embeddings, Chroma/vector stores, corpus, or private transcript files were touched.
- No API fallback was used as browser smoke.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-voicing-finder-a08eba4`
- Cache-busted URL tested: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-voicing-finder-a08eba4`
- Exact URL the user should use: `https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-voicing-finder-a08eba4`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded; the in-app browser loaded the Explorer page, not the Access login page
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: current repo HEAD `3b9cdb9`, containing implementation commit `a08eba4`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"4040a47","git_branch":"feature/answer-api","server_started_at":"2026-06-26T01:51:23.747502+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: unauthenticated root redirects to Cloudflare Access; root app behavior was not used as the smoke target
- Whether app root `/` is expected to work: root is not the canonical cache-busted Explorer smoke target
- Whether `/ui/steel-guitar-rag-mock.html` works: not retested in this task
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes, as the app shell route
- Who should test this URL: both Codex and the user
- Do not test these URLs: do not treat local `127.0.0.1` or API fallback as protected-preview browser proof
- Known caveats: `/api/version` reports runtime SHA `4040a47`, which does not contain `a08eba4`; this pass verifies protected static/browser behavior at the cache-busted Explorer URL, not a clean runtime restart to the current UI commit

## Version And Runtime

- Branch: `feature/answer-api`
- Starting HEAD: `3b9cdb9`
- Final HEAD before docs commit: `3b9cdb9`
- Expected implementation commit: `a08eba4 feat: add explorer chord voicing finder`
- Current HEAD contains `a08eba4`: yes
- Local runtime `/api/version` SHA: `4040a47`
- Runtime SHA contains `a08eba4`: no
- Protected page script evidence: Explorer loaded `e9-fretboard-explorer.js?v=chord-voicing-finder-20260627`

## Browser Smoke Results

Overall result: **WARN / protected browser behavior passed with runtime-version caveat**.

### Page Load

- Exact protected URL loaded after Cloudflare Access authentication.
- Page title identified the E9 Fretboard Explorer.
- Explore Mode included `Chord / Voicing Finder`.
- No `[object Object]` text appeared.
- Browser console warning/error log was empty during the smoke.

### Fmaj7

- Query: `Fmaj7`
- Core grip result: `Target: Fmaj7 (major 7)`, `Fmaj7: 14 practical candidates`.
- Core candidates were clearly partial where applicable, including omitted-tone labels such as `OMITTED root (F)`.
- All practical grip result: `Fmaj7: 24 practical candidates`.
- All practical included complete high-confidence candidates such as fret 3 / strings `4-5-6-9` with `B+C`, with `OMITTED none`.
- Selecting a result produced one selected fretboard marker.

### Cmin9

- Query: `Cmin9`
- Parsed target: `Target: Cm9 (minor 9)`.
- Default/Core result: `0 candidates`.
- UI showed a clear no-practical-voicing message: try All practical, Include levers, or All frets.
- No fallback/internal error text appeared.

### V7 In G

- Query: `V7 in G`
- Parsed target: `Target: D7 (dominant 7)`.
- UI stated `V7 in G resolves to D7`.
- Result count: `6 candidates` under Core.
- Candidates showed D7 partials with omitted tones where applicable.
- Selecting a result produced one selected fretboard marker.

### Grip Vocabulary

- Grip vocabulary changed candidate breadth.
- Fmaj7 Core: 14 candidates.
- Fmaj7 All practical: 24 candidates.

## Files Changed

- Created `docs/handoffs/task-completions/2026-06-27-1140-12-chord-voicing-finder-protected-smoke.md`.
- Updated `docs/handoffs/task-completions/integration-status.md`.

No app code, runtime configuration, auth configuration, DNS configuration, corpus data, Chroma/vector stores, embeddings, scraper output, or private source data was changed.

## Tests And Checks

Commands run:

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
git log -5 --oneline
git merge-base --is-ancestor a08eba4 HEAD
curl -sS http://127.0.0.1:8770/api/version
git merge-base --is-ancestor a08eba4 4040a47
git diff --check
git diff --cached --name-only
curl -sSI 'https://app.steelguitarrag.com/?v=chord-voicing-finder-a08eba4'
```

Results:

- Current branch: `feature/answer-api`.
- Current HEAD before docs commit: `3b9cdb9`.
- Current HEAD contains `a08eba4`: yes.
- Local runtime `/api/version` returned SHA `4040a47`.
- Runtime SHA `4040a47` contains `a08eba4`: no.
- `git diff --check`: passed before docs edits.
- `git diff --cached --name-only`: no staged files at task start.
- Root URL unauthenticated check returned Cloudflare Access redirect.

Browser smoke:

- Protected-preview browser smoke at the exact URL passed the Chord / Voicing Finder behavior checks listed above.
- API fallback was not used.

## Integration Notes

- The protected static Explorer file appears current via cache-busted script loading, even though the Python runtime version endpoint is older.
- This is acceptable for focused static/UI smoke but should not be represented as a runtime restart to `a08eba4`.
- If the next lane requires `/api/version` to prove `a08eba4` or later, Lane 12 should restart the protected-preview process through the documented Mac mini LaunchDaemon path and rerun smoke.

## Risk Assessment

- Risk: medium.
- Reason: browser behavior passed, but `/api/version` is stale relative to the UI implementation commit. The feature under test is static Explorer UI, so the behavior is still meaningful; runtime provenance remains a caveat.
- Rollback notes: documentation-only changes can be reverted normally. No runtime changes were made.

## Human Decision Needed

No for focused user smoke at the exact direct Explorer URL.

Yes if the user requires a strict `/api/version` runtime proof containing `a08eba4`; that requires an explicit protected-preview restart/rerun.

## Safe-To-Stage Exact File List

- `docs/handoffs/task-completions/2026-06-27-1140-12-chord-voicing-finder-protected-smoke.md`
- `docs/handoffs/task-completions/integration-status.md`

## Files That Must Not Be Staged

- Any unrelated dirty or untracked files.
- Any corpus, Chroma/vector store, embedding, scraper output, private source, auth, DNS, secret, or raw asset files.

## Recommended Next Lane

- Lane 15 or user smoke can exercise the exact direct Explorer URL for Chord / Voicing Finder behavior.
- Lane 12 should only rerun with a protected-preview restart if strict `/api/version` proof is required.

## Commit Readiness

Safe to commit.

## Suggested Next Step

Use the exact URL for focused user smoke:

```text
https://app.steelguitarrag.com/ui/e9-fretboard-explorer.html?v=chord-voicing-finder-a08eba4
```

If strict runtime provenance is required, run Lane 12 protected-preview restart from current HEAD and repeat the same smoke.
