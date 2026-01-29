# إصلاح خطأ UoM Transaction Failed

## المشكلة

```
psycopg2.errors.InFailedSqlTransaction: current transaction is aborted, 
commands ignored until end of transaction block
```

### السبب
يحدث هذا الخطأ عندما:
1. ❌ فشل استعلام SQL سابق
2. ❌ لم يتم عمل rollback للمعاملة (transaction)
3. ❌ محاولة تنفيذ استعلامات جديدة في نفس المعاملة الفاشلة
4. ❌ وجود بيانات معطوبة في جدول `uom_uom` (وحدات القياس)

---

## الحل السريع ⚡

### على السيرفر البعيد:

```bash
cd /home/lugalai/Lugal-ai

# سحب التحديثات
git pull origin main

# تشغيل سكريبت الإصلاح الشامل
bash fix_uom_complete.sh
```

---

## الحل اليدوي (خطوة بخطوة)

### 1️⃣ إيقاف Odoo

```bash
cd /home/lugalai/Lugal-ai
pkill -9 -f odoo-bin
sleep 3
```

### 2️⃣ تشغيل سكريبت الإصلاح

```bash
venv/bin/python fix_uom_transaction_error.py
```

**النتيجة المتوقعة:**
```
============================================================
إصلاح خطأ UoM Transaction - قاعدة البيانات: nbs_lugalai
============================================================

1. التحقق من وحدات القياس...
   وحدات القياس مع relative_uom_id: 15

2. البحث عن مشاكل في وحدات القياس...
   ❌ Unit X (ID: 123): relative_uom_id 999 غير موجود!
   ❌ Unit Y (ID: 456): relative_factor غير صالح (0)

3. إصلاح 2 وحدة قياس معطوبة...
   ✅ تم إصلاح UoM ID: 123
   ✅ تم إصلاح UoM ID: 456

4. إعادة حساب عوامل وحدات القياس...
   ✅ تم إعادة حساب 50 وحدة قياس

5. التحقق من وحدات القياس بعد الإصلاح...
   ✅ جميع وحدات القياس صالحة

6. مسح الكاش...
   ✅ تم مسح الكاش

✅ تم إصلاح خطأ UoM Transaction!
```

### 3️⃣ تحديث وحدة UoM

```bash
venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai -u uom --stop-after-init
```

### 4️⃣ إعادة تشغيل Odoo

```bash
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &
```

### 5️⃣ التحقق من الحالة

```bash
# التحقق من أن Odoo يعمل
ps aux | grep odoo-bin

# مراقبة اللوغات
tail -f odoo.log
```

---

## ماذا يفعل السكريبت؟

### 1. البحث عن وحدات قياس معطوبة:
- ✅ التحقق من `relative_uom_id` موجود
- ✅ التحقق من `relative_factor` صالح (ليس null أو 0)
- ✅ البحث عن المراجع الدائرية (circular references)
- ✅ التحقق من السلاسل الطويلة

### 2. إصلاح المشاكل:
```sql
-- إزالة المرجع المعطوب
UPDATE uom_uom
SET relative_uom_id = NULL,
    relative_factor = 1.0,
    factor = 1.0
WHERE id = [problematic_id];
```

### 3. إعادة حساب العوامل:
- إعادة حساب `factor` لكل وحدة قياس
- التحقق من صحة النتائج

### 4. مسح الكاش:
- مسح كاش النماذج (model cache)
- مسح كاش السجل (registry cache)

---

## إذا استمر الخطأ

### التحقق اليدوي من قاعدة البيانات:

```bash
# الاتصال بقاعدة البيانات
sudo -u postgres psql nbs_lugalai

-- عرض وحدات القياس المعطوبة
SELECT id, name, uom_type, relative_uom_id, relative_factor, factor
FROM uom_uom
WHERE relative_uom_id IS NOT NULL
  AND (relative_factor IS NULL OR relative_factor = 0);

-- البحث عن مراجع غير موجودة
SELECT u1.id, u1.name, u1.relative_uom_id
FROM uom_uom u1
LEFT JOIN uom_uom u2 ON u1.relative_uom_id = u2.id
WHERE u1.relative_uom_id IS NOT NULL
  AND u2.id IS NULL;
```

### إصلاح يدوي (إذا لزم الأمر):

```sql
-- إصلاح جميع وحدات القياس المعطوبة
UPDATE uom_uom
SET relative_uom_id = NULL,
    relative_factor = 1.0,
    factor = 1.0
WHERE relative_uom_id IS NOT NULL
  AND (relative_factor IS NULL 
       OR relative_factor = 0
       OR relative_uom_id NOT IN (SELECT id FROM uom_uom));
```

