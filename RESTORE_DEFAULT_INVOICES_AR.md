# استعادة الفواتير الأصلية من Odoo
## تم بتاريخ: 2026-01-11
## آخر تحديث: 2026-01-11 - إضافة الطباعة المباشرة

---

## 🎯 الهدف
تعطيل جميع قوالب الفواتير المخصصة من `invoice_designer` والعودة لاستخدام تقارير Odoo الأصلية (QWeb) مع إمكانية الطباعة المباشرة من POS.

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

### 4. إخفاء الأزرار من الواجهة Backend - `views/pos_perfume_order_views.xml`

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

### 5. إنشاء تقرير Odoo أصلي للطباعة المباشرة ⭐ جديد

#### أ) تقرير QWeb جديد - `reports/pos_perfume_order_simple_report.xml`:
```xml
<template id="report_pos_perfume_order_simple">
    <!-- تقرير احترافي بسيط يستخدم نمط Odoo الأصلي -->
    <!-- يدعم: custom_product_name، العملات المتعددة، SAP info -->
</template>
```

#### ب) إضافة التقرير للـ manifest - `__manifest__.py`:
```python
'reports/pos_perfume_order_simple_report.xml',  # ✅ تقرير Odoo الأصلي
```

#### ج) تفعيل دالة printOrder مع التقرير الجديد - `static/src/app/pos_perfume_screen.js`:
```javascript
async printOrder() {
    // الآن تستخدم تقرير Odoo الأصلي بدلاً من invoice_designer ✅
    const action = {
        type: 'ir.actions.report',
        report_name: 'pos_perfume_custom.report_pos_perfume_order_simple',
        ...
    };
}
```

