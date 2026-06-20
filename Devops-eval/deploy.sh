#!/usr/bin/env bash
# Permanent public deploy via Vercel — URL works 24/7
#
#   export VERCEL_TOKEN="..."      https://vercel.com/account/tokens
#   export VERCEL_INSECURE_TLS=1   # only if corporate VPN SSL errors
#   ./deploy.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/load-env.sh"
load_root_env "$ROOT"
LINK_FILE="$ROOT/.devopsinfra/DEPLOY-LINK.txt"
LOG="$ROOT/.devopsinfra/deploy.log"
PROJECT_NAME="${VERCEL_PROJECT_NAME:-devopsinfra-dash}"
CANONICAL_URL="https://${PROJECT_NAME}.vercel.app"

setup_node_tls() {
  if [ -z "${NODE_EXTRA_CA_CERTS:-}" ] && [ "$(uname -s)" = "Darwin" ]; then
    local bundle="$ROOT/.devopsinfra/macos-ca-bundle.pem"
    if [ ! -f "$bundle" ]; then
      security find-certificate -a -p /System/Library/Keychains/SystemRootCertificates.keychain \
        /Library/Keychains/System.keychain 2>/dev/null > "$bundle" || true
    fi
    [ -s "$bundle" ] && export NODE_EXTRA_CA_CERTS="$bundle"
  fi
  if [ "${VERCEL_INSECURE_TLS:-}" = "1" ]; then
    export NODE_TLS_REJECT_UNAUTHORIZED=0
    echo "[deploy] VERCEL_INSECURE_TLS=1 — TLS verification disabled (corporate proxy workaround)"
  fi
}

ensure_vercel_project_link() {
  local vercel_dir="$ROOT/dashboard/.vercel"
  local linked=""
  if [ -f "$vercel_dir/project.json" ]; then
    linked=$(python3 -c "import json; print(json.load(open('$vercel_dir/project.json')).get('projectName',''))" 2>/dev/null || true)
  fi
  if [ -n "$linked" ] && [ "$linked" != "$PROJECT_NAME" ]; then
    echo "[deploy] Unlinking old Vercel project '$linked' → '$PROJECT_NAME'"
    rm -rf "$vercel_dir"
  fi
}

run_vercel_deploy() {
  local -a args=(deploy dist --prod --yes --name "$PROJECT_NAME")
  if [ -n "${VERCEL_TOKEN:-}" ]; then
    args+=(--token "$VERCEL_TOKEN")
  fi
  cd "$ROOT/dashboard"
  # Deploy prebuilt dist/ (reports baked in locally — no remote rebuild)
  npx --yes vercel "${args[@]}"
}

alias_canonical_url() {
  local deployment_url="$1"
  if [ -z "$deployment_url" ]; then
    echo "$CANONICAL_URL"
    return
  fi
  if [[ "$deployment_url" == *"${PROJECT_NAME}"* ]]; then
    echo "$CANONICAL_URL"
    return
  fi
  local -a args=(alias set "$deployment_url" "${PROJECT_NAME}.vercel.app")
  if [ -n "${VERCEL_TOKEN:-}" ]; then
    args+=(--token "$VERCEL_TOKEN")
  fi
  cd "$ROOT/dashboard"
  if npx --yes vercel "${args[@]}" >>"$LOG" 2>&1; then
    echo "$CANONICAL_URL"
  else
    echo "$deployment_url"
  fi
}

extract_url() {
  local alias
  alias=$(grep 'Aliased' "$LOG" 2>/dev/null | grep -oE 'https://[a-zA-Z0-9.-]+\.vercel\.app' | head -1 || true)
  if [ -n "$alias" ]; then
    echo "$alias"
    return
  fi
  grep -oE 'https://[a-zA-Z0-9.-]+\.vercel\.app' "$LOG" 2>/dev/null \
    | grep -Ev 'vercel\.app/(builds|docs)' | tail -1 || true
}

print_success() {
  local url="$1"
  echo "PUBLIC_URL=${url}" > "$LINK_FILE"
  echo "HUB_URL=${url}/hub" >> "$LINK_FILE"
  echo ""
  echo "══════════════════════════════════════════════════════════"
  echo "  PERMANENT LINK (share anytime):"
  echo "  ${url}/"
  echo ""
  echo "  Services hub: ${url}/hub"
  echo "══════════════════════════════════════════════════════════"
  echo ""
  echo "Saved to .devopsinfra/DEPLOY-LINK.txt"
}

if [ -z "${VERCEL_TOKEN:-}" ] && ! npx vercel whoami &>/dev/null 2>&1; then
  echo "Vercel token missing."
  echo ""
  echo "1. Create a token: https://vercel.com/account/tokens"
  echo "2. Open .env and set:"
  echo "     VERCEL_TOKEN=your-token-here"
  echo "     VERCEL_INSECURE_TLS=1"
  echo "3. Run again: ./deploy.sh"
  echo ""
  echo "Or one-time in terminal:"
  echo "  export VERCEL_TOKEN=\"...\""
  echo "  ./deploy.sh"
  exit 1
fi

chmod +x "$ROOT/scripts/build-for-deploy.sh"
"$ROOT/scripts/build-for-deploy.sh"
mkdir -p "$ROOT/.devopsinfra"
ensure_vercel_project_link
setup_node_tls

echo "Deploying to Vercel..."
if run_vercel_deploy 2>&1 | tee "$LOG"; then
  :
elif grep -qiE 'local issuer certificate|unable to get local issuer' "$LOG"; then
  echo ""
  echo "[deploy] Retrying with VERCEL_INSECURE_TLS=1 ..."
  export VERCEL_INSECURE_TLS=1
  setup_node_tls
  run_vercel_deploy 2>&1 | tee "$LOG"
else
  exit 1
fi

URL=$(extract_url)
if [ -n "$URL" ]; then
  URL=$(alias_canonical_url "$URL")
fi
if [ -z "$URL" ]; then
  echo "Check https://vercel.com/dashboard — project: ${PROJECT_NAME}"
  grep -iE 'https://|Production|Deployed|Error|error' "$LOG" | tail -10 || true
  exit 1
fi

# Verify the site is reachable (not a bare 404)
if ! curl -sf -o /dev/null -w "%{http_code}" "${URL}/" | grep -qE '^200$'; then
  echo "[deploy] Warning: ${URL}/ did not return HTTP 200 — check Vercel dashboard"
fi

print_success "$URL"
