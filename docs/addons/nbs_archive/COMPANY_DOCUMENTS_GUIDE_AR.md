# دليل الشركات والمستندات - جاهز للاستخدام ✅

## 📌 الوضع الحالي

**كل شيء جاهز ويعمل!** النظام الآن يدعم:

1. ✅ ربط الفولدرات بالشركات
2. ✅ ربط المستندات بالشركات (ترث من الفولدر)
3. ✅ فلترة المستندات حسب الشركة
4. ✅ المستندات الرئيسية والفرعية والمرفقات كلها ترث نفس الشركة

---

## 🔗 كيف تعمل العلاقة

```
شركة ABC (company_id = 1)
    │
    ├─ فولدر المشتريات (company_id = 1)
    │   ├─ مستند رئيسي: فاتورة شراء (company_id = 1)
    │   ├─ مستند فرعي: ملحق الفاتورة (company_id = 1)
    │   └─ مرفق: صورة الفاتورة (company_id = 1)
    │
    └─ فولدر المبيعات (company_id = 1)
        ├─ مستند رئيسي: عقد بيع (company_id = 1)
        └─ مستند فرعي: ملحق العقد (company_id = 1)

شركة XYZ (company_id = 2)
    │
    └─ فولدر الشحن (company_id = 2)
        ├─ مستند رئيسي: بوليصة شحن (company_id = 2)
        └─ مستند فرعي: تأمين الشحن (company_id = 2)
```

---

## 🎯 الآليات المطبقة

### 1. الوراثة التلقائية
عند إنشاء مستند في فولدر له `company_id`:
- المستند يرث `company_id` **تلقائياً** من الفولدر
- يعمل للمستندات الرئيسية والفرعية والمرفقات

### 2. التحديث التلقائي
عند تغيير `company_id` للفولدر:
- **جميع المستندات** في الفولدر تتحدث تلقائياً

### 3. النقل التلقائي
عند نقل مستند من فولدر لآخر:
- يتحدث `company_id` تلقائياً ليطابق الفولدر الجديد

---

## 📡 الـ APIs الجاهزة

### 1️⃣ إنشاء فولدر مع شركة

**Endpoint:** `POST /api/folders/create`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "name": "فولدر مشتريات الشركة ABC",
    "code": "ABC-PUR",
    "department_id": 2,
    "company_id": 1
  },
  "id": 1
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 189,
    "name": "فولدر مشتريات الشركة ABC",
    "company_id": 1,
    "company_name": "ABC Company"
  }
}
```

---

### 2️⃣ رفع مستند رئيسي للفولدر

**Endpoint:** `POST /api/documents/upload`

```json
{
  "name": "فاتورة شراء رقم 123",
  "department_id": 2,
  "document_type_id": 1,
  "folder_id": 189,
  "folder_role": "main"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 264,
    "name": "فاتورة شراء رقم 123",
    "folder_id": 189,
    "folder_name": "فولدر مشتريات الشركة ABC",
    "company_id": 1,          // ← ورث من الفولدر تلقائياً
    "company_name": "ABC Company",  // ← ورث من الفولدر تلقائياً
    "folder_role": "main"
  }
}
```

---

### 3️⃣ رفع مستند فرعي

**Endpoint:** `POST /api/documents/upload`

```json
{
  "name": "ملحق الفاتورة",
  "department_id": 2,
  "document_type_id": 1,
  "folder_id": 189,
  "parent_document_id": 264,
  "folder_role": "sub"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 265,
    "name": "ملحق الفاتورة",
    "folder_id": 189,
    "parent_document_id": 264,
    "company_id": 1,          // ← نفس شركة الفولدر والمستند الرئيسي
    "company_name": "ABC Company",
    "folder_role": "sub"
  }
}
```

---

### 4️⃣ فلترة المستندات حسب الشركة

**Endpoint:** `POST /api/documents`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "company_id": 1,
    "page": 1,
    "per_page": 20
  },
  "id": 1
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 264,
      "name": "فاتورة شراء رقم 123",
      "company_id": 1,
      "company_name": "ABC Company",
      "folder_role": "main"
    },
    {
      "id": 265,
      "name": "ملحق الفاتورة",
      "company_id": 1,
      "company_name": "ABC Company",
      "folder_role": "sub"
    }
  ],
  "pagination": {
    "total": 2,
    "page": 1,
    "per_page": 20
  }
}
```

