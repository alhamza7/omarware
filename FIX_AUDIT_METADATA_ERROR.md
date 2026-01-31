# إصلاح خطأ حقل metadata في نظام التدقيق
## Fix "INVALID FIELD METADATA" Error in NBS Audit Log

---

## 🔴 المشكلة

عند استخدام نظام الأرشفة، تظهر رسالة خطأ:
```
INVALID FIELD METADATA IN NBS AUDIT LOG
```

---

## 🔍 السبب

### المشكلة الفعلية:

```python
# في نموذج nbs.audit.log كان موجود فقط:
metadata_snapshot = fields.Text(...)

# لكن الكود في عدة أماكن يحاول استخدام:
log.metadata          # ❌ هذا الحقل غير موجود!
'metadata': 'value'   # ❌ عند إنشاء سجلات تدقيق
```

### الملفات المتأثرة:

```
1. addons/nbs_archive/models/nbs_audit_log.py
   - النموذج لا يحتوي على حقل 'metadata'

2. addons/nbs_archive/controllers/admin_controller.py (line 251)
   - يحاول قراءة log.metadata

3. addons/nbs_archive/controllers/edit_request_controller.py
   - يمرر 'metadata' عند إنشاء سجلات

4. addons/nbs_archive/controllers/relations_controller.py
   - يمرر 'metadata' عند إنشاء سجلات

5. addons/nbs_archive/models/nbs_document_relation.py
   - يمرر 'metadata' عند رفع مرفق
```

---

## ✅ الحل

### تم إضافة حقل `metadata` للنموذج:

```python
# في nbs_audit_log.py
metadata = fields.Text(
    string='Metadata',
    readonly=True,
    help='Additional metadata information about the action'
)
```

### تم تحديث دالة `log_action`:

```python
def log_action(self, action, user_id=None, document_id=None, 
               department_id=None, ip_address=None, user_agent=None, 
               details=None, metadata=None):  # ← إضافة metadata
    """Helper method to create audit log entries"""
    vals = {
        'action': action,
        'user_id': user_id or self.env.user.id,
    }
    # ... كود آخر ...
    
    if metadata:
        vals['metadata'] = metadata  # ← إضافة metadata
    
    return self.sudo().create(vals)
```

---

## 🚀 تطبيق الإصلاح على السيرفر

### الطريقة السريعة (موصى بها):

```bash
cd /home/lugalai/Lugal-ai

# 1. سحب التحديثات
git pull origin main

# 2. تشغيل سكريبت الفحص (اختياري)
venv/bin/python fix_nbs_audit_metadata_field.py

# 3. ترقية الوحدة
bash upgrade_nbs_archive.sh
```

---

## 📋 الطريقة اليدوية (خطوة بخطوة)

### 1. سحب التحديثات

```bash
cd /home/lugalai/Lugal-ai
git pull origin main
```

### 2. التحقق من التحديثات

```bash
# تحقق من أن الحقل الجديد موجود
grep -A 3 "metadata = fields.Text" addons/nbs_archive/models/nbs_audit_log.py
```

يجب أن ترى:
```python
metadata = fields.Text(
    string='Metadata',
    readonly=True,
    help='Additional metadata information about the action'
)
```

### 3. إيقاف Odoo

```bash
pkill -9 -f odoo-bin
sleep 3
```

### 4. ترقية وحدة nbs_archive

```bash
venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai \
    -u nbs_archive --stop-after-init
```

### 5. إعادة تشغيل Odoo

```bash
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai \
    --http-port=8069 > odoo.log 2>&1 &
```

### 6. التحقق من نجاح التشغيل

```bash
# تحقق من أن Odoo يعمل
ps aux | grep odoo-bin | grep -v grep

# تحقق من اللوغات
tail -50 odoo.log
```

---

## 🔍 التحقق من الإصلاح

### 1. عبر Python Script

```bash
cd /home/lugalai/Lugal-ai
venv/bin/python fix_nbs_audit_metadata_field.py
```

