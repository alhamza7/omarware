# نظام الملاحظات - توثيق API
# Notes System - API Documentation

## 📋 نظرة عامة / Overview

تم إضافة نظام ملاحظات شامل يسمح للمستخدمين بإضافة ملاحظات على المستندات والفولدرات مع دعم رفع الصور.

A comprehensive notes system has been added allowing users to add notes to documents and folders with image upload support.

---

## ✨ الميزات الجديدة / New Features

### 1. نظام الملاحظات / Notes System
- ✅ إنشاء ملاحظات مرتبطة بالمستندات
- ✅ إنشاء ملاحظات مرتبطة بالفولدرات
- ✅ ملاحظات مستقلة (بدون ارتباط)
- ✅ رفع صورة مع الملاحظة
- ✅ ملاحظات خاصة أو عامة
- ✅ تثبيت الملاحظات المهمة
- ✅ ألوان مخصصة للملاحظات

### 2. حقول التحديث / Update Fields
- ✅ `last_modified` للفولدرات (يتضمن تعديلات المستندات والملاحظات)
- ✅ `last_modified` للمستندات (يتضمن تعديلات النسخ والملاحظات)
- ✅ `note_count` عدد الملاحظات للفولدرات والمستندات
- ✅ `user_note` حقل ملاحظة سريعة للفولدرات

---

## 🔐 المصادقة / Authentication

جميع APIs تتطلب JWT token في الـ header:
All APIs require JWT token in header:

```
Authorization: Bearer <access_token>
```

---

## 📝 APIs الملاحظات / Notes APIs

### 1. قائمة الملاحظات / List Notes

**Endpoint:** `POST /api/notes`  
**Type:** JSON-RPC

**المعاملات / Parameters:**
```json
{
  "document_id": 123,          // اختياري - تصفية حسب المستند / Optional - filter by document
  "folder_id": 50,             // اختياري - تصفية حسب الفولدر / Optional - filter by folder
  "user_id": null,             // افتراضي المستخدم الحالي / Default: current user
  "include_private": true,     // إظهار الملاحظات الخاصة / Show private notes
  "page": 1,
  "per_page": 50
}
```

**الاستجابة / Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "ملاحظة مهمة / Important Note",
      "content": "محتوى الملاحظة / Note content",
      "user_id": 2,
      "user_name": "أحمد / Ahmed",
      "document_id": 123,
      "document_title": "عقد / Contract",
      "folder_id": 50,
      "folder_name": "FIN-CONTRACT",
      "department_id": 2,
      "department_name": "Finance",
      "has_image": true,
      "image_filename": "screenshot.png",
      "is_private": false,
      "is_pinned": true,
      "color": 3,
      "created_at": "2026-02-11T12:00:00",
      "updated_at": "2026-02-11T13:30:00"
    }
  ],
  "pagination": {
    "total": 45,
    "page": 1,
    "per_page": 50,
    "total_pages": 1
  }
}
```

**مثال cURL:**
```bash
curl -X POST "http://localhost:8070/api/notes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "jsonrpc":"2.0",
    "method":"call",
    "params": {
      "document_id": 123,
      "page": 1,
      "per_page": 50
    },
    "id":1
  }'
```

---

### 2. عرض ملاحظة واحدة / Get Single Note

**Endpoint:** `POST /api/notes/<note_id>`  
**Type:** JSON-RPC

**الاستجابة / Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "ملاحظة / Note",
    "content": "المحتوى / Content",
    "user_id": 2,
    "user_name": "أحمد / Ahmed",
    "document_id": 123,
    "document_title": "عقد / Contract",
    "folder_id": 50,
    "folder_name": "FIN-CONTRACT",
    "department_id": 2,
    "department_name": "Finance",
    "image": "base64_encoded_image_string",
    "image_filename": "screenshot.png",
    "is_private": false,
    "is_pinned": true,
    "color": 3,
    "created_at": "2026-02-11T12:00:00",
    "updated_at": "2026-02-11T13:30:00"
  }
}
```

**مثال cURL:**
```bash
curl -X POST "http://localhost:8070/api/notes/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

---

### 3. إنشاء ملاحظة / Create Note

**Endpoint:** `POST /api/notes/create`  
**Type:** HTTP (Plain JSON)

**الجسم / Body:**
```json
{
  "content": "محتوى الملاحظة / Note content",           // مطلوب / Required
  "title": "عنوان الملاحظة / Note title",             // اختياري / Optional
  "document_id": 123,                                   // اختياري / Optional
  "folder_id": 50,                                      // اختياري / Optional
  "department_id": 2,                                   // اختياري / Optional
  "image": "base64_encoded_image",                      // اختياري / Optional
  "image_filename": "screenshot.png",                   // اختياري / Optional
  "is_private": true,                                   // افتراضي true / Default true
  "is_pinned": false,                                   // افتراضي false / Default false
  "color": 0                                            // افتراضي 0 / Default 0
}
```

**الاستجابة / Response:**
```json
{
  "success": true,
  "message": "Note created successfully",
  "data": {
    "id": 15,
    "created_at": "2026-02-11T14:00:00"
  }
}
```

**مثال cURL:**
```bash
curl -X POST "http://localhost:8070/api/notes/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "content": "هذه ملاحظة مهمة",
    "title": "ملاحظة عاجلة",
    "document_id": 123,
    "is_private": false,
    "is_pinned": true,
    "color": 3
  }'
