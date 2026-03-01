#!/bin/bash
# تحديث السيرفر للحصول على سعر الصرف 1510 من GitHub
# نفّذ على السيرفر: ./UPDATE_SERVER_EXCHANGE_RATE.sh

set -e
echo "=============================================="
echo "تحديث السيرفر - سعر الصرف 1510"
echo "=============================================="

cd /home/lugalai/Lugal-ai

echo ""
echo "1) التحقق من حالة Git الحالية..."
git status

echo ""
echo "2) سحب آخر التحديثات من GitHub..."
git pull

echo ""
echo "3) التحقق من وجود الثابت في الكود..."
if grep -q "EXCHANGE_RATE_USD_IQD = 1510" addons/pos_perfume_custom/static/src/app/pos_perfume_screen.js; then
    echo "✅ الكود يحتوي على EXCHANGE_RATE_USD_IQD = 1510"
    grep -n "EXCHANGE_RATE_USD_IQD = 1510" addons/pos_perfume_custom/static/src/app/pos_perfume_screen.js
else
    echo "❌ الكود لا يحتوي على الثابت! تحقق من git pull"
    exit 1
fi

echo ""
echo "4) تحديث قاعدة البيانات إلى 1510..."
PGPASSWORD=root psql -h localhost -p 5432 -U odoo_user -d nbs_lugalai -v ON_ERROR_STOP=1 << 'SQL'
UPDATE ir_config_parameter SET value = '1510.0', write_date = NOW() WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';
INSERT INTO ir_config_parameter (key, value, create_date, write_date, create_uid, write_uid)
SELECT 'pos_perfume.default_exchange_rate_usd_iqd', '1510.0', NOW(), NOW(), 1, 1
WHERE NOT EXISTS (SELECT 1 FROM ir_config_parameter WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd');
SELECT 'القيمة في قاعدة البيانات:' AS status, value FROM ir_config_parameter WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';
SQL

echo ""
echo "=============================================="
echo "5) إعادة تشغيل Odoo (ضروري)"
echo "=============================================="
echo "نفّذ الأمر التالي:"
echo "  sudo systemctl restart odoo"
echo ""
echo "بعد إعادة التشغيل:"
echo "- حدّث الصفحة (Ctrl+F5) عند كل مستخدم"
echo "- يجب أن يظهر 1510 للجميع"
echo "=============================================="
