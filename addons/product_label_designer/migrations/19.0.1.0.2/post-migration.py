# -*- coding: utf-8 -*-

def migrate(cr, version):
    """Update existing customer label templates to disable labels by default"""
    # Update all templates to have labels disabled
    cr.execute("""
        UPDATE customer_label_template
        SET show_phone_label = false,
            show_mobile_label = false,
            show_invoice_type_label = false,
            show_note_label = false
        WHERE show_phone_label = true
           OR show_mobile_label = true
           OR show_invoice_type_label = true
           OR show_note_label = true;
    """)
    
    # Also set NULL values to false
    cr.execute("""
        UPDATE customer_label_template
        SET show_phone_label = false
        WHERE show_phone_label IS NULL;
    """)
    
    cr.execute("""
        UPDATE customer_label_template
        SET show_mobile_label = false
        WHERE show_mobile_label IS NULL;
    """)
    
    cr.execute("""
        UPDATE customer_label_template
        SET show_invoice_type_label = false
        WHERE show_invoice_type_label IS NULL;
    """)
    
    cr.execute("""
        UPDATE customer_label_template
        SET show_note_label = false
        WHERE show_note_label IS NULL;
    """)

