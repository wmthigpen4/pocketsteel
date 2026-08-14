# Isolated Travis preview deployment runbook

Target project: `steel-guitar-rag-travis-preview`

Target review URL: `https://travis-preview.steelguitarrag.com/howdy`

This runbook is intentionally separate from the Mac mini runtime and the
existing `app.steelguitarrag.com` Access application. Do not change the main
app policy, Tunnel, service, corpus, model services, or root-domain Pages
project while carrying it out.

## 1. Human inputs required before external changes

- Use the already-known project-owner email as the only Access identity for
  the initial `owner_only` phase. Keep it in the ignored private release
  configuration; do not commit or print it.
- Do not add the partner tester yet. Moving to `partner_review` is a separate,
  explicitly authorized promotion step.
- Written approval to package the backing track in this private preview.
- Written approval to use the selected Travis Toy Tutorials imagery/wordmark.
- Travis's approval of the chord timeline, exact taught solo, source
  copedent, printable tab/notation, attribution, and PDF proof.

Do not infer any of these from access to the lesson page.

## 2. Create the empty Direct Upload project

Install the repository-pinned Wrangler first with `npm ci`, authenticate with
the intended Cloudflare account, and confirm it with
`node_modules/.bin/wrangler whoami`.

Create only the dedicated project:

```bash
node_modules/.bin/wrangler pages project create \
  steel-guitar-rag-travis-preview \
  --production-branch main
```

Do not connect a Git provider. Direct Upload projects accept prebuilt assets
and do not later convert to Git integration. See Cloudflare's
[Direct Upload documentation](https://developers.cloudflare.com/pages/get-started/direct-upload/).

## 3. Attach the custom domain before enabling Access

In Workers & Pages, open the new project, choose **Custom domains**, and add
`travis-preview.steelguitarrag.com`. Confirm Cloudflare created or validated
only that subdomain. Cloudflare documents this sequence in
[Pages custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/).

Cloudflare currently notes that a custom domain cannot be added while an
Access policy is already enabled on it, which is why the hostname is attached
before the applications below.

## 4. Protect every Pages address

Enable One-time PIN in Zero Trust if it is not already an available login
method. An OTP login method by itself is not an allowlist; the Allow policy
must include only the exact project-owner email during the initial phase.

Configure three Access applications/policies:

1. Production Pages hostname:
   `steel-guitar-rag-travis-preview.pages.dev`.
2. Preview deployment wildcard:
   `*.steel-guitar-rag-travis-preview.pages.dev`.
3. Custom hostname: `travis-preview.steelguitarrag.com`.

For each application:

- application type: self-hosted;
- action: Allow;
- Include: the one exact project-owner email only;
- Require: One-time PIN login method;
- no Everyone, email-domain, or login-method-only Include rule;
- short pilot session duration;
- all other identities fail closed.

Cloudflare's Pages setting can create the production/preview applications;
the custom-domain application is configured separately. Follow the current
[Pages preview Access guidance](https://developers.cloudflare.com/pages/configuration/preview-deployments/)
and [Pages known-issues sequence](https://developers.cloudflare.com/pages/platform/known-issues/).
Cloudflare's [OTP guidance](https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/one-time-pin/)
confirms that approved email addresses belong in the policy.

Record the three application IDs and anonymous-denial checks in the private
`release-config.json` with `reviewPhase: "owner_only"`. Do not add the partner
tester to any policy in this phase, and never change the application for
`app.steelguitarrag.com`.

## 5. Package and preflight

Follow the commands in
`partner_companions/travis_howdy/README.md`. The packager emits only:

- root redirect;
- `/howdy`, `/howdy/embed-demo`, and `/howdy/print` HTML;
- root branded `404.html`;
- `_headers` and `_redirects` control files;
- one content-hashed asset directory containing CSS, JavaScript, canonical
  JSON, approved audio, approved PDF, and approved hero imagery.

Wrangler's Pages Direct Upload command does not currently offer a dry-run
flag. Use `wrangler pages dev` as the non-uploading Pages preflight and run the
static verifier. Confirm:

- root is a 302 to `/howdy`;
- the three companion routes resolve;
- unknown, app, API, and encoded traversal paths return the branded 404;
- HTML and JSON are `no-store`;
- content-hashed assets are `private, max-age=31536000, immutable`;
- CSP permits only same-origin companion resources;
- there are no browser console errors or off-origin resource requests.

## 6. Direct Upload and smoke

Run `scripts/publish_travis_companion.py` first without the final flag. If it
reports `validated-not-deployed`, rerun it with
`--deploy-reviewed-bundle`. This is the only upload step.

The publisher records the immutable `*.pages.dev` deployment URL in the
private manifest. Do not share that address. Verify anonymously that the
custom, production Pages, and immutable/preview Pages addresses all fail
closed at Access. Then verify the project owner's OTP access at the branded
URL. Stop there during the `owner_only` phase.

## 7. Promote to partner review later

Only after explicit authorization to add the partner tester:

1. Add the partner's exact email to each of the three dedicated preview
   Access policies, and nowhere else.
2. Change the ignored private release configuration to
   `reviewPhase: "partner_review"` with exactly two tester emails.
3. Package a new immutable release manifest and rerun anonymous plus both-
   identity Access smoke.
4. Send only `https://travis-preview.steelguitarrag.com/howdy`.

Suggested review checklist:

- chord changes and bar boundaries;
- exact taught route versus comparison-only alternatives;
- phrase-loop start/end points;
- control labels and source copedent;
- compact embed density;
- full-page phone/tablet/desktop layout;
- notation/tab print proof and attribution;
- backing-track synchronization;
- feedback button context.

## 8. Rollback or closure

Rollback by promoting the prior immutable Pages deployment. Do not edit files
in a live deployment. To close the pilot, remove/disable the custom hostname
and the three dedicated Access applications. Do not alter
`app.steelguitarrag.com`, root DNS, the Mac mini service, Tunnel, corpus, or
model infrastructure.
