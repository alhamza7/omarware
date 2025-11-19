#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التحقق من أن الكود الجديد محمّل في Odoo
"""

import sys
import os
import inspect

# إضافة مسار Odoo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api

def verify_code():
    """التحقق من أن الكود الجديد محمّل"""
    
    odoo.tools.config.parse_config(['--config=odoo.conf'])
    db_name = odoo.tools.config['db_name'] or 'lugal'
    
    print(f"\n{'='*60}")
    print(f"التحقق من تحميل الكود الجديد")
    print(f"{'='*60}\n")
    
    registry = odoo.registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        # 1. التحقق من pos_perfume_order
        print("1. التحقق من pos.perfume.order.action_confirm...")
        try:
            model = env['pos.perfume.order']
            method = model.action_confirm
            
            # قراءة source code
            source = inspect.getsource(method)
            
            checks = [
                ('sync_successful = False', 'متغير sync_successful'),
                ('Manual SAP sync', 'مزامنة SAP يدوية'),
                ('invalidate_recordset', 'invalidate_recordset'),
                ('❌ Error sending quotation', 'رسائل خطأ محسّنة'),
            ]
            
            all_ok = True
            for check, desc in checks:
                if check in source:
                    print(f"   ✅ {desc}: موجود")
                else:
                    print(f"   ❌ {desc}: غير موجود!")
                    all_ok = False
            
            if all_ok:
                print("   ✅ الكود الجديد محمّل في pos.perfume.order")
            else:
                print("   ❌ الكود القديم ما زال محمّلاً!")
                
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
        
        print("")
        
        # 2. التحقق من sale_order_sap
        print("2. التحقق من sale.order._send_to_sap...")
        try:
            model = env['sale.order']
            method = model._send_to_sap
            
            source = inspect.getsource(method)
            
            checks = [
                ('sync_successful = False', 'متغير sync_successful'),
                ('❌ No active SAP backend', 'رسائل خطأ محسّنة'),
                ('❌ Error sending quotation', 'رسائل خطأ محسّنة'),
                ('finally:', 'finally block'),
                ('FAILED - Check errors above', 'رسالة نهائية'),
            ]
            
            all_ok = True
            for check, desc in checks:
                if check in source:
                    print(f"   ✅ {desc}: موجود")
                else:
                    print(f"   ❌ {desc}: غير موجود!")
                    all_ok = False
            
            if all_ok:
                print("   ✅ الكود الجديد محمّل في sale.order")
            else:
                print("   ❌ الكود القديم ما زال محمّلاً!")
                
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
        
        print("")
        
        # 3. التحقق من إصدارات الوحدات
        print("3. التحقق من إصدارات الوحدات...")
        modules = ['pos_perfume_custom', 'sap_integration']
        for module_name in modules:
            module = env['ir.module.module'].search([('name', '=', module_name)], limit=1)
            if module:
                print(f"   {module_name:25} : {module.state:15} (v{module.installed_version or 'N/A'})")
            else:
                print(f"   {module_name:25} : ❌ NOT FOUND")
        
        print(f"\n{'='*60}")
        print("✅ انتهى التحقق")
        print(f"{'='*60}\n")

if __name__ == '__main__':
    verify_code()

