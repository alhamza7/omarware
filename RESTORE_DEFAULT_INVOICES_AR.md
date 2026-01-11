# استعادة الفواتير الأصلية من Odoo
## تم بتاريخ: 2026-01-11

---

## 🎯 الهدف
تعطيل جميع قوالب الفواتير المخصصة والعودة لاستخدام الفاتورة الأصلية من Odoo.

---

## ✅ التعديلات التي تم إجراؤها

### 1. إصلاح خطأ Uninstall Hook في `invoice_designer`
**المشكلة:** كان هناك خطأ في دالة `uninstall_hook` تمنع إلغاء تثبيت الوحدة.

**الحل:** تم تحديث التوقيع من `uninstall_hook(cr, registry)` إلى `uninstall_hook(env)`

**الملف:** `addons/invoice_designer/__init__.py`

---

### 2. تعطيل القوالب المخصصة في `pos_perfume_custom`

#### أ) الاعتمادات (Dependencies) - `__manifest__.py`:
```python
# 'invoice_designer',  # ⭐ معطل: استخدام الفاتورة الأصلية من Odoo
```

#### ب) ملفات البيانات (Data Files) - `__manifest__.py`:
```python
# 'data/invoice_templates.xml',  # ⛔ معطل: استخدام الفاتورة الأصلية
# 'reports/pos_perfume_order_report.xml',  # ⛔ معطل
# 'reports/pos_perfume_order_report_gold.xml',  # ⛔ معطل
# 'reports/pos_perfume_order_report_nbs.xml',  # ⛔ معطل
# 'reports/pos_perfume_report_action.xml',  # ⛔ معطل
```

#### ج) ملفات الأصول (Assets) - `__manifest__.py`:
```python
# 'web.report_assets_common': [  # ⛔ معطل
#     'pos_perfume_custom/static/src/css/report_style.css',
# ],
```

---

### 3. تعطيل الحقول والدوال في `models/pos_perfume_order.py`

#### أ) حقل قالب الفاتورة:
```python
# invoice_template_id = fields.Many2one(...)  # معطل
```

#### ب) دوال الطباعة المخصصة:
```python
# def action_print_with_designer(self):  # معطلة
# def action_open_designer(self):  # معطلة
```

---

### 4. إخفاء الأزرار من الواجهة - `views/pos_perfume_order_views.xml`

#### أ) أزرار المصمم:
```xml
<!-- <button name="action_print_with_designer" ... /> -->  معطل
<!-- <button name="action_open_designer" ... /> -->  معطل
```

#### ب) حقل اختيار القالب:
```xml
<!-- <field name="invoice_template_id" ... /> -->  معطل
```

---

## 🔄 كيفية تطبيق التغييرات

### الخطوة 1: إعادة تشغيل Odoo
يجب إعادة تشغيل الخادم لتطبيق التغييرات:

**على الخادم (192.168.116.211):**
```bash
sudo systemctl restart odoo
# أو
sudo service odoo restart
```

**محلياً (على جهازك):**
```bash
cd /d/capo_dev/Lugal-ai
./venv/Scripts/python.exe odoo-bin -c odoo_simple.conf -d lugal
```

### الخطوة 2: تحديث الوحدة
بعد إعادة التشغيل، قم بتحديث الوحدة:

1. افتح Odoo على المتصفح
2. فعّل **Developer Mode** (إذا لم يكن مفعلاً)
3. اذهب إلى **التطبيقات** (Apps)
4. أزل الفلتر "Apps" واكتب في البحث: **POS Perfume Custom**
5. اضغط على **تحديث** (Upgrade)

⚠️ **مهم جداً:** يجب تحديث الوحدة حتى يتم تطبيق التغييرات على قاعدة البيانات!

### الخطوة 3: تنظيف البيانات القديمة (مهم!)
بعد التحديث، قد تحتاج لحذف البيانات القديمة من `invoice_designer`:

**الطريقة الأسهل - من الواجهة:**
1. اذهب إلى **Settings** → **Technical** → **Database Structure** → **Models**
2. ابحث عن `invoice.template.designer`
3. افتح السجلات واحذف القوالب القديمة يدوياً

**الطريقة الأسرع - من SQL (للمتقدمين فقط):**
```sql
-- حذف قوالب invoice_designer القديمة
DELETE FROM invoice_template_element WHERE template_id IN (
    SELECT id FROM invoice_template_designer WHERE code LIKE 'pos_perfume%'
);
DELETE FROM invoice_template_designer WHERE code LIKE 'pos_perfume%';

-- حذف إعدادات القالب من pos_perfume_order
UPDATE pos_perfume_order SET invoice_template_id = NULL;
```

⚠️ **تحذير:** لا تنفذ أوامر SQL إلا إذا كنت متأكداً مما تفعل!

