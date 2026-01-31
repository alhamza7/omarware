# إصلاح قيم action في نظام التدقيق
## Fix Invalid Action Values in Audit Log

---

## 🔴 المشكلة

عند محاولة إنشاء سجل تدقيق لرفع مرفق، يظهر خطأ:
```
Wrong value for nbs.audit.log action: attachment_upload
```

---

## 🔍 السبب

الكود يستخدم قيم `action` غير معرفة في نموذج `nbs.audit.log`:

### القيم المستخدمة في الكود لكن المفقودة:

```python
'attachment_upload'         # ❌ غير معرف
'signed_version_uploaded'   # ❌ غير معرف
'new_version_uploaded'      # ❌ غير معرف
'edit_request_created'      # ❌ غير معرف
'edit_request_approved'     # ❌ غير معرف
'edit_request_rejected'     # ❌ غير معرف
'relation_created'          # ❌ غير معرف
```

---

## ✅ الحل

تم إضافة جميع القيم المفقودة إلى حقل `action` في نموذج `nbs.audit.log`.

### القائمة الكاملة للإجراءات الآن:

```python
action = fields.Selection([
    ('upload', 'Upload'),
    ('view', 'View'),
    ('download', 'Download'),
    ('edit_request', 'Edit Request'),
    ('edit_request_created', 'Edit Request Created'),      # ✅ جديد
    ('edit_request_approved', 'Edit Request Approved'),    # ✅ جديد
    ('edit_request_rejected', 'Edit Request Rejected'),    # ✅ جديد
    ('approval', 'Approval'),
    ('rejection', 'Rejection'),
    ('new_version', 'New Version'),
    ('new_version_uploaded', 'New Version Uploaded'),      # ✅ جديد
    ('archive', 'Archive'),
    ('unarchive', 'Unarchive'),
    ('search', 'Search'),
    ('login', 'Login'),
    ('logout', 'Logout'),
    ('attachment_upload', 'Attachment Upload'),            # ✅ جديد
    ('signed_version_uploaded', 'Signed Version Uploaded'),# ✅ جديد
    ('relation_created', 'Relation Created'),              # ✅ جديد
])
```

---

## 🚀 تطبيق الإصلاح

### على السيرفر البعيد:

```bash
cd /home/lugalai/Lugal-ai

# 1. سحب التحديثات
git pull origin main

# 2. ترقية وحدة nbs_archive
bash upgrade_nbs_archive.sh

# 3. فحص سجلات التدقيق (اختياري)
venv/bin/python fix_audit_log_actions.py
```

---

## 📋 ماذا سيفعل سكريبت الفحص؟

```bash
venv/bin/python fix_audit_log_actions.py
```

### المخرجات المتوقعة:

```
============================================================
فحص وإصلاح قيم action في nbs.audit.log
============================================================

1. البحث عن سجلات التدقيق بقيم action غير صحيحة...
   📋 الإجراءات الصحيحة المتاحة (19):
      - upload: Upload
      - view: View
      - download: Download
      - edit_request: Edit Request
      - edit_request_created: Edit Request Created
      - edit_request_approved: Edit Request Approved
      - edit_request_rejected: Edit Request Rejected
      - approval: Approval
      - rejection: Rejection
      - new_version: New Version
      - new_version_uploaded: New Version Uploaded
      - archive: Archive
      - unarchive: Unarchive
      - search: Search
      - login: Login
      - logout: Logout
      - attachment_upload: Attachment Upload
      - signed_version_uploaded: Signed Version Uploaded
      - relation_created: Relation Created

   📊 الإجراءات المستخدمة في قاعدة البيانات:
      ✅ upload: 25 سجل
      ✅ view: 150 سجل
      ✅ download: 45 سجل
      ✅ attachment_upload: 8 سجل
      ✅ login: 50 سجل

   ✅ جميع الإجراءات صحيحة!

3. أحدث 10 سجلات تدقيق:
   - 2026-01-29 14:30:00: Administrator - attachment_upload (Attachment Upload)
     المستند: documnetAddedUnder12414
     البيانات: Attachment: new attatchemtn
   ...

============================================================
✅ اكتمل الفحص!
============================================================
```

---

## 🔧 إذا وجدت قيم غير صحيحة

إذا كان هناك سجلات بقيم `action` خاطئة (مثل `atachment_upload` بدون "t")، يمكن تصحيحها:

### طريقة 1: عبر SQL

```bash
sudo -u postgres psql nbs_lugalai
```

