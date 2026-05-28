# Cloudflare Pages Landing Deployment

This document describes how to deploy the static public landing page for `steelguitarrag.com`.

Do not connect the public root site to live RAG, Ollama, Chroma, private corpus files, or the beta app until the access model is ready.

## Static Output

- Source page: `ui/steel-guitar-rag-landing.html`
- Cloudflare Pages output directory: `deploy/landing`
- Public root file: `deploy/landing/index.html`
- Required assets: `deploy/landing/assets/`

The output directory is intentionally static. It should not include `/api/answer`, backend code, embeddings, indexes, raw corpus files, private transcripts, or local environment files.

The only public API route planned for this landing deployment is:

```text
POST /api/interest
```

That route captures interest-list submissions only. It must not call live RAG, Ollama, Chroma, or corpus services.

## Current Cloudflare Pages Method

The current landing deployment method is Wrangler/manual deploy from the static
output directory:

```bash
npx --yes wrangler@latest pages deploy deploy/landing \
  --project-name steel-guitar-rag-landing \
  --branch feature/answer-api \
  --commit-dirty=true
```

This is acceptable for early preview because the landing page is already
working, the deployment surface is limited to `deploy/landing`, and it avoids
connecting the whole mixed local repo state to automatic Pages builds.

Manual deploy checks:

1. Verify `deploy/landing/index.html` matches the intended public landing page.
2. Verify `deploy/landing/assets/` contains only public landing assets.
3. Verify there are no calls to `/api/answer`.
4. Verify the early-access CTAs point to the interest form, not to the private app.
5. Verify `POST /api/interest` returns success for a valid email.

## Later GitHub Integration

Cloudflare Pages GitHub integration should be a later migration, not the current
deployment method.

Later method:

1. Create a new Git-connected Cloudflare Pages project.
2. Connect the GitHub repository.
3. Use `main` as the production branch.
4. Deploy only public landing assets.
5. Use no build command unless a landing-only build step is added.
6. Set the output directory to:

   ```text
   deploy/landing
   ```

7. Keep `app.steelguitarrag.com` separate from the public landing page.
8. Keep `/api/answer`, Ollama, Chroma, corpus data, embeddings, and private beta
   app assets out of the landing deployment.

Reason not now:

- The repo still has mixed dirty lanes.
- Generated artifacts must not deploy.
- A Direct Upload Pages project cannot simply be converted to Git integration;
  use a new Git-connected project when migrating.
- The current landing page and interest form are already working.

Required prerequisites before GitHub integration:

- `.gitignore` hygiene reviewed.
- Clean branch with only intended public landing files.
- Deploy path documented and enforced.
- No secrets or generated corpus data in the repo.
- No raw corpus, Chroma stores, embeddings, logs, private transcripts, or
  generated corpus outputs in the landing deploy path.
- CI/test gate for the public landing page.

## Interest Form

The public landing page includes an early-access interest form with:

- name
- email
- player level, optional
- interest checkboxes
- optional message

The form posts JSON to:

```text
/api/interest
```

The custom-domain Function route has been verified on `https://steelguitarrag.com/api/interest`, so the landing form should use the same-origin `/api/interest` route. This keeps the public form independent from preview branch aliases such as `main.steel-guitar-rag-landing.pages.dev`.

The Cloudflare Pages Function lives at:

```text
functions/api/interest.js
```

It validates email, rejects obviously invalid addresses, adds a timestamp and generated id, and returns JSON. It has placeholder Turnstile support through a `turnstileToken` field, but Turnstile verification is intentionally skipped until a site key/secret are configured.

## Required Cloudflare Binding

Preferred storage binding:

```text
STEEL_RAG_INTEREST_D1
```

Create a D1 database table before relying on persistent capture:

```sql
create table if not exists interest_submissions (
  id text primary key,
  created_at text not null,
  name text,
  email text not null,
  player_level text,
  interests text,
  message text,
  user_agent text,
  ip_hash text
);
```

