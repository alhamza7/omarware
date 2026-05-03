#!/bin/bash

echo "============================================================"
echo "التحقق من سعر الصرف في POS Perfume"
echo "Check POS Perfume exchange rate"
echo "============================================================"
echo ""

DB_NAME="nbs_lugalai"

echo "📊 سعر الصرف المحفوظ:"
echo ""

sudo -u postgres psql $DB_NAME -c "
SELECT 
    '🔑 ' || key as \"المفتاح\",
    '💵 ' || value || ' IQD' as \"السعر\"
FROM ir_config_parameter
WHERE key LIKE '%exchange%rate%'
ORDER BY key;
"

echo ""
echo "📋 آخر 10 طلبات POS Perfume:"
echo ""

TABLE_EXISTS=$(sudo -u postgres psql $DB_NAME -t -c "
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_name = 'pos_perfume_order'
);
")

if [[ $TABLE_EXISTS == *"t"* ]]; then
    sudo -u postgres psql $DB_NAME -c "
    SELECT 
        '📦 ' || id as \"رقم الطلب\",
        date_order::date as \"📅 التاريخ\",
        COALESCE(exchange_rate, 0) as \"💱 السعر\",
        COALESCE(total_usd, 0) as \"💵 USD\",
        COALESCE(total_iqd, 0) as \"💰 IQD\",
        CASE 
            WHEN COALESCE(total_usd, 0) > 0 
            THEN ROUND(COALESCE(total_iqd, 0) / COALESCE(total_usd, 1))
            ELSE 0
        END as \"🧮 الحساب\"
    FROM pos_perfume_order
    WHERE date_order IS NOT NULL
    ORDER BY date_order DESC
    LIMIT 10;
    "
    
    echo ""
    echo "📊 إحصائيات:"
    echo ""
    
    sudo -u postgres psql $DB_NAME -c "
    SELECT 
        COUNT(*) as \"إجمالي الطلبات\",
        COUNT(DISTINCT exchange_rate) as \"أسعار مختلفة\",
        MIN(exchange_rate) as \"أدنى سعر\",
        MAX(exchange_rate) as \"أعلى سعر\",
        ROUND(AVG(exchange_rate), 2) as \"المتوسط\"
    FROM pos_perfume_order
    WHERE exchange_rate IS NOT NULL AND exchange_rate > 0;
    "
else
    echo "   ℹ️  جدول pos_perfume_order غير موجود (لا توجد طلبات بعد)"
fi

echo ""
echo "============================================================"
