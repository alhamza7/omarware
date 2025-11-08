-- ============================================================
-- أمر SQL مباشر لحذف التكرارات من sap_product_warehouse_info
-- ============================================================

-- الخطوة 1: التحقق من التكرارات (اختياري - للتأكد قبل الحذف)
SELECT 
    product_id, 
    warehouse_id, 
    backend_id, 
    COUNT(*) as duplicate_count,
    STRING_AGG(id::text, ', ' ORDER BY last_sync_date DESC NULLS LAST, id DESC) as record_ids
FROM sap_product_warehouse_info
GROUP BY product_id, warehouse_id, backend_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 20;

-- الخطوة 2: عد التكرارات التي سيتم حذفها
SELECT COUNT(*) as total_duplicates_to_remove
FROM (
    SELECT id,
           ROW_NUMBER() OVER (
               PARTITION BY product_id, warehouse_id, backend_id 
               ORDER BY last_sync_date DESC NULLS LAST, id DESC
           ) as rn
    FROM sap_product_warehouse_info
) sub
WHERE rn > 1;

-- الخطوة 3: حذف التكرارات (يبقي على السجل الأحدث حسب last_sync_date)
-- ⚠️ تحذير: هذا الأمر سيحذف البيانات! تأكد من عمل backup أولاً
DELETE FROM sap_product_warehouse_info
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY product_id, warehouse_id, backend_id 
                   ORDER BY last_sync_date DESC NULLS LAST, id DESC
               ) as rn
        FROM sap_product_warehouse_info
    ) sub
    WHERE rn > 1
);

-- الخطوة 4: التحقق من النتيجة (بعد الحذف)
SELECT 
    product_id, 
    warehouse_id, 
    backend_id, 
    COUNT(*) as remaining_count
FROM sap_product_warehouse_info
GROUP BY product_id, warehouse_id, backend_id
HAVING COUNT(*) > 1;

-- إذا كانت النتيجة فارغة، يعني تم حذف جميع التكرارات بنجاح ✅

