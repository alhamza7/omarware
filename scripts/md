-- Fix name_arabic field type issue
-- The field should be text, not jsonb

-- Check current type
SELECT column_name, data_type, udt_name 
FROM information_schema.columns 
WHERE table_name = 'product_template' 
  AND column_name = 'name_arabic';

-- If it's jsonb, we need to convert it
-- First, backup the data
CREATE TABLE IF NOT EXISTS name_arabic_backup AS 
SELECT id, name_arabic::text as name_arabic_text 
FROM product_template 
WHERE name_arabic IS NOT NULL;

-- Drop the column if it causes issues
-- ALTER TABLE product_template DROP COLUMN IF EXISTS name_arabic CASCADE;

-- Recreate as plain text
-- ALTER TABLE product_template ADD COLUMN name_arabic VARCHAR;

-- For product_product
SELECT column_name, data_type, udt_name 
FROM information_schema.columns 
WHERE table_name = 'product_product' 
  AND column_name = 'name_arabic';




