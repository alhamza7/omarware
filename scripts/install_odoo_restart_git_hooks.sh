#!/usr/bin/env bash
# Point this repo at scripts/git-hooks so post-merge runs after git pull.
# Run from anywhere: ./scripts/install_odoo_restart_git_hooks.sh

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

git config core.hooksPath scripts/git-hooks
chmod +x scripts/git-hooks/post-merge 2>/dev/null || true
chmod +x scripts/restart_odoo_ws.sh scripts/watch_origin_development_and_restart_odoo.sh 2>/dev/null || true

echo "core.hooksPath=$(git config --get core.hooksPath)"
echo "Hooks installed. After 'git pull' on branch 'development', Odoo (odoo_ws.conf) will restart."
echo "Optional: run ./scripts/watch_origin_development_and_restart_odoo.sh in tmux for fetch-based restarts."
