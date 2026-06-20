#!/usr/bin/env bash
#
# install.sh — make the repo-builder agent + assets globally available to Claude Code.
#
# Default: symlink this source repo into ~/.claude so edits here go live immediately.
# Use --copy for a portable snapshot (no link back to this checkout).
#
# Usage:
#   ./install.sh            # symlink install (recommended for development)
#   ./install.sh --copy     # copy install (portable; survives deleting this repo)
#   ./install.sh --uninstall

set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_HOME:-$HOME/.claude}"
AGENTS_DIR="$CLAUDE_DIR/agents"
ASSETS_DIR="$CLAUDE_DIR/repo-builder"

MODE="symlink"
case "${1:-}" in
  --copy)      MODE="copy" ;;
  --uninstall) MODE="uninstall" ;;
  ""|--symlink) MODE="symlink" ;;
  *) echo "unknown option: $1" >&2; exit 2 ;;
esac

link_or_copy() {
  # $1 = source path, $2 = dest path
  rm -rf "$2"
  if [ "$MODE" = "copy" ]; then
    cp -R "$1" "$2"
  else
    ln -s "$1" "$2"
  fi
}

if [ "$MODE" = "uninstall" ]; then
  rm -rf "$AGENTS_DIR/repo-builder.md" "$ASSETS_DIR"
  echo "Uninstalled repo-builder from $CLAUDE_DIR"
  exit 0
fi

mkdir -p "$AGENTS_DIR" "$ASSETS_DIR"

# Agent definition
link_or_copy "$SRC_DIR/agents/repo-builder.md" "$AGENTS_DIR/repo-builder.md"

# Assets the agent calls by absolute path
for sub in scripts templates scaffold; do
  link_or_copy "$SRC_DIR/$sub" "$ASSETS_DIR/$sub"
done

echo "Installed repo-builder ($MODE) into $CLAUDE_DIR"
echo "  agent : $AGENTS_DIR/repo-builder.md"
echo "  assets: $ASSETS_DIR/{scripts,templates,scaffold}"
echo
echo "Open any repo in Claude Code and invoke the 'repo-builder' agent."
