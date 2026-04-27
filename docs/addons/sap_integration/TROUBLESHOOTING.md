# 🔧 حل المشاكل الشائعة - SAP Integration

## ❌ الأخطاء الشائعة وحلولها

---

## 1️⃣ **خطأ: Field "sap_id" does not exist**

### المشكلة:
```
Field "sap_id" does not exist in model "sap.res.partner"
```

### السبب:
كان هناك خطأ في ملف الـ View - يشير لحقل قديم غير موجود.

### ✅ تم الحل:
- تم تغيير `sap_id` إلى `external_id` في جميع الـ Views
- الحقل الصحيح هو `external_id` (يحتوي على SAP CardCode أو ItemCode)

### الخطوات للتطبيق:
1. تم تعديل الملف تلقائياً
2. أعد محاولة الترقية الآن

---

## 2️⃣ **خطأ: Cannot upgrade module**

### المشكلة:
عند محاولة Upgrade للموديل يظهر خطأ.

### الحل:
```bash
# 1. أعد تشغيل Odoo
Ctrl+C  # إيقاف
python odoo-bin -c odoo.conf  # إعادة التشغيل

# 2. حدّث الموديل من Terminal
python odoo-bin -c odoo.conf -u sap_integration -d اسم_قاعدة_البيانات
```

أو من واجهة Odoo:
1. Apps > SAP Integration > Upgrade
2. إذا فشل، جرب من Technical > Modules > SAP Integration > Upgrade

---

## 3️⃣ **خطأ: Connection Failed**

### المشكلة:
```
Connection to SAP failed
```

### الحل:
```python
# في Python Shell
backend = env['sap.backend'].search([('active', '=', True)], limit=1)

# تحقق من الإعدادات
print(f"URL: {backend.base_url}")
print(f"Username: {backend.username}")
print(f"Company DB: {backend.company_db}")

# اختبار الاتصال
backend.test_connection()
```

**تحقق من:**
- ✅ URL صحيح (مثال: `https://server:50000/b1s/v1`)
- ✅ Username و Password صحيحين
- ✅ Company Database صحيح
- ✅ SAP Server يعمل ويمكن الوصول إليه
- ✅ لا توجد Firewall تمنع الاتصال

---

## 4️⃣ **خطأ: No records imported**

### المشكلة:
```python
result = env['sap.res.partner'].import_batch(backend)
# النتيجة: imported: 0
```

### الحل:

#### أ) تحقق من الاتصال:
```python
backend.test_connection()
```

#### ب) تحقق من وجود بيانات في SAP:
```python
# اختبار API مباشرة
from odoo.addons.sap_integration.models.sap_service_layer import SapServiceLayerConnection

connection = SapServiceLayerConnection(
    backend.base_url,
    backend.username,
    backend.password,
    backend.company_db
)

customers = connection.get_customers(top=5)
print(f"عدد العملاء في SAP: {len(customers.get('value', []))}")

connection.close_session()
```

#### ج) جرب استيراد عميل واحد محدد:
```python
card_code = 'C00001'  # غيّر هذا لعميل موجود
try:
    binding = env['sap.res.partner'].import_record(backend, card_code)
    print(f"✅ نجح: {binding.odoo_id.name}")
except Exception as e:
    print(f"❌ فشل: {str(e)}")
```

---

## 5️⃣ **خطأ: Binding created but no partner**

### المشكلة:
```python
# يتم إنشاء sap.res.partner لكن لا يتم إنشاء res.partner
```

### ✅ تم الحل:
تم إصلاح هذه المشكلة في `components/importer.py`. الآن يتم إنشاء `res.partner` تلقائياً.

### التحقق:
```python
# تحقق من أن العددين متساويين
partner_count = env['res.partner'].search_count([('ref', '!=', False)])
binding_count = env['sap.res.partner'].search_count([])

print(f"Partners: {partner_count}")
print(f"Bindings: {binding_count}")

if partner_count == binding_count:
    print("✅ يعمل بشكل صحيح")
```

---

## 6️⃣ **خطأ: Import Error - Mapping Failed**

### المشكلة:
```
Error during import: 'NoneType' object has no attribute 'id'
```

### السبب المحتمل:
قد يكون هناك بيانات ناقصة في SAP (مثل: Country, State)

### الحل:
```python
# استيراد مع معالجة الأخطاء
backend = env['sap.backend'].search([('active', '=', True)], limit=1)

try:
    result = env['sap.res.partner'].import_batch(backend)
    print(f"✅ نجح: {result['imported']}")
except Exception as e:
    print(f"❌ خطأ: {str(e)}")
    
    # افحص السجلات الفاشلة
    failed = env['sap.res.partner'].search([('sync_error', '!=', False)])
    for binding in failed:
        print(f"- {binding.external_id}: {binding.sync_error}")
```

---

## 7️⃣ **خطأ: Module not found**

### المشكلة:
```
ModuleNotFoundError: No module named 'connector'
```

