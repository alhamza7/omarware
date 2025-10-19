#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for SAP Integration Import

This script tests the import functionality to ensure
that res.partner records are created correctly.

Usage:
    From Odoo shell: python test_import.py
    Or from Python shell:
        import test_import
        test_import.test_partner_import(env)
"""

import logging

_logger = logging.getLogger(__name__)


def test_partner_import(env):
    """
    Test importing partners from SAP
    
    This will verify that:
    1. Binding records (sap.res.partner) are created
    2. Base records (res.partner) are created
    3. Both are linked correctly
    """
    print("\n" + "="*60)
    print("🧪 Testing SAP Partner Import")
    print("="*60 + "\n")
    
    # Step 1: Get or create backend
    print("📋 Step 1: Getting SAP Backend...")
    backend = env['sap.backend'].search([('active', '=', True)], limit=1)
    
    if not backend:
        print("❌ No active SAP backend found!")
        print("   Please create a backend first in Settings > SAP Integration > Backends")
        return False
    
    print(f"✅ Found backend: {backend.name}")
    print(f"   URL: {backend.base_url}")
    print(f"   Status: {backend.connection_status}")
    
    # Step 2: Test connection
    print("\n📋 Step 2: Testing connection...")
    if backend.connection_status != 'connected':
        print("⚠️  Backend not connected. Testing connection...")
        try:
            backend.test_connection()
            print("✅ Connection successful!")
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False
    else:
        print("✅ Backend already connected")
    
    # Step 3: Count existing records
    print("\n📋 Step 3: Counting existing records...")
    partner_count_before = env['res.partner'].search_count([])
    binding_count_before = env['sap.res.partner'].search_count([])
    
    print(f"   res.partner count: {partner_count_before}")
    print(f"   sap.res.partner count: {binding_count_before}")
    
    # Step 4: Import a batch of partners
    print("\n📋 Step 4: Importing partners from SAP...")
    print("   (This may take a moment...)")
    
    try:
        # Import with small batch size for testing
        result = env['sap.res.partner'].import_batch(backend, filters=None)
        
        print(f"\n✅ Import completed!")
        print(f"   📊 Imported: {result.get('imported', 0)}")
        print(f"   ❌ Errors: {result.get('errors', 0)}")
        
    except Exception as e:
        print(f"\n❌ Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Count records after import
    print("\n📋 Step 5: Verifying imported records...")
    partner_count_after = env['res.partner'].search_count([])
    binding_count_after = env['sap.res.partner'].search_count([])
    
    new_partners = partner_count_after - partner_count_before
    new_bindings = binding_count_after - binding_count_before
    
    print(f"   res.partner count: {partner_count_after} (+{new_partners})")
    print(f"   sap.res.partner count: {binding_count_after} (+{new_bindings})")
    
    # Step 6: Verify the data
    print("\n📋 Step 6: Checking data integrity...")
    
    # Check that all bindings have odoo_id
    bindings_without_partner = env['sap.res.partner'].search([
        ('odoo_id', '=', False)
    ])
    
    if bindings_without_partner:
        print(f"   ❌ Found {len(bindings_without_partner)} bindings without odoo_id!")
        print("   This is the original problem we fixed.")
        return False
    else:
        print("   ✅ All bindings have odoo_id")
    
    # Step 7: Display sample data
    print("\n📋 Step 7: Sample imported data:")
    sample_bindings = env['sap.res.partner'].search([], limit=3, order='id desc')
    
    if sample_bindings:
        for i, binding in enumerate(sample_bindings, 1):
            print(f"\n   📄 Sample {i}:")
            print(f"      SAP CardCode: {binding.external_id}")
            print(f"      Partner Name: {binding.odoo_id.name if binding.odoo_id else 'N/A'}")
            print(f"      Email: {binding.email or 'N/A'}")
            print(f"      Phone: {binding.phone or 'N/A'}")
            print(f"      odoo_id: {binding.odoo_id.id if binding.odoo_id else 'N/A'}")
    else:
        print("   ⚠️  No bindings found")
    
    # Step 8: Verify res.partner records exist
    print("\n📋 Step 8: Verifying res.partner records...")
    
    for binding in sample_bindings[:3]:
        partner = binding.odoo_id
        if partner:
            # Verify partner exists in res.partner
            partner_exists = env['res.partner'].search([
                ('id', '=', partner.id)
            ])
            if partner_exists:
                print(f"   ✅ Partner {partner.name} exists in res.partner")
            else:
                print(f"   ❌ Partner {partner.name} NOT found in res.partner!")
        else:
            print(f"   ❌ Binding {binding.external_id} has no odoo_id!")
    
    # Final summary
    print("\n" + "="*60)
    print("📊 IMPORT TEST SUMMARY")
    print("="*60)
    print(f"✅ Backend: {backend.name}")
    print(f"✅ Connection: {backend.connection_status}")
    print(f"✅ New Partners: {new_partners}")
    print(f"✅ New Bindings: {new_bindings}")
    print(f"✅ Data Integrity: {'OK' if not bindings_without_partner else 'FAILED'}")
    
    if new_partners == new_bindings and not bindings_without_partner:
        print("\n🎉 SUCCESS! Import is working correctly!")
        print("   ✅ res.partner records are created")
        print("   ✅ sap.res.partner bindings are created")
        print("   ✅ Both are linked correctly")
        return True
    else:
        print("\n⚠️  WARNING: Some issues detected")
        if new_partners != new_bindings:
            print(f"   ❌ Mismatch: {new_partners} partners vs {new_bindings} bindings")
        return False


def test_product_import(env):
    """Test importing products from SAP"""
    print("\n" + "="*60)
    print("🧪 Testing SAP Product Import")
    print("="*60 + "\n")
    
    backend = env['sap.backend'].search([('active', '=', True)], limit=1)
    
    if not backend:
        print("❌ No active SAP backend found!")
        return False
    
    print(f"✅ Using backend: {backend.name}")
    
    # Count before
    product_count_before = env['product.product'].search_count([])
    binding_count_before = env['sap.product.product'].search_count([])
    
    print(f"   product.product count: {product_count_before}")
    print(f"   sap.product.product count: {binding_count_before}")
    
    # Import
    print("\n📥 Importing products...")
    try:
        result = env['sap.product.product'].import_batch(backend)
        print(f"✅ Imported: {result.get('imported', 0)}")
        print(f"❌ Errors: {result.get('errors', 0)}")
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False
    
    # Count after
    product_count_after = env['product.product'].search_count([])
    binding_count_after = env['sap.product.product'].search_count([])
    
    new_products = product_count_after - product_count_before
    new_bindings = binding_count_after - binding_count_before
    
    print(f"\n📊 Results:")
    print(f"   New products: {new_products}")
    print(f"   New bindings: {new_bindings}")
    
    # Check integrity
    bindings_without_product = env['sap.product.product'].search([
        ('odoo_id', '=', False)
    ])
    
    if bindings_without_product:
        print(f"   ❌ Found {len(bindings_without_product)} bindings without odoo_id!")
        return False
    
    print("   ✅ All bindings have odoo_id")
    
    # Sample data
    sample = env['sap.product.product'].search([], limit=2, order='id desc')
    for binding in sample:
        print(f"\n   📦 {binding.odoo_id.name if binding.odoo_id else 'N/A'}")
        print(f"      SAP ItemCode: {binding.external_id}")
        print(f"      Price: {binding.list_price}")
    
    return new_products == new_bindings and not bindings_without_product


def run_all_tests(env):
    """Run all import tests"""
    print("\n" + "="*60)
    print("🚀 SAP INTEGRATION - FULL IMPORT TEST")
    print("="*60)
    
    results = {
        'partners': test_partner_import(env),
        'products': test_product_import(env),
    }
    
    print("\n" + "="*60)
    print("🏁 FINAL RESULTS")
    print("="*60)
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name.capitalize()}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed")
    
    return all_passed


# For direct execution from Odoo shell
if __name__ == '__main__':
    print("This script should be run from Odoo shell")
    print("Example: ")
    print("  from addons.sap_integration import test_import")
    print("  test_import.run_all_tests(env)")

