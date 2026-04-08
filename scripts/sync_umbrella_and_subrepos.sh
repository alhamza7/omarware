#!/usr/bin/env bash
# =====================================================================
# sync_umbrella_and_subrepos.sh
# - Umbrella (Lugal-ai): fetch + fast-forward pull للفرع الحالي.
# - إن وُجد .gitmodules (مثلاً على فرع development): تهيئة وتحديث الـ submodules.
# - اختياري: --bump-submodules يسحب أحدث commit من الفرع الافتراضي لكل submodule.
#
# الاستخدام:
#   ./scripts/sync_umbrella_and_subrepos.sh
#   ./scripts/sync_umbrella_and_subrepos.sh --fetch-only
#   ./scripts/sync_umbrella_and_subrepos.sh --bump-submodules   # يتطلب .gitmodules
# =====================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

FETCH_ONLY=false
BUMP_SUBMODULES=false
for arg in "$@"; do
  case "$arg" in
    --fetch-only) FETCH_ONLY=true ;;
    --bump-submodules) BUMP_SUBMODULES=true ;;
    -h|--help)
      sed -n '2,20p' "$0"
      exit 0
      ;;
  esac
done

echo "==> Fetch origin"
git fetch origin

if [[ -f .gitmodules ]]; then
  echo "==> Submodule layout (.gitmodules present)"
  git submodule sync --recursive
  git submodule update --init --recursive

  if [[ "$BUMP_SUBMODULES" == true ]]; then
    echo "==> Bump each submodule to latest remote default branch (ff-only)"
    git submodule foreach --recursive '
      git fetch origin
      def=$(git symbolic-ref -q refs/remotes/origin/HEAD 2>/dev/null | sed "s@^refs/remotes/origin/@@")
      def=${def:-}
      ok=
      for b in "$def" main master develop development; do
        [ -z "$b" ] && continue
        if git show-ref -q --verify "refs/remotes/origin/$b" 2>/dev/null; then
          git checkout -q "$b" 2>/dev/null || git checkout -q -B "$b" "origin/$b"
          git pull --ff-only origin "$b" && ok=1 && break
        fi
      done
      if [ -z "$ok" ]; then
        echo "WARN: $(pwd): could not ff-pull; leave as detached or fix remote branch" >&2
      fi
    '
    echo "==> Review submodule pointers, then commit umbrella:"
    echo "    git status && git add -u && git commit -m 'chore: bump submodules' && git push"
  fi
else
  echo "==> Monorepo layout (no .gitmodules): addons are inlined in this repo."
  BR="$(git rev-parse --abbrev-ref HEAD)"
  if [[ "$FETCH_ONLY" == true ]]; then
    echo "    Skipped pull (--fetch-only). Current branch: $BR"
  else
    echo "==> Pull --ff-only origin/$BR"
    git pull --ff-only origin "$BR"
  fi
  if [[ "$BUMP_SUBMODULES" == true ]]; then
    echo "WARN: --bump-submodules ignored: no .gitmodules on this branch." >&2
    echo "    To work with submodules, use a worktree on origin/development, e.g.:"
    echo "    git worktree add ../Lugal-ai-dev-sub origin/development"
    echo "    cd ../Lugal-ai-dev-sub && ./scripts/sync_umbrella_and_subrepos.sh --bump-submodules"
  fi
fi

echo "==> Done. Branch: $(git rev-parse --abbrev-ref HEAD) @ $(git rev-parse --short HEAD)"
