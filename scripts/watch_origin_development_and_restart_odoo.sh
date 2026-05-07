#!/usr/bin/env bash
# Poll git: when origin/development tip changes after fetch, restart Odoo.
# Does not modify your working tree unless PULL_ON_REMOTE_UPDATE=1 (ff-only, clean tree only).
#
# Usage (tmux/systemd):
#   ./scripts/watch_origin_development_and_restart_odoo.sh
# Env:
#   INTERVAL_SECS=120
#   REMOTE_NAME=origin
#   TRACK_BRANCH=development
#   PULL_ON_REMOTE_UPDATE=0|1
#   ODOO_RESTART_GIT_BRANCH=development  (for consistency with hooks)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

INTERVAL_SECS="${INTERVAL_SECS:-120}"
REMOTE_NAME="${REMOTE_NAME:-origin}"
TRACK_BRANCH="${TRACK_BRANCH:-development}"
STATE_DIR="${ROOT}/logs"
STATE_FILE="${STATE_DIR}/.last_seen_${REMOTE_NAME}_${TRACK_BRANCH}_commit"
LOCK_FILE="/tmp/lugal_watch_${TRACK_BRANCH}_odoo_restart.lock"

mkdir -p "$STATE_DIR"
chmod +x "$ROOT/scripts/restart_odoo_ws.sh" 2>/dev/null || true

remote_ref="${REMOTE_NAME}/${TRACK_BRANCH}"

init_state_from_remote() {
  local tip
  tip="$(git rev-parse "$remote_ref" 2>/dev/null || true)"
  if [[ -n "$tip" ]]; then
    echo "$tip" > "$STATE_FILE"
    echo "watch: initialized state $remote_ref = $tip (no restart)"
  fi
}

if [[ ! -f "$STATE_FILE" ]]; then
  git fetch "$REMOTE_NAME" "$TRACK_BRANCH" 2>/dev/null || git fetch "$REMOTE_NAME" 2>/dev/null || true
  init_state_from_remote
fi

echo "watch: polling $remote_ref every ${INTERVAL_SECS}s (state $STATE_FILE)"

while true; do
  (
    flock -n 9 || exit 0
    git fetch "$REMOTE_NAME" "$TRACK_BRANCH" 2>/dev/null || git fetch "$REMOTE_NAME" 2>/dev/null || true
    new_tip="$(git rev-parse "$remote_ref" 2>/dev/null || true)"
    if [[ -z "$new_tip" ]]; then
      exit 0
    fi
    old_tip=""
    [[ -f "$STATE_FILE" ]] && old_tip="$(cat "$STATE_FILE")"
    if [[ -z "$old_tip" ]]; then
      echo "$new_tip" > "$STATE_FILE"
      exit 0
    fi
    if [[ "$old_tip" == "$new_tip" ]]; then
      exit 0
    fi

    echo "watch: $remote_ref moved $old_tip -> $new_tip"

    if [[ "${PULL_ON_REMOTE_UPDATE:-0}" == "1" ]]; then
      cur="$(git branch --show-current 2>/dev/null || true)"
      if [[ "$cur" == "$TRACK_BRANCH" ]] && git diff --quiet && git diff --cached --quiet; then
        git pull --ff-only "$REMOTE_NAME" "$TRACK_BRANCH" || true
      fi
    fi

    echo "$new_tip" > "$STATE_FILE"
    "$ROOT/scripts/restart_odoo_ws.sh" || echo "watch: restart failed" >&2
  ) 9>"$LOCK_FILE"

  sleep "$INTERVAL_SECS"
done
