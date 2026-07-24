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
STEEL_RAG_DATA_DIR="${STEEL_RAG_DATA_DIR:-$DEFAULT_REPO_DIR}"
STEEL_RAG_HOST="${STEEL_RAG_HOST:-127.0.0.1}"
STEEL_RAG_PORT="${STEEL_RAG_PORT:-8770}"
STEEL_RAG_EXPECTED_GIT_SHA="${STEEL_RAG_EXPECTED_GIT_SHA:-}"
STEEL_RAG_HEALTH_TIMEOUT_SECONDS="${STEEL_RAG_HEALTH_TIMEOUT_SECONDS:-90}"
STEEL_RAG_REPLACE_PID="${STEEL_RAG_REPLACE_PID:-}"
STEEL_RAG_PLIST_PATH="${STEEL_RAG_PLIST_PATH:-/Library/LaunchDaemons/$STEEL_RAG_LABEL.plist}"
STEEL_RAG_WRAPPER_INSTALL_DIR="${STEEL_RAG_WRAPPER_INSTALL_DIR:-/usr/local/libexec/steel-guitar-rag}"
STEEL_RAG_WRAPPER_PATH="${STEEL_RAG_WRAPPER_PATH:-$STEEL_RAG_WRAPPER_INSTALL_DIR/run-private-preview-app.sh}"
STEEL_RAG_WORKING_DIR="${STEEL_RAG_WORKING_DIR:-$STEEL_RAG_WRAPPER_INSTALL_DIR}"
STEEL_RAG_LAUNCHCTL_BIN="${STEEL_RAG_LAUNCHCTL_BIN:-launchctl}"
STEEL_RAG_LSOF_BIN="${STEEL_RAG_LSOF_BIN:-lsof}"
TEMPLATE_PATH="$SCRIPT_DIR/com.steelguitarrag.private-preview.plist.template"
WRAPPER_SOURCE_PATH="$SCRIPT_DIR/run-private-preview-app.sh"
SUPERVISION_DIAGNOSTIC="not checked"

usage() {
  cat <<USAGE
Usage: $0 <command>

Commands:
  render    Render the LaunchDaemon plist to stdout.
  install   Render, lint, and install the plist to /Library/LaunchDaemons. Requires sudo.
  load      Bootstrap the installed LaunchDaemon. Requires sudo.
  unload    Boot out the LaunchDaemon. Requires sudo.
  activate  Install an exact detached release, restart it, and verify health. Requires sudo.
  preflight Validate an exact detached release and rendered plist without changing state.
  restart   Restart the loaded LaunchDaemon and verify the exact release. Requires sudo.
  verify    Verify live, ready, and version endpoints without changing state.
  verify-supervised
            Verify health, exact version, LaunchDaemon state, and listener ownership.
  status    Print launchctl status for the LaunchDaemon without changing state.
  tail      Tail durable app stdout/stderr logs.
  version   Curl local /api/version on the configured loopback port.

Environment overrides:
  STEEL_RAG_REPO_DIR=$STEEL_RAG_REPO_DIR
  STEEL_RAG_RUN_AS_USER=$STEEL_RAG_RUN_AS_USER
  STEEL_RAG_ENV_FILE=$STEEL_RAG_ENV_FILE
  STEEL_RAG_LOG_DIR=$STEEL_RAG_LOG_DIR
  STEEL_RAG_DATA_DIR=$STEEL_RAG_DATA_DIR
  STEEL_RAG_HOST=$STEEL_RAG_HOST
  STEEL_RAG_PORT=$STEEL_RAG_PORT
  STEEL_RAG_EXPECTED_GIT_SHA=$STEEL_RAG_EXPECTED_GIT_SHA
  STEEL_RAG_HEALTH_TIMEOUT_SECONDS=$STEEL_RAG_HEALTH_TIMEOUT_SECONDS
  STEEL_RAG_REPLACE_PID=$STEEL_RAG_REPLACE_PID
  STEEL_RAG_PLIST_PATH=$STEEL_RAG_PLIST_PATH
  STEEL_RAG_WRAPPER_INSTALL_DIR=$STEEL_RAG_WRAPPER_INSTALL_DIR
  STEEL_RAG_WRAPPER_PATH=$STEEL_RAG_WRAPPER_PATH
  STEEL_RAG_WORKING_DIR=$STEEL_RAG_WORKING_DIR
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
  [[ -x "$WRAPPER_SOURCE_PATH" ]] || {
    printf 'Missing executable wrapper source: %s\n' "$WRAPPER_SOURCE_PATH" >&2
    exit 1
  }
  if [[ "$STEEL_RAG_HOST" != "127.0.0.1" ]]; then
    printf 'Refusing non-loopback host for private preview: %s\n' "$STEEL_RAG_HOST" >&2
    exit 1
  fi
  [[ -d "$STEEL_RAG_DATA_DIR" ]] || {
    printf 'Missing data directory: %s\n' "$STEEL_RAG_DATA_DIR" >&2
    exit 1
  }
}

