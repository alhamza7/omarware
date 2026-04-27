# 🧪 اختبار SAP Label Printer API باستخدام Postman

## 📦 الملفات المرفقة

1. **`Odoo_SAP_Label_Printer.postman_collection.json`** - مجموعة الطلبات
2. **`Odoo_SAP_Label_Printer.postman_environment.json`** - متغيرات البيئة

---

## 🚀 كيفية الاستخدام

### الخطوة 1: استيراد الملفات في Postman

1. افتح **Postman**
2. اضغط **Import** في الزاوية العلوية اليسرى
3. اسحب الملفين أو اختر **Upload Files**:
   - `Odoo_SAP_Label_Printer.postman_collection.json`
   - `Odoo_SAP_Label_Printer.postman_environment.json`

### الخطوة 2: إعداد المتغيرات

1. اختر **Environment** من القائمة العلوية
2. اختر **"Odoo SAP Label Printer - Local"**
3. اضغط على أيقونة **العين** 👁️ لعرض المتغيرات
4. عدّل القيم:
   - `sap_username`: اسم المستخدم في SAP
   - `sap_password`: كلمة المرور في SAP
   - `sap_company_db`: اسم قاعدة بيانات الشركة
   - `odoo_login`: اسم المستخدم في Odoo
   - `odoo_password`: كلمة المرور في Odoo
   - `template_id`: رقم قالب الليبل (3 هو الافتراضي)

---

## 📝 ترتيب الطلبات

### المجموعة 1: SAP Service Layer

#### 1.1 Login to SAP ✅
- **الغرض**: تسجيل الدخول في SAP والحصول على Session ID
- **ملاحظة**: يحفظ `sap_session_id` تلقائياً

#### 1.2 Search Product by Barcode (Main Items)
- **الغرض**: البحث عن منتج في Items الرئيسية بالباركود
- **الباركود الافتراضي**: `20493`

#### 1.3 Get Items with UoM Sub-Units
- **الغرض**: جلب المنتجات مع وحدات القياس الفرعية
- **ملاحظة**: يرجع 100 منتج، ابحث يدوياً عن الباركود في `ItemUnitOfMeasurementCollection`

#### 1.4 Get Specific Item with UoM
- **الغرض**: جلب منتج محدد مع وحدات القياس
- **ملاحظة**: استبدل `'ITEM_CODE'` بكود المنتج الفعلي

---

### المجموعة 2: Odoo Authentication

#### 2.1 Login to Odoo ✅
- **الغرض**: تسجيل الدخول في Odoo والحصول على Session ID
- **ملاحظة**: يحفظ `odoo_session_id` تلقائياً

---

### المجموعة 3: Odoo SAP Label Printer

#### 3.1 SAP Product Lookup (by Barcode) ⭐
- **الغرض**: البحث عن منتج في SAP عن طريق Odoo
- **الباركود**: `20493`
- **النتيجة المتوقعة**:
```json
{
  "success": true,
  "product_id": 123,
  "product_name": "اسم المنتج",
  "sap_product_name": "اسم المنتج من SAP",
  "sap_uom": "وحدة القياس الفرعية",
  "barcode": "20493"
}
```

#### 3.2 Print Label
- **الغرض**: طباعة ليبل لمنتج
- **ملاحظة**: عدّل `product_id` بالرقم الذي حصلت عليه من 3.1

#### 3.3 Get SAP Label Printer Page
- **الغرض**: فتح صفحة واجهة الطباعة
- **النتيجة**: HTML للواجهة

---

### المجموعة 4: Test Different Barcodes

طلبات جاهزة لاختبار باركودات مختلفة:
- `20493` (UoM sub-unit)
- `4479`
- `7749`

---

## 🎯 سيناريو الاختبار الكامل

### الاختبار 1: من SAP مباشرة

