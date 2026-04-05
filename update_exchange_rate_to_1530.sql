-- تحديث سعر الصرف إلى 1530 في إعدادات النظام فقط
-- الفواتير القديمة لا تتأثر بهذا التحديث
UPDATE ir_config_parameter
SET value = '1530.0'
WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';
