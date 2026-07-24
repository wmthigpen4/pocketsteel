# Minimal Browser Verification 05e8748

## Task Summary

Requested Lane 12 minimal authenticated browser verification for runtime HEAD `05e8748`.

Completed:

- Confirmed current local HEAD is `05e8748`.
- Confirmed the protected preview root URL redirects to `/ui/steel-guitar-rag-mock.html`.
- Confirmed the authenticated browser app shell loads.
- Confirmed Q&A input is unlocked after the app session finishes initializing.
- Confirmed protected `/api/version` reports `05e8748`.
- Ran only the six requested browser prompts.
- Confirmed off-domain source cards did not appear.
- Confirmed fretboard rendering for chord prompts where expected.

Intentionally not changed:

- No implementation files were modified.
- No deployment, auth, DNS, Cloudflare Access, corpus, Chroma, embeddings, source-inbox, scraping, or source-data changes were made.
- No broad QA, scorer calibration, or API fallback QA was run.
- No files were staged or committed.

## Smoke Target

- Target type: protected-preview root
- Result type: browser smoke
- Exact browser URL tested: `https://app.steelguitarrag.com/?v=resolver-fix-05e8748`
- Cache-busted URL tested: `https://app.steelguitarrag.com/?v=resolver-fix-05e8748`
- Exact URL the user should use: not requested for manual smoke; verification target remains `https://app.steelguitarrag.com/?v=resolver-fix-05e8748`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded via existing authenticated browser session
- Local backend URL: `http://127.0.0.1:8770`
- Expected backend port: `8770`
- Expected git HEAD: `05e8748`
- Version endpoint: `/api/version`
- Version endpoint result: `{"git_sha":"05e8748","git_branch":"feature/answer-api","server_started_at":"2026-06-14T22:04:02.220851+00:00","python_module":"steel_guitar_rag.api","retrieval_mode":"hybrid_private_first","auth_provider":"cloudflare_access"}`
- If version endpoint missing, how version is inferred: not applicable
- Whether app root `/` works: yes, root redirects to `/ui/steel-guitar-rag-mock.html`
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex for this task
- Do not test these URLs: direct Ollama, Chroma, or unauthenticated live answer endpoints
- Known caveats: root redirect drops the query string; the app briefly shows a locked prompt while `/api/session` initializes, then unlocks in the authenticated browser session

## Current HEAD

```text
05e8748
```

Latest commits observed:

```text
05e8748 backend: replace quarantine fallback with teacher routes
24fd8e9 backend: fix repair fallback and chord classifier drift
1f91ed2 backend: block sgf primary answer leakage
14021f8 qa: add golden adversarial smoke bank
b449912 qa: harden scorer against sgf answer leakage
```

## Browser Auth And Unlock Result

- Cloudflare Access result: authenticated browser session reached the app shell.
- Final browser URL after root redirect: `https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html`.
- Q&A unlock result: passed. The question textarea became enabled with placeholder `Ask a steel guitar question...`.
- Browser `/api/version` result: passed and reported `05e8748`.

## Six Prompt Results

| # | Prompt | Result | Summary | Source-card behavior | Fretboard behavior | Hard-fail phrases |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `Show me the math answer to 1000000000x1000000000000000000.` | PASS | Returned a clean steel-guitar scope guardrail and did not compute the arithmetic. | No source links/cards; rendered `No sources returned`. | No fretboard, as expected. | None |
| 2 | `Show me a minor and b flat` | PASS | Interpreted as A minor and B-flat major; included `A-C-E` and `Bb-D-F`. | No real source links/cards; rendered `No sources returned`. | Fretboard card and SVG rendered. | None |
| 3 | `What do you get with strings 4-5-6 on the 8th fret with the A pedal engaged?` | PASS | Answered A minor, likely voiced `C-A-E`; listed string 4 = C, string 5 = A, string 6 = E. | No source links/cards; rendered `No sources returned`. | Fretboard card and SVG rendered. | None |
| 4 | `What is a C maj 7 and where do I play it?` | PASS | Answered Cmaj7 as `C-E-G-B`, explained the label, and gave E9 guidance. | No source links/cards; rendered `No sources returned`. | Fretboard card and SVG rendered for supported C major positions. | None |
| 5 | `give me a real lesson now` | PASS | Returned an actual I-to-IV E9 lesson using G at fret 3 and A+B for C. | No source links/cards; rendered `No sources returned`. | No fretboard, acceptable for this lesson response. | None |
| 6 | `How do I play uh A minor on E9?` | PASS | Answered A minor as `A-C-E` and listed practical A-pedal, E-lower, and B+C positions. | No real source links/cards; rendered `No sources returned`. | Fretboard card and SVG rendered. | None |

