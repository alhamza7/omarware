#!/bin/bash
# تصحيح سعر الصرف في قاعدة البيانات ثم إعادة تشغيل Odoo
# شغّله على السيرفر من مجلد المشروع (مثلاً: /home/lugalai/Lugal-ai)

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# إعدادات من odoo.conf
DB_NAME="${DB_NAME:-nbs_lugalai}"
DB_USER="${DB_USER:-odoo_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
export PGPASSWORD="${PGPASSWORD:-root}"

echo "=============================================="
echo "1) التحقق من القيمة الحالية في قاعدة البيانات"
echo "=============================================="
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
  "SELECT key, value FROM ir_config_parameter WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';" || true

echo ""
echo "=============================================="
echo "2) تحديث القيمة إلى 1510"
echo "=============================================="
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 << 'SQL'
UPDATE ir_config_parameter SET value = '1510.0', write_date = NOW() WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';
INSERT INTO ir_config_parameter (key, value, create_date, write_date, create_uid, write_uid)
SELECT 'pos_perfume.default_exchange_rate_usd_iqd', '1510.0', NOW(), NOW(), 1, 1
WHERE NOT EXISTS (SELECT 1 FROM ir_config_parameter WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd');
SQL

echo ""
echo "=============================================="
echo "3) التحقق بعد التحديث"
echo "=============================================="
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c \
  "SELECT key, value FROM ir_config_parameter WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';"

echo ""
echo "=============================================="
echo "4) إعادة تشغيل Odoo (لتفريغ الـ cache)"
echo "=============================================="
echo "Odoo يخزّن سعر الصرف في الذاكرة. بدون إعادة التشغيل سيبقى بعض المستخدمين يرون 1500."
if command -v systemctl >/dev/null 2>&1; then
    echo "تشغيل: sudo systemctl restart odoo"
    if [ "$(id -u)" = "0" ]; then
        systemctl restart odoo || true
    else
        echo "نفّذ يدوياً: sudo systemctl restart odoo"
    fi
else
    echo "أعد تشغيل عملية Odoo يدوياً ثم حدّث الصفحة (Ctrl+F5)."
fi
echo "=============================================="