المخرجات المتوقعة:
```
============================================================
إصلاح حقل metadata في نموذج nbs.audit.log
============================================================

1. التحقق من وحدة nbs_archive...
   ✅ الوحدة مثبتة - الحالة: installed

2. التحقق من الحقول في قاعدة البيانات...
   📋 الحقول الموجودة في جدول nbs_audit_log:
      - id (integer)
      - timestamp (timestamp without time zone)
      - user_id (integer)
      - action (character varying)
      - document_id (integer)
      - department_id (integer)
      - ip_address (character varying)
      - user_agent (text)
      - details (text)
      - metadata (text)                      ← ✅ موجود!
      - metadata_snapshot (text)
      ...

   ✅ حقل 'metadata' موجود!
   ✅ حقل 'metadata_snapshot' موجود!

3. التحقق من سجلات التدقيق...
   📊 إجمالي سجلات التدقيق: 45

5. اختبار إنشاء سجل تدقيق مع metadata...
   ✅ تم إنشاء سجل تدقيق تجريبي (ID: 123)
   ✅ قراءة metadata: Test metadata value

============================================================
✅ اكتمل الفحص!
============================================================
```

### 2. عبر SQL

```bash
sudo -u postgres psql nbs_lugalai
```

```sql
-- التحقق من وجود الحقل
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'nbs_audit_log' 
  AND column_name IN ('metadata', 'metadata_snapshot');

-- يجب أن يعرض:
--  column_name      | data_type
-- ------------------+-----------
--  metadata         | text
--  metadata_snapshot| text
-- (2 rows)

-- اختبار قراءة السجلات
SELECT id, action, metadata, 
       LEFT(metadata, 50) as metadata_preview
FROM nbs_audit_log 
WHERE metadata IS NOT NULL 
ORDER BY timestamp DESC 
LIMIT 5;

\q
```

### 3. عبر واجهة الويب

```
1. سجل دخول إلى Odoo
   http://192.168.116.211:8069

2. افتح نظام الأرشفة

3. قم بأي عملية (رفع مستند، إضافة مرفق، إلخ)

4. يجب أن تعمل بدون أخطاء ✅
```

---

## 🧪 اختبار كامل

### اختبار 1: إنشاء سجل تدقيق مع metadata

```python
# داخل Odoo shell
venv/bin/python odoo-bin shell -c odoo.conf -d nbs_lugalai

# في الشل
env['nbs.audit.log'].sudo().create({
    'action': 'search',
    'user_id': env.user.id,
    'details': 'Test search action',
    'metadata': 'Search query: test documents'
})

# يجب أن يعمل بدون أخطاء ✅
```

### اختبار 2: قراءة metadata من سجل موجود

```python
# داخل Odoo shell
log = env['nbs.audit.log'].search([], limit=1)
print(f"Action: {log.action}")
print(f"Metadata: {log.metadata}")
print(f"Metadata Snapshot: {log.metadata_snapshot}")

# يجب أن يطبع القيم بدون أخطاء ✅
```

### اختبار 3: رفع مرفق (استخدام metadata)

```python
# داخل Odoo shell
doc = env['nbs.document'].search([], limit=1)
if doc:
    attachment = env['nbs.document.attachment'].create({
        'document_id': doc.id,
        'name': 'Test Attachment',
        'file_name': 'test.txt',
        'file_data': 'SGVsbG8gV29ybGQ=',  # base64: Hello World
        'uploader_id': env.user.id,
    })
    print(f"✅ Attachment created: {attachment.id}")
    
    # تحقق من أن سجل التدقيق تم إنشاؤه مع metadata
    audit = env['nbs.audit.log'].search([
        ('action', '=', 'attachment_upload'),
        ('document_id', '=', doc.id)
    ], limit=1, order='timestamp desc')
    
    if audit:
        print(f"✅ Audit log created with metadata: {audit.metadata}")
```

---

## 📊 فهم الحقول

### `metadata` vs `metadata_snapshot`

