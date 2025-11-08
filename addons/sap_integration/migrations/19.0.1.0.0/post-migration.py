# -*- coding: utf-8 -*-

def migrate(cr, version):
    """
    Add sap_synced field to res_partner if it doesn't exist
    """
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='res_partner' AND column_name='sap_synced'
    """)
    
    if not cr.fetchone():
        cr.execute("""
            ALTER TABLE res_partner 
            ADD COLUMN sap_synced BOOLEAN DEFAULT FALSE
        """)
        cr.execute("""
            CREATE INDEX IF NOT EXISTS res_partner_sap_synced_idx 
            ON res_partner(sap_synced)
        """)