git_release() {
  git -c "safe.directory=$STEEL_RAG_REPO_DIR" -C "$STEEL_RAG_REPO_DIR" "$@"
}

release_sha() {
  git_release rev-parse HEAD 2>/dev/null
}

require_exact_release() {
  require_host_config
  [[ -n "$STEEL_RAG_EXPECTED_GIT_SHA" ]] || {
    printf 'STEEL_RAG_EXPECTED_GIT_SHA is required for activation or restart.\n' >&2
    exit 1
  }

  local actual expected
  actual="$(release_sha)" || {
    printf 'Release directory is not a Git checkout: %s\n' "$STEEL_RAG_REPO_DIR" >&2
    exit 1
  }
  expected="$(git_release rev-parse "${STEEL_RAG_EXPECTED_GIT_SHA}^{commit}" 2>/dev/null)" || {
    printf 'Expected release is not available in the release checkout: %s\n' "$STEEL_RAG_EXPECTED_GIT_SHA" >&2
    exit 1
  }
  [[ "$actual" == "$expected" ]] || {
    printf 'Release mismatch: expected %s but checkout is %s\n' "$expected" "$actual" >&2
    exit 1
  }
  git_release diff --quiet
  git_release diff --cached --quiet
}

require_immutable_release() {
  require_exact_release
  if git_release symbolic-ref -q HEAD >/dev/null; then
    printf 'Activation requires a detached exact-commit release checkout: %s\n' "$STEEL_RAG_REPO_DIR" >&2
    exit 1
  fi
  [[ "$STEEL_RAG_REPO_DIR" == "$STEEL_RAG_USER_HOME/.steel-rag/runtime/"* || \
     "$STEEL_RAG_REPO_DIR" == "$STEEL_RAG_USER_HOME/.steel-rag/releases/"* ]] || {
    printf 'Activation requires a dedicated release under ~/.steel-rag/runtime or ~/.steel-rag/releases.\n' >&2
    exit 1
  }
}

render_plist() {
  require_host_config
  STEEL_RAG_LABEL="$STEEL_RAG_LABEL" \
  STEEL_RAG_REPO_DIR="$STEEL_RAG_REPO_DIR" \
  STEEL_RAG_DATA_DIR="$STEEL_RAG_DATA_DIR" \
  STEEL_RAG_RUN_AS_USER="$STEEL_RAG_RUN_AS_USER" \
  STEEL_RAG_RUN_AS_GROUP="$STEEL_RAG_RUN_AS_GROUP" \
  STEEL_RAG_ENV_FILE="$STEEL_RAG_ENV_FILE" \
  STEEL_RAG_LOG_DIR="$STEEL_RAG_LOG_DIR" \
  STEEL_RAG_HOST="$STEEL_RAG_HOST" \
  STEEL_RAG_PORT="$STEEL_RAG_PORT" \
  STEEL_RAG_WRAPPER_PATH="$STEEL_RAG_WRAPPER_PATH" \
  STEEL_RAG_WORKING_DIR="$STEEL_RAG_WORKING_DIR" \
  python3 - "$TEMPLATE_PATH" <<'PY'
import os
import sys
from pathlib import Path

template = Path(sys.argv[1]).read_text(encoding="utf-8")
replacements = {
    "__STEEL_RAG_LABEL__": os.environ["STEEL_RAG_LABEL"],
    "__STEEL_RAG_REPO_DIR__": os.environ["STEEL_RAG_REPO_DIR"],
    "__STEEL_RAG_DATA_DIR__": os.environ["STEEL_RAG_DATA_DIR"],
    "__STEEL_RAG_RUN_AS_USER__": os.environ["STEEL_RAG_RUN_AS_USER"],
    "__STEEL_RAG_RUN_AS_GROUP__": os.environ["STEEL_RAG_RUN_AS_GROUP"],
    "__STEEL_RAG_ENV_FILE__": os.environ["STEEL_RAG_ENV_FILE"],
    "__STEEL_RAG_LOG_DIR__": os.environ["STEEL_RAG_LOG_DIR"],
    "__STEEL_RAG_HOST__": os.environ["STEEL_RAG_HOST"],
    "__STEEL_RAG_PORT__": os.environ["STEEL_RAG_PORT"],
    "__STEEL_RAG_WRAPPER_PATH__": os.environ["STEEL_RAG_WRAPPER_PATH"],
    "__STEEL_RAG_WORKING_DIR__": os.environ["STEEL_RAG_WORKING_DIR"],
}
for old, new in replacements.items():
    template = template.replace(old, new)
sys.stdout.write(template)
PY
}

