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

## Cloudflare Pages Setup

1. In Cloudflare Pages, create a new project connected to the GitHub repository.
2. Select the branch intended for preview or production deployment.
3. Use no build command for the static landing page.
4. Set the output directory to:

   ```text
   deploy/landing
   ```

5. Deploy the Pages preview and verify:
   - `index.html` loads as the root page.
   - Logo and stage background assets load from `/assets/`.
   - There are no calls to `/api/answer`.
   - The early-access CTAs point to the interest form, not to the private app.
   - `POST /api/interest` returns success for a valid email.

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
  submitted_at text not null,
  name text,
  email text not null,
  player_level text,
  interests_json text not null,
  message text,
  turnstile_token_present integer not null default 0,
  user_agent text,
  cf_ray text
);
```

Alternative storage binding:

```text
STEEL_RAG_INTEREST_KV
```

If neither binding is configured, the endpoint returns success with `stored: false`. This keeps local/dev previews from failing loudly, but production should configure one binding before collecting real interest.

## Viewing or Exporting Submissions

For D1, query or export rows from Cloudflare:

```bash
wrangler d1 execute <database-name> --command "select submitted_at, email, name, player_level, interests_json from interest_submissions order by submitted_at desc limit 50;"
```

For KV, list keys with the `interest:` prefix, then read values:

```bash
wrangler kv key list --binding STEEL_RAG_INTEREST_KV --prefix interest:
```

Email routing for `hello@steelguitarrag.com` should be configured separately in Cloudflare Email Routing or another mail provider. The interest form does not send email yet.

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
