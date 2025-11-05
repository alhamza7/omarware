#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Delete duplicate products - keep only the oldest one
حذف المنتجات المكررة - الإبقاء على الأقدم فقط
"""

import sys
import os
import io
from collections import defaultdict

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

def delete_duplicates():
    """Delete duplicate products keeping the oldest one"""
    
    # Initialize Odoo
    odoo.tools.config.parse_config(['-c', config_file, '-d', db_name])
    
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("حذف المنتجات المكررة - Delete Duplicate Products")
        print("=" * 80)
        
        ProductTemplate = env['product.template']
        
        # Get all products
        all_products = ProductTemplate.search([], order='default_code, id')
        total_count = len(all_products)
        
        print(f"\n📦 إجمالي المنتجات: {total_count}")
        
        # Group by default_code
        print("\n" + "=" * 80)
        print("تجميع المنتجات حسب الكود - Grouping by Code")
        print("=" * 80)
        
        products_by_code = defaultdict(list)
        products_without_code = []
        
        for product in all_products:
            if product.default_code:
                products_by_code[product.default_code].append(product)
            else:
                products_without_code.append(product)
        
        # Find duplicates
        duplicated_codes = {code: prods for code, prods in products_by_code.items() if len(prods) > 1}
        
        print(f"\n🔴 أكواد مكررة: {len(duplicated_codes)}")
        
        # Collect products to delete
        products_to_delete = []
        
        for code, prods in duplicated_codes.items():
            # Sort by ID (oldest first)
            sorted_prods = sorted(prods, key=lambda p: p.id)
            
            # Keep the first one (oldest), delete the rest
            to_delete = sorted_prods[1:]
            products_to_delete.extend(to_delete)
        
        print(f"🗑️  المنتجات المقرر حذفها: {len(products_to_delete)}")
        
        # Show sample
        print("\n" + "=" * 80)
        print("عينة من المنتجات المقرر حذفها - Sample to be Deleted")
        print("=" * 80)
        
        print("\nأول 20 منتج سيتم حذفه:")
        for idx, prod in enumerate(products_to_delete[:20], 1):
            code = prod.default_code or 'N/A'
            print(f"{idx:3}. ID: {prod.id:6} | Code: {code:15} | {prod.name[:50]}")
        
        if len(products_to_delete) > 20:
            print(f"\n... و {len(products_to_delete) - 20} منتج آخر")
        
        # Confirm deletion
        print("\n" + "=" * 80)
        print("⚠️  تأكيد الحذف - Confirm Deletion")
        print("=" * 80)
        
        print(f"\nسيتم حذف {len(products_to_delete)} منتج مكرر")
        print(f"العدد المتبقي بعد الحذف: {total_count - len(products_to_delete)}")
        
        response = input("\nهل تريد المتابعة؟ (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y', 'نعم']:
            print("\n❌ تم إلغاء العملية")
            return
        
        # Perform deletion
        print("\n" + "=" * 80)
        print("🗑️  جاري الحذف - Deleting...")
        print("=" * 80)
        
        deleted_count = 0
        errors = []
        
        # Delete in batches
        batch_size = 100
        total_batches = (len(products_to_delete) + batch_size - 1) // batch_size
        
        for i in range(0, len(products_to_delete), batch_size):
            batch = products_to_delete[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            try:
                print(f"\nحذف الدفعة {batch_num}/{total_batches} ({len(batch)} منتج)...")
                
                # Get IDs
                ids_to_delete = [p.id for p in batch]
                
                # Delete using unlink
                ProductTemplate.browse(ids_to_delete).unlink()
                
                deleted_count += len(batch)
                print(f"✅ تم حذف {len(batch)} منتج بنجاح")
                
                # Commit after each batch
                cr.commit()
                
            except Exception as e:
                error_msg = f"خطأ في حذف الدفعة {batch_num}: {str(e)}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)
                # Continue with next batch
        
        # Final report
        print("\n" + "=" * 80)
        print("النتيجة النهائية - Final Result")
        print("=" * 80)
        
        print(f"\n✅ تم حذف: {deleted_count} منتج")
        print(f"❌ أخطاء: {len(errors)}")
        
        if errors:
            print("\nالأخطاء:")
            for error in errors:
                print(f"  - {error}")
        
        # Verify final count
        final_count = ProductTemplate.search_count([])
        print(f"\n📊 عدد المنتجات قبل الحذف: {total_count}")
        print(f"📊 عدد المنتجات بعد الحذف: {final_count}")
        print(f"📊 الفرق: {total_count - final_count}")
        
        print("\n" + "=" * 80)
        print("✅ اكتملت العملية - Operation Complete!")
        print("=" * 80)

if __name__ == '__main__':
    try:
        delete_duplicates()
    except KeyboardInterrupt:
        print("\n\n❌ تم إلغاء العملية من قبل المستخدم")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطأ: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

