# -*- coding: utf-8 -*-

def migrate(cr, version):
    """Remove invoice_type column from print_customer_label_wizard tables"""
    import logging
    _logger = logging.getLogger(__name__)
    
    # Check if column exists before dropping from wizard table
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='print_customer_label_wizard' 
        AND column_name='invoice_type'
    """)
    if cr.fetchone():
        try:
            cr.execute("ALTER TABLE print_customer_label_wizard DROP COLUMN invoice_type")
            _logger.info("Dropped invoice_type column from print_customer_label_wizard")
        except Exception as e:
            _logger.warning("Error dropping invoice_type from print_customer_label_wizard: %s", str(e))
    
    # Also check and drop from wizard line table
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='print_customer_label_wizard_line' 
        AND column_name='invoice_type'
    """)
    if cr.fetchone():
        try:
            cr.execute("ALTER TABLE print_customer_label_wizard_line DROP COLUMN invoice_type")
            _logger.info("Dropped invoice_type column from print_customer_label_wizard_line")
        except Exception as e:
            _logger.warning("Error dropping invoice_type from print_customer_label_wizard_line: %s", str(e))