#### د) تفعيل زر Print في الواجهة - `static/src/xml/pos_perfume_screen.xml`:
```xml
<button t-on-click="printOrder">🖨️ Print</button>  ✅ مفعّل
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

### لـ POS Perfume Orders (من واجهة POS) - ⭐ الطريقة السريعة:
1. أدخل الطلب في واجهة POS Perfume
2. اضغط على **💾 Save** لحفظ الطلب
3. اضغط على **🖨️ Print** للطباعة المباشرة
4. ✅ سيُفتح PDF جاهز للطباعة باستخدام تقرير Odoo الأصلي

**مميزات التقرير الجديد:**
- ✅ يعرض `custom_product_name` (الأسماء المخصصة للمنتجات)
- ✅ يدعم العملات المتعددة (USD + IQD)
- ✅ يعرض الخصومات والمخازن
- ✅ تصميم احترافي نظيف بنمط Odoo
- ✅ سريع وموثوق

### الطريقة البديلة (عبر Sale Order):
1. اضغط على **📋 Create Sale Order** أو **📄 Create Quotation**
2. سينفتح Sale Order في صفحة جديدة
3. من Sale Order، اضغط **Print** → اختر:
   - **Quotation** (لعرض السعر)
   - **Sale Order** (للطلب المؤكد)

### لـ POS Perfume Orders (من Backend):
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
- ✅ جميع وظائف POS Perfume (الطلبات، المنتجات، العملاء)
- ✅ البحث والفلترة
- ✅ حفظ الطلبات (💾 Save)
- ✅ **الطباعة المباشرة** (🖨️ Print) - باستخدام تقرير Odoo الأصلي ⭐ جديد
- ✅ إنشاء Sale Orders (📋 Create Sale Order)
- ✅ إنشاء Quotations (📄 Create Quotation)
- ✅ إرسال WhatsApp (📱 WhatsApp)
- ✅ العملات المتعددة (USD/IQD)
- ✅ دعم الأسماء المخصصة للمنتجات (custom_product_name)
- ✅ طباعة من Sale Orders باستخدام قوالب Odoo الأصلية

### ⚠️ ما لن يعمل (تم تعطيله):
- ❌ زر **طباعة مع المصمم** في Backend
- ❌ زر **فتح المصمم** في Backend
- ❌ القوالب المخصصة من invoice_designer (كلاسيكي، عصري، ذهبي، NBS)
- ❌ مصمم الفواتير المرئي (invoice_designer)
- ❌ التخصيصات المتقدمة للفواتير من invoice_designer

### ℹ️ البديل الأفضل:
بدلاً من invoice_designer المعطل، الآن لديك:
- ✅ تقرير Odoo QWeb احترافي ونظيف
- ✅ طباعة سريعة ومباشرة من POS
- ✅ دعم كامل للمنتجات المخصصة والعملات
- ✅ سهولة التعديل والتخصيص (ملف XML بسيط)

---

## 🆘 حل المشاكل

### المشكلة: "The method 'pos.perfume.order.action_print_with_designer' does not exist"
**السبب:** كود قديم يحاول استدعاء دالة من invoice_designer المعطلة

**الحل:** ✅ تم حلها! الآن يستخدم النظام تقرير Odoo الأصلي
1. أعد تشغيل Odoo
2. حدّث الوحدة `POS Perfume Custom`
3. امسح الكاش من المتصفح (Ctrl + Shift + Delete)
4. أعد تحميل الصفحة (Ctrl + F5)

**للطباعة الآن:** اضغط زر **🖨️ Print** مباشرة - يعمل بتقرير Odoo الأصلي!

---

### المشكلة: خطأ عند بدء Odoo
**الحل:** تأكد من حفظ جميع الملفات وأعد التشغيل مرة أخرى

### المشكلة: لا تظهر خيارات الطباعة
**الحل:** 
1. تأكد من تحديث الوحدة
2. أعد تحميل الصفحة (Ctrl + F5)
3. امسح الكاش من المتصفح

### المشكلة: رسالة خطأ "Module dependency not found"
**الحل:** إذا كان `invoice_designer` لا يزال مثبتاً ولكن معطلاً في depends، قم بإلغاء تثبيته أولاً

### المشكلة: زر Print لا يظهر في POS (أو لا يعمل)
**الحل:**
1. تأكد من تحديث الوحدة `POS Perfume Custom` من Apps
2. امسح الكاش: Settings → Developer Tools → Clear Assets
3. أعد تحميل الصفحة (Ctrl + F5)
4. تأكد من حفظ الطلب أولاً (💾 Save) قبل الطباعة
5. إذا لم يعمل، أعد تشغيل Odoo

### المشكلة: PDF لا يُفتح عند الطباعة
**الحل:**
1. تحقق من إعدادات Pop-up في المتصفح (يجب السماح)
2. جرب في نافذة تصفح خاص (Incognito)
3. تحقق من console log في المتصفح (F12) لرؤية الأخطاء

---

## 📞 الدعم الفني

إذا واجهت أي مشاكل:
1. تحقق من سجل الأخطاء (Log)
2. تأكد من إعادة تشغيل Odoo بعد التعديلات
3. تأكد من تحديث الوحدة من قائمة التطبيقات

---

## 🎨 تخصيص التقرير الجديد (اختياري)

التقرير الجديد موجود في ملف XML بسيط وسهل التعديل:
```
addons/pos_perfume_custom/reports/pos_perfume_order_simple_report.xml
```

### أمثلة على التخصيصات الممكنة:

#### 1. تغيير الألوان:
```xml
<!-- في الـ template، ابحث عن: -->
style="background-color: #f8f9fa;"
<!-- وغيّرها للون المطلوب -->
```

#### 2. إضافة شعار الشركة:
التقرير يستخدم `web.external_layout` الذي يعرض شعار الشركة تلقائياً من:
- **Settings** → **Companies** → رفع الشعار (Logo)

#### 3. إضافة حقول إضافية:
```xml
<!-- أضف أي حقل من pos.perfume.order -->
<div class="row">
    <strong>Field Name:</strong>
    <span t-field="o.field_name"/>
</div>
```

#### 4. تغيير التنسيق:
- يمكنك تعديل الجداول، الخطوط، الهوامش
- التقرير يستخدم Bootstrap 5 classes
- راجع توثيق Odoo QWeb Reports: [Odoo Reports Documentation](https://www.odoo.com/documentation/17.0/developer/reference/backend/reports.html)

#### 5. إنشاء تقرير آخر (مثلاً: نسخة مبسطة للإيصالات):
1. انسخ الملف `pos_perfume_order_simple_report.xml`
2. غيّر الـ IDs والأسماء
3. أضف التقرير الجديد في `__manifest__.py`
4. عدّل دالة `printOrder` لاستخدام التقرير المناسب

---

**تاريخ الإنشاء:** 2026-01-11  
**آخر تحديث:** 2026-01-11 - إضافة الطباعة المباشرة  
**الحالة:** ✅ جاهز للتطبيق

