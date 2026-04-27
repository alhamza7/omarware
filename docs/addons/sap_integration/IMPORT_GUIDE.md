# 📥 دليل استيراد البيانات من SAP إلى Odoo

## المشكلة التي تم حلها

**المشكلة السابقة**: عند استيراد العملاء من SAP، كانت تُنشأ سجلات binding فقط (`sap.res.partner`) دون إنشاء سجلات العملاء الفعلية في `res.partner`.

**الحل**: تم تعديل الـ Importer لإنشاء السجل الأساسي (`res.partner`) أولاً، ثم ربطه مع binding record.

---

## 🔧 كيفية الاستيراد الصحيح

### 1️⃣ إعداد Backend أولاً

```python
# في Python Shell أو في كود
backend = env['sap.backend'].search([('active', '=', True)], limit=1)

# أو إنشاء backend جديد
backend = env['sap.backend'].create({
    'name': 'SAP Production',
    'base_url': 'https://your-sap-server:50000/b1s/v1',
    'username': 'manager',
    'password': 'password',
    'company_db': 'COMPANY_DB',
    'batch_size': 100,
})

# اختبار الاتصال
backend.test_connection()
```

---

### 2️⃣ استيراد العملاء (Business Partners)

#### الطريقة 1: استيراد دفعة (Batch Import)

```python
# استيراد جميع العملاء
result = env['sap.res.partner'].import_batch(backend)

print(f"✅ تم استيراد {result['imported']} عميل")
print(f"❌ فشل {result['errors']} عميل")
```

#### الطريقة 2: استيراد عميل واحد

```python
# استيراد عميل محدد بـ CardCode
card_code = 'C00001'
binding = env['sap.res.partner'].import_record(backend, card_code)

# الآن يمكنك الوصول للعميل في res.partner
partner = binding.odoo_id
print(f"✅ تم استيراد: {partner.name}")
print(f"   📧 Email: {partner.email}")
print(f"   📱 Phone: {partner.phone}")
print(f"   🆔 SAP CardCode: {binding.external_id}")
```

#### الطريقة 3: استيراد مع فلتر

```python
# استيراد العملاء النشطين فقط
filters = "Valid eq 'Y'"
result = env['sap.res.partner'].import_batch(backend, filters=filters)

# استيراد العملاء من مدينة معينة
filters = "City eq 'Riyadh'"
result = env['sap.res.partner'].import_batch(backend, filters=filters)
```

---

### 3️⃣ استيراد المنتجات (Items)

#### استيراد دفعة من المنتجات

```python
# استيراد جميع المنتجات
result = env['sap.product.product'].import_batch(backend)

print(f"✅ تم استيراد {result['imported']} منتج")
```

#### استيراد منتج واحد

```python
# استيراد منتج محدد بـ ItemCode
item_code = 'ITEM001'
binding = env['sap.product.product'].import_record(backend, item_code)

# الوصول للمنتج
product = binding.odoo_id
print(f"✅ تم استيراد: {product.name}")
print(f"   💰 السعر: {product.list_price}")
print(f"   📦 الكود: {product.default_code}")
print(f"   🆔 SAP ItemCode: {binding.external_id}")
```

#### استيراد مع فلتر

```python
# استيراد المنتجات النشطة فقط
filters = "Valid eq 'Y'"
result = env['sap.product.product'].import_batch(backend, filters=filters)

# استيراد من مجموعة محددة
filters = "ItemsGroupCode eq 100"
result = env['sap.product.product'].import_batch(backend, filters=filters)
```

---

### 4️⃣ استيراد أوامر البيع (Orders)

```python
# استيراد أوامر البيع
result = env['sap.sale.order'].import_batch(backend)

# استيراد أمر محدد
doc_entry = '12345'
binding = env['sap.sale.order'].import_record(backend, doc_entry)

sale_order = binding.odoo_id
print(f"✅ تم استيراد طلب: {sale_order.name}")
print(f"   👤 العميل: {sale_order.partner_id.name}")
print(f"   💵 المبلغ: {sale_order.amount_total}")
```

---

### 5️⃣ استيراد الفواتير (Invoices)

```python
# استيراد الفواتير
result = env['sap.account.move'].import_batch(backend)

# استيراد فاتورة محددة
doc_entry = '67890'
binding = env['sap.account.move'].import_record(backend, doc_entry)

invoice = binding.odoo_id
print(f"✅ تم استيراد فاتورة: {invoice.name}")
```

---

## 🔍 التحقق من البيانات المستوردة

### عرض جميع العملاء المستوردين من SAP

```python
# عرض جميع bindings
bindings = env['sap.res.partner'].search([])

for binding in bindings:
    print(f"SAP CardCode: {binding.external_id}")
    print(f"Odoo Partner: {binding.odoo_id.name}")
    print(f"Email: {binding.email}")
    print(f"Phone: {binding.phone}")
    print("---")
```

### عرض العملاء العاديين في res.partner

```python
# العملاء المستوردين موجودون في res.partner أيضاً
partners = env['res.partner'].search([])

# يمكنك البحث بالـ ref (يحتوي على SAP CardCode)
sap_partners = env['res.partner'].search([('ref', '!=', False)])

for partner in sap_partners:
    print(f"اسم العميل: {partner.name}")
    print(f"SAP Ref: {partner.ref}")
    print("---")
```

---

