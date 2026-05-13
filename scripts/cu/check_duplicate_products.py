#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check for duplicate products with A, B suffixes
فحص المنتجات المكررة التي تحتوي على A و B
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

def check_duplicates():
    """Check for duplicate products"""
    
    # Initialize Odoo
    odoo.tools.config.parse_config(['-c', config_file, '-d', db_name])
    
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("فحص المنتجات المكررة - Checking Duplicate Products")
        print("=" * 80)
        
        ProductTemplate = env['product.template']
        
        # 1. Find products with " A" in name
        products_with_a = ProductTemplate.search([('name', 'ilike', ' A')])
        print(f"\n📦 منتجات تحتوي على ' A' في الاسم: {len(products_with_a)}")
        
        # 2. Find products with " B" in name
        products_with_b = ProductTemplate.search([('name', 'ilike', ' B')])
        print(f"📦 منتجات تحتوي على ' B' في الاسم: {len(products_with_b)}")
        
        # 3. Find products ending with " A" or " B"
        products_ending_a = ProductTemplate.search([
            '|',
            ('name', '=ilike', '% A'),
            ('name', '=ilike', '% a')
        ])
        print(f"📦 منتجات تنتهي بـ ' A': {len(products_ending_a)}")
        
        products_ending_b = ProductTemplate.search([
            '|',
            ('name', '=ilike', '% B'),
            ('name', '=ilike', '% b')
        ])
        print(f"📦 منتجات تنتهي بـ ' B': {len(products_ending_b)}")
        
        # 4. Show samples
        print("\n" + "=" * 80)
        print("عينات من المنتجات - Sample Products")
        print("=" * 80)
        
        all_suspect_products = (products_ending_a | products_ending_b).sorted(key=lambda p: p.name)
        
        print(f"\n📋 إجمالي المنتجات المشتبه بها: {len(all_suspect_products)}")
        print("\nعينة من أول 50 منتج:")
        print("-" * 80)
        
        for idx, product in enumerate(all_suspect_products[:50], 1):
            code = product.default_code or 'N/A'
            active = '✓' if product.active else '✗'
            sale_ok = '✓' if product.sale_ok else '✗'
            
            # Check if there's a "parent" product without A/B
            base_name = product.name
            if base_name.endswith(' A') or base_name.endswith(' a'):
                base_name = base_name[:-2].strip()
            elif base_name.endswith(' B') or base_name.endswith(' b'):
                base_name = base_name[:-2].strip()
            
            parent_exists = ProductTemplate.search([('name', '=', base_name)], limit=1)
            parent_mark = '⚠️ Parent exists!' if parent_exists else ''
            
            print(f"{idx:3}. [{active}] {product.name[:60]:60} | Code: {code:15} | Sale: {sale_ok} {parent_mark}")
        
        if len(all_suspect_products) > 50:
            print(f"\n... و {len(all_suspect_products) - 50} منتج آخر")
        
        # 5. Analyze duplicates
        print("\n" + "=" * 80)
        print("تحليل المنتجات المكررة - Duplicate Analysis")
        print("=" * 80)
        
        duplicates_found = []
        
        for product in all_suspect_products:
            base_name = product.name
            if base_name.endswith(' A') or base_name.endswith(' a'):
                base_name = base_name[:-2].strip()
            elif base_name.endswith(' B') or base_name.endswith(' b'):
                base_name = base_name[:-2].strip()
            
            # Find all related products
            related = ProductTemplate.search([
                '|', '|', '|',
                ('name', '=', base_name),
                ('name', '=', base_name + ' A'),
                ('name', '=', base_name + ' a'),
                '|', '|',
                ('name', '=', base_name + ' B'),
                ('name', '=', base_name + ' b'),
                ('name', '=', base_name + ' C')
            ])
            
            if len(related) > 1:
                duplicates_found.append({
                    'base_name': base_name,
                    'products': related
                })
        
        # Remove duplicate entries in our analysis
        unique_groups = {}
        for dup in duplicates_found:
            if dup['base_name'] not in unique_groups:
                unique_groups[dup['base_name']] = dup
        
        print(f"\n📊 مجموعات المنتجات المكررة: {len(unique_groups)}")
        print("\nأول 20 مجموعة:")
        print("-" * 80)
        
        for idx, (base_name, dup_group) in enumerate(list(unique_groups.items())[:20], 1):
            print(f"\n{idx}. المنتج الأساسي: {base_name}")
            for prod in dup_group['products']:
                code = prod.default_code or 'N/A'
                active = '✓' if prod.active else '✗'
                print(f"   [{active}] {prod.name:60} | Code: {code:15} | ID: {prod.id}")
        
        # 6. Statistics
        print("\n" + "=" * 80)
        print("الإحصائيات - Statistics")
        print("=" * 80)
        
        total_products = ProductTemplate.search_count([])
        active_products = ProductTemplate.search_count([('active', '=', True)])
        
        print(f"\n📊 إجمالي المنتجات في النظام: {total_products}")
        print(f"📊 المنتجات النشطة: {active_products}")
        print(f"📊 المنتجات المشتبه بأنها مكررة (تنتهي بـ A/B): {len(all_suspect_products)}")
        print(f"📊 مجموعات التكرار: {len(unique_groups)}")
        
        active_suspects = len([p for p in all_suspect_products if p.active])
        print(f"📊 المنتجات المشتبه بها النشطة: {active_suspects}")
        print(f"📊 المنتجات المشتبه بها غير النشطة: {len(all_suspect_products) - active_suspects}")
        
        print("\n" + "=" * 80)
        print("✅ اكتمل الفحص - Check Complete!")
        print("=" * 80)
        
        print("\n💡 الخطوات التالية:")
        print("   1. راجع المنتجات المكررة أعلاه")
        print("   2. قرر ما إذا كنت تريد حذف المنتجات المكررة")
        print("   3. إذا أردت الحذف، سأقوم بإنشاء سكريبت للحذف")

if __name__ == '__main__':
    try:
        check_duplicates()
    except Exception as e:
        print(f"\n❌ خطأ: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

