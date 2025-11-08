-- SQL Command to Remove Duplicates from sap_product_warehouse_info
-- This keeps the record with the latest last_sync_date (or highest ID if last_sync_date is NULL)
-- for each (product_id, warehouse_id, backend_id) combination

-- Method 1: Delete duplicates keeping the newest record by last_sync_date
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

-- Method 2: Alternative - Delete duplicates keeping the record with highest ID
-- Use this if last_sync_date is not reliable
/*
DELETE FROM sap_product_warehouse_info
WHERE id IN (
    SELECT id
    FROM (
        SELECT id,
               ROW_NUMBER() OVER (
                   PARTITION BY product_id, warehouse_id, backend_id 
                   ORDER BY id DESC
               ) as rn
        FROM sap_product_warehouse_info
    ) sub
    WHERE rn > 1
);
*/

-- Check duplicates before deletion (run this first to see how many will be deleted)
/*
SELECT 
    product_id, 
    warehouse_id, 
    backend_id, 
    COUNT(*) as duplicate_count,
    STRING_AGG(id::text, ', ') as record_ids
FROM sap_product_warehouse_info
GROUP BY product_id, warehouse_id, backend_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;
*/

-- Count total duplicates
/*
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
*/

