#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التحقق من إعدادات filestore في Odoo
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api
from odoo.orm.registry import Registry

def check_filestore_config():
    """التحقق من إعدادات وصلاحيات filestore"""
    
    # تحليل الإعدادات
    odoo.tools.config.parse_config(['--config=odoo.conf'])
    
    # الحصول على اسم قاعدة البيانات
    db_name = odoo.tools.config.get('db_name', '')
    if isinstance(db_name, list):
        db_name = db_name[0] if db_name else ''
    
    if not db_name:
        dbfilter = odoo.tools.config.get('dbfilter', '')
        if dbfilter:
            import re
            match = re.match(r'\^?(\w+).*\$?', dbfilter)
            if match:
                db_name = match.group(1)
    
    if not db_name:
        db_name = 'lugal'
    
    print(f"\n{'='*60}")
    print(f"التحقق من إعدادات Filestore - قاعدة البيانات: {db_name}")
    print(f"{'='*60}\n")
    
    # 1. التحقق من data_dir
    data_dir = odoo.tools.config.get('data_dir', '/var/lib/odoo')
    print(f"1. مجلد البيانات (data_dir):")
    print(f"   المسار: {data_dir}")
    
    if os.path.exists(data_dir):
        print(f"   ✅ المجلد موجود")
        
        # التحقق من الصلاحيات
        if os.access(data_dir, os.W_OK):
            print(f"   ✅ يمكن الكتابة")
        else:
            print(f"   ❌ لا يمكن الكتابة!")
            print(f"   المالك: {os.stat(data_dir).st_uid}")
            print(f"   الصلاحيات: {oct(os.stat(data_dir).st_mode)[-3:]}")
    else:
        print(f"   ❌ المجلد غير موجود!")
    
    # 2. التحقق من filestore
    filestore_dir = os.path.join(data_dir, 'filestore', db_name)
    print(f"\n2. مجلد filestore:")
    print(f"   المسار: {filestore_dir}")
    
    if os.path.exists(filestore_dir):
        print(f"   ✅ المجلد موجود")
        
        # التحقق من الصلاحيات
        if os.access(filestore_dir, os.W_OK):
            print(f"   ✅ يمكن الكتابة")
        else:
            print(f"   ❌ لا يمكن الكتابة!")
            print(f"   المالك: {os.stat(filestore_dir).st_uid}")
            print(f"   الصلاحيات: {oct(os.stat(filestore_dir).st_mode)[-3:]}")
        
        # عرض حجم الملفات
        total_size = 0
        file_count = 0
        for root, dirs, files in os.walk(filestore_dir):
            for f in files:
                fp = os.path.join(root, f)
                if os.path.exists(fp):
                    total_size += os.path.getsize(fp)
                    file_count += 1
        
        print(f"   📊 عدد الملفات: {file_count}")
        print(f"   📊 الحجم الإجمالي: {total_size / (1024*1024):.2f} MB")
    else:
        print(f"   ❌ المجلد غير موجود!")
        print(f"   سيتم إنشاؤه تلقائياً عند رفع أول ملف")
    
    # 3. اختبار الكتابة
    print(f"\n3. اختبار الكتابة...")
    
    try:
        # محاولة إنشاء مجلد اختباري
        test_dir = os.path.join(data_dir, 'test_write')
        os.makedirs(test_dir, exist_ok=True)
        
        # محاولة إنشاء ملف اختباري
        test_file = os.path.join(test_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        print(f"   ✅ نجح اختبار الكتابة!")
        
        # حذف الملف والمجلد
        os.remove(test_file)
        os.rmdir(test_dir)
        
    except Exception as e:
        print(f"   ❌ فشل اختبار الكتابة: {e}")
    
    # 4. التحقق من ir.attachment
    print(f"\n4. التحقق من المرفقات في قاعدة البيانات...")
    
    try:
        registry = Registry(db_name)
        
        with registry.cursor() as cr:
            env = api.Environment(cr, odoo.SUPERUSER_ID, {})
            
            # عدد المرفقات
            total_attachments = env['ir.attachment'].search_count([])
            print(f"   📎 إجمالي المرفقات: {total_attachments}")
            
            # المرفقات في نظام الأرشفة
            nbs_attachments = env['ir.attachment'].search_count([
                ('res_model', '=', 'nbs.document')
            ])
            print(f"   📎 مرفقات نظام الأرشفة: {nbs_attachments}")
            
            # المرفقات المخزنة في الملفات (filestore)
            file_attachments = env['ir.attachment'].search_count([
                ('store_fname', '!=', False)
            ])
            print(f"   💾 مرفقات في filestore: {file_attachments}")
            
            # المرفقات المخزنة في قاعدة البيانات (db_datas)
            db_attachments = env['ir.attachment'].search_count([
                ('db_datas', '!=', False)
            ])
            print(f"   💾 مرفقات في قاعدة البيانات: {db_attachments}")
            
    except Exception as e:
        print(f"   ⚠️  تعذر الاتصال بقاعدة البيانات: {e}")
    
    print(f"\n{'='*60}")
    print("✅ انتهى الفحص")
    print(f"{'='*60}\n")
    
    # التوصيات
    print("التوصيات:")
    
    if not os.path.exists(data_dir):
        print(f"❌ أنشئ المجلد: sudo mkdir -p {data_dir}")
        print(f"   ثم: sudo chown -R $(whoami):$(whoami) {data_dir}")
    elif not os.access(data_dir, os.W_OK):
        print(f"❌ أصلح الصلاحيات: sudo chown -R $(whoami):$(whoami) {data_dir}")
        print(f"   ثم: sudo chmod -R 775 {data_dir}")
    else:
        print("✅ جميع الإعدادات صحيحة!")
    
    print("")

if __name__ == '__main__':
    check_filestore_config()
