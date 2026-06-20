#!/usr/bin/env bash
# Deploy ParallelOps eval dashboard to Vercel (static + bundled artifacts).
#
# Default artifact source: Devliker_fullstack (override with arg or PARALLELOPS_ARTIFACTS_REPO).
#
# Usage:
#   VERCEL_TOKEN=xxx ./deploy-dashboard-vercel.sh
#   VERCEL_TOKEN=xxx VERCEL_INSECURE_TLS=1 ./deploy-dashboard-vercel.sh   # corporate VPN SSL errors
#   VERCEL_TOKEN=xxx ./deploy-dashboard-vercel.sh /path/to/other-repo
#   VERCEL_TOKEN=xxx ./deploy-dashboard-vercel.sh /path/to/repo my-project-name
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_ARTIFACTS_REPO="${PARALLELOPS_ARTIFACTS_REPO:-$HOME/Desktop/Devliker_fullstack}"
REPO_ROOT="${1:-$DEFAULT_ARTIFACTS_REPO}"
PROJECT_NAME="${2:-parallelops-eval-dash}"
CANONICAL_URL="https://${PROJECT_NAME}.vercel.app"
DASHBOARD="$SCRIPT_DIR/.parallelops/dashboard"
ARTIFACTS="$(cd "$REPO_ROOT" && pwd)/.parallelops/artifacts"
VERCEL_DIR="$DASHBOARD/.vercel"
TLS_DIR="$SCRIPT_DIR/.parallelops"

setup_node_tls() {
  if [[ -z "${NODE_EXTRA_CA_CERTS:-}" && "$(uname -s)" == "Darwin" ]]; then
    local bundle="$TLS_DIR/macos-ca-bundle.pem"
    if [[ ! -f "$bundle" ]]; then
      mkdir -p "$TLS_DIR"
      security find-certificate -a -p /System/Library/Keychains/SystemRootCertificates.keychain \
        /Library/Keychains/System.keychain 2>/dev/null >"$bundle" || true
    fi
    [[ -s "$bundle" ]] && export NODE_EXTRA_CA_CERTS="$bundle"
  fi
  if [[ "${VERCEL_INSECURE_TLS:-}" == "1" ]]; then
    export NODE_TLS_REJECT_UNAUTHORIZED=0
    echo "[deploy] VERCEL_INSECURE_TLS=1 — TLS verification disabled (corporate proxy workaround)"
  fi
}

setup_node_tls

if [[ -z "${VERCEL_TOKEN:-}" ]]; then
  echo "Error: set VERCEL_TOKEN (Vercel → Account Settings → Tokens)" >&2
  exit 1
fi

if [[ ! -d "$ARTIFACTS" ]]; then
  echo "Error: no artifacts at $ARTIFACTS" >&2
  echo "  Run eval-finish in the target repo, or pass its path:" >&2
  echo "  ./deploy-dashboard-vercel.sh /path/to/Devliker_fullstack" >&2
  exit 1
fi

if [[ ! -f "$ARTIFACTS/index.json" ]]; then
  echo "Error: missing $ARTIFACTS/index.json — run eval-finish first" >&2
  exit 1
fi

echo "Repo:       $(basename "$REPO_ROOT")"
echo "Artifacts:  $ARTIFACTS"
echo "Dashboard:  $DASHBOARD"
echo "Project:    $PROJECT_NAME"
echo ""

if [[ -f "$VERCEL_DIR/project.json" ]]; then
  linked="$(python3 -c "import json; print(json.load(open('$VERCEL_DIR/project.json')).get('projectName',''))" 2>/dev/null || true)"
  if [[ -n "$linked" && "$linked" != "$PROJECT_NAME" ]]; then
    echo "Unlinking old Vercel project '$linked' → '$PROJECT_NAME'"
    rm -rf "$VERCEL_DIR"
  fi
fi

cd "$DASHBOARD"
npm install --silent
export VITE_ARTIFACTS_ROOT="$ARTIFACTS"
npm run build:vercel

npx --yes vercel deploy --prod --yes \
  --token "$VERCEL_TOKEN" \
  --scope shivendra-11s-projects \
  --name "$PROJECT_NAME" \
  --cwd "$DASHBOARD"

echo ""
echo "Done. Live dashboard: $CANONICAL_URL"
