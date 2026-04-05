# Document Role - Final Logic (Arabic/English)

## المنطق النهائي / Final Logic

### التعريفات / Definitions

#### `is_main_document` (Boolean)
**المنطق الصارم / Strict Logic:**
```python
is_main_document = (doc.folder_role == 'main')
```

**القاعدة / Rule:**
- ✅ فقط إذا كان `folder_role = 'main'` → `is_main_document = true`
- ❌ أي شيء آخر → `is_main_document = false`

**مثال / Example:**
```json
// وثيقة رئيسية / Main Document
{
  "folder_role": "main",
  "is_main_document": true
}

// وثيقة فرعية / Sub Document  
{
  "folder_role": "sub",
  "is_main_document": false
}

// وثيقة عادية (ليست في إضبارة) / Regular Document (not in folder)
{
  "folder_role": "other",
  "is_main_document": false
}
```

---

#### `document_role` (String)
**المنطق / Logic:**
```python
document_role = doc.folder_role or 'other'
```

**القيم الممكنة / Possible Values:**
- `"main"` - وثيقة رئيسية في إضبارة / Main document in folder
- `"sub"` - وثيقة فرعية / Sub document
- `"attachment"` - مرفق / Attachment
- `"other"` - وثيقة عادية (خارج نظام الإضبارات) / Regular document (outside folder system)

---

#### `relation_type` (String)
**المنطق / Logic:**
```python
relation_type = (
    'attachment' 
        if doc.folder_role == 'attachment' or (doc.parent_document_id and doc.is_attachment)
    else 'secondary_document' 
        if doc.folder_role == 'sub' or doc.parent_document_id
    else 'main' 
        if doc.folder_role == 'main'
    else 'other'
)
```

**القيم الممكنة / Possible Values:**
- `"main"` - وثيقة رئيسية / Main document
- `"secondary_document"` - وثيقة فرعية / Secondary document
- `"attachment"` - مرفق / Attachment
- `"other"` - غير مصنف / Unclassified

---

## أمثلة كاملة / Complete Examples

### 1. وثيقة رئيسية في إضبارة / Main Document in Folder
```json
{
  "id": 85,
  "title": "Main Contract.pdf",
  "folder_id": 60,
  "folder_role": "main",
  "parent_document_id": null,
  "is_attachment": false,
  
  "is_main_document": true,
  "document_role": "main",
  "relation_type": "main"
}
```

### 2. وثيقة فرعية / Sub Document
```json
{
  "id": 86,
  "title": "Amendment 1.pdf",
  "folder_id": 60,
  "folder_role": "sub",
  "parent_document_id": 85,
  "is_attachment": false,
  
  "is_main_document": false,
  "document_role": "sub",
  "relation_type": "secondary_document"
}
```

### 3. مرفق / Attachment
```json
{
  "id": 87,
  "title": "Supporting Document.pdf",
  "folder_id": 60,
  "folder_role": "attachment",
  "parent_document_id": 85,
  "is_attachment": true,
  
  "is_main_document": false,
  "document_role": "attachment",
  "relation_type": "attachment"
}
```

### 4. وثيقة عادية (خارج نظام الإضبارات) / Regular Document
```json
{
  "id": 88,
  "title": "Standalone Document.pdf",
  "folder_id": null,
  "folder_role": null,
  "parent_document_id": null,
  "is_attachment": false,
  
  "is_main_document": false,
  "document_role": "other",
  "relation_type": "other"
}
```

---

## متى يتم تعيين folder_role / When is folder_role Set?

### عند الرفع / On Upload

```javascript
// رفع وثيقة رئيسية / Upload Main Document
POST /api/documents/upload
{
  "upload_kind": "main",  // ← يُعيّن folder_role = 'main'
  "create_folder": true
}

// رفع وثيقة فرعية / Upload Sub Document
POST /api/documents/upload
{
  "upload_kind": "sub",  // ← يُعيّن folder_role = 'sub'
  "folder_id": 60,
  "parent_document_id": 85
}

// رفع مرفق / Upload Attachment
POST /api/documents/upload
{
  "upload_kind": "attachment",  // ← يُعيّن folder_role = 'attachment'
  "folder_id": 60,
  "parent_document_id": 85
}
```

### الوثائق القديمة / Legacy Documents

الوثائق التي تم رفعها قبل تطبيق نظام `folder_role`:
- `folder_role = null` أو `'other'`
- `is_main_document = false`
- `relation_type = 'other'`

---

## التحقق / Validation

### 1. الوثائق الرئيسية فقط / Main Documents Only
```javascript
const mainDocs = documents.filter(d => d.is_main_document === true);
// أو / or
const mainDocs = documents.filter(d => d.document_role === 'main');
```

### 2. الوثائق الفرعية فقط / Secondary Documents Only
```javascript
const subDocs = documents.filter(d => d.document_role === 'sub');
```

### 3. المرفقات فقط / Attachments Only
```javascript
const attachments = documents.filter(d => d.document_role === 'attachment');
```

### 4. الوثائق في نظام الإضبارات / Documents in Folder System
```javascript
const folderDocs = documents.filter(d => 
  d.document_role === 'main' || 
  d.document_role === 'sub' || 
  d.document_role === 'attachment'
);
```

### 5. الوثائق خارج نظام الإضبارات / Documents Outside Folder System
```javascript
const standaloneeDocs = documents.filter(d => d.document_role === 'other');
```

---

## الفرق عن السابق / Difference from Before

### قبل / Before ❌
```python
# كان يعتبر أي وثيقة بدون parent كـ main
is_main_document = not bool(doc.parent_document_id)
# النتيجة: كل الوثائق العادية تظهر كـ main
```

### الآن / Now ✅
```python
# فقط الوثائق التي folder_role='main'
is_main_document = (doc.folder_role == 'main')
# النتيجة: فقط الوثائق الرئيسية في الإضبارات تظهر كـ main
```

---

## ملخص / Summary

| Field | Main | Sub | Attachment | Other |
|-------|------|-----|------------|-------|
| `is_main_document` | ✅ `true` | ❌ `false` | ❌ `false` | ❌ `false` |
| `document_role` | `"main"` | `"sub"` | `"attachment"` | `"other"` |
| `relation_type` | `"main"` | `"secondary_document"` | `"attachment"` | `"other"` |
| `folder_role` | `"main"` | `"sub"` | `"attachment"` | `null`/`"other"` |
| `parent_document_id` | `null` | number | number | `null` |

---

## التطبيق / Deployment

```bash
# 1. إيقاف Odoo
pkill -f "odoo-bin -c odoo_local.conf"

# 2. إعادة التشغيل
bash start_local.sh

# 3. التحقق
curl -X POST http://localhost:8070/api/documents \
  -H "Authorization: Bearer TOKEN" \
  -d '{"page": 1, "per_page": 10}'
```

---

**تاريخ التحديث / Update Date:** 2026-02-14  
**الإصدار / Version:** 1.2 (Final)
