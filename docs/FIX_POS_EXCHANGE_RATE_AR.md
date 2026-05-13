# إصلاح سعر الصرف في POS (نقطة البيع)

## المشكلة

```
سعر الصرف في POS: 1480 IQD ❌
سعر الصرف الصحيح: 1510 IQD ✅
```

الباركود يقرأ المنتج بسعر صرف قديم (1480) في نقطة البيع.

---

## السبب

POS (Point of Sale) يخزن البيانات محلياً في المتصفح:
- **LocalStorage**: يحفظ الإعدادات والكاش
- **Session Cache**: يحفظ بيانات الجلسة الحالية
- **Service Worker**: قد يخزن نسخة قديمة

عند فتح جلسة POS، يتم تحميل:
- أسعار المنتجات
- سعر الصرف
- إعدادات POS

**حتى لو حدّثت سعر الصرف في النظام، الجلسة المفتوحة تستمر باستخدام السعر القديم!**

---

## الحل الكامل

### على السيرفر البعيد:

```bash
cd /home/lugalai/Lugal-ai

# سحب التحديثات
git pull origin main

# تشغيل سكريبت إصلاح POS
venv/bin/python fix_pos_exchange_rate.py
```

---

## النتيجة المتوقعة

```
======================================================================
إصلاح سعر الصرف في POS - قاعدة البيانات: nbs_lugalai
======================================================================

1. التحقق من سعر الصرف في النظام...
   ✅ السعر في النظام: 1 USD = 1510.00 IQD

2. التحقق من جلسات POS المفتوحة...
   ⚠️  وجدت 1 جلسة POS مفتوحة:
      - POS/2026/01/0001 (الحالة: opened)
        POS Config: Main POS

   ⚠️  تحذير: جلسات POS المفتوحة تستخدم الكاش القديم!
   يجب إغلاقها وإعادة فتحها لتطبيق السعر الجديد.

3. التحقق من إعدادات POS...
   وجدت 1 نقطة بيع مفعلة:
      ✅ Main POS
         العملة: IQD

4. التحقق من أسعار المنتجات...
   وجدت 150 منتج في POS

✅ تم إصلاح إعدادات سعر الصرف!

📋 الخطوات المطلوبة لإصلاح POS:

⚠️  1. إغلاق جلسات POS المفتوحة:
      - اذهب إلى: Point of Sale → Sessions → POS/2026/01/0001
        اضغط 'Close Session' (إغلاق الجلسة)

2. مسح كاش المتصفح:
   - اضغط: Ctrl+Shift+Delete
   - احذف: Cached images and files
   - الفترة: All time

3. في واجهة POS:
   - اذهب إلى: Point of Sale
   - افتح نقطة بيع جديدة (New Session)
   - تأكد من السعر: 1 USD = 1510 IQD

4. اختبار:
   - امسح باركود منتج
   - تحقق من السعر المعروض
```

---

## الخطوات اليدوية في Odoo

### 1. إغلاق جلسة POS الحالية

```
Point of Sale (نقطة البيع)
→ Dashboard (لوحة التحكم)
→ اضغط على الجلسة المفتوحة
→ Close Session (إغلاق الجلسة)
→ أدخل المبالغ النقدية
→ Validate Closing (تأكيد الإغلاق)
```

**أو من القائمة:**

```
Point of Sale
→ Orders (الطلبات)
→ Sessions (الجلسات)
→ اختر الجلسة المفتوحة
→ Close Session Posting At Bank (إغلاق)
```

---

### 2. مسح كاش المتصفح

#### في Chrome/Edge:

```
1. اضغط: Ctrl+Shift+Delete
2. اختر: Cached images and files ✓
3. Time range: All time
4. Clear data
```

#### في Firefox:

```
1. اضغط: Ctrl+Shift+Delete
2. اختر: Cache ✓
3. Time range: Everything
4. Clear Now
```

#### مسح LocalStorage يدوياً:

```
1. افتح Developer Tools: F12
2. اذهب إلى: Application → Storage → Local Storage
3. اختر النطاق: http://192.168.116.211:8069
4. اضغط: Clear All
```

---

### 3. فتح جلسة POS جديدة

```
1. اذهب إلى: Point of Sale
2. اختر: نقطة البيع (Main POS مثلاً)
3. Open Session (فتح جلسة جديدة)
4. تحقق من السعر:
   - Settings (⚙️) في POS
   - Currency Rate: يجب أن يكون 1510
```

---

### 4. اختبار السعر الجديد

```
1. في واجهة POS
2. امسح باركود أي منتج
3. تحقق من السعر:

مثال:
- المنتج: عطر XYZ
- السعر الأصلي: 50 USD
- السعر المعروض: 75,500 IQD
- الحساب: 50 × 1510 = 75,500 ✅
```

---

## إذا لم يعمل بعد

### حل إضافي: إعادة تشغيل Odoo

```bash
# على السيرفر
pkill -9 -f odoo-bin
cd /home/lugalai/Lugal-ai
nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &
```

---

### حل إضافي: مسح Service Worker

في المتصفح:

```
1. F12 (Developer Tools)
2. Application → Service Workers
3. اضغط: Unregister على كل service worker
4. أعد تحميل الصفحة: Ctrl+F5
```