```

---

### 4. تحديث ملاحظة / Update Note

**Endpoint:** `POST /api/notes/<note_id>/update`  
**Type:** HTTP (Plain JSON)

**الجسم / Body:**
```json
{
  "title": "عنوان محدث / Updated title",
  "content": "محتوى محدث / Updated content",
  "is_private": false,
  "is_pinned": true,
  "color": 5,
  "image": "base64_encoded_new_image",
  "image_filename": "new_image.png"
}
```

**ملاحظة:** فقط منشئ الملاحظة يمكنه التحديث  
**Note:** Only the creator can update the note

**الاستجابة / Response:**
```json
{
  "success": true,
  "message": "Note updated successfully",
  "data": {
    "updated_at": "2026-02-11T14:30:00"
  }
}
```

**مثال cURL:**
```bash
curl -X POST "http://localhost:8070/api/notes/15/update" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "content": "محتوى محدث",
    "is_pinned": true
  }'
```

---

### 5. حذف ملاحظة / Delete Note

**Endpoint:** `DELETE /api/notes/<note_id>`  
**Type:** HTTP

**ملاحظة:** الحذف ناعم (soft delete) - يتم تعيين `active=False`  
**Note:** Soft delete - sets `active=False`

**الاستجابة / Response:**
```json
{
  "success": true,
  "message": "Note deleted successfully"
}
```

**مثال cURL:**
```bash
curl -X DELETE "http://localhost:8070/api/notes/15" \
  -H "Authorization: Bearer <token>"
```

---

## 📁 تحديثات APIs الفولدرات / Folder APIs Updates

### الحقول الجديدة في الاستجابة / New Fields in Response

#### 1. `POST /api/folders/<folder_id>`
#### 2. `POST /api/folders/<folder_id>/documents`

**الحقول الإضافية / Additional Fields:**
```json
{
  "note_count": 5,                                    // عدد الملاحظات / Number of notes
  "user_note": "ملاحظة سريعة / Quick note",          // ملاحظة المستخدم / User note
  "last_modified": "2026-02-11T14:00:00"             // آخر تعديل / Last modified
}
```

**مثال استجابة كاملة / Full Response Example:**
```json
{
  "success": true,
  "folder": {
    "id": 50,
    "name": "FIN-CONTRACT-asd1_814",
    "code": "814",
    "description": "وصف الفولدر / Folder description",
    "department_id": 2,
    "department_name": "Finance",
    "document_count": 12,
    "note_count": 5,
    "user_note": "فولدر العقود المالية للربع الأول / Q1 financial contracts folder",
    "last_modified": "2026-02-11T14:00:00",
    "updated_at": "2026-02-11T13:45:00"
  }
}
```

---

### تحديث ملاحظة الفولدر / Update Folder Note

**Endpoint:** `POST /api/folders/<folder_id>/update`  
**Type:** JSON-RPC

**المعاملات / Parameters:**
```json
{
  "user_note": "ملاحظة جديدة للفولدر / New folder note",
  "name": "اسم جديد / New name",
  "description": "وصف جديد / New description"
}
```

**مثال cURL:**
```bash
curl -X POST "http://localhost:8070/api/folders/50/update" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "jsonrpc":"2.0",
    "method":"call",
    "params": {
      "user_note": "فولدر العقود المالية المهمة"
    },
    "id":1
  }'
```

---

## 📄 تحديثات APIs المستندات / Document APIs Updates

### الحقول الجديدة في الاستجابة / New Fields in Response

#### 1. `POST /api/documents` (List)
#### 2. `POST /api/documents/<id>` (Single)

**الحقول الإضافية / Additional Fields:**
```json
{
  "note_count": 3,                                   // عدد الملاحظات / Number of notes
  "last_modified": "2026-02-11T14:00:00"            // آخر تعديل / Last modified
}
```

**مثال استجابة / Response Example:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "title": "عقد مالي / Financial Contract",
    "department_id": 2,
    "department_name": "Finance",
    "document_type_id": 5,
    "document_type_name": "عقد / Contract",
    "uploader_id": 2,
    "uploader_name": "أحمد / Ahmed",
    "upload_date": "2026-01-15T10:00:00",
    "status": "active",
    "barcode": "DOC-123",
    "note_count": 3,
    "last_modified": "2026-02-11T14:00:00"
  }
}
```