## 🔄 إعادة الاستيراد (Force Import)

إذا كنت تريد إعادة استيراد سجل موجود:

```python
# استيراد مع إجبار التحديث
binding = env['sap.res.partner'].search([
    ('external_id', '=', 'C00001')
], limit=1)

if binding:
    # إعادة الاستيراد
    with backend.work_on('sap.res.partner') as work:
        importer = work.component(usage='record.importer')
        binding = importer.run('C00001', force=True)
    print("✅ تم إعادة الاستيراد بنجاح")
```

---

## 🎯 المزامنة التدريجية (Incremental Sync)

استيراد السجلات المعدلة فقط منذ آخر مزامنة:

```python
# مزامنة العملاء المعدلين فقط
backend.sync_incremental_partners()

# مزامنة المنتجات المعدلة فقط
backend.sync_incremental_products()

# مزامنة كل شيء معدل
backend.sync_incremental_all()
```

---

## ⚠️ معالجة الأخطاء

### إذا فشل الاستيراد

```python
try:
    result = env['sap.res.partner'].import_batch(backend)
except Exception as e:
    print(f"❌ خطأ في الاستيراد: {str(e)}")
    
    # التحقق من سجلات الأخطاء
    failed_bindings = env['sap.res.partner'].search([
        ('sync_error', '!=', False)
    ])
    
    for binding in failed_bindings:
        print(f"CardCode: {binding.external_id}")
        print(f"Error: {binding.sync_error}")
        print("---")
```

### إعادة المحاولة للسجلات الفاشلة

```python
# البحث عن السجلات التي فشلت
failed_bindings = env['sap.res.partner'].search([
    ('sync_error', '!=', False),
    ('sync_retry_count', '<', 3)
])

# إعادة المحاولة
for binding in failed_bindings:
    try:
        with backend.work_on('sap.res.partner') as work:
            importer = work.component(usage='record.importer')
            importer.run(binding.external_id, force=True)
        print(f"✅ نجح: {binding.external_id}")
    except Exception as e:
        binding.write({
            'sync_error': str(e),
            'sync_retry_count': binding.sync_retry_count + 1
        })
        print(f"❌ فشل: {binding.external_id}")
```

---

## 📊 إحصائيات الاستيراد

```python
# عدد العملاء المستوردين
partner_count = env['sap.res.partner'].search_count([])
print(f"📊 إجمالي العملاء المستوردين: {partner_count}")

# عدد المنتجات المستوردة
product_count = env['sap.product.product'].search_count([])
print(f"📦 إجمالي المنتجات المستوردة: {product_count}")

# عدد الطلبات المستوردة
order_count = env['sap.sale.order'].search_count([])
print(f"🛒 إجمالي الطلبات المستوردة: {order_count}")

# آخر مزامنة
print(f"🕐 آخر مزامنة للعملاء: {backend.last_partner_sync}")
print(f"🕐 آخر مزامنة للمنتجات: {backend.last_product_sync}")
```

---

## 🎓 أمثلة متقدمة

### مثال 1: استيراد ومعالجة البيانات

```python
# استيراد جميع العملاء ثم معالجتهم
result = env['sap.res.partner'].import_batch(backend)

# الحصول على جميع العملاء المستوردين
bindings = env['sap.res.partner'].search([
    ('sync_date', '>=', fields.Datetime.now() - timedelta(hours=1))
])

# معالجة البيانات
for binding in bindings:
    partner = binding.odoo_id
    
    # مثال: إضافة تاج للعملاء الجدد
    tag = env['res.partner.category'].search([('name', '=', 'SAP Customer')], limit=1)
    if tag and tag not in partner.category_id:
        partner.category_id = [(4, tag.id)]
```

### مثال 2: استيراد مع تحديث مخصص

```python
# استيراد العملاء
result = env['sap.res.partner'].import_batch(backend)

# تحديث حقول إضافية بعد الاستيراد
bindings = env['sap.res.partner'].search([])

for binding in bindings:
    partner = binding.odoo_id
    
    # تحديث حقول إضافية
    partner.write({
        'comment': f'مستورد من SAP - CardCode: {binding.external_id}',
        'is_company': True,
    })
```

---

## ✅ التأكد من نجاح الاستيراد

بعد الاستيراد، تحقق من:

1. **في res.partner**:
   ```python
   partners = env['res.partner'].search([('ref', 'like', 'C%')])  # العملاء من SAP
   print(f"✅ عدد العملاء: {len(partners)}")
   ```

2. **في sap.res.partner**:
   ```python
   bindings = env['sap.res.partner'].search([])
   print(f"✅ عدد Bindings: {len(bindings)}")
   ```

3. **يجب أن يكون العددان متساويان**!

---

## 🚀 نصائح للأداء

1. **استخدم Filters** لاستيراد بيانات محددة
2. **اضبط batch_size** في Backend settings
3. **استخدم Incremental Sync** للمزامنة الدورية
4. **ثبّت queue_job** للمعالجة في الخلفية

---

## 📞 الدعم

إذا واجهت مشاكل:
1. تحقق من Logs: Settings > Technical > Logging
2. افحص sync_error في binding records
3. اختبر الاتصال بـ SAP: `backend.test_connection()`

---

**تم الحل! الآن يتم إنشاء السجلات في res.partner بشكل صحيح عند الاستيراد من SAP** ✅

