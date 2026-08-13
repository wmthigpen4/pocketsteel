#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

STEEL_RAG_LABEL="${STEEL_RAG_LABEL:-com.steelguitarrag.private-preview}"
STEEL_RAG_REPO_DIR="${STEEL_RAG_REPO_DIR:-}"
STEEL_RAG_DATA_DIR="${STEEL_RAG_DATA_DIR:-}"
STEEL_RAG_ENV_FILE="${STEEL_RAG_ENV_FILE:-$HOME/.steel-rag/env/private-preview.env}"
STEEL_RAG_LOG_DIR="${STEEL_RAG_LOG_DIR:-$HOME/Library/Logs/steel-guitar-rag}"
STEEL_RAG_HOST="${STEEL_RAG_HOST:-127.0.0.1}"
STEEL_RAG_PORT="${STEEL_RAG_PORT:-8770}"
STEEL_RAG_EXPECTED_GIT_SHA="${STEEL_RAG_EXPECTED_GIT_SHA:-}"
STEEL_RAG_HEALTH_TIMEOUT_SECONDS="${STEEL_RAG_HEALTH_TIMEOUT_SECONDS:-90}"
STEEL_RAG_INSTALL_DIR="${STEEL_RAG_INSTALL_DIR:-$HOME/.steel-rag/supervisors/private-preview}"
STEEL_RAG_WRAPPER_PATH="${STEEL_RAG_WRAPPER_PATH:-$STEEL_RAG_INSTALL_DIR/run-private-preview-app.sh}"
STEEL_RAG_WORKING_DIR="${STEEL_RAG_WORKING_DIR:-$STEEL_RAG_INSTALL_DIR}"
STEEL_RAG_PLIST_PATH="${STEEL_RAG_PLIST_PATH:-$HOME/Library/LaunchAgents/$STEEL_RAG_LABEL.plist}"
STEEL_RAG_LAUNCHCTL_BIN="${STEEL_RAG_LAUNCHCTL_BIN:-launchctl}"
STEEL_RAG_LSOF_BIN="${STEEL_RAG_LSOF_BIN:-lsof}"
STEEL_RAG_DOMAIN="${STEEL_RAG_DOMAIN:-gui/$(id -u)}"

TEMPLATE_SOURCE="$SCRIPT_DIR/com.steelguitarrag.private-preview.launchagent.plist.template"
WRAPPER_SOURCE="$SCRIPT_DIR/run-private-preview-app.sh"
SUPERVISION_DIAGNOSTIC="not checked"

fail() {
  printf 'private-preview LaunchAgent: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<'USAGE'
Usage: install-private-preview-launchagent.sh <command>

Commands:
  render             Render the user LaunchAgent plist without changing state.
  preflight          Verify the exact release, configuration, wrapper, and plist.
  install            Install the wrapper and plist without loading the service.
  load               Bootstrap the service in the current user's GUI domain.
  unload             Boot the service out of the current user's GUI domain.
  restart            Restart the loaded service and verify exact health.
  verify             Verify live, ready, and exact version endpoints.
  verify-supervised  Verify health, user-domain supervision, and listener ownership.
  status             Print the user-domain launchd service status.

This supervisor does not use sudo. The one-time retirement of any old system
LaunchDaemon is deliberately outside this installer.
USAGE
}

git_release() {
  git -c "safe.directory=$STEEL_RAG_REPO_DIR" -C "$STEEL_RAG_REPO_DIR" "$@"
}

release_sha() {
  git_release rev-parse HEAD 2>/dev/null
}

require_configuration() {
  [[ -d "$STEEL_RAG_REPO_DIR" ]] || fail "an explicit release directory is required"
  [[ -d "$STEEL_RAG_DATA_DIR" ]] || fail "an explicit data directory is required"
  [[ -r "$STEEL_RAG_ENV_FILE" ]] || fail "protected environment file is missing"
  [[ -n "$STEEL_RAG_LOG_DIR" ]] || fail "an explicit log directory is required"
  [[ -n "$STEEL_RAG_INSTALL_DIR" ]] || fail "an explicit supervisor install directory is required"
  [[ -n "$STEEL_RAG_PLIST_PATH" ]] || fail "an explicit LaunchAgent plist path is required"
  [[ -r "$TEMPLATE_SOURCE" ]] || fail "LaunchAgent template is missing"
  [[ -x "$WRAPPER_SOURCE" ]] || fail "app wrapper is missing or not executable"
  [[ -x "$STEEL_RAG_REPO_DIR/.venv/bin/python" ]] || fail "release Python is missing"
  [[ "$STEEL_RAG_HOST" == "127.0.0.1" ]] || fail "non-loopback binding is prohibited"
  [[ "$STEEL_RAG_PORT" =~ ^[0-9]+$ ]] || fail "port must be numeric"
  [[ "$STEEL_RAG_HEALTH_TIMEOUT_SECONDS" =~ ^[1-9][0-9]*$ ]] || fail "health timeout must be a positive integer"
}

