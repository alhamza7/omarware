# SAP Integration - Quick Start Guide

## 🚀 تثبيت سريع

### 1. التحقق من المتطلبات

```bash
# تأكد من وجود موديلات OCA في addons/
ls addons/connector
ls addons/component
ls addons/component_event
```

✅ **موجودة في المشروع**:
- connector
- component
- component_event

❌ **مفقودة - تحتاج تثبيت**:
```bash
pip install odoo-addon-queue-job==17.0.*
```

### 2. تثبيت المودل

1. قم بتحديث قائمة التطبيقات
2. ابحث عن "SAP Integration"
3. اضغط تثبيت

## ⚙️ الإعداد الأولي

### 1. إعداد Backend

**Settings > SAP Integration > Backends > Create**

```
Name: SAP Production
Service Layer URL: https://your-sap-server:50000/b1s/v1
Username: your_username
Password: your_password
Company DB: YOUR_COMPANY_DB
```

اضغط **Test Connection**

### 2. استيراد البيانات من SAP

#### من Python Shell

```python
# احصل على Backend
backend = env['sap.backend'].search([('active', '=', True)], limit=1)

# استيراد العملاء
result = env['sap.res.partner'].import_batch(backend)
print(f"✅ تم استيراد {result['imported']} عميل")

# استيراد المنتجات
result = env['sap.product.product'].import_batch(backend)
print(f"✅ تم استيراد {result['imported']} منتج")

# استيراد الطلبات
result = env['sap.sale.order'].import_batch(backend)
print(f"✅ تم استيراد {result['imported']} طلب")
```

## 📊 البنية الأساسية

```
Odoo Record (res.partner)
    ↓ _inherits
Binding Record (sap.res.partner)
    + external_id: SAP CardCode
    + backend_id: SAP Backend
    ↓
Components (Adapter, Binder, Mapper)
    ↓
SAP Service Layer API
    ↓
SAP Business One
```

## 🔄 أمثلة الاستخدام

### مثال 1: استيراد عميل واحد

```python
backend = env['sap.backend'].browse(1)
external_id = 'C00001'  # SAP CardCode

binding = env['sap.res.partner'].import_record(backend, external_id)
print(f"Partner: {binding.name}")
print(f"SAP CardCode: {binding.external_id}")
```

### مثال 2: تصدير منتج لـ SAP

```python
# احصل على المنتج
product = env['product.product'].search([('default_code', '=', 'PROD001')])

# أنشئ Binding
binding = env['sap.product.product'].create({
    'odoo_id': product.id,
    'backend_id': backend.id,
})

# صدّر لـ SAP
binding.export_record()
print(f"✅ تم التصدير برقم SAP: {binding.external_id}")
```

### مثال 3: ربط تلقائي عند الإنشاء

```python
# تفعيل الربط التلقائي
partner = env['res.partner'].with_context(
    sap_auto_bind=True,
    sap_backend=backend
).create({
    'name': 'عميل جديد',
    'email': 'customer@example.com',
})

# سيتم إنشاء sap.res.partner تلقائياً
```

## 🎯 نقاط مهمة

### ✅ ما تم تنفيذه

- [x] Binding Models لجميع الكيانات
- [x] Backend Adapters لـ SAP Service Layer
- [x] Binders للربط بين Odoo و SAP
- [x] Mappers لتحويل البيانات
- [x] Importers/Exporters Components
- [x] Event Listeners للمزامنة التلقائية
- [x] Error handling و retry mechanism

### ⚠️ ملاحظات

1. **queue_job غير مثبت**: المزامنة تتم مباشرة (blocking)
   - لتفعيل Background Jobs: `pip install odoo-addon-queue-job`

2. **الـ Components جاهزة** لكن يجب اختبارها

3. **الـ Listeners معطلة افتراضياً**: فعّلها عبر context

## 🔧 استكشاف الأخطاء

### مشكلة: فشل الاتصال

```python
# اختبر الاتصال يدوياً
backend.test_connection()
```

### مشكلة: السجل موجود مسبقاً

```python
# أعد الاستيراد بالإجبار
importer = work.component(usage='record.importer')
binding = importer.run(external_id, force=True)
```

### مشكلة: خطأ في Mapping

```python
# افحص البيانات الخام من SAP
adapter = work.component(usage='backend.adapter')
sap_data = adapter.read(external_id)
print(sap_data)
```

## 📝 الخطوات التالية

1. ✅ تثبيت queue_job (اختياري)
2. ✅ اختبار استيراد العملاء
3. ✅ اختبار استيراد المنتجات
4. ✅ اختبار تصدير الطلبات
5. ✅ تفعيل Event Listeners للمزامنة التلقائية
6. ✅ إعداد Cron Jobs للمزامنة الدورية

## 📚 مصادر إضافية

- `README.md` - التوثيق الكامل
- `components/` - كود الـ Components
- `models/sap_binding.py` - Binding Models
- OCA Connector Docs: https://github.com/OCA/connector

---

**نجح الدمج! 🎉**

المودل الآن يستخدم OCA Connector Framework بشكل احترافي.

