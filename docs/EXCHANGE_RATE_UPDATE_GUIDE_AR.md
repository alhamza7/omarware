# دليل تحديث سعر الصرف في Odoo

## المشكلة

- ✅ سعر الصرف الحالي: **1510 IQD** لكل 1 USD
- ❌ **اختفى المكان** الذي يمكن تعديل سعر الصرف منه في Settings

---

## الحل السريع ⚡

### على السيرفر البعيد:

```bash
cd /home/lugalai/Lugal-ai

# سحب التحديثات
git pull origin main

# تفعيل قوائم العملات
venv/bin/python activate_currency_menu.py

# تحديث سعر الصرف إلى 1510
venv/bin/python update_exchange_rate.py 1510
```

---

## النتيجة المتوقعة

### 1. تفعيل قوائم العملات:

```
============================================================
تفعيل قوائم العملات - قاعدة البيانات: nbs_lugalai
============================================================

1. تفعيل Multi-Currency في الإعدادات...
   ✅ تم تفعيل Multi-Currency لـ 5 مستخدم

2. تفعيل قوائم العملات...
   ✅ تم تفعيل: Currencies
   ✅ تم تفعيل 1 قائمة

3. التحقق من Actions للعملات...
   ✅ Action للعملات موجود (ID: 42)
   ✅ القائمة مربوطة: Currencies

5. التحقق من قائمة Accounting/Configuration/Currencies...
   ✅ قائمة Currencies موجودة ومفعلة

✅ تم تفعيل قوائم العملات!
```

### 2. تحديث سعر الصرف:

```
============================================================
تحديث سعر الصرف - قاعدة البيانات: nbs_lugalai
============================================================

1. التحقق من العملات...
   ✅ عملة IQD موجودة (ID: 1)
   ✅ عملة USD موجودة (ID: 2)

2. سعر الصرف الحالي...
   التاريخ: 2026-01-29
   السعر: 1 USD = 1450.00 IQD

3. تحديث سعر الصرف إلى: 1 USD = 1510 IQD...
   ⚠️  يوجد سعر صرف لليوم، سيتم تحديثه...
   ✅ تم تحديث السعر

6. التحقق من النتيجة النهائية...
   ✅ التاريخ: 2026-01-29
   ✅ السعر: 1 USD = 1510.00 IQD

✅ تم تحديث سعر الصرف بنجاح!
```

---

## الوصول إلى إعدادات العملات

بعد تشغيل السكريبتات، يمكنك الوصول من:

### الطريقة 1: من الإعدادات

1. **Settings** (أيقونة الترس ⚙️)
2. **General Settings**
3. **قسم Multi-Currencies**
4. **اضغط على "Currencies"**
5. اختر **USD**
6. تبويب **"Rates"**
7. **أضف/عدّل السعر**

### الطريقة 2: من المحاسبة

1. **Accounting** (المحاسبة)
2. **Configuration** (الإعدادات)
3. **Currencies** (العملات)
4. اختر **USD**
5. تبويب **"Rates"**
6. **أضف/عدّل السعر**

---

## تحديث سعر الصرف يدوياً

### إذا كنت تريد سعر صرف مختلف:

```bash
# تحديث إلى 1520 مثلاً
venv/bin/python update_exchange_rate.py 1520

# تحديث إلى 1500
venv/bin/python update_exchange_rate.py 1500
```

### في واجهة Odoo:

1. اذهب إلى: **Accounting → Configuration → Currencies**
2. افتح عملة **USD**
3. اذهب إلى تبويب **"Rates"**
4. اضغط **"Add a line"** (إضافة سطر)
5. أدخل:
   ```
   Date: 2026-01-29 (اليوم)
   Rate: 0.00066225 (= 1 / 1510)
   ```
6. **احفظ**

**ملاحظة مهمة:** 
- في Odoo، `Rate` يُخزن كـ `1 / السعر الفعلي`
- إذا كان السعر الفعلي **1510 IQD** لكل **1 USD**
- فإن `Rate` في Odoo = `1 / 1510 = 0.00066225`

