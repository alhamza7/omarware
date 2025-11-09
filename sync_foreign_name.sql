-- ===================================================================
-- نسخ foreign_name من sap.product.extended إلى product.template
-- ===================================================================

-- الخطوة 1: عرض عدد السجلات التي سيتم تحديثها (للمعاينة)
SELECT 
    COUNT(*) as total_to_update,
    COUNT(DISTINCT spe.product_id) as unique_products
FROM sap_product_extended spe
INNER JOIN product_product pp ON spe.product_id = pp.id
INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
WHERE spe.foreign_name IS NOT NULL 
  AND spe.foreign_name != ''
  AND (pt.foreign_name IS NULL OR pt.foreign_name = '');

-- الخطوة 2: عرض بعض الأمثلة على ما سيتم تحديثه (أول 10 سجلات)
SELECT 
    pp.id as product_id,
    pp.default_code,
    pt.name as current_name,
    pt.foreign_name as current_foreign_name,
    spe.foreign_name as new_foreign_name
FROM sap_product_extended spe
INNER JOIN product_product pp ON spe.product_id = pp.id
INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
WHERE spe.foreign_name IS NOT NULL 
  AND spe.foreign_name != ''
  AND (pt.foreign_name IS NULL OR pt.foreign_name = '')
LIMIT 10;

-- ===================================================================
-- الخطوة 3: التحديث الفعلي (قم بتنفيذ هذا بعد التأكد من الخطوات السابقة)
-- ===================================================================

UPDATE product_template pt
SET 
    foreign_name = spe.foreign_name,
    write_date = NOW(),
    write_uid = 2  -- غيّر هذا إلى ID المستخدم المناسب
FROM sap_product_extended spe
INNER JOIN product_product pp ON spe.product_id = pp.id
WHERE pp.product_tmpl_id = pt.id
  AND spe.foreign_name IS NOT NULL 
  AND spe.foreign_name != ''
  AND (pt.foreign_name IS NULL OR pt.foreign_name = '');

-- الخطوة 4: التحقق من النتائج
SELECT 
    COUNT(*) as updated_count
FROM product_template pt
INNER JOIN product_product pp ON pt.id = pp.product_tmpl_id
INNER JOIN sap_product_extended spe ON pp.id = spe.product_id
WHERE pt.foreign_name IS NOT NULL 
  AND pt.foreign_name != ''
  AND pt.foreign_name = spe.foreign_name;

-- ===================================================================
-- نسخة بديلة: تحديث الكل (بما في ذلك الموجود)
-- ===================================================================

-- استخدم هذا إذا أردت تحديث جميع السجلات حتى لو كان foreign_name موجوداً
/*
UPDATE product_template pt
SET 
    foreign_name = spe.foreign_name,
    write_date = NOW(),
    write_uid = 2
FROM sap_product_extended spe
INNER JOIN product_product pp ON spe.product_id = pp.id
WHERE pp.product_tmpl_id = pt.id
  AND spe.foreign_name IS NOT NULL 
  AND spe.foreign_name != '';
*/

-- ===================================================================
-- إحصائيات بعد التحديث
-- ===================================================================

SELECT 
    COUNT(*) as total_products,
    COUNT(CASE WHEN pt.foreign_name IS NOT NULL AND pt.foreign_name != '' THEN 1 END) as with_foreign_name,
    COUNT(CASE WHEN pt.foreign_name IS NULL OR pt.foreign_name = '' THEN 1 END) as without_foreign_name
FROM product_template pt
WHERE pt.type = 'product';