### السبب:
مكتبات OCA غير مثبتة.

### الحل:
تأكد من وجود هذه الموديلات في مجلد `addons/`:
- ✅ `connector`
- ✅ `component`
- ✅ `component_event`

```bash
# تحقق من وجودها
ls addons/ | grep connector
ls addons/ | grep component
```

إذا لم تكن موجودة:
```bash
# حملها من OCA
git clone https://github.com/OCA/connector.git
cd connector
git checkout 17.0
cp -r connector component component_event ../addons/
```

---

## 8️⃣ **خطأ: Session Expired**

### المشكلة:
```
SAP Session expired or invalid
```

### الحل:
```python
# Session ينتهي بعد 30 دقيقة تلقائياً
# الكود يعيد الاتصال تلقائياً، لكن إذا واجهت مشكلة:

backend = env['sap.backend'].search([('active', '=', True)], limit=1)

# إعادة اختبار الاتصال
backend.write({'connection_status': 'disconnected'})
backend.test_connection()

# ثم أعد الاستيراد
result = env['sap.res.partner'].import_batch(backend)
```

---

## 9️⃣ **خطأ: Constraint Violation**

### المشكلة:
```
unique constraint "sap_partner_uniq" violated
```

### السبب:
محاولة استيراد نفس العميل مرتين.

### الحل:
```python
# البحث عن Binding موجود
existing = env['sap.res.partner'].search([
    ('external_id', '=', 'C00001')
])

if existing:
    print(f"✅ موجود مسبقاً: {existing.odoo_id.name}")
    
    # إذا أردت تحديثه:
    with backend.work_on('sap.res.partner') as work:
        importer = work.component(usage='record.importer')
        binding = importer.run('C00001', force=True)
    print("✅ تم التحديث")
```

---

## 🔟 **خطأ: Performance Issues**

### المشكلة:
الاستيراد بطيء جداً.

### الحل:

#### أ) تقليل Batch Size:
```python
backend = env['sap.backend'].search([('active', '=', True)], limit=1)
backend.batch_size = 50  # بدلاً من 100
```

#### ب) استخدام Filters:
```python
# استيراد العملاء النشطين فقط
filters = "Valid eq 'Y'"
result = env['sap.res.partner'].import_batch(backend, filters=filters)
```

#### ج) استخدام Incremental Sync:
```python
# استيراد المعدّل فقط
backend.sync_incremental_partners()
```

#### د) تثبيت queue_job (اختياري):
```bash
pip install odoo-addon-queue-job==17.0.*
```

---

## 📊 **أدوات التشخيص**

### 1. فحص شامل:
```python
from odoo.addons.sap_integration import test_import
test_import.run_all_tests(env)
```

### 2. فحص الاتصال:
```python
backend = env['sap.backend'].search([('active', '=', True)], limit=1)
print(f"Status: {backend.connection_status}")
print(f"Last Connection: {backend.last_connection}")
print(f"Error: {backend.error_message or 'None'}")
```

### 3. فحص البيانات:
```python
# إحصائيات
print(f"Partners: {env['res.partner'].search_count([])}")
print(f"Bindings: {env['sap.res.partner'].search_count([])}")
print(f"Products: {env['product.product'].search_count([])}")

# السجلات الفاشلة
failed_partners = env['sap.res.partner'].search([('sync_error', '!=', False)])
failed_products = env['sap.product.product'].search([('sync_error', '!=', False)])

print(f"Failed Partners: {len(failed_partners)}")
print(f"Failed Products: {len(failed_products)}")
```

### 4. فحص السجلات (Logs):
```
Settings > Technical > Logging
ابحث عن: sap_integration
```

---

## 🆘 **إذا لم تحل المشكلة**

1. **اقرأ الوثائق:**
   - `IMPORT_GUIDE.md` - دليل الاستيراد
   - `FIX_DETAILS.md` - تفاصيل الإصلاحات
   - `README.md` - الوثائق الكاملة

2. **استخدم الأمثلة:**
   ```python
   from odoo.addons.sap_integration.examples import import_example
   import_example.run_all_examples(env)
   ```

3. **افحص Logs:**
   ```bash
   tail -f odoo.log | grep sap
   ```

4. **أعد التثبيت:**
   ```python
   # إزالة الموديل
   module = env['ir.module.module'].search([('name', '=', 'sap_integration')])
   module.button_immediate_uninstall()
   
   # إعادة التثبيت
   module.button_immediate_install()
   ```

---

## ✅ **Checklist - قائمة التحقق**

قبل أي استيراد، تأكد من:

- [ ] Odoo مُعاد تشغيله بعد آخر تعديل
- [ ] الموديل محدّث (Upgraded)
- [ ] Backend مضبوط بشكل صحيح
- [ ] الاتصال بـ SAP يعمل (`test_connection()`)
- [ ] لا توجد أخطاء في السجلات
- [ ] الحقول في Views تطابق الموديل

---

**تم توثيق جميع المشاكل والحلول! 📝**

