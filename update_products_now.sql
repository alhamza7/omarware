-- تحديث Foreign Name من SAP Extended
UPDATE product_product pp
SET foreign_name = spe.foreign_name,
    write_date = NOW(),
    write_uid = 2
FROM sap_product_extended spe
WHERE spe.product_id = pp.id
AND spe.foreign_name IS NOT NULL
AND spe.foreign_name != '';

-- تحديث الأسعار من SAP Price List 1
UPDATE product_product pp
SET list_price = pli.fixed_price,
    write_date = NOW(),
    write_uid = 2
FROM product_pricelist_item pli
INNER JOIN product_pricelist pl ON pli.pricelist_id = pl.id
WHERE pli.product_id = pp.id
AND pl.name = 'SAP Price List 1'
AND pli.fixed_price > 0;

-- عرض النتائج
SELECT 
    COUNT(*) FILTER (WHERE foreign_name IS NOT NULL AND foreign_name != '') as products_with_foreign_name,
    COUNT(*) FILTER (WHERE list_price > 0) as products_with_price,
    COUNT(*) as total_products
FROM product_product;