### الخطوة 4: (اختياري) إلغاء تثبيت Invoice Designer
إذا كنت تريد إزالة `invoice_designer` تماماً:

1. اذهب إلى **التطبيقات** (Apps)
2. ابحث عن **Invoice Designer**
3. اضغط على **إلغاء التثبيت** (Uninstall)

⚠️ الآن بعد إصلاح خطأ uninstall_hook، يمكنك إلغاء التثبيت بأمان!

---

## 📋 الفواتير المتاحة الآن

بعد هذه التغييرات، ستستخدم الفواتير الأصلية من Odoo:

### لـ POS Perfume Orders (Backend):
1. افتح أي طلب من **POS Perfume** → **Backend Orders**
2. اضغط على زر **Confirm Sale Order** لتحويله لـ Sale Order
3. سينفتح Sale Order، ومن هناك يمكنك:
   - طباعة **Quotation** (عرض سعر)
   - طباعة **Sale Order** (أمر بيع)
   - إنشاء فاتورة والطباعة

### لـ Sale Orders:
- اذهب إلى **Sales** → **Orders**
- افتح أي طلب واضغط **Print** → اختر:
  - **Quotation** (قبل التأكيد)
  - **Sale Order** (بعد التأكيد)

### لـ Invoices:
1. من Sale Order، اضغط **Create Invoice**
2. اذهب إلى **Accounting** → **Customers** → **Invoices**
3. افتح الفاتورة واضغط **Print** → **Invoice**

### لـ POS (نقاط البيع):
- **الإيصال الافتراضي من Odoo POS**
- يطبع تلقائياً عند إتمام الدفع
- قالب نظيف واحترافي

---

## 🎨 تخصيص الفواتير الأصلية (اختياري)

إذا أردت تخصيص شكل الفواتير الأصلية:

### 1. تعديل Header/Footer الشركة:
- **Settings** → **Companies** → اختر الشركة
- رفع الشعار (Logo)
- إضافة معلومات الاتصال في Footer

### 2. تخصيص قوالب QWeb:
يمكنك تعديل قوالب Odoo الأصلية من:
- **Settings** → **Technical** → **User Interface** → **Views**
- ابحث عن:
  - `report_saleorder_document` - لـ Sale Orders
  - `report_invoice_document` - لـ Invoices
  - نسخ (Inherit) القالب وتعديله

### 3. استخدام وحدات التصميم الجاهزة:
- `l10n_din5008` - تصميم ألماني احترافي
- `invoice_design` - وحدات مجانية من Odoo Apps Store

---

## 🔙 كيفية العودة للقوالب المخصصة (إذا لزم الأمر)

إذا أردت العودة للقوالب المخصصة في المستقبل:

1. افتح `addons/pos_perfume_custom/__manifest__.py`
2. أزل علامات التعليق `#` من الأسطر التي تحتوي على:
   - `'invoice_designer'`
   - `'data/invoice_templates.xml'`
   - ملفات `reports/...`
   - `'web.report_assets_common'`
3. احفظ الملف
4. أعد تشغيل Odoo
5. حدّث الوحدة

---

## 📝 ملاحظات مهمة

### ✅ ما يعمل الآن:
- جميع وظائف POS Perfume (الطلبات، المنتجات، العملاء)
- البحث والفلترة
- حفظ الطلبات
- العملات المتعددة (USD/IQD)
- طباعة الإيصالات باستخدام قالب Odoo الافتراضي

### ⚠️ ما لن يعمل:
- القوالب المخصصة (كلاسيكي، عصري، ذهبي، NBS)
- مصمم الفواتير المرئي
- التخصيصات المتقدمة للفواتير

---

## 🆘 حل المشاكل

### المشكلة: خطأ عند بدء Odoo
**الحل:** تأكد من حفظ جميع الملفات وأعد التشغيل مرة أخرى

### المشكلة: لا تظهر خيارات الطباعة
**الحل:** 
1. تأكد من تحديث الوحدة
2. أعد تحميل الصفحة (Ctrl + F5)
3. امسح الكاش من المتصفح

### المشكلة: رسالة خطأ "Module dependency not found"
**الحل:** إذا كان `invoice_designer` لا يزال مثبتاً ولكن معطلاً في depends، قم بإلغاء تثبيته أولاً

---

## 📞 الدعم الفني

إذا واجهت أي مشاكل:
1. تحقق من سجل الأخطاء (Log)
2. تأكد من إعادة تشغيل Odoo بعد التعديلات
3. تأكد من تحديث الوحدة من قائمة التطبيقات

---

**تاريخ التعديل الأخير:** 2026-01-11  
**الحالة:** ✅ جاهز للتطبيق

