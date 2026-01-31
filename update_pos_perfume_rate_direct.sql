-- =====================================================
-- تحديث سعر الصرف في POS Perfume مباشرة
-- Direct update for POS Perfume exchange rate
-- =====================================================

-- 1. التحقق من السعر الحالي
SELECT 
    key as "المفتاح",
    value as "السعر الحالي"
FROM ir_config_parameter
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';

-- 2. تحديث السعر إلى 1510
UPDATE ir_config_parameter
SET value = '1510.0'
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';

-- 3. إذا لم يكن موجوداً، أنشئه
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

-- 4. التحقق من النتيجة
SELECT 
    key as "المفتاح",
    value as "السعر الجديد"
FROM ir_config_parameter
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';

-- 5. عرض آخر 5 طلبات من POS Perfume
SELECT 
    id as "رقم الطلب",
    date_order as "التاريخ",
    exchange_rate as "السعر المستخدم",
    total_usd as "المبلغ بالدولار",
    total_iqd as "المبلغ بالدينار"
FROM pos_perfume_order
ORDER BY date_order DESC
LIMIT 5;

-- =====================================================
-- ملاحظات:
-- - السعر الجديد: 1510 IQD لكل 1 USD
-- - الطلبات القديمة لن تتأثر
-- - الطلبات الجديدة ستستخدم السعر الجديد
-- =====================================================