require_exact_release() {
  require_configuration
  [[ -n "$STEEL_RAG_EXPECTED_GIT_SHA" ]] || fail "STEEL_RAG_EXPECTED_GIT_SHA is required"
  local actual expected
  actual="$(release_sha)" || fail "release directory is not a Git checkout"
  expected="$(git_release rev-parse "${STEEL_RAG_EXPECTED_GIT_SHA}^{commit}" 2>/dev/null)" || fail "expected release commit is unavailable"
  [[ "$actual" == "$expected" ]] || fail "release mismatch: expected $expected but checkout is $actual"
  git_release diff --quiet || fail "release has unstaged tracked changes"
  git_release diff --cached --quiet || fail "release has staged changes"
  git_release symbolic-ref -q HEAD >/dev/null && fail "release must be an exact detached checkout"
  [[ "$STEEL_RAG_REPO_DIR" == "$HOME/.steel-rag/releases/"* ]] || fail "release must be under ~/.steel-rag/releases"
}

render_plist() {
  require_configuration
  STEEL_RAG_TEMPLATE_SOURCE="$TEMPLATE_SOURCE" \
  STEEL_RAG_REPO_DIR="$STEEL_RAG_REPO_DIR" \
  STEEL_RAG_DATA_DIR="$STEEL_RAG_DATA_DIR" \
  STEEL_RAG_ENV_FILE="$STEEL_RAG_ENV_FILE" \
  STEEL_RAG_LOG_DIR="$STEEL_RAG_LOG_DIR" \
  STEEL_RAG_WRAPPER_PATH="$STEEL_RAG_WRAPPER_PATH" \
  STEEL_RAG_WORKING_DIR="$STEEL_RAG_WORKING_DIR" \
  python3 - <<'PY'
import os
from pathlib import Path
from xml.sax.saxutils import escape

template = Path(os.environ["STEEL_RAG_TEMPLATE_SOURCE"]).read_text(encoding="utf-8")
replacements = {
    "__STEEL_RAG_REPO_DIR__": os.environ["STEEL_RAG_REPO_DIR"],
    "__STEEL_RAG_DATA_DIR__": os.environ["STEEL_RAG_DATA_DIR"],
    "__STEEL_RAG_ENV_FILE__": os.environ["STEEL_RAG_ENV_FILE"],
    "__STEEL_RAG_LOG_DIR__": os.environ["STEEL_RAG_LOG_DIR"],
    "__STEEL_RAG_WRAPPER_PATH__": os.environ["STEEL_RAG_WRAPPER_PATH"],
    "__STEEL_RAG_WORKING_DIR__": os.environ["STEEL_RAG_WORKING_DIR"],
}
for placeholder, value in replacements.items():
    template = template.replace(placeholder, escape(value))
if "__STEEL_RAG_" in template:
    raise SystemExit("Rendered plist contains an unresolved placeholder.")
print(template, end="")
PY
}

preflight() {
  require_exact_release
  bash -n "$WRAPPER_SOURCE"
  local temporary_plist
  temporary_plist="$(mktemp "/tmp/$STEEL_RAG_LABEL.launchagent.XXXXXX")"
  render_plist > "$temporary_plist"
  plutil -lint "$temporary_plist" >/dev/null
  rm -f "$temporary_plist"
  printf 'Private-preview LaunchAgent preflight passed for exact release %s; no state changed.\n' "$(release_sha)"
}

install_service() {
  preflight
  mkdir -p "$STEEL_RAG_INSTALL_DIR" "$STEEL_RAG_LOG_DIR" "$(dirname "$STEEL_RAG_PLIST_PATH")"
  install -m 0755 "$WRAPPER_SOURCE" "$STEEL_RAG_WRAPPER_PATH"
  local temporary_plist
  temporary_plist="$(mktemp "/tmp/$STEEL_RAG_LABEL.install.XXXXXX")"
  render_plist > "$temporary_plist"
  plutil -lint "$temporary_plist" >/dev/null
  install -m 0644 "$temporary_plist" "$STEEL_RAG_PLIST_PATH"
  rm -f "$temporary_plist"
  printf 'Installed private-preview LaunchAgent files without loading the service.\n'
}

