# دليل التثبيت السريع / Quick Installation Guide
# POS Perfume Custom Module

## خطوات التثبيت السريعة / Quick Installation Steps

### 1️⃣ التحقق من الموقع / Verify Location
```bash
cd L:\Lugal-ai
ls addons/pos_perfume_custom
```

الملفات المطلوبة / Required files:
- ✅ `__init__.py`
- ✅ `__manifest__.py`
- ✅ `models/`
- ✅ `views/`
- ✅ `static/`
- ✅ `security/`

### 2️⃣ تحديث قائمة التطبيقات / Update Apps List

**الطريقة 1 - من واجهة Odoo:**
```
1. Login to Odoo
2. Settings → Apps
3. Click "Update Apps List" (في القائمة المنسدلة)
4. Search: "POS Perfume"
```

**الطريقة 2 - من سطر الأوامر:**
```bash
# Windows PowerShell
cd L:\Lugal-ai
.\odoo-bin -c odoo.conf -d your_database -u pos_perfume_custom --stop-after-init
```

### 3️⃣ تفعيل الوضع المطور / Activate Developer Mode

```
Settings → General Settings
→ Developer Tools
→ Activate the developer mode
```

### 4️⃣ تثبيت الوحدة / Install Module

```
1. Settings → Apps
2. Remove "Apps" filter
3. Search: "pos_perfume_custom"
4. Click "Install"
```

### 5️⃣ التحقق من التثبيت / Verify Installation

```python
# في Odoo Shell
from odoo import api, SUPERUSER_ID

with api.Environment.manage():
    env = api.Environment(cr, SUPERUSER_ID, {})
    module = env['ir.module.module'].search([('name', '=', 'pos_perfume_custom')])
    print(f"Module State: {module.state}")
    # يجب أن يكون: installed
```

## التكوين / Configuration

### إضافة اسم عربي للمنتجات / Add Arabic Names to Products

```
1. Inventory → Products
2. Select a product
3. Add "Arabic Name" (اسم المنتج بالعربية)
4. Save
```

### مثال على المنتجات / Product Examples

```
Product: Vanilla Absolute
Arabic Name: فانيليا مطلقة
Code: PF001
Price: $45.00
```

## اختبار الواجهة / Test Interface

### 1. فتح POS / Open POS
```
Point of Sale → Dashboard → New Session
```

### 2. اختبار التنقل بالأسهم / Test Arrow Navigation

- انقر على أي خلية في جدول الطلب
- جرب الأسهم: ↑ ↓ ← →
- جرب Tab و Enter
- تأكد من:
  - ✅ التنقل العمودي (↑↓)
  - ✅ التنقل الأفقي (←→)
  - ✅ Enter ينقل للأسفل
  - ✅ Tab ينقل لليمين

### 3. اختبار الحسابات / Test Calculations

```
1. أضف منتج (Double-click)
2. غير الكمية → الحساب تلقائي
3. غير السعر → الحساب تلقائي
4. أضف خصم % → الحساب تلقائي
5. تحقق من:
   - ✅ السعر بعد الخصم
   - ✅ المجموع للسطر
   - ✅ المجموع الكلي (USD)
   - ✅ المجموع بالدينار (IQD)
```

## استكشاف الأخطاء / Troubleshooting

### ❌ المشكلة: الوحدة لا تظهر في قائمة التطبيقات
**الحل:**
```bash
# إعادة تشغيل Odoo
.\odoo-bin -c odoo.conf -d your_database --update=all
```

### ❌ المشكلة: واجهة POS لم تتغير
**الحل:**
```
1. إفراغ الكاش / Clear cache
2. إغلاق Session وفتح جديد
3. Ctrl+Shift+R (Hard refresh)
4. تحقق من تحميل ملفات JS/CSS في Developer Tools
```

### ❌ المشكلة: التنقل بالأسهم لا يعمل
**الحل:**
```javascript
// تحقق من Console في المتصفح
F12 → Console
// يجب ألا يكون هناك أخطاء JavaScript
```

### ❌ المشكلة: الحسابات غير صحيحة
**الحل:**
```
1. تحقق من قيم الإدخال (أرقام صحيحة)
2. تحقق من معدل التحويل IQD (1:1510)
3. راجع console للأخطاء
```

## الأوامر المفيدة / Useful Commands

### إعادة تثبيت الوحدة / Reinstall Module
```bash
.\odoo-bin -c odoo.conf -d your_database -u pos_perfume_custom
```

### حذف البيانات وإعادة التثبيت / Uninstall & Reinstall
```python
# في Odoo
Settings → Apps → Search "pos_perfume_custom"
→ Uninstall → Install
```

### تحديث الملفات الثابتة فقط / Update Assets Only
```bash
.\odoo-bin -c odoo.conf -d your_database -u pos_perfume_custom --update=assets
```

### عرض السجلات / Show Logs
```bash
.\odoo-bin -c odoo.conf -d your_database --log-level=debug
```

## التحقق من الأداء / Performance Check

### قياس سرعة التحميل / Measure Load Time
```javascript
// في Console المتصفح
console.time('POS Load');
// افتح POS
console.timeEnd('POS Load');
// يجب أن يكون أقل من 3 ثوانٍ
```

### قياس سرعة الحسابات / Measure Calculation Speed
```javascript
// في Console
console.time('Calculate');
// غير قيمة في الجدول
console.timeEnd('Calculate');
// يجب أن يكون أقل من 50ms
```

## الميزات المتقدمة / Advanced Features

### تخصيص معدل التحويل IQD / Customize IQD Exchange Rate

```javascript
// في: static/src/app/perfume_product_screen.js
formatIQD(amount) {
    const iqdAmount = amount * 1510; // غير هذا الرقم / Change this number
    return iqdAmount.toLocaleString('en-US') + ' IQD';
}
```

### تخصيص عدد الصفوف الافتراضية / Customize Default Rows

```javascript
// في: static/src/app/excel_order_table.js
getOrderLines() {
    const minRows = 5; // غير هذا الرقم / Change this number
    // ...
}
```

### تخصيص الألوان / Customize Colors

```scss
// في: static/src/scss/perfume_pos.scss
$primary-purple: #714B67; // غير هذا اللون
$excel-focus: #217346;    // لون التركيز
```

## الدعم الفني / Technical Support

### معلومات الإصدار / Version Info
- **Module**: pos_perfume_custom
- **Version**: 1.0.0
- **Odoo**: 17.0
- **Date**: October 23, 2025

### جهات الاتصال / Contact
- **Email**: support@lugal-ai.com
- **Website**: https://lugal-ai.com

---

## ملخص سريع / Quick Summary

✅ **تم بنجاح:**
1. ✅ تصميم واجهة 50/50
2. ✅ جدول طلبات Excel-like
3. ✅ **التنقل بالأسهم بين الخلايا** ← **الميزة الرئيسية**
4. ✅ حسابات تلقائية
5. ✅ دعم الأسماء العربية
6. ✅ تحويل تلقائي لـ IQD
7. ✅ نظام ألوان احترافي
8. ✅ أزرار إجراءات متعددة

🎯 **الميزة الأهم: التنقل بالأسهم (↑↓←→) في جدول الطلبات!**

---

Made with ❤️ by Lugal-AI




