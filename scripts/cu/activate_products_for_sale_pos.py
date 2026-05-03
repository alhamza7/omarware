#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to activate products for Sale and POS
تفعيل المنتجات للبيع ونقاط البيع
"""

import sys
import os
import io

# Fix encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add Odoo to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

# Configuration
config_file = 'odoo.conf'
db_name = 'lugal'

def activate_products():
    """Activate products for sale and POS"""
    
    # Initialize Odoo
    odoo.tools.config.parse_config(['-c', config_file, '-d', db_name])
    
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("فحص وتفعيل المنتجات للبيع ونقاط البيع")
        print("Checking and Activating Products for Sale and POS")
        print("=" * 80)
        
        # Get all product templates
        ProductTemplate = env['product.template']
        all_products = ProductTemplate.search([])
        
        print(f"\n📦 إجمالي المنتجات: {len(all_products)} products")
        
        # Find products not activated for sale
        products_not_for_sale = ProductTemplate.search([('sale_ok', '=', False)])
        print(f"❌ منتجات غير مفعلة للبيع: {len(products_not_for_sale)} products")
        
        # Find products not available in POS
        products_not_in_pos = ProductTemplate.search([('available_in_pos', '=', False)])
        print(f"❌ منتجات غير متاحة في POS: {len(products_not_in_pos)} products")
        
        print("\n" + "=" * 80)
        print("تفعيل المنتجات - Activating Products")
        print("=" * 80)
        
        # Activate all products for sale and POS
        products_to_update = ProductTemplate.search([
            '|',
            ('sale_ok', '=', False),
            ('available_in_pos', '=', False)
        ])
        
        if products_to_update:
            print(f"\n🔧 تحديث {len(products_to_update)} منتج...")
            print(f"   Updating {len(products_to_update)} products...")
            
            count = 0
            for product in products_to_update:
                try:
                    values = {}
                    if not product.sale_ok:
                        values['sale_ok'] = True
                    if not product.available_in_pos:
                        values['available_in_pos'] = True
                    
                    if values:
                        product.write(values)
                        count += 1
                        
                        if count <= 10:  # Show first 10 products
                            status = []
                            if 'sale_ok' in values:
                                status.append("✓ Sale")
                            if 'available_in_pos' in values:
                                status.append("✓ POS")
                            print(f"   [{count}] {product.name} ({product.default_code or 'N/A'}) - {' | '.join(status)}")
                        elif count == 11:
                            print(f"   ... (المزيد من المنتجات قيد التحديث)")
                    
                except Exception as e:
                    print(f"   ❌ خطأ في تحديث {product.name}: {str(e)}")
            
            cr.commit()
            
            print(f"\n✅ تم تفعيل {count} منتج بنجاح!")
            print(f"   Successfully activated {count} products!")
            
        else:
            print("\n✅ جميع المنتجات مفعلة بالفعل!")
            print("   All products are already activated!")
        
        # Final verification
        print("\n" + "=" * 80)
        print("التحقق النهائي - Final Verification")
        print("=" * 80)
        
        products_not_for_sale = ProductTemplate.search([('sale_ok', '=', False)])
        products_not_in_pos = ProductTemplate.search([('available_in_pos', '=', False)])
        
        print(f"\n✓ منتجات مفعلة للبيع: {len(all_products) - len(products_not_for_sale)}/{len(all_products)}")
        print(f"✓ منتجات متاحة في POS: {len(all_products) - len(products_not_in_pos)}/{len(all_products)}")
        
        if products_not_for_sale:
            print(f"\n⚠️  لا تزال {len(products_not_for_sale)} منتجات غير مفعلة للبيع:")
            for prod in products_not_for_sale[:5]:
                print(f"   - {prod.name} ({prod.default_code or 'N/A'})")
        
        if products_not_in_pos:
            print(f"\n⚠️  لا تزال {len(products_not_in_pos)} منتجات غير متاحة في POS:")
            for prod in products_not_in_pos[:5]:
                print(f"   - {prod.name} ({prod.default_code or 'N/A'})")
        
        print("\n" + "=" * 80)
        print("✅ اكتمل التفعيل - Activation Complete!")
        print("=" * 80)

if __name__ == '__main__':
    try:
        activate_products()
    except Exception as e:
        print(f"\n❌ خطأ: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