Hard-fail phrases checked:

- `Forum snippets should not become the main answer`
- `fallback`
- `retrieval`
- `source fragment`
- `deterministic map`
- `payload`
- `classifier`
- `I found this in limited source support`
- `Can someone please tell me`
- `I know when I first started`

None appeared in the browser-rendered answer bodies.

## Source-Card Behavior

Passed for the requested scope.

- Off-domain math guardrail did not show source links/cards.
- Deterministic chord/fretboard prompts rendered `No sources returned` rather than forum cards.
- No SGF/forum fragments appeared as primary answer text.

## Fretboard Render Result

Passed.

Fretboard card and SVG rendered for:

- `Show me a minor and b flat`
- `What do you get with strings 4-5-6 on the 8th fret with the A pedal engaged?`
- `What is a C maj 7 and where do I play it?`
- `How do I play uh A minor on E9?`

No fretboard was shown for the off-domain guardrail or the lesson-only response, which is acceptable for this minimal verification.

## Files Changed

Created:

- `docs/handoffs/task-completions/minimal-browser-verification-05e8748.md`

Implementation files changed:

- None.

Generated artifacts:

- None.

Deleted files:

- None.

## Tests And Checks

Commands run:

```bash
git status --short
git rev-parse --short HEAD
git log --oneline -5
curl -sS http://127.0.0.1:8770/api/version
curl -sS -I 'http://127.0.0.1:8770/?v=resolver-fix-05e8748'
curl -sS -I 'http://127.0.0.1:8770/ui/steel-guitar-rag-mock.html?v=resolver-fix-05e8748'
git diff --check -- docs/handoffs/task-completions/minimal-browser-verification-05e8748.md
git diff --check
```

Browser checks run:

- Opened `https://app.steelguitarrag.com/?v=resolver-fix-05e8748`.
- Opened protected `/api/version` in the authenticated browser and confirmed `git_sha=05e8748`.
- Submitted the six requested prompts through the authenticated browser UI.

Results:

- Git HEAD check: passed, `05e8748`.
- Local `/api/version`: passed, `05e8748`.
- Root route: passed, `302` to `/ui/steel-guitar-rag-mock.html`.
- Fallback route: passed, `200`.
- Browser auth: passed.
- Browser Q&A unlock: passed after session initialization.
- Six-prompt browser smoke: passed.
- Scoped `git diff --check` for this handoff: passed.
- Full worktree `git diff --check`: failed on pre-existing parked generated `docs/answer-eval-report.md` trailing whitespace; this task did not modify that file.

Skipped:

- Broad QA: intentionally skipped per task.
- Scorer calibration: intentionally skipped per task.
- API fallback QA: intentionally skipped; Lane 15 already covered API QA.

## Integration Notes

This run verifies the authenticated protected-preview browser path at runtime HEAD `05e8748`; it does not supersede Lane 15's broader API QA. The app may briefly show locked private-beta text immediately after reload until `/api/session` completes.

The root route remains a redirect to `/ui/steel-guitar-rag-mock.html`. That behavior is acceptable for this smoke target.

## Risk Assessment

Risk: low.

Why:

- No implementation or deployment configuration was changed.
- Verification was limited to the requested six prompts.
- Runtime identity was proven through the protected browser `/api/version`.

Rollback notes: no rollback needed; only this handoff was created.

## Commit Readiness

Not ready to commit.

Reason: no commit was requested, and the worktree contains many unrelated parked dirty/untracked files. This handoff can be committed later by Repo Steward if desired.

## Suggested Next Step

Recommended lane: 12 Self-Hosted Deployment or 01 Repo Steward.

Exact next prompt:

```text
Lane 01 Repo Steward: review and, if appropriate, commit only docs/handoffs/task-completions/minimal-browser-verification-05e8748.md as the Lane 12 minimal protected-preview browser verification handoff. Do not stage parked docs, generated reports, corpus/source files, or implementation files.
```

## Final Decision

Browser ready.
