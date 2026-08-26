# Owner Chord Reader Protected Hostname

## Task summary

- Published the owner chord-reader workbench at `https://chords.steelguitarrag.com/` for phone and tablet testing.
- Added a separate Cloudflare Access self-hosted application using the existing owner-only reusable policy.
- Added a separate published application route on the existing `steel-rag-mac-mini` tunnel from `chords.steelguitarrag.com` to `http://127.0.0.1:8899`.
- Kept `app.steelguitarrag.com` unchanged on `http://127.0.0.1:8770`.
- Hardened the chord-reader origin so authenticated requests can serve only the four workbench UI files, its API, and seekable generated audio—not arbitrary repository files.
- Updated the owner-page privacy copy for access through the protected hostname.
- Intentionally did not modify `docs/handoffs/task-completions/integration-status.md`; its pre-existing edit remains parked.

## Lane classification

- Primary lane: `12 Self-Hosted Deployment`
- Supporting lanes: `11 Auth / Security`, `06 UX/UI Design`, `15 QA / Answer Eval`, `01 Repo Steward`
- Mode: RED deployment/auth/DNS work, explicitly authorized by the user.

## Files changed

- `scripts/serve_owner_chord_reader.py`
- `ui/chord-reader-owner-test/index.html`
- `tests/test_owner_chord_reader_ui.py`
- `docs/handoffs/task-completions/2026-08-26-1450-12-owner-chord-reader-protected-hostname.md`

No files were deleted. The ignored generated manifest and song audio remain local and uncommitted.

## Tests and checks

- `.venv/bin/python -m pytest tests/test_owner_chord_reader_ui.py -q` — passed, 4 tests.
- Authenticated browser smoke against the protected hostname — passed.
- Anonymous `curl -sS -I https://chords.steelguitarrag.com/` — `302` to Cloudflare Access.
- Anonymous `curl -sS -I https://app.steelguitarrag.com/` — existing `302` to Cloudflare Access; app hostname remains protected.
- Authenticated request to `https://chords.steelguitarrag.com/scripts/serve_owner_chord_reader.py` — `404`, confirming repository source is not exposed.
- Root `https://chords.steelguitarrag.com/` — redirects to `/ui/chord-reader-owner-test/` after Access.
- Workbench loaded the attached song as `3:54`, Ab major, 6/8, 137 BPM, 96 changes.
- Exact-model timing status displayed because downbeat phase is unresolved.
- Selecting change 3 sought to `0:18`, updated the persistent transport to change 3 / chord 4, and marked the same box `NOW`.
- Playback was paused after the smoke.

## Smoke Target

- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested: `https://chords.steelguitarrag.com/ui/chord-reader-owner-test/?v=owner-secure-1`
- Cache-busted URL tested: `https://chords.steelguitarrag.com/ui/chord-reader-owner-test/?v=owner-secure-1`
- Exact URL the user should use: `https://chords.steelguitarrag.com/`
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result: succeeded using the existing browser session
- Local backend URL: `http://127.0.0.1:8899`
- Expected backend port: `8899`
- Expected git HEAD: scoped owner-server hardening commit produced from prior HEAD `c6290a51`
- Version endpoint: none for this standalone owner workbench
- Version endpoint result: version inferred from the scoped commit and cache-busted browser smoke
- Whether app root `/` works: yes; redirects to the owner workbench
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: not tested
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: no; it belongs to the separate `app` origin
- Who should test this URL: Codex and the user
- Do not test these URLs: do not substitute `app.steelguitarrag.com`; it is a separate application
- Known caveats: the Mac must remain awake, connected, and running the loopback chord-reader server for the tunnel origin to respond

## Integration notes

- Cloudflare reported successful tunnel settings and DNS record creation for `chords.steelguitarrag.com`.
- The new Access application is named `Steel Guitar RAG Chord Reader` and reuses the existing owner-only policy.
- The existing `app.steelguitarrag.com` and `test.steelguitarrag.com` tunnel routes were not edited.
- The origin still binds only to loopback; Cloudflare Tunnel is the only public path.
- The current chord-reader process is running on port 8899. It is suitable for the current owner test but requires the Mac to remain on.

## Risk assessment

- Risk: medium because this changes Cloudflare Access, DNS, and Tunnel configuration.
- Exposure is limited by Cloudflare Access and the loopback-only origin.
- Rollback: remove only the `chords.steelguitarrag.com` published application route and its matching Access application/DNS record. Do not change the `app.steelguitarrag.com` route.

## Human decision needed

- No. User smoke can continue at the protected hostname.

## Safe-to-stage exact file list

- `scripts/serve_owner_chord_reader.py`
- `ui/chord-reader-owner-test/index.html`
- `tests/test_owner_chord_reader_ui.py`
- `docs/handoffs/task-completions/2026-08-26-1450-12-owner-chord-reader-protected-hostname.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `ui/chord-reader-owner-test/local-data/`
- Any credentials, tunnel tokens, environment files, logs, or generated media

## Recommended next lane

- Lane 15 user smoke: test the highlighted chord changes from a phone or tablet in front of the guitar.

## Commit readiness

Safe to commit

## Suggested next step

Open `https://chords.steelguitarrag.com/` on the phone or tablet, complete Cloudflare Access login if prompted, and listen through the attached song while watching the `NOW` box.
