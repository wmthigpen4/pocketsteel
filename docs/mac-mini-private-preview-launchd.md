# Mac Mini Private Preview Launchd Runbook

This runbook keeps the Mac mini as the protected-preview origin. It does not move the app to a VPS, managed platform, laptop, or other host.

The target runtime remains:

```text
Internet -> Cloudflare Access -> Cloudflare Tunnel -> Mac mini app on 127.0.0.1:8770 -> local Chroma -> local Ollama
```

## Repo-Managed Files

- `deploy/macos/com.steelguitarrag.private-preview.plist.template`
- `deploy/macos/run-private-preview-app.sh`
- `deploy/macos/install-private-preview-launchdaemon.sh`

These files contain no Cloudflare Tunnel tokens, Cloudflare Access secrets, email allowlists, or private env values.

## Service Shape

The app service is designed as a system LaunchDaemon:

- Label: `com.steelguitarrag.private-preview`
- Bind host: `127.0.0.1`
- Default port: `8770`
- LaunchDaemon program: `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh`
- LaunchDaemon working directory: `/usr/local/libexec/steel-guitar-rag`
- App entrypoint from the wrapper: `.venv/bin/python scripts/serve_v2_rerank_smoke.py`
- Auth provider: `cloudflare_access`
- Answer auth mode: `production`
- Default Chroma path: `corpus-v2/vector-stores/chroma`
- Default Chroma collection: `steel_guitar_unified_v2`
- Durable logs:
  - `~/Library/Logs/steel-guitar-rag/app.out.log`
  - `~/Library/Logs/steel-guitar-rag/app.err.log`

The repo-managed wrapper is copied to `/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh` during `install`. The LaunchDaemon runs that installed copy instead of executing directly from `~/Documents/Steel Guitar RAG`; this avoids macOS launchd/TCC failures seen when a system daemon tries to execute a program or use a working directory under `~/Documents`.

The service wrapper reads `~/.steel-rag/env/private-preview.env` at runtime. That file must stay outside the repo and must not be pasted into handoffs, issues, prompts, shell history, or screenshots.

When `STEEL_RAG_SEMANTIC_ANSWER_ENABLED=true`, the wrapper loads
`OPENAI_API_KEY` into the server process from the current macOS user's
Keychain if the variable is not already present. The default generic-password
service is `pocket-steel-openai-api-key`; the account defaults to the runtime
user. The wrapper fails closed when semantic answers are enabled and that
credential cannot be read, and it never writes the credential to the env file
or command line. The optional `STEEL_RAG_OPENAI_KEYCHAIN_SERVICE` and
`STEEL_RAG_OPENAI_KEYCHAIN_ACCOUNT` settings select a reviewed alternate
Keychain item without containing the credential itself.

The installed private-preview wrapper enables Melody Studio and the tested
printed-score import path by default with:

```text
STEEL_RAG_ENABLE_MELODY_EXERCISE=true
STEEL_RAG_ENABLE_MELODY_IMPORT=true
STEEL_RAG_SCORE_OMR_PROVIDER=homr
```

The app-wide feature defaults remain off. The private-preview environment may
set either feature flag to `false` for rollback or select a different reviewed
OMR provider. When Homr is selected, the wrapper fails closed unless the
configured `HOMR_BIN` is executable.

## Install Or Update The App LaunchDaemon

From the repo root on the Mac mini:

```bash
deploy/macos/install-private-preview-launchdaemon.sh render > /tmp/com.steelguitarrag.private-preview.plist
plutil -lint /tmp/com.steelguitarrag.private-preview.plist
```

Review the rendered plist for paths only. Do not put secrets in the plist.

Install the daemon-safe wrapper copy, plist, and durable log directory:

```bash
deploy/macos/install-private-preview-launchdaemon.sh install
```

The default installed wrapper path is:

```text
/usr/local/libexec/steel-guitar-rag/run-private-preview-app.sh
```

The installed wrapper is root-owned and executable, while runtime env values stay in `~/.steel-rag/env/private-preview.env`.

Load it:

```bash
deploy/macos/install-private-preview-launchdaemon.sh load
```

Activate a clean detached release after reviewed code changes:

