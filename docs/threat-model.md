# Threat Model

Last reviewed: 2026-07-13

## Protected Assets

- Cloudflare Access, Tunnel, Worker, and administrator credentials.
- User identity and interest-list PII.
- Private/profile-backed lessons, transcripts, source metadata, and local
  environment values.
- Local Chroma/vector stores, corpus outputs, and Ollama prompts/responses.
- Availability of Chat, Explorer, Melody Studio, Lessons, and the digest job.
- Integrity of E9 positions, tabs, score events, source links, and deliveries.

## Trust Boundaries And Controls

| Boundary | Main threats | Current controls |
| --- | --- | --- |
| Internet to app | Anonymous use, forged identity, oversized bodies, abuse | Cloudflare Access plus application authorization before body parsing; production fail-closed auth; 1 MiB JSON cap; bounded rate state |
| Access JWT to role | Forged/expired token, wrong tenant/audience, key rotation | PyJWT/cryptography RS256 signature, issuer, audience, expiry; bounded JWKS cache and one refresh |
| App to retrieval/provider | Prompt injection, slow dependency, data leakage | Retrieved text treated as untrusted; deterministic guardrails; dependency timeouts; content concurrency; sanitized logs |
| Browser to source | Script/data URL injection, stale assets | HTTP(S)-only source links; CSP report-only; ETag/Last-Modified; immutable versioned assets |
| Public interest form to D1 | Spam, PII exposure, duplicate digest | Input limits; D1 storage; admin routes require Access/service identity plus secret; transactional digest claims and per-part state |
| Repository to deployment | Secrets or generated/private artifacts committed | Ignore rules, secret scan, asset budgets, exact-path staging, protected-path rules |
| Local host availability | Serialized requests, hung provider, unclean stop | Bounded threaded runtime, queue/concurrency limits, health probes, graceful shutdown, rotating logs |

## Deliberate Security Properties

- `/api/version` and health probes reveal no identity, feature, corpus, or
  provider configuration.
- `/api/session` does not retrieve content.
- Local role headers are development-only and cannot enable production access.
- Unauthorized and oversized requests are rejected before expensive work.
- The app, Chroma, and Ollama are not exposed through router port forwarding.
- Digest retry never resends a part already recorded as sent. Ambiguous sends
  require manual reconciliation.

## Residual Risks

- Cloudflare Access and the Mac mini remain availability dependencies.
- Rate limiting and JWKS caches are process-local, suitable for the current
  single-process protected preview but not a distributed quota service.
- CSP is report-only while compatibility is observed; violations must be
  reviewed before enforcing it.
- The retired 70 MB Explorer catalog remains tracked for history even though
  runtime code no longer requests it.
- The public interest form still needs ongoing abuse monitoring.
- A stolen administrator secret plus an accepted Access identity could reach
  digest administration; rotate either credential on suspected compromise.

## Response Priorities

1. Disable affected public ingress or administrative route.
2. Preserve logs and delivery state without copying private contents into
   tickets or handoffs.
3. Rotate exposed credentials through the owning platform.
4. Revert the smallest reviewed commit or Worker version.
5. Verify health, version, authorization failure, and authenticated browser
   behavior before restoring access.

See [recovery-procedure.md](recovery-procedure.md) for exact recovery flow.
