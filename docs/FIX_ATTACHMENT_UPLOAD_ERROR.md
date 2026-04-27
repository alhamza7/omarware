# إصلاح خطأ رفع المرفقات في نظام الأرشفة
## Fix "DOCUMENT NOT FOUND" Error in NBS Archive

---

## 🔴 المشكلة

عند محاولة رفع مرفق (attachment) في نظام الأرشفة، تظهر رسالة الخطأ:
```
DOCUMENT NOT FOUND
```

---

## 🔍 الأسباب المحتملة

### 1. المستند غير موجود أو محذوف
```
❌ المستند الذي تحاول رفع مرفق له غير موجود في قاعدة البيانات
❌ المستند في حالة محذوف (deleted) أو مؤرشف (archived)
❌ document_id المرسل خاطئ
```

### 2. مشكلة في الصلاحيات
```
❌ المستخدم لا يملك صلاحيات الوصول للمستند
❌ JWT token منتهي الصلاحية أو غير صحيح
❌ المستخدم ليس ضمن مجموعة NBS Archive
```

### 3. مشكلة في API endpoint
```
❌ URL خاطئ
❌ معاملات (parameters) خاطئة
❌ طريقة الإرسال (method) خاطئة
```

### 4. مشكلة في البيانات الأساسية
```
❌ لا توجد أقسام (departments) في النظام
❌ لا توجد أنواع مستندات (document types)
❌ لا توجد مستندات على الإطلاق
```

---

## 🚀 الحل السريع

### على السيرفر البعيد:

```bash
cd /home/lugalai/Lugal-ai

# سحب التحديثات
git pull origin main

# تشغيل سكريبت التشخيص
venv/bin/python fix_nbs_archive_attachments.py
```

---

## 📋 ماذا يفعل السكريبت؟

```
1. ✓ التحقق من تثبيت وحدة nbs_archive
2. ✓ التحقق من وجود مستندات في النظام
3. ✓ التحقق من نموذج المرفقات
4. ✓ التحقق من الأقسام (departments)
5. ✓ التحقق من أنواع المستندات (document types)
6. ✓ التحقق من صلاحيات المستخدمين
7. ✓ التحقق من صلاحيات الملفات (filestore)
8. ✓ إنشاء مستند تجريبي إذا لم يكن هناك مستندات
```

---

## 🔧 الحل التفصيلي

### 1. التحقق من وجود مستندات

```bash
venv/bin/python odoo-bin shell -c odoo.conf -d nbs_lugalai
```

```python
# داخل Odoo shell
env['nbs.document'].search_count([])

# إذا كانت النتيجة 0، يجب إنشاء مستند أولاً
```

### 2. إنشاء مستند تجريبي

```python
# داخل Odoo shell
dept = env['nbs.department'].search([], limit=1)
doc_type = env['nbs.document.type'].search([], limit=1)

if dept and doc_type:
    doc = env['nbs.document'].create({
        'name': 'مستند اختبار',
        'document_number': 'TEST-001',
        'department_id': dept.id,
        'document_type_id': doc_type.id,
        'description': 'مستند للاختبار',
        'uploader_id': env.user.id,
        'state': 'draft',
    })
    print(f"تم إنشاء المستند - ID: {doc.id}")
    env.cr.commit()
```

### 3. الحصول على قائمة المستندات المتاحة

```python
# داخل Odoo shell
docs = env['nbs.document'].search([('state', 'not in', ['archived', 'deleted'])], limit=10)
for doc in docs:
    print(f"ID: {doc.id}, Name: {doc.name}, State: {doc.state}")
```

---

## 🌐 استخدام API بشكل صحيح

### 1. تسجيل الدخول والحصول على JWT

```bash
curl -X POST http://192.168.116.211:8069/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_password"
  }'
```

الاستجابة:
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 2,
    "name": "Admin"
  }
}
```

### 2. الحصول على قائمة المستندات

```bash
curl -X POST http://192.168.116.211:8069/api/documents \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "page": 1,
      "per_page": 10
    },
    "id": 1
  }'
```

### 3. رفع مرفق بشكل صحيح

```bash
# استخدم document_id من الخطوة السابقة
DOCUMENT_ID=5  # مثال

curl -X POST http://192.168.116.211:8069/api/documents/${DOCUMENT_ID}/add-attachment \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "name": "اسم المرفق",
      "file_name": "document.pdf",
      "file_data": "BASE64_ENCODED_FILE_DATA",
      "description": "وصف المرفق",
      "attachment_type": "supporting"
    },
    "id": 1
  }'
```

---

## 🐍 استخدام Python

```python
import requests
import base64

# 1. تسجيل الدخول
login_url = "http://192.168.116.211:8069/api/auth/login"
login_data = {
    "username": "admin",
    "password": "admin"
}
response = requests.post(login_url, json=login_data)
token = response.json()['token']

