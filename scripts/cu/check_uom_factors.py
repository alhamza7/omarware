#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص UoMs وFactors
"""

import xmlrpc.client

url = "http://localhost:8069"
db = "lugal"
username = "admin"
password = "admin"

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    
    print("=" * 80)
    print("🔍 فحص UoMs وFactors")
    print("=" * 80 + "\n")
    
    # جلب UoMs
    uom_ids = [70, 79, 80]  # Manual, 0.5 كيلو, 0.25 كغم
    
    uoms = models.execute_kw(db, uid, password,
        'uom.uom', 'read',
        [uom_ids],
        {'fields': ['id', 'name', 'factor', 'rounding']})
    
    for uom in uoms:
        print(f"UoM: {uom['name']}")
        print(f"   ID: {uom['id']}")
        print(f"   Factor: {uom.get('factor', 'N/A')}")
        print(f"   Rounding: {uom.get('rounding', 'N/A')}\n")
    
    # حساب توقعي
    print("=" * 80)
    print("🧮 التحليل")
    print("=" * 80 + "\n")
    
    print("إذا كان السعر الأساسي $40 لـ Manual:")
    print("   0.5 كيلو بـ factor 6.02785 → $40 / 6.02785 = $6.63 ✅ (هذا ما حدث!)")
    print("   0.25 كغم بـ factor 12.0557 → $40 / 12.0557 = $3.31 ✅ (هذا ما حدث!)\n")
    
    print("المشكلة: Module لم يجد القواعد المحددة لـ UoM!")
    print("→ يحتاج تحسين منطق المطابقة\n")
    
except Exception as e:
    print(f"❌ {e}")