---

### حل إضافي: استخدام Incognito Mode

```
1. افتح نافذة تصفح خاص (Ctrl+Shift+N)
2. سجل دخول إلى Odoo
3. افتح POS
4. جرب الباركود
→ إذا عمل، المشكلة في الكاش
```

---

## فهم آلية عمل POS

### عند فتح جلسة POS:

```javascript
// يتم تحميل البيانات من الخادم
pos.load_server_data().then(() => {
    // تحميل المنتجات
    products: [...],
    
    // تحميل سعر الصرف
    currency_rate: 1480,  ← من الكاش القديم!
    
    // تحميل الإعدادات
    config: {...}
});

// يتم حفظها في LocalStorage
localStorage.setItem('pos_session_data', JSON.stringify(data));
```

### عند مسح منتج:

```javascript
// يُحسب السعر باستخدام الكاش
price_in_iqd = product.price_usd * cached_rate;
// إذا كان cached_rate = 1480 → يعطي سعر خاطئ!
```

---

## الوقاية من المشكلة مستقبلاً

### 1. إغلاق الجلسات يومياً

```
- لا تترك جلسات POS مفتوحة لأيام
- أغلق الجلسة في نهاية كل يوم
- افتح جلسة جديدة في بداية اليوم التالي
```

### 2. تحديث السعر قبل فتح POS

```bash
# صباحاً قبل فتح POS
venv/bin/python update_exchange_rate.py 1510

# ثم افتح POS
# ستحصل على السعر الجديد تلقائياً
```

### 3. مسح الكاش دورياً

```
- مرة كل أسبوع على الأقل
- خاصة بعد تحديثات النظام
- أو عند ملاحظة أي مشاكل
```

---

## استكشاف الأخطاء

### المشكلة: السعر ما زال 1480

**الحل:**

```bash
# 1. تحقق من السعر في قاعدة البيانات
venv/bin/python -c "
import odoo
from odoo import api

odoo.tools.config.parse_config(['-c', 'odoo.conf'])
with odoo.registry('nbs_lugalai').cursor() as cr:
    env = api.Environment(cr, 1, {})
    usd = env['res.currency'].search([('name', '=', 'USD')], limit=1)
    rate = env['res.currency.rate'].search([
        ('currency_id', '=', usd.id)
    ], order='name desc', limit=1)
    print(f'Rate in DB: 1 USD = {1/rate.rate:.2f} IQD')
"

# 2. إذا كان خاطئاً، حدّثه
venv/bin/python change_current_rate_to_1510.py

# 3. أعد تشغيل Odoo
pkill -9 -f odoo-bin && nohup venv/bin/python odoo-bin -c odoo.conf -d nbs_lugalai --http-port=8069 > odoo.log 2>&1 &

# 4. امسح كاش المتصفح كاملاً
# 5. أغلق وأعد فتح جلسة POS
```

---

### المشكلة: لا يمكن إغلاق الجلسة

**السبب:** يوجد أوامر مفتوحة (Draft Orders)

**الحل:**

```
1. Point of Sale → Orders → Orders
2. فلتر: Session = [الجلسة الحالية], State = New
3. لكل أمر:
   - إما: تأكيده (Validate)
   - أو: حذفه (Delete)
4. ثم أغلق الجلسة
```

---

### المشكلة: الباركود لا يعمل

**تحقق من:**

```
1. إعدادات POS:
   Point of Sale → Configuration → Point of Sale
   → اختر POS الخاص بك
   → تأكد من: Barcode Scanner: Enabled ✓

2. إعدادات المنتج:
   - افتح المنتج
   - تبويب: General Information
   - تأكد من: Barcode (EAN13): مملوء
   - تأكد من: Available in POS: ✓

3. جهاز الماسح:
   - تأكد من التوصيل (USB/Bluetooth)
   - جرب المسح في Notepad أولاً
```

---

## الملخص

| المشكلة | السبب | الحل |
|---------|-------|------|
| ❌ POS يعرض 1480 | كاش قديم في الجلسة | إغلاق الجلسة |
| ❌ الباركود سعر خاطئ | LocalStorage قديم | مسح كاش المتصفح |
| ❌ السعر لا يتحدث | الجلسة ما زالت مفتوحة | فتح جلسة جديدة |
| ❌ لا يمكن الإغلاق | أوامر مفتوحة | تأكيد/حذف الأوامر |

---

## الملفات المضافة:

1. ✅ **`fix_pos_exchange_rate.py`**: إصلاح سعر الصرف في POS
2. ✅ **`FIX_POS_EXCHANGE_RATE_AR.md`**: دليل شامل بالعربية

---

**الآن نفذ السكريبت واتبع الخطوات!** 🛒💳

```bash
cd /home/lugalai/Lugal-ai
git pull origin main
venv/bin/python fix_pos_exchange_rate.py
```

**ثم في المتصفح:**
1. أغلق جلسة POS الحالية
2. امسح الكاش (Ctrl+Shift+Delete)
3. افتح جلسة POS جديدة
4. جرب الباركود → يجب أن يعرض السعر الصحيح! ✅