```bash
STEEL_RAG_REPO_DIR="$HOME/.steel-rag/releases/<short-sha>" \
STEEL_RAG_DATA_DIR="$HOME/Documents/Steel Guitar RAG" \
STEEL_RAG_EXPECTED_GIT_SHA=<full-sha> \
deploy/macos/install-private-preview-launchdaemon.sh activate
```

The dedicated release contains code only. `STEEL_RAG_DATA_DIR` points the
wrapper at existing local corpus/vector paths without copying or modifying
them. Activation rejects a branch checkout, tracked modifications, or a SHA
mismatch.

Restart the same installed release only with the exact release and SHA:

```bash
STEEL_RAG_REPO_DIR="$HOME/.steel-rag/releases/<short-sha>" \
STEEL_RAG_DATA_DIR="$HOME/Documents/Steel Guitar RAG" \
STEEL_RAG_EXPECTED_GIT_SHA=<full-sha> \
deploy/macos/install-private-preview-launchdaemon.sh restart
```

Do not kill the port listener to refresh the service. The runtime handles
SIGTERM gracefully, and a successful exit is not a safe implicit restart
contract. The hardened LaunchDaemon uses `KeepAlive=true`, while the installer
uses explicit launchctl operations followed by live, ready, and exact-version
verification.

Unload it for rollback:

```bash
deploy/macos/install-private-preview-launchdaemon.sh unload
```

The installer intentionally keeps privileged actions explicit. It uses `sudo` only for `/Library/LaunchDaemons`, launchctl system-domain operations, and log-directory ownership setup.

It also uses `sudo` to install the non-secret wrapper copy under `/usr/local/libexec/steel-guitar-rag`.

If launchd can execute the installed wrapper but the wrapper later fails to `cd` into `~/Documents/Steel Guitar RAG`, the remaining issue is the runtime checkout location rather than the wrapper. In that case, move or create an operator-approved runtime checkout outside TCC-sensitive folders, then reinstall with:

```bash
STEEL_RAG_REPO_DIR=/Users/cory/steel-guitar-rag-runtime \
deploy/macos/install-private-preview-launchdaemon.sh install
```

Do not copy private env files, Cloudflare tokens, Chroma/vector stores, private corpus, or generated artifacts into a new runtime path unless that exact data move is separately approved.

## Service Status And Logs

Check app service state:

```bash
deploy/macos/install-private-preview-launchdaemon.sh status
```

Tail app logs:

```bash
deploy/macos/install-private-preview-launchdaemon.sh tail
```

Check the local version endpoint:

```bash
deploy/macos/install-private-preview-launchdaemon.sh version
```

Expected shape:

```json
{"git_sha":"<current-head>","git_branch":"feature/answer-api","python_module":"steel_guitar_rag.api","auth_provider":"cloudflare_access"}
```

If `/api/version` does not report the expected commit, do not terminate the
listener. Confirm the configured detached release, then run the exact-SHA
`restart` command above.

## Cloudflare Tunnel Status

Cloudflare Tunnel should remain a boot-time system service on the same Mac mini. The observed service is:

```text
/Library/LaunchDaemons/com.cloudflare.cloudflared.plist
```

Check status without copying token-bearing plist contents:

```bash
sudo launchctl print system/com.cloudflare.cloudflared | grep -E 'state|pid|last exit|runs|path'
tail -n 100 /Library/Logs/com.cloudflare.cloudflared.err.log
tail -n 100 /Library/Logs/com.cloudflare.cloudflared.out.log
```

Do not paste raw `ProgramArguments`, raw `ps` output, or raw plist contents into docs, prompts, handoffs, or screenshots if they include a tunnel token.

Safer future token/config path:

- Prefer a named tunnel config file and Cloudflare credentials file stored outside the repo with root-only permissions.
- Keep any tunnel token or credentials under a private path such as `/etc/cloudflared/` or `/usr/local/etc/cloudflared/`.
- Keep the LaunchDaemon plist in the repo as a template only.
- Do not commit rendered tunnel config, token files, or credentials JSON.
- Rotate the existing inline token only as a separate Lane 11/Lane 12 security task.

## Power And Sleep Checks

