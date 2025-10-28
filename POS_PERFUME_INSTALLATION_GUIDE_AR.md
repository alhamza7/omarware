# دليل تثبيت واجهة POS للعطور
# POS Perfume Interface - Installation Guide

## ✅ ما تم عمله / What Was Done

تم إصلاح وتطوير وحدة `pos_perfume_custom` بالكامل وهي الآن جاهزة للتثبيت!

### الميزات المضافة / Added Features:

1. **حقل الاسم العربي للمنتجات** - Arabic Product Names
   - إضافة حقل `name_arabic` في `product.template`
   - يظهر في واجهة المنتجات

2. **عرض الأسعار بالدينار العراقي** - IQD Price Display
   - سعر التحويل: 1 دولار = 1,300 دينار عراقي
   - يظهر تلقائياً بجانب السعر بالدولار

3. **تنسيقات مخصصة** - Custom Styling
   - ألوان بنفسجية مميزة (#714B67)
   - تصميم عصري وجميل

## 📋 خطوات التثبيت / Installation Steps

### الخطوة 1: التحقق من الملفات / Verify Files

تأكد من وجود الوحدة في:
```
L:\Lugal-ai\addons\pos_perfume_custom\
```

### الخطوة 2: إعادة تشغيل Odoo / Restart Odoo

**مهم جداً!** الوحدة في حالة "to install" وتحتاج إعادة تشغيل Odoo:

#### الطريقة 1: إعادة تشغيل عادية

1. أوقف Odoo الحالي (Ctrl+C)
2. شغّل Odoo من جديد:
```bash
cd L:\Lugal-ai
python odoo-bin -c odoo.conf
```

3. افتح المتصفح على: `http://localhost:8069`

#### الطريقة 2: التثبيت من Command Line

```bash
cd L:\Lugal-ai
python odoo-bin -c odoo.conf -d lugal -i pos_perfume_custom
```

ثم افتح المتصفح.

### الخطوة 3: التحقق من التثبيت / Verify Installation

1. اذهب إلى **Settings → Apps**
2. أزل فلتر "Apps" واختر "All"
3. ابحث عن: `pos_perfume_custom`
4. يجب أن ترى الحالة: **Installed** ✅

### الخطوة 4: إضافة أسماء عربية للمنتجات / Add Arabic Names

1. اذهب إلى **Inventory → Products**
2. افتح أي منتج
3. ستجد حقل جديد: **Arabic Name** (الاسم العربي)
4. أضف الأسماء العربية لمنتجاتك

### الخطوة 5: فتح POS / Open POS

1. اذهب إلى **Point of Sale**
2. افتح جلسة جديدة
3. ستلاحظ:
   - ✅ الأسعار معروضة بالدولار والدينار العراقي
   - ✅ الأسماء العربية تظهر للمنتجات
   - ✅ الألوان البنفسجية المميزة

## 🎨 الميزات التفصيلية / Detailed Features

### 1. الأسماء العربية / Arabic Names

```python
# في product.template
name_arabic = fields.Char(
    string='Arabic Name',
    help='اسم المنتج بالعربية'
)
```

**مثال:**
- English: "Vanilla Absolute"
- Arabic: "فانيليا مطلقة"

### 2. عرض الأسعار بالدينار / IQD Price Display

```javascript
formatIQD(amount) {
    const iqdAmount = amount * 1300;
    return `${iqdAmount.toLocaleString()} IQD`;
}
```

**مثال:**
- Price: $45.00
- IQD: 58,500 IQD

### 3. التنسيقات المخصصة / Custom Styling

```scss
$perfume-primary: #714B67;  // البنفسجي الأساسي
$perfume-secondary: #8B5A8E; // البنفسجي الثانوي
```

## 🔧 استكشاف الأخطاء / Troubleshooting

### المشكلة 1: الوحدة لا تظهر في Apps

**الحل:**
1. اذهب إلى Settings → Apps
2. اضغط "Update Apps List"
3. انتظر الانتهاء
4. ابحث عن "pos_perfume_custom"

### المشكلة 2: الوحدة في حالة "to install"

**الحل:**
أعد تشغيل Odoo بالكامل (الخطوة 2 أعلاه)

### المشكلة 3: لا تظهر الأسعار بالدينار

**الحل:**
1. تأكد أن الوحدة مثبتة
2. افتح POS من جديد (F5)
3. نظف الـ cache في المتصفح (Ctrl+Shift+Delete)

### المشكلة 4: الأسماء العربية لا تظهر

**الحل:**
1. تأكد أنك أضفت الأسماء العربية في صفحة المنتج
2. الحقل اسمه: "Arabic Name"
3. احفظ المنتج وافتح POS من جديد

## 📝 أمثلة للاستخدام / Usage Examples

### إضافة منتج عطور / Adding a Perfume Product

1. اذهب إلى Inventory → Products → Create
2. املأ البيانات:
   ```
   Name: Vanilla Absolute
   Arabic Name: فانيليا مطلقة
   Product Code: PF001
   Sales Price: $45.00
   ```
3. احفظ

4. افتح POS، ستجد:
   ```
   Vanilla Absolute
   فانيليا مطلقة
   $45.00 | 58,500 IQD
   ```

### تخصيص سعر التحويل / Customize Exchange Rate

إذا أردت تغيير سعر التحويل من 1,300 إلى رقم آخر:

1. افتح الملف:
   ```
   addons/pos_perfume_custom/static/src/app/perfume_enhancements.js
   ```

2. غيّر السطر:
   ```javascript
   const iqdAmount = amount * 1300; // غيّر 1300 إلى السعر المطلوب
   ```

3. أعد تشغيل Odoo وحدّث الوحدة:
   ```bash
   python odoo-bin -c odoo.conf -d lugal -u pos_perfume_custom
   ```

## 📊 بنية الوحدة / Module Structure

```
addons/pos_perfume_custom/
├── __init__.py
├── __manifest__.py              # إعدادات الوحدة
├── models/
│   ├── __init__.py
│   └── product_product.py       # حقل name_arabic
├── views/
│   └── pos_perfume_views.xml    # عرض الحقل في الواجهة
├── security/
│   └── ir.model.access.csv      # الصلاحيات
├── static/src/
│   ├── app/
│   │   └── perfume_enhancements.js   # كود JavaScript
│   ├── xml/
│   │   └── perfume_enhancements.xml  # قوالب الواجهة
│   └── scss/
│       └── perfume_pos.scss          # التنسيقات
└── README.md
```

## ✅ قائمة التحقق / Checklist

قبل الاستخدام، تأكد من:

- [ ] الوحدة في مجلد addons
- [ ] إعادة تشغيل Odoo
- [ ] الوحدة مثبتة (Installed)
- [ ] إضافة أسماء عربية للمنتجات
- [ ] فتح POS ورؤية التحسينات

## 🎉 النتيجة النهائية / Final Result

بعد التثبيت الصحيح، ستحصل على:

1. ✅ **واجهة POS محسّنة** مع دعم اللغة العربية
2. ✅ **عرض الأسعار بعملتين** (دولار ودينار عراقي)
3. ✅ **تصميم جميل** بالألوان البنفسجية
4. ✅ **سهولة الاستخدام** للعملاء الناطقين بالعربية

## 📞 المساعدة / Support

إذا واجهت أي مشاكل:

1. تحقق من سجلات Odoo:
   ```
   L:\Lugal-ai\odoo.log
   ```

2. شغّل سكريبت التحقق:
   ```bash
   cd L:\Lugal-ai
   python verify_pos_installation.py
   ```

3. أعد تثبيت الوحدة:
   ```bash
   python odoo-bin -c odoo.conf -d lugal -u pos_perfume_custom --stop-after-init
   ```

## 🚀 الخطوات التالية / Next Steps

لتحسينات مستقبلية:

1. إضافة المزيد من العملات
2. تقارير مخصصة للمبيعات
3. تكامل WhatsApp لإرسال الفواتير
4. واجهة Excel-like كاملة (نسخة متقدمة)

---

**تاريخ الإنشاء:** 23 أكتوبر 2025  
**النسخة:** 1.0.0  
**الحالة:** ✅ جاهز للاستخدام

---

Made with ❤️ by Lugal-AI Team

