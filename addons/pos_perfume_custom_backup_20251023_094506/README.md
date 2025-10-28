# POS Perfume Custom - واجهة POS مخصصة للعطور

## الوصف / Description

وحدة مخصصة لنظام نقاط البيع (POS) مصممة خصيصًا لمتاجر العطور مع واجهة مستخدم محسّنة بتصميم Excel-like.

Custom POS interface module designed specifically for perfume stores with an Excel-like interface.

## المميزات / Features

### ✨ الميزات الرئيسية / Main Features

1. **واجهة 50/50 مقسمة / 50/50 Split Interface**
   - قسم يسار: جدول الطلبات (Excel-like)
   - قسم يمين: بحث وعرض المنتجات
   - Left: Order table (Excel-like)
   - Right: Product search and display

2. **جدول طلبات يشبه Excel / Excel-like Order Table**
   - خلايا قابلة للتعديل مباشرة / Direct editable cells
   - **التنقل بالأسهم (↑↓←→) / Arrow key navigation**
   - Tab و Enter للانتقال بين الخلايا / Tab and Enter to move between cells
   - حسابات تلقائية / Auto-calculations
   - ألوان مميزة للخلايا المختلفة / Distinctive colors for different cells

3. **التنقل بلوحة المفاتيح / Keyboard Navigation**
   - **Arrow Up (↑)**: الانتقال للصف السابق / Move to previous row
   - **Arrow Down (↓)** أو **Enter**: الانتقال للصف التالي / Move to next row
   - **Arrow Left (←)**: الانتقال للعمود السابق / Move to previous column
   - **Arrow Right (→)** أو **Tab**: الانتقال للعمود التالي / Move to next column
   - تحديد النص تلقائيًا عند التركيز / Auto-select text on focus

4. **بحث متقدم عن المنتجات / Advanced Product Search**
   - بحث بالاسم الإنجليزي والعربي / Search by English and Arabic names
   - بحث بالكود والباركود / Search by code and barcode
   - فلاتر حسب الحجم (100ml, 50ml, 1 Kilo, 100gm) / Size filters
   - فلاتر حسب العلامة التجارية / Brand filters

5. **حسابات تلقائية / Auto-Calculations**
   - حساب السعر بعد الخصم / Price after discount calculation
   - حساب المجموع الفرعي / Subtotal calculation
   - حساب الخصم الإجمالي / Total discount calculation
   - **تحويل تلقائي للدينار العراقي (USD → IQD)** / Auto IQD conversion

