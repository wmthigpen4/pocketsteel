# Travis Companion Worker

This Worker serves the Access-protected authoring studio, D1/R2/Workflow APIs,
leased private-runner surface, Teachable OAuth verification, stable lesson
iframe, token-authorized audio ranges/downloads, and immutable publication
bundles.

## Local development

```bash
cp workers/travis-companion/.dev.vars.example workers/travis-companion/.dev.vars
npx wrangler d1 migrations apply DB --local \
  --config workers/travis-companion/wrangler.jsonc
npx wrangler dev --config workers/travis-companion/wrangler.jsonc --port 8791
```

Open `http://127.0.0.1:8791/admin?local=1`. The `local=1` author bypass exists
only when `ENVIRONMENT=development`. The learner preview exposes a local token
button only in that environment.

Useful checks:

```bash
npm run check:travis-companion
npm run test:travis-companion
npx wrangler deploy --dry-run --env='' \
  --config workers/travis-companion/wrangler.jsonc
```

## Production configuration

Before any staging or production deployment, replace every `.example.invalid`
or `CONFIGURE_*` value and provision the named D1 database, private R2 bucket,
and Workflow. Configure these secrets separately in each environment:

- `RUNNER_TOKEN`
- `LESSON_TOKEN_SECRET` (at least 32 random bytes)
- `TEACHABLE_CLIENT_SECRET`
- `TRAVIS_COPEDENT_JSON` (the approved account-level snapshot)

Configure Cloudflare Access for `/admin` and `/api/author/*`, then set the exact
Access team domain and audience. Register `${PUBLIC_ORIGIN}/auth/teachable/callback`
as the Teachable OAuth redirect and request required `courses:read`. Enrollment
is verified through Teachable's current-user course endpoint for the configured
course ID; a profile response is not treated as enrollment evidence.

The Teachable lesson needs one iframe:

```html
<iframe
  src="https://configured-travis-host/embed/lesson-slug"
  title="Lesson companion"
  loading="lazy"
  style="width:100%;min-height:760px;border:0"
  allow="autoplay"
></iframe>
```

`FRAME_ANCESTORS` must contain only the exact Travis school origins. Published
JSON and PDFs use content-addressed, revisioned R2 keys; publish writes both
objects before a transactional D1 pointer update. Rollback updates only that
pointer. No v1 retention or purge job is configured.
