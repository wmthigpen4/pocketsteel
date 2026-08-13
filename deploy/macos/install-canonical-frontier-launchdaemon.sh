#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

STEEL_RAG_CANONICAL_FRONTIER_LABEL="${STEEL_RAG_CANONICAL_FRONTIER_LABEL:-com.steelguitarrag.canonical-frontier}"
STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT="${STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT:-}"
STEEL_RAG_CANONICAL_FRONTIER_PYTHON="${STEEL_RAG_CANONICAL_FRONTIER_PYTHON:-}"
STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE="${STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE:-}"
STEEL_RAG_CANONICAL_FRONTIER_LOG_DIR="${STEEL_RAG_CANONICAL_FRONTIER_LOG_DIR:-}"
STEEL_RAG_CANONICAL_FRONTIER_HOST="${STEEL_RAG_CANONICAL_FRONTIER_HOST:-127.0.0.1}"
STEEL_RAG_CANONICAL_FRONTIER_PORT="${STEEL_RAG_CANONICAL_FRONTIER_PORT:-8771}"
STEEL_RAG_CANONICAL_FRONTIER_RUN_AS_USER="${STEEL_RAG_CANONICAL_FRONTIER_RUN_AS_USER:-$(id -un)}"
STEEL_RAG_CANONICAL_FRONTIER_RUN_AS_GROUP="${STEEL_RAG_CANONICAL_FRONTIER_RUN_AS_GROUP:-$(id -gn)}"
STEEL_RAG_CANONICAL_FRONTIER_INSTALL_DIR="${STEEL_RAG_CANONICAL_FRONTIER_INSTALL_DIR:-/usr/local/libexec/steel-guitar-rag/canonical-frontier}"
STEEL_RAG_CANONICAL_FRONTIER_RUNTIME_DIR="${STEEL_RAG_CANONICAL_FRONTIER_RUNTIME_DIR:-}"
STEEL_RAG_CANONICAL_FRONTIER_PLIST_PATH="${STEEL_RAG_CANONICAL_FRONTIER_PLIST_PATH:-/Library/LaunchDaemons/$STEEL_RAG_CANONICAL_FRONTIER_LABEL.plist}"
STEEL_RAG_CANONICAL_FRONTIER_WRAPPER="${STEEL_RAG_CANONICAL_FRONTIER_WRAPPER:-$STEEL_RAG_CANONICAL_FRONTIER_INSTALL_DIR/run-canonical-frontier-service.sh}"
STEEL_RAG_CANONICAL_FRONTIER_VERIFIER="${STEEL_RAG_CANONICAL_FRONTIER_VERIFIER:-$STEEL_RAG_CANONICAL_FRONTIER_INSTALL_DIR/verify_canonical_frontier_service.py}"
STEEL_RAG_CANONICAL_FRONTIER_MANIFEST="${STEEL_RAG_CANONICAL_FRONTIER_MANIFEST:-$STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT/canonical-frontier-service-bundle-v1035.json}"
STEEL_RAG_CANONICAL_FRONTIER_HEALTH_TIMEOUT_SECONDS="${STEEL_RAG_CANONICAL_FRONTIER_HEALTH_TIMEOUT_SECONDS:-120}"

TEMPLATE_SOURCE="$SCRIPT_DIR/com.steelguitarrag.canonical-frontier.plist.template"
WRAPPER_SOURCE="$SCRIPT_DIR/run-canonical-frontier-service.sh"
VERIFIER_SOURCE="$REPO_DIR/scripts/verify_canonical_frontier_service.py"

fail() {
  printf 'canonical-frontier LaunchDaemon: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<'USAGE'
Usage: install-canonical-frontier-launchdaemon.sh <command>

Commands:
  render      Render the LaunchDaemon plist to stdout without changing state.
  preflight   Verify bundle, configuration, token presence, shell, and plist.
  install     Install verified wrapper, verifier, manifest, log dir, and plist.
  load        Bootstrap the installed service in the system launchd domain.
  unload      Boot out the installed service from the system launchd domain.
  verify      Verify loopback live/ready endpoints and unauthorized rejection.
  status      Print the launchd service status.
  tail        Tail the service's durable stdout and stderr logs.

install, load, and unload mutate protected-preview host state and require
separate explicit authorization. render, preflight, verify, and status are
read-only.
USAGE
}

