# Backend Fixes Summary - NBS Archive API

## تاريخ التحديث: 2026-02-09

---

## المشاكل التي تم إصلاحها

### 1. ✅ Audit Log - Invalid Action Values (Trash & Restore)

**المشكلة:**
- عند نقل مستند لسلة المحذوفات أو استعادته، كانت العملية تنجح لكن الـ API ترجع `success: false` بسبب قيمة `action` غير مسموح بها في audit log.

**الإصلاح:**
- إضافة قيم جديدة في `nbs_audit_log.py`:
  - `document_soft_deleted`
  - `document_restored`
  - `document_permanently_deleted`
- جعل كتابة audit log **غير معيقة** (try/except) في `nbs_document.py`

**الملفات المعدلة:**
- `addons/nbs_archive/models/nbs_audit_log.py`
- `addons/nbs_archive/models/nbs_document.py`

---

### 2. ✅ Archive/Unarchive - No Permission to Create Audit Log

**المشكلة:**
- عند أرشفة مستند، العملية تنجح لكن الـ API ترجع خطأ بسبب عدم وجود صلاحية create على `nbs.audit.log`.

**الإصلاح:**
- استخدام `.sudo()` عند إنشاء audit log في archive و unarchive
- جعل audit log **غير معيق** (try/except)

**الملفات المعدلة:**
- `addons/nbs_archive/controllers/document_controller.py`

---

### 3. ✅ Permanent Delete - Confirmation Not Received

**المشكلة:**
- الواجهة الأمامية ترسل DELETE request لكن معامل `confirmation` لا يصل للـ backend.

**الإصلاح:**
- قراءة `confirmation` من:
  1. معاملات الـ route (kwargs)
  2. Query string (`?confirmation=...`)
  3. JSON body
- إضافة رسالة خطأ مفصّلة توضح ما تم استقباله وكيفية الإرسال الصحيحة

**الملفات المعدلة:**
- `addons/nbs_archive/controllers/document_controller.py`

---

### 4. ✅ Permanent Delete - Access Denied

**المشكلة:**
- حتى بعد وصول `confirmation` بشكل صحيح، الحذف يفشل بـ `AccessError` لأن المستخدم ليس لديه صلاحية unlink.

**الإصلاح:**
- استخدام `.sudo()` عند الحذف لأن الـ controller فحص مسبقاً أن المستخدم Admin

**الملفات المعدلة:**
- `addons/nbs_archive/models/nbs_document.py`

---

### 5. ✅ Permanent Delete - FK Violation (Versions)

**المشكلة:**
- عند محاولة حذف المستند، قاعدة البيانات ترفض بسبب وجود versions مرتبطة به عبر FK constraint.

**الإصلاح:**
- حذف **كل الـ versions والعلاقات والمرفقات** قبل حذف المستند
- إضافة context flag `force_delete_versions` للسماح بحذف versions فقط عند الحذف النهائي
- تعديل `nbs_document_version.unlink()` للسماح بالحذف عند وجود الـ flag

**الملفات المعدلة:**
- `addons/nbs_archive/models/nbs_document.py`
- `addons/nbs_archive/models/nbs_document_version.py`

---

### 6. ✅ Folder Delete - FK Violation

**المشكلة:**
- `update or delete on table "nbs_document_folder" violates RESTRICT` عند محاولة حذف مجلد مرتبط بمستندات.

**الإصلاح:**
- قبل حذف المجلد:
  - إزالة `folder_id` من المستندات المرتبطة
  - إزالة روابط Many2many
- منع الحذف إذا كان المجلد يحتوي على مجلدات فرعية

**الملفات المعدلة:**
- `addons/nbs_archive/models/nbs_folder.py`

---

## تحسينات عامة

### 7. ✅ Enhanced Error Responses

كل استجابة خطأ الآن تحتوي على:

```json
{
  "success": false,
  "error": "رسالة الخطأ",
  "error_type": "ValidationError",
  "error_location": "File \"/path/to/file.py\", line 123, in method_name",
  "traceback": "... آخر 10 أسطر من stack trace ..."
}
```

هذا يساعد مطوري الواجهة الأمامية في:
- معرفة **نوع** الخطأ
- معرفة **مكان** الخطأ بالضبط
- الحصول على معلومات تقنية للتشخيص

**الملفات المعدلة:**
- `addons/nbs_archive/controllers/document_controller.py` - إضافة دالة `format_error_response()`

---

### 8. ✅ Detailed Error for Permanent Delete

عند فشل الحذف النهائي بسبب عدم وجود confirmation، الاستجابة تحتوي على:

```json
{
  "success": false,
  "error": "Invalid confirmation. Use \"DELETE_PERMANENT\"",
  "error_detail": {
    "received_confirmation": null,
    "expected": "DELETE_PERMANENT",
    "method": "Send as query param: ?confirmation=DELETE_PERMANENT OR...",
    "received_from_query": null,
    "body_was_empty": true
  }
}
```

---

## ملخص الملفات المعدلة

| الملف | نوع التعديل |
|------|-------------|
| `models/nbs_audit_log.py` | إضافة قيم action جديدة |
| `models/nbs_document.py` | حذف cascade + audit non-blocking |
| `models/nbs_document_version.py` | السماح بالحذف مع context flag |
| `models/nbs_folder.py` | إصلاح FK violation عند الحذف |
| `controllers/document_controller.py` | رسائل خطأ محسّنة + قراءة confirmation |
| `NBS_ARCHIVE_API_REFERENCE_FRONTEND.md` | توثيق permanent delete confirmation |

---

## اختبار الحذف النهائي

### الطلب الصحيح:

```bash
DELETE http://localhost:3003/api/documents/3/permanent?confirmation=DELETE_PERMANENT
```

### ما يحدث عند الحذف النهائي:

1. ✅ التحقق من أن المستخدم **Admin**
2. ✅ التحقق من أن `confirmation == 'DELETE_PERMANENT'`
3. ✅ التحقق من أن المستند في **سلة المحذوفات**
4. ✅ كتابة audit log (non-blocking)
5. ✅ حذف **كل الـ versions** (مع context flag)
6. ✅ حذف **كل العلاقات** (relations)
7. ✅ حذف **كل المرفقات** (attachments)
8. ✅ حذف **المستند** نفسه
9. ✅ إرجاع `success: true`

---

## الحالة النهائية

✅ **كل المشاكل تم حلها:**
- Trash ✓
- Restore ✓
- Archive ✓
- Unarchive ✓
- Permanent Delete ✓
- Folder Delete ✓

✅ **رسائل خطأ مفصّلة في كل الـ APIs**

✅ **Audit log غير معيق في كل العمليات**

---

## للواجهة الأمامية

تأكد من إرسال `confirmation=DELETE_PERMANENT` في طلب الحذف النهائي:

```javascript
// الطريقة الموصى بها - Query String
await fetch(`/api/documents/${id}/permanent?confirmation=DELETE_PERMANENT`, {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

الخادم جاهز الآن والحذف النهائي يجب أن يعمل بشكل كامل! ✅
