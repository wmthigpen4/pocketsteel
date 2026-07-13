# The Turnaround — Current Architecture

Last verified: 2026-07-13

This is the canonical current architecture. Older phase, switch, deployment,
and cleanup plans are historical inputs, not operating instructions.

## Product Surfaces

One protected application exposes four workspaces:

- Chat: source-aware steel-guitar questions and deterministic teaching answers.
- Fretboard Explorer: validated standard-E9 positions loaded from versioned,
  lazy static chunks.
- Melody Studio: melody/score input, standard-E9 arranging, synchronized staff,
  fretboard, tablature, playback, and printing.
- Lessons: structured lesson navigation and practice content.

The public landing page is a separate Cloudflare Pages surface. It does not
host the private application or expose retrieval endpoints.

## Runtime Topology

```text
Browser
  -> Cloudflare Access
  -> Cloudflare Tunnel
  -> Mac mini LaunchDaemon on 127.0.0.1:8770
  -> bounded threaded WSGI runtime
       -> deterministic E9/lesson/arranger services
       -> local Chroma retrieval
       -> local Ollama answer provider
```

Ollama, Chroma, private corpus data, and environment values remain local. They
must not receive direct public ingress.

The runtime has one process, one retrieval-model instance, bounded request and
content concurrency, dependency timeouts, graceful shutdown, rotating logs,
and minimal liveness/readiness endpoints. Static files are streamed with
compression, validators, and cache policy.

## Trust Boundaries

- Cloudflare Access is the public identity gateway.
- Application authorization is still mandatory. Every content-bearing API
  route authorizes before reading its request body or starting expensive work.
- Production construction fails closed unless `cloudflare_access` is selected
  explicitly.
- `/api/version`, `/health/live`, and `/health/ready` expose only minimal
  operational state.
- `/api/session` is the authenticated identity/feature probe.
- Normal JSON requests are capped at 1 MiB. Import routes keep their narrower
  feature-specific limits.
- Clickable source references are limited to HTTP(S).

Cloudflare Access JWTs are verified with PyJWT/cryptography using RS256,
signature, issuer, audience, expiry, and bounded JWKS caching with one rotation
refresh.

## Static Data

Explorer data is published as `ui/explorer-data-v1/manifest.json` plus
content-hashed compressed chunks. The normal page load never requests the
retired 70 MB JavaScript catalog. Existing browser data objects remain the
compatibility contract after a chunk loads.

## Interest Digest

The public interest form writes to D1. A separately deployed scheduled Worker
claims digest windows transactionally and records delivery parts, hashes,
attempts, sent timestamps, and errors. Retries select only unsent parts.
PII-bearing administrative routes require both Cloudflare Access/service
identity and the existing administrator token.

## Build And Quality Boundaries

- Python 3.12 environments are hash-locked under `requirements/` for runtime,
  RAG, test, and deployment use.
- Node 24 tooling is pinned by `package-lock.json`.
- CI runs full pytest, JavaScript syntax, Worker-runtime tests, lint/type
  checks, dependency audits, secret-pattern scanning, lock checks, and asset
  budgets.
- Public contracts remain exported from their established modules while
  internal CLI, contract, model, browser-config, and browser-style services
  live behind smaller module boundaries.

## Canonical Operations

- [Private preview operations](private-preview-operations.md)
- [Verified commands](current-commands.md)
- [Threat model](threat-model.md)
- [Recovery procedure](recovery-procedure.md)
- [Current integration snapshot](handoffs/task-completions/integration-status.md)