require_configuration() {
  [[ -d "$STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT" ]] || fail "service root is required and must exist"
  [[ -x "$STEEL_RAG_CANONICAL_FRONTIER_PYTHON" ]] || fail "an executable service Python is required"
  [[ -n "$STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE" ]] || fail "an explicit protected environment file is required"
  [[ -r "$STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE" ]] || fail "protected environment file is missing"
  [[ -n "$STEEL_RAG_CANONICAL_FRONTIER_LOG_DIR" ]] || fail "an explicit service log directory is required"
  [[ "$STEEL_RAG_CANONICAL_FRONTIER_RUNTIME_DIR" == /* ]] || fail "an absolute runtime state directory is required"
  [[ -r "$TEMPLATE_SOURCE" ]] || fail "plist template is missing"
  [[ -x "$WRAPPER_SOURCE" ]] || fail "service wrapper is missing or not executable"
  [[ -x "$VERIFIER_SOURCE" ]] || fail "bundle verifier is missing or not executable"
  [[ -r "$STEEL_RAG_CANONICAL_FRONTIER_MANIFEST" ]] || fail "bundle manifest is missing"
  [[ "$STEEL_RAG_CANONICAL_FRONTIER_HOST" == "127.0.0.1" ]] || fail "non-loopback binding is prohibited"
  [[ "$STEEL_RAG_CANONICAL_FRONTIER_PORT" =~ ^[0-9]+$ ]] || fail "port must be numeric"
  [[ "$STEEL_RAG_CANONICAL_FRONTIER_HEALTH_TIMEOUT_SECONDS" =~ ^[1-9][0-9]*$ ]] || fail "health timeout must be a positive integer"
}

token_is_present() {
  STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE="$STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE" bash -c '
    set -euo pipefail
    set -a
    source "$STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE"
    set +a
    [[ -n "${STEEL_RAG_CANONICAL_FRONTIER_TOKEN:-}" ]]
  '
}

render_plist() {
  require_configuration
  STEEL_RAG_CANONICAL_FRONTIER_TEMPLATE="$TEMPLATE_SOURCE" \
  STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT="$STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT" \
  STEEL_RAG_CANONICAL_FRONTIER_MANIFEST="$STEEL_RAG_CANONICAL_FRONTIER_MANIFEST" \
  STEEL_RAG_CANONICAL_FRONTIER_PYTHON="$STEEL_RAG_CANONICAL_FRONTIER_PYTHON" \
  STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE="$STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE" \
  STEEL_RAG_CANONICAL_FRONTIER_VERIFIER="$STEEL_RAG_CANONICAL_FRONTIER_VERIFIER" \
  STEEL_RAG_CANONICAL_FRONTIER_RUNTIME_DIR="$STEEL_RAG_CANONICAL_FRONTIER_RUNTIME_DIR" \
  STEEL_RAG_CANONICAL_FRONTIER_WRAPPER="$STEEL_RAG_CANONICAL_FRONTIER_WRAPPER" \
  STEEL_RAG_CANONICAL_FRONTIER_LOG_DIR="$STEEL_RAG_CANONICAL_FRONTIER_LOG_DIR" \
  STEEL_RAG_CANONICAL_FRONTIER_RUN_AS_USER="$STEEL_RAG_CANONICAL_FRONTIER_RUN_AS_USER" \
  STEEL_RAG_CANONICAL_FRONTIER_RUN_AS_GROUP="$STEEL_RAG_CANONICAL_FRONTIER_RUN_AS_GROUP" \
  python3 - <<'PY'
import os
from pathlib import Path
from xml.sax.saxutils import escape

template = Path(os.environ["STEEL_RAG_CANONICAL_FRONTIER_TEMPLATE"]).read_text(encoding="utf-8")
replacements = {
    "__STEEL_RAG_RUN_AS_USER__": os.environ["STEEL_RAG_CANONICAL_FRONTIER_RUN_AS_USER"],
    "__STEEL_RAG_RUN_AS_GROUP__": os.environ["STEEL_RAG_CANONICAL_FRONTIER_RUN_AS_GROUP"],
    "__STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT__": os.environ["STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT"],
    "__STEEL_RAG_CANONICAL_FRONTIER_MANIFEST__": os.environ["STEEL_RAG_CANONICAL_FRONTIER_MANIFEST"],
    "__STEEL_RAG_CANONICAL_FRONTIER_PYTHON__": os.environ["STEEL_RAG_CANONICAL_FRONTIER_PYTHON"],
    "__STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE__": os.environ["STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE"],
    "__STEEL_RAG_CANONICAL_FRONTIER_VERIFIER__": os.environ["STEEL_RAG_CANONICAL_FRONTIER_VERIFIER"],
    "__STEEL_RAG_CANONICAL_FRONTIER_RUNTIME_DIR__": os.environ["STEEL_RAG_CANONICAL_FRONTIER_RUNTIME_DIR"],
    "__STEEL_RAG_CANONICAL_FRONTIER_WRAPPER__": os.environ["STEEL_RAG_CANONICAL_FRONTIER_WRAPPER"],
    "__STEEL_RAG_CANONICAL_FRONTIER_LOG_DIR__": os.environ["STEEL_RAG_CANONICAL_FRONTIER_LOG_DIR"],
}
for placeholder, value in replacements.items():
    template = template.replace(placeholder, escape(value))
if "__STEEL_RAG_" in template:
    raise SystemExit("Rendered plist contains an unresolved placeholder.")
print(template, end="")
PY
}

preflight() {
  require_configuration
  token_is_present || fail "service bearer token is absent from the protected environment"
  bash -n "$WRAPPER_SOURCE"
  "$STEEL_RAG_CANONICAL_FRONTIER_PYTHON" "$VERIFIER_SOURCE" \
    --service-root "$STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT" \
    --manifest "$STEEL_RAG_CANONICAL_FRONTIER_MANIFEST" >/dev/null
  local temporary_plist
  temporary_plist="$(mktemp "/tmp/$STEEL_RAG_CANONICAL_FRONTIER_LABEL.preflight.XXXXXX")"
  render_plist > "$temporary_plist"
  plutil -lint "$temporary_plist" >/dev/null
  rm -f "$temporary_plist"
  printf 'Canonical-frontier preflight passed: bundle v1035, loopback %s, no state changed.\n' "$STEEL_RAG_CANONICAL_FRONTIER_PORT"
}

install_service() {
  preflight
  local temporary_plist
  temporary_plist="$(mktemp "/tmp/$STEEL_RAG_CANONICAL_FRONTIER_LABEL.install.XXXXXX")"
  render_plist > "$temporary_plist"
  plutil -lint "$temporary_plist" >/dev/null
  sudo install -d -o root -g wheel -m 0755 "$STEEL_RAG_CANONICAL_FRONTIER_INSTALL_DIR"
  sudo install -o root -g wheel -m 0755 "$WRAPPER_SOURCE" "$STEEL_RAG_CANONICAL_FRONTIER_WRAPPER"
  sudo install -o root -g wheel -m 0755 "$VERIFIER_SOURCE" "$STEEL_RAG_CANONICAL_FRONTIER_VERIFIER"
  sudo install -d -o "$STEEL_RAG_CANONICAL_FRONTIER_RUN_AS_USER" -g "$STEEL_RAG_CANONICAL_FRONTIER_RUN_AS_GROUP" -m 0755 "$STEEL_RAG_CANONICAL_FRONTIER_LOG_DIR"
  sudo install -o root -g wheel -m 0644 "$temporary_plist" "$STEEL_RAG_CANONICAL_FRONTIER_PLIST_PATH"
  rm -f "$temporary_plist"
  printf 'Installed canonical-frontier files without loading the service.\n'
}

load_service() {
  [[ -r "$STEEL_RAG_CANONICAL_FRONTIER_PLIST_PATH" ]] || fail "installed plist is missing"
  sudo launchctl bootstrap system "$STEEL_RAG_CANONICAL_FRONTIER_PLIST_PATH"
}

unload_service() {
  sudo launchctl bootout "system/$STEEL_RAG_CANONICAL_FRONTIER_LABEL"
}

verify_service() {
  require_configuration
  local deadline live ready ready_body unauthorized_code
  deadline=$((SECONDS + STEEL_RAG_CANONICAL_FRONTIER_HEALTH_TIMEOUT_SECONDS))
  live="http://127.0.0.1:$STEEL_RAG_CANONICAL_FRONTIER_PORT/health/live"
  ready="http://127.0.0.1:$STEEL_RAG_CANONICAL_FRONTIER_PORT/health/ready"
  until curl --silent --show-error --fail --max-time 3 "$live" >/dev/null 2>&1 \
    && ready_body="$(curl --silent --show-error --fail --max-time 3 "$ready" 2>/dev/null)" \
    && [[ "$(printf '%s' "$ready_body" | python3 -c 'import json,sys; print((json.load(sys.stdin) or {}).get("status", ""))')" == "ready" ]]; do
    (( SECONDS < deadline )) || fail "service health verification timed out"
    sleep 1
  done
  unauthorized_code="$(curl --silent --output /dev/null --write-out '%{http_code}' \
    --max-time 3 --request POST --header 'Content-Type: application/json' \
    --data '{"schema_version":1,"question":"health check"}' \
    "http://127.0.0.1:$STEEL_RAG_CANONICAL_FRONTIER_PORT/v1/answer")"
  [[ "$unauthorized_code" == "401" ]] || fail "unauthorized answer request was not rejected"
  printf 'Canonical-frontier loopback health and unauthorized rejection passed.\n'
}

command="${1:-}"
case "$command" in
  render) render_plist ;;
  preflight) preflight ;;
  install) install_service ;;
  load) load_service ;;
  unload) unload_service ;;
  verify) verify_service ;;
  status) launchctl print "system/$STEEL_RAG_CANONICAL_FRONTIER_LABEL" ;;
  tail) tail -n 100 -f "$STEEL_RAG_CANONICAL_FRONTIER_LOG_DIR/service.out.log" "$STEEL_RAG_CANONICAL_FRONTIER_LOG_DIR/service.err.log" ;;
  *) usage; exit 2 ;;
esac