The Pages Function D1 insert expects exactly these columns:

- `id`
- `created_at`
- `name`
- `email`
- `player_level`
- `interests`
- `message`
- `user_agent`
- `ip_hash`

If the table still has older columns such as `submitted_at`, `interests_json`,
`turnstile_token_present`, or `cf_ray`, the D1 insert can throw inside the Pages
Function and Cloudflare may surface that as error `1101`.

Alternative storage binding:

```text
STEEL_RAG_INTEREST_KV
```

If neither binding is configured, the endpoint returns success with `stored: false`. This keeps local/dev previews from failing loudly, but production should configure one binding before collecting real interest.

## Viewing or Exporting Submissions

For D1, query or export rows from Cloudflare:

```bash
wrangler d1 execute <database-name> --command "select created_at, email, name, player_level, interests from interest_submissions order by created_at desc limit 50;"
```

For KV, list keys with the `interest:` prefix, then read values:

```bash
wrangler kv key list --binding STEEL_RAG_INTEREST_KV --prefix interest:
```

Email routing for `hello@steelguitarrag.com` should be configured separately in Cloudflare Email Routing or another mail provider. The interest form does not send email yet.

## Debugging D1 1101 Errors

If `POST /api/interest` returns Cloudflare error `1101` after adding the D1
binding:

1. Confirm the Pages Function is live by checking behavior without a D1/KV
   binding in a preview environment. The expected no-storage response is:

   ```json
   {"ok":true,"stored":false,"storage":"missing"}
   ```

2. Confirm the D1 binding name is exactly:

   ```text
   STEEL_RAG_INTEREST_D1
   ```

3. Inspect the deployed table schema and verify it matches the required schema
   above. The most likely runtime failure is a schema mismatch between the
   Function insert and D1 table columns.

4. Check Cloudflare Pages Function logs for `interest storage error`. The
   Function logs storage type, error name, and error message, but returns only
   safe JSON to the browser:

   ```json
   {"ok":false,"error":"storage_error"}
   ```

5. Do not add live RAG, Ollama, Chroma, or private beta routes while debugging
   the public landing interest form.

## Custom Domain Plan

When ready to attach `steelguitarrag.com`:

1. Add `steelguitarrag.com` as a custom domain in the Cloudflare Pages project.
2. Let Cloudflare create or verify the required DNS record.
3. Keep the root domain pointed only at the static landing Pages project.
4. Do not point the root domain at any private beta app, tunnel, local machine, Ollama process, Chroma process, or RAG API.

## WWW Redirect Plan

Preferred public URL:

```text
https://steelguitarrag.com
```

Plan for `www.steelguitarrag.com`:

1. Add `www.steelguitarrag.com` as a Pages custom domain or Cloudflare DNS hostname.
2. Configure a Cloudflare redirect rule from:

   ```text
   https://www.steelguitarrag.com/*
   ```

   to:

   ```text
   https://steelguitarrag.com/$1
   ```

3. Use a permanent redirect only after the root domain has been verified.

## Rollback Plan

If a public deployment has a problem:

1. In Cloudflare Pages, open the project deployments list.
2. Select the previous known-good deployment.
3. Use Cloudflare Pages rollback/promote controls to restore it.
4. If the domain routing itself is wrong, temporarily remove the custom domain from the Pages project or point DNS back to the prior public target.
5. Keep the private beta app and RAG services separate so landing-page rollback never affects corpus, embeddings, Chroma, or answer logic.

## Pre-Deploy Checks

Run locally before creating a Pages deployment:

```bash
.venv/bin/python -m pytest
git diff --check
```

Optional static spot checks:

```bash
rg "/api/answer|Ollama|Chroma|steel-guitar-rag-mock|answer-client|mock-answer-data" deploy/landing
```

That search should return no matches for a public root deployment.