---

### 5️⃣ عرض مستند واحد

**Endpoint:** `POST /api/documents/<document_id>`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 264,
    "name": "فاتورة شراء رقم 123",
    "company_id": 1,
    "company_name": "ABC Company",
    "folder_id": 189,
    "folder_name": "فولدر مشتريات الشركة ABC",
    "folder_role": "main",
    "department_id": 2,
    "document_type_id": 1
  }
}
```

---

### 6️⃣ عرض المستندات في فولدر

**Endpoint:** `POST /api/folders/<folder_id>/documents`

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {},
  "id": 1
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 264,
      "name": "فاتورة شراء رقم 123",
      "company_id": 1,           // ← نفس الشركة للفولدر
      "company_name": "ABC Company",
      "folder_role": "main"
    },
    {
      "id": 265,
      "name": "ملحق الفاتورة",
      "company_id": 1,           // ← نفس الشركة للفولدر
      "company_name": "ABC Company",
      "folder_role": "sub"
    }
  ]
}
```

---

## 🔍 سيناريوهات الاستخدام

### سيناريو 1: شركة جديدة
```
1. إنشاء شركة جديدة عبر POST /api/companies/create
2. إنشاء فولدرات للشركة مع company_id
3. رفع مستندات للفولدرات
4. ✓ جميع المستندات ترث company_id تلقائياً
```

### سيناريو 2: فلترة حسب الشركة
```
1. المستخدم يختار شركة من القائمة
2. استدعاء POST /api/documents مع company_id
3. ✓ الحصول على جميع المستندات (رئيسية وفرعية) للشركة
```

### سيناريو 3: نقل مستندات بين شركات
```
1. نقل مستند من فولدر شركة A إلى فولدر شركة B
2. ✓ company_id يتحدث تلقائياً من A إلى B
```

---

## 📊 البيانات المُرجعة في كل استجابة

كل استجابة للمستندات تتضمن:

```json
{
  "company_id": 1,          // رقم الشركة (أو null إذا لم يكن للفولدر شركة)
  "company_name": "ABC",    // اسم الشركة (أو null)
  "folder_id": 189,         // رقم الفولدر
  "folder_name": "...",     // اسم الفولدر
  "folder_role": "main"     // دور المستند (main/sub/attachment)
}
```

---

## ✅ الحالة الحالية

| الميزة | الحالة |
|--------|---------|
| ربط الفولدرات بالشركات | ✅ جاهز |
| وراثة المستندات للشركة من الفولدر | ✅ جاهز |
| فلترة المستندات حسب الشركة | ✅ جاهز |
| company_id في استجابة API | ✅ جاهز |
| company_name في استجابة API | ✅ جاهز |
| المستندات الرئيسية ترث الشركة | ✅ جاهز |
| المستندات الفرعية ترث الشركة | ✅ جاهز |
| المرفقات ترث الشركة | ✅ جاهز |
| تحديث تلقائي عند تغيير شركة الفولدر | ✅ جاهز |

---

## 🚀 جاهز للاختبار

النظام جاهز **100%** للاختبار. يمكن للـ FE:

1. ✅ إنشاء فولدرات مع `company_id`
2. ✅ رفع مستندات للفولدرات
3. ✅ الحصول على `company_id` و `company_name` في الاستجابة
4. ✅ فلترة المستندات حسب `company_id`

---

## 📝 ملاحظات مهمة

1. **التلقائية:** لا حاجة لإرسال `company_id` عند رفع المستند - يُحسب تلقائياً من الفولدر
2. **الشمولية:** جميع أنواع المستندات (main/sub/attachment) ترث نفس الشركة
3. **التحديث:** عند تحديث شركة الفولدر، تتحدث جميع المستندات تلقائياً
4. **الفلترة:** يمكن فلترة المستندات حسب الشركة عبر `company_id` parameter

---

## 🎉 الخلاصة

**كل ما طلبته موجود ويعمل!**

- ✅ الفولدرات مرتبطة بالشركات
- ✅ المستندات ترث الشركة من الفولدر
- ✅ المستندات الرئيسية والفرعية تتبع نفس الشركة
- ✅ يمكن فلترة المستندات حسب الشركة

**النظام جاهز للاختبار والاستخدام الآن! 🚀**
