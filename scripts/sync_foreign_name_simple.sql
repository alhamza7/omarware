-- نسخ foreign_name - نسخة مبسطة للتنفيذ المباشر

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

