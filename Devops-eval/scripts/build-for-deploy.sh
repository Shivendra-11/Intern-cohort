#!/usr/bin/env bash
# Copy REPORT.json into dashboard as real files (works on static hosts — no symlinks)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORTS="$ROOT/dashboard/public/reports"

rm -rf "$REPORTS"
mkdir -p "$REPORTS"

for d in d1-terraform d2-compose-stack d3-ci-pipeline d4-kubernetes d5-dev-env d6-observability; do
  mkdir -p "$REPORTS/$d"
  if [ -f "$ROOT/$d/REPORT.json" ]; then
    cp "$ROOT/$d/REPORT.json" "$REPORTS/$d/REPORT.json"
  else
    echo '{"task":"'"${d##*-}"'","status":"NOT_RUN","description":"","duration_seconds":0,"artifacts":[],"timestamp":""}' \
      > "$REPORTS/$d/REPORT.json"
  fi
done

echo "Reports copied to dashboard/public/reports/"
cd "$ROOT/dashboard"
npm run build

# SPA routing for static hosts (Vercel prebuilt deploy reads this from dist/)
cat > dist/vercel.json <<'EOF'
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
EOF

echo "Built: $ROOT/dashboard/dist/"
