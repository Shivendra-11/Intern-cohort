#!/usr/bin/env bash
# Source repo-root .env if present (auto-export all KEY=value pairs).
load_root_env() {
  local root="${1:?root directory required}"
  local env_file="$root/.env"
  if [ -f "$env_file" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$env_file"
    set +a
  fi
}
