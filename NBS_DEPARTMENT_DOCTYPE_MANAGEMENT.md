# 📋 إدارة الأقسام وأنواع المستندات - Department & Document Type Management

## 🎯 الميزات المضافة

تم إضافة نظام كامل لإدارة الأقسام وأنواع المستندات عبر API:
- ✅ Create (إضافة)
- ✅ Read (عرض)
- ✅ Update (تعديل)
- ✅ Delete (أرشفة)

---

## 📂 الأقسام (Departments)

### 1. عرض جميع الأقسام

```bash
POST /api/departments
```

**Request:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "include_inactive": false
    }
}
```

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "المشتريات",
            "code": "PUR",
            "description": "قسم المشتريات",
            "active": true,
            "sequence": 10,
            "manager_ids": [
                {"id": 5, "name": "أحمد محمد"}
            ],
            "document_count": 150
        }
    ]
}
```

---

### 2. عرض قسم واحد

```bash
POST /api/departments/{department_id}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "name": "المشتريات",
        "code": "PUR",
        "description": "قسم المشتريات",
        "active": true,
        "sequence": 10,
        "manager_ids": [
            {"id": 5, "name": "أحمد محمد"}
        ],
        "document_count": 150,
        "document_type_count": 8
    }
}
```

---

### 3. إنشاء قسم جديد

```bash
POST /api/departments/create
```

**Request:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "name": "الموارد البشرية",
        "code": "HR",
        "description": "قسم الموارد البشرية",
        "manager_ids": [5, 6],
        "sequence": 20
    }
}
```

**Response:**
```json
{
    "success": true,
    "message": "تم إنشاء القسم بنجاح",
    "data": {
        "id": 10,
        "name": "الموارد البشرية",
        "code": "HR"
    }
}
```

**الصلاحيات:**
- ✅ Admin فقط

---

### 4. تحديث قسم

```bash
POST /api/departments/{department_id}/update
```

**Request:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "name": "المشتريات والتوريد",
        "description": "قسم المشتريات والتوريد المركزي",
        "manager_ids": [5, 6, 7],
        "sequence": 15,
        "active": true
    }
}
```

**Response:**
```json
{
    "success": true,
    "message": "تم تحديث القسم بنجاح",
    "data": {
        "id": 1,
        "name": "المشتريات والتوريد",
        "code": "PUR"
    }
}
```

**الصلاحيات:**
- ✅ Admin فقط

**ملاحظات:**
- يمكن تحديث أي حقل بشكل منفصل
- إذا لم تمرر حقل، يبقى كما هو
- لا يمكن استخدام code موجود مسبقاً

---

### 5. حذف (أرشفة) قسم

```bash
DELETE /api/departments/{department_id}
```

**Response:**
```json
{
    "success": true,
    "message": "تم أرشفة القسم بنجاح"
}
```

**الصلاحيات:**
- ✅ Admin فقط

**ملاحظات:**
- ❌ لا يمكن حذف قسم يحتوي على مستندات
- ✅ يتم الأرشفة فقط (active = False)
- ✅ يمكن استرجاعه بتحديث active إلى True

---

## 📄 أنواع المستندات (Document Types)

### 1. عرض جميع أنواع المستندات

```bash
POST /api/document-types
```

**Request:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "department_id": 1,
        "include_inactive": false
    }
}
```

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "name": "فاتورة شراء",
            "code": "PINV",
            "description": "فواتير الشراء",
            "department_id": 1,
            "department_name": "المشتريات",
            "active": true,
            "sequence": 10,
            "document_count": 450
        }
    ]
}
```

---

### 2. عرض نوع مستند واحد

```bash
POST /api/document-types/{doc_type_id}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 1,
        "name": "فاتورة شراء",
        "code": "PINV",
        "description": "فواتير الشراء من الموردين",
        "department_id": 1,
        "department_name": "المشتريات",
        "active": true,
        "sequence": 10,
        "document_count": 450
    }
}
```

---

### 3. إنشاء نوع مستند جديد

```bash
POST /api/document-types/create
```

**Request:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "name": "أمر شراء",
        "code": "PO",
        "department_id": 1,
        "description": "أوامر الشراء",
        "sequence": 15
    }
}
```

**Response:**
```json
{
    "success": true,
    "message": "تم إنشاء نوع المستند بنجاح",
    "data": {
        "id": 25,
        "name": "أمر شراء",
        "code": "PO"
    }
}
```

**الصلاحيات:**
- ✅ Admin
- ✅ Manager

---

### 4. تحديث نوع مستند

```bash
POST /api/document-types/{doc_type_id}/update
```

**Request:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "name": "أمر شراء محلي",
        "description": "أوامر الشراء من الموردين المحليين",
        "sequence": 20,
        "active": true
    }
}
```

**Response:**
```json
{
    "success": true,
    "message": "تم تحديث نوع المستند بنجاح",
    "data": {
        "id": 25,
        "name": "أمر شراء محلي",
        "code": "PO"
    }
}
```

**الصلاحيات:**
- ✅ Admin
- ✅ Manager

---

### 5. حذف (أرشفة) نوع مستند

```bash
DELETE /api/document-types/{doc_type_id}
```

**Response:**
```json
{
    "success": true,
    "message": "تم أرشفة نوع المستند بنجاح"
}
```

**الصلاحيات:**
- ✅ Admin
- ✅ Manager

