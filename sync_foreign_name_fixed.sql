-- نسخ foreign_name من sap_product_extended إلى product_template
-- استعلام محسّن ومختبر

-- الخطوة 1: عرض عدد السجلات والأمثلة
SELECT 
    COUNT(*) as total_to_sync,
    STRING_AGG(DISTINCT spe.foreign_name, ', ' ORDER BY spe.foreign_name) FILTER (WHERE spe.foreign_name IS NOT NULL) as sample_foreign_names
FROM sap_product_extended spe
WHERE spe.foreign_name IS NOT NULL AND spe.foreign_name != '';

-- الخطوة 2: عرض أمثلة تفصيلية (أول 20)
SELECT 
    spe.id as extended_id,
    pp.id as product_id,
    pp.default_code,
    pt.id as template_id,
    COALESCE(pt.name->>'en_US', pt.name::text) as product_name,
    pt.foreign_name as current_foreign_name,
    spe.foreign_name as new_foreign_name,
    CASE 
        WHEN pt.foreign_name IS NULL OR pt.foreign_name = '' THEN 'سيتم التحديث'
        WHEN pt.foreign_name = spe.foreign_name THEN 'متطابق'
        ELSE 'سيتم الاستبدال'
    END as status
FROM sap_product_extended spe
INNER JOIN product_product pp ON spe.product_id = pp.id
INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
WHERE spe.foreign_name IS NOT NULL AND spe.foreign_name != ''
ORDER BY pp.default_code
LIMIT 20;

-- الخطوة 3: التحديث الفعلي (نسخ الكل - حتى الموجود)
UPDATE product_template 
SET 
    foreign_name = subquery.foreign_name,
    write_date = NOW() AT TIME ZONE 'UTC',
    write_uid = 2
FROM (
    SELECT DISTINCT ON (pt.id)
        pt.id as template_id,
        spe.foreign_name
    FROM sap_product_extended spe
    INNER JOIN product_product pp ON spe.product_id = pp.id
    INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
    WHERE spe.foreign_name IS NOT NULL 
      AND spe.foreign_name != ''
    ORDER BY pt.id, spe.id DESC
) AS subquery
WHERE product_template.id = subquery.template_id;

-- الخطوة 4: التحقق من النتائج
SELECT 
    COUNT(*) as total_products,
    COUNT(CASE WHEN pt.foreign_name IS NOT NULL AND pt.foreign_name != '' THEN 1 END) as with_foreign_name,
    COUNT(CASE WHEN pt.foreign_name IS NULL OR pt.foreign_name = '' THEN 1 END) as without_foreign_name,
    ROUND(COUNT(CASE WHEN pt.foreign_name IS NOT NULL AND pt.foreign_name != '' THEN 1 END)::numeric / 
          NULLIF(COUNT(*)::numeric, 0) * 100, 2) as percentage_filled
FROM product_template pt
INNER JOIN product_product pp ON pt.id = pp.product_tmpl_id
INNER JOIN sap_product_extended spe ON pp.id = spe.product_id;

-- الخطوة 5: عرض بعض النتائج بعد التحديث
SELECT 
    pp.default_code,
    COALESCE(pt.name->>'en_US', pt.name::text) as product_name,
    pt.foreign_name,
    spe.foreign_name as extended_foreign_name,
    CASE WHEN pt.foreign_name = spe.foreign_name THEN '✓' ELSE '✗' END as match
FROM sap_product_extended spe
INNER JOIN product_product pp ON spe.product_id = pp.id
INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
WHERE spe.foreign_name IS NOT NULL AND spe.foreign_name != ''
ORDER BY pp.default_code
LIMIT 20;

