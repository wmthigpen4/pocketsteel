#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

STEEL_RAG_LABEL="${STEEL_RAG_LABEL:-com.steelguitarrag.private-preview}"
STEEL_RAG_REPO_DIR="${STEEL_RAG_REPO_DIR:-$DEFAULT_REPO_DIR}"
STEEL_RAG_RUN_AS_USER="${STEEL_RAG_RUN_AS_USER:-$(id -un)}"
STEEL_RAG_RUN_AS_GROUP="${STEEL_RAG_RUN_AS_GROUP:-$(id -gn "$STEEL_RAG_RUN_AS_USER" 2>/dev/null || id -gn)}"

user_home() {
  dscl . -read "/Users/$STEEL_RAG_RUN_AS_USER" NFSHomeDirectory 2>/dev/null | awk '{print $2}'
}

STEEL_RAG_USER_HOME="${STEEL_RAG_USER_HOME:-$(user_home)}"
if [[ -z "$STEEL_RAG_USER_HOME" ]]; then
  STEEL_RAG_USER_HOME="$HOME"
fi

STEEL_RAG_ENV_FILE="${STEEL_RAG_ENV_FILE:-$STEEL_RAG_USER_HOME/.steel-rag/env/private-preview.env}"
STEEL_RAG_LOG_DIR="${STEEL_RAG_LOG_DIR:-$STEEL_RAG_USER_HOME/Library/Logs/steel-guitar-rag}"
STEEL_RAG_HOST="${STEEL_RAG_HOST:-127.0.0.1}"
STEEL_RAG_PORT="${STEEL_RAG_PORT:-8770}"
STEEL_RAG_PLIST_PATH="${STEEL_RAG_PLIST_PATH:-/Library/LaunchDaemons/$STEEL_RAG_LABEL.plist}"
TEMPLATE_PATH="$SCRIPT_DIR/com.steelguitarrag.private-preview.plist.template"
WRAPPER_PATH="$STEEL_RAG_REPO_DIR/deploy/macos/run-private-preview-app.sh"

usage() {
  cat <<USAGE
Usage: $0 <command>

Commands:
  render    Render the LaunchDaemon plist to stdout.
  install   Render, lint, and install the plist to /Library/LaunchDaemons. Requires sudo.
  load      Bootstrap the installed LaunchDaemon. Requires sudo.
  unload    Boot out the LaunchDaemon. Requires sudo.
  restart   Restart the loaded LaunchDaemon. Requires sudo.
  status    Print launchctl status for the LaunchDaemon. Requires sudo.
  tail      Tail durable app stdout/stderr logs.
  version   Curl local /api/version on the configured loopback port.

Environment overrides:
  STEEL_RAG_REPO_DIR=$STEEL_RAG_REPO_DIR
  STEEL_RAG_RUN_AS_USER=$STEEL_RAG_RUN_AS_USER
  STEEL_RAG_ENV_FILE=$STEEL_RAG_ENV_FILE
  STEEL_RAG_LOG_DIR=$STEEL_RAG_LOG_DIR
  STEEL_RAG_HOST=$STEEL_RAG_HOST
  STEEL_RAG_PORT=$STEEL_RAG_PORT
  STEEL_RAG_PLIST_PATH=$STEEL_RAG_PLIST_PATH
USAGE
}

require_host_config() {
  [[ -d "$STEEL_RAG_REPO_DIR" ]] || {
    printf 'Missing repo directory: %s\n' "$STEEL_RAG_REPO_DIR" >&2
    exit 1
  }
  [[ -f "$TEMPLATE_PATH" ]] || {
    printf 'Missing plist template: %s\n' "$TEMPLATE_PATH" >&2
    exit 1
  }
  [[ -x "$WRAPPER_PATH" ]] || {
    printf 'Missing executable wrapper: %s\n' "$WRAPPER_PATH" >&2
    exit 1
  }
  if [[ "$STEEL_RAG_HOST" != "127.0.0.1" ]]; then
    printf 'Refusing non-loopback host for private preview: %s\n' "$STEEL_RAG_HOST" >&2
    exit 1
  fi
}

