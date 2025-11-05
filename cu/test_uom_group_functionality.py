#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test UoM Group functionality on a single product
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

# Initialize Odoo
odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'lugal'])

def test_uom_groups():
    """Test UoM Group functionality"""
    
    registry = Registry('lugal')
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 80)
        print("Testing UoM Group Functionality")
        print("=" * 80)
        
        # 1. Find a product with multiple UoM prices (ADF00002)
        print("\n1. Finding test product (ADF00002)...")
        product = env['product.product'].search([
            ('default_code', 'ilike', 'ADF00002')
        ], limit=1)
        
        if not product:
            print("   ERROR: Product ADF00002 not found!")
            return
        
        print(f"   Found: {product.name} ({product.default_code})")
        
        # 2. Check if product has UoM Group
        print(f"\n2. Checking UoM Group...")
        extended_info = env['sap.product.extended'].search([
            ('product_id', '=', product.id)
        ], limit=1)
        
        if not extended_info:
            print("   WARNING: No SAP extended info found")
            print("   Creating extended info record...")
            # Try to create it
            backend = env['sap.backend'].search([], limit=1)
            if backend:
                extended_info = env['sap.product.extended'].create({
                    'product_id': product.id,
                    'backend_id': backend.id,
                })
                print(f"   Created extended info")
        
        if extended_info:
            print(f"   Extended Info ID: {extended_info.id}")
            print(f"   UoM Group: {extended_info.sap_uom_group_id.name if extended_info.sap_uom_group_id else 'None'}")
            print(f"   UoM Group Entry: {extended_info.sap_uom_group_entry}")
        
        # 3. Check available UoMs from pricelist
        print(f"\n3. Checking pricelist items...")
        pricelist = env['product.pricelist'].search([('name', '=', 'SAP Price List 1')], limit=1)
        
        if pricelist:
            items = env['product.pricelist.item'].search([
                ('pricelist_id', '=', pricelist.id),
                ('product_tmpl_id', '=', product.product_tmpl_id.id),
                ('applied_on', '=', '1_product'),
            ])
            
            print(f"   Found {len(items)} pricelist items")
            uom_ids = []
            for item in items:
                uom = item.product_packaging_id
                if uom:
                    uom_ids.append(uom.id)
                    print(f"   - {uom.name}: ${item.fixed_price:.2f}")
                else:
                    print(f"   - Base: ${item.fixed_price:.2f}")
        
        # 4. Create a fake sale order line to test
        print(f"\n4. Testing sale order line UoM restriction...")
        
        # Get partner
        partner = env['res.partner'].search([], limit=1)
        if not partner:
            print("   ERROR: No partner found")
            return
        
        # Create sale order
        order = env['sale.order'].create({
            'partner_id': partner.id,
        })
        print(f"   Created sale order: {order.name}")
        
        # Create sale order line
        line = env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product.id,
            'product_uom_qty': 1,
        })
        print(f"   Created sale order line")
        
        # Check available UoMs
        print(f"\n5. Checking available_uom_ids computation...")
        line._compute_available_uoms()
        print(f"   Available UoMs: {len(line.available_uom_ids)}")
        
        if line.available_uom_ids:
            print(f"   UoM List:")
            for uom in line.available_uom_ids[:10]:  # Show first 10
                print(f"     - {uom.name}")
        else:
            print(f"   WARNING: No UoMs available (fallback - allows all)")
        
        # 6. Check if sap_uom_group_id is computed
        print(f"\n6. Checking sap_uom_group_id...")
        line._compute_sap_uom_group()
        if line.sap_uom_group_id:
            print(f"   UoM Group: {line.sap_uom_group_id.name}")
            print(f"   Group has {len(line.sap_uom_group_id.uom_ids)} UoMs")
        else:
            print(f"   No UoM Group (fallback mode)")
        
        # 7. Test domain restriction
        print(f"\n7. Testing domain restriction...")
        domain_field = line._fields['product_uom_id']
        if hasattr(domain_field, 'domain'):
            print(f"   Domain: {domain_field.domain}")
        else:
            print(f"   No domain restriction")
        
        # Clean up
        print(f"\n8. Cleaning up...")
        order.unlink()
        print(f"   Sale order deleted")
        
        print("\n" + "=" * 80)
        print("Test Summary")
        print("=" * 80)
        print(f"✓ Product: {product.name}")
        print(f"✓ Extended Info: {'Yes' if extended_info else 'No'}")
        print(f"✓ UoM Group: {extended_info.sap_uom_group_id.name if extended_info and extended_info.sap_uom_group_id else 'None'}")
        print(f"✓ Pricelist Items: {len(items) if pricelist else 0}")
        print(f"✓ Available UoMs: {len(line.available_uom_ids)}")
        print(f"✓ Domain Restriction: {'Active' if line.available_uom_ids else 'Fallback (all UoMs)'}")
        
        print("\n" + "=" * 80)

if __name__ == '__main__':
    try:
        test_uom_groups()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()


