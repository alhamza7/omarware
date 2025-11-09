-- نسخ foreign_name من sap.product.extended إلى product.template
-- تنفيذ مباشر بدون تعليقات

UPDATE product_template pt
SET 
    foreign_name = spe.foreign_name,
    write_date = NOW(),
    write_uid = 2
FROM sap_product_extended spe
INNER JOIN product_product pp ON spe.product_id = pp.id
WHERE pp.product_tmpl_id = pt.id
  AND spe.foreign_name IS NOT NULL 
  AND spe.foreign_name != ''
  AND (pt.foreign_name IS NULL OR pt.foreign_name = '');