render_plist() {
  require_host_config
  STEEL_RAG_LABEL="$STEEL_RAG_LABEL" \
  STEEL_RAG_REPO_DIR="$STEEL_RAG_REPO_DIR" \
  STEEL_RAG_RUN_AS_USER="$STEEL_RAG_RUN_AS_USER" \
  STEEL_RAG_RUN_AS_GROUP="$STEEL_RAG_RUN_AS_GROUP" \
  STEEL_RAG_ENV_FILE="$STEEL_RAG_ENV_FILE" \
  STEEL_RAG_LOG_DIR="$STEEL_RAG_LOG_DIR" \
  STEEL_RAG_HOST="$STEEL_RAG_HOST" \
  STEEL_RAG_PORT="$STEEL_RAG_PORT" \
  python3 - "$TEMPLATE_PATH" <<'PY'
import os
import sys
from pathlib import Path

template = Path(sys.argv[1]).read_text(encoding="utf-8")
replacements = {
    "__STEEL_RAG_LABEL__": os.environ["STEEL_RAG_LABEL"],
    "__STEEL_RAG_REPO_DIR__": os.environ["STEEL_RAG_REPO_DIR"],
    "__STEEL_RAG_RUN_AS_USER__": os.environ["STEEL_RAG_RUN_AS_USER"],
    "__STEEL_RAG_RUN_AS_GROUP__": os.environ["STEEL_RAG_RUN_AS_GROUP"],
    "__STEEL_RAG_ENV_FILE__": os.environ["STEEL_RAG_ENV_FILE"],
    "__STEEL_RAG_LOG_DIR__": os.environ["STEEL_RAG_LOG_DIR"],
    "__STEEL_RAG_HOST__": os.environ["STEEL_RAG_HOST"],
    "__STEEL_RAG_PORT__": os.environ["STEEL_RAG_PORT"],
}
for old, new in replacements.items():
    template = template.replace(old, new)
sys.stdout.write(template)
PY
}

install_plist() {
  require_host_config
  local tmp
  tmp="$(mktemp "/tmp/$STEEL_RAG_LABEL.XXXXXX.plist")"
  render_plist > "$tmp"
  plutil -lint "$tmp"
  if [[ ! -r "$STEEL_RAG_ENV_FILE" ]]; then
    printf 'Warning: env file is not readable yet: %s\n' "$STEEL_RAG_ENV_FILE" >&2
  fi
  sudo install -d -o "$STEEL_RAG_RUN_AS_USER" -g "$STEEL_RAG_RUN_AS_GROUP" -m 0755 "$STEEL_RAG_LOG_DIR"
  sudo install -o root -g wheel -m 0644 "$tmp" "$STEEL_RAG_PLIST_PATH"
  rm -f "$tmp"
  printf 'Installed %s\n' "$STEEL_RAG_PLIST_PATH"
  printf 'Next: %s load\n' "$0"
}

case "${1:-}" in
  render)
    render_plist
    ;;
  install)
    install_plist
    ;;
  load)
    sudo launchctl bootstrap system "$STEEL_RAG_PLIST_PATH"
    ;;
  unload)
    sudo launchctl bootout system "$STEEL_RAG_PLIST_PATH"
    ;;
  restart)
    sudo launchctl kickstart -k "system/$STEEL_RAG_LABEL"
    ;;
  status)
    sudo launchctl print "system/$STEEL_RAG_LABEL"
    ;;
  tail)
    tail -n 100 -f "$STEEL_RAG_LOG_DIR/app.out.log" "$STEEL_RAG_LOG_DIR/app.err.log"
    ;;
  version)
    curl -sS "http://$STEEL_RAG_HOST:$STEEL_RAG_PORT/api/version"
    ;;
  -h|--help|help|"")
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
