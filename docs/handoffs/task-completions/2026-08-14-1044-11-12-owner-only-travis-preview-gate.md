# Owner-only Travis preview access gate

## Task summary

Corrected the deterministic Travis preview release contract so the initial
review phase includes only the project owner. The already-known owner email is
treated as a private release input and is never committed, printed, bundled,
or emitted into a release manifest.

The release contract now has two explicit phases:

- `owner_only`: exactly one named Cloudflare Access identity;
- `partner_review`: exactly two named identities, available only through a
  later explicit private-configuration promotion.

The packager, canonical artifact, verifier, publisher, tests, example private
configuration, deployment runbook, and prior implementation handoff now agree
on this phased contract. A manifest cannot claim a different phase or tester
count than the canonical companion.

No Cloudflare project, DNS record, custom domain, Access application, policy,
identity, deployment, secret, or main-app setting was created or changed.
The partner tester was not added anywhere.

## Lane classification

- Lane 11: Access identity and fail-closed phase contract
- Lane 12: release-manifest and publisher enforcement
- Lane 15: regression and isolation verification
- Lane 01: exact-path commit hygiene

This is a user-approved correction to the previously approved feature scope.
Live Cloudflare changes remain behind the musical, rights, brand, print, and
private-asset approval gates.

## Files changed

- `partner_companions/travis_howdy/release.py`
- `partner_companions/travis_howdy/content/howdy.draft.json`
- `partner_companions/travis_howdy/release-config.example.json`
- `partner_companions/travis_howdy/README.md`
- `scripts/verify_travis_companion.py`
- `scripts/publish_travis_companion.py`
- `tests/test_travis_companion.py`
- `deploy/travis-preview/README.md`
- `docs/handoffs/task-completions/2026-08-14-1032-06-11-12-15-travis-howdy-companion.md`
- this handoff

Generated ignored draft outputs were refreshed under `tmp/`; they must not be
staged.

## Tests and checks

- `.venv/bin/pytest -q tests/test_travis_companion.py` - 16 passed.
- `npm run build:travis-preview:draft` - passed.
- `npm run verify:travis-preview` - passed; 11 allowlisted files,
  same-origin-only network policy, and all blocked-route checks retained.
- `.venv/bin/ruff check partner_companions/travis_howdy/release.py scripts/verify_travis_companion.py scripts/publish_travis_companion.py tests/test_travis_companion.py` - passed.
- Python compile checks for the companion release/package/verify/publish/PDF
  modules - passed.
- `node --check partner_companions/travis_howdy/site/companion.js` - passed.
- `git diff --check` - passed before handoff creation and must be rerun before
  commit.

Focused coverage now proves:

- `owner_only` accepts exactly one identity and rejects a second;
- `partner_review` accepts exactly two only when selected explicitly;
- unknown phases fail closed;
- private tester addresses are not copied into the companion artifact;
- manifest phase/count drift from the canonical artifact is rejected;
- the existing human approval gates remain required.

Browser smoke was not repeated because no HTML, CSS, JavaScript, route, or
rendering behavior changed. The same generated UI bundle passed the static
isolation verifier.

## Integration notes

The ignored private `release-config.json` for the initial rollout must contain:

```json
{
  "reviewPhase": "owner_only",
  "testerEmails": ["<already-known-owner-email>"]
}
```

The placeholder above is documentation only. The actual address must remain
in the private configuration and Cloudflare Access policy, never in Git or
generated deploy artifacts.

Adding the partner later requires all of the following as a separate action:

1. explicit user authorization;
2. the partner address added only to the three dedicated Travis preview
   Access applications;
3. `reviewPhase: "partner_review"` with exactly two tester emails;
4. a new immutable release manifest;
5. anonymous and both-identity Access smoke.

The Access policy for `app.steelguitarrag.com` must remain unchanged in both
phases.

## Risk assessment

Low for the tracked correction. The primary remaining risk is operational:
the Cloudflare Access isolation cannot be proven until the dedicated project
and three preview applications are created. The publisher still refuses a
draft or a release lacking music, chord, tab, print, audio-rights, brand, and
Access approvals.

Rollback is the single scoped correction commit; there are no external-state
changes to reverse.

## Human decision needed

Yes, but not an email decision. The known owner identity is sufficient for the
initial phase. Live packaging/deployment still needs the approved musical
artifact, audio-rights approval, brand assets/approval, and approved print
proof. Partner access remains explicitly deferred.

## Safe-to-stage exact file list

- `deploy/travis-preview/README.md`
- `docs/handoffs/task-completions/2026-08-14-1032-06-11-12-15-travis-howdy-companion.md`
- `docs/handoffs/task-completions/2026-08-14-1044-11-12-owner-only-travis-preview-gate.md`
- `partner_companions/travis_howdy/README.md`
- `partner_companions/travis_howdy/content/howdy.draft.json`
- `partner_companions/travis_howdy/release-config.example.json`
- `partner_companions/travis_howdy/release.py`
- `scripts/publish_travis_companion.py`
- `scripts/verify_travis_companion.py`
- `tests/test_travis_companion.py`

## Files that must not be staged

- `docs/handoffs/task-completions/integration-status.md`
- `docs/handoffs/task-completions/2026-08-04-1629-12-app-origin-502-diagnosis.md`
- `docs/handoffs/task-completions/2026-08-12-0714-18-rag-architecture-research-summary.md`
- `docs/handoffs/task-completions/2026-08-13-1323-15-huge-question-answer-regression.md`
- `tmp/`, `output/`, `.wrangler/`, private release configuration, actual
  tester addresses, Access IDs, audio, font, imagery, rights records,
  credentials, and unpublished musical content
- all unrelated corpus, vector, model, transcript, source-inbox, main-app,
  Tunnel, DNS, auth-policy, and dirty worktree files

## Recommended next lane

Lane 20/18 should complete and approve the private musical/tab artifact and
print proof. After the remaining rights and brand approvals exist, Lane 11 can
create the three owner-only Access applications and Lane 12 can create and
deploy the isolated Pages project. Do not enter `partner_review` yet.

## Commit readiness

Safe to commit the exact file list above after final staged-diff checks.

## Suggested next step

Proceed under Repo Steward auto-approval with exact-path staging for this
owner-only correction. Afterward, keep the live deployment stopped at the
existing content/rights/brand/print gate.