# 2. الحصول على المستندات
docs_url = "http://192.168.116.211:8069/api/documents"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
docs_payload = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {"page": 1, "per_page": 10},
    "id": 1
}
docs_response = requests.post(docs_url, json=docs_payload, headers=headers)
documents = docs_response.json()['result']['data']

print(f"Found {len(documents)} documents")
for doc in documents:
    print(f"ID: {doc['id']}, Name: {doc['name']}")

# 3. رفع مرفق
if documents:
    document_id = documents[0]['id']
    
    # قراءة ملف
    with open('test_file.pdf', 'rb') as f:
        file_data = base64.b64encode(f.read()).decode('utf-8')
    
    # رفع المرفق
    upload_url = f"http://192.168.116.211:8069/api/documents/{document_id}/add-attachment"
    upload_payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "name": "مرفق تجريبي",
            "file_name": "test_file.pdf",
            "file_data": file_data,
            "description": "ملف تجريبي",
            "attachment_type": "supporting"
        },
        "id": 1
    }
    
    upload_response = requests.post(upload_url, json=upload_payload, headers=headers)
    print(upload_response.json())
```

---

## 🔍 التحقق من اللوغات

### إذا استمرت المشكلة:

```bash
# تحقق من آخر 100 سطر في لوغات Odoo
tail -100 /home/lugalai/Lugal-ai/odoo.log

# ابحث عن أخطاء محددة
grep -i "attachment\|document not found" /home/lugalai/Lugal-ai/odoo.log | tail -20
```

---

## ✅ التحقق من نجاح الحل

### 1. في المتصفح:

```
1. سجل دخول إلى نظام الأرشفة
2. افتح أي مستند موجود
3. اضغط على "إضافة مرفق"
4. اختر ملف وارفعه
5. يجب أن يظهر المرفق في قائمة المرفقات
```

### 2. عبر API:

```bash
# الحصول على قائمة المرفقات لمستند معين
curl -X POST http://192.168.116.211:8069/api/documents/5/attachments \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {},
    "id": 1
  }'
```

---

## 📊 فهم بنية نظام المرفقات

### جداول قاعدة البيانات:

```
nbs_document
├── id (المستند الأساسي)
└── name, state, department_id, etc.

nbs_document_attachment
├── id (المرفق)
├── document_id → nbs_document.id (العلاقة)
├── name, file_name, file_data
└── uploader_id, upload_date
```

### العلاقات:

```
مستند واحد ← يمكن أن يحتوي على عدة مرفقات
مرفق واحد ← ينتمي لمستند واحد فقط
```

---

## 🛠️ حلول إضافية

### إذا كانت صلاحيات الملفات هي المشكلة:

```bash
# إصلاح صلاحيات filestore
sudo mkdir -p /var/lib/odoo/filestore/nbs_lugalai
sudo chown -R lugalai:lugalai /var/lib/odoo
sudo chmod -R 775 /var/lib/odoo
```

### إذا كانت الأقسام مفقودة:

```python
# داخل Odoo shell
env['nbs.department'].create({
    'name': 'عام',
    'code': 'GEN',
    'description': 'القسم العام'
})
env.cr.commit()
```

### إذا كانت أنواع المستندات مفقودة:

```python
# داخل Odoo shell
env['nbs.document.type'].create({
    'name': 'عام',
    'code': 'GEN',
    'description': 'نوع عام'
})
env.cr.commit()
```

---

## 🎯 الملخص

### السبب الأساسي:
```
المستند الذي تحاول رفع مرفق له غير موجود أو لا يمكن الوصول إليه
```

### الحل:
```
1. ✓ تأكد من وجود مستندات في النظام
2. ✓ استخدم document_id صحيح
3. ✓ تأكد من صلاحيات المستخدم
4. ✓ تأكد من JWT token صالح
5. ✓ استخدم API endpoint الصحيح
```

### الخطوات:
```bash
# 1. تشخيص
venv/bin/python fix_nbs_archive_attachments.py

# 2. إذا لم تكن هناك مستندات، أنشئ واحداً
# (السكريبت سيفعل ذلك تلقائياً)

# 3. جرب رفع مرفق مرة أخرى
# استخدم document_id من قائمة المستندات المتاحة
```

---

## 📞 للدعم

إذا استمرت المشكلة:

```bash
# 1. تحقق من اللوغات
tail -100 odoo.log

# 2. شغل السكريبت مرة أخرى
venv/bin/python fix_nbs_archive_attachments.py

# 3. تحقق من الاتصال
curl -I http://192.168.116.211:8069/api/documents
```

---

**تاريخ الإنشاء:** 29 يناير 2026  
**الحالة:** ✅ جاهز للاستخدام
