#!/bin/bash
# =====================================================================
# extract_submodules.sh
# يفصل كل موديول إلى repo مستقل على GitHub ثم يضيفه كـ submodule
# =====================================================================
set -euo pipefail

ROOT="/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai"
ADDONS="$ROOT/addons"
GH_USER="alhamza7"
TMP_DIR="/tmp/nbs_submodule_extract"

# الموديولات المطلوب فصلها
MODULES=(
  "lugal_email"
  "lugal_inventory"
  "lugal_ai"
  "lugal_fragrantica"
  "ultramsg_integration"
  "perfume_showcase_api"
  "invoice_designer"
  "custom_pricelist_packaging"
  "product_label_designer"
  "nbs_archive"
  "sap_integration"
  "pos_perfume_custom"
  "repzo_integration"
)

echo "======================================================"
echo "  NBS Submodule Extractor — account: $GH_USER"
echo "  Modules to process: ${#MODULES[@]}"
echo "======================================================"

mkdir -p "$TMP_DIR"

extract_module() {
  local MOD_NAME="$1"
  local MOD_PATH="$ADDONS/$MOD_NAME"
  local TMP="$TMP_DIR/$MOD_NAME"

  echo ""
  echo "──────────────────────────────────────────────────"
  echo "▶  $MOD_NAME"
  echo "──────────────────────────────────────────────────"

  # ── تحقق من وجود المجلد ──
  if [ ! -d "$MOD_PATH" ]; then
    echo "   ⚠️  مجلد غير موجود — تخطي"
    return 0
  fi

  # ── تحقق: هل هو submodule بالفعل؟ ──
  if grep -q "\"addons/$MOD_NAME\"" "$ROOT/.gitmodules" 2>/dev/null; then
    echo "   ✅ submodule موجود بالفعل — تخطي"
    return 0
  fi

  # ── 1. إنشاء repo مؤقت وcommit ──
  rm -rf "$TMP"
  mkdir -p "$TMP"
  cp -r "$MOD_PATH/." "$TMP/"
  cd "$TMP"
  git init -q
  git add .
  git commit -q -m "init: $MOD_NAME — extracted from Lugal-ai monorepo"

  # ── 2. إنشاء repo على GitHub ──
  if gh repo view "$GH_USER/$MOD_NAME" &>/dev/null 2>&1; then
    echo "   ℹ️  repo موجود على GitHub بالفعل"
  else
    echo "   📦 إنشاء repo على GitHub..."
    gh repo create "$GH_USER/$MOD_NAME" \
      --private \
      --description "Odoo module: $MOD_NAME — NBS Lugal ERP"
    echo "   ✅ تم إنشاء الـ repo"
  fi

  # ── 3. رفع الكود ──
  git remote add origin "https://github.com/$GH_USER/$MOD_NAME.git"
  git branch -M main
  git push -q -u origin main
  echo "   ✅ كود مرفوع"

  # ── 4. إضافة كـ submodule ──
  cd "$ROOT"
  git rm -r --cached "addons/$MOD_NAME" -q 2>/dev/null || true
  rm -rf "$MOD_PATH"

  git submodule add \
    "https://github.com/$GH_USER/$MOD_NAME.git" \
    "addons/$MOD_NAME"

  echo "   ✅ تمت إضافته كـ submodule"
}

# ── تشغيل لكل موديول ──
for MOD in "${MODULES[@]}"; do
  extract_module "$MOD"
done

# ── 5. Commit نهائي على Lugal-ai ──
echo ""
echo "══════════════════════════════════════════════════"
echo "▶  Committing to Lugal-ai umbrella repo..."
echo "══════════════════════════════════════════════════"

cd "$ROOT"
git add .gitmodules addons/

COMMIT_BODY=""
for M in "${MODULES[@]}"; do
  COMMIT_BODY+="  - $M → github.com/$GH_USER/$M"$'\n'
done

git commit -m "$(cat <<EOF
refactor: extract custom modules as git submodules

Modules extracted:
$COMMIT_BODY
Lugal-ai is now the umbrella repo. Each module has its own GitHub repo.
EOF
)"

echo ""
echo "▶  Pushing Lugal-ai to GitHub (branch: development)..."
git push origin development

echo ""
echo "════════════════════════════════════════════════════"
echo "✅  اكتمل! الموديولات الجديدة على GitHub:"
echo "════════════════════════════════════════════════════"
for M in "${MODULES[@]}"; do
  echo "  https://github.com/$GH_USER/$M"
done
