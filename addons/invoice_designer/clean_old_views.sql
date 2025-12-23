-- SQL Script to Clean Old Invoice Designer Views
-- Run this in PostgreSQL to remove cached views

-- Delete old views for invoice_designer module
DELETE FROM ir_ui_view 
WHERE model = 'invoice.template.designer' 
  AND name NOT IN ('invoice.template.designer.tree', 'invoice.template.designer.form.v2');

-- Delete old actions
DELETE FROM ir_act_window 
WHERE res_model = 'invoice.template.designer'
  AND id NOT IN (
    SELECT id FROM ir_act_window 
    WHERE res_model = 'invoice.template.designer' 
    ORDER BY create_date DESC 
    LIMIT 1
  );

-- Clear cache
DELETE FROM ir_model_data 
WHERE module = 'invoice_designer' 
  AND model = 'ir.ui.view'
  AND name NOT IN ('view_invoice_template_designer_tree', 'view_invoice_template_designer_form_v2');

-- Show remaining views
SELECT id, name, model, arch_db 
FROM ir_ui_view 
WHERE model = 'invoice.template.designer';