---

## فهم كيفية تخزين سعر الصرف

### في Odoo:

| السعر الفعلي | Rate في Odoo |
|--------------|--------------|
| 1 USD = 1510 IQD | 0.00066225 |
| 1 USD = 1500 IQD | 0.00066667 |
| 1 USD = 1520 IQD | 0.00065789 |

### معادلة التحويل:

```python
# من Odoo Rate إلى السعر الفعلي:
actual_rate = 1 / odoo_rate

# من السعر الفعلي إلى Odoo Rate:
odoo_rate = 1 / actual_rate

# مثال:
# إذا كان odoo_rate = 0.00066225
actual_rate = 1 / 0.00066225 = 1510.00 IQD
```

---

## في قاعدة البيانات

### الجداول المستخدمة:

```sql
-- جدول العملات
SELECT id, name, symbol, active
FROM res_currency
WHERE name IN ('IQD', 'USD');

-- جدول أسعار الصرف
SELECT 
    cr.name as date,
    c.name as currency,
    cr.rate as odoo_rate,
    1.0 / cr.rate as actual_rate
FROM res_currency_rate cr
JOIN res_currency c ON c.id = cr.currency_id
WHERE c.name = 'USD'
ORDER BY cr.name DESC
LIMIT 5;
```

### تحديث SQL مباشر (طريقة بديلة):

```bash
# الاتصال بقاعدة البيانات
sudo -u postgres psql nbs_lugalai
```

```sql
-- تحديث سعر الصرف لليوم
UPDATE res_currency_rate
SET rate = 1.0 / 1510.0  -- = 0.00066225
WHERE currency_id = (SELECT id FROM res_currency WHERE name = 'USD')
  AND name = CURRENT_DATE;

-- إذا لم يوجد سعر لليوم، أنشئه
INSERT INTO res_currency_rate (currency_id, name, rate, company_id, create_date, write_date, create_uid, write_uid)
SELECT 
    id as currency_id,
    CURRENT_DATE as name,
    1.0 / 1510.0 as rate,
    1 as company_id,
    NOW() as create_date,
    NOW() as write_date,
    2 as create_uid,
    2 as write_uid
FROM res_currency
WHERE name = 'USD'
  AND NOT EXISTS (
      SELECT 1 FROM res_currency_rate 
      WHERE currency_id = res_currency.id 
        AND name = CURRENT_DATE
  );
```

---

## الأسباب الشائعة لاختفاء قائمة العملات

### 1. Multi-Currency غير مفعل

```python
# الحل
venv/bin/python activate_currency_menu.py
```

### 2. المستخدم لا يملك الصلاحيات

```bash
# في Odoo UI:
Settings → Users & Companies → Users → [اختر المستخدم]
→ Technical Settings → Multi Currencies ✓
```

### 3. القائمة معطلة في ir.ui.menu

```python
# تفعيل القائمة
env['ir.ui.menu'].search([('name', '=', 'Currencies')]).write({'active': True})
```

### 4. الوحدة المطلوبة غير مثبتة

```bash
# تثبيت وحدة account (المحاسبة)
venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai -i account --stop-after-init
```

---

## تحديث تلقائي لسعر الصرف (متقدم)

### إنشاء Cron Job لتحديث السعر يومياً:

```python
# في Odoo shell
venv/bin/python odoo-bin shell -c odoo.conf -d nbs_lugalai
```

```python
# إنشاء Scheduled Action
env['ir.cron'].create({
    'name': 'Update USD Exchange Rate',
    'model_id': env.ref('base.model_res_currency_rate').id,
    'state': 'code',
    'code': '''
# تحديث سعر USD يومياً
usd = env['res.currency'].search([('name', '=', 'USD')], limit=1)
if usd:
    today = fields.Date.today()
    rate_record = env['res.currency.rate'].search([
        ('currency_id', '=', usd.id),
        ('name', '=', today),
    ], limit=1)
    
    new_rate = 1.0 / 1510.0  # يمكنك تغيير القيمة
    
    if rate_record:
        rate_record.write({'rate': new_rate})
    else:
        env['res.currency.rate'].create({
            'currency_id': usd.id,
            'name': today,
            'rate': new_rate,
            'company_id': env.company.id,
        })
''',
    'interval_number': 1,
    'interval_type': 'days',
    'numbercall': -1,
    'active': True,
})
```

