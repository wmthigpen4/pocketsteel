#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'private-preview app startup failed: %s\n' "$*" >&2
  exit 1
}

STEEL_RAG_REPO_DIR="${STEEL_RAG_REPO_DIR:-}"
STEEL_RAG_DATA_DIR="${STEEL_RAG_DATA_DIR:-$STEEL_RAG_REPO_DIR}"
STEEL_RAG_ENV_FILE="${STEEL_RAG_ENV_FILE:-}"
STEEL_RAG_LOG_DIR="${STEEL_RAG_LOG_DIR:-}"
STEEL_RAG_HOST="${STEEL_RAG_HOST:-127.0.0.1}"
STEEL_RAG_PORT="${STEEL_RAG_PORT:-8770}"

[[ -n "$STEEL_RAG_REPO_DIR" ]] || fail "STEEL_RAG_REPO_DIR is required"
[[ -d "$STEEL_RAG_DATA_DIR" ]] || fail "missing data directory: $STEEL_RAG_DATA_DIR"
[[ -n "$STEEL_RAG_ENV_FILE" ]] || fail "STEEL_RAG_ENV_FILE is required"
[[ -n "$STEEL_RAG_LOG_DIR" ]] || fail "STEEL_RAG_LOG_DIR is required"
[[ "$STEEL_RAG_HOST" == "127.0.0.1" ]] || fail "refusing to bind private preview to non-loopback host: $STEEL_RAG_HOST"
[[ "$STEEL_RAG_PORT" =~ ^[0-9]+$ ]] || fail "STEEL_RAG_PORT must be numeric"

cd "$STEEL_RAG_REPO_DIR" || fail "cannot cd to repo: $STEEL_RAG_REPO_DIR"
[[ -x ".venv/bin/python" ]] || fail "missing executable .venv/bin/python"
[[ -r "$STEEL_RAG_ENV_FILE" ]] || fail "missing readable env file: $STEEL_RAG_ENV_FILE"

mkdir -p "$STEEL_RAG_LOG_DIR"

# shellcheck disable=SC1090
set -a
source "$STEEL_RAG_ENV_FILE"
set +a

export STEEL_RAG_SEMANTIC_ANSWER_ENABLED="${STEEL_RAG_SEMANTIC_ANSWER_ENABLED:-false}"
STEEL_RAG_SEMANTIC_ENABLED="$(printf '%s' "$STEEL_RAG_SEMANTIC_ANSWER_ENABLED" | tr '[:upper:]' '[:lower:]')"
case "$STEEL_RAG_SEMANTIC_ENABLED" in
  1|true|yes|on)
    if [[ -z "${OPENAI_API_KEY:-}" ]]; then
      STEEL_RAG_SECURITY_BIN="${STEEL_RAG_SECURITY_BIN:-/usr/bin/security}"
      STEEL_RAG_OPENAI_KEYCHAIN_ACCOUNT="${STEEL_RAG_OPENAI_KEYCHAIN_ACCOUNT:-$(/usr/bin/id -un)}"
      STEEL_RAG_OPENAI_KEYCHAIN_SERVICE="${STEEL_RAG_OPENAI_KEYCHAIN_SERVICE:-pocket-steel-openai-api-key}"
      [[ -x "$STEEL_RAG_SECURITY_BIN" ]] || fail "macOS Keychain client is not executable"
      if ! STEEL_RAG_OPENAI_KEY="$("$STEEL_RAG_SECURITY_BIN" find-generic-password \
        -a "$STEEL_RAG_OPENAI_KEYCHAIN_ACCOUNT" \
        -s "$STEEL_RAG_OPENAI_KEYCHAIN_SERVICE" \
        -w 2>/dev/null)"; then
        fail "semantic answers are enabled but the OpenAI credential could not be loaded from macOS Keychain"
      fi
      [[ -n "$STEEL_RAG_OPENAI_KEY" ]] || fail "semantic answers are enabled but the macOS Keychain credential is empty"
      export OPENAI_API_KEY="$STEEL_RAG_OPENAI_KEY"
      unset STEEL_RAG_OPENAI_KEY
    fi
    ;;
  0|false|no|off)
    ;;
  *)
    fail "STEEL_RAG_SEMANTIC_ANSWER_ENABLED must be a boolean"
    ;;
esac

export PYTHONPATH="${STEEL_RAG_PYTHONPATH:-.}"
export STEEL_RAG_AUTH_PROVIDER="${STEEL_RAG_AUTH_PROVIDER:-cloudflare_access}"
export STEEL_RAG_ANSWER_AUTH_MODE="${STEEL_RAG_ANSWER_AUTH_MODE:-production}"
export STEEL_RAG_RETRIEVAL_MODE="${STEEL_RAG_RETRIEVAL_MODE:-hybrid_private_first}"
export STEEL_RAG_ENABLE_PRIVATE_SOURCES="${STEEL_RAG_ENABLE_PRIVATE_SOURCES:-true}"
export STEEL_RAG_ENABLE_MELODY_EXERCISE="${STEEL_RAG_ENABLE_MELODY_EXERCISE:-true}"
export STEEL_RAG_ENABLE_MELODY_IMPORT="${STEEL_RAG_ENABLE_MELODY_IMPORT:-true}"
export STEEL_RAG_SCORE_OMR_PROVIDER="${STEEL_RAG_SCORE_OMR_PROVIDER:-homr}"
export STEEL_RAG_RETRIEVAL_DEBUG="${STEEL_RAG_RETRIEVAL_DEBUG:-false}"
export OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"

STEEL_RAG_OPERATOR_HOME="$(cd "$(dirname "$STEEL_RAG_ENV_FILE")/../.." && pwd)"
export HOMR_BIN="${HOMR_BIN:-$STEEL_RAG_OPERATOR_HOME/.local/bin/homr}"
STEEL_RAG_IMPORT_ENABLED="$(printf '%s' "$STEEL_RAG_ENABLE_MELODY_IMPORT" | tr '[:upper:]' '[:lower:]')"
STEEL_RAG_OMR_PROVIDER="$(printf '%s' "$STEEL_RAG_SCORE_OMR_PROVIDER" | tr '[:upper:]' '[:lower:]')"
case "$STEEL_RAG_IMPORT_ENABLED" in
  1|true|yes|on)
    if [[ "$STEEL_RAG_OMR_PROVIDER" == "homr" && ! -x "$HOMR_BIN" ]]; then
      fail "Homr is selected for printed-score import but is not executable: $HOMR_BIN"
    fi
    ;;
esac

STEEL_RAG_CHROMA_PATH="${STEEL_RAG_CHROMA_PATH:-$STEEL_RAG_DATA_DIR/corpus-v2/vector-stores/chroma}"
STEEL_RAG_CHROMA_COLLECTION="${STEEL_RAG_CHROMA_COLLECTION:-steel_guitar_unified_v2}"
export STEEL_RAG_PRIVATE_CHROMA_PATH="${STEEL_RAG_PRIVATE_CHROMA_PATH:-$STEEL_RAG_DATA_DIR/corpus-private/vector-stores/chroma}"

exec .venv/bin/python scripts/serve_v2_rerank_smoke.py \
  --host "$STEEL_RAG_HOST" \
  --port "$STEEL_RAG_PORT" \
  --v2-chroma-path "$STEEL_RAG_CHROMA_PATH" \
  --v2-collection "$STEEL_RAG_CHROMA_COLLECTION" \
  --answer-auth-mode production \
  --auth-provider cloudflare-access
