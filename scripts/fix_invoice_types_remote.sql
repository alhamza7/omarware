-- تصحيح قيم invoice_type القديمة في قاعدة البيانات
-- نفذ هذا على السيرفر البعيد

-- التحقق من وجود بيانات قديمة
SELECT invoice_type, COUNT(*) 
FROM pos_perfume_order 
WHERE invoice_type IS NOT NULL 
GROUP BY invoice_type;

SELECT invoice_type, COUNT(*) 
FROM sale_order 
WHERE invoice_type IS NOT NULL 
GROUP BY invoice_type;

-- إذا وجدت قيم قديمة (customer_shop, delivery_companies, إلخ)، نفذ التصحيح:

-- في pos_perfume_order
UPDATE pos_perfume_order SET invoice_type = '1' WHERE invoice_type = 'customer_shop';
UPDATE pos_perfume_order SET invoice_type = '2' WHERE invoice_type = 'delivery_companies';
UPDATE pos_perfume_order SET invoice_type = '3' WHERE invoice_type IN ('ta3keebat', 'transport');
UPDATE pos_perfume_order SET invoice_type = '4' WHERE invoice_type IN ('dalmari', 'delivery');
UPDATE pos_perfume_order SET invoice_type = '5' WHERE invoice_type = 'nbs';
UPDATE pos_perfume_order SET invoice_type = '6' WHERE invoice_type IN ('shoroja', 'shorja');
UPDATE pos_perfume_order SET invoice_type = '7' WHERE invoice_type = 'na';
UPDATE pos_perfume_order SET invoice_type = '8' WHERE invoice_type IN ('promotion_offices', 'shorja_offices');

-- في sale_order
UPDATE sale_order SET invoice_type = '1' WHERE invoice_type = 'customer_shop';
UPDATE sale_order SET invoice_type = '2' WHERE invoice_type = 'delivery_companies';
UPDATE sale_order SET invoice_type = '3' WHERE invoice_type IN ('ta3keebat', 'transport');
UPDATE sale_order SET invoice_type = '4' WHERE invoice_type IN ('dalmari', 'delivery');
UPDATE sale_order SET invoice_type = '5' WHERE invoice_type = 'nbs';
UPDATE sale_order SET invoice_type = '6' WHERE invoice_type IN ('shoroja', 'shorja');
UPDATE sale_order SET invoice_type = '7' WHERE invoice_type = 'na';
UPDATE sale_order SET invoice_type = '8' WHERE invoice_type IN ('promotion_offices', 'shorja_offices');

