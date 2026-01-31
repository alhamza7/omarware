#!/bin/bash

echo "============================================================"
echo "تحديث مباشر لسعر الصرف في POS Perfume"
echo "Direct database update for POS Perfume exchange rate"
echo "============================================================"
echo ""

# اسم قاعدة البيانات
DB_NAME="nbs_lugalai"

echo "قاعدة البيانات: $DB_NAME"
echo ""

echo "1. التحقق من السعر الحالي..."
echo ""

sudo -u postgres psql $DB_NAME -c "
SELECT 
    key as \"المفتاح\",
    value as \"السعر الحالي (IQD)\"
FROM ir_config_parameter
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';
"

echo ""
echo "2. تحديث السعر إلى 1510..."
echo ""

# التحديث
sudo -u postgres psql $DB_NAME -c "
UPDATE ir_config_parameter
SET value = '1510.0',
    write_date = NOW()
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';
"

# إنشاء إذا لم يكن موجوداً
sudo -u postgres psql $DB_NAME -c "
INSERT INTO ir_config_parameter (key, value, create_date, write_date, create_uid, write_uid)
SELECT 
    'pos_perfume.default_exchange_rate_usd_iqd',
    '1510.0',
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
echo "3. التحقق من السعر الجديد..."
echo ""

sudo -u postgres psql $DB_NAME -c "
SELECT 
    key as \"المفتاح\",
    value as \"السعر الجديد (IQD)\"
FROM ir_config_parameter
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';
"

echo ""
echo "4. عرض آخر 5 طلبات POS Perfume..."
echo ""

# التحقق من وجود الجدول أولاً
TABLE_EXISTS=$(sudo -u postgres psql $DB_NAME -t -c "
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'pos_perfume_order'
);
")

if [[ $TABLE_EXISTS == *"t"* ]]; then
    sudo -u postgres psql $DB_NAME -c "
    SELECT 
        id as \"ID\",
        date_order::date as \"التاريخ\",
        COALESCE(exchange_rate, 0) as \"السعر المستخدم\",
        COALESCE(total_usd, 0) as \"USD\",
        COALESCE(total_iqd, 0) as \"IQD\"
    FROM pos_perfume_order
    WHERE date_order IS NOT NULL
    ORDER BY date_order DESC
    LIMIT 5;
    "
else
    echo "   ℹ️  جدول pos_perfume_order غير موجود (لا توجد طلبات بعد)"
fi

echo ""
echo "============================================================"
echo "✅ تم التحديث بنجاح!"
echo "============================================================"
echo ""
echo "الخطوات التالية:"
echo "1. أعد تشغيل Odoo:"
echo "   pkill -9 -f odoo-bin"
echo "   nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &"
echo ""
echo "2. في المتصفح:"
echo "   - امسح الكاش: Ctrl+Shift+Delete"
echo "   - أعد تحميل الصفحة"
echo ""
echo "3. اختبار POS Perfume:"
echo "   - افتح POS Perfume"
echo "   - امسح باركود منتج"
echo "   - تحقق من السعر: يجب أن يكون × 1510"
echo ""
