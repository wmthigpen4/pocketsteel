# Workspace card mini previews

## Task summary

Brought the landing workspace cards closer to the approved mockup by giving each non-Ask card a compact visual preview of its tool:

- Fretboard Explorer: miniature three-grip neck visualization.
- Melody Studio: six-note musical phrase on a five-line staff.
- Lessons: compact Beginner/Intermediate/Advanced selector and a starter lesson preview.
- Ask: retained its existing functional question composer.

Also aligned card icons and headings horizontally and changed the first two CTAs to `Explore now` and `Start composing`, matching the mockup's product-card tone.

No progress percentage, saved state, account state, or unsupported audio/transcription claim was added.

## Lane classification

- Primary lane: `06 UX/UI Design`
- Task mode: YELLOW landing UI enhancement explicitly approved by the user's mockup-directed request.

## Files changed

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1838-06-workspace-card-mini-previews.md`

No image asset was copied into the repository. No shared renderer, workspace interior, backend, auth, corpus, Cloudflare, or deployment configuration changed.

## Tests and checks

- `node --check ui/answer-client.js` — passed.
- `node --check ui/pedal-steel-fretboard.js` — passed.
- `node --check ui/landing-home.js` — passed.
- Focused frontend/fretboard suite — `95 passed in 2.91s`.
- Full Python suite — `1036 passed in 48.12s`.
- Scoped `git diff --check` — passed.
- Local desktop and mobile-breakpoint browser smoke — passed.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested: `http://127.0.0.1:8897/ui/steel-guitar-rag-mock.html?access=beta_user&v=workspace-card-previews-local-1`
- Cache-busted URL tested: same as above
- Exact URL the user should use: protected-preview URL will be recorded after commit and restart
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8897`
- Expected backend port: 8897
- Expected git HEAD: working tree on `5aad3d76700bbc271762c65aee62b81b3beca3dd`
- Version endpoint: not used for local visual smoke
- Version endpoint result: not attempted
- If version endpoint missing, how version is inferred: cache-busted assets served directly from the scoped working tree
- Whether app root `/` works: not tested in this focused local smoke
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: yes
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: yes
- Who should test this URL: Codex
- Do not test these URLs: historical cached landing URLs or the public marketing page
- Known caveats: the responsive override reported a 487-pixel effective width when 390 pixels was requested; it still exercised the below-700-pixel layout.

Browser assertions:

- Four product cards rendered at equal 423-pixel desktop heights.
- Three visual previews rendered.
- Melody score rendered visibly at 238×88 pixels with six notes.
- Explorer preview rendered three colored grips.
- Lessons preview rendered once with no progress claim.
- Ask composer remained enabled.
- Mobile-breakpoint cards remained one column; the score expanded to the card width.
- Desktop and mobile-breakpoint layouts had zero document overflow.

## Integration notes

The previews are semantic inline HTML/SVG and CSS rather than new raster assets or additional renderer instances. They add no tab stops and do not alter destination behavior.

The landing shell stylesheet cache key is `workspace-card-previews-20260713-1`.

## Risk assessment

Low. The change is isolated to landing markup, landing-scoped styles, and regression tests. Rollback is the single scoped commit.

## Human decision needed

No. The request explicitly asked for the landing cards to resemble the supplied mockup, including a score beneath Melody Studio.

## Safe-to-stage exact file list

- `ui/steel-guitar-rag-mock.html`
- `ui/workspace-shell.css`
- `tests/test_landing_home_ui.py`
- `tests/test_same_origin_smoke_server.py`
- `docs/handoffs/task-completions/2026-07-13-1838-06-workspace-card-mini-previews.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- Earlier unstaged coordination handoffs.
- Dirty/unrelated `ui/brand/`, `public/`, `Neon Sign/`, corpus, source-inbox, backend, auth, Cloudflare, vector, embedding, private-data, and deployment paths.

## Recommended next lane

`01 Repo Steward` for exact-path commit, followed by `12 Self-Hosted Deployment` for protected-preview restart and authenticated browser smoke.

## Commit readiness

Safe to commit

## Suggested next step

Commit the five exact paths, update the protected preview, and visually compare the workspace cards with the supplied mockup at desktop and mobile widths.
