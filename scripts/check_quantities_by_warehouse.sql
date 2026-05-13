-- ============================================
-- التحقق من الكميات لكل مخزن
-- Check quantities by warehouse
-- ============================================

-- عرض الكميات مجمعة حسب المخزن
-- Show quantities grouped by warehouse
SELECT 
    sw.id as warehouse_id,
    sw.name as warehouse_name,
    sw.code as warehouse_code,
    COUNT(DISTINCT sq.product_id) as product_count,
    COUNT(sq.id) as quant_records,
    SUM(sq.quantity) as total_quantity,
    SUM(sq.reserved_quantity) as total_reserved
FROM stock_quant sq
JOIN stock_location sl ON sq.location_id = sl.id
LEFT JOIN stock_warehouse sw ON (
    sl.parent_path LIKE concat('%/', sw.view_location_id, '/%')
    OR sl.parent_path LIKE concat(sw.view_location_id, '/%')
)
WHERE sq.quantity > 0
GROUP BY sw.id, sw.name, sw.code
ORDER BY sw.name;

-- عرض الكميات لكل منتج في كل موقع (للتأكد من التقسيم)
-- Show quantities per product per location (to verify division)
SELECT 
    pp.default_code as product_code,
    pt.name as product_name,
    sl.name as location_name,
    sw.name as warehouse_name,
    sq.quantity,
    sq.reserved_quantity
FROM stock_quant sq
JOIN product_product pp ON sq.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
JOIN stock_location sl ON sq.location_id = sl.id
LEFT JOIN stock_warehouse sw ON (
    sl.parent_path LIKE concat('%/', sw.view_location_id, '/%')
    OR sl.parent_path LIKE concat(sw.view_location_id, '/%')
)
WHERE sq.quantity > 0
ORDER BY sw.name, pp.default_code, sl.name
LIMIT 50;

