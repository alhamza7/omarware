#!/bin/bash

echo "============================================================"
echo "تحديث جميع أسعار الصرف إلى 1500 IQD"
echo "Update all exchange rates to 1500 IQD"
echo "============================================================"
echo ""

cd /home/lugalai/Lugal-ai

# 1. تحديث سعر الصرف الرئيسي في Odoo
echo "1. تحديث سعر الصرف الرئيسي في Odoo..."
venv/bin/python update_exchange_rate.py 1500

echo ""
echo "2. تحديث سعر الصرف في POS Perfume (قاعدة البيانات)..."
sudo -u postgres psql nbs_lugalai -c "
UPDATE ir_config_parameter
SET value = '1500.0',
    write_date = NOW()
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';

INSERT INTO ir_config_parameter (key, value, create_date, write_date, create_uid, write_uid)
SELECT 
    'pos_perfume.default_exchange_rate_usd_iqd',
    '1500.0',
    NOW(),
    NOW(),
    1,
    1
WHERE NOT EXISTS (
    SELECT 1 FROM ir_config_parameter 
    WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd'
);
"

echo ""
echo "3. التحقق من التحديث..."
sudo -u postgres psql nbs_lugalai -c "
SELECT 
    'pos_perfume' as module,
    key as parameter,
    value as rate
FROM ir_config_parameter
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd'
UNION ALL
SELECT 
    'odoo_main' as module,
    'res_currency_rate' as parameter,
    ROUND(1.0 / rate::numeric, 2)::text as rate
FROM res_currency_rate cr
JOIN res_currency c ON c.id = cr.currency_id
WHERE c.name = 'USD'
ORDER BY cr.name DESC
LIMIT 1;
"

echo ""
echo "4. ترقية وحدة POS Perfume..."
venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai -u pos_perfume_custom --stop-after-init

echo ""
echo "5. إعادة تشغيل Odoo..."
pkill -9 -f odoo-bin
sleep 3
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &
echo "   PID: $!"
sleep 5

if pgrep -f "odoo-bin" > /dev/null; then
    echo "   ✅ Odoo يعمل بنجاح!"
else
    echo "   ❌ فشل تشغيل Odoo!"
fi

echo ""
echo "============================================================"
echo "✅ تم تحديث جميع أسعار الصرف إلى 1500 IQD"
echo "============================================================"
echo ""
echo "الخطوات التالية في المتصفح:"
echo "1. امسح الكاش: Ctrl+Shift+Delete → All time"
echo "2. Hard Refresh: Ctrl+F5"
echo "3. سجل خروج ثم دخول"
echo "4. افتح POS Perfume واختبر"
echo ""
echo "اختبار السعر:"
echo "100 USD × 1500 = 150,000 IQD ✓"
echo ""