---

## 🎨 أكواد الألوان / Color Codes

الأكواد المتاحة للملاحظات / Available codes for notes:

| Code | اللون / Color |
|------|--------------|
| 0    | افتراضي / Default |
| 1    | أحمر / Red |
| 2    | أزرق / Blue |
| 3    | أخضر / Green |
| 4    | أصفر / Yellow |
| 5    | برتقالي / Orange |
| 6    | بنفسجي / Purple |
| 7    | وردي / Pink |
| 8    | بني / Brown |
| 9    | رمادي / Gray |

---

## 🔒 الصلاحيات / Permissions

### الملاحظات / Notes

- **إنشاء:** أي مستخدم مصادق عليه  
  **Create:** Any authenticated user
  
- **القراءة:**  
  **Read:**
  - الملاحظات الخاصة: منشئها فقط  
    Private notes: Creator only
  - الملاحظات العامة: المدراء والإداريين في نفس القسم  
    Public notes: Managers and admins in same department
  
- **التحديث:** منشئ الملاحظة فقط  
  **Update:** Creator only
  
- **الحذف:** منشئ الملاحظة أو الإداري  
  **Delete:** Creator or admin

### حقل user_note للفولدرات / Folder user_note Field

- **التحديث:** المدراء والإداريين فقط  
  **Update:** Managers and admins only

---

## 📊 حساب last_modified

### للفولدرات / For Folders
```
last_modified = max(
    folder.write_date,
    max(document.write_date for all documents),
    max(note.write_date for all notes)
)
```

### للمستندات / For Documents
```
last_modified = max(
    document.write_date,
    max(version.write_date for all versions),
    max(note.write_date for all notes)
)
```

---

## ⚠️ ملاحظات مهمة / Important Notes

1. **الصور / Images:**
   - يجب أن تكون الصور بصيغة Base64
   - Images must be in Base64 format
   - الحد الأقصى الموصى به: 5MB
   - Recommended max size: 5MB

2. **الملاحظات الخاصة / Private Notes:**
   - افتراضياً جميع الملاحظات خاصة
   - By default all notes are private
   - يمكن تغييرها لعامة عند الإنشاء أو التحديث
   - Can be changed to public on create or update

3. **الحذف / Deletion:**
   - الحذف ناعم (soft delete)
   - Soft delete (sets active=False)
   - لا يتم حذف الملاحظات نهائياً من قاعدة البيانات
   - Notes are not permanently deleted from database

4. **الأداء / Performance:**
   - `last_modified` محسوب ديناميكياً (غير مخزن)
   - `last_modified` is computed dynamically (not stored)
   - قد يؤثر على الأداء في الفولدرات الكبيرة
   - May impact performance on large folders

---

## 📱 أمثلة الاستخدام / Usage Examples

### مثال 1: إنشاء ملاحظة مع صورة / Create Note with Image

```javascript
const imageBase64 = canvas.toDataURL('image/png').split(',')[1]; // Extract base64

const response = await fetch('http://localhost:8070/api/notes/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({
    content: 'ملاحظة مع صورة توضيحية',
    title: 'لقطة شاشة',
    document_id: 123,
    image: imageBase64,
    image_filename: 'screenshot.png',
    is_private: false,
    color: 3
  })
});
```

### مثال 2: عرض ملاحظات مستند / List Document Notes

```javascript
const response = await fetch('http://localhost:8070/api/notes', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'call',
    params: {
      document_id: 123,
      page: 1,
      per_page: 50
    },
    id: 1
  })
});
```

### مثال 3: تحديث ملاحظة الفولدر / Update Folder Note

```javascript
const response = await fetch('http://localhost:8070/api/folders/50/update', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'call',
    params: {
      user_note: 'فولدر العقود المالية - الربع الأول 2026'
    },
    id: 1
  })
});
```

---

## 🔧 استكشاف الأخطاء / Troubleshooting

### الخطأ: "Unauthorized"
- تحقق من JWT token في الـ header
- Check JWT token in header

### الخطأ: "Access denied"
- تحقق من صلاحيات المستخدم
- Check user permissions
- الملاحظات الخاصة يمكن الوصول إليها من قبل منشئها فقط
- Private notes are only accessible by their creator

### الخطأ: "Only creator can update"
- فقط منشئ الملاحظة يمكنه تحديثها
- Only the note creator can update it

### الخطأ: "Field 'content' is required"
- محتوى الملاحظة مطلوب
- Note content is required

---

## 📞 الدعم / Support

للمساعدة أو الاستفسارات:  
For help or inquiries:

- الموقع: http://localhost:8070
- Site: http://localhost:8070

---

**آخر تحديث / Last Updated:** 11 فبراير 2026 / February 11, 2026  
**الإصدار / Version:** 1.0.0
