# Howdy embed simplification

## Task summary

Simplified the Teachable-style Howdy embed so each top-level tab has one clear
learner job. Transcript-backed search now appears only on Map and is collapsed
until requested. Phrase Practice no longer repeats the song map, and the
compact presentation no longer shows the redundant inner mode switcher,
explanatory layer band, source card, long intro, or full review-status ribbon.

The standalone Travis companion remains expanded: full layer names,
descriptions, open lesson search, inner modes, source context, and partner
branding are unchanged there. Musical data, print output, comments space,
playback behavior, security policy, and remote state were not changed.

## Lane classification

- Primary: `06 UX/UI Design`
- Verification: `15 QA / Answer Eval`
- Closeout: `01 Repo Steward`
- Task mode: user-approved follow-up UI flow adjustment under Autopilot.

## Files changed

- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/site/companion.css`
- `tests/test_travis_companion.py`
- this handoff

## Compact information architecture

- **Map:** collapsed `Search lesson moments`, phrase route, and eight-bar chord
  chart. No transport or practice workspace.
- **Practice:** step controls, 50% phrase loop, current/next move, fretboard,
  compact tab, phrase note, and feedback. No search or song map.
- **Chords:** chord chart, 75% transport, held chord move, fretboard, chord note,
  and feedback. No search, solo tab, or duplicate inner mode choice.
- **Explore:** only the two lesson-demonstrated comparisons. No search, map,
  transport, practice workspace, or generated substitutes.

The compact tab names are now `Map`, `Practice`, `Chords`, and `Explore`.
The preview marker is reduced to owner-preview revision and build SHA, while
the key, meter, tempo, full companion, and print actions remain visible.

## Tests and checks

- `node --check partner_companions/travis_howdy/site/companion.js` — passed.
- `.venv/bin/python -m pytest tests/test_travis_companion.py -q` — 21 passed.
- Focused `git diff --check` — passed.
- Deterministic package build — passed with 12 allowlisted files.
- Isolation verifier — passed; same-origin-only networking and all eight
  blocked route/traversal checks remained intact.
- Browser Map smoke — search collapsed by default; opening it and searching
  `hammer` returned only the indexed open-position A-pedal moment.
- Browser tab smoke — verified search visibility `true/false/false/false` for
  Map/Practice/Chords/Explore; duplicate inner modes and source card remained
  hidden on all compact tabs.
- Browser full-page regression smoke — full layer labels, descriptions, open
  lesson search, featured results, and full companion header remained visible.

## Smoke Target

- Target type: local
- Result type: browser smoke
- Exact browser URL tested:
  `http://127.0.0.1:8899/howdy/embed-demo/`
- Cache-busted URL tested: not required for the content-hashed local bundle
- Exact URL the user should use:
  `http://127.0.0.1:8899/howdy/embed-demo/`
- Auth required: no
- Auth provider: none
- Cloudflare Access login result: not required
- Local backend URL: `http://127.0.0.1:8899`
- Expected backend port: `8899`
- Expected git HEAD: implementation commit produced by this task
- Version endpoint: none in this isolated static product
- Version endpoint result: not applicable
- If version endpoint missing, how version is inferred: visible owner-preview
  revision and 12-character build SHA
- Whether app root `/` works: yes; it redirects to `/howdy`
- Whether app root `/` is expected to work: yes
- Whether `/ui/steel-guitar-rag-mock.html` works: no
- Whether `/ui/steel-guitar-rag-mock.html` is expected to work: no; isolation
  requires 404
- Who should test this URL: Codex and the user
- Do not test these URLs: general Steel Guitar RAG app or API routes
- Known caveats: musical, chord, copedent, print, brand, and audio-rights
  approvals remain outstanding

## Integration notes

No schema or canonical-event changes were made. Compact-versus-full behavior
continues to derive from `data-presentation`; search remains deterministic and
in-memory. CSS controls which authored workspace is visible for each layer.

## Risk assessment

Low. The change is confined to presentation and visibility. The full companion
regression smoke passed, and the static bundle/network policy is unchanged.
Rollback is the preceding Git commit.

## Human decision needed

No. User smoke can continue on the ungated local preview. Further simplification
would be a product choice about removing either the compact fretboard or compact
tablature from Practice; both remain because the earlier accepted companion
scope called for both.

## Safe-to-stage exact file list

- `partner_companions/travis_howdy/templates/companion.fragment.html`
- `partner_companions/travis_howdy/site/companion.js`
- `partner_companions/travis_howdy/site/companion.css`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-14-1311-06-howdy-embed-simplification.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- the three pre-existing unrelated untracked handoffs
- `tmp/`, `.wrangler/`, `output/`, private companion/source/video/audio/PDF
  data, identities, credentials, and all unrelated dirty files

## Recommended next lane

Continue user smoke in Lane 06. Lane 15 should perform independent musical and
print QA only after the compact interaction hierarchy settles.

## Commit readiness

Safe to commit

## Suggested next step

Reload the embed demo and compare Map, Practice, Chords, and Explore. If the
Practice tab still feels too dense, choose whether compact tab or fretboard is
the secondary element to collapse; do not remove either from the full page.
