# Howdy embed: Teachable typeset and preserved discussion space

## Task summary

Matched the standalone Howdy embed demo to the measured typography of the live
Travis Toy Tutorials Teachable lesson and added a reserved Discussion module
below the companion. The placeholder makes the intended insertion order
explicit: lesson video, companion, then Teachable's existing member comments.
It is disabled and does not collect, replace, copy, or move member discussion.

No Teachable content was changed. No deployment, Access gate, tester identity,
remote service, analytics, model client, or general application surface was
added.

## Lane classification

- Primary: `06 UX/UI Design`
- Verification: `15 QA / Answer Eval`
- Closeout: `01 Repo Steward`
- Task mode: approved follow-up UI implementation.

## Files changed

- `partner_companions/travis_howdy/templates/embed.html`
- `partner_companions/travis_howdy/site/companion.css`
- `tests/test_travis_companion.py`
- this handoff

## Live reference measurements

Browser inspection of the authenticated Teachable lesson established the
following computed styles, all of which are now reproduced in the embed demo:

- Lesson heading: Metropolis, 22.784px, 600, 34.176px line height,
  `#212338`, normal tracking, `10px 0 30px` margin.
- Discussion label: Metropolis, 15px, 700, 28px line height, white on
  `#134361`, 3px radius, `0 15px` padding.
- Post-a-comment heading: Metropolis, 18px, 600, 19.8px line height.
- Comment box: Metropolis, 15px, 400, 21.4286px line height, 14px padding,
  5px top radius.
- Actions retain the school coral `#ff3f20` and 6px radius.

The compact companion presentation now also removes its previous extra-heavy
weights and negative heading tracking, using the same 600/700 Teachable weight
system. The full Travis-branded companion is intentionally unchanged.

## Discussion behavior

- The reserved Discussion card follows the companion in document order.
- It includes a generic member avatar, comment composer, Add Image label, and
  Post Comment treatment so vertical space is realistic.
- The textarea and button are disabled; the preview collects no comment text
  or identity.
- Visible copy states that comments remain in Teachable.
- Mobile CSS preserves the composer with a reduced avatar and padding.

## Tests and checks

- `.venv/bin/python -m pytest tests/test_travis_companion.py -q` — 20 passed.
- `git diff --check` — passed for the task files.
- Deterministic package build — passed with 12 allowlisted files.
- Isolation verifier — passed; same-origin-only networking and all eight
  blocked route/traversal checks remained intact.
- Browser DOM smoke — Discussion appears after the companion, with a disabled
  comment box and no form submission surface.
- Browser computed-style smoke — all four live-reference typography groups
  matched exactly.
- Browser visual smoke — desktop embed remained within the 900px lesson frame;
  responsive discussion rules were inspected for the existing 680px breakpoint.

## Smoke Target

- Target type: local
- Exact URL the user should use:
  `http://127.0.0.1:8899/howdy/embed-demo/`
- Auth required: no
- Access gate: none
- Local backend URL: `http://127.0.0.1:8899`
- Expected backend port: `8899`
- Who should test this URL: Codex and the user
- Do not test: general Steel Guitar RAG application or API routes
- Known caveat: the release path accepts an approved private Metropolis font;
  the ungated local draft retains the declared Metropolis stack and uses the
  closest installed fallback when that licensed asset is absent.

## Risk assessment

Low. This is isolated embed-demo presentation work. Musical data, runtime
behavior, full-page branding, print content, network policy, and remote state
are unchanged. Rollback is the preceding Git commit.

## Human decision needed

No decision is needed to inspect the preview. The discussion module is a
layout placeholder only; final Teachable insertion should leave the platform's
real comment feature in place beneath the companion.

## Safe-to-stage exact file list

- `partner_companions/travis_howdy/templates/embed.html`
- `partner_companions/travis_howdy/site/companion.css`
- `tests/test_travis_companion.py`
- `docs/handoffs/task-completions/2026-08-14-1303-06-howdy-teachable-typeset-comments.md`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- the three pre-existing unrelated untracked handoffs
- `tmp/`, `.wrangler/`, `output/`, private companion/source/video/audio/PDF
  data, identities, credentials, and all unrelated dirty files

## Commit readiness

Safe to commit.

## Suggested next step

Reload the local embed demo and confirm that the transition from the companion
into Discussion feels like one Teachable lesson page at the width Travis's
members typically use.