**ملاحظات:**
- ❌ لا يمكن حذف نوع مستند يحتوي على مستندات
- ✅ يتم الأرشفة فقط (active = False)
- ✅ يمكن استرجاعه بتحديث active إلى True

---

## 🔐 الصلاحيات (Permissions)

### الأقسام (Departments):
```
Action      | Admin | Manager | User
------------|-------|---------|------
View        |  ✅   |   ✅    |  ✅
Create      |  ✅   |   ❌    |  ❌
Update      |  ✅   |   ❌    |  ❌
Delete      |  ✅   |   ❌    |  ❌
```

### أنواع المستندات (Document Types):
```
Action      | Admin | Manager | User
------------|-------|---------|------
View        |  ✅   |   ✅    |  ✅
Create      |  ✅   |   ✅    |  ❌
Update      |  ✅   |   ✅    |  ❌
Delete      |  ✅   |   ✅    |  ❌
```

---

## ✅ الميزات

### الأقسام:
```
✅ CRUD كامل
✅ تعيين مدراء متعددين
✅ ترتيب حسب sequence
✅ حساب عدد المستندات
✅ حماية من الحذف إذا كان يحتوي مستندات
✅ أرشفة بدلاً من الحذف النهائي
✅ Audit logging لجميع العمليات
✅ التحقق من تكرار الـ code
```

### أنواع المستندات:
```
✅ CRUD كامل
✅ ربط مع قسم واحد
✅ ترتيب حسب sequence
✅ حساب عدد المستندات
✅ حماية من الحذف إذا كان يحتوي مستندات
✅ أرشفة بدلاً من الحذف النهائي
✅ Audit logging لجميع العمليات
✅ التحقق من تكرار الـ code
✅ Manager يمكنه الإدارة
```

---

## 🧪 أمثلة استخدام

### مثال 1: إنشاء قسم جديد

```bash
curl -X POST http://localhost:8070/api/departments/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "name": "المالية",
        "code": "FIN",
        "description": "قسم المالية والمحاسبة",
        "manager_ids": [5],
        "sequence": 30
    }
  }'
```

---

### مثال 2: تحديث قسم

```bash
curl -X POST http://localhost:8070/api/departments/1/update \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "name": "المشتريات والتوريد",
        "manager_ids": [5, 6, 7]
    }
  }'
```

---

### مثال 3: إنشاء نوع مستند

```bash
curl -X POST http://localhost:8070/api/document-types/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "name": "عقد توريد",
        "code": "SUP_CONTRACT",
        "department_id": 1,
        "description": "عقود التوريد مع الموردين"
    }
  }'
```

---

### مثال 4: حذف (أرشفة) نوع مستند

```bash
curl -X DELETE http://localhost:8070/api/document-types/25 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔄 Workflow مقترح

### لإنشاء هيكل كامل:

```javascript
// 1. إنشاء الأقسام
const departments = [
    {name: "المشتريات", code: "PUR"},
    {name: "المالية", code: "FIN"},
    {name: "الموارد البشرية", code: "HR"}
];

for (const dept of departments) {
    await createDepartment(dept);
}

// 2. إنشاء أنواع المستندات لكل قسم
const docTypes = [
    {name: "فاتورة شراء", code: "PINV", department_id: 1},
    {name: "أمر شراء", code: "PO", department_id: 1},
    {name: "كشف حساب", code: "STMT", department_id: 2},
    {name: "عقد عمل", code: "EMP_CONTRACT", department_id: 3}
];

for (const docType of docTypes) {
    await createDocumentType(docType);
}

// 3. الآن يمكن رفع المستندات
await uploadDocument({
    name: "فاتورة #12345",
    department_id: 1,
    document_type_id: 1,
    file_data: "base64..."
});
```

---

## 📊 Audit Log

جميع العمليات تُسجل في Audit Log:

```
- department_created: تم إنشاء قسم
- department_updated: تم تحديث قسم
- department_archived: تم أرشفة قسم
- document_type_created: تم إنشاء نوع مستند
- document_type_updated: تم تحديث نوع مستند
- document_type_archived: تم أرشفة نوع مستند
```

يمكن الاستعلام عنها عبر:
```bash
GET /api/audit-logs?action=department_created
```

---

## 🚀 التنفيذ

### تم إضافة الملفات:

```
✅ controllers/department_management_controller.py
   - 10 API endpoints جديدة
   - CRUD كامل للأقسام وأنواع المستندات
   
✅ controllers/__init__.py
   - تم تسجيل الـ controller الجديد
```

### للتفعيل:

```bash
# 1. تحديث المودل
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_local \
  -u nbs_archive --stop-after-init

# 2. إعادة تشغيل Odoo
pkill -f odoo-bin && ./start_local.sh

# 3. اختبر الـ APIs
curl -X POST http://localhost:8070/api/departments ...
```

---

## 📝 Checklist

```
✅ Department GET APIs
✅ Department CREATE API
✅ Department UPDATE API
✅ Department DELETE API
✅ Document Type GET APIs
✅ Document Type CREATE API
✅ Document Type UPDATE API
✅ Document Type DELETE API
✅ Permission checks
✅ Validation (duplicate codes)
✅ Audit logging
✅ Error handling
✅ Documentation
```

---

**تاريخ الإضافة:** 2026-02-07  
**الحالة:** ✅ جاهز للتطبيق  
**الصلاحيات:** Admin (Departments), Admin/Manager (Document Types)