```
1. 1.1 Login to SAP
   → احصل على SAP Session ID
   
2. 1.2 Search Product by Barcode
   → ابحث عن 20493 في Items الرئيسية
   → النتيجة: value: [] (فارغ)
   
3. 1.3 Get Items with UoM Sub-Units
   → جلب جميع المنتجات مع UoM
   → ابحث يدوياً في النتيجة عن:
     "ItemUnitOfMeasurementCollection": [
       {
         "BarCode": "20493",
         "UoMCode": "PCS",
         "UoMName": "Piece"
       }
     ]
   → ✅ وُجد!
```

### الاختبار 2: عن طريق Odoo

```
1. 2.1 Login to Odoo
   → احصل على Odoo Session ID
   
2. 3.1 SAP Product Lookup
   → أرسل barcode: "20493"
   → Odoo يبحث في SAP تلقائياً
   → النتيجة:
     {
       "success": true,
       "sap_product_name": "...",
       "sap_uom": "..."
     }
   → ✅ نجح!
```

---

## 🔍 نصائح الاختبار

### 1. تفعيل SSL Certificate Verification

إذا كان SAP يستخدم شهادة self-signed:

1. في Postman، اذهب إلى **Settings** (⚙️)
2. **General** → أوقف **SSL certificate verification**

### 2. عرض الـ Logs

في كل طلب، افتح تبويب **Console** في Postman لرؤية:
- الـ Requests الكاملة
- الـ Responses
- الأخطاء

### 3. حفظ Session IDs

الـ Scripts في الطلبات تحفظ تلقائياً:
- `sap_session_id` من SAP Login
- `odoo_session_id` من Odoo Login

يمكنك استخدامها في الطلبات اللاحقة عن طريق:
```
{{sap_session_id}}
{{odoo_session_id}}
```

---

## 🐛 استكشاف الأخطاء

### خطأ: "Invalid session"

**الحل**:
1. أعد تشغيل طلب Login (1.1 أو 2.1)
2. تأكد من أن Session ID محفوظ في المتغيرات

### خطأ: "Product not found"

**الحل**:
1. تحقق من أن الباركود موجود فعلاً في SAP
2. جرب 1.3 للبحث في UoM sub-units
3. تأكد من أن المنتج نشط في SAP (Valid = 'Y')

### خطأ: "Connection refused"

**الحل**:
1. تأكد من أن Odoo Server يعمل على port 8070
2. تأكد من أن SAP Service Layer يعمل

---

## 📊 مثال على Response ناجح

### من SAP (1.3 Get Items with UoM):

```json
{
  "odata.metadata": "...",
  "value": [
    {
      "ItemCode": "PROD001",
      "ItemName": "منتج تجريبي",
      "ItemUnitOfMeasurementCollection": [
        {
          "UoMEntry": 1,
          "UoMCode": "BOX",
          "UoMName": "صندوق",
          "BarCode": "111111"
        },
        {
          "UoMEntry": 2,
          "UoMCode": "PCS",
          "UoMName": "قطعة",
          "BarCode": "20493"
        }
      ]
    }
  ]
}
```

### من Odoo (3.1 SAP Product Lookup):

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "product_id": 456,
    "product_name": "منتج تجريبي",
    "sap_product_name": "منتج تجريبي",
    "sap_uom": "قطعة",
    "barcode": "20493",
    "price": 10.0,
    "code": "PROD001",
    "sap_item_code": "PROD001",
    "print_url": "/report/pdf/product_label_designer.report_label_simple/456?template_id=3"
  }
}
```

---

## 📞 الدعم

إذا واجهت أي مشاكل:

1. **راجع الـ Logs في Postman Console**
2. **راجع الـ Logs في Odoo**:
   ```powershell
   Get-Content "L:\Lugal-ai\odoo.log" -Tail 50
   ```
3. **تحقق من SAP Service Layer** أنه يعمل بشكل صحيح

---

**تاريخ الإنشاء**: ديسمبر 2024  
**الإصدار**: 1.0  
**المطور**: Lugal AI

