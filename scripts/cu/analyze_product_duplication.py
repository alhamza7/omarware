#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze product duplication by default_code
تحليل تكرار المنتجات بناءً على الكود الفريد
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

def analyze_duplicates():
    """Analyze product duplication"""
    
    # Initialize Odoo
    odoo.tools.config.parse_config(['-c', config_file, '-d', db_name])
    
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("تحليل تكرار المنتجات - Product Duplication Analysis")
        print("=" * 80)
        
        ProductTemplate = env['product.template']
        
        # Get all products
        all_products = ProductTemplate.search([])
        total_count = len(all_products)
        
        print(f"\n📦 إجمالي المنتجات في النظام: {total_count}")
        print(f"📦 العدد المتوقع: 12,745")
        print(f"⚠️  الفرق: {total_count - 12745} منتج زائد!")
        
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
        
        print(f"\n📊 منتجات لها كود فريد: {len(products_by_code)} كود مختلف")
        print(f"📊 منتجات بدون كود: {len(products_without_code)}")
        
        # Find duplicates
        duplicated_codes = {code: prods for code, prods in products_by_code.items() if len(prods) > 1}
        unique_codes = {code: prods for code, prods in products_by_code.items() if len(prods) == 1}
        
        print(f"\n🔴 أكواد مكررة: {len(duplicated_codes)} كود")
        print(f"🟢 أكواد فريدة: {len(unique_codes)} كود")
        
        # Calculate total duplicates
        total_duplicate_products = sum(len(prods) for prods in duplicated_codes.values())
        total_unique_products = len(unique_codes)
        
        print(f"\n📊 مجموع المنتجات المكررة: {total_duplicate_products}")
        print(f"📊 المنتجات الفريدة (كود واحد): {total_unique_products}")
        print(f"📊 المنتجات بدون كود: {len(products_without_code)}")
        print(f"📊 الإجمالي: {total_duplicate_products + total_unique_products + len(products_without_code)}")
        
        # Show most duplicated codes
        print("\n" + "=" * 80)
        print("أكثر الأكواد تكراراً - Most Duplicated Codes")
        print("=" * 80)
        
        sorted_duplicates = sorted(duplicated_codes.items(), key=lambda x: len(x[1]), reverse=True)
        
        print(f"\nأول 30 كود مكرر:")
        print("-" * 80)
        
        for idx, (code, prods) in enumerate(sorted_duplicates[:30], 1):
            count = len(prods)
            sample_name = prods[0].name[:50] if prods else 'N/A'
            print(f"{idx:3}. [{count} نسخ] {code:15} | {sample_name}")
            
            # Show all IDs for heavily duplicated products
            if count > 5:
                print(f"     IDs: {', '.join(str(p.id) for p in prods)}")
        
        # Analyze duplication patterns
        print("\n" + "=" * 80)
        print("تحليل أنماط التكرار - Duplication Patterns")
        print("=" * 80)
        
        duplication_stats = defaultdict(int)
        for code, prods in duplicated_codes.items():
            count = len(prods)
            duplication_stats[count] += 1
        
        print("\nتوزيع التكرار:")
        for count in sorted(duplication_stats.keys(), reverse=True):
            num_codes = duplication_stats[count]
            total_prods = count * num_codes
            print(f"  {count:2} نسخ: {num_codes:4} كود ({total_prods:5} منتج)")
        
        # Calculate expected vs actual
        print("\n" + "=" * 80)
        print("الحساب المتوقع - Expected Calculation")
        print("=" * 80)
        
        # If we keep only one product per code
        expected_products = len(products_by_code) + len(products_without_code)
        products_to_delete = total_count - expected_products
        
        print(f"\n📊 عدد الأكواد الفريدة: {len(products_by_code)}")
        print(f"📊 منتجات بدون كود: {len(products_without_code)}")
        print(f"📊 العدد المتوقع بعد إزالة التكرار: {expected_products}")
        print(f"🗑️  المنتجات التي يجب حذفها: {products_to_delete}")
        
        print(f"\n✅ العدد المتوقع ({expected_products}) قريب من العدد الفعلي ({12745})؟")
        if abs(expected_products - 12745) < 100:
            print("   ✓ نعم! المشكلة هي التكرار فقط")
        else:
            print(f"   ⚠️  لا، لا يزال هناك فرق: {abs(expected_products - 12745)}")
            print(f"   قد تكون هناك منتجات بدون كود مكررة أيضاً")
        
        # Sample of duplicated products
        print("\n" + "=" * 80)
        print("عينة من المنتجات المكررة - Sample Duplicates")
        print("=" * 80)
        
        for idx, (code, prods) in enumerate(sorted_duplicates[:10], 1):
            print(f"\n{idx}. الكود: {code} ({len(prods)} نسخ)")
            for i, prod in enumerate(prods, 1):
                active = '✓' if prod.active else '✗'
                print(f"   [{active}] ID: {prod.id:6} | {prod.name[:60]}")
        
        # Check products without code for duplicates
        print("\n" + "=" * 80)
        print("تحليل المنتجات بدون كود - Products Without Code Analysis")
        print("=" * 80)
        
        print(f"\n📊 منتجات بدون كود: {len(products_without_code)}")
        
        # Group by name
        no_code_by_name = defaultdict(list)
        for prod in products_without_code:
            no_code_by_name[prod.name].append(prod)
        
        duplicate_no_code = {name: prods for name, prods in no_code_by_name.items() if len(prods) > 1}
        
        print(f"🔴 أسماء مكررة (بدون كود): {len(duplicate_no_code)}")
        
        if duplicate_no_code:
            print("\nأول 10 أسماء مكررة:")
            for idx, (name, prods) in enumerate(list(duplicate_no_code.items())[:10], 1):
                print(f"{idx:3}. [{len(prods)} نسخ] {name[:60]}")
        
        # Summary
        print("\n" + "=" * 80)
        print("الخلاصة - Summary")
        print("=" * 80)
        
        print(f"\n🔍 السبب الرئيسي للزيادة:")
        print(f"   - إجمالي المنتجات: {total_count}")
        print(f"   - منتجات مكررة (لها نفس الكود): {total_duplicate_products}")
        print(f"   - نسبة التكرار: {(total_duplicate_products / total_count * 100):.1f}%")
        
        print(f"\n💡 التوصيات:")
        print(f"   1. حذف {products_to_delete} منتج مكرر")
        print(f"   2. الإبقاء على نسخة واحدة فقط من كل كود")
        print(f"   3. مراجعة عملية الاستيراد من SAP لمنع التكرار المستقبلي")
        
        print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        analyze_duplicates()
    except Exception as e:
        print(f"\n❌ خطأ: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