install_plist() {
  require_host_config
  local tmp
  tmp="$(mktemp "/tmp/$STEEL_RAG_LABEL.plist.XXXXXX")"
  render_plist > "$tmp"
  plutil -lint "$tmp"
  if [[ ! -r "$STEEL_RAG_ENV_FILE" ]]; then
    printf 'Warning: env file is not readable yet: %s\n' "$STEEL_RAG_ENV_FILE" >&2
  fi
  sudo install -d -o root -g wheel -m 0755 "$STEEL_RAG_WRAPPER_INSTALL_DIR"
  sudo install -o root -g wheel -m 0755 "$WRAPPER_SOURCE_PATH" "$STEEL_RAG_WRAPPER_PATH"
  sudo xattr -d com.apple.quarantine "$STEEL_RAG_WRAPPER_PATH" 2>/dev/null || true
  sudo install -d -o "$STEEL_RAG_RUN_AS_USER" -g "$STEEL_RAG_RUN_AS_GROUP" -m 0755 "$STEEL_RAG_LOG_DIR"
  sudo install -o root -g wheel -m 0644 "$tmp" "$STEEL_RAG_PLIST_PATH"
  rm -f "$tmp"
  printf 'Installed %s\n' "$STEEL_RAG_WRAPPER_PATH"
  printf 'Installed %s\n' "$STEEL_RAG_PLIST_PATH"
  printf 'Next: %s load\n' "$0"
}

preflight_release() {
  require_immutable_release
  local tmp
  tmp="$(mktemp "/tmp/$STEEL_RAG_LABEL.preflight.plist.XXXXXX")"
  render_plist > "$tmp"
  plutil -lint "$tmp"
  rm -f "$tmp"
  printf 'Validated exact detached release %s\n' "$(release_sha)"
}

launchd_job_status() {
  local output
  if output="$("$STEEL_RAG_LAUNCHCTL_BIN" print "system/$STEEL_RAG_LABEL" 2>/dev/null)"; then
    printf '%s\n' "$output"
    return 0
  fi
  if output="$(sudo -n "$STEEL_RAG_LAUNCHCTL_BIN" print "system/$STEEL_RAG_LABEL" 2>/dev/null)"; then
    printf '%s\n' "$output"
    return 0
  fi
  return 1
}

