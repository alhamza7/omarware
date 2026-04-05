# ✅ تم تثبيت واجهة POS للعطور بنجاح!
# POS Perfume Module Successfully Installed!

## 🎊 التثبيت مكتمل / Installation Complete

```
✅ Module Name: pos_perfume_custom
✅ State: INSTALLED
✅ Version: 19.0.1.0.0
```

---

## 🚀 كيفية الاستخدام / How to Use

### الخطوة 1: شغّل Odoo / Start Odoo

```bash
cd L:\Lugal-ai
python odoo-bin -c odoo.conf
```

ثم افتح المتصفح على: **http://localhost:8069**

---

### الخطوة 2: أضف الأسماء العربية للمنتجات / Add Arabic Names

1. اذهب إلى: **Inventory → Products → Products**
2. افتح أي منتج موجود أو أنشئ منتج جديد
3. ستجد حقل جديد اسمه: **"Arabic Name"** (الاسم العربي)
4. املأ الحقل بالاسم العربي للمنتج

**مثال:**

| English Name | Arabic Name |
|-------------|-------------|
| Vanilla Absolute | فانيليا مطلقة |
| Oud Wood Oriental | عود خشبي شرقي |
| Rose Bulgarian | ورد بلغاري |

5. احفظ المنتج ✅

---

### الخطوة 3: افتح POS / Open POS

1. من القائمة الرئيسية، اذهب إلى: **Point of Sale**
2. اختر نقطة البيع الخاصة بك
3. اضغط **"New Session"** لفتح جلسة جديدة

---

## 🎨 الميزات الجديدة / New Features

### 1️⃣ عرض الأسعار بالدينار العراقي

في واجهة POS، ستجد الأسعار معروضة بعملتين:

```
Vanilla Absolute
$45.00
58,500 IQD  ← جديد!
```

**سعر التحويل:** 1 USD = 1,300 IQD

### 2️⃣ الأسماء العربية

إذا أضفت اسماً عربياً للمنتج، سيظهر تحت الاسم الإنجليزي:

```
Vanilla Absolute
فانيليا مطلقة  ← جديد!
$45.00 | 58,500 IQD
```

### 3️⃣ تصميم محسّن

- ألوان بنفسجية أنيقة (#714B67)
- تنسيق أفضل لعرض الأسعار
- واجهة أكثر احترافية

---

## 📝 مثال عملي / Practical Example

### إنشاء منتج عطور كامل:

1. **اذهب إلى:** Inventory → Products → Create

2. **املأ البيانات:**
   ```
   Product Name: Vanilla Absolute
   Arabic Name: فانيليا مطلقة
   Internal Reference: PF001
   Sales Price: 45.00
   Cost: 30.00
   Product Type: Storable Product
   ```

3. **احفظ المنتج**

4. **افتح POS**

5. **النتيجة في POS:**
   ```
   ┌─────────────────────────────┐
   │  Vanilla Absolute           │
   │  فانيليا مطلقة              │
   │  ─────────────────────────  │
   │  $45.00                     │
   │  58,500 IQD                 │
   └─────────────────────────────┘
   ```

---

## 🔧 تخصيص سعر الصرف / Customize Exchange Rate

إذا أردت تغيير سعر الصرف (حالياً 1 USD = 1,300 IQD):

1. افتح الملف:
   ```
   L:\Lugal-ai\addons\pos_perfume_custom\static\src\app\perfume_enhancements.js
   ```

2. ابحث عن السطر:
   ```javascript
   const iqdAmount = amount * 1300;
   ```

3. غيّر `1300` إلى السعر المطلوب (مثلاً `1450`)

4. احفظ الملف

5. أعد تشغيل Odoo:
   ```bash
   # أوقف Odoo (Ctrl+C)
   # ثم شغّله من جديد
   python odoo-bin -c odoo.conf
   ```

---

## 📊 بيانات تجريبية / Demo Data

لتجربة سريعة، أنشئ هذه المنتجات:

| Code  | Name EN | Name AR | Price |
|-------|---------|---------|-------|
| PF001 | Vanilla Absolute | فانيليا مطلقة | $45.00 |
| PF002 | Oud Wood Oriental | عود خشبي شرقي | $125.00 |
| PF003 | Rose Bulgarian | ورد بلغاري | $68.50 |
| PF004 | Musk White | مسك أبيض | $280.00 |
| PF005 | Lavender French | خزامى فرنسي | $32.75 |

---

## ✅ قائمة التحقق / Checklist

تأكد من:

- [x] الوحدة مثبتة (installed) ✅
- [ ] تم إضافة أسماء عربية لبعض المنتجات
- [ ] تم فتح POS والتحقق من عرض الأسعار بالدينار
- [ ] تم التحقق من ظهور الأسماء العربية

---

## 🎯 ماذا بعد؟ / What's Next?

### الميزات المتقدمة (اختيارية):

إذا أردت المزيد من التخصيص:

1. **تقارير مخصصة** للمبيعات بالدينار العراقي
2. **طباعة الفواتير** بالعربية
3. **إضافة عملات أخرى**
4. **واجهة Excel-like كاملة** (كما في التصميم الأصلي)

---

## 📞 المساعدة / Support

إذا واجهت أي مشكلة:

### 1. تحقق من حالة الوحدة:
```bash
cd L:\Lugal-ai
python verify_pos_installation.py
```

### 2. تحقق من السجلات:
```bash
Get-Content odoo.log -Tail 100
```

### 3. أعد تحديث الوحدة:
```bash
python odoo-bin -c odoo.conf -d lugal -u pos_perfume_custom --stop-after-init
```

---

## 🎉 الخلاصة / Summary

تم بنجاح:

✅ **تثبيت الوحدة** في Odoo  
✅ **إضافة حقل الاسم العربي** للمنتجات  
✅ **عرض الأسعار بالدينار** في POS  
✅ **تحسين التصميم** بالألوان البنفسجية  

**الآن يمكنك استخدام POS مع دعم كامل للغة العربية والدينار العراقي!** 🎊

---

**تاريخ التثبيت:** 23 أكتوبر 2025  
**الحالة:** ✅ مثبت وجاهز للاستخدام  
**النسخة:** 19.0.1.0.0

Made with ❤️ by Lugal-AI Team