The app can only behave like an appliance if the Mac remains awake and returns after power loss.

Read current settings:

```bash
pmset -g custom
pmset -g sched
sudo systemsetup -getrestartpowerfailure
fdesetup status
```

Recommended operator settings for AC-powered private preview:

```bash
sudo pmset -c sleep 0
sudo systemsetup -setrestartpowerfailure on
```

If FileVault is enabled later, unattended reboot may stop at pre-boot authentication before launchd can start the app or tunnel. FileVault was observed as off during the 2026-06-23 reliability audit.

## Ollama Runtime Check

If answer generation depends on local Ollama, verify whether it is available without an interactive login session:

```bash
launchctl list | grep -i ollama
curl -sS http://127.0.0.1:11434/api/tags
```

If Ollama is only user-session started, create a separate supervised boot plan before inviting outside testers. Do not expose `127.0.0.1:11434` through Cloudflare Tunnel and do not add router port forwarding.

## Protected-Preview Smoke After Service Changes

After loading or restarting the LaunchDaemon, run protected-preview browser smoke against the real Cloudflare URL:

```text
https://app.steelguitarrag.com/ui/steel-guitar-rag-mock.html?v=<commit-or-slice>
```

Smoke Target block to record:

```text
Smoke Target:
- Target type: protected-preview
- Result type: browser smoke
- Exact browser URL tested:
- Cache-busted URL tested:
- Exact URL the user should use:
- Auth required: yes
- Auth provider: Cloudflare Access
- Cloudflare Access login result:
- Local backend URL: http://127.0.0.1:8770
- Expected backend port: 8770
- Expected git HEAD:
- Version endpoint: /api/version
- Version endpoint result:
- Whether app root `/` works:
- Whether `/ui/steel-guitar-rag-mock.html` works:
- API fallback status:
```

Minimum prompts:

- `Show me a G major grip.`
- `Show me a 4-5-6 grip.`
- `Where is G on E9?`
- `Show me a G to C move.`
- `How do I use A+B pedals?`
- `Show me an E-lower move.`
- `Give me a beginner lick in G.`
- `Give me the full tab for a modern copyrighted song.`
- `Tab the whole solo from Together Again.`
- `Transcribe this YouTube recording into tab.`
- `What are good Fender Steel King settings?`
- `Why does my amp buzz at idle?`

Expected behavior:

- Static grip prompts are fretboard-first and do not show tab by default.
- Movement prompts may show deterministic tab plus matching fretboard.
- Copyright/transcription prompts do not generate full-song tab, solo transcription, or recording transcription.
- Gear prompts do not show stale tab/fretboard payload.
- No raw `[object Object]`.
- No relevant browser console errors.
- Q&A unlocks after Cloudflare Access login.

## Rollback

Unload the app LaunchDaemon:

```bash
deploy/macos/install-private-preview-launchdaemon.sh unload
```

If necessary, return to the current manual screen process while debugging:

```bash
cd ~/Documents/Steel\ Guitar\ RAG
source .venv/bin/activate
set -a
source ~/.steel-rag/env/private-preview.env
set +a

PYTHONPATH=. \
STEEL_RAG_AUTH_PROVIDER=cloudflare_access \
STEEL_RAG_ANSWER_AUTH_MODE=production \
STEEL_RAG_RETRIEVAL_MODE=hybrid_private_first \
STEEL_RAG_ENABLE_PRIVATE_SOURCES=true \
STEEL_RAG_CHROMA_PATH=corpus-v2/vector-stores/chroma \
STEEL_RAG_CHROMA_COLLECTION=steel_guitar_unified_v2 \
STEEL_RAG_PRIVATE_CHROMA_PATH=corpus-private/vector-stores/chroma \
STEEL_RAG_PRIVATE_CHROMA_COLLECTION=steel_guitar_private_sources_v1 \
STEEL_RAG_RETRIEVAL_DEBUG=false \
.venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host 127.0.0.1 \
  --port 8770 \
  --answer-auth-mode production \
  --auth-provider cloudflare-access
```

Rollback does not require DNS, Cloudflare Access policy, Chroma, embedding, corpus, or Cloudflare Tunnel changes.
