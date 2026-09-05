# Environments

The authoritative product, branch, CI, runtime, hostname, and local-release
inventory is [docs/current-state-inventory.md](docs/current-state-inventory.md).

The sanctioned protected-application promotion path is:

```text
local -> test.steelguitarrag.com -> app.steelguitarrag.com
```

The public `steelguitarrag.com` Pages site and dedicated Travis preview are
separate deployable surfaces. Observe `AGENTS.md` and
`docs/platform-architecture.md` before changing any environment.
