#!/usr/bin/env bash
# Push the Repzo submodule change to the umbrella repo (origin, branch development).
# Run from anywhere; uses repo root. Needs sudo once to fix mixed .git ownership.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! git diff --cached --name-only | grep -q .; then
  echo "No staged changes. From repo root run:" >&2
  echo "  git add .gitmodules addons/repzo_integration" >&2
  echo "  git add -u addons/repzo_integration  # if replacing tracked files" >&2
  exit 1
fi

echo "Fixing .git ownership (sudo password may be required)..."
sudo chown -R "$(id -un)":"$(id -gn)" .git

echo "Committing..."
git commit -m "chore(repzo): track addons/repzo_integration as git submodule (odoo-repzo-integration)"

echo "Pushing origin development..."
git push origin development

echo "OK — umbrella updated."