```sql
-- تصحيح الأخطاء الإملائية
UPDATE nbs_audit_log 
SET action = 'attachment_upload' 
WHERE action = 'atachment_upload';

-- التحقق
SELECT action, COUNT(*) 
FROM nbs_audit_log 
GROUP BY action 
ORDER BY COUNT(*) DESC;

\q
```

### طريقة 2: عبر Python

```python
# داخل Odoo shell
venv/bin/python odoo-bin shell -c odoo.conf -d nbs_lugalai

# في الشل
env.cr.execute("""
    UPDATE nbs_audit_log 
    SET action = 'attachment_upload' 
    WHERE action = 'atachment_upload'
""")
env.cr.commit()
```

---

## 📊 استخدام كل إجراء

### في أي ملف يتم استخدام كل action:

| Action | الملف | الاستخدام |
|--------|------|-----------|
| `upload` | document_controller.py, nbs_document.py | رفع مستند جديد |
| `view` | - | عرض مستند |
| `download` | document_controller.py, nbs_document_version.py | تنزيل مستند |
| `edit_request` | nbs_edit_request.py | طلب تعديل |
| `edit_request_created` | edit_request_controller.py | إنشاء طلب تعديل |
| `edit_request_approved` | edit_request_controller.py | الموافقة على طلب تعديل |
| `edit_request_rejected` | edit_request_controller.py | رفض طلب تعديل |
| `approval` | nbs_edit_request.py | موافقة عامة |
| `rejection` | nbs_edit_request.py | رفض عام |
| `new_version` | nbs_document_version.py | نسخة جديدة |
| `new_version_uploaded` | edit_request_controller.py | رفع نسخة جديدة |
| `archive` | document_controller.py, nbs_document.py | أرشفة مستند |
| `unarchive` | document_controller.py | إلغاء الأرشفة |
| `search` | - | بحث |
| `login` | jwt_service.py | تسجيل دخول |
| `logout` | - | تسجيل خروج |
| `attachment_upload` | nbs_document_relation.py | رفع مرفق |
| `signed_version_uploaded` | signature_controller.py | رفع نسخة موقعة |
| `relation_created` | relations_controller.py | إنشاء علاقة |

---

## 🧪 اختبار

### اختبار 1: رفع مرفق

```python
# داخل Odoo shell
doc = env['nbs.document'].search([], limit=1)
attachment = env['nbs.document.attachment'].create({
    'document_id': doc.id,
    'name': 'Test Attachment',
    'file_name': 'test.pdf',
    'file_data': 'SGVsbG8gV29ybGQ=',
    'uploader_id': env.user.id,
})

# تحقق من سجل التدقيق
audit = env['nbs.audit.log'].search([
    ('action', '=', 'attachment_upload'),
    ('document_id', '=', doc.id)
], limit=1, order='timestamp desc')

print(f"✅ Audit log created: {audit.action}")
# يجب أن يطبع: ✅ Audit log created: attachment_upload
```

### اختبار 2: جميع الإجراءات

```bash
venv/bin/python fix_audit_log_actions.py
```

يجب أن يعرض جميع الإجراءات بدون أخطاء.

---

## 🎯 الملخص

### ما تم إصلاحه:

```
✅ أضيف 7 قيم action جديدة
✅ جميع الإجراءات المستخدمة في الكود الآن معرفة
✅ سكريبت فحص شامل للتحقق من صحة البيانات
✅ دليل كامل لتصحيح القيم الخاطئة
```

### الخطوات:

```bash
cd /home/lugalai/Lugal-ai
git pull origin main
bash upgrade_nbs_archive.sh
venv/bin/python fix_audit_log_actions.py
```

### النتيجة:

```
✅ رفع المرفقات يعمل
✅ جميع سجلات التدقيق تُنشأ بنجاح
✅ لا أخطاء في قيم action
✅ النظام جاهز للاستخدام
```

---

## 📞 للدعم

إذا استمرت المشكلة:

```bash
# تحقق من اللوغات
tail -50 odoo.log | grep -i audit

# شغل سكريبت الفحص
venv/bin/python fix_audit_log_actions.py

# تحقق من قاعدة البيانات
sudo -u postgres psql nbs_lugalai -c "
  SELECT action, COUNT(*) 
  FROM nbs_audit_log 
  GROUP BY action 
  ORDER BY COUNT(*) DESC;
"
```

---

**تاريخ الإنشاء:** 29 يناير 2026  
**الحالة:** ✅ جاهز للتطبيق