version_matches_expected() {
  local actual="$1"
  [[ ${#actual} -ge 7 && "$STEEL_RAG_EXPECTED_GIT_SHA" == "$actual"* ]]
}

wait_for_health() {
  local require_supervised="${1:-0}"
  local deadline live ready ready_status version actual
  deadline=$(( $(date +%s) + STEEL_RAG_HEALTH_TIMEOUT_SECONDS ))
  while (( $(date +%s) < deadline )); do
    live="$(curl --max-time 3 --fail --silent "http://$STEEL_RAG_HOST:$STEEL_RAG_PORT/health/live" 2>/dev/null || true)"
    ready="$(curl --max-time 3 --fail --silent "http://$STEEL_RAG_HOST:$STEEL_RAG_PORT/health/ready" 2>/dev/null || true)"
    ready_status="$(python3 -c 'import json,sys; print((json.load(sys.stdin) or {}).get("status", ""))' <<<"$ready" 2>/dev/null || true)"
    version="$(curl --max-time 3 --fail --silent "http://$STEEL_RAG_HOST:$STEEL_RAG_PORT/api/version" 2>/dev/null || true)"
    actual="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("git_sha", ""))' <<<"$version" 2>/dev/null || true)"
    if [[ "$live" == *'"live"'* && "$ready_status" == "ready" ]] && version_matches_expected "$actual"; then
      if [[ "$require_supervised" == "0" ]] || supervised_listener_is_ready; then
        printf '%s\n' "$version"
        return 0
      fi
    fi
    sleep 1
  done
  printf 'Timed out waiting for private-preview LaunchAgent health on %s:%s. %s\n' "$STEEL_RAG_HOST" "$STEEL_RAG_PORT" "$SUPERVISION_DIAGNOSTIC" >&2
  return 1
}

pid_is_or_descends_from() {
  local candidate_pid="$1" ancestor_pid="$2" parent_pid
  while [[ "$candidate_pid" =~ ^[1-9][0-9]*$ ]]; do
    [[ "$candidate_pid" == "$ancestor_pid" ]] && return 0
    parent_pid="$(ps -o ppid= -p "$candidate_pid" 2>/dev/null | tr -d '[:space:]')"
    [[ -n "$parent_pid" && "$parent_pid" != "$candidate_pid" ]] || break
    candidate_pid="$parent_pid"
  done
  return 1
}

supervised_listener_is_ready() {
  local job_status state service_pid listener_pid listener_user
  job_status="$("$STEEL_RAG_LAUNCHCTL_BIN" print "$STEEL_RAG_DOMAIN/$STEEL_RAG_LABEL" 2>/dev/null)" || {
    SUPERVISION_DIAGNOSTIC="user LaunchAgent is not loaded"
    return 1
  }
  state="$(sed -nE 's/^[[:space:]]*state = (.*)$/\1/p' <<<"$job_status" | head -n 1)"
  service_pid="$(sed -nE 's/^[[:space:]]*pid = ([0-9]+).*$/\1/p' <<<"$job_status" | head -n 1)"
  listener_pid="$("$STEEL_RAG_LSOF_BIN" -nP -tiTCP:"$STEEL_RAG_PORT" -sTCP:LISTEN 2>/dev/null | head -n 1)"
  listener_user="$(ps -o user= -p "$listener_pid" 2>/dev/null | tr -d '[:space:]')"
  [[ "$state" == "running" ]] || { SUPERVISION_DIAGNOSTIC="LaunchAgent state is ${state:-unknown}"; return 1; }
  [[ -n "$service_pid" && -n "$listener_pid" ]] || { SUPERVISION_DIAGNOSTIC="LaunchAgent or listener PID is missing"; return 1; }
  [[ "$listener_user" == "$(id -un)" ]] || { SUPERVISION_DIAGNOSTIC="listener is not owned by the current user"; return 1; }
  pid_is_or_descends_from "$listener_pid" "$service_pid" || { SUPERVISION_DIAGNOSTIC="listener is not owned by LaunchAgent PID $service_pid"; return 1; }
  SUPERVISION_DIAGNOSTIC="LaunchAgent PID $service_pid owns listener PID $listener_pid"
}

command="${1:-}"
case "$command" in
  render) render_plist ;;
  preflight) preflight ;;
  install) install_service ;;
  load) "$STEEL_RAG_LAUNCHCTL_BIN" bootstrap "$STEEL_RAG_DOMAIN" "$STEEL_RAG_PLIST_PATH" ;;
  unload) "$STEEL_RAG_LAUNCHCTL_BIN" bootout "$STEEL_RAG_DOMAIN/$STEEL_RAG_LABEL" ;;
  restart) require_exact_release; "$STEEL_RAG_LAUNCHCTL_BIN" kickstart -k "$STEEL_RAG_DOMAIN/$STEEL_RAG_LABEL"; wait_for_health 1 ;;
  verify) require_exact_release; wait_for_health 0 ;;
  verify-supervised) require_exact_release; wait_for_health 1 ;;
  status) "$STEEL_RAG_LAUNCHCTL_BIN" print "$STEEL_RAG_DOMAIN/$STEEL_RAG_LABEL" ;;
  *) usage; exit 2 ;;
esac