pid_is_or_descends_from() {
  local candidate_pid="$1"
  local ancestor_pid="$2"
  local parent_pid
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
  if ! job_status="$(launchd_job_status)"; then
    SUPERVISION_DIAGNOSTIC="LaunchDaemon job is not readable in the system domain"
    return 1
  fi
  state="$(sed -nE 's/^[[:space:]]*state = (.*)$/\1/p' <<<"$job_status" | head -n 1)"
  service_pid="$(sed -nE 's/^[[:space:]]*pid = ([0-9]+).*$/\1/p' <<<"$job_status" | head -n 1)"
  listener_pid="$("$STEEL_RAG_LSOF_BIN" -nP -tiTCP:"$STEEL_RAG_PORT" -sTCP:LISTEN 2>/dev/null | head -n 1)"
  if [[ "$state" != "running" ]]; then
    SUPERVISION_DIAGNOSTIC="LaunchDaemon state is '${state:-unknown}', expected 'running'"
    return 1
  fi
  if [[ -z "$service_pid" ]]; then
    SUPERVISION_DIAGNOSTIC="LaunchDaemon is running but did not report a service PID"
    return 1
  fi
  if [[ -z "$listener_pid" ]]; then
    SUPERVISION_DIAGNOSTIC="LaunchDaemon PID $service_pid is running but port $STEEL_RAG_PORT has no listener"
    return 1
  fi
  listener_user="$(ps -o user= -p "$listener_pid" 2>/dev/null | tr -d '[:space:]')"
  if [[ "$listener_user" != "$STEEL_RAG_RUN_AS_USER" ]]; then
    SUPERVISION_DIAGNOSTIC="port $STEEL_RAG_PORT listener PID $listener_pid is owned by '${listener_user:-unknown}', expected '$STEEL_RAG_RUN_AS_USER'"
    return 1
  fi
  if ! pid_is_or_descends_from "$listener_pid" "$service_pid"; then
    SUPERVISION_DIAGNOSTIC="port $STEEL_RAG_PORT listener PID $listener_pid is not LaunchDaemon PID $service_pid or its descendant"
    return 1
  fi
  SUPERVISION_DIAGNOSTIC="LaunchDaemon PID $service_pid owns listener PID $listener_pid"
  return 0
}

bootstrap_with_retry() {
  local attempts="${1:-3}"
  local attempt
  for (( attempt=1; attempt<=attempts; attempt++ )); do
    if sudo "$STEEL_RAG_LAUNCHCTL_BIN" bootstrap system "$STEEL_RAG_PLIST_PATH"; then
      return 0
    fi
    if (( attempt < attempts )); then
      printf 'LaunchDaemon bootstrap attempt %s/%s failed; retrying after launchd settles.\n' "$attempt" "$attempts" >&2
      sleep 2
    fi
  done
  return 1
}

wait_for_health() {
  local require_supervised="${1:-0}"
  local deadline now live ready version actual
  [[ "$STEEL_RAG_HEALTH_TIMEOUT_SECONDS" =~ ^[1-9][0-9]*$ ]] || {
    printf 'STEEL_RAG_HEALTH_TIMEOUT_SECONDS must be a positive integer.\n' >&2
    return 1
  }
  deadline=$(( $(date +%s) + STEEL_RAG_HEALTH_TIMEOUT_SECONDS ))
  while :; do
    now="$(date +%s)"
    if (( now >= deadline )); then
      printf 'Timed out waiting for private preview health on %s:%s\n' "$STEEL_RAG_HOST" "$STEEL_RAG_PORT" >&2
      if [[ "$require_supervised" == "1" ]]; then
        printf 'Last supervision check: %s\n' "$SUPERVISION_DIAGNOSTIC" >&2
      fi
      return 1
    fi
    live="$(curl --max-time 3 --fail --silent --show-error "http://$STEEL_RAG_HOST:$STEEL_RAG_PORT/health/live" 2>/dev/null || true)"
    ready="$(curl --max-time 3 --fail --silent --show-error "http://$STEEL_RAG_HOST:$STEEL_RAG_PORT/health/ready" 2>/dev/null || true)"
    version="$(curl --max-time 3 --fail --silent --show-error "http://$STEEL_RAG_HOST:$STEEL_RAG_PORT/api/version" 2>/dev/null || true)"
    if [[ "$live" == *'"live"'* && "$ready" == *'"ready"'* && -n "$version" ]]; then
      actual="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("git_sha", ""))' <<<"$version" 2>/dev/null || true)"
      if [[ -z "$STEEL_RAG_EXPECTED_GIT_SHA" || "$actual" == "${STEEL_RAG_EXPECTED_GIT_SHA:0:7}" ]]; then
        if [[ "$require_supervised" == "1" ]]; then
          if ! supervised_listener_is_ready; then
            sleep 1
            continue
          fi
        fi
        printf '%s\n' "$version"
        return 0
      fi
    fi
    sleep 1
  done
}

