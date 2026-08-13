#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'canonical-frontier service startup failed: %s\n' "$*" >&2
  exit 1
}

STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT="${STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT:-}"
STEEL_RAG_CANONICAL_FRONTIER_MANIFEST="${STEEL_RAG_CANONICAL_FRONTIER_MANIFEST:-}"
STEEL_RAG_CANONICAL_FRONTIER_PYTHON="${STEEL_RAG_CANONICAL_FRONTIER_PYTHON:-}"
STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE="${STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE:-}"
STEEL_RAG_CANONICAL_FRONTIER_VERIFIER="${STEEL_RAG_CANONICAL_FRONTIER_VERIFIER:-}"
STEEL_RAG_CANONICAL_FRONTIER_HOST="${STEEL_RAG_CANONICAL_FRONTIER_HOST:-127.0.0.1}"
STEEL_RAG_CANONICAL_FRONTIER_PORT="${STEEL_RAG_CANONICAL_FRONTIER_PORT:-8771}"
STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_PORT="${STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_PORT:-11435}"

[[ -d "$STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT" ]] || fail "service root is missing"
[[ -r "$STEEL_RAG_CANONICAL_FRONTIER_MANIFEST" ]] || fail "bundle manifest is missing"
[[ -r "$STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE" ]] || fail "environment file is missing"
[[ -r "$STEEL_RAG_CANONICAL_FRONTIER_VERIFIER" ]] || fail "bundle verifier is missing"
[[ "$STEEL_RAG_CANONICAL_FRONTIER_HOST" == "127.0.0.1" ]] || fail "non-loopback binding is prohibited"
[[ "$STEEL_RAG_CANONICAL_FRONTIER_PORT" =~ ^[0-9]+$ ]] || fail "port must be numeric"
[[ "$STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_PORT" =~ ^[0-9]+$ ]] || fail "Ollama port must be numeric"

# shellcheck disable=SC1090
set -a
source "$STEEL_RAG_CANONICAL_FRONTIER_ENV_FILE"
set +a

[[ -n "${STEEL_RAG_CANONICAL_FRONTIER_TOKEN:-}" ]] || fail "service bearer token is missing"

STEEL_RAG_CANONICAL_FRONTIER_OLLAMA="$STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT/assets/ollama/bin/ollama"
STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_MODELS="$STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT/assets/ollama/models"
STEEL_RAG_CANONICAL_FRONTIER_HF_HOME="$STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT/assets/huggingface"
STEEL_RAG_CANONICAL_FRONTIER_VENDOR="$STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT/vendor/python"
STEEL_RAG_CANONICAL_FRONTIER_BUNDLED_PYTHON="$STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT/assets/python/3.9/bin/python3"
[[ -x "$STEEL_RAG_CANONICAL_FRONTIER_BUNDLED_PYTHON" ]] || fail "bundled Python runtime is missing"
[[ "$STEEL_RAG_CANONICAL_FRONTIER_PYTHON" == "$STEEL_RAG_CANONICAL_FRONTIER_BUNDLED_PYTHON" ]] \
  || fail "configured Python must be the bundled service runtime"
[[ -x "$STEEL_RAG_CANONICAL_FRONTIER_OLLAMA" ]] || fail "bundled Ollama executable is missing"
[[ -d "$STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_MODELS" ]] || fail "bundled bge-m3 assets are missing"
[[ -d "$STEEL_RAG_CANONICAL_FRONTIER_HF_HOME" ]] || fail "bundled BGE reranker assets are missing"
[[ -d "$STEEL_RAG_CANONICAL_FRONTIER_VENDOR" ]] || fail "bundled Python dependencies are missing"

export PYTHONPATH="$STEEL_RAG_CANONICAL_FRONTIER_VENDOR:$STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT"
export PYTHONDONTWRITEBYTECODE="1"
export HF_HUB_OFFLINE="1"
export TRANSFORMERS_OFFLINE="1"
export HF_HOME="$STEEL_RAG_CANONICAL_FRONTIER_HF_HOME"
export HUGGINGFACE_HUB_CACHE="$STEEL_RAG_CANONICAL_FRONTIER_HF_HOME/hub"
export OLLAMA_MODELS="$STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_MODELS"
export OLLAMA_HOST="127.0.0.1:$STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_PORT"
export OLLAMA_URL="http://127.0.0.1:$STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_PORT"
cd "$STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT" || fail "cannot enter service root"

"$STEEL_RAG_CANONICAL_FRONTIER_PYTHON" \
  "$STEEL_RAG_CANONICAL_FRONTIER_VERIFIER" \
  --service-root "$STEEL_RAG_CANONICAL_FRONTIER_SERVICE_ROOT" \
  --manifest "$STEEL_RAG_CANONICAL_FRONTIER_MANIFEST"

# Validate credential availability without printing or transmitting it.
"$STEEL_RAG_CANONICAL_FRONTIER_PYTHON" - <<'PY'
from project_answer_relation_openai_v2 import api_key

if not api_key():
    raise SystemExit("OpenAI API credential is unavailable.")
PY

"$STEEL_RAG_CANONICAL_FRONTIER_OLLAMA" serve &
STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_PID=$!
cleanup() {
  if [[ -n "${STEEL_RAG_CANONICAL_FRONTIER_API_PID:-}" ]] \
    && kill -0 "$STEEL_RAG_CANONICAL_FRONTIER_API_PID" 2>/dev/null; then
    kill "$STEEL_RAG_CANONICAL_FRONTIER_API_PID" 2>/dev/null || true
    wait "$STEEL_RAG_CANONICAL_FRONTIER_API_PID" 2>/dev/null || true
  fi
  if kill -0 "$STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_PID" 2>/dev/null; then
    kill "$STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_PID" 2>/dev/null || true
    wait "$STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_DEADLINE=$((SECONDS + 60))
until curl --silent --show-error --fail --max-time 2 "$OLLAMA_URL/api/tags" \
  | "$STEEL_RAG_CANONICAL_FRONTIER_PYTHON" -c 'import json,sys; value=json.load(sys.stdin); raise SystemExit(0 if any(row.get("name", "").split(":", 1)[0] == "bge-m3" for row in value.get("models", [])) else 1)' \
  >/dev/null 2>&1; do
  kill -0 "$STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_PID" 2>/dev/null || fail "bundled Ollama exited during startup"
  (( SECONDS < STEEL_RAG_CANONICAL_FRONTIER_OLLAMA_DEADLINE )) || fail "bundled bge-m3 startup timed out"
  sleep 1
done

export STEEL_RAG_FRONTIER_BUNDLE_VERIFIED="1"
"$STEEL_RAG_CANONICAL_FRONTIER_PYTHON" canonical_frontier_http_api_v3.py \
  --host "$STEEL_RAG_CANONICAL_FRONTIER_HOST" \
  --port "$STEEL_RAG_CANONICAL_FRONTIER_PORT" &
STEEL_RAG_CANONICAL_FRONTIER_API_PID=$!
wait "$STEEL_RAG_CANONICAL_FRONTIER_API_PID"