---

## اختبار سعر الصرف

### في Odoo Shell:

```bash
venv/bin/python odoo-bin shell -c odoo.conf -d nbs_lugalai
```

```python
# الحصول على العملات
iqd = env['res.currency'].search([('name', '=', 'IQD')], limit=1)
usd = env['res.currency'].search([('name', '=', 'USD')], limit=1)

# تحويل من USD إلى IQD
amount_usd = 100.0
amount_iqd = usd._convert(amount_usd, iqd, env.company, fields.Date.today())
print(f"{amount_usd} USD = {amount_iqd} IQD")

# تحويل من IQD إلى USD
amount_iqd = 151000.0
amount_usd = iqd._convert(amount_iqd, usd, env.company, fields.Date.today())
print(f"{amount_iqd} IQD = {amount_usd} USD")
```

النتيجة المتوقعة:
```
100.0 USD = 151000.0 IQD
151000.0 IQD = 100.0 USD
```

---

## في المتصفح

بعد تشغيل السكريبتات:

1. **امسح كاش المتصفح**: `Ctrl+Shift+Delete`
2. **سجل خروج** من Odoo
3. **سجل دخول** مرة أخرى
4. اذهب إلى: **Accounting → Configuration → Currencies**
5. يجب أن تظهر القائمة الآن! ✅

---

## استكشاف الأخطاء

### إذا لم تظهر القائمة بعد:

```bash
# 1. تحقق من صلاحيات المستخدم
venv/bin/python odoo-bin shell -c odoo.conf -d nbs_lugalai
```

```python
admin = env['res.users'].browse(env.uid)
print(f"User: {admin.name}")

# التحقق من صلاحية Multi-Currency
multi_currency_group = env.ref('base.group_multi_currency')
if multi_currency_group in admin.group_ids:
    print("✅ Has Multi-Currency permission")
else:
    print("❌ Missing Multi-Currency permission")
    admin.write({'group_ids': [(4, multi_currency_group.id)]})
    print("✅ Added Multi-Currency permission")

exit()
```

### إذا كان السعر لا يُطبق على الفواتير:

```python
# تحقق من إعدادات الشركة
company = env.company
if not company.currency_exchange_journal_id:
    journal = env['account.journal'].search([
        ('type', '=', 'general'),
        ('company_id', '=', company.id),
    ], limit=1)
    if journal:
        company.write({'currency_exchange_journal_id': journal.id})
        print("✅ Fixed currency exchange journal")
```

---

## الملخص

| المشكلة | الحل |
|---------|------|
| ❌ القائمة اختفت | ✅ `venv/bin/python activate_currency_menu.py` |
| ❌ السعر 1510 قديم | ✅ `venv/bin/python update_exchange_rate.py 1510` |
| ❌ لا صلاحيات | ✅ إضافة `base.group_multi_currency` |
| ❌ لا يُطبق على الفواتير | ✅ ربط `currency_exchange_journal_id` |

---

## الملفات المضافة:

1. ✅ **`update_exchange_rate.py`**: تحديث سعر الصرف تلقائياً
2. ✅ **`activate_currency_menu.py`**: تفعيل قوائم العملات
3. ✅ **`EXCHANGE_RATE_UPDATE_GUIDE_AR.md`**: دليل شامل بالعربية

---

**الآن نفذ السكريبتات على السيرفر البعيد!** 💱

```bash
cd /home/lugalai/Lugal-ai
git pull origin main
venv/bin/python activate_currency_menu.py
venv/bin/python update_exchange_rate.py 1510
```