6. **نظام ألوان احترافي / Professional Color Scheme**
   - لون أساسي بنفسجي (#714B67) / Primary purple color
   - خلفية خضراء للسعر بعد الخصم / Green background for after-discount
   - خلفية برتقالية للمجموع / Orange background for total
   - تمييز أخضر عند التركيز (Excel-style) / Green focus highlight

7. **أزرار إجراءات / Action Buttons**
   - 📋 عرض سعر / Quotation
   - ✅ طلب بيع / Sale Order
   - 💾 حفظ مسودة / Save Draft
   - 🚫 إلغاء / Cancel
   - 📱 إرسال واتساب / Send WhatsApp

8. **دعم الأسماء العربية / Arabic Names Support**
   - حقل خاص للاسم العربي للمنتج / Arabic name field for products
   - عرض ثنائي اللغة / Bilingual display

## التثبيت / Installation

### 1. نسخ الوحدة / Copy Module

```bash
cp -r pos_perfume_custom /path/to/odoo/addons/
```

### 2. تحديث قائمة الوحدات / Update App List

```python
# في Odoo / In Odoo
Settings → Apps → Update Apps List
```

### 3. تثبيت الوحدة / Install Module

```python
# البحث عن / Search for: POS Perfume Design
Settings → Apps → Search "POS Perfume Design" → Install
```

### 4. إعادة تشغيل Odoo / Restart Odoo

```bash
# Windows PowerShell
Restart-Service odoo-service

# أو / or
./odoo-bin -u pos_perfume_custom -d your_database
```

## الاستخدام / Usage

### فتح واجهة POS / Open POS Interface

1. اذهب إلى Point of Sale → Dashboard
2. اختر نقطة البيع الخاصة بك / Select your POS
3. انقر على "New Session" / Click "New Session"
4. ستظهر الواجهة الجديدة تلقائيًا / The new interface will appear automatically

### استخدام جدول الطلبات / Using Order Table

#### التنقل بالأسهم / Arrow Navigation

- **↑ (Up Arrow)**: الانتقال لخلية في الصف الأعلى (نفس العمود)
- **↓ (Down Arrow) أو Enter**: الانتقال لخلية في الصف الأسفل (نفس العمود)
- **← (Left Arrow)**: الانتقال للعمود السابق (نفس الصف)
- **→ (Right Arrow) أو Tab**: الانتقال للعمود التالي (نفس الصف)

#### إضافة منتج / Adding a Product

**طريقة 1 - النقر المزدوج / Double-click:**
- انقر مرتين على المنتج في القائمة اليمنى
- سيتم إضافته تلقائيًا لأول صف فارغ

**طريقة 2 - السحب / Drag:**
- اسحب المنتج من القائمة اليمنى إلى الجدول

#### تعديل الكمية والسعر / Edit Quantity & Price

1. انقر على الخلية المراد تعديلها
2. اكتب القيمة الجديدة
3. اضغط Enter أو السهم للانتقال
4. الحسابات ستتم تلقائيًا

### إضافة اسم عربي للمنتج / Add Arabic Name to Product

```python
# من واجهة Odoo / From Odoo interface
Inventory → Products → Select Product
# في تبويب Information تحت اسم المنتج
Arabic Name: [أدخل الاسم بالعربية]
```

## الهيكل التقني / Technical Structure

### الملفات الرئيسية / Main Files

```
pos_perfume_custom/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── product_product.py          # إضافة حقل الاسم العربي
├── views/
│   └── pos_perfume_views.xml       # واجهات XML
├── security/
│   └── ir.model.access.csv         # صلاحيات الوصول
└── static/src/
    ├── app/
    │   ├── excel_order_table.js    # مكون جدول الطلبات + التنقل بالأسهم
    │   └── perfume_product_screen.js # شاشة المنتجات
    ├── xml/
    │   ├── excel_order_table.xml   # قالب جدول الطلبات
    │   └── perfume_product_screen.xml # قالب الشاشة
    └── scss/
        └── perfume_pos.scss         # تنسيقات وألوان
```

### المكونات الرئيسية / Main Components

1. **ExcelOrderTable**: مكون جدول الطلبات
   - التنقل بالأسهم / Arrow navigation
   - الحسابات التلقائية / Auto-calculations
   - معالجة الأحداث / Event handling

2. **PerfumeProductScreen**: شاشة المنتجات المعدلة
   - البحث والفلترة / Search & filtering
   - عرض المنتجات / Product display
   - الأزرار والإجراءات / Buttons & actions

## الاعتمادات / Dependencies

- `point_of_sale` - وحدة POS الأساسية
- `product` - إدارة المنتجات
- `stock` - إدارة المخزون

## متطلبات النظام / System Requirements

- Odoo 17.0
- Python 3.10+
- PostgreSQL 12+
- متصفح حديث (Chrome 90+, Firefox 88+, Edge 90+)

## الألوان المستخدمة / Color Palette

```scss
Primary Purple: #714B67
Secondary Purple: #8B5A8E
Success Green: #4CAF50
Info Blue: #2196F3
Warning Orange: #FF9800
Error Red: #f44336
WhatsApp Green: #25D366
Excel Focus: #217346 (Green outline)
Excel Selection: #fffacd (Light yellow)
Discount BG: #e8f5e9 (Light green)
Total BG: #fff3e0 (Light orange)
```

## الاختصارات / Shortcuts Summary

| المفتاح / Key | الوظيفة / Function |
|---------------|-------------------|
| ↑ | الصف السابق / Previous row |
| ↓ أو Enter | الصف التالي / Next row |
| ← | العمود السابق / Previous column |
| → أو Tab | العمود التالي / Next column |
| Double-click | إضافة منتج / Add product |
| Esc | إلغاء التعديل / Cancel edit |

## الدعم / Support

للمساعدة والدعم:
- Email: support@lugal-ai.com
- Website: https://lugal-ai.com

## الترخيص / License

LGPL-3

## الإصدار / Version

**1.0.0** - October 23, 2025

## ملاحظات مهمة / Important Notes

1. **التنقل بالأسهم** يعمل فقط داخل جدول الطلبات
2. الحسابات تتم **تلقائيًا** عند تغيير أي قيمة
3. معدل التحويل إلى IQD: **1 USD = 1,300 IQD** (يمكن تعديله في الكود)
4. الجدول يعرض **5 صفوف كحد أدنى** للتسهيل
5. الخلايا المحسوبة (بعد الخصم والمجموع) **للقراءة فقط**

---

Made with ❤️ by Lugal-AI