stop_replacement_origin() {
  [[ -n "$STEEL_RAG_REPLACE_PID" ]] || return 0
  [[ "$STEEL_RAG_REPLACE_PID" =~ ^[1-9][0-9]*$ ]] || {
    printf 'STEEL_RAG_REPLACE_PID must be a positive process ID.\n' >&2
    return 1
  }
  local listener_pid deadline
  listener_pid="$(lsof -nP -tiTCP:"$STEEL_RAG_PORT" -sTCP:LISTEN 2>/dev/null | head -n 1)"
  [[ "$listener_pid" == "$STEEL_RAG_REPLACE_PID" ]] || {
    printf 'Refusing to stop PID %s because it is not the port-%s listener.\n' "$STEEL_RAG_REPLACE_PID" "$STEEL_RAG_PORT" >&2
    return 1
  }
  kill -TERM "$STEEL_RAG_REPLACE_PID"
  deadline=$(( $(date +%s) + 30 ))
  while kill -0 "$STEEL_RAG_REPLACE_PID" 2>/dev/null; do
    (( $(date +%s) < deadline )) || {
      printf 'Timed out waiting for replacement PID %s to stop.\n' "$STEEL_RAG_REPLACE_PID" >&2
      return 1
    }
    sleep 1
  done
}

activate_release() {
  require_immutable_release
  local backup="" was_loaded=0
  if [[ -f "$STEEL_RAG_PLIST_PATH" ]]; then
    backup="$(mktemp "/tmp/$STEEL_RAG_LABEL.rollback.plist.XXXXXX")"
    cp "$STEEL_RAG_PLIST_PATH" "$backup"
  fi
  if launchctl print "system/$STEEL_RAG_LABEL" >/dev/null 2>&1; then
    was_loaded=1
  fi

  install_plist
  if (( was_loaded )); then
    if ! sudo launchctl bootout "system/$STEEL_RAG_LABEL"; then
      if [[ -n "$backup" ]]; then
        sudo install -o root -g wheel -m 0644 "$backup" "$STEEL_RAG_PLIST_PATH"
        rm -f "$backup"
      fi
      printf 'Could not stop the loaded LaunchDaemon; the previous definition was restored.\n' >&2
      return 1
    fi
  fi
  if ! stop_replacement_origin; then
    if [[ -n "$backup" ]]; then
      sudo install -o root -g wheel -m 0644 "$backup" "$STEEL_RAG_PLIST_PATH"
      bootstrap_with_retry
      rm -f "$backup"
    else
      sudo rm -f "$STEEL_RAG_PLIST_PATH"
    fi
    printf 'Replacement-origin handover failed; the previous definition was restored.\n' >&2
    return 1
  fi
  if bootstrap_with_retry && wait_for_health 1; then
    [[ -z "$backup" ]] || rm -f "$backup"
    printf 'Activated verified release %s\n' "$(release_sha)"
    return 0
  fi

  printf 'Activation failed; attempting rollback to the previous LaunchDaemon definition.\n' >&2
  sudo launchctl bootout "system/$STEEL_RAG_LABEL" >/dev/null 2>&1 || true
  if [[ -n "$backup" ]]; then
    sudo install -o root -g wheel -m 0644 "$backup" "$STEEL_RAG_PLIST_PATH"
    sleep 2
    bootstrap_with_retry
    rm -f "$backup"
  else
    sudo rm -f "$STEEL_RAG_PLIST_PATH"
  fi
  return 1
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
  activate)
    activate_release
    ;;
  preflight)
    preflight_release
    ;;
  restart)
    require_exact_release
    sudo launchctl kickstart -k "system/$STEEL_RAG_LABEL"
    wait_for_health 1
    ;;
  status)
    launchctl print "system/$STEEL_RAG_LABEL"
    ;;
  tail)
    tail -n 100 -f "$STEEL_RAG_LOG_DIR/app.out.log" "$STEEL_RAG_LOG_DIR/app.err.log"
    ;;
  version)
    curl -sS "http://$STEEL_RAG_HOST:$STEEL_RAG_PORT/api/version"
    ;;
  verify)
    wait_for_health
    ;;
  verify-supervised)
    wait_for_health 1
    ;;
  -h|--help|help|"")
    usage
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
