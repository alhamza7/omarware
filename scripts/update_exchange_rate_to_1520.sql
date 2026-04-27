-- تحديث جميع سجلات سعر الصرف إلى 1520
-- Update all exchange rate records to 1520

-- 1. تحديث الفواتير والطلبات إذا كانت تحتوي على سعر صرف قديم
-- Update invoices and orders with old exchange rate

-- فحص الفواتير الحالية
SELECT 
    'POS Perfume Orders with old rate' as record_type,
    COUNT(*) as count
FROM pos_perfume_order
WHERE exchange_rate != 1520.0;

-- تحديث جميع الطلبات إلى 1520
UPDATE pos_perfume_order
SET exchange_rate = 1520.0
WHERE exchange_rate != 1520.0;

-- 2. تحديث قيمة سعر الصرف في إعدادات النظام
UPDATE ir_config_parameter
SET value = '1520.0'
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';

-- 3. تأكيد القيمة الجديدة
SELECT 
    key,
    value,
    CASE 
        WHEN value = '1520.0' THEN 'صحيح ✓'
        ELSE 'قيمة أخرى - يحتاج مراجعة'
    END as status
FROM ir_config_parameter
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';

-- 4. عرض الإحصائيات النهائية
SELECT 
    'Total POS Orders' as metric,
    COUNT(*) as value
FROM pos_perfume_order
UNION ALL
SELECT 
    'Orders with 1520 rate',
    COUNT(*)
FROM pos_perfume_order
WHERE exchange_rate = 1520.0
UNION ALL
SELECT 
    'Orders with other rate',
    COUNT(*)
FROM pos_perfume_order
WHERE exchange_rate != 1520.0;