---

## الأسباب الشائعة

### 1. استيراد بيانات SAP معطوبة
```python
# في sap_integration
# تحقق من أن UoM يتم إنشاؤها بشكل صحيح
product.uom_id = env['uom.uom'].search([('name', '=', 'Unit')], limit=1)
```

### 2. ترقية وحدة مع بيانات غير متوافقة
```bash
# حل: إعادة تحديث الوحدة
venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai -u uom --stop-after-init
```

### 3. حذف وحدة قياس مستخدمة
```sql
-- لا تحذف وحدات القياس مباشرة!
-- بدلاً من ذلك، قم بتعطيلها:
UPDATE uom_uom SET active = false WHERE id = 123;
```

### 4. مراجع دائرية
```
UoM A -> references -> UoM B
UoM B -> references -> UoM C
UoM C -> references -> UoM A  ❌ Circular!
```

---

## الوقاية من المشكلة

### عند إنشاء وحدات قياس جديدة:

```python
# ✅ طريقة صحيحة
uom = env['uom.uom'].create({
    'name': 'Custom Unit',
    'category_id': env.ref('uom.product_uom_categ_unit').id,
    'uom_type': 'reference',  # أو 'bigger' أو 'smaller'
    'relative_factor': 1.0,   # يجب أن يكون > 0
    'rounding': 0.01,
})

# ❌ طريقة خاطئة
uom = env['uom.uom'].create({
    'name': 'Bad Unit',
    'relative_uom_id': 999,  # ID غير موجود
    'relative_factor': 0,    # صفر!
})
```

### عند استيراد منتجات SAP:

```python
# في sap_integration/models/sap_product.py
def import_product(self, sap_data):
    # تحقق من UoM قبل الاستخدام
    uom_name = sap_data.get('BaseUoM', 'Unit')
    uom = self.env['uom.uom'].search([
        ('name', '=', uom_name)
    ], limit=1)
    
    if not uom:
        # استخدم القيمة الافتراضية
        uom = self.env.ref('uom.product_uom_unit')
    
    product_vals = {
        'uom_id': uom.id,
        'uom_po_id': uom.id,
        # ...
    }
```

---

## في المتصفح

بعد تشغيل السكريبت:

1. **امسح كاش المتصفح**: `Ctrl+Shift+Delete`
2. **سجل خروج** من Odoo
3. **سجل دخول** مرة أخرى
4. **جرب الصفحة** التي كانت تعطي الخطأ

---

## للمطورين

### كيف يحدث الخطأ؟

```python
# في addons/uom/models/uom_uom.py
@api.depends('relative_factor', 'relative_uom_id')
def _compute_factor(self):
    for uom in self:
        if uom.uom_type == 'reference':
            uom.factor = 1.0
        else:
            # هنا يحدث الخطأ إذا كان relative_uom_id معطوب!
            uom.factor = uom.relative_factor * uom.relative_uom_id.factor
            #                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^
            #                                  يحاول جلب factor من uom معطوب
```

### الحل البرمجي:

```python
@api.depends('relative_factor', 'relative_uom_id')
def _compute_factor(self):
    for uom in self:
        if uom.uom_type == 'reference':
            uom.factor = 1.0
        elif uom.relative_uom_id and uom.relative_factor:
            try:
                uom.factor = uom.relative_factor * uom.relative_uom_id.factor
            except Exception:
                # Fallback to 1.0 if computation fails
                uom.factor = 1.0
        else:
            uom.factor = 1.0
```

---

## الملخص

| المشكلة | الحل |
|---------|------|
| ❌ Transaction failed | ✅ إعادة تشغيل Odoo |
| ❌ UoM معطوبة | ✅ تشغيل `fix_uom_transaction_error.py` |
| ❌ relative_uom_id غير موجود | ✅ إزالة المرجع وجعلها reference uom |
| ❌ relative_factor = 0 | ✅ تعيينها إلى 1.0 |
| ❌ مراجع دائرية | ✅ كسر الدائرة وإعادة هيكلة |

---

## روابط مفيدة

- [Odoo UoM Documentation](https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html#odoo.fields.Float)
- [PostgreSQL Transaction Management](https://www.postgresql.org/docs/current/tutorial-transactions.html)

---

**ملاحظة:** هذا الخطأ خطير ويجب إصلاحه فوراً. لا تحاول تجاهله أو إعادة تشغيل الخادم فقط بدون إصلاح البيانات المعطوبة!
