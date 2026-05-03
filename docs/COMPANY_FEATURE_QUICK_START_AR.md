# دليل البدء السريع - ميزة الشركات/البراندات

## 🚀 البدء السريع

### الخطوة 1: إضافة شركات

```bash
# إضافة شركة
POST /api/companies/create
{
  "name": "شركة الأمل",
  "phone": "+962777123456",
  "email": "info@amal.jo"
}

# الاستجابة:
{
  "success": true,
  "data": {
    "id": 10,
    "name": "شركة الأمل"
  }
}
```

### الخطوة 2: إنشاء إضبارات للشركة

```bash
POST /api/folders/create
{
  "name": "عقود 2024",
  "code": "CONTRACTS-2024",
  "department_id": 4,
  "company_id": 10  ← ربط بالشركة
}
```

### الخطوة 3: عرض إضبارات الشركة

```bash
POST /api/folders
{
  "company_id": 10  ← فلترة حسب الشركة
}
```

---

## 📋 الـ API الجديدة

### 1. قائمة الشركات
```
POST /api/companies
```

### 2. تفاصيل شركة
```
POST /api/companies/<id>
```

### 3. إنشاء شركة
```
POST /api/companies/create
```

### 4. إحصائيات شركة
```
POST /api/companies/<id>/stats
```

---

## 🎯 الاستخدام

### الفلترة في الإضبارات:
```json
POST /api/folders
{"company_id": 10}
```

### الفلترة في الوثائق:
```json
POST /api/documents  
{"company_id": 10}
```

### إنشاء إضبارة مع شركة:
```json
POST /api/folders/create
{
  "name": "إضبارة جديدة",
  "department_id": 4,
  "company_id": 10
}
```

---

## ✅ الحالة

- ✅ جميع التغييرات مطبقة
- ✅ Odoo قيد التحديث
- ✅ الميزة جاهزة

**بعد اكتمال التحديث، يمكنك استخدام الميزة مباشرة!** 🎉