```python
# metadata
# - معلومات إضافية عن الإجراء نفسه
# - مثل: "Request ID: 123", "Attachment: invoice.pdf"
# - تُستخدم للربط مع سجلات أخرى

metadata = "Request ID: 456, Reason: Urgent update"

# metadata_snapshot
# - نسخة كاملة من بيانات المستند في وقت الإجراء
# - تُستخدم لحفظ حالة المستند تاريخياً
# - مفيدة للتدقيق والمراجعة

metadata_snapshot = {
    'document_name': 'Contract 2026',
    'state': 'approved',
    'version': 2,
    'tags': ['urgent', 'finance']
}
```

### استخدام الحقول في الكود

```python
# إنشاء سجل تدقيق كامل
env['nbs.audit.log'].sudo().create({
    'action': 'new_version',
    'user_id': env.user.id,
    'document_id': doc.id,
    'department_id': doc.department_id.id,
    'details': 'User uploaded version 3',
    'metadata': f'Version 3, Edit Request ID: {request_id}',
    'metadata_snapshot': json.dumps({
        'document_name': doc.name,
        'document_number': doc.document_number,
        'state': doc.state,
        'version': doc.version,
    }),
    'ip_address': request.httprequest.remote_addr,
    'user_agent': request.httprequest.user_agent.string,
})
```

---

## 🛠️ استكشاف الأخطاء

### الخطأ: "column nbs_audit_log.metadata does not exist"

```bash
# الحل: لم تتم ترقية الوحدة بعد
cd /home/lugalai/Lugal-ai
bash upgrade_nbs_archive.sh
```

### الخطأ: "field 'metadata' not found"

```bash
# الحل: تحقق من أن ملف nbs_audit_log.py محدث
grep "metadata = fields.Text" addons/nbs_archive/models/nbs_audit_log.py

# إذا لم تجد النتيجة، سحب التحديثات:
git pull origin main
```

### الخطأ: الوحدة لا تترقى

```bash
# تحقق من اللوغات
tail -100 odoo.log

# ابحث عن أخطاء محددة
grep -i "error\|exception\|metadata" odoo.log | tail -20

# حاول ترقية بـ verbose mode
venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai \
    -u nbs_archive --stop-after-init --log-level=debug
```

---

## 🗄️ تحديث قاعدة البيانات يدوياً (إذا لزم)

### إذا فشلت الترقية التلقائية:

```bash
sudo -u postgres psql nbs_lugalai
```

```sql
-- التحقق من وجود الحقل
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'nbs_audit_log' 
  AND column_name = 'metadata';

-- إذا لم يكن موجوداً، أضفه يدوياً:
ALTER TABLE nbs_audit_log 
ADD COLUMN IF NOT EXISTS metadata TEXT;

-- تحقق من الإضافة
\d nbs_audit_log

\q
```

ثم أعد تشغيل Odoo:

```bash
pkill -9 -f odoo-bin
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai \
    --http-port=8069 > odoo.log 2>&1 &
```

---

## 🎯 الملخص

### التغييرات:

```
✅ إضافة حقل 'metadata' لنموذج nbs.audit.log
✅ تحديث دالة log_action لدعم metadata
✅ سكريبت فحص وتشخيص
✅ سكريبت ترقية تلقائي
✅ دليل إصلاح شامل
```

### الخطوات السريعة:

```bash
cd /home/lugalai/Lugal-ai
git pull origin main
bash upgrade_nbs_archive.sh
```

### التحقق:

```bash
venv/bin/python fix_nbs_audit_metadata_field.py
```

---

## 📞 للدعم

إذا استمرت المشكلة:

```bash
# 1. تحقق من اللوغات
tail -100 odoo.log | grep -i metadata

# 2. تحقق من الحقول في قاعدة البيانات
sudo -u postgres psql nbs_lugalai -c "
  SELECT column_name, data_type 
  FROM information_schema.columns 
  WHERE table_name = 'nbs_audit_log';
"

# 3. شغل سكريبت الفحص
venv/bin/python fix_nbs_audit_metadata_field.py
```

---

**تاريخ الإنشاء:** 29 يناير 2026  
**الحالة:** ✅ جاهز للتطبيق  
**الأولوية:** 🔴 عالية
