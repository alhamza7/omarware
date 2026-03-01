-- تحديث سعر الصرف إلى 1510 في قاعدة البيانات
-- شغّل على السيرفر: PGPASSWORD=root psql -h localhost -U odoo_user -d nbs_lugalai -f update_exchange_rate_to_1510.sql
-- مهم: بعد التشغيل يجب إعادة تشغيل Odoo (sudo systemctl restart odoo) لأن القيمة تُخزَّن في الذاكرة

-- 1) عرض القيمة الحالية
SELECT key, value AS "القيمة_الحالية" FROM ir_config_parameter WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';

-- 2) التحديث إلى 1510
UPDATE ir_config_parameter SET value = '1510.0', write_date = NOW(), write_uid = 1 WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';

-- 3) إن لم يكن السجل موجوداً أصلاً
INSERT INTO ir_config_parameter (key, value, create_date, write_date, create_uid, write_uid)
SELECT 'pos_perfume.default_exchange_rate_usd_iqd', '1510.0', NOW(), NOW(), 1, 1
WHERE NOT EXISTS (SELECT 1 FROM ir_config_parameter WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd');

-- 4) التحقق
SELECT key, value AS "القيمة_بعد_التحديث" FROM ir_config_parameter WHERE key = 'pos_perfume.default_exchange_rate_usd_iqd';
