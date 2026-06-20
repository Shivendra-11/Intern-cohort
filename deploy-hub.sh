#!/usr/bin/env bash
# Deploy combined portfolio hub to Vercel — one shareable link for all four projects.
#
#   export VERCEL_TOKEN="..."      https://vercel.com/account/tokens
#   export VERCEL_INSECURE_TLS=1   # only if corporate VPN SSL errors
#   ./deploy-hub.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
HUB="$ROOT/hub"
# Force portfolio hub project name (do not inherit from subproject .env files)
unset VERCEL_PROJECT_NAME 2>/dev/null || true
# Set your desired URL: https://<HUB_PROJECT_NAME>.vercel.app
# Example: export HUB_PROJECT_NAME=ai-agent-eval-suite
PROJECT_NAME="${HUB_PROJECT_NAME:-ai-agent-eval-suite}"
VERCEL_SCOPE="${VERCEL_SCOPE:-shivendra-11s-projects}"
CANONICAL_URL="https://${PROJECT_NAME}.vercel.app"
LOG="$ROOT/.intern-cohort/deploy.log"
VERCEL_DIR="$HUB/.vercel"

mkdir -p "$ROOT/.intern-cohort"

setup_node_tls() {
  if [ "${VERCEL_INSECURE_TLS:-}" = "1" ]; then
    export NODE_TLS_REJECT_UNAUTHORIZED=0
    echo "[deploy] VERCEL_INSECURE_TLS=1 — TLS verification disabled"
  fi
}

if [ -z "${VERCEL_TOKEN:-}" ] && ! npx vercel whoami &>/dev/null 2>&1; then
  echo "Vercel token missing."
  echo "1. Create a token: https://vercel.com/account/tokens"
  echo "2. export VERCEL_TOKEN=your-token"
  echo "3. ./deploy-hub.sh"
  exit 1
fi

setup_node_tls

link_args=(link "$HUB" --yes --project "$PROJECT_NAME" --scope "$VERCEL_SCOPE")
if [ -n "${VERCEL_TOKEN:-}" ]; then
  link_args+=(--token "$VERCEL_TOKEN")
fi
echo "Linking Vercel project: $PROJECT_NAME ..."
npx --yes vercel "${link_args[@]}" >>"$LOG" 2>&1 || true

echo "Deploying portfolio hub from $HUB ..."
echo "Target URL: $CANONICAL_URL"

args=(deploy "$HUB" --prod --yes --scope "$VERCEL_SCOPE")
if [ -n "${VERCEL_TOKEN:-}" ]; then
  args+=(--token "$VERCEL_TOKEN")
fi

if npx --yes vercel "${args[@]}" 2>&1 | tee "$LOG"; then
  DEPLOY_URL="$(grep -oE 'https://[a-zA-Z0-9-]+-[a-zA-Z0-9-]+-shivendra-11s-projects\.vercel\.app' "$LOG" | head -1 || true)"
  if [ -n "$DEPLOY_URL" ]; then
    alias_args=(alias set "$DEPLOY_URL" "${PROJECT_NAME}.vercel.app" --scope "$VERCEL_SCOPE")
    if [ -n "${VERCEL_TOKEN:-}" ]; then
      alias_args+=(--token "$VERCEL_TOKEN")
    fi
    npx --yes vercel "${alias_args[@]}" >>"$LOG" 2>&1 || true
  fi
  echo ""
  echo "✓ Live at: $CANONICAL_URL"
  echo "$CANONICAL_URL" > "$ROOT/.intern-cohort/DEPLOY-LINK.txt"
  echo "Saved to .intern-cohort/DEPLOY-LINK.txt"
else
  echo "Deploy failed — check $LOG"
  exit 1
fi
