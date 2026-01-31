#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Add Odoo to Python path
sys.path.append('/home/lugalai/Lugal-ai')
sys.path.append('/home/lugalai/Lugal-ai/odoo')

import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

def fix_nbs_archive_attachments():
    """
    Fix NBS Archive attachment upload issues:
    1. Check if documents exist
    2. Check permissions
    3. Check model integrity
    4. Provide diagnostic info
    """
    
    # Initialize Odoo
    odoo.tools.config.parse_config(['-c', '/home/lugalai/Lugal-ai/odoo.conf'])
    
    dbname = 'nbs_lugalai'
    registry = Registry(dbname)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        print("=" * 60)
        print("تشخيص مشكلة رفع المرفقات في نظام الأرشفة")
        print("=" * 60)
        print()
        
        # 1. Check if nbs_archive module is installed
        print("1. التحقق من وحدة nbs_archive...")
        module = env['ir.module.module'].search([('name', '=', 'nbs_archive')], limit=1)
        if not module:
            print("   ❌ وحدة nbs_archive غير مثبتة!")
            return
        print(f"   ✅ الوحدة مثبتة - الحالة: {module.state}")
        print()
        
        # 2. Check if nbs.document model exists and has records
        print("2. التحقق من المستندات...")
        try:
            Document = env['nbs.document']
            total_docs = Document.search_count([])
            active_docs = Document.search_count([('state', 'not in', ['archived', 'deleted'])])
            
            print(f"   ✅ نموذج nbs.document موجود")
            print(f"   📊 إجمالي المستندات: {total_docs}")
            print(f"   📊 المستندات النشطة: {active_docs}")
            
            if total_docs == 0:
                print()
                print("   ⚠️  لا توجد مستندات في النظام!")
                print("   💡 يجب إنشاء مستند أولاً قبل رفع المرفقات")
            else:
                # Show some sample documents
                print()
                print("   📄 أمثلة من المستندات المتاحة:")
                docs = Document.search([('state', 'not in', ['archived', 'deleted'])], limit=5)
                for doc in docs:
                    print(f"      - ID: {doc.id}, الاسم: {doc.name}, الحالة: {doc.state}")
                    print(f"        القسم: {doc.department_id.name if doc.department_id else 'غير محدد'}")
                    print(f"        الرافع: {doc.uploader_id.name if doc.uploader_id else 'غير محدد'}")
        except Exception as e:
            print(f"   ❌ خطأ في الوصول لنموذج المستندات: {str(e)}")
            return
        
        print()
        
        # 3. Check nbs.document.attachment model
        print("3. التحقق من نموذج المرفقات...")
        try:
            Attachment = env['nbs.document.attachment']
            total_attachments = Attachment.search_count([])
            print(f"   ✅ نموذج nbs.document.attachment موجود")
            print(f"   📊 إجمالي المرفقات: {total_attachments}")
            
            if total_attachments > 0:
                print()
                print("   📎 أمثلة من المرفقات الموجودة:")
                atts = Attachment.search([], limit=5)
                for att in atts:
                    print(f"      - ID: {att.id}, الاسم: {att.name}")
                    print(f"        المستند: {att.document_id.name} (ID: {att.document_id.id})")
                    print(f"        الحجم: {att.file_size} bytes")
        except Exception as e:
            print(f"   ❌ خطأ في الوصول لنموذج المرفقات: {str(e)}")
        
        print()
        
        # 4. Check departments
        print("4. التحقق من الأقسام...")
        try:
            Department = env['nbs.department']
            total_depts = Department.search_count([])
            print(f"   ✅ إجمالي الأقسام: {total_depts}")
            
            if total_depts == 0:
                print("   ⚠️  لا توجد أقسام! سيتم إنشاء أقسام افتراضية...")
                default_depts = [
                    {'name': 'عام', 'code': 'GEN', 'description': 'القسم العام'},
                    {'name': 'الموارد البشرية', 'code': 'HR', 'description': 'قسم الموارد البشرية'},
                    {'name': 'المالية', 'code': 'FIN', 'description': 'القسم المالي'},
                    {'name': 'تقنية المعلومات', 'code': 'IT', 'description': 'قسم تقنية المعلومات'},
                ]
                for dept_data in default_depts:
                    dept = Department.create(dept_data)
                    print(f"      ✅ تم إنشاء قسم: {dept.name}")
            else:
                print("   📋 الأقسام المتاحة:")
                depts = Department.search([], limit=10)
                for dept in depts:
                    print(f"      - ID: {dept.id}, الاسم: {dept.name}, الكود: {dept.code}")
        except Exception as e:
            print(f"   ❌ خطأ في الوصول للأقسام: {str(e)}")
        
        print()
        
        # 5. Check document types
        print("5. التحقق من أنواع المستندات...")
        try:
            DocType = env['nbs.document.type']
            total_types = DocType.search_count([])
            print(f"   ✅ إجمالي أنواع المستندات: {total_types}")
            
            if total_types == 0:
                print("   ⚠️  لا توجد أنواع مستندات! سيتم إنشاء أنواع افتراضية...")
                default_types = [
                    {'name': 'عقد', 'code': 'CONT', 'description': 'عقود ومستندات تعاقدية'},
                    {'name': 'فاتورة', 'code': 'INV', 'description': 'فواتير مالية'},
                    {'name': 'تقرير', 'code': 'RPT', 'description': 'تقارير إدارية'},
                    {'name': 'رسالة', 'code': 'LTR', 'description': 'رسائل رسمية'},
                    {'name': 'أخرى', 'code': 'OTH', 'description': 'مستندات متنوعة'},
                ]
                for type_data in default_types:
                    doc_type = DocType.create(type_data)
                    print(f"      ✅ تم إنشاء نوع: {doc_type.name}")
            else:
                print("   📋 أنواع المستندات المتاحة:")
                types = DocType.search([], limit=10)
                for dt in types:
                    print(f"      - ID: {dt.id}, الاسم: {dt.name}, الكود: {dt.code}")
        except Exception as e:
            print(f"   ❌ خطأ في الوصول لأنواع المستندات: {str(e)}")
        
        print()
        
        # 6. Check user permissions
        print("6. التحقق من صلاحيات المستخدمين...")
        try:
            admin = env.ref('base.user_admin')
            groups = env['res.groups'].search([('name', 'ilike', 'nbs_archive')])
            
            print(f"   👤 المستخدم: {admin.name} (ID: {admin.id})")
            print(f"   📋 مجموعات NBS Archive:")
            
            for group in groups:
                is_member = admin.id in group.users.ids
                status = "✅" if is_member else "❌"
                print(f"      {status} {group.name} (ID: {group.id})")
                
                if not is_member:
                    print(f"         💡 سيتم إضافة المستخدم للمجموعة...")
                    group.users = [(4, admin.id)]
                    print(f"         ✅ تمت الإضافة")
            
        except Exception as e:
            print(f"   ⚠️  خطأ في التحقق من الصلاحيات: {str(e)}")
        
        print()
        
        # 7. Check filestore permissions
        print("7. التحقق من صلاحيات الملفات...")
        import subprocess
        try:
            filestore_path = "/var/lib/odoo/filestore/nbs_lugalai"
            if os.path.exists(filestore_path):
                result = subprocess.run(['ls', '-ld', filestore_path], 
                                      capture_output=True, text=True)
                print(f"   📁 {filestore_path}")
                print(f"      {result.stdout.strip()}")
                
                # Check if writable
                if os.access(filestore_path, os.W_OK):
                    print(f"   ✅ المجلد قابل للكتابة")
                else:
                    print(f"   ❌ المجلد غير قابل للكتابة!")
                    print(f"   💡 نفذ: sudo chown -R lugalai:lugalai {filestore_path}")
                    print(f"   💡 نفذ: sudo chmod -R 775 {filestore_path}")
            else:
                print(f"   ⚠️  المجلد غير موجود: {filestore_path}")
                print(f"   💡 نفذ: sudo mkdir -p {filestore_path}")
                print(f"   💡 نفذ: sudo chown -R lugalai:lugalai {filestore_path}")
                print(f"   💡 نفذ: sudo chmod -R 775 {filestore_path}")
        except Exception as e:
            print(f"   ⚠️  خطأ في التحقق من المجلد: {str(e)}")
        
        print()
        
        # 8. Test creating a sample document if none exist
        if total_docs == 0:
            print("8. إنشاء مستند تجريبي...")
            try:
                dept = Department.search([], limit=1)
                doc_type = DocType.search([], limit=1)
                
                if dept and doc_type:
                    test_doc = Document.create({
                        'name': 'مستند تجريبي للاختبار',
                        'document_number': 'TEST-001',
                        'department_id': dept.id,
                        'document_type_id': doc_type.id,
                        'description': 'مستند تم إنشاؤه تلقائياً للاختبار',
                        'uploader_id': env.user.id,
                        'state': 'draft',
                    })
                    print(f"   ✅ تم إنشاء مستند تجريبي: {test_doc.name} (ID: {test_doc.id})")
                    print()
                    print("   💡 يمكنك الآن محاولة رفع مرفق على هذا المستند")
                    print(f"   💡 استخدم document_id: {test_doc.id}")
                else:
                    print("   ❌ لا يمكن إنشاء مستند تجريبي - القسم أو النوع مفقود")
            except Exception as e:
                print(f"   ❌ خطأ في إنشاء المستند: {str(e)}")
            print()
        
        env.cr.commit()
    
    print("=" * 60)
    print("✅ اكتمل التشخيص!")
    print("=" * 60)
    print()
    print("🔍 الأسباب المحتملة لخطأ 'DOCUMENT NOT FOUND':")
    print()
    print("1. ❌ document_id المرسل غير صحيح أو المستند غير موجود")
    print("   💡 تأكد من أن المستند موجود في النظام")
    print("   💡 استخدم ID صحيح من القائمة أعلاه")
    print()
    print("2. ❌ المستخدم لا يملك صلاحيات الوصول")
    print("   💡 تأكد من أن المستخدم ضمن مجموعة NBS Archive")
    print("   💡 تحقق من JWT token صالح")
    print()
    print("3. ❌ المستند في حالة محذوف أو مؤرشف")
    print("   💡 تحقق من state المستند (يجب أن تكون: draft/active/approved)")
    print()
    print("4. ❌ مشكلة في الاتصال بـ API")
    print("   💡 تحقق من URL الصحيح: /api/documents/<document_id>/add-attachment")
    print("   💡 تحقق من إرسال JWT token في الهيدر")
    print()
    print("📋 خطوات الحل:")
    print("1. تأكد من وجود مستند في النظام (انظر القائمة أعلاه)")
    print("2. استخدم document_id الصحيح عند رفع المرفق")
    print("3. تأكد من تسجيل الدخول وحصولك على JWT token")
    print("4. استخدم endpoint الصحيح: POST /api/documents/<document_id>/add-attachment")
    print()

if __name__ == '__main__':
    fix_nbs_archive_attachments()
