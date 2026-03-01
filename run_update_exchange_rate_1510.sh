#!/bin/bash
# تحديث سعر الصرف إلى 1510 في قاعدة البيانات
# استخدم من مجلد المشروع: ./run_update_exchange_rate_1510.sh

# مطابق لـ odoo.conf (db_name = nbs_lugalai)
DB_NAME="${DB_NAME:-nbs_lugalai}"
DB_USER="${DB_USER:-odoo_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
PGPASSWORD="${PGPASSWORD:-root}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "تحديث سعر الصرف إلى 1510 (POS Perfume)"
echo "قاعدة البيانات: $DB_NAME"
echo "=============================================="

export PGPASSWORD
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 << 'SQL'
-- تحديث إن وُجد
UPDATE ir_config_parameter
SET value = '1510.0'
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';

-- إدراج إن لم يكن السجل موجوداً
INSERT INTO ir_config_parameter (key, value, create_date, write_date, create_uid, write_uid)
SELECT 'pos_perfume.default_exchange_rate_usd_iqd', '1510.0', NOW(), NOW(), 1, 1
WHERE NOT EXISTS (
    SELECT 1 FROM ir_config_parameter WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd'
);

-- عرض النتيجة
SELECT key AS "المفتاح", value AS "السعر (IQD/USD)" FROM ir_config_parameter
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';
SQL

echo ""
echo "تم. السعر الافتراضي للطلبات الجديدة: 1510 د.ع"
