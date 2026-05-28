# Cloudflare Pages Landing Deployment

This document describes how to deploy the static public landing page for `steelguitarrag.com`.

Do not connect the public root site to live RAG, Ollama, Chroma, private corpus files, or the beta app until the access model is ready.

## Static Output

- Source page: `ui/steel-guitar-rag-landing.html`
- Cloudflare Pages output directory: `deploy/landing`
- Public root file: `deploy/landing/index.html`
- Required assets: `deploy/landing/assets/`

The output directory is intentionally static. It should not include `/api/answer`, backend code, embeddings, indexes, raw corpus files, private transcripts, or local environment files.

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
   - The Backstage Pass CTA points to the beta note, not to the private app.

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
