#!/usr/bin/env python3
"""
تعيين شركة لجميع الفولدرات التي ليس لديها company_id
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', 'odoo_local.conf'])
db_name = odoo.tools.config.get('db_name') or 'lugal_local'
if isinstance(db_name, list):
    db_name = db_name[0] if db_name else 'lugal_local'

print(f"🏢 تعيين شركة للفولدرات - قاعدة البيانات: {db_name}\n")

with Registry(db_name).cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get default company
    default_company = env['res.partner'].search([
        ('is_company', '=', True),
        ('active', '=', True)
    ], limit=1)
    
    if not default_company:
        print("❌ لا توجد شركة في النظام!")
        sys.exit(1)
    
    print(f"🏢 الشركة الافتراضية: {default_company.name} (ID: {default_company.id})\n")
    
    # Get folders without company_id
    folders_without_company = env['nbs.document.folder'].search([
        ('company_id', '=', False),
        ('active', '=', True)
    ])
    
    print(f"📊 عدد الفولدرات بدون شركة: {len(folders_without_company)}\n")
    
    if not folders_without_company:
        print("✅ جميع الفولدرات لديها شركة!")
        sys.exit(0)
    
    updated_count = 0
    
    for folder in folders_without_company:
        print(f"📁 {folder.name} (ID: {folder.id})")
        
        # Assign default company
        folder.write({'company_id': default_company.id})
        
        # Check documents in this folder
        docs = env['nbs.document'].search([('folder_id', '=', folder.id)])
        print(f"   ├─ تم تعيين الشركة: {default_company.name}")
        print(f"   └─ عدد المستندات في الفولدر: {len(docs)}")
        
        if docs:
            print(f"      └─ سيتم تحديث company_id لـ {len(docs)} مستند تلقائياً")
        
        updated_count += 1
    
    # Commit changes
    cr.commit()
    
    # Trigger recomputation of company_id for all documents
    print(f"\n🔄 إعادة حساب company_id للمستندات...")
    all_docs = env['nbs.document'].search([])
    all_docs._compute_company_id()
    cr.commit()
    
    print(f"\n✅ اكتمل!")
    print(f"   📁 تم تحديث {updated_count} فولدر")
    print(f"   📄 جميع المستندات الآن يجب أن يكون لديها company_id")
